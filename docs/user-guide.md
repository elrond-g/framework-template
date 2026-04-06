# 使用手册

## 快速开始

1. 打开浏览器，访问 `http://localhost:5173`
2. 点击左侧栏 **"+ New Chat"** 创建新会话
3. 填写八字测算表单（出生时间、性别、出生地、测算方向）
4. 点击 **"开始测算"** 按钮
5. 等待 AI 回复测算结果

## 功能说明

### 会话管理
- 从左侧栏创建多个会话
- 点击会话名称切换会话
- 点击 **x** 按钮删除会话

### 八字测算表单

每次发起对话需填写以下信息：

| 字段 | 说明 | 必填 |
|------|------|------|
| 出生时间 | 年、月、日、时、分 | 是 |
| 性别 | 男 / 女 | 是 |
| 出生地 | 具体到市区，如"北京市海淀区" | 是 |
| 测算方向 | 可多选：财运、事业、情感、健康、学业，也可输入自定义方向 | 至少选一项 |

填写完成后，系统自动拼接为提示词发送给 AI，由八字大师角色进行测算回复。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat/conversations` | 创建新会话 |
| GET | `/api/chat/conversations` | 获取会话列表 |
| PATCH | `/api/chat/conversations/{id}` | 更新会话标题 |
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
