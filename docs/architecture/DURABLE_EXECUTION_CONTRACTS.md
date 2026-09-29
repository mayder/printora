# Contratos De Execução Durável

## Escopo

Eventos entre processos, jobs assíncronos, comandos repetíveis e sessões de
agentes usam PostgreSQL como fonte canônica. Redis pode acelerar notificação,
presença, cache e rate limit, mas sua ausência nunca altera o resultado de
negócio nem remove um job confirmado.

## Envelope De Evento V1

Campos obrigatórios:

- `event_id`: identificador global imutável e usado para deduplicação;
- `event_type`: nome estável no formato `<dominio>.<fato>`;
- `schema_version`: inteiro positivo;
- `aggregate_type` e `aggregate_id`: origem canônica;
- `ordering_key` e `sequence_no`: ordem total dentro do agregado;
- `payload`: dados mínimos do fato, sem segredo;
- `headers`: correlação, causalidade e tenant quando aplicável.

O produtor grava a mudança de negócio e `outbox_events` na mesma transação. Um
consumidor grava `inbox_receipts` antes do efeito. O par
`(consumer_name, event_id)` é único; o mesmo ID com hash de payload diferente é
conflito, não retry.

Compatibilidade:

- produtores N podem publicar V1 enquanto consumidores N-1 drenam;
- adicionar campo opcional é compatível;
- remover, renomear ou mudar semântica exige nova `schema_version`;
- contração só ocorre depois de não haver worker N-1 ativo nem evento antigo
  pendente/dead-letter;
- eventos desconhecidos não são descartados: permanecem pendentes ou vão para
  dead-letter com diagnóstico sanitizado.

## Job Durável V1

`job_key` é a chave idempotente global. `queue_name` separa criticidade:
`critical`, `default` e `bulk`. Menor número em `priority` executa primeiro. O
claim usa lock concorrente no PostgreSQL, cria `lease_token`, incrementa
`attempts` e define expiração. Somente o portador do token vigente pode renovar,
concluir ou reagendar o job.

Estados:

```text
queued -> leased -> succeeded
   ^         |
   |         +-> queued (retry com backoff)
   |         +-> dead_letter (limite atingido)
   +---------+ (lease expirado e retomado)
```

Estados terminais: `succeeded`, `failed`, `dead_letter`, `canceled`. Um lease
expirado nunca autoriza o worker anterior a confirmar resultado. Efeitos
externos também devem usar `job_key`/idempotency key no adapter de destino.

## Idempotência HTTP E Comandos

Operações repetíveis recebem `Idempotency-Key`. O escopo inclui identidade do
ator, método e rota normalizada. O hash cobre o corpo canônico. Repetição com o
mesmo hash devolve a resposta persistida; mesma chave com hash diferente retorna
conflito. Registro em processamento possui lease curto para recuperação de
processo morto e expiração operacional de 24 horas, ampliável por domínio.

## Sessão Realtime

`realtime_sessions` registra instância, agente, impressora, versão de protocolo,
heartbeat, expiração e último job confirmado. A conexão WebSocket existe apenas
na memória do processo que possui o socket; ela não é fila nem fonte canônica.
Notificações entre instâncias usam pub/sub recomponível e o agente sempre retoma
jobs por consulta PostgreSQL após reconnect com jitter.

## Backpressure, Retenção E Owner

- `critical`: fluxo P0/P1, concorrência 2 e sem bloqueio por fila bulk;
- `default`: trabalho interativo normal, concorrência 2;
- `bulk`: tarefas pesadas, concorrência 1 e quota estrita;
- retry usa backoff exponencial com jitter e limite por contrato;
- dead-letter tem owner do domínio, alerta por idade/volume e replay
  supervisionado com preview;
- payload de job/outbox/inbox: 30 dias após terminal;
- idempotência HTTP: 24 horas por padrão;
- sessões encerradas: 7 dias;
- métricas agregadas não carregam payload nem identificador sensível;
- limpeza física só será ativada após rotina com preview, auditoria e rollback.

## Threat Model Resumido

- duplicação/replay: chaves únicas, hash e efeito idempotente;
- concorrência: lock PostgreSQL, lease token e compare-and-set;
- tenant cruzado: owner explícito e autorização antes do enqueue/replay;
- payload hostil: schema versionado, limite de tamanho e validação por tipo;
- Redis comprometido ou vazio: nenhuma decisão canônica depende dele;
- worker antigo: drain N/N-1 antes de contração;
- segredo em evento/log: payload mínimo, sanitização e scan bloqueante;
- saturação: filas por classe, quota, prioridade e backpressure.
