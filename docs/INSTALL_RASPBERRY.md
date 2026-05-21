# Instalação Na Raspberry Pi

Este roteiro integra o Printora com Klipper, Moonraker e Mainsail sem alterar configurações da impressora automaticamente.

## Pré-requisitos

- Raspberry Pi com Klipper/Moonraker/Mainsail já funcionando.
- Acesso SSH.
- `python3`, `venv`, `npm`, `rsync` e `git`.
- Impressora parada antes de iniciar/reiniciar serviços.

## Instalação Segura

Rodar primeiro em dry-run:

```bash
cd /home/pi/Printora
./scripts/install_raspberry.sh
```

Aplicar somente depois de revisar os comandos:

```bash
cd /home/pi/Printora
./scripts/install_raspberry.sh --apply
```

Em hosts não-Raspberry que usam outro usuário/home, como Catalyst/CB1 com `linaro`:

```bash
cd /home/linaro/Printora
PRINTORA_INSTALL_USER=linaro \
PRINTORA_INSTALL_HOME=/home/linaro \
PRINTORA_INSTALL_DIR=/home/linaro/Printora \
PRINTORA_PUBLIC_URL=http://voron-02-pro.local:8085 \
./scripts/install_raspberry.sh --apply
```

O script:

- cria/atualiza `/home/pi/Printora`;
- em hosts não-Raspberry, respeita `PRINTORA_INSTALL_USER`, `PRINTORA_INSTALL_HOME` e `PRINTORA_INSTALL_DIR`;
- cria venv do backend;
- instala dependências Python;
- instala dependências frontend e gera build estático quando `npm` existe;
- usa `frontend/dist` já buildado quando `npm` não existe no host;
- cria `.env` se ainda não existir;
- copia `printora.service`;
- habilita o serviço.

Ele não inicia o serviço automaticamente. Depois de revisar `.env`:

```bash
sudo systemctl start printora.service
sudo systemctl status printora.service --no-pager
curl -s http://127.0.0.1:8085/health
```

## Mainsail

Arquivo de exemplo:

```text
packaging/mainsail/navi.json
```

Instalação manual sugerida:

```bash
mkdir -p /home/pi/printer_data/config/.theme
cp packaging/mainsail/navi.json /home/pi/printer_data/config/.theme/navi.json
```

Se já existir um `navi.json`, mesclar manualmente para não perder links atuais.

## Moonraker Update Manager

Snippet de exemplo:

```text
packaging/moonraker/update_manager_printora.conf
```

Adicionar manualmente ao `moonraker.conf` ou incluir como arquivo separado, conforme o padrão do ambiente.

Antes de reiniciar Moonraker:

```bash
cp /home/pi/printer_data/config/moonraker.conf /home/pi/printer_data/config/backups/moonraker.conf.before-printora
```

Depois:

```bash
sudo systemctl restart moonraker
curl -s http://127.0.0.1:7125/server/info
```

## Rollback

Parar e desabilitar serviço:

```bash
sudo systemctl stop printora.service
sudo systemctl disable printora.service
sudo rm -f /etc/systemd/system/printora.service
sudo systemctl daemon-reload
```

Remover link do Mainsail:

```bash
# Se o arquivo foi criado só para o Printora:
rm -f /home/pi/printer_data/config/.theme/navi.json
```

Se o `navi.json` já existia antes, restaurar o backup manual.

Remover entrada do Update Manager:

```bash
cp /home/pi/printer_data/config/backups/moonraker.conf.before-printora /home/pi/printer_data/config/moonraker.conf
sudo systemctl restart moonraker
```

Dados locais ficam em:

```text
/home/pi/.local/share/printora
```

Não remova esse diretório se quiser manter histórico, backups e inventário.
