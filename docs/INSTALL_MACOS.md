# Instalação No macOS

Use este guia para instalar o Printora em um Mac.

## Requisitos

- macOS com Terminal;
- Git;
- Python `3.11+`;
- Node.js/npm;
- acesso de rede ao Moonraker da impressora.

## Instalar Dependências

```bash
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install git python node
```

Se o Mac já tiver um Python antigo usado por outro sistema, não remova esse Python. O instalador do Printora procura um Python `3.11+` compatível e usa somente a venv local `backend/.venv`.

## Instalar O Printora

```bash
cd "$HOME"
git clone https://github.com/mayder/printora.git
cd printora
chmod +x "Abrir Printora.command" scripts/*.sh
PRINTORA_PORT=8069 ./scripts/install_printora.sh --apply --yes
```

Abrir:

```text
http://127.0.0.1:8069
```

## Forçar Um Python Específico

Use apenas se o `python3` padrão do Mac for antigo.

```bash
cd "$HOME/printora"
PRINTORA_PYTHON_BIN=/usr/local/opt/python@3.14/bin/python3 PRINTORA_PORT=8069 ./scripts/install_printora.sh --apply --yes
```

Em Macs Apple Silicon, o caminho pode ser:

```bash
PRINTORA_PYTHON_BIN=/opt/homebrew/opt/python@3.14/bin/python3 PRINTORA_PORT=8069 ./scripts/install_printora.sh --apply --yes
```

## Rodar Manualmente

```bash
cd "$HOME/printora"
PRINTORA_HOST=0.0.0.0 PRINTORA_PORT=8069 ./scripts/run_app.sh --no-open
```

## Parar Ou Ver Status

```bash
cd "$HOME/printora"
PRINTORA_PORT=8069 ./scripts/run_app.sh --status
PRINTORA_PORT=8069 ./scripts/run_app.sh --stop
```

## Diagnóstico

```bash
cd "$HOME/printora"
PRINTORA_PORT=8069 ./scripts/doctor_install.sh
```

## Dados Locais

```text
~/Library/Application Support/Printora/printora.db
```

## Alternativa Com ZIP

Git é o caminho recomendado. ZIP funciona para instalação inicial, mas piora o fluxo de update.

```bash
curl -L -o "$HOME/Downloads/printora.zip" https://github.com/mayder/printora/archive/refs/heads/main.zip
cd "$HOME/Downloads"
unzip printora.zip
cd printora-main
chmod +x "Abrir Printora.command" scripts/*.sh
PRINTORA_PORT=8069 ./scripts/install_printora.sh --apply --yes
```
