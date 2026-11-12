"""中文响应式 Web 计算器：仅使用 Python 3.12 标准库。"""

from __future__ import annotations

import json
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import calculator

HOST = "0.0.0.0"
PORT = 8000

OPERATIONS = {
    "add": calculator.add,
    "subtract": calculator.subtract,
    "multiply": calculator.multiply,
    "divide": calculator.divide,
}

PAGE_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>中文计算器</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #eef3fb;
      --card: #ffffff;
      --text: #1b2738;
      --muted: #5b6b82;
      --primary: #2563eb;
      --primary-dark: #1d4ed8;
      --border: #cbd6e6;
      --result-bg: #eff6ff;
      --error-bg: #fef2f2;
      --error-text: #b91c1c;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      background: linear-gradient(160deg, #eef3fb 0%, #dbe7fa 100%);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
        "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    }

    .calculator {
      width: min(100%, 460px);
      padding: 28px;
      border-radius: 20px;
      background: var(--card);
      box-shadow: 0 18px 45px rgba(31, 54, 92, 0.16);
    }

    h1 {
      margin: 0 0 6px;
      font-size: clamp(1.5rem, 5vw, 1.9rem);
      text-align: center;
    }

    .subtitle {
      margin: 0 0 24px;
      color: var(--muted);
      font-size: 0.95rem;
      text-align: center;
    }

    .field {
      margin-bottom: 18px;
    }

    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 600;
    }

    input,
    select {
      width: 100%;
      min-height: 48px;
      padding: 10px 14px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: #fff;
      color: var(--text);
      font: inherit;
      font-size: 1.05rem;
    }

    input:focus,
    select:focus {
      outline: 3px solid rgba(37, 99, 235, 0.18);
      border-color: var(--primary);
    }

    button {
      width: 100%;
      min-height: 50px;
      border: 0;
      border-radius: 12px;
      background: var(--primary);
      color: #fff;
      font: inherit;
      font-size: 1.1rem;
      font-weight: 700;
      cursor: pointer;
    }

    button:hover {
      background: var(--primary-dark);
    }

    button:active {
      transform: translateY(1px);
    }

    .panel {
      margin-top: 18px;
      padding: 14px 16px;
      border-radius: 12px;
    }

    .panel h2 {
      margin: 0 0 6px;
      font-size: 0.9rem;
      color: var(--muted);
      font-weight: 600;
    }

    .panel p {
      margin: 0;
      min-height: 1.5em;
      font-size: 1.35rem;
      font-weight: 700;
      overflow-wrap: anywhere;
    }

    .result {
      background: var(--result-bg);
    }

    .error {
      background: var(--error-bg);
      color: var(--error-text);
    }

    .error p {
      font-size: 1rem;
      font-weight: 600;
    }

    @media (max-width: 480px) {
      body {
        align-items: flex-start;
        padding: 12px;
      }

      .calculator {
        padding: 20px 16px;
        border-radius: 16px;
      }

      input,
      select,
      button {
        min-height: 52px;
        font-size: 16px;
      }
    }
  </style>
</head>
<body>
  <main class="calculator">
    <h1>中文计算器</h1>
    <p class="subtitle">输入两个数字，选择加、减、乘、除后点击计算。</p>
    <form id="calculator-form" novalidate>
      <div class="field">
        <label for="a">数字 A</label>
        <input id="a" name="a" type="number" step="any" inputmode="decimal" placeholder="例如 2" required>
      </div>
      <div class="field">
        <label for="b">数字 B</label>
        <input id="b" name="b" type="number" step="any" inputmode="decimal" placeholder="例如 3" required>
      </div>
      <div class="field">
        <label for="operation">运算</label>
        <select id="operation" name="operation">
          <option value="add">加（+）</option>
          <option value="subtract">减（-）</option>
          <option value="multiply">乘（×）</option>
          <option value="divide">除（÷）</option>
        </select>
      </div>
      <button id="calculate" type="submit">计算</button>
    </form>
    <section class="panel result" aria-live="polite">
      <h2>结果</h2>
      <p id="result">—</p>
    </section>
    <section class="panel error" aria-live="assertive">
      <h2>错误提示</h2>
      <p id="error" role="alert"></p>
    </section>
  </main>
  <script>
    (function () {
      "use strict";
      var form = document.getElementById("calculator-form");
      var aInput = document.getElementById("a");
      var bInput = document.getElementById("b");
      var operationInput = document.getElementById("operation");
      var resultOutput = document.getElementById("result");
      var errorOutput = document.getElementById("error");

      function showError(message) {
        resultOutput.textContent = "—";
        errorOutput.textContent = message;
      }

      form.addEventListener("submit", async function (event) {
        event.preventDefault();
        errorOutput.textContent = "";

        if (aInput.value.trim() === "" || bInput.value.trim() === "") {
          showError("请输入两个数字");
          return;
        }

        var a = Number(aInput.value);
        var b = Number(bInput.value);
        if (!Number.isFinite(a) || !Number.isFinite(b)) {
          showError("数字格式不正确");
          return;
        }

        resultOutput.textContent = "计算中…";
        try {
          var response = await fetch("/api/calculate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              operation: operationInput.value,
              a: a,
              b: b
            })
          });
          var data = await response.json();
          if (!response.ok) {
            showError(data.error || "计算失败，请稍后重试");
            return;
          }
          resultOutput.textContent = String(data.result);
          errorOutput.textContent = "";
        } catch (error) {
          showError("网络错误，请稍后重试");
        }
      });
    })();
  </script>
