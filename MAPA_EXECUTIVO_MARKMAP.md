# Printora - Mapa executivo

## Modelo IA

### Fonte de verdade

- `PATHS.toml`
- `QUALITY_ROADMAP.md`
- `GOVERNANCA.md`
- `DEMANDAS.md`

### Monorepo

- Raiz governa regras transversais
- Backend FastAPI
- Frontend Vite/React
- `./check.sh` na raiz

### Qualidade

- SOLID
- Separacao de responsabilidades
- CRUD separado por tela
- Teste proporcional ao risco
- Commit no fechamento de pacote

### Operacao

- Read-only por padrao
- Backup antes de mutacao
- Sem migrations
- SQL idempotente
- Rollback documentado
