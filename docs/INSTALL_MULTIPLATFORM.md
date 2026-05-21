# Instalação Multiplataforma

O MayderPrintLab suporta quatro modos de uso:

- Raspberry/Manta/Linux com systemd;
- Linux/macOS em modo desenvolvimento;
- Windows em modo desenvolvimento;
- Docker Compose.

Nenhum instalador aplica mudanças destrutivas por padrão.

## macOS E Linux Dev

Abrir direto:

```bash
./scripts/run_app.sh
```

No macOS também é possível abrir `Abrir MayderPrintLab.command` com duplo clique. A janela do terminal deve ficar aberta enquanto o app estiver em uso.

Dry-run:

```bash
./scripts/bootstrap_dev.sh
```

Aplicar:

```bash
./scripts/bootstrap_dev.sh --apply
```

Rodar backend:

```bash
./scripts/dev_backend.sh
```

Rodar frontend:

```bash
./scripts/dev_frontend.sh
```

Parar o processo iniciado pelo runner:

```bash
./scripts/run_app.sh --stop
```

Quando usar `Abrir MayderPrintLab.command`, para parar basta fechar a janela do terminal ou pressionar `Ctrl+C`.

No macOS, o banco padrão fica em:

```text
~/Library/Application Support/MayderPrintLab
```

## Raspberry, Manta, CB1 Ou Linux Com Systemd

Dry-run:

```bash
./scripts/install_raspberry.sh
```

Aplicar:

```bash
./scripts/install_raspberry.sh --apply
```

Esse instalador exige Linux com systemd. Ele não é para macOS ou Windows.

## Windows Dev

Abrir direto no PowerShell:

```powershell
.\scripts\run_app_windows.ps1
```

No Windows também é possível abrir `Abrir MayderPrintLab.bat` com duplo clique. A janela do PowerShell deve ficar aberta enquanto o app estiver em uso.

Dry-run no PowerShell:

```powershell
.\scripts\bootstrap_windows.ps1
```

Aplicar:

```powershell
.\scripts\bootstrap_windows.ps1 --apply
```

Este modo não instala serviço Windows. Ele prepara Python, frontend e build local.

Parar processo em background iniciado pelo runner:

```powershell
.\scripts\run_app_windows.ps1 --stop
```

Quando usar `Abrir MayderPrintLab.bat`, para parar basta fechar a janela do PowerShell ou pressionar `Ctrl+C`.

## Docker Compose

Build e execução:

```bash
docker compose up --build
```

URL:

```text
http://127.0.0.1:8085
```

O volume `mayderprintlab-data` preserva o SQLite.

## Recomendação De Uso

- Para desenvolvimento no seu Mac: `bootstrap_dev.sh --apply`.
- Para centralizar várias impressoras na rede: Docker ou Mac/Linux dev.
- Para instalar na Raspberry/Manta da impressora: `install_raspberry.sh --apply`.
- Para Windows: começar com PowerShell dev; serviço Windows fica para etapa futura.
