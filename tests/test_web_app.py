"""中文 Web 计算器的 HTTP 验收测试。"""

from __future__ import annotations

import http.client
import json
import threading
import unittest

import web_app


class WebAppHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = web_app.create_server(host="127.0.0.1", port=0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def request(self, method, path, payload=None, raw_body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {}
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif raw_body is not None:
            body = raw_body
            headers["Content-Type"] = "application/json"
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            content = response.read()
            return response.status, response.getheader("Content-Type", ""), content
        finally:
            connection.close()

    def post_calculate(self, payload):
        status, content_type, content = self.request(
            "POST", "/api/calculate", payload=payload
        )
        self.assertIn("application/json", content_type)
        return status, json.loads(content.decode("utf-8"))

    def test_server_binding_defaults(self):
        self.assertEqual(web_app.HOST, "0.0.0.0")
        self.assertEqual(web_app.PORT, 8000)

    def test_page_returns_chinese_responsive_calculator(self):
        status, content_type, content = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        html = content.decode("utf-8")
        for text in ("计算器", "viewport", "加", "减", "乘", "除", "计算", "结果", "错误"):
            self.assertIn(text, html)
        self.assertIn('type="number"', html)
        self.assertEqual(html.count('type="number"'), 2)
        self.assertIn("<style>", html)
        self.assertIn("<script>", html)
        self.assertNotIn("<link", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)

    def test_page_has_clear_button_next_to_calculate(self):
        status, content_type, content = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        html = content.decode("utf-8")
        self.assertIn("清空", html)
        self.assertIn('id="clear"', html)
        actions_index = html.index('class="actions"')
        calculate_index = html.index('id="calculate"')
        clear_index = html.index('id="clear"')
        self.assertLess(actions_index, calculate_index)
        self.assertLess(calculate_index, clear_index)

    def test_page_clear_button_resets_state(self):
        status, _, content = self.request("GET", "/")
        self.assertEqual(status, 200)
        html = content.decode("utf-8")
        self.assertIn("加法", html)
        reset_script = html[
            html.index("clearButton.addEventListener") : html.index(
                "button.addEventListener"
            )
        ]
        self.assertIn('firstInput.value = ""', reset_script)
        self.assertIn('secondInput.value = ""', reset_script)
        self.assertIn('operationSelect.value = "add"', reset_script)
        self.assertIn('resultOutput.textContent = "等待计算"', reset_script)
        self.assertIn("clearError();", reset_script)

    def test_clear_then_recalculate_returns_five(self):
        status, _, content = self.request("GET", "/")
        self.assertEqual(status, 200)
        html = content.decode("utf-8")
        self.assertIn("清空", html)
        self.assertIn("等待计算", html)

        status, data = self.post_calculate(
            {"operation": "add", "a": 2, "b": 3}
        )
        self.assertEqual(status, 200)
        self.assertEqual(data, {"result": 5})

    def test_health(self):
        status, content_type, content = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        self.assertEqual(json.loads(content.decode("utf-8")), {"status": "ok"})

    def test_four_operations(self):
        cases = [
            ({"operation": "add", "a": 2, "b": 3}, 5),
            ({"operation": "subtract", "a": 7, "b": 9}, -2),
            ({"operation": "multiply", "a": -3, "b": 4}, -12),
            ({"operation": "divide", "a": 7, "b": 2}, 3.5),
        ]
        for payload, expected in cases:
            with self.subTest(payload=payload):
                status, data = self.post_calculate(payload)
                self.assertEqual(status, 200)
                self.assertEqual(data, {"result": expected})

    def test_decimals_and_negative_numbers(self):
        cases = [
            ({"operation": "add", "a": 1.25, "b": 2.5}, 3.75),
            ({"operation": "add", "a": -5, "b": 2.5}, -2.5),
            ({"operation": "subtract", "a": -1.5, "b": 0.5}, -2.0),
            ({"operation": "multiply", "a": -1.5, "b": -2}, 3.0),
            ({"operation": "divide", "a": -7.5, "b": 2.5}, -3.0),
        ]
        for payload, expected in cases:
            with self.subTest(payload=payload):
                status, data = self.post_calculate(payload)
                self.assertEqual(status, 200)
                self.assertEqual(data["result"], expected)

    def test_division_by_zero_and_negative_zero(self):
        for divisor in (0, -0.0):
            with self.subTest(divisor=divisor):
                status, data = self.post_calculate(
                    {"operation": "divide", "a": 7, "b": divisor}
                )
                self.assertEqual(status, 400)
                self.assertEqual(data, {"error": "除数不能为零"})

    def test_missing_parameters(self):
        cases = [
            {"operation": "add", "a": 2},
            {"a": 2, "b": 3},
            {"operation": "add", "b": 3},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                status, data = self.post_calculate(payload)
                self.assertEqual(status, 400)
                self.assertEqual(data, {"error": "参数缺失"})

    def test_invalid_numbers(self):
        cases = [
            {"operation": "add", "a": "abc", "b": 3},
            {"operation": "add", "a": True, "b": 3},
            {"operation": "add", "a": "NaN", "b": 3},
            {"operation": "add", "a": None, "b": 3},
            {"operation": "add", "a": 2, "b": False},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                status, data = self.post_calculate(payload)
                self.assertEqual(status, 400)
                self.assertEqual(data, {"error": "数字格式不正确"})

    def test_non_finite_numbers_are_rejected(self):
        for name, value in (
            ("nan", float("nan")),
            ("inf", float("inf")),
            ("-inf", float("-inf")),
        ):
            with self.subTest(name=name):
                status, data = self.post_calculate(
                    {"operation": "add", "a": value, "b": 3}
                )
                self.assertEqual(status, 400)
                self.assertEqual(data, {"error": "数字格式不正确"})

    def test_unsupported_operation(self):
        status, data = self.post_calculate(
            {"operation": "pow", "a": 2, "b": 3}
        )
        self.assertEqual(status, 400)
        self.assertEqual(data, {"error": "不支持的运算"})

    def test_non_string_operation_is_rejected(self):
        status, data = self.post_calculate({"operation": True, "a": 2, "b": 3})
        self.assertEqual(status, 400)
        self.assertEqual(data, {"error": "不支持的运算"})

    def test_malformed_json_is_structured_error(self):
        status, content_type, content = self.request(
            "POST", "/api/calculate", raw_body=b"{not valid json"
        )
        self.assertEqual(status, 400)
        self.assertIn("application/json", content_type)
        data = json.loads(content.decode("utf-8"))
        self.assertIn("error", data)
        self.assertTrue(data["error"])

    def test_unknown_paths_return_json_404(self):
        status, content_type, content = self.request("GET", "/missing")
        self.assertEqual(status, 404)
        self.assertIn("application/json", content_type)
        self.assertIn("error", json.loads(content.decode("utf-8")))


if __name__ == "__main__":
    unittest.main()
