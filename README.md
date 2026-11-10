# Agent Loop

GitHub Issue → OpenCode 编码与独立测试 → PR → GitHub Actions / AI Review → 自动合并与通知的真实验收仓库。

## 本地测试

```bash
python -m unittest discover -s tests -v
```

项目只使用 Python 标准库。初始化基线由调度控制面准备，后续需求代码由独立 OpenCode Worker 执行。

## 任务入口

创建包含明确验收条件的 Issue，再由授权账号添加 `agent:ready` 标签。中央定期扫描队列，串行执行任务。

现阶段模型仅能编辑 `calculator.py` 及指定的新测试文件；基线测试和 CI 配置保持固定。正常交付通过 CI 与 AI 门禁后自动合并，异常任务保留阻断原因和证据。
