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
- template systemd em `packaging/systemd/`.

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
