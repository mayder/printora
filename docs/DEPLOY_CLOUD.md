# Deploy Cloud Do Printora

Publicacao planejada:

- produto: Printora;
- dominio publico: `print3dmaker.xyz`;
- DNS recomendado: Cloudflare;
- branch de publicacao: `cloud`;
- alvo SSH: `deploy@187.45.180.181:1158`;
- path base no servidor: `/var/www/print3dmaker.xyz`;
- servidor de aplicacao: Python/FastAPI atrás de Nginx;
- porta interna: `127.0.0.1:8069`;
- agente: conexao outbound para `https://print3dmaker.xyz`.

## DNS

Use a GoDaddy apenas como registrador. Configure os nameservers do dominio para
os nameservers da Cloudflare.

Registros esperados na Cloudflare:

```text
A      print3dmaker.xyz      <IP_DO_SERVIDOR>      proxied
CNAME  www                   print3dmaker.xyz      proxied
```

SSL/TLS na Cloudflare:

```text
Full (strict)
Always Use HTTPS: enabled
WebSockets: enabled
```

Se o servidor ainda nao tiver certificado valido, use temporariamente `Full`
somente durante a primeira subida e volte para `Full (strict)` depois de emitir
certificado no origin.

## Servidor

Arquivo de referencia sem segredo:

```bash
packaging/cloud/production-target.env.example
```

O servidor atual usa Python 3.12, Nginx e systemd. Docker/Node nao ficam
disponiveis para o usuario `deploy`; por isso o frontend deve ser buildado antes
do upload e o backend roda via venv Python.

Estrutura esperada:

```text
/var/www/print3dmaker.xyz
├── current -> releases/<versao>
├── releases/
└── shared/
    ├── data/
    ├── logs/
    ├── printora-cloud.env
    └── venv/
```

Validar localmente no servidor:

```bash
curl -fsS http://127.0.0.1:8069/health
curl -fsS http://127.0.0.1:8069/api/agent/update/manifest
```

Nginx:

```bash
sudo cp packaging/nginx/print3dmaker.xyz.conf /etc/nginx/sites-available/print3dmaker.xyz.conf
sudo ln -sfn /etc/nginx/sites-available/print3dmaker.xyz.conf /etc/nginx/sites-enabled/print3dmaker.xyz.conf
sudo certbot --nginx -d print3dmaker.xyz -d www.print3dmaker.xyz
sudo nginx -t
sudo systemctl reload nginx
```

Se o certificado ainda nao existir, emita antes de ativar o modo `Full (strict)`
na Cloudflare.

Systemd:

```bash
sudo cp packaging/systemd/printora-cloud.service /etc/systemd/system/printora-cloud.service
sudo systemctl daemon-reload
sudo systemctl enable --now printora-cloud.service
sudo systemctl status printora-cloud.service --no-pager
```

Validar publico:

```bash
curl -fsS https://print3dmaker.xyz/health
curl -fsS https://print3dmaker.xyz/api/agent/update/manifest
```

## Agente

O agente deve usar:

```json
{
  "api_base_url": "https://print3dmaker.xyz",
  "update_manifest_url": "https://print3dmaker.xyz/api/agent/update/manifest"
}
```

O pareamento normal pela UI gera o comando completo com token curto. Nao grave
`ptr_pair_*`, `ptr_agent_*` ou `ptr_sess_*` em arquivo versionado.

## Rollback

Parar somente o Printora:

```bash
sudo systemctl stop printora-cloud.service
```

Desativar vhost:

```bash
sudo rm -f /etc/nginx/sites-enabled/print3dmaker.xyz.conf
sudo nginx -t
sudo systemctl reload nginx
```

Voltar DNS na Cloudflare para outro origin exige apenas editar o registro `A`.

## Smoke Test

- `GET /health` retorna sucesso.
- frontend abre em `https://print3dmaker.xyz`.
- `GET /api/agent/update/manifest` retorna JSON.
- WebSocket do agente conecta em `/api/agent/ws` via Cloudflare.
- instalador do agente gerado pela UI usa `https://print3dmaker.xyz`.
