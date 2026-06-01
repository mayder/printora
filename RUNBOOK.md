# RUNBOOK.md

Runbook operacional do Printora.

## Comandos principais

```bash
./check.sh
```

O `check.sh` da raiz e o ponto oficial de validacao do monorepo. Ele valida o modelo, compila o backend, valida o pacote frontend e executa checks leves por padrao.

## Desenvolvimento local

Backend:

```bash
./scripts/dev_backend.sh
```

Frontend:

```bash
./scripts/dev_frontend.sh
```

Aplicacao completa:

```bash
./scripts/run_app.sh
```

Diagnostico de instalacao:

```bash
PRINTORA_PORT=8069 ./scripts/doctor_install.sh
```

Em ambiente cloud, esse diagnostico nao fica na tela global. Para host de
impressora, use `Detalhe do agente > Doctor remoto`; para diagnostico local do
servidor, use o script acima no host da instalacao.

Setup do Zero via SSH:

```bash
curl -s -X POST http://127.0.0.1:8069/api/setup/ssh/preflight \
  -H 'Content-Type: application/json' \
  -d '{"host":"btt-pi.local","port":22,"username":"pi","auth_method":"agent","timeout_seconds":12}'

curl -s -X POST http://127.0.0.1:8069/api/setup/ssh/plan \
  -H 'Content-Type: application/json' \
  -d '{"host":"btt-pi.local","port":22,"username":"pi","auth_method":"agent","timeout_seconds":12}'

curl -s http://127.0.0.1:8069/api/setup/ssh/history
```

O PKG-34 exige que a Pi ja tenha Linux, rede e SSH ativo. Placa virgem sem
sistema operacional nao pode ser acessada por SSH; primeiro grave a mídia/boot,
habilite SSH e confirme o primeiro login. O preflight coleta somente dados
read-only. O plano retorna comandos prefixados por `PLAN` e nao executa
instalacao real, `apt`, edicao de arquivo, restart, flash, G-code ou alteracao
de Klipper/Moonraker.

Setup CAN/U2C/can0 via SSH:

```bash
curl -s -X POST http://127.0.0.1:8069/api/setup/can/preflight \
  -H 'Content-Type: application/json' \
  -d '{"target":{"host":"btt-pi.local","port":22,"username":"pi","auth_method":"agent","timeout_seconds":12},"interface_name":"can0","bitrate":1000000}'

curl -s -X POST http://127.0.0.1:8069/api/setup/can/plan \
  -H 'Content-Type: application/json' \
  -d '{"target":{"host":"btt-pi.local","port":22,"username":"pi","auth_method":"agent","timeout_seconds":12},"interface_name":"can0","bitrate":1000000}'

curl -s http://127.0.0.1:8069/api/setup/can/history
```

O apply CAN real fica bloqueado por padrão. Para executar em host real, o
processo do backend precisa estar com `PRINTORA_CAN_SETUP_MODE=remote` e o
payload precisa incluir `confirmation=CONFIGURAR CAN0`. Antes de alterar o host,
o backend roda preflight, bloqueia impressão em andamento quando detectável,
exige `sudo -n`, cria backup remoto de `/etc/systemd/system/can0.service` em
`~/.local/share/printora/can-setup/backups/<timestamp>/`, escreve o serviço
`can0.service`, roda `systemctl daemon-reload`, `enable`, `restart` e valida
`ip -details -statistics link show can0`.

Rollback CAN:

```bash
sudo cp ~/.local/share/printora/can-setup/backups/<timestamp>/can0.service.before /etc/systemd/system/can0.service
sudo systemctl daemon-reload
sudo systemctl restart can0.service
ip -details -statistics link show can0
```

Se não havia serviço anterior, o rollback é desabilitar/remover o serviço criado
e recarregar o systemd:

```bash
sudo systemctl disable --now can0.service
sudo rm -f /etc/systemd/system/can0.service
sudo systemctl daemon-reload
```

Wizard remoto de firmware:

```bash
curl -s -X POST http://127.0.0.1:8069/api/setup/firmware/plan \
  -H 'Content-Type: application/json' \
  -d '{"target":{"host":"btt-pi.local","port":22,"username":"pi","auth_method":"agent","timeout_seconds":12},"preset_id":"btt_octopus_pro_h723_usb_can","board_name":"Octopus Pro H723","board_role":"mainboard","can_interface":"can0","klipper_path":"~/klipper","output_root":"~/.local/share/printora/firmware-setup","variant_confirmed":true}'

curl -s http://127.0.0.1:8069/api/setup/firmware/history
```

