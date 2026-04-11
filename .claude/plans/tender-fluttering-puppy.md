# 开启模型深度思考

## Context

用户使用 `zenmux.ai` 代理（OpenAI 兼容格式）调用 Claude（`anthropic/claude-opus-4.6`），希望开启模型的深度思考（extended thinking）功能。

**现状分析**：整个 thinking 处理链路已经完整构建好：
- ✅ `LLMStep.call_llm_stream()` 已解析 `reasoning_content` 字段（第 202 行）
- ✅ `ChatPhrase` / `ChatCommand` / `ChatService` 已透传 thinking 事件
- ✅ SSE 协议已支持 `thinking` 类型事件
- ✅ 前端 `ChatWindow.jsx` 已处理 `onThinking` 回调
- ✅ 前端 `MessageBubble.jsx` 已实现可折叠的思考过程区域
- ✅ CSS 思考过程样式已就绪
- ✅ `.env` 中 `LLM_TEMPERATURE=1.0`（Claude 思考模式要求 temperature=1）

**问题**：当前代码虽然**能接收**思考内容，但没有在请求参数中**主动启用**思考功能。大多数 OpenAI 兼容代理（包括 zenmux.ai）需要在请求 body 中传递额外参数来触发 Claude 的 extended thinking。

## 实现方案

### 1. 新增配置项

**`application/config/settings.py`**：
```python
# LLM Thinking
llm_enable_thinking: bool = True
llm_thinking_budget_tokens: int = 10000
```

**`application/.env.example`**：
```
LLM_ENABLE_THINKING=true
LLM_THINKING_BUDGET_TOKENS=10000
```

### 2. 修改 LLM 请求参数

**`application/library/domain/step/llm_step.py`**：

在 `call_llm_stream()` 的请求 JSON 中，当 `settings.llm_enable_thinking` 为 `True` 时，添加 thinking 相关参数。考虑到用户使用 OpenAI 兼容代理，常见的启用方式有两种：

**方案 A（推荐）**：使用 `reasoning_effort` 参数（部分代理支持）
```json
{
    "model": "...",
    "messages": [...],
    "stream": true,
    "reasoning_effort": "high"
}
```

**方案 B**：使用 `enable_thinking` + `thinking` 参数（部分代理支持）
```json
{
    "model": "...",
    "messages": [...],
    "stream": true,
    "enable_thinking": true,
    "thinking": {"budget_tokens": 10000}
}
```

由于用户表示代理自动处理，**实际采用**：同时传递 `reasoning_effort` 参数，让代理自行判断。如果代理确实完全自动，那多传参数也无害。

同时在非流式 `call_llm()` 中也加入相同参数。

### 涉及文件

| 文件 | 操作 |
|------|------|
| `application/config/settings.py` | 新增 `llm_enable_thinking`、`llm_thinking_budget_tokens` 配置 |
| `application/.env.example` | 新增 thinking 相关配置项 |
| `application/library/domain/step/llm_step.py` | 请求中添加 thinking 启用参数 |
| `docs/user-guide.md` | 更新深度思考功能说明 |
| `docs/operations-guide.md` | 更新配置项说明 |

### 验证方式

1. 启动后端 `python main.py`
2. 启动前端 `npm run dev`
3. 发送消息 → 观察 AI 回复时是否有"思考过程"折叠区域
4. Mock 模式下也能看到模拟的思考过程
5. 检查 `llm-describe.log` 确认请求参数中包含 thinking 参数
