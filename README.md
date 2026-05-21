# Printora

Klipper firmware, maintenance and diagnostics toolkit.

Printora será uma aplicação externa para Klipper/Moonraker/Mainsail, com foco em:

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

Abrir local no macOS/Linux:

```bash
./scripts/run_app.sh
```

Também existe o atalho clicável `Abrir Printora.command` na raiz do projeto. Ele prepara o ambiente local quando necessário, inicia o backend em `http://127.0.0.1:8085` e abre o navegador. A janela do terminal deve ficar aberta enquanto o app estiver em uso.

Abrir local no Windows:

```powershell
.\scripts\run_app_windows.ps1
```

Também existe o atalho clicável `Abrir Printora.bat` na raiz do projeto. Ele prepara o ambiente local quando necessário, inicia o backend em `http://127.0.0.1:8085` e abre o navegador. A janela do PowerShell deve ficar aberta enquanto o app estiver em uso.

## MVP Atual

O MVP inicial contém:

- backend FastAPI em `backend/`;
- frontend React/TypeScript em `frontend/`;
- SQLite preparado em `~/.local/share/printora`;
- cadastro local de múltiplas impressoras;
- endpoints somente leitura para Moonraker;
- checklist pós-update básico;
- health check por impressora;
- políticas de backup e dry-run seguro;
- relatório Markdown sanitizado por impressora;
- diário de manutenção e tarefas preventivas por impressora;
- registro manual de Z-offset por chapa/material/nozzle;
- wizard manual de Z-offset;
- registro manual/read-only de saúde CAN;
- auditoria read-only de mods e plugins;
- cadastro local de placas e presets de firmware;
- dry-run planejado de build de firmware;
- dry-run planejado de flash de firmware;
- catálogo read-only de calibrações e testes Voron/Klipper;
- auditoria somente leitura com classificação de achados;
- backend servindo frontend buildado quando `frontend/dist` existe;
- templates de integração em `packaging/`;
- instalador Raspberry com dry-run em `scripts/install_raspberry.sh`.

Endpoints iniciais:

- `GET /health`
- `GET /api/printers`
- `POST /api/printers`
- `PUT /api/printers/{printer_id}`
- `GET /api/printers/{printer_id}/moonraker/status`
- `GET /api/printers/{printer_id}/health`
- `GET /api/printers/{printer_id}/reports/sanitized`
- `GET /api/printers/{printer_id}/backup/policies`
- `POST /api/printers/{printer_id}/backup/policies`
- `GET /api/printers/{printer_id}/backup/runs`
- `POST /api/backup/policies/{policy_id}/dry-run`
- `POST /api/backup/policies/{policy_id}/execute-local`
- `GET /api/printers/{printer_id}/maintenance/events`
- `POST /api/printers/{printer_id}/maintenance/events`
- `GET /api/printers/{printer_id}/maintenance/tasks`
- `POST /api/printers/{printer_id}/maintenance/tasks`
- `POST /api/maintenance/tasks/{task_id}/complete`
- `GET /api/printers/{printer_id}/z-offsets`
- `POST /api/printers/{printer_id}/z-offsets`
- `GET /api/printers/{printer_id}/z-offsets/wizard-plan`
- `GET /api/printers/{printer_id}/can/records`
- `POST /api/printers/{printer_id}/can/records`
- `GET /api/printers/{printer_id}/plugins/audit`
- `GET /api/firmware/board-presets`
- `GET /api/printers/{printer_id}/firmware/boards`
- `POST /api/printers/{printer_id}/firmware/boards`
- `GET /api/printers/{printer_id}/firmware/build-runs`
- `POST /api/firmware/boards/{board_id}/build-runs/dry-run`
- `POST /api/firmware/boards/{board_id}/build-runs/execute-local`
- `GET /api/printers/{printer_id}/firmware/flash-runs`
- `POST /api/firmware/boards/{board_id}/flash-runs/dry-run`
- `GET /api/calibration/tests`
- `GET /api/calibration/tests/{test_key}`
- `GET /api/printers/{printer_id}/calibration/runs`
- `POST /api/printers/{printer_id}/calibration/runs`
- `POST /api/printers/{printer_id}/snapshots/moonraker`
- `GET /api/printers/{printer_id}/snapshots`
- `GET /api/printers/{printer_id}/snapshots/diff?from_id=...&to_id=...`
- `GET /api/snapshots/{snapshot_id}`
- `GET /api/moonraker/status`
- `GET /api/checklist/post-update`
- `GET /api/audit/read-only`
- `GET /api/audit/host-read-only`

## Integração Raspberry/Mainsail/Moonraker

Artefatos principais:

- `packaging/systemd/printora.service`
- `packaging/env/printora.env.example`
- `packaging/mainsail/navi.json`
- `packaging/moonraker/update_manager_printora.conf`
- `scripts/install_raspberry.sh`
- `docs/INSTALL_RASPBERRY.md`
- `docs/INSTALL_MULTIPLATFORM.md`

