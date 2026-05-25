# Instalação No Android Com Termux

Use este guia para transformar um Android em host local do Printora.

Sem root, use a porta `8069`. Portas abaixo de `1024`, como `80`, exigem root.

## Requisitos

- Android com Termux;
- Termux:Boot para iniciar no boot;
- Wi-Fi estável;
- otimização de bateria desativada para Termux e Termux:Boot;
- internet para baixar dependências ausentes;
- opcional: ADB no computador para instalar e copiar arquivos.

## Instalação Recomendada

No Termux:

```bash
cd "$HOME"
git clone https://github.com/mayder/printora.git Printora
cd Printora
chmod +x check.sh scripts/*.sh scripts/*.py
./scripts/install-android-termux.sh
```

O instalador verifica Python, Node.js/npm, Git, OpenSSH, tmux, Rust, clang, make, pkg-config, curl e Termux:API. Se faltar algo, ele pergunta antes de instalar via `pkg`.

Abra o app Termux:Boot uma vez depois da instalação. Remova a otimização de bateria do Termux e do Termux:Boot.

## Instalar Dependências Manualmente

Use apenas se quiser preparar o Termux antes de rodar o instalador.

```bash
pkg update
pkg upgrade
pkg install python nodejs git openssh tmux rust clang make pkg-config curl termux-api
```

## Instalar Com Boot Automático Manualmente

```bash
cd "$HOME/Printora"
PRINTORA_PORT=8069 PRINTORA_DATA_DIR="$HOME/.local/share/printora" ./scripts/install_printora.sh --apply --yes
```

## Rodar Manualmente

```bash
cd "$HOME/Printora"
HTTP_PORT=8069 PUBLIC_PORT=8069 ./scripts/android_start_printora.sh
```

Abrir na rede:

```text
http://printora.local:8069
```

Se `printora.local` não resolver, descubra o IP do Android:

```bash
ip -o -4 addr show wlan0
```

Exemplo:

```text
http://192.168.15.16:8069
```

## Validar

```bash
curl -s http://127.0.0.1:8069/health
tmux ls
tmux capture-pane -pt printora -S -80
tmux capture-pane -pt printora-mdns -S -80
```

## Dados Locais

```text
~/.local/share/printora/printora.db
```
