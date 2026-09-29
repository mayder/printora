# PKG-101 — Layout, Design System E Coerência Visual

## Definition Of Ready

### Problema, Pessoas E Resultado

O frontend consolidado possui tokens básicos de cor, mas espaçamentos, raios,
tipografia, estados, densidade e componentes responsivos ainda são definidos de
forma dispersa. Isso aumenta inconsistência entre operação, comunidade e
administração e dificulta validar a interface em celular, teclado, zoom e modo
offline.

Pessoas afetadas: operadores de oficina, makers, leitores da comunidade e
administradores. O resultado esperado é reduzir decisões visuais locais e
oferecer uma referência executável para os oito lotes do pacote. A hipótese
mensurável é que todas as oito famílias possam ser localizadas, inspecionadas e
experimentadas sem ação operacional, com navegação funcional a partir de
320 px e sem perda de rascunho após recarregar a página.

### Baseline Auditado

- `frontend/src/styles.css` possui somente tokens de cor e aplica medidas
  literais em componentes globais;
- estados vazios e de falha possuem implementações diferentes por tela;
- não existe catálogo documentado, laboratório visual ou densidade ajustável;
- `prefers-reduced-motion` não possui política global;
- navegação principal usa `section` em query string e não expõe as rotas
  `SCR-0137` a `SCR-0144`;
- não existe contrato backend do domínio `design_system`;
- nenhum schema ou dado canônico existente precisa ser alterado.

Baseline de benefício: zero das oito famílias disponíveis no produto. Baseline
de dano: não há medição central de falha visual; regressões são detectadas por
testes locais e relatos.

### Ownership E Contratos

- owner primário: `design_system`;
- colaboradores: `shared`, `administration` e `platform`;
- área frontend: `administration`;
- risco: `high`;
- contrato novo: `GET /api/design-system/v1/capabilities`, autenticado, somente
  leitura, versionado e compatível N/N-1;
- consumidores: tela administrativa e testes de contrato;
- contratos existentes reutilizados: autenticação, transporte HTTP, shell,
  tema local, toasts e navegação.

O domínio é compartilhado e durável, não um módulo nomeado pelo número do
pacote. Nenhum detalhe interno de operação ou comunidade será importado.

### Atores E Autorização

| Ator | Consultar catálogo | Experimentar localmente | Publicar token global |
|---|---:|---:|---:|
| visitante | não | não | não |
| usuário autenticado | sim | sim | não |
| administrador de plataforma | sim | sim | não neste pacote |

O backend é deny-by-default por sessão autenticada. O laboratório não concede
permissão operacional, não publica conteúdo e não altera configuração global.

### Entidades, Invariantes E Estados

`DesignCapability` é um contrato imutável versionado em código com slug,
capacidade, IDs `COM`, família `SCR`, objetivo, tokens e evidências. `LabDraft`
é um value object local, sem dado pessoal, com densidade, modo, valores de
formulário e versão de schema.

| Invariante | Garantia |
|---|---|
| catálogo | contém exatamente `CAP-18-01` a `CAP-18-08`, sem slug ou ID duplicado |
| rastreabilidade | cada capacidade contém sete IDs `COM` contíguos e um `SCR` exclusivo |
| mutação | nenhum endpoint mutável ou efeito externo existe |
| rascunho | gravação substitui a mesma chave local; repetição não duplica estado |
| segurança | catálogo e rascunho não contêm segredo, PII ou permissão operacional |
| compatibilidade | versão `v1` mantém campos e slugs; evolução aditiva preserva N/N-1 |

Máquina de estados do laboratório:

```text
loading -> ready
loading -> error -> loading
ready -> editing -> saved
editing -> conflict -> editing
ready|editing|saved -> offline -> ready
```

`empty` e `partial` são projeções de `ready`; não existe transição destrutiva.

### Comandos, Consultas E Efeitos

- consulta: listar capacidades estáticas com versão e permissões;
- comandos locais: selecionar família, alterar densidade, editar rascunho,
  revisar e restaurar os valores documentados;
- efeitos externos: nenhum;
- eventos persistidos, jobs, filas, webhooks, uploads e comandos físicos: não
  aplicável, pois a capacidade é visual e somente leitura no servidor.

### Dados, Retenção E Banco