O instalador roda em dry-run por padrão:

```bash
./scripts/install_raspberry.sh
```

Para aplicar em uma Raspberry depois de revisar:

```bash
./scripts/install_raspberry.sh --apply
```

O script não inicia o serviço automaticamente. Revise `.env` antes:

```bash
sudo systemctl start printora.service
curl -s http://127.0.0.1:8085/health
```

## Instalação Multiplataforma

Roteiro completo:

```text
docs/INSTALL_MULTIPLATFORM.md
```

Atalhos:

```bash
# macOS/Linux dev, dry-run
./scripts/bootstrap_dev.sh

# macOS/Linux dev, aplicar
./scripts/bootstrap_dev.sh --apply

# macOS/Linux, iniciar e abrir app local
./scripts/run_app.sh

# Windows, iniciar e abrir app local
.\scripts\run_app_windows.ps1

# Raspberry/Manta/Linux systemd, dry-run
./scripts/install_raspberry.sh

# Docker
docker compose up --build
```

Windows PowerShell:

```powershell
.\scripts\bootstrap_windows.ps1
.\scripts\bootstrap_windows.ps1 --apply
```

## Múltiplas Impressoras

O banco SQLite já suporta várias impressoras no mesmo Printora.

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

## Backups

O primeiro incremento de backups é propositalmente conservador.

Ele permite:

- criar políticas por impressora;
- definir origem e destino;
- usar padrões de inclusão/exclusão;
- registrar dry-run no histórico.

Ele ainda não:

- apaga arquivos;
- restaura arquivos;
- acessa a Raspberry por SSH.

Endpoint principal:

```text
POST /api/backup/policies/{policy_id}/dry-run
```

O resultado `dry_run_planned` documenta o que seria feito em etapa futura, sem executar a operação real.

Execução local:

```text
POST /api/backup/policies/{policy_id}/execute-local
```

Regras:

- só executa quando a política não está marcada como `dry_run_only`;
- só usa caminhos locais do host onde o backend está rodando;
- cria `.zip` no destino;
- bloqueia destino dentro da origem;
- registra resultado no histórico.

## Relatórios Sanitizados

O relatório sanitizado gera Markdown read-only para suporte/comunidade.

Endpoint:

```text
GET /api/printers/{printer_id}/reports/sanitized
```

Inclui:

- resumo da impressora;
- decisão do health check;
- itens de ação;
- snapshots recentes;
- última comparação de snapshots;
- histórico recente de backups.

Sanitização aplicada:

- URLs;
- IPs;
- caminhos locais em `/home/...`;
- valores detectáveis de senha, token, chave e segredo.

O relatório deve ser revisado antes de ser publicado fora da rede local.

## Manutenção

O módulo de manutenção registra histórico local por impressora.

Eventos suportados:

- manutenção;
- falha;
- ajuste;
- nota.

Tarefas preventivas:

- nome;
- componente;
- intervalo em dias;
- última execução;
- status `pendente`, `em dia` ou `desconhecido`.

Concluir uma tarefa preventiva cria automaticamente um evento no diário e atualiza `last_done_at`.

O módulo não envia G-code, não reinicia serviços e não altera configuração da impressora.

## Z-offset

O registro manual de Z-offset guarda histórico por impressora, chapa, material e nozzle/toolhead.

Campos principais:

- chapa;
- material;
- nozzle/toolhead;
- valor do Z-offset;
- valor anterior compatível;
- delta;
- alerta;
- notas.

Alertas:

- `ok`: diferença menor que `0.05`;
- `monitorar`: diferença a partir de `0.05`;
- `revisar`: diferença a partir de `0.10`.

Este módulo não executa `PROBE_CALIBRATE`, não envia G-code e não altera `printer.cfg`.

O wizard manual gera um roteiro seguro com comandos sugeridos, checklist e recomendação baseada no delta do valor anterior. Ele não executa os comandos pelo usuário.

## Monitor CAN

O Monitor CAN registra leituras manuais por impressora e interface.

Campos principais:

- interface, por exemplo `can0`;
- `rx_error`;
- `tx_error`;
- `tx_retries`;
- estado do barramento;
- bitrate;
- notas.

Alertas:

- `ok`: sem erro e sem delta relevante;
- `monitorar`: contador absoluto de erro existe ou `tx_retries` subiu;
- `problema`: `rx_error` ou `tx_error` subiu desde a leitura anterior.

Este módulo não executa `ip`, não acessa SSH, não zera contadores CAN e não reinicia serviços. A leitura real continua sendo feita pelo usuário ou por um coletor futuro.

## Mods E Plugins

A auditoria de mods e plugins usa o último snapshot Moonraker/Update Manager.

Itens do catálogo inicial:

- KAMP / adaptive meshing;
- KTC-Easy / StealthChanger;
- `led_effect`;
- Crowsnest;
- Sonar;
- Timelapse;
- Auto Speed;
- TapChanger antigo;
- TMC Autotune.

