# Instalação Multiplataforma

Este é o manual operacional para instalar e validar o Printora em macOS, Windows, Android/Termux, Raspberry/Linux com systemd e Docker.

O Printora roda como uma aplicação web local:

- backend Python/FastAPI;
- frontend React/Vite buildado em `frontend/dist`;
- banco SQLite local `printora.db`;
- porta padrão `8085`, ajustável por `PRINTORA_PORT`.

Nenhum passo abaixo executa G-code, reinicia Klipper/Moonraker ou altera firmware. Integrações com impressoras devem continuar seguindo `GOVERNANCA.md`.

## URLs E Portas

URL padrão local:

```text
http://127.0.0.1:8085
```

Em rede local, use o IP ou nome do host:

```text
http://NOME-DO-HOST.local:8085
http://IP-DO-HOST:8085
```

Portas abaixo de `1024` exigem root/admin no Linux/Android. Sem root no Android, use uma porta alta, por exemplo:

```text
http://printora.local:8069
```

## Variáveis Úteis

macOS/Linux/Android:

```bash
export PRINTORA_PORT=8085
export PRINTORA_HOST=0.0.0.0
export PRINTORA_MOONRAKER_URL=http://voron.local:7125
export PRINTORA_DATA_DIR="$HOME/.local/share/printora"
export PRINTORA_RELEASE_SOURCE_MODE=github
export PRINTORA_RELEASE_GITHUB_OWNER=mayder
export PRINTORA_RELEASE_GITHUB_REPO=printora
export PRINTORA_RELEASE_CHANNEL=stable
```

Windows PowerShell:

```powershell
$env:PRINTORA_PORT="8085"
$env:PRINTORA_HOST="0.0.0.0"
$env:PRINTORA_MOONRAKER_URL="http://voron.local:7125"
$env:PRINTORA_DATA_DIR="$env:LOCALAPPDATA\Printora"
$env:PRINTORA_RELEASE_SOURCE_MODE="github"
$env:PRINTORA_RELEASE_GITHUB_OWNER="mayder"
$env:PRINTORA_RELEASE_GITHUB_REPO="printora"
$env:PRINTORA_RELEASE_CHANNEL="stable"
```

Variáveis de releases:

- `PRINTORA_RELEASE_SOURCE_MODE`: `github`, `fixture` ou `disabled`. Padrão: `github`.
- `PRINTORA_RELEASE_GITHUB_OWNER`: proprietário do repositório público no GitHub. Padrão: `mayder`.
- `PRINTORA_RELEASE_GITHUB_REPO`: nome do repositório público. Padrão: `printora`.
- `PRINTORA_RELEASE_GITHUB_API_BASE_URL`: base da API do GitHub. Padrão: `https://api.github.com`.
- `PRINTORA_RELEASE_CHANNEL`: canal exibido na UI. Padrão: `stable`.
- `PRINTORA_RELEASE_FIXTURE_PATH`: arquivo JSON local usado apenas para teste sem rede quando `PRINTORA_RELEASE_SOURCE_MODE=fixture`.
- `PRINTORA_RELEASE_REQUEST_TIMEOUT_SECONDS`: timeout da consulta read-only. Padrão: `5`.

Essas variáveis só controlam consulta de releases. Elas não aplicam update, não alteram banco e não exigem token para repositório público.

## Validação Comum

Depois de iniciar:

```bash
curl -s http://127.0.0.1:8085/health
```

Resposta esperada:

```json
{"status":"ok","app":"Printora"}
```

Listar impressoras:

```bash
curl -s http://127.0.0.1:8085/api/printers | python -m json.tool
```

Rodar check do projeto:

```bash
./check.sh
```

## macOS

### Verificar Dependências

```bash
python3 --version
npm --version
git --version
curl --version
```

Requisitos:

- Python `3.11+`;
- Node.js/npm;
- Git;
- curl.

### Instalar Dependências Ausentes

Instalar Homebrew se não existir:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Instalar pacotes:

```bash
brew install python node git
```

Se o macOS pedir ferramentas de linha de comando:

```bash
xcode-select --install
```

