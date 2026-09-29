# Execução Durável E Realtime Distribuído

Data: 2026-07-22
Escopo: outbox, inbox, jobs, idempotência, workers, Redis e sessões de agentes.

## Arquitetura Entregue

- PostgreSQL canônico para eventos, recibos, jobs, leases, idempotência, sessão e
  controle de worker;
- Redis dedicado por socket Unix, ACL, `allkeys-lru`, 256 MiB, sem persistência;
- workers systemd `outbox`, `critical`, `default` e `bulk`, vinculados à release
  imutável ativa;
- transição de worker por `SIGTERM`, drain e retomada por lease;
- sessão de agente com fencing no PostgreSQL e notificação pub/sub;
- polling/reconnect continua sendo caminho de recuperação quando Redis ou uma
  instância WebSocket falha;
- administração de pause/drain, métricas, dead-letter e replay deny-by-default.

## Evidência Local

- testes focados: atomicidade, ordem, dedupe, timeout, retry, dead-letter,
  idempotência, sessão multi-instância, Redis degradado e fatiamento agendado;
- Redis efêmero real: cache, rate limit, presença e publicação passaram;
- pub/sub Redis real entregou notificação entre publisher e subscriber;
- carga: 500 jobs, oito consumidores, 500 conclusões, zero duplicidade,
  170,38 jobs/s e p95 de claim em 129,177 ms;
- gate bloqueante elimina `asyncio.Queue`, `queue.Queue`, `deque` e `push_job`
  no backend runtime.

## Retenção E Rollback

Jobs/outbox/inbox terminais têm política de 30 dias; idempotência expira em 24
horas; sessões e workers encerrados em sete dias. A rotina é preview-only por
padrão e a exclusão requer confirmação textual explícita. Nenhuma limpeza foi
executada durante esta entrega.

Rollback drena workers, publica código N-1 compatível e preserva PostgreSQL. Uma
release sem worker deixa jobs enfileirados para forward-fix; Redis pode ser
recriado vazio. Nunca restaurar snapshot antigo sobre jobs/eventos confirmados.

## Evidência Remota

- workflow `29968900686` passou gate completo, auditorias de dependência, SBOM,
  preflight, blue/green e smoke; release ativa `79084f8`;
- `preflight` validou os dois slots, PostgreSQL, Redis, workers, backup, recursos,
  nginx e certificado;
- auditoria final: zero jobs de agente sem evento, zero leases expirados, 73
  eventos publicados e 73 jobs críticos concluídos;
- carga PostgreSQL: 500 jobs, oito consumidores, 500 conclusões, zero
  duplicidade, 10,29 jobs/s e p95 de claim em 484,162 ms;
- saturação solicitada de 2.000 jobs foi bloqueada na quota de 1.000. Os 1.000
  probes sintéticos pendentes foram marcados `canceled`, sem exclusão física;
- falha controlada: job `1574` foi retomado na tentativa 2 após expiração do
  lease e rejeitou o completion token antigo;
- restart de Redis manteve as contagens PostgreSQL em 1.537 jobs e 37 eventos,
  recompôs o socket com `PONG` e preservou dois apps e quatro workers ativos;
- rollback real para N-1 `686e5ca` e forward-deploy para `79084f8` passaram com
  drain/restart de workers, `data_restored=false` e schema revision 74;
- backpressure HTTP aceitou 600/1.000 e respondeu 429 nas 400 excedentes. Após
  recomposição do Redis, smoke controlado passou 500/500, zero erro e p95 de
  953,159 ms;
- o agente físico, Moonraker, Klipper, MCU e Raspberry Pi não foram acessados ou
  reiniciados durante a comprovação.

## Resultado

Todos os critérios do pacote foram comprovados. O arquivo SQLite anterior e os
backups continuam preservados; nenhuma retenção ou exclusão física foi executada.
