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
- cadastro local de múltiplas impressoras;
- endpoints somente leitura para Moonraker;
- checklist pós-update básico;
- health check por impressora;
- auditoria somente leitura com classificação de achados;
- template systemd em `packaging/systemd/`.

Endpoints iniciais:

- `GET /health`
- `GET /api/printers`
- `POST /api/printers`
- `PUT /api/printers/{printer_id}`
- `GET /api/printers/{printer_id}/moonraker/status`
- `GET /api/printers/{printer_id}/health`
- `POST /api/printers/{printer_id}/snapshots/moonraker`
- `GET /api/printers/{printer_id}/snapshots`
- `GET /api/printers/{printer_id}/snapshots/diff?from_id=...&to_id=...`
- `GET /api/snapshots/{snapshot_id}`
- `GET /api/moonraker/status`
- `GET /api/checklist/post-update`
- `GET /api/audit/read-only`
- `GET /api/audit/host-read-only`

## Múltiplas Impressoras

O banco SQLite já suporta várias impressoras no mesmo MayderPrintLab.

Campos principais:

- nome;
- URL do Moonraker;
- modo da auditoria do host;
- alvo SSH opcional;
- localização;
- notas.

Isso permite dois modelos de uso:

- instalado em uma Raspberry, cuidando da impressora local;
- instalado em um computador da rede, centralizando várias impressoras Klipper.

O cadastro não armazena credenciais. Acesso SSH, quando usado no futuro, deve depender de chave SSH do sistema.

## Snapshots

Snapshots salvam leituras read-only para histórico e desenvolvimento offline.

O primeiro tipo suportado é `moonraker_status`, com:

- `printer/info`;
- `server/info`;
- `machine/update/status`;
- `machine/system_info`;
- `machine/proc_stats`.

A listagem retorna resumo. O payload completo fica disponível em `GET /api/snapshots/{snapshot_id}`.

Snapshots também podem ser comparados sem executar ações na impressora:

```text
GET /api/printers/{printer_id}/snapshots/diff?from_id={base}&to_id={atual}
```

A comparação destaca estado Klipper, versões, warnings, componentes Moonraker com falha, repos `dirty`, versões do Update Manager e variações relevantes de temperatura do host.

## Health Check

O health check consolida leituras read-only por impressora:

- estado Klipper;
- conexão Moonraker;
- componentes e warnings;
- Update Manager;
- temperatura do host;
- espaço livre quando disponível;
- snapshots recentes;
- última comparação entre snapshots.

Resultado:

```text
OK para imprimir
Pode imprimir com atenção
Não imprima ainda
```

Endpoint:

```text
GET /api/printers/{printer_id}/health
```

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
