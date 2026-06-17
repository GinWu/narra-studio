# 贡献指南

English version: [CONTRIBUTING.md](CONTRIBUTING.md)

感谢你关注 Narra Studio。

## 开发原则

- 保持后端 Docker-first。
- 不要让 Provider 凭证进入前端代码。
- 使用 `CredentialResolver` 读取密钥。
- 使用 `CapabilityRunService` 发起模型调用。
- Adapter 只返回临时文件或 source URL。
- `AssetService` 负责创建最终资产。
- 不要将生成文件提交到 Git。

## 环境准备

```bash
pip install -r backend/requirements.txt
```

运行后端测试：

```bash
PYTHONPATH=. python -m pytest tests -q
```

运行前端 smoke test：

```bash
node --test tests/frontend/*.test.js
```

验证 Docker Compose：

```bash
docker compose config
docker compose --profile async config
```

## 提交 Pull Request 前

- 不要包含真实密钥或本地数据。
- 不要包含内部 PRD/TDS 文档。
- 运行相关测试。
- 行为变化时更新 README 或公开文档。
- 新增 service、adapter、task 或 API 行为时补充测试。

## 文档边界

内部产品文档和技术设计文档不属于开源发布内容。公开设计说明应以高层形式写入 `docs/`。
