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

Pela interface, use `Configuracoes > Diagnostico da instalacao` para recarregar
checks locais e copiar um resumo tecnico para suporte.

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
`running` como `failed`. A UI tambem possui acao para reconciliar updates
travados em `Configuracoes > Historico de updates`.

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
`/openapi.json` ou o historico em `Configuracoes > Historico de updates`.
Os instaladores Linux/Raspberry criam `/etc/sudoers.d/printora-restart` com
permissao minima para o usuario do servico executar `systemctl restart/status
printora.service` sem senha. Isso e necessario para update automatico do app,
porque o backend roda sem terminal interativo.

Log de update iniciado pela UI:

```bash
~/.local/share/printora/logs/self-update-run-<id>.log
```

No Android/Termux, o banco e os backups ficam em `~/.local/share/printora/`.
Se a UI cair durante o restart, consultar `Configuracoes > Historico de updates`
ou enviar esse log junto com o resumo de `Diagnostico da instalacao`.

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

Executar build local controlado, sem flash:

```bash
PRINTORA_FIRMWARE_BUILD_MODE=local
curl -s -X POST http://127.0.0.1:8069/api/firmware/boards/BOARD_ID/build-runs/execute-local \
  -H 'Content-Type: application/json' \
  -d '{"klipper_path":"/caminho/local/klipper","output_root":"~/.local/share/printora/firmware_builds","confirmation":"EXECUTE_LOCAL_BUILD_NO_FLASH"}'
```

Travas:

- sem `PRINTORA_FIRMWARE_BUILD_MODE=local`, o histórico registra `blocked_build_mode_disabled`;
- sem confirmação textual exata `EXECUTE_LOCAL_BUILD_NO_FLASH`, o histórico registra `blocked_invalid_build_confirmation`;
- o executor local não usa SSH, não faz flash, não reinicia Klipper/Moonraker e não executa update;
- o executor usa apenas o diretório Klipper local informado e o `output_root` informado.

Artefatos salvos em `output_root/local-build/<placa>/`:

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
9. Criar a GitHub Release da tag publicada; a tela `Configuracoes > Releases do Printora` consulta GitHub Releases, nao apenas tags Git.
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
