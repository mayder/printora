<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="identidade/printora-logo-horizontal-dark-bg.png">
    <img src="identidade/printora-logo-horizontal-color.png" alt="Printora" width="620">
  </picture>
</p>

Printora é uma aplicação web local para acompanhar, diagnosticar e manter impressoras 3D com Klipper/Moonraker.

O foco é segurança operacional: ler o estado real da impressora, registrar histórico, gerar evidências e reduzir risco antes de updates, manutenção, ajustes ou planejamento de firmware.

## Para Que Serve

- cadastrar e selecionar múltiplas impressoras Klipper/Moonraker;
- acompanhar visão geral, health check e alertas;
- visualizar operação ao vivo da impressora ativa;
- consultar Update Manager e checklist pós-update;
- registrar manutenção preventiva, diário técnico e horas de impressão;
- capturar snapshots read-only e comparar mudanças;
- gerar relatórios sanitizados para compartilhar sem expor dados sensíveis;
- acompanhar histórico CAN, Z-offset e calibração;
- planejar build e flash de firmware com fluxo conservador.

## Estado Atual

Esta versão é local, gratuita e ainda está em teste.

Por padrão, o Printora é conservador:

- não envia G-code pelo launcher rápido;
- não reinicia Klipper, Moonraker ou systemd pelo launcher rápido;
- não faz flash de firmware pelo launcher rápido;
- salva os dados em SQLite no computador ou dispositivo onde a aplicação está rodando.

O fluxo de firmware é uma das prioridades do projeto. A meta inicial é simplificar atualização e planejamento seguro de MCU, EBB e placas relacionadas, mas as etapas críticas continuam protegidas por dry-run, validação e confirmação.

## Requisitos

- Python 3.11 ou mais novo;
- Node.js e npm;
- acesso de rede ao Moonraker da impressora para dados ao vivo.

URL padrão usada pelos atalhos locais:

```text
http://voron.local:7125
```

## Uso Rápido

### macOS

1. Abra a pasta do projeto.
2. Dê duplo clique em `Abrir Printora.command`.
3. Mantenha a janela do Terminal aberta.
4. Abra `http://127.0.0.1:8085`.

Se o macOS bloquear o arquivo:

```bash
chmod +x "Abrir Printora.command" scripts/run_app.sh
```

### Windows

1. Abra a pasta do projeto.
2. Dê duplo clique em `Abrir Printora.bat`.
3. Mantenha a janela do PowerShell aberta.
4. Abra `http://127.0.0.1:8085`.

Se o Windows bloquear a execução:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_app_windows.ps1
```

### Linux, Raspberry Ou Android/Termux

Consulte o guia completo:

```text
docs/INSTALL_MULTIPLATFORM.md
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

## Configurar Moonraker

macOS/Linux:

```bash
PRINTORA_MOONRAKER_URL=http://sua-impressora.local:7125 ./scripts/run_app.sh
```

Windows PowerShell:

```powershell
$env:PRINTORA_MOONRAKER_URL="http://sua-impressora.local:7125"
.\scripts\run_app_windows.ps1
```

Também é possível cadastrar impressoras pela interface.

## Onde Ficam Os Dados

- macOS: `~/Library/Application Support/Printora`
- Windows: `%LOCALAPPDATA%\Printora`
- Linux: `~/.local/share/printora`
- Docker: volume `printora-data`

Banco local:

```text
printora.db
```

## Validação

Health check:

```bash
curl http://127.0.0.1:8085/health
```

Resposta esperada:

```json
{"status":"ok","app":"Printora"}
```

Check oficial do projeto:

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

## Estrutura Do Repositório

`PATHS.toml` é o mapa oficial do monorepo. Ele define raízes, arquivos principais, checks, módulos e regras de qualidade usadas para manter backend, frontend, documentação e scripts alinhados.

Arquivos principais:

- `PATHS.toml`: mapa oficial do projeto;
- `QUALITY_ROADMAP.md`: fluxo de desenvolvimento e critérios de qualidade;
- `GOVERNANCA.md`: segurança, riscos, release gates e rollback;
- `DEMANDAS.md`: backlog de pacotes e entregas;
- `TELAS.md`: telas, rotas e estados da interface;
- `TESTES.md`: estratégia de validação;
- `RUNBOOK.md`: operação local, diagnóstico e publicação;
- `MAPA_EXECUTIVO_MARKMAP.md`: mapa mental executivo;
- `MAPA_MENTAL_MARKMAP.md`: mapa mental completo.

## Licença

Printora é open source sob a licença MIT. Veja `LICENSE`.

O software é fornecido sem garantia. Operações em impressoras, firmware, Moonraker, Klipper, systemd ou arquivos de configuração devem ser revisadas pelo usuário antes de execução real.

## Links

- Projeto: <https://github.com/mayder/printora>
- Autor: <https://www.linkedin.com/in/brenomayder/>
- Instagram: <https://www.instagram.com/brenomayder>

## Documentação

- Recursos e endpoints: `docs/FEATURES.md`
- Instalação multiplataforma: `docs/INSTALL_MULTIPLATFORM.md`
- Instalação Raspberry/Mainsail/Moonraker: `docs/INSTALL_RASPBERRY.md`
- Governança e segurança: `GOVERNANCA.md`
- Testes: `TESTES.md`
- Runbook: `RUNBOOK.md`
