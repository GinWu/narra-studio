# 路线图

English version: [ROADMAP.md](ROADMAP.md)

本路线图只描述公开层面的产品方向，不承诺具体交付日期。

## 当前重点

- 本地 Docker-first 的媒体模型 Studio。
- 覆盖音频、图片、视频实验的 Mock-first 端到端工作流。
- Experiment、Asset、Prompt、Evaluation、Cost、Log、Task、Project 记录。
- 安全的 Provider 凭证引用和后端统一 Provider 调用。
- Audio Lab 后端已具备 STT、声音克隆和基于 VoiceProfile 的 TTS 初始能力。

## 近期改进

- 对选定真实 Provider Adapter 做 live 验证和校准，包括阿里云百炼 / DashScope 语音端点。
- 强化选定 TTS、STT、声音克隆和图片生成 Provider 的真实 Adapter。
- 改进异步视频 Provider 支持和轮询。
- 丰富 PromptTemplate、Evaluation、Cost、Project Workspace 等前端工作流。
- 增加异步视频生成的 Docker 端到端 smoke test。
- 改进公开文档和安装体验。

## 后续想法

- 图片编辑、图片变体、参考图工作流。
- 更完整的 VoiceProfile 与语音克隆授权 UI 工作流。
- 带签名校验与重放保护的 Provider webhook。
- 项目素材包导出。
- 团队协作、账号、RBAC 和审计日志。
- 可选的本地加密凭证存储。

## 当前非目标

- 商业结算。
- 全自动内容生产流水线。
- 前端直接调用外部 AI Provider。
