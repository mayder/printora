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
ficam em `shared/`. O perfil cloud usa exclusivamente o cluster PostgreSQL
dedicado `16/printora` em `127.0.0.1:5433`; a credencial fica em
`/etc/printora-cloud/postgresql.env`, fora do release. A origem anterior e seus
backups permanecem preservados e não podem ser removidos sem confirmação humana.

## Bootstrap Privilegiado

Antes de executar, salvar configuração Nginx e confirmar uma janela operacional.
O script instala units, upstreams, logrotate e sudoers limitado, valida `visudo`
e `nginx -t`, e recarrega o Nginx sem trocar o backend ativo.

```bash
sudo PRINTORA_POSTGRESQL_PASSWORD_FILE=/etc/printora-cloud/postgresql-password \
  scripts/cloud/bootstrap-postgresql.sh
sudo PRINTORA_BASE_PATH=/var/www/print3dmaker.xyz \
  scripts/cloud/bootstrap-blue-green.sh
sudo /usr/local/sbin/printora-cloud-preflight
```

O primeiro deploy sobe green em `8070` e valida em loopback antes da troca. O
segundo ciclo popula blue com release imutável e torna rollback entre os dois
slots comprovável. Depois da migração inicial, unit e venv compartilhados são
removidos; apenas `printora-cloud@blue` e `printora-cloud@green` são válidos.

## Backup Externo

Instalar `restic` e criar `/var/www/print3dmaker.xyz/shared/backup-target.conf`
com modo `0600`. O arquivo deve apontar para repositório fora do host e arquivo
de senha fora do release. Nunca versionar seu conteúdo. A chave/senha precisa
ter custódia externa ao servidor.

```bash
sudo systemctl start printora-cloud-backup.service
sudo systemd-run --wait --collect \
  --unit=printora-cloud-restore-test \
  --property=CPUQuota=20% \
  --property='IOReadBandwidthMax=/dev/sda4 10M' \
  --property='IOWriteBandwidthMax=/dev/sda4 10M' \
  /usr/local/libexec/printora-cloud/restore-postgresql-backup-test.sh
sudo systemctl enable --now printora-cloud-backup.timer
```

O backup combina `pg_basebackup`, WAL e dump lógico com checksum. O teste de
restore promove um cluster temporário isolado, valida tabelas, versões e FKs e
não inicia a aplicação. Retenção não é apagada automaticamente; limpeza exige
política e execução supervisionada.
O serviço usa cache dedicado em `shared/backup-cache`, limite alto de 6 GB,
limite máximo de 8 GB e no máximo 200% de CPU. O preflight exige acesso ao
repositório, 2 GB de RAM, 20 GB de disco e um milhão de inodes disponíveis.

## Deploy

O workflow `Deploy Printora Cloud`:

1. faz checkout de `cloud`;
2. instala dependências frontend e roda o gate completo em modo estrito;
3. audita dependências Python, Node e Go;
4. gera SBOM CycloneDX reproduzível e checksums em `.artifacts/sbom`;
5. gera bundle e SHA-256 incluindo o SBOM;
6. exige preflight privilegiado verde;
7. cria release e venv independentes usando `uv.lock` congelado;
8. inicia o slot inativo e exige `/ready`, `/health` e catálogo;
9. executa `nginx -t`, troca upstream e recarrega Nginx;
10. drena por 30 segundos, reinicia N-1 sem conexões antigas e o mantém como
    backup aquecido do Nginx;
11. valida endpoints públicos.

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
