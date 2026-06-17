# Docker Secrets

Place local secret files here only for development. Real secret files are ignored by git.

Recommended names:

- `openai_api_key`
- `elevenlabs_api_key`
- `dashscope_api_key`
- `fal_key`
- `replicate_api_token`
- `postgres_password`

Provider rows should store only `credential_source`, `credential_ref`, `credential_file`, and `masked_credential`.

To validate Docker secret mounts when real credentials are available, create the
secret files locally and run:

```bash
docker compose -f docker-compose.yml -f docker-compose.secrets.example.yml up --build
```

The optional override mounts secrets only into `api` and `worker`, never into
`web`.
