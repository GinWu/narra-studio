# 架构概览

English version: [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)

Narra Studio 采用 Docker-first 架构。

## 运行服务

默认 profile：

- `web`：浏览器 UI；
- `api`：FastAPI 后端；
- `db`：PostgreSQL；
- `workspace`：用于生成资产和导出的 Docker volume。

异步 profile：

- `redis`：Celery broker/backend；
- `worker`：处理异步任务的 Celery worker。

## 后端分层

后端将 Provider 差异隔离在 Adapter 边界内：

- Provider 记录描述供应商和凭证引用。
- Model 记录描述具体能力和默认参数。
- CredentialResolver 从批准的后端来源读取凭证。
- Capability Adapter 归一化不同 Provider API 的差异。
- CapabilityRunService 创建 Experiment、调用 Adapter、处理错误，并协调 Asset/Cost/Log hook。
- AssetService 将下载或移动生成文件到最终 workspace 存储。
- Audio Lab 通过 runtime-only 文件引用将已有音频 Asset 传给 Provider Adapter，这些本地路径不会持久化到 Experiment 或日志。

## 核心事实对象

- `Experiment`：一次模型调用事实。
- `Asset`：生成或上传的素材事实。
- `PromptTemplate`：可复用 Prompt 内容和版本元数据。
- `Evaluation`：人工评价事实。
- `CostRecord`：成本估算事实。
- `InvocationLog`：调用摘要日志。
- `Task`：异步执行状态事实。
- `Project` 和 `ProjectItem`：组织有用素材和实验结果的项目层。
- `VoiceProfile`：受治理的 Provider 声音身份，用于 VoiceProfile TTS。

## 安全边界

- 前端只调用本项目后端 API。
- 前端不持有 Provider API Key。
- Adapter 不创建最终 Asset。
- Adapter 不直接读取环境变量或 Docker secrets。
- workspace 资产路径在记录中使用相对路径。
- runtime-only 本地文件引用不得持久化。
- SanitizerService 负责在持久化或导出前脱敏敏感载荷。
