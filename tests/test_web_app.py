import json
import threading
import unittest
import urllib.error
import urllib.request

import web_app

_NO_PAYLOAD = object()


class WebCalculatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = web_app.create_server("127.0.0.1", 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address[:2]
        cls.base_url = f"http://{host}:{port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def _request(self, method, path, payload=_NO_PAYLOAD, raw_body=None):
        data = None
        headers = {}
        if raw_body is not None:
            data = raw_body
            headers["Content-Type"] = "application/json"
        elif payload is not _NO_PAYLOAD:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            self.base_url + path, data=data, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                body = response.read().decode("utf-8")
                return response.status, response.headers.get("Content-Type", ""), body
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8")
            return exc.code, exc.headers.get("Content-Type", ""), body

    def post_calculate(self, payload):
        return self._request("POST", "/api/calculate", payload=payload)

    def assert_calculation(self, operation, a, b, expected):
        status, content_type, body = self.post_calculate(
            {"operation": operation, "a": a, "b": b}
        )
        self.assertEqual(status, 200, body)
        self.assertIn("application/json", content_type)
        self.assertEqual(json.loads(body), {"result": expected})

    def assert_error(self, payload, expected_error):
        status, content_type, body = self.post_calculate(payload)
        self.assertEqual(status, 400, body)
        self.assertIn("application/json", content_type)
        data = json.loads(body)
        self.assertEqual(data, {"error": expected_error})
        self.assertTrue(data["error"])

    def test_page_is_chinese_and_responsive(self):
        status, content_type, body = self._request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        for text in ("计算器", "viewport", "加", "减", "乘", "除", "计算", "结果", "错误"):
            self.assertIn(text, body)
        self.assertEqual(body.count('type="number"'), 2)
        self.assertIn("<select", body)
        self.assertIn("width=device-width", body)
        self.assertIn("@media", body)
        self.assertNotIn("http://", body)
        self.assertNotIn("https://", body)

    def test_health(self):
        status, content_type, body = self._request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        self.assertEqual(json.loads(body), {"status": "ok"})

    def test_addition(self):
        cases = [
            (2, 3, 5),
            (1.25, 2.5, 3.75),
            (-5, 2.5, -2.5),
            (-2.5, -1.5, -4.0),
        ]
        for a, b, expected in cases:
            with self.subTest(a=a, b=b):
                self.assert_calculation("add", a, b, expected)

    def test_subtraction(self):
        cases = [
            (7, 9, -2),
            (-2.5, 1.25, -3.75),
            (0.5, -0.25, 0.75),
        ]
        for a, b, expected in cases:
            with self.subTest(a=a, b=b):
                self.assert_calculation("subtract", a, b, expected)

    def test_multiplication(self):
        cases = [
            (-3, 4, -12),
            (1.5, -2, -3.0),
            (0.25, 0.4, 0.1),
        ]
        for a, b, expected in cases:
            with self.subTest(a=a, b=b):
                self.assert_calculation("multiply", a, b, expected)

    def test_division(self):
        cases = [
            (7, 2, 3.5),
            (-7, 2, -3.5),
            (0.5, 0.25, 2.0),
        ]
        for a, b, expected in cases:
            with self.subTest(a=a, b=b):
                self.assert_calculation("divide", a, b, expected)

    def test_division_by_zero_and_negative_zero(self):
        for divisor in (0, -0.0):
            with self.subTest(divisor=divisor):
                self.assert_error(
                    {"operation": "divide", "a": 7, "b": divisor},
                    "除数不能为零",
                )

    def test_missing_parameters(self):
        cases = [
            {"a": 2, "operation": "add"},
            {"a": 2, "b": 3},
            {"operation": "add", "b": 3},
            {},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                self.assert_error(payload, "参数缺失")

    def test_invalid_numbers(self):
        cases = [
            {"operation": "add", "a": "abc", "b": 3},
            {"operation": "add", "a": True, "b": 3},
            {"operation": "add", "a": "NaN", "b": 3},
            {"operation": "add", "a": None, "b": 3},
            {"operation": "add", "a": [], "b": 3},
            {"operation": "add", "a": 2, "b": False},
            {"operation": "multiply", "a": "1e3", "b": 2},
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                self.assert_error(payload, "数字格式不正确")

    def test_non_finite_numbers_rejected(self):
        for raw_value in ("NaN", "Infinity", "-Infinity", "1e999"):
            raw = (
                '{"operation":"add","a":' + raw_value + ',"b":3}'
            ).encode("utf-8")
            with self.subTest(raw_value=raw_value):
                status, _, body = self._request(
                    "POST", "/api/calculate", raw_body=raw
                )
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(body), {"error": "数字格式不正确"})

    def test_unsupported_operation(self):
        for operation in ("pow", "ADD", "mod", None):
            with self.subTest(operation=operation):
                self.assert_error(
                    {"operation": operation, "a": 2, "b": 3},
                    "不支持的运算",
                )

    def test_malformed_and_non_object_json_do_not_crash(self):
        for raw in (b"{not json", b"", b"[]", b"null"):
            with self.subTest(raw=raw):
                status, content_type, body = self._request(
                    "POST", "/api/calculate", raw_body=raw
                )
                self.assertEqual(status, 400)
                self.assertIn("application/json", content_type)
                data = json.loads(body)
                self.assertIn("error", data)
                self.assertTrue(data["error"])

        status, _, body = self._request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"status": "ok"})

    def test_unknown_path_returns_json_error(self):
        status, content_type, body = self._request("GET", "/missing")
        self.assertEqual(status, 404)
        self.assertIn("application/json", content_type)
        self.assertIn("error", json.loads(body))


if __name__ == "__main__":
    unittest.main()