### Instalar O Printora Com Boot Automático

Na pasta do projeto:

```bash
cd /caminho/para/Printora
./scripts/install_printora.sh
./scripts/install_printora.sh --apply --yes
```

O instalador prepara backend/frontend e configura `launchd` com `KeepAlive`.
Se o Node global for antigo, o Printora instala Node 22 via `nvm` apenas para o
usuário atual e grava `.printora-node-env`, sem trocar o Node do sistema.

### Rodar

```bash
cd /caminho/para/Printora
PRINTORA_HOST=0.0.0.0 PRINTORA_PORT=8085 ./scripts/run_app.sh --no-open
```

Abrir:

```text
http://127.0.0.1:8085
```

Parar:

```bash
./scripts/run_app.sh --stop
```

Ver status:

```bash
./scripts/run_app.sh --status
```

Dados locais:

```text
~/Library/Application Support/Printora/printora.db
```

## Windows

Use PowerShell.

### Verificar Dependências

```powershell
python --version
npm --version
git --version
curl --version
```

Requisitos:

- Python `3.11+`;
- Node.js/npm;
- Git;
- PowerShell.

### Instalar Dependências Ausentes

Com `winget`:

```powershell
winget install --id Python.Python.3.13 -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Git.Git -e
```

Feche e reabra o PowerShell depois da instalação.

### Liberar Execução Do Script Só Para Esta Sessão

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Instalar O Printora Com Boot Automático

```powershell
cd C:\caminho\para\Printora
.\scripts\install_printora_windows.ps1
.\scripts\install_printora_windows.ps1 --apply --yes
```

O instalador registra a tarefa `Printora` no Agendador de Tarefas para iniciar
no logon e reiniciar em caso de falha.

### Rodar

```powershell
cd C:\caminho\para\Printora
$env:PRINTORA_HOST="0.0.0.0"
$env:PRINTORA_PORT="8085"
.\scripts\run_app_windows.ps1 --no-open
```

Abrir:

```text
http://127.0.0.1:8085
```

Parar:

```powershell
.\scripts\run_app_windows.ps1 --stop
```

Ver status:

```powershell
.\scripts\run_app_windows.ps1 --status
```

Dados locais:

```text
%LOCALAPPDATA%\Printora\printora.db
```

## Android Com Termux

Este modo transforma o Android em host local da aplicação. Sem root, use porta alta (`8069`, `8085`, etc.). Porta `69` ou `80` não funciona sem root.

### Verificar ADB No Mac/Linux

No computador:

```bash
adb devices -l
```

Se `adb` não existir no macOS:

```bash
brew install android-platform-tools
```

No Android:

- ativar Opções do desenvolvedor;
- ativar Depuração USB;
- autorizar o computador na tela do celular.

### Instalar Termux Pelo ADB

Baixar APK oficial do GitHub:

```bash
curl -L -o /tmp/termux.apk \
  "https://github.com/termux/termux-app/releases/download/v0.118.3/termux-app_v0.118.3%2Bgithub-debug_universal.apk"
adb install -r /tmp/termux.apk
adb shell monkey -p com.termux 1
```

Aguarde o Termux criar os arquivos internos.

### Instalar Dependências No Termux

Via ADB:

```bash
adb shell 'run-as com.termux /data/data/com.termux/files/usr/bin/bash -lc "
export PREFIX=/data/data/com.termux/files/usr
export HOME=/data/data/com.termux/files/home
export PATH=\$PREFIX/bin:\$PATH
yes | pkg update
yes | pkg upgrade
yes | pkg install python nodejs git openssh tmux rust clang make pkg-config curl termux-api
"'
```

Verificar:

```bash
adb shell 'run-as com.termux /data/data/com.termux/files/usr/bin/bash -lc "
export PREFIX=/data/data/com.termux/files/usr
export HOME=/data/data/com.termux/files/home
export PATH=\$PREFIX/bin:\$PATH
python --version
node --version
npm --version
git --version
rustc --version
"'
```

### Copiar O Projeto Para O Android

Do computador, na pasta acima do projeto:

