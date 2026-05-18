# Instalação Multiplataforma

O MayderPrintLab suporta quatro modos de uso:

- Raspberry/Manta/Linux com systemd;
- Linux/macOS em modo desenvolvimento;
- Windows em modo desenvolvimento;
- Docker Compose.

Nenhum instalador aplica mudanças destrutivas por padrão.

## macOS E Linux Dev

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

Dry-run no PowerShell:

```powershell
.\scripts\bootstrap_windows.ps1
```

Aplicar:

```powershell
.\scripts\bootstrap_windows.ps1 --apply
```

Este modo não instala serviço Windows. Ele prepara Python, frontend e build local.

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
