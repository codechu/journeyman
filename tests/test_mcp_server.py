"""The scene's MCP endpoint: one path per cell, one session per path.

A CLI agent reaches the scene only through this server, so the server is
where two cells could bleed into each other or a stray client could feed a
cell. These tests drive it over real HTTP on localhost.
"""
import json
import unittest
import urllib.error
import urllib.request

from journeyman.mcp_server import McpServer, SESSION_HEADER


def _tool(name):
    return {"type": "function", "function": {
        "name": name, "description": f"{name} tool",
        "parameters": {"type": "object", "properties": {"x": {"type": "string"}}}}}


def _post(url, method, params=None, session=None, mid=1):
    body = {"jsonrpc": "2.0", "method": method}
    if mid is not None:
        body["id"] = mid
    if params is not None:
        body["params"] = params
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    if session:
        req.add_header(SESSION_HEADER, session)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            raw = r.read()
            return r.status, r.headers.get(SESSION_HEADER), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, None, None


class TestMcpServer(unittest.TestCase):
    def setUp(self):
        self.srv = McpServer()
        self.calls = []

        def answer_a(name, args, meta):
            self.calls.append(("a", name, args, meta))
            return f"A answered {name} {args.get('x')}"

        def answer_b(name, args, meta):
            self.calls.append(("b", name, args, meta))
            return f"B answered {name} {args.get('x')}"

        self.url_a = self.srv.register("assayers-bench_s777", [_tool("assay"), _tool("conclude")], answer_a)
        self.url_b = self.srv.register("assayers-bench_s4242", [_tool("assay"), _tool("conclude")], answer_b)

    def tearDown(self):
        self.srv.close()

    def _open(self, url):
        st, sess, res = _post(url, "initialize", {"protocolVersion": "2025-11-25"})
        self.assertEqual(st, 200)
        self.assertTrue(sess)
        self.assertEqual(res["result"]["protocolVersion"], "2025-11-25")
        self.assertNotIn("instructions", res["result"])   # no hidden prompt
        return sess

    def test_random_localhost_port_and_distinct_paths(self):
        self.assertGreater(self.srv.port, 0)
        self.assertTrue(self.url_a.startswith(f"http://127.0.0.1:{self.srv.port}/mcp/assayers-bench_s777_"))
        self.assertNotEqual(self.url_a, self.url_b)

    def test_discover_before_initialize_is_answered(self):
        st, _, res = _post(self.url_a, "server/discover", {})
        self.assertEqual(st, 200)
        self.assertEqual(res["result"], {})

    def test_tools_list_names_unchanged(self):
        s = self._open(self.url_a)
        st, _, res = _post(self.url_a, "tools/list", session=s, mid=2)
        names = [t["name"] for t in res["result"]["tools"]]
        self.assertEqual(names, ["assay", "conclude"])
        self.assertEqual(res["result"]["tools"][0]["inputSchema"]["properties"], {"x": {"type": "string"}})

    def test_same_tool_name_goes_to_its_own_cell(self):
        sa, sb = self._open(self.url_a), self._open(self.url_b)
        _, _, ra = _post(self.url_a, "tools/call", {"name": "assay", "arguments": {"x": "ore-1"},
                                                    "_meta": {"claudecode/toolUseId": "toolu_1"}}, session=sa, mid=3)
        _, _, rb = _post(self.url_b, "tools/call", {"name": "assay", "arguments": {"x": "ore-2"}}, session=sb, mid=3)
        self.assertEqual(ra["result"]["content"][0]["text"], "A answered assay ore-1")
        self.assertEqual(rb["result"]["content"][0]["text"], "B answered assay ore-2")
        self.assertFalse(ra["result"]["isError"])
        self.assertEqual([c[0] for c in self.calls], ["a", "b"])
        self.assertEqual(self.calls[0][3], {"claudecode/toolUseId": "toolu_1"})   # meta reaches the cell

    def test_notification_is_accepted_without_body(self):
        s = self._open(self.url_a)
        st, _, res = _post(self.url_a, "notifications/initialized", {}, session=s, mid=None)
        self.assertEqual(st, 202)
        self.assertIsNone(res)

    def test_session_is_pinned(self):
        s = self._open(self.url_a)
        st, _, _ = _post(self.url_a, "initialize", {"protocolVersion": "2025-11-25"}, mid=9)
        self.assertEqual(st, 409)
        st, _, _ = _post(self.url_a, "tools/call", {"name": "assay", "arguments": {}}, session="someone-else", mid=4)
        self.assertEqual(st, 404)
        st, _, _ = _post(self.url_a, "tools/call", {"name": "assay", "arguments": {}}, mid=5)
        self.assertEqual(st, 404)
        self.assertEqual(self.calls, [])   # nothing reached the cell
        v = self.srv.violations(self.url_a)
        self.assertEqual(len(v), 3)
        self.assertIn("second initialize", v[0])
        # the pinned session still works
        st, _, res = _post(self.url_a, "tools/call", {"name": "assay", "arguments": {"x": "y"}}, session=s, mid=6)
        self.assertEqual(st, 200)

    def test_unknown_path_and_get(self):
        st, _, _ = _post(f"http://127.0.0.1:{self.srv.port}/mcp/nope", "initialize", {})
        self.assertEqual(st, 404)
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(self.url_a, timeout=5)
        self.assertEqual(cm.exception.code, 405)

    def test_unregister_closes_the_path(self):
        self.srv.unregister(self.url_a)
        st, _, _ = _post(self.url_a, "initialize", {})
        self.assertEqual(st, 404)

    def test_answer_error_is_an_rpc_error_and_a_violation(self):
        def boom(name, args, meta):
            raise RuntimeError("scene broke")
        url = self.srv.register("x_s1", [_tool("t")], boom)
        s = self._open(url)
        _, _, res = _post(url, "tools/call", {"name": "t", "arguments": {}}, session=s, mid=2)
        self.assertEqual(res["error"]["code"], -32603)
        self.assertIn("scene broke", self.srv.violations(url)[0])


if __name__ == "__main__":
    unittest.main()
