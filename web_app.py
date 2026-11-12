"""中文响应式 Web 计算器（Python 3.12 标准库实现）。"""

from __future__ import annotations

import json
import math
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import calculator

HOST = "0.0.0.0"
PORT = 8000
MAX_BODY_BYTES = 1024 * 1024

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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>中文计算器</title>
<style>
  :root {
    color-scheme: light;
    --brand: #2563eb;
    --brand-dark: #1d4ed8;
    --bg: #eef2ff;
    --card: #ffffff;
    --text: #1e293b;
    --muted: #64748b;
    --error-bg: #fef2f2;
    --error-text: #b91c1c;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: linear-gradient(135deg, var(--bg), #f8fafc);
    color: var(--text);
    font-family: system-ui, -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
  }
  main {
    width: 100%;
    max-width: 420px;
    background: var(--card);
    border-radius: 18px;
    padding: 28px;
    box-shadow: 0 18px 50px rgba(30, 41, 59, 0.16);
  }
  h1 { margin: 0 0 6px; font-size: 1.6rem; text-align: center; }
  .subtitle { margin: 0 0 22px; text-align: center; color: var(--muted); font-size: 0.92rem; }
  .field { margin-bottom: 15px; }
  label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 0.95rem; }
  input, select, button {
    width: 100%;
    font: inherit;
    border-radius: 10px;
    padding: 12px 13px;
  }
  input, select {
    border: 1px solid #cbd5e1;
    background: #fff;
    color: var(--text);
  }
  input:focus, select:focus {
    outline: 3px solid rgba(37, 99, 235, 0.18);
    border-color: var(--brand);
  }
  .actions {
    display: flex;
    gap: 10px;
    margin-top: 4px;
  }
  button {
    border: 0;
    background: var(--brand);
    color: #fff;
    font-weight: 700;
    cursor: pointer;
    margin-top: 0;
    flex: 1 1 0;
  }
  button:hover { background: var(--brand-dark); }
  button:active { transform: translateY(1px); }
  button.secondary {
    background: #e2e8f0;
    color: var(--text);
  }
  button.secondary:hover { background: #cbd5e1; }
  .result, .error {
    margin-top: 18px;
    padding: 14px;
    border-radius: 12px;
    word-break: break-word;
  }
  .result { background: #eff6ff; border: 1px solid #bfdbfe; }
  .result strong { display: block; margin-bottom: 4px; color: var(--muted); font-size: 0.85rem; }
  .result output { font-size: 1.6rem; font-weight: 800; color: var(--brand-dark); }
  .error {
    display: none;
    background: var(--error-bg);
    border: 1px solid #fecaca;
    color: var(--error-text);
    font-weight: 600;
  }
  .error.visible { display: block; }
  @media (max-width: 480px) {
    body { padding: 12px; align-items: flex-start; }
    main { padding: 20px; border-radius: 14px; }
    h1 { font-size: 1.4rem; }
    input, select, button { padding: 11px 12px; }
  }
</style>
</head>
<body>
<main>
  <h1>中文计算器</h1>
  <p class="subtitle">支持负数与小数的加、减、乘、除运算</p>

  <div class="field">
    <label for="first">第一个数字</label>
    <input id="first" type="number" step="any" inputmode="decimal" placeholder="例如 1.25 或 -5">
  </div>

  <div class="field">
    <label for="operation">选择运算</label>
    <select id="operation">
      <option value="add">加法（+）</option>
      <option value="subtract">减法（-）</option>
      <option value="multiply">乘法（×）</option>
      <option value="divide">除法（÷）</option>
    </select>
  </div>

  <div class="field">
    <label for="second">第二个数字</label>
    <input id="second" type="number" step="any" inputmode="decimal" placeholder="例如 2.5 或 -3">
  </div>

  <div class="actions">
    <button id="calculate" type="button">计算</button>
    <button id="clear" type="button" class="secondary">清空</button>
  </div>

  <section class="result" aria-live="polite">
    <strong>结果</strong>
    <output id="result">等待计算</output>
  </section>

  <section id="error" class="error" role="alert" aria-live="assertive">
    <strong>错误：</strong><span id="error-text"></span>
  </section>
</main>
<script>
(function () {
  var firstInput = document.getElementById("first");
  var secondInput = document.getElementById("second");
  var operationSelect = document.getElementById("operation");
  var button = document.getElementById("calculate");
  var clearButton = document.getElementById("clear");
  var resultOutput = document.getElementById("result");
  var errorBox = document.getElementById("error");
  var errorText = document.getElementById("error-text");

  function showError(message) {
    resultOutput.textContent = "等待计算";
    errorText.textContent = message;
    errorBox.classList.add("visible");
  }

  function clearError() {
    errorText.textContent = "";
    errorBox.classList.remove("visible");
  }

  function parseNumber(input) {
    if (input.value.trim() === "") {
      return null;
    }
    var value = Number(input.value);
    return Number.isFinite(value) ? value : null;
  }

  clearButton.addEventListener("click", function () {
    firstInput.value = "";
    secondInput.value = "";
    operationSelect.value = "add";
    resultOutput.textContent = "等待计算";
    clearError();
    firstInput.focus();
  });

  button.addEventListener("click", function () {
    clearError();
    var a = parseNumber(firstInput);
    var b = parseNumber(secondInput);
    if (a === null || b === null) {
      showError("数字格式不正确");
      return;
    }

    button.disabled = true;
    fetch("/api/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operation: operationSelect.value, a: a, b: b })
    })
      .then(function (response) {
        return response.json().then(function (data) {
          return { ok: response.ok, data: data };
        });
      })
      .then(function (outcome) {
        if (!outcome.ok) {
          showError(outcome.data.error || "计算失败");
          return;
        }
        resultOutput.textContent = String(outcome.data.result);
      })
      .catch(function () {
        showError("网络错误，请稍后重试");
      })
      .finally(function () {
        button.disabled = false;
      });
  });
})();
</script>
</body>
</html>
"""


class CalculatorRequestHandler(BaseHTTPRequestHandler):
    """处理计算器页面与 JSON API。"""

    server_version = "ChineseCalculator/1.0"

    def log_message(self, format, *args):  # noqa: A002 - 与基类签名一致
        # 避免测试和运行日志被每个请求刷屏，同时不改变响应行为。
        return

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, status, html):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status, message):
        self._send_json(status, {"error": message})

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/":
            self._send_html(HTTPStatus.OK, PAGE_HTML)
        elif path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
        else:
            self._send_error_json(HTTPStatus.NOT_FOUND, "页面不存在")

    def do_POST(self):
        path = urlsplit(self.path).path
        if path != "/api/calculate":
            self._send_error_json(HTTPStatus.NOT_FOUND, "页面不存在")
            return

        payload = self._read_json_body()
        if payload is None:
            return

        status, response = calculate_response(payload)
        self._send_json(status, response)

    def _read_json_body(self):
        """读取并解析请求体；失败时直接发送结构化错误并返回 None。"""
        try:
            raw_length = self.headers.get("Content-Length", "0")
            length = int(raw_length)
        except (TypeError, ValueError):
            self._send_error_json(HTTPStatus.BAD_REQUEST, "请求格式不正确")
            return None

        if length < 0:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "请求格式不正确")
            return None
        if length > MAX_BODY_BYTES:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "请求过大")
            return None

        try:
            body = self.rfile.read(length) if length else b""
            return json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, RecursionError):
            self._send_error_json(HTTPStatus.BAD_REQUEST, "请求格式不正确")
            return None
        except Exception:
            self._send_error_json(HTTPStatus.BAD_REQUEST, "请求格式不正确")
            return None


def _is_valid_number(value):
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except (TypeError, ValueError, OverflowError):
        return False


def calculate_response(payload):
    """校验请求并返回 (HTTP 状态码, JSON 响应对象)。"""
    if not isinstance(payload, dict):
        return HTTPStatus.BAD_REQUEST, {"error": "参数缺失"}

    if "operation" not in payload or "a" not in payload or "b" not in payload:
        return HTTPStatus.BAD_REQUEST, {"error": "参数缺失"}

    operation = payload["operation"]
    if not isinstance(operation, str) or operation not in OPERATIONS:
        return HTTPStatus.BAD_REQUEST, {"error": "不支持的运算"}

    a = payload["a"]
    b = payload["b"]
    if not _is_valid_number(a) or not _is_valid_number(b):
        return HTTPStatus.BAD_REQUEST, {"error": "数字格式不正确"}

    if operation == "divide" and b == 0:
        return HTTPStatus.BAD_REQUEST, {"error": "除数不能为零"}

    try:
        result = OPERATIONS[operation](a, b)
    except ValueError as exc:
        message = str(exc) or "计算失败"
        return HTTPStatus.BAD_REQUEST, {"error": message}
    except Exception:
        return HTTPStatus.BAD_REQUEST, {"error": "计算失败"}

    if not _is_valid_number(result):
        return HTTPStatus.BAD_REQUEST, {"error": "数字格式不正确"}

    return HTTPStatus.OK, {"result": result}


def create_server(host=HOST, port=PORT):
    """创建 HTTP 服务；测试可传入 127.0.0.1 与端口 0。"""
    return ThreadingHTTPServer((host, port), CalculatorRequestHandler)


def main():
    server = create_server()
    try:
        print(f"中文计算器已启动：http://{HOST}:{PORT}", flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
