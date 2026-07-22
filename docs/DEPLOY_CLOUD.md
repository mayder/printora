# Deploy Cloud Do Printora

Alvo operacional:

- domínio: `print3dmaker.xyz`;
- branch publicada: `cloud`;
- SSH: `deploy@187.45.180.181:1158`;
- base: `/var/www/print3dmaker.xyz`;
- proxy: Nginx;
- slots: blue em `127.0.0.1:8069` e green em `127.0.0.1:8070`;
- agente: conexão outbound para `https://print3dmaker.xyz`.

## Estrutura

```text
/var/www/print3dmaker.xyz
├── current -> releases/<sha-ativo>
├── releases/<sha>/
│   ├── backend/
│   ├── frontend/dist/
│   ├── uv.lock
│   └── venv/
├── slots/
│   ├── blue -> ../releases/<sha>
│   └── green -> ../releases/<sha>
└── shared/
    ├── active-slot
    ├── backup-target.conf
    ├── data/
    ├── logs/
    ├── nginx/
    ├── slots/
    └── printora-cloud.env
```

Releases não compartilham venv, frontend nem dependência mutável. Dados e logs
ficam em `shared/`. O perfil cloud atual ainda usa SQLite até a transição
específica para PostgreSQL; não apague banco ou backup sem confirmação humana.

## Bootstrap Privilegiado

Antes de executar, salvar configuração Nginx e confirmar uma janela operacional.
O script mantém a instância legada em `8069`, instala units, upstreams, logrotate
e sudoers limitado, valida `visudo` e `nginx -t`, e recarrega o Nginx sem trocar
o backend ativo.

```bash
sudo PRINTORA_BASE_PATH=/var/www/print3dmaker.xyz \
  scripts/cloud/bootstrap-blue-green.sh
sudo /usr/local/sbin/printora-cloud-preflight
```

O primeiro deploy sobe green em `8070`, valida em loopback, troca o upstream e
só então encerra a instância legada. O segundo ciclo popula blue com release
imutável e torna rollback entre os dois slots comprovável.

## Backup Externo

Instalar `restic` e criar `/var/www/print3dmaker.xyz/shared/backup-target.conf`
com modo `0600`. O arquivo deve apontar para repositório fora do host e arquivo
de senha fora do release. Nunca versionar seu conteúdo. A chave/senha precisa
ter custódia externa ao servidor.

```bash
sudo systemctl start printora-cloud-backup.service
sudo -u deploy /usr/local/libexec/printora-cloud/restore-backup-test.sh
sudo systemctl enable --now printora-cloud-backup.timer
```

O backup usa a API de backup SQLite e valida `PRAGMA integrity_check`. O teste de
restore usa diretório temporário isolado e não inicia a aplicação. Retenção não
é apagada automaticamente; limpeza exige política e execução supervisionada.

## Deploy

O workflow `Deploy Printora Cloud`:

1. faz checkout de `cloud`;
2. instala dependências frontend e roda o gate completo;
3. gera bundle e SHA-256;
4. exige preflight privilegiado verde;
5. cria release e venv independentes usando `uv.lock` congelado;
6. inicia o slot inativo e exige `/ready`, `/health` e catálogo;
7. executa `nginx -t`, troca upstream e recarrega Nginx;
8. drena por 30 segundos e encerra o slot anterior;
9. valida endpoints públicos.

Candidato inválido é parado antes da troca e não recebe tráfego público.

## Rollback

O workflow `Rollback Printora Cloud` exige confirmação textual `ROLLBACK`. Ele
reativa o slot anterior, valida readiness, troca upstream e drena o release
atual. Banco, objetos e escritas posteriores não são restaurados nem sobrescritos.

Operação local equivalente:

```bash
sudo /usr/local/sbin/printora-cloud-rollback
```

## Validação

```bash
curl -fsS http://127.0.0.1:8069/health
curl -fsS http://127.0.0.1:8070/health
curl -fsS https://print3dmaker.xyz/health
curl -fsS https://print3dmaker.xyz/ready
curl -fsS https://print3dmaker.xyz/api/agent/update/manifest
python3 scripts/cloud/load-smoke.py https://print3dmaker.xyz/health \
  --requests 1000 --concurrency 30 --p95-ms 1000
```

Também validar WebSocket do agente, ausência de duplicidade de job, troca sob
carga, morte do candidato/ativo, rollback e reconexão dentro do SLO medido.

## DNS E TLS

GoDaddy permanece como registrador e Cloudflare como DNS/proxy. O modo TLS deve
ser `Full (strict)`, HTTPS obrigatório e WebSockets habilitados. O certificado
do origin precisa estar válido antes do preflight.