O build remoto real fica bloqueado por padrão. Para executar em host real, o
processo do backend precisa estar com `PRINTORA_REMOTE_FIRMWARE_BUILD_MODE=remote`
e o payload precisa incluir `confirmation=BUILD_FIRMWARE_NO_FLASH`. O build:

- salva o `.config` gerado em diretório controlado do Printora;
- cria backup de `<klipper_path>/.config`;
- substitui `.config` apenas durante o build;
- executa `make clean && make`;
- copia o binário para os artefatos Printora;
- calcula hash do `.config` e do binário;
- consulta UUIDs CAN quando `~/klippy-env` e `canbus_query.py` existirem;
- restaura `.config` com `trap` em sucesso ou falha;
- nunca executa flash, restart, update, G-code ou edição de `printer.cfg`.

Rollback firmware build:

```bash
cp ~/.local/share/printora/firmware-setup/<placa>/.config.before-build ~/klipper/.config
rm -rf ~/.local/share/printora/firmware-setup/<placa>
```

Instalação com boot automático:

```bash
./scripts/install-macos.sh
./scripts/install-linux.sh
./scripts/install-android-termux.sh
```

No Windows:

```powershell
.\scripts\install-windows.ps1
```

Os instaladores publicos verificam o ambiente, exibem o que ja esta OK e
perguntam antes de instalar dependencias ausentes. O instalador interno
`scripts/install_printora.sh --apply --yes` continua existindo para automacao.
Ele prepara dependencias, usa Node local via `nvm` quando o Node global for
antigo, procura Python 3.11+ sem remover Python antigo do usuario e configura o
mecanismo de boot do ambiente atual. A porta padrao do Printora e `8069`.

Destravar update local orfao:

```bash
./scripts/unlock_update.sh
```

O script cria backup do `printora.db` no mesmo diretorio antes de marcar runs
`running` como `failed`. Em cloud, a UI de `Administracao > Historico da plataforma`
e informativa; reconciliacao de travados e rotina de suporte/admin via script.

Updater local macOS/Linux/Raspberry:

```bash
./scripts/update_printora.sh --plan --tag v0.1.1
./scripts/update_printora.sh --apply --tag v0.1.1
./scripts/update_printora.sh --rollback --previous-path /caminho/Printora.previous-update-YYYYMMDDTHHMMSSZ
```

O script detecta macOS sem systemd, Linux/Raspberry com systemd e Linux sem systemd. Quando `printora.service` existe, reinicia somente esse serviço; sem systemd, tenta `tmux` ou `scripts/run_app.sh`.
Em Linux/Raspberry com systemd, o run pode ser finalizado antes do restart
efetivo, pois o `systemctl restart printora.service` encerra o processo antigo
que iniciou o update. A validacao operacional depois do restart continua sendo
`/openapi.json` ou o historico em `Administracao > Historico da plataforma`.
Os instaladores Linux/Raspberry criam `/etc/sudoers.d/printora-restart` com
permissao minima para o usuario do servico executar `systemctl restart/status
printora.service` sem senha. Isso e necessario para update automatico do app,
porque o backend roda sem terminal interativo.

Log de update iniciado pela UI:

```bash
~/.local/share/printora/logs/self-update-run-<id>.log
```

No Android/Termux, o banco e os backups ficam em `~/.local/share/printora/`.
Se a UI cair durante o restart, consultar `Administracao > Historico da plataforma`
ou enviar esse log junto com o diagnostico local gerado pelo script.

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_app_windows.ps1
```

Updater Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\update_printora_windows.ps1 --Plan --Tag v0.1.1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\update_printora_windows.ps1 --Apply --Tag v0.1.1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\update_printora_windows.ps1 --Rollback --PreviousPath C:\caminho\Printora.previous-update-YYYYMMDDTHHMMSSZ
```

O updater Windows usa apenas escopo de processo para a política de execução, cria backup de `%LOCALAPPDATA%\Printora\printora.db`, preserva a pasta anterior do projeto e reinicia pelo runner Windows.

## Catalogo firmware CANBus

O catalogo do PKG-30 usa o guia Esoterical CANBus como fonte publica, mas o runtime do Printora consulta somente arquivos locais versionados em `backend/app/data/`.

Atualizar manifesto em dry-run:

```bash
python3 scripts/build_canbus_manifest.py --retrieved-at YYYY-MM-DD --timeout 10
```

Gravar manifesto apos revisar o dry-run:

```bash
python3 scripts/build_canbus_manifest.py --write --retrieved-at YYYY-MM-DD --timeout 10
```

Atualizar catalogo local em dry-run:

```bash
cd backend
uv run python ../scripts/build_firmware_catalog.py --manifest ../backend/app/data/firmware_canbus_manifest.json --output ../backend/app/data/firmware_hardware_catalog.json --generated-at YYYY-MM-DD --timeout 12
```

