# 开发手册

## 环境要求

- Python 3.11+
- Node.js 18+
- npm 或 yarn

## 后端启动

```bash
cd application
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

pip install -r requirements.txt
cp .env.example .env       # 编辑 .env 填入你的配置
python main.py
```

后端运行在 `http://localhost:8000`，API 文档在 `http://localhost:8000/docs`。

## 前端启动

```bash
cd application-web
npm install
npm run dev
```

前端运行在 `http://localhost:5173`，API 请求通过 Vite 配置代理到后端。

## 项目结构

```
application/
├── main.py                    # 入口文件
├── config/settings.py         # pydantic-settings 配置
├── controller/                # HTTP 层（路由 + VO）
│   ├── chat/                  # 聊天接口
│   └── system/                # 系统接口（健康检查）
└── library/
    ├── base/                  # API 响应封装、异常处理
    ├── domain/                # 领域驱动逻辑
    │   ├── command/           # 业务命令
    │   ├── phrase/            # 逻辑组合
    │   └── step/              # 原子操作
    ├── models/                # SQLAlchemy ORM 模型
    ├── managers/              # 数据访问层
    └── services/              # 业务服务层
```

## 层级调用规则

1. **Controller** 只能导入 `services`
2. **Service** 可导入 `managers` 和 `domain/command`
3. **Command** 只能导入 `domain/phrase`
4. **Phrase** 只能导入 `domain/step`
5. **Step** 执行原子操作（API 调用、工具调用）

## 新增功能流程

1. 在 `controller/<domain>/<domain>_vo.py` 中定义请求/响应 VO
2. 在 `controller/<domain>/<domain>_controller.py` 中创建或更新控制器
3. 在 `library/services/<domain>_service.py` 中实现业务逻辑
4. 如果涉及复杂逻辑，在 `library/domain/` 下创建领域层代码
5. 如果需要数据持久化，在 `library/models/` 添加模型，在 `library/managers/` 添加管理器

## API 响应格式

所有接口返回统一格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

- `code: 0` = 成功
- `code: 非零` = 失败（message 字段说明错误原因）

## 环境变量

参见 `.env.example` 获取所有支持的配置项。所有配置通过 `pydantic-settings` 管理，可通过环境变量或 `.env` 文件覆盖。