```bash
tar --exclude='.git' \
  --exclude='frontend/node_modules' \
  --exclude='backend/.venv' \
  --exclude='**/__pycache__' \
  --no-xattrs \
  -czf /tmp/printora-app.tgz Printora

adb push /tmp/printora-app.tgz /data/local/tmp/printora-app.tgz
```

Extrair no Termux:

```bash
adb shell 'run-as com.termux /data/data/com.termux/files/usr/bin/bash -lc "
export PREFIX=/data/data/com.termux/files/usr
export HOME=/data/data/com.termux/files/home
export PATH=\$PREFIX/bin:\$PATH
cd \$HOME
rm -rf Printora
tar -xzf /data/local/tmp/printora-app.tgz -C \$HOME
find \$HOME/Printora -name \"._*\" -delete
chmod +x \$HOME/Printora/check.sh \$HOME/Printora/scripts/*.sh \$HOME/Printora/scripts/*.py
"'
```

### Instalar E Configurar Boot Automático No Android

```bash
adb shell 'run-as com.termux /data/data/com.termux/files/usr/bin/bash -lc "
export PREFIX=/data/data/com.termux/files/usr
export HOME=/data/data/com.termux/files/home
export PATH=\$PREFIX/bin:\$PATH
cd \$HOME/Printora
PRINTORA_PORT=8069 PRINTORA_DATA_DIR=\$HOME/.local/share/printora ./scripts/install_printora.sh
PRINTORA_PORT=8069 PRINTORA_DATA_DIR=\$HOME/.local/share/printora ./scripts/install_printora.sh --apply --yes
"'
```

O instalador cria `~/.termux/boot/start-printora`. Abra o app Termux:Boot uma vez
e remova a otimização de bateria do Termux/Termux:Boot; sem isso, o Android pode
bloquear processos em segundo plano após reinício.

Observação: `pydantic-core` pode compilar no Android. Isso pode demorar alguns minutos.

### Rodar No Android

Porta recomendada sem root:

```bash
adb shell 'run-as com.termux /data/data/com.termux/files/usr/bin/bash -lc "
export PREFIX=/data/data/com.termux/files/usr
export HOME=/data/data/com.termux/files/home
export PATH=\$PREFIX/bin:\$PATH
cd \$HOME/Printora
HTTP_PORT=8069 PUBLIC_PORT=8069 ./scripts/android_start_printora.sh
"'
```

Abrir na rede:

```text
http://printora.local:8069
```

Validar no Termux:

```bash
curl -s http://127.0.0.1:8069/health
curl -s http://127.0.0.1:8069/api/printers | python -m json.tool
tmux ls
```

Se `printora.local` não resolver, descubra o IP do Android no Wi-Fi e acesse:

```bash
adb shell ip -o -4 addr show wlan0
```

Exemplo:

```text
http://192.168.15.16:8069
```

### Porta 80 Ou 69 No Android

Sem root, portas abaixo de `1024` falham com `PermissionError`. Com root/Magisk autorizado no Termux:

```bash
cd ~/Printora
./scripts/android_enable_port80_root.sh
HTTP_PORT=8085 PUBLIC_PORT=80 ./scripts/android_start_printora.sh
```

## Raspberry Pi, Manta, CB1 Ou Linux Com Systemd

Use este modo para instalar como serviço.

### Verificar Dependências

```bash
python3 --version
python3 -m venv --help >/dev/null && echo "venv ok"
npm --version
git --version
rsync --version
systemctl --version
curl --version
```

### Instalar Dependências Ausentes

