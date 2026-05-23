# Printora

![Printora logo](frontend/public/brand/printora-logo-horizontal-color.png)

Printora é uma aplicação web local para impressoras Klipper/Moonraker.

Ela ajuda com saúde da impressora, auditorias read-only, snapshots, backups, manutenção, histórico de CAN, Z-offset, registros de calibração e planejamento seguro de firmware.

Por padrão, o Printora é conservador:

- não envia G-code pelo launcher rápido;
- não reinicia Klipper, Moonraker ou systemd pelo launcher rápido;
- não faz flash de firmware pelo launcher rápido;
- salva os dados locais em SQLite no computador onde a aplicação está rodando.

## Modelo de trabalho

Este monorepo usa `PATHS.toml` como mapa oficial para IA e humanos. A raiz concentra governanca, backlog, testes, telas, decisoes, runbook, mapas e check oficial.

Arquivos principais:

- `PATHS.toml`
- `QUALITY_ROADMAP.md`
- `GOVERNANCA.md`
- `DEMANDAS.md`
- `TESTES.md`
- `BUGS.md`
- `TELAS.md`
- `DECISOES.md`
- `RUNBOOK.md`
- `MAPA_EXECUTIVO_MARKMAP.md`
- `MAPA_MENTAL_MARKMAP.md`

Validacao oficial:

```bash
./check.sh
```

## O Que Clicar

### macOS

1. Abra a pasta do projeto.
2. Dê duplo clique em:

```text
Abrir Printora.command
```

3. Mantenha a janela do Terminal aberta.
4. O navegador deve abrir:

```text
http://127.0.0.1:8085
```

Para parar o Printora, pressione `Ctrl+C` nessa janela do Terminal ou feche a janela.

Se o macOS bloquear o arquivo, rode uma vez dentro da pasta do projeto:

```bash
chmod +x "Abrir Printora.command" scripts/run_app.sh
```

Depois dê duplo clique em `Abrir Printora.command` de novo.

### Windows

1. Abra a pasta do projeto.
2. Dê duplo clique em:

```text
Abrir Printora.bat
```

3. Mantenha a janela do PowerShell aberta.
4. O navegador deve abrir:

```text
http://127.0.0.1:8085
```

Para parar o Printora, pressione `Ctrl+C` nessa janela do PowerShell ou feche a janela.

Se o Windows bloquear a execução do script, abra o PowerShell na pasta do projeto e rode:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_app_windows.ps1
```

## Requisitos

Para macOS, Linux e Windows:

- Python 3.11 ou mais novo;
- Node.js e npm;
- acesso de rede ao Moonraker da impressora, se quiser dados ao vivo.

URL padrão da impressora usada pelo launcher:

```text
http://voron.local:7125
```

Para trocar a URL antes de abrir:

macOS/Linux:

```bash
PRINTORA_MOONRAKER_URL=http://sua-impressora.local:7125 ./scripts/run_app.sh
```

Windows PowerShell:

```powershell
$env:PRINTORA_MOONRAKER_URL="http://sua-impressora.local:7125"
.\scripts\run_app_windows.ps1
```

## Comandos Manuais

macOS/Linux:

```bash
./scripts/run_app.sh
./scripts/run_app.sh --status
./scripts/run_app.sh --stop
```

Windows PowerShell:

```powershell
.\scripts\run_app_windows.ps1
.\scripts\run_app_windows.ps1 --status
.\scripts\run_app_windows.ps1 --stop
```

Docker:

```bash
docker compose up --build
```

Depois abra:

```text
http://127.0.0.1:8085
```

## Instalação Na Raspberry Ou Mainsail

O instalador Raspberry/systemd é separado dos atalhos locais de duplo clique.

Dry-run:

```bash
./scripts/install_raspberry.sh
```

Aplicar depois de revisar:

```bash
./scripts/install_raspberry.sh --apply
```

Guia completo:

```text
docs/INSTALL_RASPBERRY.md
```

## Onde Ficam Os Dados

Pastas padrão:

- macOS: `~/Library/Application Support/Printora`
- Windows: `%LOCALAPPDATA%\Printora`
- Linux: `~/.local/share/printora`
- Docker: volume `printora-data`

O banco SQLite se chama:

```text
printora.db
```

## Como Validar

Health check:

```bash
curl http://127.0.0.1:8085/health
```

Resposta esperada:

```json
{"status":"ok","app":"Printora"}
```

Checks do projeto:

```bash
./check.sh
```

Testes do backend:

```bash
backend/.venv/bin/python -m pytest backend/tests
```

Build do frontend:

```bash
npm --prefix frontend run build
```

## Mais Documentação

- Detalhes de recursos e endpoints: `docs/FEATURES.md`
- Instalação multiplataforma com comandos para macOS, Windows, Android, Raspberry/Linux e Docker: `docs/INSTALL_MULTIPLATFORM.md`
- Instalação Raspberry/Mainsail/Moonraker: `docs/INSTALL_RASPBERRY.md`
- Escopo: `ESCOPO.md`
- Governança e segurança: `GOVERNANCA.md`
- Workflow de desenvolvimento: `QUALITY_ROADMAP.md`
- Backlog: `DEMANDAS.md`
