# PKG-101 — Evidência De Fechamento

Data: 2026-07-26
Estado: concluído e publicável; publicação não executada.

## Resultado Entregue

O pacote entrega um domínio compartilhado `design_system`, catálogo autenticado
e somente leitura, tokens semânticos, estados coerentes, três densidades,
componentes responsivos, formulário longo com rascunho local e um laboratório
visual com regressão desktop/mobile. A entrada fica em Sistema > Design system.

O contrato `GET /api/design-system/v1/capabilities` expõe exatamente oito
capacidades, 56 requisitos e oito famílias de tela. Lista/filtro, detalhe e
edição local usam rotas separadas. Não existe endpoint mutável, comando físico,
telemetria individual ou dado canônico novo.

## Matriz CAP, COM E SCR

Cada faixa `COM` contém, nesta ordem, as lentes produto, tela, mobile,
acessibilidade, confiança, impacto e qualidade.

| Capacidade | COM | SCR | Evidência funcional |
|---|---|---|---|
| `CAP-18-01` | `COM-0953`–`COM-0959` | `SCR-0137` | catálogo versionado e tabela de tokens semânticos |
| `CAP-18-02` | `COM-0960`–`COM-0966` | `SCR-0138` | hierarquia comum de contexto, título, conteúdo e ação |
| `CAP-18-03` | `COM-0967`–`COM-0973` | `SCR-0139` | cards, tabela e galeria sem perda de conteúdo |
| `CAP-18-04` | `COM-0974`–`COM-0980` | `SCR-0140` | densidades oficina, leitura e administração |
| `CAP-18-05` | `COM-0981`–`COM-0987` | `SCR-0141` | formulário longo, revisão, save idempotente e conflito |
| `CAP-18-06` | `COM-0988`–`COM-0994` | `SCR-0142` | oito estados textuais, recuperáveis e sem dependência de cor |
| `CAP-18-07` | `COM-0995`–`COM-1001` | `SCR-0143` | feedback, foco visível e redução de movimento |
| `CAP-18-08` | `COM-1002`–`COM-1008` | `SCR-0144` | laboratório e snapshots desktop escuro/mobile claro |

Para todas as linhas:

- produto: contrato, owner, autorização, persistência e rollback estão em
  `PKG_101_DESIGN_SYSTEM.md` e `DEC-20260726-05`;
- tela: lista/filtro, detalhe e editor são estados e URLs separados;
- mobile: o E2E bloqueia overflow em 320, 375, 768, 1024 e 1440 px, incluindo
  paisagem; 320 CSS px comprova o reflow equivalente a 400% em 1280 px;
- acessibilidade: Axe bloqueia violações críticas/sérias; teclado, ordem de
  foco, outline, nomes, roles, contraste claro/escuro e redução de movimento
  são verificados; as quatro referências visuais foram inspecionadas;
- confiança: sessão é obrigatória, conteúdo é fixo ou texto React, o rascunho é
  limitado a 32 KiB e não contém PII. Moderação, denúncia e bloqueio não se
  aplicam porque não existe conteúdo público ou interação entre pessoas;
- impacto: baseline de zero passou a oito famílias verificáveis. Os recortes
  são tema, largura, orientação, densidade e movimento reduzido; overflow,
  perda de foco, contraste e snapshot divergente falham o gate. A revisão é
  repetida a cada mudança visual, sem métrica de vaidade ou rastreamento pessoal;
- qualidade: testes de domínio, API, UI e E2E usam dados sintéticos e cobrem
  autenticação, permissão, timeout, `429`, `5xx`, offline, conflito e regressão.

## Idempotência, Concorrência E Falhas

- chamadas GET repetidas não gravam estado;
- salvar o mesmo rascunho mantém uma única chave versionada;
- revisão divergente entre abas bloqueia sobrescrita e exige recarga explícita;
- timeout, `429` e `5xx` mantêm o rascunho e oferecem retry;
- offline preserva o rascunho local e identifica o catálogo indisponível;
- nenhuma repetição cria registro, evento, cobrança, mensagem, arquivo ou
  comando de impressora.

## Banco, Retenção E Observabilidade

Não houve alteração de banco. Nenhum script SQL é necessário porque o catálogo
é código versionado e o rascunho fica no navegador. Não foram usados migration,
`DROP`, `DELETE` ou limpeza. Uma futura persistência canônica exige script
idempotente em `backend/sql/`, ordem, validação e rollback próprios.

Não há log persistido novo, PII ou política de cleanup adicional. Falhas HTTP
seguem a observabilidade e o rate limit globais existentes; o laboratório não
registra o conteúdo do rascunho.

## Evidência Executada

- backend focado: oito testes de catálogo, contrato, autenticação e tamanho;
- frontend focado: rascunho, tela, estados e recuperação;
- regressão E2E: desktop Chromium/tema escuro e mobile Chromium/tema claro,
  com snapshots aprovados e dados sintéticos isolados;
- bundle: lazy chunk próprio; total `3.413.730` bytes e `839.557` bytes gzip,
  dentro dos tetos documentados;
- mutation score: `70,34%`, mínimo `60%`;
- coverage gate: aprovado;
- dependências: 55 pacotes, 440 capacidades, 3.080 requisitos e 440 telas em
  ordem topológica, sem dependência futura;
- gate final obrigatório: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

Nota de vigência: a evidência acima registra o gate executado no fechamento do
PKG-101. A `DEC-20260727-01` substituiu posteriormente a sequência de 55
pacotes por portfólio ativo explícito; isso não altera a evidência funcional do
pacote concluído.

## Rollout, Smoke E Rollback

Rollout é aditivo e não foi executado. O smoke autenticado consulta o catálogo,
abre uma rota base, detalhe e editor, salva/recarrega um rascunho e confirma que
nenhuma requisição mutável ocorreu.

Rollback é restaurar a release N-1. Não executar SQL, limpeza de banco,
restauração de snapshot ou remoção de dado local. O rascunho de schema
desconhecido permanece inerte e o parser usa fallback seguro.

## Commits Lógicos

- `7afcc3e` — arquitetura e Definition of Ready;
- `cf2e12a` — contrato backend e fronteira modular;
- `3f5585b` — fundação visual e persistência local;
- `6ce4cc2` — laboratório e rotas;
- `efdc8cc` — regressão visual, acessibilidade e recuperação.