Debian/Raspberry Pi OS:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm git rsync curl
```

Se o Node.js do repositório for antigo, não troque o Node global. O instalador do
Printora usa `nvm` no usuário atual e deixa outros serviços, como Spoolman,
usando o Node que já estavam usando.

### Clonar Ou Copiar O Projeto

```bash
cd /home/pi
git clone <URL_DO_REPOSITORIO> Printora
cd /home/pi/Printora
```

Se estiver instalando em `linaro`:

```bash
cd /home/linaro
git clone <URL_DO_REPOSITORIO> Printora
cd /home/linaro/Printora
```

### Instalar Em Dry-run

```bash
./scripts/install_printora.sh
```

### Aplicar

Raspberry com usuário `pi`:

```bash
./scripts/install_printora.sh --apply --yes
```

CB1/Manta com usuário `linaro`:

```bash
PRINTORA_INSTALL_USER=linaro \
PRINTORA_INSTALL_HOME=/home/linaro \
PRINTORA_INSTALL_DIR=/home/linaro/Printora \
PRINTORA_PUBLIC_URL=http://voron-02-pro.local:8085 \
./scripts/install_raspberry.sh --apply
```

### Revisar `.env`

```bash
nano /home/pi/Printora/.env
```

Exemplo:

```text
PRINTORA_MOONRAKER_URL=http://127.0.0.1:7125
PRINTORA_DATA_DIR=/home/pi/.local/share/printora
PRINTORA_FRONTEND_DIST_DIR=/home/pi/Printora/frontend/dist
PRINTORA_RELEASE_SOURCE_MODE=github
PRINTORA_RELEASE_GITHUB_OWNER=mayder
PRINTORA_RELEASE_GITHUB_REPO=printora
PRINTORA_RELEASE_CHANNEL=stable
```

### Iniciar Serviço

```bash
sudo systemctl start printora.service
sudo systemctl status printora.service --no-pager
curl -s http://127.0.0.1:8085/health
```

### Logs

```bash
journalctl -u printora.service -f
```

### Parar Ou Remover

```bash
sudo systemctl stop printora.service
sudo systemctl disable printora.service
sudo rm -f /etc/systemd/system/printora.service
sudo systemctl daemon-reload
```

Dados locais:

```text
/home/pi/.local/share/printora/printora.db
```

## Docker

Use Docker quando quiser isolar dependências e persistir dados em volume.

### Verificar Dependências

```bash
docker --version
docker compose version
```

### Instalar Dependências

macOS/Windows:

- instalar Docker Desktop;
- reiniciar o terminal.

Linux Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Permitir uso sem `sudo` no Linux:

```bash
sudo usermod -aG docker "$USER"
```

Faça logout/login depois.

### Rodar

```bash
cd /caminho/para/Printora
docker compose up --build
```

Abrir:

```text
http://127.0.0.1:8085
```

Rodar em background:

```bash
docker compose up -d --build
```

Ver logs:

```bash
docker compose logs -f printora
```

Parar:

```bash
docker compose down
```

Preservar dados:

```text
volume Docker: printora-data
container path: /data/printora.db
```

Backup do banco:

```bash
docker compose exec printora python - <<'PY'
from pathlib import Path
src = Path("/data/printora.db")
print(src if src.exists() else "banco ainda nao criado")
PY
```

## Copiar Banco Existente

macOS para Android:

```bash
scp -P 8022 "$HOME/Library/Application Support/Printora/printora.db" \
  u0_xxx@127.0.0.1:/data/data/com.termux/files/home/printora.db.from-mac
```

No Termux:

```bash
mkdir -p ~/.local/share/printora
cp ~/.local/share/printora/printora.db ~/.local/share/printora/printora.db.before-import-$(date +%Y%m%d-%H%M%S) 2>/dev/null || true
cp ~/printora.db.from-mac ~/.local/share/printora/printora.db
```

Validar:

```bash
python - <<'PY'
import sqlite3
conn = sqlite3.connect("/data/data/com.termux/files/home/.local/share/printora/printora.db")
for row in conn.execute("select id, name, moonraker_url from printers order by id"):
    print(row)
PY
```

## Diagnóstico Rápido

Porta ocupada:

```bash
lsof -nP -iTCP:8085 -sTCP:LISTEN
```

Backend responde:

```bash
curl -v http://127.0.0.1:8085/health
```

Frontend build existe:

```bash
test -s frontend/dist/index.html && echo "frontend ok"
```

Banco existe:

```bash
ls -lh "$HOME/.local/share/printora/printora.db"
```

No Android:

```bash
tmux ls
tmux capture-pane -pt printora -S -80
tmux capture-pane -pt printora-mdns -S -80
```
