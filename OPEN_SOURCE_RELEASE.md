# Open-Source Release Checklist

中文版本见 [OPEN_SOURCE_RELEASE.zh-CN.md](OPEN_SOURCE_RELEASE.zh-CN.md).

Use this checklist before publishing a repository or source archive.

## Must Exclude

- `docs/prd/`
- `docs/tds/`
- `docs/internal/`
- `docs/implementation/`
- `.agents/`
- `.codex/`
- local virtual environments such as `.venv/` or `venv/`
- `.env`
- local secret files under `secrets/`
- generated workspace assets and exports
- local logs, temporary outputs, coverage files, and runtime state
- Python caches and pytest caches
- local database files

## Suggested Checks

```bash
rg -n '/home/|/Users/' .
rg -n '[A-Za-z]:\\\\' .
rg -n -i "api[_-]?key|token|secret|password|bearer|authorization|sk-|ghp_|github_pat_|AKIA" .
find . -type d -name "__pycache__" -print
find . -type d \( -name ".agents" -o -name ".codex" -o -name ".venv" -o -name "venv" \) -print
find . -type f \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.log" -o -name "*.out" -o -name "*.err" -o -name "*.pid" -o -name "*.tmp" -o -name "*.pem" -o -name "*.key" \) -print
```

Review matches manually. Test fixtures may intentionally contain fake values such as `secret-token`.

## Build and Test

```bash
PYTHONPATH=. python -m pytest tests -q
node --test tests/frontend/*.test.js
docker compose config
docker compose --profile async config
```

## Documentation

Public documentation should include:

- `README.md`
- `LICENSE`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `docs/ROADMAP.md`
- `docs/ARCHITECTURE_OVERVIEW.md`
