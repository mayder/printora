# Instalação Com Docker

Use Docker quando quiser isolar dependências e persistir dados em volume.

## Requisitos

- Docker;
- Docker Compose.

## Instalar Docker

macOS/Windows:

- instale Docker Desktop;
- reinicie o terminal.

Linux Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Permitir uso sem `sudo` no Linux:

```bash
sudo usermod -aG docker "$USER"
```

Faça logout/login depois.

## Rodar

```bash
cd /caminho/para/printora
docker compose up --build
```

Abrir:

```text
http://127.0.0.1:8069
```

Rodar em background:

```bash
docker compose up -d --build
```

Ver logs:

```bash
docker compose logs -f printora
```

Parar:

```bash
docker compose down
```

## Dados Locais

```text
volume Docker: printora-data
container path: /data/printora.db
```
