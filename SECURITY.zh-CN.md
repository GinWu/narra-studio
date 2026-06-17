# 安全政策

English version: [SECURITY.md](SECURITY.md)

## 支持版本

本项目仍处于早期阶段。除非后续引入 release branch 策略，安全修复默认应用到主分支。

## 报告安全漏洞

请不要通过公开 issue 披露密钥泄露、凭证处理缺陷、路径穿越、不安全下载、Provider 回调漏洞等细节。

请优先通过仓库维护者提供的私密渠道报告。如果暂时没有私密渠道，请创建一个不包含漏洞细节的公开 issue，请求维护者提供私密披露联系方式。

## 凭证处理规则

- 不要提交真实 API Key、Provider token、密码、私钥或 signed URL。
- 前端代码不得保存 Provider 密钥。
- Provider 凭证必须由后端 `CredentialResolver` 解析。
- Adapter 代码不得直接读取环境变量或 Docker secrets。
- 日志、Task payload、Experiment、InvocationLog 和导出内容不得包含原始凭证。

## 本地开发密钥

本地 Docker secret 文件可以放在 `secrets/` 下；该目录除说明占位文件外会被忽略。请将 `secrets/` 下的任何文件都视为私有本地状态。

## 范围说明

CostRecord 仅为估算，不用于商业结算。本项目当前尚未提供多用户权限控制或 RBAC。