Gravar catalogo apos revisar o dry-run:

```bash
cd backend
uv run python ../scripts/build_firmware_catalog.py --manifest ../backend/app/data/firmware_canbus_manifest.json --output ../backend/app/data/firmware_hardware_catalog.json --generated-at YYYY-MM-DD --timeout 12 --write
```

Validar cobertura e contrato do catalogo:

```bash
cd backend
uv run pytest tests/test_canbus_manifest.py tests/test_firmware.py -q
```

Gerar preview de `.config` de um preset sem salvar arquivo:

```bash
curl -s http://127.0.0.1:8069/api/firmware/board-presets/btt_kraken_h723_usb_can/config-preview
```

O preview de `.config` retorna `content`, `lines`, `config_file`, `build_output` e `artifact_saved=false`. Ele é gerado em memória, não grava arquivo no host, não escreve no diretório Klipper e não executa `make`, flash, SSH, restart ou update.

Preparar dry-run de build de uma placa cadastrada:

```bash
curl -s -X POST http://127.0.0.1:8069/api/firmware/boards/BOARD_ID/build-runs/dry-run \
  -H 'Content-Type: application/json' \
  -d '{"klipper_path":"~/klipper","output_root":"~/printer_data/firmware_builds"}'
```

O dry-run retorna `preset_id`, `preset_build_config_status`, `generated_config_path`, `config_backup_path`, `work_dir`, `expected_build_output`, `binary_output_path`, `log_path`, checklist e comandos `PLAN ...`. Esses comandos são plano revisável, não execução. Preset incompleto bloqueia o dry-run antes de criar histórico.

Executar build pelo agente, sem flash:

```bash
curl -s -X POST http://127.0.0.1:8069/api/firmware/boards/BOARD_ID/build-runs/execute-local \
  -H 'Content-Type: application/json' \
  -d '{"klipper_path":"~/klipper","output_root":"~/.local/share/printora/firmware_builds","confirmation":"EXECUTE_LOCAL_BUILD_NO_FLASH"}'
```

Travas:

- sem confirmação textual exata `EXECUTE_LOCAL_BUILD_NO_FLASH`, o histórico registra `blocked_invalid_build_confirmation`;
- o executor roda no agente pareado, não no servidor da API;
- o executor não faz flash, não reinicia Klipper/Moonraker e não executa update;
- o executor usa apenas o diretório Klipper do host do agente e o `output_root` informado.

Artefatos salvos em `output_root/AGENT/<placa>/`:

- `.config.before-build`: backup da `.config` original;
- `generated/<arquivo>.config`: `.config` determinístico gerado pelo preset;
- `logs/build.log`: saída de `make clean` e `make`, ou erro capturado;
- `<binário>`: cópia do output esperado quando o build termina com sucesso.

Rollback:

- o executor restaura a `.config` original ao final em sucesso ou falha;
- se a operação for interrompida fora do controle do processo, restaurar manualmente `output_root/local-build/<placa>/.config.before-build` para `<klipper_path>/.config`;
- não há flash automático; se o binário gerado estiver incorreto, apagar o diretório de artefatos e repetir depois de corrigir o preset/build config.

Validar fechamento completo do pacote:

