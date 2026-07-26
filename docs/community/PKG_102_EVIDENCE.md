# PKG-102 — Evidência De Fechamento

Data: 2026-07-26
Estado: concluído e publicável; publicação e piloto externo não executados.

## Resultado Entregue

O pacote entrega o domínio compartilhado `accessibility`, catálogo autenticado
com oito capacidades, preferências sincronizadas por usuário e uma central
acessível em Sistema > Acessibilidade. Lista/filtro, detalhe e edição usam
rotas separadas; a aplicação das preferências ocorre após autenticação sem
acoplar regra de negócio à tela.

Os contratos `GET /api/accessibility/v1/capabilities`,
`GET /api/accessibility/v1/preferences` e
`PUT /api/accessibility/v1/preferences` cobrem leitura, atualização
idempotente e concorrência otimista. A atualização deriva o usuário da sessão,
exige `Idempotency-Key` e rejeita revisão divergente com conflito explícito.

## Matriz CAP, COM E SCR

Cada faixa `COM` contém as lentes de produto, tela, mobile, acessibilidade,
confiança, impacto e qualidade documentadas no backlog comunitário.

| Capacidade | COM | SCR | Evidência funcional |
|---|---|---|---|
| `CAP-09-01` | `COM-0449`–`COM-0455` | `SCR-0065` | catálogo WCAG, Axe e matriz desktop/mobile |
| `CAP-09-02` | `COM-0456`–`COM-0462` | `SCR-0066` | teclado, foco, switch equivalente e rótulos para voz |
| `CAP-09-03` | `COM-0463`–`COM-0469` | `SCR-0067` | landmarks, semântica e regiões de anúncio |
| `CAP-09-04` | `COM-0470`–`COM-0476` | `SCR-0068` | contraste, escala, tema e redução de movimento |
| `CAP-09-05` | `COM-0477`–`COM-0483` | `SCR-0069` | legendas, transcrição e audiodescrição configuráveis |
| `CAP-09-06` | `COM-0484`–`COM-0490` | `SCR-0070` | linguagem simples e modo de baixa carga cognitiva |
| `CAP-09-07` | `COM-0491`–`COM-0497` | `SCR-0071` | alternativa textual e artefato tátil SVG/BRF local |
| `CAP-09-08` | `COM-0498`–`COM-0504` | `SCR-0072` | preferências sincronizadas, idempotência e conflito |

Para todas as linhas:

- produto: owner, autorização, contrato, persistência, rollout e rollback estão
  em `PKG_102_ACCESSIBILITY.md` e `DEC-20260726-06`;
- tela: lista/filtro, detalhe e editor têm URLs e responsabilidades distintas;
- mobile: o E2E valida 320, 375, 768, 1024 e 1440 px, incluindo reflow sem
  overflow e snapshots desktop/mobile;
- acessibilidade: Axe bloqueia violações críticas/sérias; teclado, ordem de
  foco, nomes, roles, live regions, contraste e movimento reduzido são
  verificados;
- confiança: sessão é obrigatória, `user_id` nunca vem do payload, enums e
  limites são fechados, e valores de preferência não entram em logs;
- impacto: o benefício é a disponibilidade verificável das oito famílias; dano
  é medido por overflow, foco perdido, anúncio ausente, contraste insuficiente,
  movimento indevido, preferência perdida ou conflito sobrescrito;
- qualidade: testes de domínio, API, UI e E2E usam dados sintéticos e cobrem
  autenticação, isolamento, offline, timeout, `429`, `5xx` e conflito.

## Idempotência, Concorrência E Falhas

- a mesma chave idempotente e o mesmo payload retornam o resultado anterior;
- reuso da chave com payload diferente é rejeitado;
- `revision` implementa compare-and-swap e impede lost update;
- usuários distintos não leem nem alteram preferências entre si;
- offline mantém o formulário atual e bloqueia gravação remota;
- timeout, `429` e `5xx` preservam estado local e permitem retry;
- nenhuma repetição cria cobrança, mensagem, arquivo persistido ou comando
  físico.

## Banco, Retenção E Observabilidade

Ordem de execução:

1. SQLite local: `backend/sql/086_accessibility_preferences.sql`, após
   `085_analytics_intelligence.sql`;
2. PostgreSQL por ambiente: `backend/sql/postgresql/018_accessibility_preferences.sql`,
   antes da release que consome o schema.

Ambos os scripts são aditivos e idempotentes por `CREATE TABLE IF NOT EXISTS`.
Não contêm migration, `DROP`, `DELETE`, backfill ou alteração destrutiva.
`ON DELETE RESTRICT` impede remoção em cascata do usuário. A validação repete o
script e verifica tabela, constraints, defaults, isolamento e conflito.

Rollback restaura a release N-1 e preserva tabela e dados. Não há log persistido
novo; a observabilidade HTTP global registra somente metadados seguros. Uma
linha pequena por usuário é atualizada no lugar, sem histórico ou cleanup novo.

## Evidência Executada

- backend focado: 12 testes de catálogo, contrato, SQL, autenticação,
  idempotência, isolamento e conflito;
- frontend focado: quatro testes de tela, documento, artefato tátil e aplicação
  de preferências;
- regressão E2E: quatro cenários próprios em Chromium desktop/mobile, com Axe,
  teclado, reflow, offline, erro, conflito e snapshots aprovados;
- regressão completa: 30 cenários E2E;
- bundle: tela em chunk lazy; total `3.432.387` bytes e `846.062` bytes gzip,
  dentro dos tetos documentados;
- mutation score: `70,57%`, mínimo `60%`;
- coverage gate: aprovado; código crítico do frontend acima do mínimo;
- dependências: 55 pacotes, 440 capacidades, 3.080 requisitos e 440 telas em
  ordem topológica, com ownership e sem dependência futura;
- gate final obrigatório:
  `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

## Rollout, Smoke E Rollback

O rollout é aditivo e não foi executado. O smoke autenticado consulta catálogo
e preferências, grava dados sintéticos, repete a chave idempotente, recarrega,
simula conflito e restaura defaults por nova revisão.

Publicação, aplicação do SQL em ambiente remoto e teste com pessoas
representativas exigem autorização e coordenação separadas. Sua ausência não é
tratada como evidência equivalente: permanece como validação operacional
externa posterior à entrega local publicável.

O rollback restaura a release N-1 e preserva schema/dados. Não executar limpeza
de banco, restauração de snapshot, `DROP` ou `DELETE`. Nenhum fluxo de
impressora, agente, Moonraker, firmware ou pagamento foi acionado.

## Commits Lógicos

- `d434de4` — contraste do botão primário e baseline visual;
- `4641397` — arquitetura, ameaças e Definition of Ready;
- `b181548` — contrato backend, persistência e SQL idempotente;
- `cc59f75` — central acessível, preferências globais e regressão de UI.
