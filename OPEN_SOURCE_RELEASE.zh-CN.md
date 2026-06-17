# 开源发布检查清单

English version: [OPEN_SOURCE_RELEASE.md](OPEN_SOURCE_RELEASE.md)

发布仓库或源码包前，请使用本清单检查。

## 必须排除

- `docs/prd/`
- `docs/tds/`
- `docs/internal/`
- `docs/implementation/`
- `.agents/`
- `.codex/`
- `.venv/` 或 `venv/` 等本地虚拟环境
- `.env`
- `secrets/` 下的本地密钥文件
- 生成的 workspace 资产和导出文件
- 本地日志、临时输出、覆盖率文件和运行状态文件
- Python 缓存和 pytest 缓存
- 本地数据库文件

## 建议检查命令

```bash
rg -n '/home/|/Users/' .
rg -n '[A-Za-z]:\\\\' .
rg -n -i "api[_-]?key|token|secret|password|bearer|authorization|sk-|ghp_|github_pat_|AKIA" .
find . -type d -name "__pycache__" -print
find . -type d \( -name ".agents" -o -name ".codex" -o -name ".venv" -o -name "venv" \) -print
find . -type f \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.log" -o -name "*.out" -o -name "*.err" -o -name "*.pid" -o -name "*.tmp" -o -name "*.pem" -o -name "*.key" \) -print
```

请人工复核命中项。测试 fixture 中可能刻意包含 `secret-token` 这类假值。

## 构建与测试

```bash
PYTHONPATH=. python -m pytest tests -q
node --test tests/frontend/*.test.js
docker compose config
docker compose --profile async config
```

## 文档

公开文档应包含：

- `README.md` / `README.zh-CN.md`
- `LICENSE`
- `SECURITY.md` / `SECURITY.zh-CN.md`
- `CONTRIBUTING.md` / `CONTRIBUTING.zh-CN.md`
- `docs/ROADMAP.md` / `docs/ROADMAP.zh-CN.md`
- `docs/ARCHITECTURE_OVERVIEW.md` / `docs/ARCHITECTURE_OVERVIEW.zh-CN.md`
