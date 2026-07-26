# PKG-102 — Acessibilidade Universal

## Definition Of Ready

### Problema, Pessoas E Resultado

O Printora possui foco visível, temas e componentes responsivos em partes do
frontend, mas ainda não oferece um contrato único para preferências acessíveis,
semântica, anúncios de estado, mídia alternativa, linguagem simples ou
alternativas à visualização 3D. A experiência pode variar entre telas e
dispositivos, obrigando pessoas com necessidades visuais, auditivas, motoras ou
cognitivas a repetir ajustes.

Pessoas afetadas: operadores, makers, leitores da comunidade e administradores
que usam teclado, switch, voz, leitor de tela, zoom, alto contraste, redução de
movimento, legendas, audiodescrição ou linguagem simples. O resultado esperado
é disponibilizar oito famílias acessíveis, com preferências sincronizadas por
conta e aplicação local imediata. A hipótese mensurável é passar de zero para
oito famílias verificáveis, sem perda de tarefa a 320 px, zoom equivalente a
400%, teclado ou rede instável.

### Baseline Auditado

- o PKG-101 oferece tokens, foco, temas, redução de movimento e laboratório
  visual, mas seu rascunho é local e não representa preferências pessoais;
- não existe módulo backend `accessibility`, contrato público ou tabela de
  preferências acessíveis;
- o shell não aplica escala de texto, contraste adaptativo, linguagem simples,
  legendas, audiodescrição ou anúncios configuráveis;
- não existem rotas `SCR-0065` a `SCR-0072`;
- não há alternativa textual/tátil exportável compartilhada para amostras 3D;
- o produto não mede engajamento de acessibilidade nem persiste diagnóstico de
  saúde. Falhas são detectadas por testes e relatos.

Baseline de benefício: zero das oito famílias do pacote disponíveis como fluxo
integrado. Baseline de dano: bloqueio de tarefa, perda de foco, overflow,
movimento indesejado, ausência de alternativa e conflito de sincronização.

### Ownership E Contratos

- owner primário: `accessibility`;
- colaboradores: `shared`, `community` e `platform`;
- área frontend: `platform`;
- risco: `high`;
- contratos novos:
  - `GET /api/accessibility/v1/capabilities`;
  - `GET /api/accessibility/v1/preferences`;
  - `PUT /api/accessibility/v1/preferences`;
- consumidores: shell autenticado, central de acessibilidade e testes;
- contratos reutilizados: identidade, banco, idempotência, rate limit,
  observabilidade, transporte HTTP, design system, tema e navegação.

O módulo não importa detalhes internos de comunidade, operação ou impressora.
Preferências são um contrato compartilhado e nunca concedem permissão
operacional.

### Atores E Autorização

| Ator | Consultar catálogo | Ler preferências | Alterar preferências | Alterar outra conta |
|---|---:|---:|---:|---:|
| visitante | não | não | não | não |
| usuário autenticado | sim | sim, próprias | sim, próprias | não |
| administrador de plataforma | sim | sim, próprias | sim, próprias | não |

Autorização é deny-by-default por sessão. O identificador do usuário vem
exclusivamente da sessão e não é aceito no path ou payload.

### Entidades, Value Objects E Invariantes

`AccessibilityCapability` é catálogo imutável versionado em código.
`AccessibilityPreferences` é uma entidade por usuário, com revisão monotônica.
`AccessibilityPreferencePatch` é validado integralmente antes da escrita.

| Invariante | Garantia |
|---|---|
| catálogo | exatamente `CAP-09-01` a `CAP-09-08`, sem slug ou ID duplicado |
| rastreabilidade | sete `COM` contíguos e um `SCR` exclusivo por capacidade |
| isolamento | uma preferência pertence ao usuário autenticado e não aceita owner externo |
| unicidade | `user_id` é chave primária; retry nunca cria segunda preferência |
| concorrência | `expected_revision` divergente responde conflito sem escrita parcial |
| idempotência | mesmo payload e revisão corrente não altera conteúdo nem duplica efeito |
| limites | enums, booleanos e escala entre 100% e 200% são validados na borda |
| segurança | payload não contém diagnóstico, deficiência, áudio, biometria, segredo ou PII livre |
| compatibilidade | contrato `v1` é aditivo e declara compatibilidade `1.x` |

Máquina de estados:

```text
absent -> defaults(revision 0) -> saved(revision 1)
saved(N) -> saved(N+1)
saved(N) -> unchanged(N)
saved(N) -> conflict(N) -> reload -> saved(N+1)
loading -> error -> loading
ready|editing -> offline -> ready
```

Não existe estado de exclusão ou cleanup automático neste pacote.

### Comandos, Consultas E Efeitos

- consultas: catálogo e preferências próprias;
- comando: substituir atomicamente as preferências próprias com revisão
  esperada e `Idempotency-Key`;
- efeitos: aplicar atributos semânticos no documento e salvar uma única linha;
- exportação tátil: artefato SVG local, sem upload ou persistência;
- eventos, jobs, filas, webhooks, cobrança, moderação e comandos físicos: não
  aplicável.

### Dados, Retenção, Exportação E Banco

Preferências revelam adaptações de interface e são tratadas como dado pessoal
sensível por inferência. O banco armazena somente enums, booleanos, escala e
revisão; não armazena diagnóstico, justificativa ou conteúdo livre. Logs não
registram payload.

