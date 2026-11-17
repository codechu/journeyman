"""Scene tools over MCP, for agents that bring their own loop (a CLI agent).

The HTTP agent path drives the model turn by turn and dispatches tool calls
itself. A CLI agent runs its own loop and reaches tools only through MCP, so
journeyman serves each cell's tools from one in-process HTTP server on a
random localhost port: one path per cell, only that scene's tools, with the
same names the HTTP path uses. Nothing is written to disk and no extra
process runs — the scene, the budget and every event stay in this process.

The server knows nothing about scenes or budgets. A cell registers its tool
list and an `answer(name, arguments, meta)` callback; the callback is where
the shared per-call rules (driver.Ledger) live. `meta` carries the client's
tool-use id when it sends one (Claude Code does: `claudecode/toolUseId`), so
a call can be bound exactly to the transcript the CLI streams.

A path accepts one MCP session: the first `initialize` pins it, and any other
session on that path is refused and recorded as a violation, so a cell can
only be fed by the agent it was given to.
"""
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SESSION_HEADER = "Mcp-Session-Id"


def mcp_tools(openai_tools):
    """OpenAI function specs → MCP tool list (names and schemas unchanged)."""
    out = []
    for t in openai_tools:
        fn = t["function"]
        out.append({"name": fn["name"],
                    "description": fn.get("description", ""),
                    "inputSchema": fn.get("parameters")
                    or {"type": "object", "properties": {}}})
    return out


class _Cell:
    def __init__(self, tools, answer):
        self.tools = mcp_tools(tools)
        self.answer = answer
        self.session = None
        self.violations = []
        self.lock = threading.Lock()   # one call at a time per cell


class McpServer:
    """One localhost MCP endpoint, many cells (one path each)."""

    def __init__(self):
        self._cells = {}
        self._guard = threading.Lock()
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def do_GET(self):
                self.send_response(405)
                self.end_headers()

            def do_DELETE(self):
                cell = server._cell(self.path)
                if cell is not None and self.headers.get(SESSION_HEADER) == cell.session:
                    cell.session = None
                self.send_response(200)
                self.end_headers()

            def do_POST(self):
                server._post(self)

        self._http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._http.serve_forever,
                                        daemon=True)
        self._thread.start()

    @property
    def port(self):
        return self._http.server_address[1]

    def register(self, cell_key, tools, answer):
        """Open a path for one cell; returns its URL."""
        path = f"/mcp/{cell_key}_{secrets.token_hex(4)}"
        with self._guard:
            self._cells[path] = _Cell(tools, answer)
        return f"http://127.0.0.1:{self.port}{path}"

    def violations(self, url):
        cell = self._cell(url.split(str(self.port), 1)[-1])
        return list(cell.violations) if cell else []

    def unregister(self, url):
        with self._guard:
            self._cells.pop(url.split(str(self.port), 1)[-1], None)

    def close(self):
        self._http.shutdown()
        self._http.server_close()

    def _cell(self, path):
        with self._guard:
            return self._cells.get(path.split("?", 1)[0])

    def _post(self, h):
        cell = self._cell(h.path)
        if cell is None:
            return _reply(h, 404)
        try:
            msg = json.loads(h.rfile.read(int(h.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            return _reply(h, 400)
        mid, method = msg.get("id"), msg.get("method")
        params = msg.get("params") or {}
        sent = h.headers.get(SESSION_HEADER)
        extra = {}
        if method == "initialize":
            if cell.session is not None:
                cell.violations.append("second initialize on a pinned path")
                return _reply(h, 409)
            cell.session = secrets.token_hex(8)
            extra[SESSION_HEADER] = cell.session
        elif method != "server/discover":
            if cell.session is None or sent != cell.session:
                cell.violations.append(f"{method} from session {sent!r}")
                return _reply(h, 404)
        if mid is None:   # a notification: nothing to answer
            return _reply(h, 202)
        if method == "initialize":
            result = {"protocolVersion": params.get("protocolVersion", "2025-03-26"),
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "journeyman-scene", "version": "1"}}
        elif method == "server/discover":
            result = {}
        elif method == "tools/list":
            result = {"tools": cell.tools}
        elif method == "tools/call":
            with cell.lock:
                try:
                    text = cell.answer(params.get("name"), params.get("arguments") or {},
                                       params.get("_meta") or {})
                except Exception as e:   # the cell decides what this means
                    cell.violations.append(f"answer raised {e!r}")
                    return _rpc(h, mid, error={"code": -32603, "message": str(e)})
            result = {"content": [{"type": "text", "text": text}], "isError": False}
        elif method in ("prompts/list", "resources/list"):
            result = {method.split("/")[0]: []}
        elif method == "ping":
            result = {}
        else:
            return _rpc(h, mid, error={"code": -32601, "message": f"unknown method {method}"})
        return _rpc(h, mid, result=result, headers=extra)


def _reply(h, code):
    h.send_response(code)
    h.send_header("Content-Length", "0")
    h.end_headers()


def _rpc(h, mid, result=None, error=None, headers=None):
    body = {"jsonrpc": "2.0", "id": mid}
    body["error" if error is not None else "result"] = error if error is not None else result
    data = json.dumps(body).encode()
    h.send_response(200)
    h.send_header("Content-Type", "application/json")
    h.send_header("Content-Length", str(len(data)))
    for k, v in (headers or {}).items():
        h.send_header(k, v)
    h.end_headers()
    h.wfile.write(data)
