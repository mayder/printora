# Manifesto Da Arquitetura Final

Data de corte: 2026-07-24

## Topologia canônica

- Cloud: Nginx distribui tráfego entre duas instâncias web da mesma release
  imutável. O slot N-1 fica aquecido somente para rollback de código.
- Persistência: PostgreSQL 16 é a única fonte relacional cloud. Redis contém
  somente estado recomponível. Objetos ficam no storage S3 compatível.
- Processamento: filas duráveis, outbox, inbox, leases e idempotência ficam no
  PostgreSQL; workers são processos systemd limitados.
- Busca e inteligência: busca usa índice PostgreSQL. Analytics e decisões
  consomem eventos sanitizados sob a role `printora_analytics`.
- Local: SQLite continua válido apenas no perfil local/Raspberry. Não existe
  fallback de PostgreSQL para SQLite no perfil cloud.
- Dispositivo: o agente Go continua sendo a fronteira operacional com a
  impressora. A consolidação cloud não altera Moonraker, Klipper, MCU ou
  configuração física.

## Serviços, owner e ciclo de vida

| Unit | Perfil | Owner | Versão/atualização | Alerta | Remoção segura |
| --- | --- | --- | --- | --- | --- |
| `printora-cloud@.service` | cloud | Plataforma | release Git imutável | readiness e journal | retirar do upstream, drenar e parar |
| `printora-cloud-worker@.service` | cloud | Plataforma | mesma release web | lease, fila e journal | drenar fila e parar target |
| `printora-cloud-workers.target` | cloud | Plataforma | mesma release web | estado das quatro filas | parar após drenagem |
| `printora-cloud-intelligence.service` | cloud | Dados | mesma release web | heartbeat, drift e journal | ativar kill switch e parar |
| `printora-cloud-backup.service` | cloud | SRE | scripts da release | timer, snapshot e restore | preservar último snapshot antes de desativar |
| `printora-cloud-backup.timer` | cloud | SRE | systemd da release | atraso do último backup | desativar somente após destino substituto |
| `printora-cloud-wal-sync.service` | cloud | SRE | scripts da release | atraso, duração e WAL externo corrente | preservar WAL e substituir a cópia antes de parar |
| `printora-cloud-wal-sync.timer` | cloud | SRE | systemd da release | monitor de RPO a cada minuto | desativar somente após proteção equivalente |
| `printora-cloud-recovery-monitor.service` | cloud | SRE | scripts da release | alerta fail-closed antes do RPO/RTO | corrigir a causa antes de desativar |
| `printora-cloud-recovery-monitor.timer` | cloud | SRE | systemd da release | execução a cada minuto | desativar somente após monitor equivalente |
| `printora-cloud-restore-test.service` | cloud | SRE | scripts da release | resultado, duração e reconciliação | preservar a última evidência válida |
| `printora-cloud-restore-test.timer` | cloud | SRE | systemd da release | atraso do teste semanal | desativar somente após ensaio substituto |
| `printora-cloud-recovery-alert@.service` | cloud | SRE | scripts da release | journal crítico e webhook opcional | manter owner e canal substituto |
| `redis-printora.service` | cloud | Plataforma | pacote do SO | readiness e memória | esvaziar cache e parar após consumidores |
| `minio-printora.service` | cloud | Plataforma | binário com checksum | readiness, capacidade e backup | reconciliar e copiar objetos antes de parar |
| `postgresql-printora-limits.conf` | cloud | SRE | pacote PostgreSQL 16 | memória, I/O e conexões | remover apenas junto da instância |
| `printora.service` | local | Dispositivo | instalador local versionado | doctor e journal local | parar após confirmar outro launcher |

Lockfiles canônicos: `backend/uv.lock`, `frontend/package-lock.json` e
`agent/go.sum`. O workflow gera SBOM CycloneDX reproduzível para backend,
frontend e agente com checksums SHA-256. Atualizações seguem pull request, gate
completo, scanner de segredo/dependência, deploy blue/green e rollback.

## Artefatos aposentados

Os itens abaixo devem permanecer ausentes e são bloqueados pelo scanner:

- transition outbox e estado de replicação SQLite/PostgreSQL;
- snapshot, importação, replicação e reconciliação da transição SQLite;
- canário/cutover PostgreSQL temporário;
- backup/restore cloud baseado em SQLite;
- flags `SQLITE_SHADOW`, `POSTGRESQL_SHADOW`, `DUAL_READ`, `DUAL_WRITE` e
  `TRANSITION_OUTBOX`;
- contrato interno `database_transition`.

Termos de negócio como transição de estado de pedido e bridge USB-CAN de
firmware não são bridges arquiteturais e continuam válidos. Histórico em
decisões e auditorias permanece como evidência, não como runtime.

## Inventário de dados e contratos

- Tabelas cloud: scripts PostgreSQL versionados e extensões exigidas pelo
  startup; schema sem extensão pendente.
- Objetos: referências canônicas em `cloud_objects`, reconciliação contra o
  bucket e versões incluídas no backup.
- Jobs: `durable_jobs`, `outbox_events` e `inbox_receipts` são canônicos;
  Redis nunca é fonte de recuperação.
- Contratos: OpenAPI e realtime possuem snapshots versionados e compatibilidade
  N/N-1 durante drenagem.
- Retenção: auditoria, jobs, objetos temporários, analytics e backups têm
  preview/limites documentados. Exclusão física requer confirmação própria.

## Revisão de limites e arquivos grandes

O inventário modular define owner para cada módulo, bloqueia ciclos e mantém
domain/application sem framework ou driver. Os maiores arquivos existentes
(`social_catalog.py`, telas de comunidade/setup/autenticação e serviços
operacionais históricos) foram classificados como dívida incremental, não como
bridge de transição. Eles não cresceram neste fechamento; novas capacidades
devem entrar em módulos menores e extrações precisam preservar contratos e
testes antes de remover o arquivo original.

## Rollback e recuperação

Rollback de código troca para a release N-1 sem restaurar banco antigo.
Recuperação física usa PostgreSQL base backup + WAL, objetos versionados e
configuração criptografada externa. O host único oferece redundância de
processo, não alta disponibilidade física. Nenhuma tabela, arquivo de usuário,
backup ou objeto é removido por este manifesto ou pelo scanner.
