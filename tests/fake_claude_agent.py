#!/usr/bin/env python3
"""A stand-in for `claude -p` on the cli-agent route (tests only).

It plays a script instead of thinking: it connects to the MCP URL it was
given, announces each tool call on stdout the way the CLI streams it, makes
the call, streams the result, and ends with a `result` event. The script
comes from the JSON file named by FAKE_AGENT_SCRIPT: a list of processes
(one per episode), each a list of steps:

  {"calls": [[name, args], ...]}   one assistant message with tool calls
  {"text": "..."}                  one assistant message with text only
  {"phantom": [name, args]}        announced in the stream, never sent
  {"unannounced": [name, args]}    sent to the server, never streamed
  {"hang": seconds}                sleep (for the timeout test)
  {"end": {...}}                   overrides fields of the final result
"""
import json
import os
import sys
import time
import urllib.request


def arg(name):
    return sys.argv[sys.argv.index(name) + 1]


if sys.argv[1:] == ["--version"]:
    print("9.9.9 (Fake Code)")
    sys.exit(0)

model = arg("--model")
url = json.loads(arg("--mcp-config"))["mcpServers"]["scene"]["url"]
sys.stdin.read()
spec = json.load(open(os.environ["FAKE_AGENT_SCRIPT"]))
counter = os.environ["FAKE_AGENT_SCRIPT"] + ".n"
n = int(open(counter).read()) if os.path.exists(counter) else 0
open(counter, "w").write(str(n + 1))
steps = spec[n]
session = None
rid = 0


def rpc(method, params=None, notify=False):
    global session, rid
    body = {"jsonrpc": "2.0", "method": method}
    if not notify:
        rid += 1
        body["id"] = rid
    if params is not None:
        body["params"] = params
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    if session:
        req.add_header("Mcp-Session-Id", session)
    with urllib.request.urlopen(req, timeout=10) as r:
        session = r.headers.get("Mcp-Session-Id") or session
        raw = r.read()
        return json.loads(raw) if raw else None


def emit(ev):
    print(json.dumps(ev), flush=True)


rpc("initialize", {"protocolVersion": "2025-11-25"})
rpc("notifications/initialized", {}, notify=True)
rpc("tools/list")
emit({"type": "system", "subtype": "init"})
end = {}
tu = 0
for mi, step in enumerate(steps):
    mid = f"msg_{n}_{mi}"
    usage = {"input_tokens": 10, "output_tokens": 5}
    if "hang" in step:
        time.sleep(step["hang"])
    elif "end" in step:
        end = step["end"]
    elif "text" in step:
        emit({"type": "assistant", "message": {"id": mid, "usage": usage,
                                               "content": [{"type": "text", "text": step["text"]}]}})
    else:
        calls = step.get("calls") or []
        if "phantom" in step:
            calls = [step["phantom"]]
        if "unannounced" in step:
            calls = [step["unannounced"]]
        ids = []
        for name, args in calls:
            tu += 1
            tid = f"toolu_{n}_{tu}"
            ids.append(tid)
            if "unannounced" not in step:
                emit({"type": "assistant", "message": {"id": mid, "usage": usage, "content": [
                    {"type": "tool_use", "id": tid, "name": "mcp__scene__" + name, "input": args}]}})
        if "phantom" in step:
            continue
        for (name, args), tid in zip(calls, ids):
            res = rpc("tools/call", {"name": name, "arguments": args,
                                     "_meta": {"claudecode/toolUseId": tid}})
            text = res["result"]["content"][0]["text"]
            if "unannounced" not in step:
                emit({"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": tid, "content": [{"type": "text", "text": text}]}]}})
result = {"type": "result", "subtype": "success", "is_error": False, "result": "",
          "modelUsage": {model: {}, "claude-haiku-5-5": {}}}
result.update(end)
emit(result)