</body>
</html>
"""


def _is_valid_number(value):
    """只接受有限的 JSON 数字，明确排除布尔值、字符串和 null。"""
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    return False


def _error_response(message):
    return 400, {"error": message}


def calculate_payload(payload):
    """校验请求 JSON 并返回 (HTTP 状态码, JSON 响应对象)。"""
    if not isinstance(payload, dict):
        return _error_response("参数缺失")

    for field in ("operation", "a", "b"):
        if field not in payload:
            return _error_response("参数缺失")

    operation = payload["operation"]
    if not isinstance(operation, str) or operation not in OPERATIONS:
        return _error_response("不支持的运算")

    a = payload["a"]
    b = payload["b"]
    if not _is_valid_number(a) or not _is_valid_number(b):
        return _error_response("数字格式不正确")

    if operation == "divide" and b == 0:
        return _error_response("除数不能为零")

    try:
        result = OPERATIONS[operation](a, b)
    except ValueError as exc:
        message = str(exc) or "不支持的运算"
        return _error_response(message)
    except (OverflowError, ZeroDivisionError):
        return _error_response("数字格式不正确")

    if isinstance(result, float) and not math.isfinite(result):
        return _error_response("数字格式不正确")

    return 200, {"result": result}


class CalculatorRequestHandler(BaseHTTPRequestHandler):
    server_version = "ChineseCalculator/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):  # noqa: A002 - 标准库方法签名
        # 保持服务输出整洁；请求结果已通过 HTTP 状态码返回。
        pass

    def _send_body(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status, payload):
        try:
            body = json.dumps(
                payload, ensure_ascii=False, allow_nan=False
            ).encode("utf-8")
        except (TypeError, ValueError, OverflowError):
            status = 400
            body = json.dumps(
                {"error": "数字格式不正确"}, ensure_ascii=False
            ).encode("utf-8")
        self._send_body(status, body, "application/json; charset=utf-8")

    def do_GET(self):  # noqa: N802 - 标准库方法名
        path = urlsplit(self.path).path
        if path == "/":
            self._send_body(200, PAGE_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        self._send_json(404, {"error": "未找到请求的资源"})

    def do_POST(self):  # noqa: N802 - 标准库方法名
        path = urlsplit(self.path).path
        if path != "/api/calculate":
            self._send_json(404, {"error": "未找到请求的资源"})
            return

        raw_length = self.headers.get("Content-Length")
        try:
            length = int(raw_length) if raw_length is not None else 0
        except (TypeError, ValueError):
            self._send_json(400, {"error": "请求体格式不正确"})
            return

        if length < 0 or length > 1024 * 1024:
            self.close_connection = True
            self._send_json(400, {"error": "请求体格式不正确"})
            return

        body = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            self._send_json(400, {"error": "请求体格式不正确"})
            return

        status, response = calculate_payload(payload)
        self._send_json(status, response)

    def do_PUT(self):  # noqa: N802
        self._send_json(405, {"error": "不支持的请求方法"})

    def do_DELETE(self):  # noqa: N802
        self._send_json(405, {"error": "不支持的请求方法"})

    def do_PATCH(self):  # noqa: N802
        self._send_json(405, {"error": "不支持的请求方法"})


def create_server(host=HOST, port=PORT):
    """创建 HTTP 服务器；测试可传入 127.0.0.1 和端口 0。"""
    server = ThreadingHTTPServer((host, port), CalculatorRequestHandler)
    server.daemon_threads = True
    return server


def main():
    server = create_server()
    print(f"中文计算器服务已启动：http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
