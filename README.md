# MayderPrintLab

Klipper firmware, maintenance and diagnostics toolkit.

MayderPrintLab será uma aplicação externa para Klipper/Moonraker/Mainsail, com foco em:

- saúde da impressora;
- auditoria de configuração;
- backups;
- CAN;
- primeira camada e Z-offset;
- manutenção preventiva;
- gestão de plugins;
- firmware de MCUs;
- relatórios sanitizados.

Leia primeiro:

1. `CODEX_PATHS.toml`
2. `ESCOPO.md`
3. `QUALITY_ROADMAP.md`
4. `GOVERNANCA.md`
5. `DEMANDAS.md`

Check local:

```bash
./check.sh
```

## MVP Atual

O MVP inicial contém:

- backend FastAPI em `backend/`;
- frontend React/TypeScript em `frontend/`;
- SQLite preparado em `~/.local/share/mayderprintlab`;
- endpoints somente leitura para Moonraker;
- checklist pós-update básico;
- auditoria somente leitura com classificação de achados;
- template systemd em `packaging/systemd/`.

Endpoints iniciais:

- `GET /health`
- `GET /api/moonraker/status`
- `GET /api/checklist/post-update`
- `GET /api/audit/read-only`
- `GET /api/audit/host-read-only`

## Auditoria Do Host

O coletor do host é read-only e vem desabilitado por padrão.

Configuração por ambiente:

```bash
MAYDER_PRINT_LAB_HOST_AUDIT_MODE=disabled
MAYDER_PRINT_LAB_HOST_AUDIT_MODE=local
MAYDER_PRINT_LAB_HOST_AUDIT_MODE=ssh
MAYDER_PRINT_LAB_HOST_AUDIT_SSH_TARGET=pi@voron.local
```

Regras:

- não envia G-code;
- não reinicia serviços;
- não edita arquivos;
- não executa update;
- não faz flash;
- não armazena senha.

Em produção na Raspberry, o modo recomendado é `local`. Em desenvolvimento fora da Raspberry, usar `ssh` apenas com chave SSH configurada.

Backend local:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8085 --reload
```

Frontend local:

```bash
cd frontend
npm install
npm run dev
```