Classificações:

- necessário;
- opcional;
- legado/lixo técnico;
- perigoso remover agora;
- seguro remover depois de backup;
- precisa confirmação.

Endpoint:

```text
GET /api/printers/{printer_id}/plugins/audit
```

Este módulo é read-only. Ele não remove repositórios, não edita `moonraker.conf`, não reinicia serviços e não altera configurações Klipper.

## Firmware Manager

O primeiro incremento do Firmware Manager é apenas cadastro local.

Ele permite:

- listar presets de placas comuns no ecossistema Voron/Klipper;
- cadastrar placas por impressora;
- guardar UUID CAN, interface CAN, arquivo `.config`, MCU e método futuro de flash;
- preparar o inventário para build/dry-run em etapa futura.

Presets iniciais:

- BTT Octopus/Octopus Pro F446/H723;
- BTT EBB36/EBB42;
- BTT SB2209/SB2240;
- Mellow Fly SHT36/SB2040;
- Fysetc Spider;
- Fysetc SB CAN.

Endpoints:

```text
GET /api/firmware/board-presets
GET /api/printers/{printer_id}/firmware/boards
POST /api/printers/{printer_id}/firmware/boards
```

Esta etapa não compila firmware, não faz flash, não acessa SSH, não reinicia serviços e não altera Klipper.

### Build Dry-Run

O build dry-run registra o que seria feito para compilar firmware de uma placa cadastrada.

Ele salva:

- caminho do Klipper;
- diretório planejado de output;
- backup planejado da `.config`;
- caminho planejado do binário;
- checklist pré-build;
- comandos planejados.

Endpoints:

```text
GET /api/printers/{printer_id}/firmware/build-runs
POST /api/firmware/boards/{board_id}/build-runs/dry-run
```

O dry-run não executa `make`, não copia arquivos, não cria diretórios, não acessa SSH, não reinicia serviços e não faz flash.

### Build Local Controlado

O executor local fica bloqueado por padrão.

Para habilitar em uma instalação local controlada:

```bash
PRINTORA_FIRMWARE_BUILD_MODE=local
```

Mesmo habilitado, a chamada exige confirmação textual:

```text
EXECUTE_LOCAL_BUILD_NO_FLASH
```

O fluxo local:

- cria diretório de saída;
- faz backup da `.config`;
- roda `make clean`;
- copia a config cadastrada para `.config`;
- roda `make`;
- copia o binário gerado;
- restaura a `.config` original;
- registra resultado no histórico.

Ele não faz flash, não reinicia serviços e não acessa SSH.

### Flash Dry-Run

O flash dry-run registra o plano de flash de uma placa cadastrada, sem executar comandos.

Ele salva:

- método de flash da placa;
- UUID CAN esperado;
- interface CAN;
- binário planejado;
- checklist pré-flash;
- comandos que seriam usados em uma etapa futura.

Endpoints:

```text
GET /api/printers/{printer_id}/firmware/flash-runs
POST /api/firmware/boards/{board_id}/flash-runs/dry-run
```

Esta etapa não faz flash, não reinicia Klipper, não acessa SSH, não valida MCU ao vivo e não altera a impressora. O objetivo é revisar o procedimento antes de liberar qualquer execução real.

## Calibração E Testes

O catálogo inicial lista testes e calibrações comuns para Voron/Klipper sem executar nada.

Cada item guarda:

- categoria;
- objetivo;
- fonte;
- modo de execução;
- nível de risco;
- se deve bloquear durante impressão;
- pré-condições;
- G-code sugerido para revisão futura;
- critérios de sucesso;
- notas.

Modos de execução:

- `read_only`;
- `manual`;
- `gcode_review_required`;
- `blocked_while_printing`.

Endpoints:

```text
GET /api/calibration/tests
GET /api/calibration/tests?category=qualidade
GET /api/calibration/tests/{test_key}
```

Esta etapa não envia G-code, não reinicia serviços, não altera configs e não conversa com a impressora. O objetivo é organizar conhecimento operacional antes de permitir execução guiada.

### Histórico Manual De Calibração

O histórico permite registrar resultado manual por impressora:

- teste executado;
- aprovado, atenção, falhou ou ignorado;
- material;
- chapa;
- nozzle/tool;
- valor observado;
- confirmação de G-code revisado;
- notas.

Endpoints:

```text
GET /api/printers/{printer_id}/calibration/runs
POST /api/printers/{printer_id}/calibration/runs
```

Este registro não executa o teste. Ele apenas documenta o que o operador fez fisicamente ou via Mainsail/console fora do Printora.

## Auditoria Do Host

O coletor do host é read-only e vem desabilitado por padrão.

Configuração por ambiente:

```bash
PRINTORA_HOST_AUDIT_MODE=disabled
PRINTORA_HOST_AUDIT_MODE=local
PRINTORA_HOST_AUDIT_MODE=ssh
PRINTORA_HOST_AUDIT_SSH_TARGET=pi@voron.local
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
