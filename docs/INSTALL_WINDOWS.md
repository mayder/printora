# Instalação No Windows

Use este guia para instalar o Printora no Windows.

## Requisitos

- Windows com PowerShell;
- `winget` ou dependências instaladas manualmente;
- internet para baixar dependências ausentes;
- acesso de rede ao Moonraker da impressora.

## Instalação Recomendada

Abra o PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
cd $HOME
git clone https://github.com/mayder/printora.git
cd printora
.\scripts\install-windows.ps1
```

O instalador verifica Python `3.11+`, Git, Node.js/npm e pergunta antes de instalar o que estiver faltando via `winget`.

Abrir:

```text
http://127.0.0.1:8069
```

## Instalar Dependências Manualmente

Use apenas se quiser preparar o Windows antes de rodar o instalador.

```powershell
winget install --id Python.Python.3.13 -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Git.Git -e
```

Feche e reabra o PowerShell.

## Instalar O Printora Manualmente

```powershell
cd $HOME
git clone https://github.com/mayder/printora.git
cd printora
$env:PRINTORA_PORT="8069"
.\scripts\install_printora_windows.ps1 --apply --yes
```

## Rodar Manualmente

```powershell
cd $HOME\printora
$env:PRINTORA_HOST="0.0.0.0"
$env:PRINTORA_PORT="8069"
.\scripts\run_app_windows.ps1 --no-open
```

## Parar Ou Ver Status

```powershell
cd $HOME\printora
$env:PRINTORA_PORT="8069"
.\scripts\run_app_windows.ps1 --status
.\scripts\run_app_windows.ps1 --stop
```

## Dados Locais

```text
%LOCALAPPDATA%\Printora\printora.db
```
