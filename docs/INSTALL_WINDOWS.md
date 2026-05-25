# Instalação No Windows

Use este guia para instalar o Printora no Windows.

## Requisitos

- Windows com PowerShell;
- Python `3.11+`;
- Node.js/npm;
- Git;
- acesso de rede ao Moonraker da impressora.

## Instalar Dependências

Abra o PowerShell e rode:

```powershell
winget install --id Python.Python.3.13 -e
winget install --id OpenJS.NodeJS.LTS -e
winget install --id Git.Git -e
```

Feche e reabra o PowerShell.

## Liberar Execução Nesta Sessão

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Instalar O Printora

```powershell
cd $HOME
git clone https://github.com/mayder/printora.git
cd printora
$env:PRINTORA_PORT="8069"
.\scripts\install_printora_windows.ps1 --apply --yes
```

Abrir:

```text
http://127.0.0.1:8069
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
