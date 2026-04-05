# 使用手册

## 快速开始

1. 打开浏览器，访问 `http://localhost:5173`
2. 点击左侧栏 **"+ New Chat"** 创建新会话
3. 在输入框中输入消息，按 **Enter** 发送（或点击 **Send** 按钮）
4. 等待 AI 回复，继续对话即可

## 功能说明

### 会话管理
- 从左侧栏创建多个会话
- 点击会话名称切换会话
- 点击 **x** 按钮删除会话

### 聊天
- 输入消息并接收 AI 回复
- 每个会话的消息历史独立保存
- 按 **Shift+Enter** 在消息中换行

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/conversations` | 创建新会话 |
| GET | `/api/chat/conversations` | 获取会话列表 |
| GET | `/api/chat/conversations/{id}/messages` | 获取会话消息记录 |
| POST | `/api/chat/conversations/{id}/chat` | 发送消息并获取回复 |
| DELETE | `/api/chat/conversations/{id}` | 删除会话 |
| GET | `/api/system/health` | 健康检查 |

## 配置说明

编辑 `application/.env` 文件进行配置：

- `LLM_API_KEY` — LLM 提供商的 API Key
- `LLM_MODEL` — 使用的模型（默认：gpt-4）
- `DATABASE_URL` — 数据库连接字符串

未配置 API Key 时，系统会返回 Mock 响应，方便测试。
