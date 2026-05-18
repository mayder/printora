# Instalação Na Raspberry Pi

Este roteiro integra o MayderPrintLab com Klipper, Moonraker e Mainsail sem alterar configurações da impressora automaticamente.

## Pré-requisitos

- Raspberry Pi com Klipper/Moonraker/Mainsail já funcionando.
- Acesso SSH.
- `python3`, `venv`, `npm`, `rsync` e `git`.
- Impressora parada antes de iniciar/reiniciar serviços.

## Instalação Segura

Rodar primeiro em dry-run:

```bash
cd /home/pi/MayderPrintLab
./scripts/install_raspberry.sh
```

Aplicar somente depois de revisar os comandos:

```bash
cd /home/pi/MayderPrintLab
./scripts/install_raspberry.sh --apply
```

O script:

- cria/atualiza `/home/pi/MayderPrintLab`;
- cria venv do backend;
- instala dependências Python;
- instala dependências frontend;
- gera build estático;
- cria `.env` se ainda não existir;
- copia `mayderprintlab.service`;
- habilita o serviço.

Ele não inicia o serviço automaticamente. Depois de revisar `.env`:

```bash
sudo systemctl start mayderprintlab.service
sudo systemctl status mayderprintlab.service --no-pager
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
packaging/moonraker/update_manager_mayderprintlab.conf
```

Adicionar manualmente ao `moonraker.conf` ou incluir como arquivo separado, conforme o padrão do ambiente.

Antes de reiniciar Moonraker:

```bash
cp /home/pi/printer_data/config/moonraker.conf /home/pi/printer_data/config/backups/moonraker.conf.before-mayderprintlab
```

Depois:

```bash
sudo systemctl restart moonraker
curl -s http://127.0.0.1:7125/server/info
```

## Rollback

Parar e desabilitar serviço:

```bash
sudo systemctl stop mayderprintlab.service
sudo systemctl disable mayderprintlab.service
sudo rm -f /etc/systemd/system/mayderprintlab.service
sudo systemctl daemon-reload
```

Remover link do Mainsail:

```bash
# Se o arquivo foi criado só para o MayderPrintLab:
rm -f /home/pi/printer_data/config/.theme/navi.json
```

Se o `navi.json` já existia antes, restaurar o backup manual.

Remover entrada do Update Manager:

```bash
cp /home/pi/printer_data/config/backups/moonraker.conf.before-mayderprintlab /home/pi/printer_data/config/moonraker.conf
sudo systemctl restart moonraker
```

Dados locais ficam em:

```text
/home/pi/.local/share/mayderprintlab
```

Não remova esse diretório se quiser manter histórico, backups e inventário.
