# Narra Studio

English version: [README.md](README.md)

Narra Studio 是一个 Docker-first 的 AI 内容生产实验与模型调试工作台。

它不是普通 AI 聊天应用，也不是自动成片平台。它的目标是提供一个可本地运行、可检查、可复盘的工作台，让创作者和开发者能够调用媒体生成模型、比较结果、保存生成资产，并在事后理解每一次调用发生了什么。

## 项目想实现什么

Narra Studio 围绕以下目标设计：

- 通过统一后端 API 调用不同 AI Provider；
- 支持文本转语音、语音识别、VoiceProfile、文生图、视频生成等媒体实验工作流；
- 将每一次模型调用记录为 `Experiment`；
- 将生成的音频、图片、视频和其他文件保存为 `Asset`；
- 让 Prompt 模板、参数和结果可复现；
- 支持人工评价和结果对比；
- 记录估算成本和调用日志，方便复盘；
- 将可用结果组织到内容项目中；
- 默认通过 Docker Compose 在本地长期运行。

## 当前已实现

当前版本包含：

- FastAPI 后端；
- Docker Compose 默认服务：`api`、`web`、`db` 和 workspace volume；
- async profile：`redis` 和 Celery `worker`；
- 默认 PostgreSQL 数据库，以及便于开发/测试的 SQLite 路径；
- Provider 和 Model Registry API；
- `CredentialResolver`，支持环境变量、Docker secret、文件或无凭证 Provider；
- Capability Adapter 协议和 Adapter Registry；
- 覆盖 TTS、STT、声音克隆、文生图、视频生成的 Mock Adapter；
- OpenAI、ElevenLabs、fal.ai、Replicate、阿里云百炼 / DashScope 的初始 Adapter 支持；
- Experiment、Asset、PromptTemplate、Evaluation、CostRecord、InvocationLog、Task、Project、ProjectItem、ScriptVersion、Shot、VoiceProfile 等数据模型；
- Voice Lab TTS API 和基于 VoiceProfile 的 TTS；
- Audio Lab STT 与声音克隆 API；
- Image Lab 文生图 API；
- 基于异步任务的 Video Lab API；
- Asset 存储、下载、上传、discard/delete 规则和存储检查；
- Evaluation 和 Compare API；
- 成本估算与 Invocation Log API；
- 项目组织和安全 manifest 导出；
- 用于敏感字段和 signed URL 脱敏的 SanitizerService；
- 覆盖主要工作台视图的浏览器前端。

## 当前尚未包含

以下能力尚未完整实现：

- 已经 live 验证的真实视频 Provider 生产工作流；
- 已经 live 验证的阿里云百炼 / DashScope 语音端点。代码路径已实现，并有 mocked HTTP 测试覆盖，但真实凭证、工作空间权限、endpoint path 和计费仍需由具体部署环境验证；
- Provider webhook 签名校验与公网回调处理；
- 图片编辑、图片变体、参考图工作流；
- 通过 UI 加密保存本地 API Key；
- 完整语音克隆和授权管理 UI。后端已有 VoiceProfile 治理能力，但前端流程仍是受限版本；
- 多用户、RBAC 和团队协作；
- zip 包、剪辑软件工程等项目打包导出；
- 生产级计费。当前 CostRecord 仅用于成本估算。

## 快速开始

环境要求：

- Docker 和 Docker Compose；
- 可选：Python 3.11，用于本地后端测试；
- 可选：Node.js 20+，用于前端 smoke test。

启动默认服务：

```bash
docker compose up --build
```

访问：

- 前端：http://localhost:8501
- 后端健康检查：http://localhost:8000/api/system/health

如果宿主机端口已被占用：

```bash
AIWM_API_PUBLISHED_PORT=18080 AIWM_WEB_PUBLISHED_PORT=18501 docker compose up --build
```

启动包含 Redis 和 Celery worker 的异步 profile：

```bash
docker compose --profile async up --build
```

## Provider 凭证

前端不应保存 Provider API Key。Provider 记录只配置凭证引用，例如：

- `credential_source=docker_secret`
- `credential_ref=openai_api_key`
- `credential_file=/run/secrets/openai_api_key`

如需在本地通过 Docker secret 挂载真实凭证，可在 `secrets/` 下创建本地文件，并使用可选 override：

```bash
docker compose -f docker-compose.yml -f docker-compose.secrets.example.yml --profile async up --build
```

不要提交真实凭证文件。

### 阿里云百炼 / DashScope

后端已包含可选的 `bailian` Adapter，用于接入阿里云百炼 / DashScope 语音相关能力。该 Provider 默认禁用，凭证引用名称为 `dashscope_api_key`。

典型配置方式：

```bash
printf '%s' "$DASHSCOPE_API_KEY" > secrets/dashscope_api_key
docker compose -f docker-compose.yml -f docker-compose.secrets.example.yml --profile async up --build
```

然后通过后端 API seed 或创建 Provider / Model 记录：

```bash
curl -X POST http://localhost:8000/api/providers/seed-defaults
curl -X POST 'http://localhost:8000/api/models/seed-bailian?provider_id=<bailian_provider_id>'
```

seed 出来的百炼模型默认是 disabled。启用前请先在百炼工作空间确认地域 `api_base`、模型 ID 和 endpoint path。语音识别与声音克隆 Adapter 会通过后端内部的 runtime-only 文件传递机制上传音频，本地文件路径不会写入 `Experiment` 或日志。

## 开发

安装后端依赖：

```bash
pip install -r backend/requirements.txt
```

运行后端测试：

```bash
PYTHONPATH=. python -m pytest tests -q
```

对本地数据库运行 Alembic migration：

```bash
AIWM_DATABASE_URL=sqlite:////tmp/aiwm-dev.db python -m alembic upgrade head
```

运行前端 smoke test：

```bash
node --test tests/frontend/*.test.js
```

验证 Compose 配置：

```bash
docker compose config
docker compose --profile async config
```

## 存储模型

生成文件存储在 Docker workspace volume 中，容器内挂载路径为 `/app/workspace`。Asset 记录保存相对路径，不保存宿主机绝对路径。下载应通过后端 Asset API 完成。

## 安全注意事项

- 不要提交真实 API Key、token、密码、私钥、Provider signed URL 或本地数据库文件。
- 前端只调用本项目后端 API，不应直接调用外部 AI Provider。
- Provider 凭证必须通过 `CredentialResolver` 读取。
- Adapter 只应返回临时文件或 source URL。
- 最终 Asset 持久化由 `AssetService` 负责。
- 敏感响应载荷在存储或导出前应经过 `SanitizerService`。
- 默认数据库密码仅用于本地开发。共享或部署环境必须覆盖。

## 命名与兼容性

公开项目名和仓库名为 `narra-studio`。部分内部环境变量仍保留历史 `AIWM_` 前缀，用于兼容已有本地部署。

## 开源边界

内部产品文档和技术设计文档不属于开源发布内容。公开文档应使用 README、`docs/ROADMAP.md`、`docs/ARCHITECTURE_OVERVIEW.md` 等文件表达。

## License

本项目使用 MIT License。详见 [LICENSE](LICENSE)。
