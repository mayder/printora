# Instalação Por Plataforma

O Printora roda como aplicação local na porta padrão `8069`.

Escolha o guia do seu sistema:

- [macOS](INSTALL_MACOS.md)
- [Windows](INSTALL_WINDOWS.md)
- [Android com Termux](INSTALL_ANDROID_TERMUX.md)
- [Linux/Raspberry/CB1/Manta](INSTALL_LINUX_RASPBERRY.md)
- [Docker](INSTALL_DOCKER.md)

## Validação Comum

Depois de iniciar:

```bash
curl -s http://127.0.0.1:8069/health
```

Resposta esperada:

```json
{"status":"ok","app":"Printora"}
```

## Dados Locais

- macOS: `~/Library/Application Support/Printora/printora.db`
- Windows: `%LOCALAPPDATA%\Printora\printora.db`
- Linux/Raspberry: `~/.local/share/printora/printora.db`
- Android/Termux: `~/.local/share/printora/printora.db`
- Docker: volume `printora-data`
