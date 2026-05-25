# Instalação No Linux, Raspberry, CB1 Ou Manta

Use este guia para instalar o Printora em Linux com `systemd`, Raspberry Pi, CB1 ou Manta.

## Requisitos

- Python `3.11+`;
- `python3-venv`;
- Node.js/npm;
- Git;
- curl;
- systemd.

## Instalar Dependências

Debian/Raspberry Pi OS:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm git rsync curl
```

Se o Node.js do sistema for antigo, não troque o Node global. O instalador usa Node isolado via `nvm` quando necessário.

## Clonar O Projeto

Raspberry com usuário `pi`:

```bash
cd /home/pi
git clone https://github.com/mayder/printora.git Printora
cd /home/pi/Printora
```

CB1/Manta com usuário `linaro`:

```bash
cd /home/linaro
git clone https://github.com/mayder/printora.git Printora
cd /home/linaro/Printora
```

## Instalar

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
