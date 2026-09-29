# Padrão De Execução Dos Pacotes Ativos

Este documento é bloqueante somente para IDs com status `active` em
`PACKAGE_PORTFOLIO.csv`. Ele transforma os princípios gerais do projeto em um
contrato operacional verificável para cada janela de implementação. Inventário
`COM/CAP/SCR` não autoriza trabalho. Em caso de conflito, prevalecem
`PATHS.toml`, `QUALITY_ROADMAP.md`, `GOVERNANCA.md`, `DEMANDAS.md` e as
decisões aceitas.

## Garantia Alcançável

Nenhum documento garante ausência absoluta de defeitos em código futuro. A
garantia exigível é que:

- o pacote começa somente quando suas dependências técnicas explícitas estão fechadas;
- o desenho explicita domínio, dados, estados, permissões e falhas antes do código;
- backend, frontend, banco e integrações respeitam fronteiras existentes;
- gates automatizados e evidência manual proporcional ao risco bloqueiam o fechamento;
- regressões do que já existe são exercitadas antes de commit e publicação;
- falha de gate, evidência ausente ou risco crítico aberto impede declarar 100%.

## Fonte De Ownership

`PACKAGE_ARCHITECTURE.csv` define para cada pacote:

- fronteira backend primária;
- fronteiras colaboradoras permitidas;
- área frontend;
- perfil de risco.
- dependências técnicas explícitas.

Ownership não autoriza importação interna entre módulos. Colaboração ocorre por
contrato público, port, evento versionado ou application service do owner.
Alterar a matriz exige decisão arquitetural, atualização deste padrão e gate
completo. Não criar um módulo por pacote por conveniência.

## Definition Of Ready

Antes do primeiro lote, a janela deve registrar no próprio pacote ou nos
documentos oficiais:

1. problema, pessoas afetadas, resultado esperado e hipótese mensurável;
2. baseline atual auditado no código, sem confiar apenas no backlog;
3. owner primário, colaboradores e contratos existentes que serão reutilizados;
4. atores, papéis e matriz de autorização deny-by-default;
5. entidades, value objects, invariantes e estados do domínio;
6. comandos, consultas, eventos e efeitos externos;
7. classificação dos dados, retenção, exportação e exclusão;
8. ameaça, abuso, dano humano/físico e limites de automação;
9. contratos API/evento N/N-1 e consumidores conhecidos;
10. telas, rotas, estados, responsividade e acessibilidade;
11. orçamento de capacidade, latência, payload, arquivo e concorrência;
12. plano de testes, rollout, observabilidade e rollback;
13. lotes e critérios de aceite do pacote ativo, sem importar escopo cancelado;
14. confirmação de que nenhuma tabela, serviço ou pacote não ativo é necessário.

Se um item não se aplicar, registrar `não aplicável` com justificativa. Campo
vazio, placeholder ou “definir depois” bloqueia implementação.

## Modelagem De Domínio

- Uma entidade possui owner único e identidade estável.
- Invariantes ficam em domínio/application, nunca em route, componente ou SQL solto.
- Estado é enum/contrato explícito; transição inválida falha sem efeito parcial.
- Datas usam UTC na persistência e timezone explícito na apresentação.
- Dinheiro usa unidade mínima inteira e ledger canônico; float é proibido.
- Unidades físicas são explícitas e convertidas na borda.
- Conteúdo, projeto, arquivo, job, impressão, pagamento e evento referenciam
  versões imutáveis quando reprodutibilidade for necessária.
- Exclusão lógica, arquivamento, moderação, revogação e retenção são estados
  diferentes; não reutilizar um booleano genérico.
- Relação social nunca concede permissão operacional sobre impressora.
- Identificador público não revela sequência interna, tenant ou dado sensível.
- Regra transversal compartilhada vira contrato reutilizável, não cópia entre módulos.

Antes de codificar, documentar ao menos uma tabela de invariantes e uma máquina
de estados para toda entidade mutável não trivial.

## Backend

### Fronteiras

