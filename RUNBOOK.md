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

Validar fechamento completo do pacote:

```bash
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Regras operacionais:

- os scripts executam apenas leitura HTTP do dominio `canbus.esoterical.online` e leitura/escrita local dos JSONs quando `--write` for informado;
- os scripts nao executam flash, build, update, SSH, restart, `make`, G-code ou alteracao de configuracao de impressora;
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
