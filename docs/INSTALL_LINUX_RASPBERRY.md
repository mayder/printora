# Instalação No Linux, Raspberry, CB1 Ou Manta

Use este guia para instalar o Printora em Linux com `systemd`, Raspberry Pi, CB1 ou Manta.

## Requisitos

- Linux com `systemd`;
- `sudo` para instalar dependências;
- internet para baixar dependências ausentes;
- acesso de rede ao Moonraker da impressora.

## Instalação Recomendada

Raspberry com usuário `pi`:

```bash
cd /home/pi
git clone https://github.com/mayder/printora.git Printora
cd /home/pi/Printora
chmod +x check.sh scripts/*.sh scripts/*.py
./scripts/install-linux.sh
```

CB1/Manta com usuário `linaro`:

```bash
cd /home/linaro
git clone https://github.com/mayder/printora.git Printora
cd /home/linaro/Printora
chmod +x check.sh scripts/*.sh scripts/*.py
./scripts/install-linux.sh
```

O instalador verifica `systemd`, Python `3.11+`, Git, curl, rsync, pkg-config, make e Node.js/npm. Se faltar algo, ele pergunta antes de instalar via `apt`.

Se o Node.js do sistema for antigo, não troque o Node global. O instalador do Printora usa Node isolado via `nvm` quando necessário.

## Instalar Dependências Manualmente

Debian/Raspberry Pi OS:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm git rsync curl pkg-config build-essential
```

## Instalar Manualmente

```bash
PRINTORA_PORT=8069 ./scripts/install_printora.sh --apply --yes
```

## Instalar Em CB1/Manta Com Caminhos Explícitos

```bash
PRINTORA_INSTALL_USER=linaro \
PRINTORA_INSTALL_HOME=/home/linaro \
PRINTORA_INSTALL_DIR=/home/linaro/Printora \
PRINTORA_PUBLIC_URL=http://voron-02-pro.local:8069 \
./scripts/install_raspberry.sh --apply
```

## Validar Serviço

```bash
sudo systemctl status printora.service --no-pager
curl -s http://127.0.0.1:8069/health
```

Abrir:

```text
http://IP-DO-HOST:8069
```

## Logs

```bash
journalctl -u printora.service -f
```

## Parar Ou Remover

```bash
sudo systemctl stop printora.service
sudo systemctl disable printora.service
sudo rm -f /etc/systemd/system/printora.service
sudo systemctl daemon-reload
```

## Dados Locais

```text
~/.local/share/printora/printora.db
```