```bash
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

## Setup Do Zero - Flash Supervisionado

O flash supervisionado fica em `Setup do Zero > Flash supervisionado` e depende do SSH da Pi, CAN funcional e artefato de firmware gerado/validado.

Fluxo seguro:

1. informar placa, método, artefato remoto, UUID esperado e interface CAN;
2. marcar checklist físico somente após confirmar alimentação, cabos, placa correta, bootloader/Katapult e binário;
3. executar `Preflight flash`;
4. gerar `Plano flash` e revisar bloqueios, comando `PLAN`, frase de confirmação e rollback;
5. para execução real CAN/Katapult, habilitar o backend com `PRINTORA_REMOTE_FLASH_MODE=remote` e digitar exatamente a frase gerada;
6. revisar log, hash, duração e validação pós-flash.

Limites:

- o método real inicial é somente `can_katapult`;
- `usb_dfu` e `manual` ficam bloqueados no backend;
- o fluxo não edita `printer.cfg`, não reinicia Klipper/Moonraker, não executa update e não envia G-code;
- se falhar ou ficar inconclusivo, seguir o rollback manual exibido e colocar a placa novamente em bootloader.

SQL:

- `backend/sql/024_setup_flash_runs.sql` cria histórico local de preflight, plano e execução;
- rollback de schema: restaurar backup `printora.<timestamp>.before-schema.db` criado pelo versionador antes de aplicar scripts pendentes.

## Setup Do Zero - Validação Final

A validação final fica em `Setup do Zero > Validação final` e deve ser executada depois de SSH, CAN, firmware e flash estarem prontos.

O que a validação coleta:

- serviços `klipper`, `moonraker`, `can0` e auxiliares quando `systemctl` existir;
- `server/info`, `printer/info`, `print_stats`, temperaturas e Update Manager via Moonraker local;
- estado da interface CAN;
- UUIDs visíveis e UUIDs referenciados em configs;
- resumo de arquivos `.cfg`, MCUs, includes e identificadores serial/CAN;
- trechos recentes de logs com erros relevantes.

Limites:

- não envia G-code;
- não move eixo;
- não aquece hotend/mesa;
- não reinicia Klipper/Moonraker;
- não altera `printer.cfg` ou includes;
- não executa update.

SQL:

- `backend/sql/025_setup_final_validation_runs.sql` cria histórico local da validação e relatório sanitizado;
- rollback de schema: restaurar backup `printora.<timestamp>.before-schema.db` criado pelo versionador antes de aplicar scripts pendentes.

## Autenticação Cloud E Conta

O desenvolvimento inicial do PKG-39 usa SQLite. A modelagem deve permanecer simples e portátil para migração futura para Postgres quando a operação cloud exigir.

Fluxos:

- cadastro: `POST /api/auth/register` com `email` e `password` obrigatórios; `display_name`, `whatsapp`, `telegram` e `social_links` opcionais;
- login: `POST /api/auth/login`;
- login com 2FA: quando `mfa_required=true`, chamar `POST /api/auth/login/mfa` com `challenge_token` e código;
- sessão atual: `GET /api/auth/me` com `Authorization: Bearer <token>`;
- logout: `POST /api/auth/logout`;
- organização opcional: `POST /api/auth/organizations` e `POST /api/auth/organizations/{id}/members`;
- impressoras: cada registro tem dono e pode ter organização opcional; a API lista apenas impressoras do usuário autenticado ou de organizações das quais ele participa;
- rotas por impressora: antes de ler health, snapshots, operação, manutenção, backup, update, firmware, CAN, calibração, relatórios ou auditoria, a API valida a impressora no escopo do usuário/organização;
- rotas legadas sem `printer_id`: em sessão cloud usam uma impressora visível do usuário; se o usuário não tiver impressora visível, retornam 404 em vez de usar o Moonraker global;
- históricos operacionais: `setup_*_runs` e `app_update_runs` possuem owner e organização opcional para evitar vazamento entre usuários;
- 2FA: `POST /api/auth/mfa/setup`, `POST /api/auth/mfa/enable` e `POST /api/auth/mfa/disable`;
- step-up auth: `POST /api/auth/step-up` antes de ações destrutivas quando houver sessão autenticada;
- credencial de agente: `POST /api/auth/agent-credentials`, retornada completa somente uma vez.

## Gestão Cloud De Impressoras

O PKG-40 mantém o cadastro de impressoras em SQLite e usa owner/organização opcional para isolar acesso.

Fluxos:

- listar impressoras visíveis: `GET /api/printers`;
- criar impressora cloud: `POST /api/printers`;
- detalhar impressora: `GET /api/printers/{printer_id}`;
- editar impressora: `PUT /api/printers/{printer_id}`;
- testar conexão manualmente: `POST /api/printers/test-connection` retorna bloqueio cloud-safe; validação real acontece por agente pareado;
- descobrir Moonraker na rede local: `GET /api/printers/discover` fica bloqueado na API cloud até existir agente de rede dedicado.

Campos cloud:

- `name`, `moonraker_url`, `cloud_model`, `location`, `cloud_tags`, `notes` e `organization_id`;
- `organization_id` é opcional; sem organização a impressora fica individual;
- tags são normalizadas para minúsculas e deduplicadas;
- a credencial SSH pode ser configurada, mas não é retornada pela API.

Status cloud:

- `sem_agente`: nenhum token ativo e nenhum agente ativo;
- `aguardando_pareamento`: token ativo ou agente pareado sem heartbeat;
- `online`: agente ativo com heartbeat recente;
- `offline`: agente ativo sem heartbeat recente;
- `revogado`: apenas agentes revogados conhecidos.

Rollback PKG-40:

- reverter backend/UI/docs do pacote;
- se for necessário desfazer dados de schema, restaurar backup `printora.<timestamp>.before-schema.db` criado pelo versionador antes dos scripts aplicados;
- não apagar impressoras, agentes ou tokens manualmente sem confirmação explícita.

## Pareamento Seguro Do Agente

O PKG-41 usa SQLite e adiciona `backend/sql/029_agent_pairing.sql`.

Fluxos:

- gerar token curto: `POST /api/printers/{printer_id}/pairing/tokens` com sessão do usuário;
- listar pareamento: `GET /api/printers/{printer_id}/pairing`;
- revogar token: `POST /api/printers/{printer_id}/pairing/tokens/{token_id}/revoke`;
- trocar token por credencial operacional: `POST /api/agent/pairing/exchange`;
- heartbeat do agente: `POST /api/agent/heartbeat` com `Authorization: Bearer <credencial>`;
- snapshot do agente: `POST /api/agent/snapshots` com `Authorization: Bearer <credencial>`;
- fila de jobs: `GET /api/agent/jobs/next` com `Authorization: Bearer <credencial>`;
- rotacionar credencial: `POST /api/printers/{printer_id}/agents/{agent_id}/rotate`;
- revogar agente: `POST /api/printers/{printer_id}/agents/{agent_id}/revoke`.

Segurança:

- token de pareamento é persistido somente por hash, possui expiração, uso único e revogação;
- credencial operacional é persistida somente por hash e retornada completa apenas na troca ou rotação;
- eventos de agente guardam somente prefixos/detalhes sanitizados, nunca token completo ou credencial;
- agente revogado ou credencial antiga após rotação recebe 401 em heartbeat, snapshot e jobs.

Rollback:

- para desfazer o pareamento, reverter arquivos do PKG-41;
- se `029_agent_pairing.sql` já tiver sido aplicado e o schema não puder permanecer, restaurar o backup `printora.<timestamp>.before-schema.db` criado pelo versionador antes da aplicação;
- não apagar tokens, agentes ou eventos manualmente sem confirmação explícita.

## Agente Remoto Base

O PKG-42 adiciona o agente em Go em `agent/`.

Build:

```bash
cd agent
go test ./...
GOOS=linux GOARCH=arm64 go build ./cmd/printora-agent
GOOS=linux GOARCH=arm GOARM=7 go build ./cmd/printora-agent
GOOS=linux GOARCH=amd64 go build ./cmd/printora-agent
```

Config inicial:

```bash
printora-agent -config /etc/printora-agent/config.json config-sample
printf '%s\n' 'ptr_agent_xxx' | printora-agent -config /etc/printora-agent/config.json store-credential
chmod 600 /etc/printora-agent/config.json /etc/printora-agent/credential
printora-agent -config /etc/printora-agent/config.json doctor
```

Execução:

```bash
printora-agent -config /etc/printora-agent/config.json once
printora-agent -config /etc/printora-agent/config.json run
```

Canal remoto:

- `run` usa WebSocket outbound em `/api/agent/ws` quando `websocket_enabled=true`;
- se o WebSocket falhar, o agente continua tentando reconectar com backoff ate 60s;
- durante a reconexao, o agente segue enviando heartbeat/snapshot por HTTPS e, se `polling_enabled=true`, faz fallback em `/api/agent/jobs/next`;
- jobs suportados nesta etapa: `ping` e `snapshot`;
- cada job usa `correlation_id` e resultado idempotente;
- payloads acima de 64 KB são rejeitados pelo backend.

Serviço systemd:

```bash
sudo install -m 0755 printora-agent /usr/local/bin/printora-agent
sudo install -m 0644 agent/systemd/printora-agent.service /etc/systemd/system/printora-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now printora-agent
```

Segurança:

- o agente só abre conexões de saída;
- Moonraker local é acessado pelo agente; a API cloud não acessa Moonraker/SSH/rede local diretamente;
- jobs mutáveis usam tipos explícitos ou `remote_host_script` controlado pelo backend, com confirmação/gate quando aplicável;
- credencial operacional fica em arquivo separado com permissão `0600`;
- logs passam por redaction de tokens;
- fila local JSONL é limitada e guarda payload compacto quando a API está indisponível.

Rollback PKG-43:

- reverter os arquivos do PKG-43;
- se `backend/sql/030_agent_channel.sql` já tiver sido aplicado e a tabela não puder permanecer, restaurar o backup `printora.<timestamp>.before-schema.db` criado antes da aplicação do schema;
- no host real, definir `"websocket_enabled": false` mantém o agente no ciclo HTTP/polling enquanto o backend é revertido.

## Instalador Online Assistido Do Agente

Fluxos:

- gerar plano de instalação: `POST /api/printers/{printer_id}/agent/install-plan`;
- consultar validação pós-instalação: `GET /api/printers/{printer_id}/agent/install-status`;
- baixar script público sem segredo: `GET /api/agent/install/linux.sh`.

Uso no host Klipper:

```bash
curl -fsSL https://printora.example.com/api/agent/install/linux.sh | PRINTORA_API_BASE=https://printora.example.com PRINTORA_MOONRAKER_URL=http://127.0.0.1:7125 bash -s -- --preflight
curl -fsSL https://printora.example.com/api/agent/install/linux.sh | sudo PRINTORA_API_BASE=https://printora.example.com PRINTORA_PAIRING_TOKEN=ptr_pair_xxx PRINTORA_MOONRAKER_URL=http://127.0.0.1:7125 PRINTORA_AGENT_BIN_URL=https://releases.example.com/printora-agent-linux-arm64 bash -s -- --apply --yes
```

Segurança:

- o script nunca imprime o token de pareamento;
- o token curto é enviado somente para `/api/agent/pairing/exchange` e vira credencial operacional local;
- config e credencial ficam em `/etc/printora-agent` com permissão `0600`;
- dados de fila ficam em `/var/lib/printora-agent` e logs em `/var/log/printora-agent`;
- o script exige systemd para instalar serviço e não executa G-code, restart de Klipper, update ou flash.

Uninstall:

```bash
curl -fsSL https://printora.example.com/api/agent/install/linux.sh | sudo bash -s -- --uninstall
```

O uninstall para/desabilita o serviço e remove o binário, mas preserva configuração, fila e logs. Apagar esses diretórios exige ação manual explícita.

Rollback PKG-44:

- reverter backend, UI e `backend/scripts/install_agent_linux.sh`;
- no host real, rodar o uninstall acima;
- revogar o agente ou token pela tela Impressoras quando necessário;
- não apagar dados locais do agente sem confirmação.

## Atualização Automática Do Agente

Fluxos cloud:

- manifesto público: `GET /api/agent/update/manifest`;
- solicitar update remoto: `POST /api/printers/{printer_id}/agents/{agent_id}/update-check`;
- relatório do agente: `POST /api/agent/update/reports` com `Authorization: Bearer <credencial>`;
- histórico por impressora: `GET /api/printers/{printer_id}/agent/update-history`.

Config do agente:

```json
{
  "update_enabled": true,
  "update_check_interval_seconds": 3600,
  "update_manifest_url": "https://printora.example.com/api/agent/update/manifest",
  "update_state_file": "/var/lib/printora-agent/update-state.json",
  "update_staging_dir": "/var/lib/printora-agent/updates",
  "agent_binary_path": "/usr/local/bin/printora-agent",
  "agent_service_name": "printora-agent",
  "allow_service_restart": true
}
```

Execução manual:

```bash
sudo printora-agent -config /etc/printora-agent/config.json update-check
```

Publicação do binário do agente:

- o arquivo servido em `releases[].url` precisa ser exatamente o mesmo binário usado para calcular `releases[].sha256`;
- a API serve o binário em `/api/agent/update/releases/linux-arm64` a partir de `.artifacts/agent/printora-agent-linux-arm64`;
- se o download falhar com `sha256 inválido`, conferir o SHA do arquivo servido pela URL pública/local antes de tentar reinstalar a impressora;
- em ambiente local de teste, não depender de servidor HTTP avulso para o binário quando a API estiver acessível pela impressora.

Execução pela UI:

- abrir `Agentes`, conferir `Versão instalada` e `Versão esperada`;
- clicar `Atualizar` na linha ou `Atualizar agente` no detalhe;
- o servidor cria um job `remote_agent_update_check` para o agente ativo, sem SSH e sem comando manual para o usuário;
- o agente baixa o binário indicado no manifesto, valida SHA-256, troca somente `/usr/local/bin/printora-agent` e reinicia apenas `printora-agent` quando `allow_service_restart=true`.

Segurança:

- o update consulta somente o manifesto do agente e baixa o binário indicado para a plataforma do host;
- `sha256` é obrigatório para aplicar;
- versão/protocolo bloqueado pelo servidor impede aplicação;
- antes da troca, o agente preserva backup do binário atual e tenta preservar o config;
- a troca altera apenas o binário do `printora-agent`;
- restart automático, quando habilitado, executa apenas `systemctl restart printora-agent`;
- o fluxo não reinicia Klipper, Moonraker, firmware, Raspberry ou impressora;
- falha em health command ou restart restaura o binário anterior quando possível.

Rollback local:

- se o rollback automático não for suficiente, parar o serviço, restaurar `printora-agent.backup-*` de `/var/lib/printora-agent/updates` para `/usr/local/bin/printora-agent` e iniciar `printora-agent`;
- revogar agente pela tela Impressoras se houver suspeita de credencial comprometida;
- não apagar histórico local sem confirmação.

## Paridade Funcional Remota

Fluxos:

- matriz de paridade: `GET /api/printers/{printer_id}/remote/parity`;
- solicitar job remoto: `POST /api/printers/{printer_id}/remote/parity/jobs`;
- execução do agente: `GET /api/agent/jobs/next`, `ack`, `result` e `error`.

Funcionalidades remotas read-only:

- `audit`;
- `snapshot`;
- `health`;
- `temperatures`;
- `update_manager`;
- `can`;
- `final_validation`;
- `sanitized_report`.

Funcionalidades remotas dry-run/preview:

- `backup_preview`;
- `operation_preview`;
- `firmware_preview`.

Bloqueios explícitos até PKG-47:

- `backup_payload`;
- `firmware_build_apply`;
- `mutable_operation`.

Estados:

- `implemented`: agente recente e funcionalidade disponível;
- `cached`: último resultado conhecido existe, mas agente não está recente;
- `offline`: sem agente recente e sem resultado anterior;
- `blocked`: bloqueio de segurança;
- `not_supported`: não suportado pela plataforma/contrato atual.

Segurança:

- o servidor cloud não acessa Moonraker direto no modo remoto; ele agenda job para o agente;
- o agente sanitiza campos com `password`, `token`, `secret`, `credential` e `private_key`;
- payload grande de backup real continua bloqueado até política própria;
- operações mutáveis, build e flash remoto continuam bloqueados até o PKG-47.

## Operação Segura Remota

Fluxos:

- matriz de operações: `GET /api/printers/{printer_id}/remote/operations`;
- solicitar preflight: `POST /api/printers/{printer_id}/remote/operations/preflight`;
- solicitar execução: `POST /api/printers/{printer_id}/remote/operations/execute`;
- cancelar job pendente: `POST /api/printers/{printer_id}/remote/operations/jobs/{job_id}/cancel`;
- execução do agente: `remote_mutation_preflight` e `remote_mutation_execute` via `agent_jobs`.

Gates obrigatórios:

- usuário autenticado com acesso à impressora por ownership ou organização;
- agente ativo pareado com a impressora;
- job de preflight remoto concluído com `can_execute=true`;
- confirmação textual exata do preflight;
- job ainda não expirado;
- estado detectável sem impressão em andamento;
- Klipper e Klippy em `ready` quando retornados pelo Moonraker.

Política de job:

- preflight expira em 10 minutos;
- execução expira em 5 minutos;
- jobs expirados não são entregues em `/api/agent/jobs/next`;
- cancelamento é permitido para job pendente; job em progresso não é cancelado pelo servidor para não mascarar execução já recebida pelo agente.

Auditoria:

- `agent_jobs` guarda solicitação, confirmação, payload sanitizado, status, agente, resultado e erro;
- `printer_agent_events` registra criação, ack, resultado, erro e cancelamento por impressora/agente;
- detalhes de evento ficam truncados e não devem conter token, senha, chave ou payload sensível.

Rollback:

- a UI mostra rollback antes da confirmação;
- para comandos de aquecimento, enviar alvo `0`;
- para fan, enviar `M107` ou `SPEED=0`;
- para comportamento inesperado de movimento/extrusão, usar Emergency Stop no Mainsail/Klipper e revalidar `printer/info`.

## Observabilidade E Suporte Do Agente

Fluxos:

- painel de suporte: `GET /api/printers/{printer_id}/agent/support`;
- doctor remoto: `POST /api/printers/{printer_id}/agent/support/doctor`;
- pacote sanitizado: `GET /api/printers/{printer_id}/agent/support/bundle`;
- job do agente: `remote_doctor`.

Estados diagnosticáveis:

- sem agente pareado: instalar/parear agente;
- sem heartbeat recente: validar serviço `printora-agent`, rede de saída e credencial local;
- agente revogado: parear novo agente ou rotacionar credencial;
- versão diferente da esperada: executar update do agente;
- protocolo incompatível: atualizar agente antes de novos jobs;
- fila acumulada: verificar WebSocket/polling e conectividade com a API;
- falha recorrente: rodar doctor remoto e revisar última falha;
- Moonraker/Klipper indisponível no doctor: corrigir host local antes de operar remotamente.

Sanitização:

- pacote de suporte remove campos `password`, `token`, `secret`, `credential` e `private_key`;
- tokens `ptr_agent_*`, `ptr_pair_*` e `ptr_sess_*` são redigidos;
- log tail do agente é limitado e sanitizado antes de sair do host;
- pacote de suporte não deve ser usado como backup nem conter payload completo sensível.

Retenção e limpeza:

- eventos de agente e jobs usados para suporte têm retenção operacional definida de 180 dias;
- o endpoint de pacote não apaga dados;
- limpeza deve ser rotina operacional manual/supervisionada enquanto não existir job dedicado, para evitar apagar histórico útil sem confirmação.

Segurança:

- senhas usam PBKDF2 e nunca são retornadas;
- tokens de sessão, desafios 2FA, step-up tokens e credenciais de agente são persistidos por hash;
- segredo TOTP é protegido por chave local `auth_secrets.key`, fora do Git;
- credencial de agente completa não aparece na listagem, somente prefixo/status;
- operações da tela Operação chamadas com sessão autenticada exigem step-up token para envio de G-code.
- endpoints operacionais exigem sessão quando já existe ao menos um usuário ativo no banco; bancos locais sem usuários preservam o modo local de desenvolvimento.

Rollback:

- para remover a camada de autenticação, reverter os arquivos do PKG-39;
- se os scripts `026_auth_identity.sql`, `027_printer_ownership.sql` ou `028_operational_ownership.sql` já tiverem sido aplicados e precisar desfazer o schema, restaurar o backup `printora.<timestamp>.before-schema.db` criado pelo versionador antes da aplicação;
- não apagar tabelas ou dados manualmente sem confirmação explícita.

Regras operacionais:

- os scripts executam apenas leitura HTTP do dominio `canbus.esoterical.online` e leitura/escrita local dos JSONs quando `--write` for informado;
- os scripts nao executam flash, build, update, SSH, restart, `make`, G-code ou alteracao de configuracao de impressora;
- o preview de `.config` do PKG-33 e somente leitura em memoria; se a geracao falhar por preset incompleto, corrigir o preset/build config antes de qualquer build futuro;
- o dry-run de build do PKG-33 registra somente plano local com comandos `PLAN ...`; nao grava `.config`, nao copia para Klipper, nao executa `make` e nao abre SSH;
- o build local controlado do PKG-33 pode executar `make clean` e `make` apenas no `klipper_path` local informado, com modo local e confirmacao textual; ele deve restaurar `.config` e salvar log/binario em artefatos Printora, nunca fazer flash, SSH, restart ou update;
- se o site externo mudar menu, conteudo ou disponibilidade, o manifesto deve manter status explicito por URL e a validacao de cobertura deve falhar antes de afetar a UI;
- rollback rapido: restaurar a versao anterior de `backend/app/data/firmware_canbus_manifest.json` e `backend/app/data/firmware_hardware_catalog.json` ou reverter os arquivos do PKG-30 no Git;
- se o catalogo ficar indisponivel ou invalido, a tela Firmware deve preservar o fluxo principal por impressora ativa e exibir estado de erro/sem referencia, sem consultar o site externo em runtime.

## Validacao por risco

- Documentacao, label ou ajuste local simples: validar arquivo alterado e executar `./check.sh` se a alteracao tocar regra do modelo.
- Bug simples e isolado: reteste focado e check proporcional.
- Bug complexo: `./check.sh`, teste automatizado quando viavel e regressao do fluxo afetado.
- Lote de pacote: teste raso e direcionado.
- Fechamento de pacote: `./check.sh`, review final e commit.

## Banco de dados

- Nao usar migrations.
- Mudancas de banco entram como scripts `.sql` idempotentes em `backend/sql/`.
- Toda mudanca deve ter ordem de execucao, efeito esperado e rollback documentado.

## Operacao segura

- Leitura de logs, snapshots e diagnosticos deve ser read-only por padrao.
- Operacao mutavel em Klipper, Moonraker, systemd, firmware ou arquivos de configuracao exige confirmacao, backup e plano de rollback.
- Logs e relatorios nao podem vazar token, senha, IP privado sensivel, caminho local completo ou payload sensivel sem sanitizacao.

## Publicacao

Antes de publicar:

1. Rodar `./check.sh`.
2. Conferir bugs criticos/altos em `BUGS.md`.
3. Conferir riscos e rollback em `GOVERNANCA.md`.
4. Validar smoke do backend e frontend.
5. Registrar decisao relevante em `DECISOES.md` quando houver mudanca de operacao, arquitetura ou rollback.
6. Garantir que a versao foi atualizada no backend, frontend, lockfiles e frontend pre-buildado.
7. Criar commit de release e tag anotada no formato `vX.Y.Z`.
8. Publicar a branch e a tag no remoto.
9. Criar a GitHub Release da tag publicada; a tela `Administracao > Administracao do sistema` consulta GitHub Releases, nao apenas tags Git.
10. Confirmar que `gh release list` mostra a nova versao como `Latest`.

Exemplo para `v0.1.9`:

```bash
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
git tag -a v0.1.9 -m "Printora v0.1.9"
git push origin main
git push origin v0.1.9
gh release create v0.1.9 --title "Printora 0.1.9" --notes "Release v0.1.9"
gh release list --limit 5
```

Se a GitHub Release nao for criada, o app pode continuar mostrando a release anterior como ultima disponivel mesmo com commit e tag locais corretos.