A tabela `accessibility_preferences` é criada pelos scripts idempotentes
`backend/sql/086_accessibility_preferences.sql` e
`backend/sql/postgresql/018_accessibility_preferences.sql`. A linha acompanha
a conta enquanto ela existir. Este pacote não executa exclusão, retenção
automática ou `ON DELETE CASCADE`; a referência usa `ON DELETE RESTRICT`.
Exportação é a própria resposta autenticada do contrato.

Ordem: aplicar o SQL PostgreSQL privilegiado antes da release cloud; SQLite
local aplica o script numerado no bootstrap. Validação: tabela, constraints,
índice, primeira execução, reexecução e concorrência. Rollback: reverter código
e preservar a tabela/linhas sem consumidores; não usar `DROP`, `DELETE`,
restauração de snapshot ou cleanup.

### Ameaça, Abuso E Limites

| Ameaça/abuso | Controle |
|---|---|
| leitura de outra conta | owner derivado da sessão; sem parâmetro de usuário |
| mass assignment | contrato fechado e campos explícitos |
| replay/duplicidade | chave idempotente global e chave primária por usuário |
| lost update entre dispositivos | revisão otimista e HTTP 409 |
| enumeração sem sessão | todos os endpoints exigem autenticação |
| inferência em logs | payload e valores não são logados |
| XSS em alternativa | conteúdo fixo/texto React; SVG gerado com texto controlado |
| payload excessivo | contrato pequeno, enums e limites rígidos |
| adaptação bloquear operação | defaults seguros e restauração por escrita aditiva |
| movimento/contraste causar dano | preferência explícita e respeito ao sistema operacional |

Nenhuma preferência aciona impressora, agente, Moonraker, firmware, pagamento,
publicação ou moderação.

### Telas E Rotas

As rotas `SCR-0065` a `SCR-0072` usam
`/community/accessibility/{capacidade}` para lista/filtro, `/detail` para
detalhe e `/edit` para formulário separado. A entrada fica em Sistema >
Acessibilidade.

Estados: loading, empty, error, success, partial, offline, forbidden e conflict.
Validação: 320, 375, 768, 1024 e 1440 px; retrato/paisagem; teclado, switch
equivalente, ordem de foco, nomes/roles, leitor de tela, anúncios, zoom 400%,
contraste, tema e redução de movimento.

### Orçamentos

- catálogo: oito itens, máximo 64 KiB;
- preferências: uma linha por usuário e resposta máxima de 8 KiB;
- mutação: uma transação e uma linha, timeout HTTP global;
- frontend: chunk lazy isolado, sem elevar o bundle inicial;
- concorrência: compare-and-swap por `revision`;
- SVG tátil: gerado localmente, máximo 32 KiB e sem dado livre;
- animação: removida quando SO ou preferência pedir redução.

### Testes, Observabilidade, Rollout E Rollback

- domínio: catálogo, valores, defaults e transições;
- repository: primeira gravação, reexecução, isolamento, conflito e concorrência;
- API: autenticação, contrato, validação, idempotência, 409 e N/N-1;
- frontend: lista/filtro, detalhe, editor, estados, sync, offline, retry e
  preservação do formulário;
- acessibilidade: Axe, teclado, foco, live regions, contraste, zoom, movimento
  reduzido e ausência de overflow;
- regressão: autenticação, shell, tema e design system;
- SQL: primeira execução, reexecução e constraints em SQLite e validação do
  script PostgreSQL;
- gates: testes focados, build/budget, E2E, dependências e `./check.sh`.

Métrica de benefício: oito famílias exercitáveis e conclusão da jornada por
matriz de largura, tema, entrada e tecnologia assistiva. Métrica de dano:
overflow, foco perdido, anúncio ausente, contraste insuficiente, movimento
indevido, preferência perdida ou conflito sobrescrito. Não há telemetria
individual nova; revisão periódica usa resultados agregados dos gates e
feedback voluntário sem diagnóstico.

Rollout é aditivo e não interrompe fluxos existentes. Smoke autenticado lê o
catálogo, salva uma preferência sintética, repete a chave idempotente, recarrega
e restaura defaults por nova revisão. Publicação e teste com pessoas dependem
de autorização separada. Rollback usa release N-1 e preserva schema/dados.

### Rastreabilidade E Independência

- `CAP-09-01` a `CAP-09-08`;
- `COM-0449` a `COM-0504`;
- `SCR-0065` a `SCR-0072`;
- dependências: base consolidada `PKG-01` a `PKG-100` e `PKG-101`;
- nenhum contrato, tabela, rota ou serviço de `PKG-103` ou posterior é usado.

## Plano De Evidência Por Lote

1. catálogo de conformidade WCAG e matriz de testes;
2. navegação por teclado/switch/voz equivalente;
3. semântica, landmarks e anúncios de estado;
4. contraste, escala, movimento e temas adaptativos;
5. legendas, transcrições e audiodescrição;
6. linguagem simples e baixa carga cognitiva;
7. alternativa textual e SVG tátil exportável;
8. preferências sincronizadas com conflito e idempotência;
9. jornada integrada, piloto local, benefício/dano e falhas;
10. revisão dos 56 `COM`, oito `SCR`, documentação, gate e commits.