- Route/endpoint trata transporte, autenticação, parsing e tradução de erro.
- Application service coordena caso de uso, transação e ports.
- Domínio contém regra pura e não importa FastAPI, driver, banco, Redis, storage ou UI.
- Repository/adapter implementa persistência ou integração sem regra de apresentação.
- Contratos públicos ficam tipados e não expõem entidade/tabela interna.
- Módulo só consome outro owner por contract/application/port/evento permitido.
- Arquivo crítico existente não deve crescer; ao tocá-lo, extrair responsabilidade
  coesa preservando contrato e testes.

### API E Eventos

- Rotas seguem nomenclatura e prefixos atuais do owner.
- Mutação define autorização, idempotência, conflito e resposta após retry.
- Listagem define paginação limitada, filtros permitidos e ordenação determinística.
- Erro público usa código estável, mensagem segura e correlation/request ID.
- API/evento mantém N/N-1 ou cria versão explícita com migração de consumidores.
- Evento possui ID, versão, tipo, actor, tenant, timestamp e payload mínimo.
- Webhook autentica origem, registra receipt idempotente e suporta replay seguro.
- Operação longa vira job durável com lease, timeout, retry, backoff e dead-letter.
- Redis nunca é fonte canônica; cache pode ser perdido e reconstruído.
- Comando físico exige preflight, confirmação, step-up e trilha operacional.

### Segurança

- Autorização é validada no backend em leitura, escrita, busca, objeto e evento.
- Testar owner/tenant diferente, recurso inexistente e ator sem papel.
- Proteger contra mass assignment, enumeração, replay, SSRF, traversal, parser bomb,
  archive bomb, MIME enganoso e payload excessivo quando aplicável.
- Logs, traces, métricas, eventos e bundles não carregam segredo ou payload sensível.
- Rate limit e quotas diferenciam leitura, mutação, upload, busca e ação crítica.

## Banco E Persistência

- Migrations são proibidas; usar `.sql` idempotente em `backend/sql/`.
- Cloud usa PostgreSQL; SQLite existe somente no adapter do perfil local.
- Script declara ordem, precondição, lock esperado, impacto, validação e rollback.
- Expandir schema antes de consumir; remover referência antiga somente após N/N-1.
- `CREATE ... IF NOT EXISTS`, catálogo do PostgreSQL e upsert seguro devem tornar
  reexecução previsível sem esconder divergência incompatível.
- `DROP`, `DELETE`, prune e destruição de objeto exigem confirmação explícita e
  nunca fazem parte de rollback automático.
- Índices consideram seletividade, plano e impacto de criação no servidor atual.
- Constraints sustentam invariantes críticas; aplicação traduz violações.
- Escrita que cruza processo usa outbox/inbox e chave idempotente.
- Auditoria/log persistido reutiliza estrutura existente e define retenção/cleanup.
- Rollback de código não restaura snapshot antigo sobre escritas confirmadas.

Testes devem provar primeira execução, reexecução, execução concorrente, falha
intermediária e retomada.

## Frontend

### Estrutura

- Page/view compõe a rota e estados, sem persistência ou regra de negócio.
- Hook/view model coordena carregamento, cache de tela e ações.
- Form component recebe dados/callbacks; não possui rota, fetch ou persistência.
- API client tipado centraliza transporte e tradução de contrato.
- Regras críticas e permissões não existem somente no frontend.
- Lista/filtro, detalhe, criação e edição são telas/estados distintos.
- Estado compartilhado é mínimo; dado servidor continua canônico.

### Experiência Obrigatória

- Loading, empty, error, success, partial, offline, forbidden e conflict.
- Retry seguro não duplica mutação; formulário preserva entrada após falha.
- Desktop, tablet e mobile a partir de 320 px, sem depender de hover.
- Teclado, foco, leitor de tela, zoom 400%, contraste e redução de movimento.
- Uma ação principal inequívoca; ação perigosa possui confirmação contextual.
- Paginação/virtualização evita carregar coleções ilimitadas.
- Data crítica mostra origem, atualização e estado stale/offline.
- Erro não enumera recurso privado e oferece recuperação acionável.
- Alteração visual atualiza `TELAS.md` e possui regressão proporcional.

## Integrações, Jobs E IA

