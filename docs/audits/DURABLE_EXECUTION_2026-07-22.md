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

## Evidência Remota Pendente

Preencher no fechamento com release, schema, serviços, carga/soak, worker morto,
Redis reiniciado, drain/rollback e smoke público. A impressora física e seu host
não fazem parte desta validação.