O catálogo é código versionado e o rascunho fica no `localStorage` do navegador
sob chave versionada. Não há PII, telemetria individual ou dado canônico.
Restauração do padrão substitui apenas o rascunho local após confirmação da
pessoa.

Não há mudança de banco no PKG-101. Portanto nenhum SQL é necessário. Caso uma
evolução futura introduza persistência canônica, ela deverá usar scripts
idempotentes em `backend/sql/` e PostgreSQL, sem migration, `DROP` ou `DELETE`.

### Ameaça, Abuso E Limites

| Ameaça/abuso | Controle |
|---|---|
| enumeração sem autenticação | endpoint exige sessão válida |
| payload malicioso no rascunho local | parse defensivo, enums e limites de tamanho |
| XSS em amostras | conteúdo fixo ou texto renderizado pelo React, sem HTML arbitrário |
| abuso de leitura | rate limit global existente e payload pequeno/cacheável |
| aparência confundida com permissão | permissões explícitas e nenhuma ação operacional |
| movimento causando desconforto | redução de movimento do SO e controle local |
| rascunho antigo incompatível | `schema_version`, fallback seguro e restauração |

O laboratório nunca aciona impressora, publica conteúdo, cobra, modera ou
persiste configuração de servidor.

### Telas E Rotas

As rotas base `SCR-0137` a `SCR-0144` abrem lista/filtro. Sufixos `/detail` e
`/edit` representam detalhe e cadastro/edição separados. A entrada global fica
em Administração > Design system. Estados obrigatórios: loading, empty, error,
success, partial, offline, forbidden e conflict.

Validação visual: 320, 375, 768, 1024 e 1440 px; retrato e paisagem; teclado,
foco visível, leitor de tela, zoom 400%, contraste claro/escuro e redução de
movimento.

### Orçamentos

- catálogo: oito itens, sem paginação remota;
- resposta API: máximo de 64 KiB;
- rascunho local: máximo de 32 KiB;
- primeira interação: sem dependência de upload, fila ou impressora;
- concorrência: abas usam revisão local e detectam conflito antes de sobrescrever;
- animações: até 160 ms e removidas quando `prefers-reduced-motion: reduce`.

### Testes, Observabilidade, Rollout E Rollback

- domínio: invariantes e serialização do catálogo;
- API: autenticação, contrato v1, tamanho, erro seguro e ausência de mutação;
- frontend: catálogo, busca/filtro, lista/detalhe/editor, estados, rascunho
  idempotente, conflito, offline, densidade e movimento reduzido;
- regressão visual: screenshots desktop/mobile dos componentes e temas;
- acessibilidade manual: teclado, foco, landmarks e zoom;
- regressão: shell, tema e rotas existentes;
- gates: testes focados por lote, validador de dependências e `./check.sh`.

Métrica local agregável sem identidade: famílias exercitadas e resultado do
check visual (`pass`, `warning`, `fail`). Métrica de benefício: oito famílias
verificáveis e redução de divergências do laboratório. Alertas de dano:
overflow, corte de foco, contraste ou movimento incompatível. Não será criada
telemetria persistida neste pacote.

Rollout: entrada aditiva na Administração, sem flag e sem alterar tela
operacional. Smoke lê o catálogo e percorre lista, detalhe e editor. Rollback:
reverter a release; não há banco, dado canônico, dual-write ou cleanup.
Publicação e piloto dependem de autorização separada.

### Rastreabilidade E Independência

- `CAP-18-01` a `CAP-18-08`;
- `COM-0953` a `COM-1008`;
- `SCR-0137` a `SCR-0144`;
- base consolidada `PKG-01` a `PKG-100`;
- nenhum contrato, tabela, rota ou serviço de `PKG-102` ou posterior é
  necessário.

## Plano De Evidência Por Lote

1. tokens semânticos e documentação executável;
2. hierarquia compartilhada entre amostras social e operação;
3. cards, tabela e galeria responsivos;
4. densidades oficina, leitura e administração;
5. rascunho longo com salvamento, conflito e revisão;
6. estados coerentes e recuperáveis;
7. feedback, foco e redução de movimento;
8. laboratório e regressão desktop/mobile;
9. integração, smoke e revisão de benefício/dano;
10. revisão dos 56 `COM`, oito `SCR`, documentação, gate completo e commit.

As evidências finais e a matriz de aceite estão em
`docs/community/PKG_101_EVIDENCE.md`.