- Adapter externo possui timeout, circuit breaker, retry somente quando seguro e
  observabilidade sanitizada.
- Quota e backpressure protegem servidor, provedor e usuário.
- Import preserva original sanitizado, provenance, licença e checksum.
- IA registra modelo/versão, fontes, confiança, avaliação, opt-out e revisão humana.
- Automação nunca publica, cobra, modera definitivamente ou comanda impressora
  apenas por score sem política e autorização explícitas.
- Falha externa degrada a capacidade afetada sem derrubar funções não relacionadas.

## Testes Por Perfil De Risco

Todos os pacotes:

- unitários de invariantes e estados;
- service/use case com sucesso, validação, permissão e falha de dependência;
- repository/adapter para query, serialização e idempotência;
- contrato/API para payload, erros, paginação e N/N-1;
- componente para estados e ação principal;
- regressão dos fluxos existentes tocados;
- `./check.sh`.

Perfil `high` adiciona integração realista, concorrência/retry, acessibilidade
manual e smoke da jornada principal.

Perfil `critical` adiciona threat model, matriz de abuso, isolamento multi-tenant,
E2E principal/erro, testes de carga/capacidade proporcionais, rollback ensaiado,
piloto/canário, observação e revisão humana/independente quando exigida pela
governança. A dispensa de teste externo registra risco residual; não vira “aprovado”.

## Compatibilidade E Proteção Do Legado

- Capturar testes de caracterização antes de alterar comportamento consolidado.
- Não renomear/remover rota, campo, evento ou estado sem inventário de consumidores.
- Preferir mudança aditiva e leitura compatível durante rollout.
- Dados antigos continuam legíveis; backfill é idempotente e reconciliável.
- Feature flag temporária possui owner, expiração e remoção no mesmo pacote.
- Não manter dual-write, adapter ou caminho legado após fechamento.
- Comparar contagens, checksums e consultas semânticas em mudança de dados.
- UI anterior permanece recuperável até o novo fluxo passar smoke e rollback.

## Entregas Obrigatórias Por Lote

Cada lote fecha com:

- código e documentação do recorte;
- testes focados proporcionais;
- atualização do lote e de sua evidência em `DEMANDAS.md`;
- evidência de contrato, permissão, erro e idempotência aplicáveis;
- diff sem mudança de pacote cancelado, fundido ou adiado;
- nenhuma pendência escondida para “lote posterior” fora do pacote.

## Definition Of Done Do Pacote

O pacote só pode ser marcado 100% quando:

1. todos os itens da Definition of Ready possuem resposta final;
2. todos os lotes declarados em `DEMANDAS.md` têm evidência;
3. arquitetura e ownership passam nos gates;
4. SQL/contratos são idempotentes e N/N-1;
5. testes do perfil de risco e regressões passam;
6. `TELAS.md`, `TESTES.md`, `BUGS.md`, `DECISOES.md` e `RUNBOOK.md` estão coerentes;
7. segurança, privacidade, acessibilidade e dano foram revisados;
8. métricas, logs, alertas, retenção e cleanup estão operacionais;
9. rollout, smoke, observação e rollback têm evidência;
10. nenhum resíduo temporário, referência futura ou dívida oculta permanece;
11. diff completo foi revisado e `./check.sh` passou;
12. commit exclusivo do pacote foi criado.

Check, lint, cobertura ou publicação isoladamente não provam o pacote. Evidência
de produção só é exigida quando a superfície de aceite for produção e houver
autorização para publicar.

## Handoff Para Outra Janela

Enviar à nova janela:

1. “implemente somente `PKG-NNN`”;
2. branch e commit base;
3. confirmação de dependências concluídas;
4. referência a este padrão e à linha do pacote na matriz;
5. proibição de implementar pacote não ativo;
6. obrigação de atualizar `DEMANDAS.md` por lote;
7. obrigação de parar se surgir mudança destrutiva, credencial, produção ou
   decisão que expanda o escopo;
8. comando de check e critério de commit.

A janela deve começar relendo `PATHS.toml`; não deve assumir que uma conversa
anterior substitui o estado atual do repositório.
