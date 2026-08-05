# TESTES.md

## Objetivo

Definir validações mínimas para o Printora.

## Pirâmide de testes

### Unitário

- Testa regra pura, parser, policy, sanitizacao, mapper e calculo.
- Deve ser rapido e deterministico.
- Nao acessa rede, banco real, filesystem real ou UI real.

### Service/use case

- Testa fluxo de negocio com fakes, mocks ou fixtures controladas.
- Cobre caso feliz, validacao, erro de dependencia e permissao quando aplicavel.

### Repository/adapter

- Testa transformacao, query, serializacao e contrato com dependencia externa usando fixture ou banco local controlado.

### Contrato/API

- Testa payload publico, status, erro, paginacao, filtros e compatibilidade com frontend.

### Componente/UI

- Testa estados principais quando houver estrutura de teste disponivel.
- Cobre loading, empty, error, success e interacao principal.

### E2E

- Reservado para fluxo critico, regressao de alto risco ou fechamento de pacote.
- O gate do `PKG-97` usa Playwright/Chromium com dados sintéticos isolados:

```bash
scripts/run-e2e-gate.sh
PRINTORA_E2E_REPEAT_EACH=10 scripts/run-e2e-gate.sh
```

- A matriz obrigatória cobre desktop/tema escuro, mobile/tema claro, teclado,
  acessibilidade, isolamento entre organizações, permissões e recuperação de
  offline, timeout, `429` e `5xx`.
- Fluxos P0 não usam retry nem quarentena; repetição deve usar identidade única
  por projeto e índice para revelar colisão ou vazamento entre execuções.
- O E2E provisiona `pentest-admin@example.test` por canal local antes de iniciar
  o backend. Cadastro público dessa identidade deve retornar `403`, login deve
  funcionar e o contrato autenticado deve expor somente
  `platform_admin=true`, nunca senha ou sessão.

## Cobertura mínima por criticidade

- P0/critico: teste automatizado ou evidencia objetiva obrigatoria, `./check.sh` e regressao do fluxo.
- P1/alto: teste automatizado quando viavel e reteste focado.
- P2/medio: reteste direcionado e teste local proporcional.
- P3/baixo: validacao local da alteracao.

Metas percentuais podem ser ativadas em `PATHS.toml` por projeto, mas o minimo universal e evidencia proporcional ao risco.

## Dados de teste e fixtures

- Fixtures ficam em `backend/tests/fixtures` e `frontend/tests/fixtures`.
- Nao usar dump de producao.
- IDs e datas devem ser deterministicas quando possivel.
- Fixture grande demais precisa justificativa.
- Fixture nao pode conter senha, token, chave, URL privada sensivel ou payload real sem sanitizacao.

## Check Local

Comando obrigatório antes de commit:

```bash
./check.sh
```

## Onboarding Operacional

- regra pura valida progresso local corrompido, ordem das etapas e ausência de
  falso sucesso quando Moonraker, projetos ou slicing não respondem;
- componente cobre instalação vazia, linguagem sem identificadores internos e
  retomada do passo preservada em falha de rede;
- E2E isolado cobre desktop e mobile, teclado, análise Axe sem violações sérias
  ou críticas, ausência de overflow e recuperação após timeout;
- pareamento de identidade repetida, token de uso único e segredo sanitizado
  continuam cobertos pelos testes de agente existentes;
- validação focada: `scripts/run-e2e-gate.sh onboarding.spec.ts`.

## Portfólio Ativo Pós-PKG-100

Cada pacote ativo segue o perfil de risco e as dependências técnicas definidos
em `docs/community/PACKAGE_ARCHITECTURE.csv`, o estado registrado em
`docs/community/PACKAGE_PORTFOLIO.csv` e os testes de
`docs/community/PACKAGE_EXECUTION_STANDARD.md`.

Validação estrutural obrigatória:

```bash
python3 scripts/generate_community_roadmap.py
git diff --exit-code -- docs/community/COMMUNITY_BACKLOG.csv docs/community/COMMUNITY_BACKLOG.md docs/community/COMMUNITY_SCREENS.csv docs/community/COMMUNITY_SCREENS.md docs/community/PRIORITIES.md docs/community/SUMMARY.json
python3 scripts/validate-demand-package-dependencies.py
```

Além do gate estrutural, todo pacote cobre:

- invariantes e transições de estado;
- autorização e isolamento em leitura e mutação;
- idempotência, retry, concorrência e retomada quando houver efeito;
- contrato API/evento e compatibilidade N/N-1;
- repository/adapter e falha da dependência;
- estados frontend, mobile e acessibilidade;
- regressão dos fluxos consolidados tocados;
- rollout, smoke e rollback proporcionais ao risco.

Gerador e validador aprovados não significam funcionalidade implementada. O
inventário gerado é apenas histórico de ideias. O fechamento exige evidência
real das superfícies alteradas e não exige implementar todos os IDs
`COM/CAP/SCR`.

## Objetos e busca Cloud

No fechamento do contrato de objetos e busca, executar o gate completo e, no
host Cloud, comprovar: upload no limite de 25 MiB, quarentena/promoção, restart e
reconciliação sem ausência/corrupção/órfão, busca com GIN e filtro de geração,
backup externo e restore físico isolado com checksums de banco, WAL e objetos.
O restore deve reconstruir a busca sem iniciar a aplicação restaurada nem escrever
no cluster de produção.

## Impressão, marketplace e fontes externas

Validação focada:

```bash
cd backend && uv run --extra dev pytest tests/test_print_history.py tests/test_social_catalog.py tests/test_external_library.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Aceite:

- histórico de impressão não expõe impressora privada em resposta pública;
- feedback público/privado persiste resultado, nota e foto HTTPS opcional;
- sinais de ranking são atualizados por sucesso/falha sem payload sensível;
- premium/patrocinado público exige revisão aprovada;
- conteúdo patrocinado exibe transparência e não aparece como recomendação técnica neutra;
- bookmark externo não copia arquivo e diferencia referência externa de item hospedado;
- importação externa exige atribuição quando a fonte assim definir;
- checksum opcional detecta duplicidade com arquivo local;
- falha de fonte externa não quebra biblioteca local.

## PKG-77 a PKG-81 - Projetos de impressão

Validação obrigatória para fechamento de cada pacote proporcional ao lote, e completa no fechamento do PKG-81:

```bash
cd backend && uv run --extra dev pytest tests/test_print_projects.py tests/test_print_project_privacy.py tests/test_slicing_pipeline.py tests/test_print_delivery.py tests/test_print_history.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Aceite de domínio:

- projeto de impressão é a entidade raiz; arquivos, versões/snapshots, compartilhamentos, publicação, jobs, G-code e histórico são relações ou derivados;
- projeto pode conter múltiplos arquivos, com arquivo principal/preview, arquivos imprimíveis, peças opcionais, documentação, links externos e artefatos;
- compartilhamento com comunidade é N:N; remover compartilhamento não apaga projeto, não arquiva, não muda ownership, não muda visibilidade e não remove arquivos;
- visibilidade, revisão/publicação, classificação comercial e compartilhamento em comunidade são dimensões separadas;
- classificação comercial usa `gratuito`, `curado`, `premium` ou `patrocinado`; comunidade não é classificação comercial;
- `Salvar nos meus projetos` não duplica arquivo indevidamente: deve registrar referência/salvo, fork/remix explícito ou cópia somente quando o usuário confirmar e a licença permitir;
- bookmark/link externo sem arquivo hospedado/importado/validado não pode ser fatiado, salvo como G-code ou enviado para impressora;
- falha parcial de arquivo não bloqueia o projeto inteiro quando houver arquivos válidos, mas bloqueia publicação/fatiamento/envio da peça inválida e mostra estado acionável;
- job de fatiamento aponta para snapshot imutável do projeto, arquivos selecionados, orientação/dimensões relevantes, perfil, usuário e impressora;
- alteração posterior do projeto não altera job, preflight, G-code ou histórico já criados;
- histórico público é agregado/sanitizado por projeto/material/perfil/tipo técnico e nunca expõe impressora privada, agente, Moonraker, token, IP, path ou organização;
- `Social > Comunidades > Projetos` lista compartilhamentos e aponta para o projeto central; não cria/upload/fatia/envia arquivo como fluxo principal;
- Administração mostra configuração/diagnóstico/fallback do fatiamento; criação diária de job, preflight, salvar G-code e envio ficam no fluxo do projeto;
- bundle nativo de fatiamento preserva campos OrcaSlicer conhecidos e desconhecidos permitidos no round-trip, rejeita dados operacionais sensíveis, isola owners e não duplica importação idempotente;
- nova versão produz diff compreensível sem alterar a revisão, versão da engine, checksum ou snapshot canônico já fixados em um job;
- a interface de perfis descreve impressora, qualidade e material em linguagem humana, suporta teclado e não exige conhecimento do schema JSON;
- rotas e entradas legadas (`models`, biblioteca social, comunidade/arquivos, pipeline administrativo) redirecionam, ficam somente leitura ou são rebaixadas sem quebrar dados existentes.

Validação inicial do contrato central:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_print_projects.py ../backend/tests/test_print_project_postgresql_identity.py -q
npm --prefix frontend run build
```

Critérios do lote inicial:

- `/api/print-projects/contract` retorna `Projeto de impressão` como entidade raiz;
- `/api/print-projects` lista apenas projetos públicos ativos;
- referência externa sem arquivo validado aparece como não fatiável;
- projeto multi-arquivo com uma peça válida e outra inválida mantém o projeto acessível e bloqueia só o arquivo inválido para fatiamento;
- a tela `Projetos de impressão` aparece no menu principal sem expor identificadores internos de pacote/lote.
- no PostgreSQL, criar projeto gera o identificador do projeto e do snapshot
  inicial sem exigir `id` no payload; arquivos, compartilhamentos, salvamentos e
  revisões usam identidades próprias pelo mesmo contrato.

Validação de fechamento da área central:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_print_projects.py -q
npm --prefix frontend run build
./check.sh
```

Critérios adicionais:

- detalhe central retorna arquivos, versões/snapshots e estado de salvamento;
- `Meus projetos` preserva a lista pessoal quando somente o resumo de
  armazenamento falhar, apresentando a indisponibilidade da cota no próprio
  painel e sem expor `Internal Server Error`;
- o resumo de armazenamento funciona tanto com linhas SQLite quanto com linhas
  nomeadas do PostgreSQL;
- `Salvar nos meus projetos` cria referência sem duplicar arquivo;
- compartilhamento com comunidade é N:N e não altera owner, visibilidade nem classificação comercial;
- comunidade lista projetos centrais compartilhados e não apresenta upload/fatiamento/envio como fluxo principal;
- Administração lista jobs existentes como diagnóstico/fallback e não cria job diário nem inicia envio operacional como caminho principal.

### PKG-128 - Arquivos, manifesto e inspeção 3D

Validação focada:

```bash
backend/.venv/bin/python -m pytest -q backend/tests/test_project_assets.py backend/tests/test_print_projects.py backend/tests/test_schema_versioning.py
PATH=/Users/brenomayder/.nvm/versions/node/v22.22.0/bin:$PATH npm --prefix frontend run build
PATH=/Users/brenomayder/.nvm/versions/node/v22.22.0/bin:$PATH npm --prefix frontend run test:unit -- tests/unit/ProjectAssetsPanel.test.ts
```

Aceite adicional:

- upload repetido por chave ou assinatura do arquivo não duplica objeto nem snapshot;
- cota soma biblioteca e projetos ativos antes de gravar o upload;
- parser STL/3MF respeita limites de tamanho, triângulos, entradas e conteúdo descompactado;
- medidas, escala simulada, seção, overhang, ilhas e falhas possuem alternativa textual;
- arquivo rejeitado, externo ou em quarentena não entra no bundle;
- bundle contém `manifest.json`, `SHA256SUMS.txt` e somente arquivos validados;
- outro usuário não altera peça, montagem ou variação;
- versão anterior mantém manifesto e checksum depois de nova organização;
- desktop e mobile preservam leitura, foco, zoom e uso sem preview aberto;
- fechamento executa contrato OpenAPI, inventário modular e `./check.sh` completo.

## Social, Catálogo E Comunidades

Validação focada:

```bash
cd backend && uv run pytest tests/test_social_catalog.py -q
cd frontend && npm run test:releases
cd frontend && npm run build
```

Aceite:

- Seed amplo do catálogo cobre fabricantes/modelos DIY relevantes, mantendo itens incertos como `community` ou `draft`.
- Contrato administrativo retorna fabricante/modelo agrupado, links enriquecidos, logo confiável ou monograma, Discord, Reddit, documentação, BOM, ficha técnica/fonte de curadoria e notas quando disponíveis.
- UI do Catálogo valida listagem paginada, filtros pesquisáveis em cascata, detalhe dedicado e retorno preservando filtros/página.
- Usuário comum autenticado navega no catálogo detalhado em modo leitura, mas não cria/edita/curadoria catálogo canônico; estados `official`, `community`, `draft`, `obsolete` e `blocked` preservam vínculos existentes e bloqueiam nova publicação quando aplicável.

- catálogo seedado contém fabricantes, modelos e variações técnicas canônicas além de Voron, com RatRig, VzBot, Annex, HevORT, Printers For Ants, ZeroG, RailCore, SecKit, BLV, HyperCube, D-Bot, V-King, CroXY, Rook, Positron, The 100, Doron, SnakeOilXY, MaybeCube, Rolohaun/Bastion, T250, SM-100, BabyCube e OLSK;
- itens com dado técnico menos seguro ficam em `community` ou `draft`, sem inventar precisão frágil;
- endpoint administrativo filtra por fabricante, modelo, variação/tamanho, componente, cinemática, firmware e `trust_state`;
- contrato administrativo retorna modelos agrupados com variações dentro do detalhe, sem depender de uma lista plana de variantes;
- fontes técnicas internas não expõem identificadores de pacote no seed/API;
- duplicidade de slug/modelo/variante é bloqueada por contrato de banco/API;
- estados `official`, `community`, `draft`, `obsolete` e `blocked` são administráveis;
- variante `obsolete` ou `blocked` não quebra impressora já vinculada, mas não é aceita em nova publicação pública;
- usuário comum consegue ler o catálogo detalhado e recebe 403 ao tentar curar catálogo canônico;
- perfil social não expõe email, WhatsApp, organizações, permissões ou credenciais operacionais;
- impressora pública exige vínculo com variante do catálogo e não retorna Moonraker, SSH, agente, token ou IP;
- comunidades automáticas são derivadas de impressoras públicas e não concedem permissão operacional;
- bloqueio social encerra follows/amizades e impede nova interação social sem apagar histórico operacional.

### PKG-50 - Perfil social do usuário

Validação automatizada obrigatória para fechamento:

```bash
cd backend && uv run --extra dev pytest tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- slug duplicado é rejeitado com mensagem clara;
- slug antigo reservado por outro usuário é rejeitado;
- perfil `private` não abre publicamente;
- perfil `unlisted` abre por URL direta;
- bloqueio social impede visualização autenticada do perfil e das impressoras públicas;
- `avatar_url` e links sociais rejeitam HTTP, localhost, IP privado e host de rede social fora do permitido;
- contrato público não expõe email, WhatsApp, organizações, permissões, agente, Moonraker, SSH, token ou host operacional;
- `Conta > Perfil > Público` contém edição social, URL pública, estado de privacidade, prévia pública e impressoras públicas em contexto;
- `/u/{slug}` mostra perfil público e impressoras públicas sem dados operacionais.

Evidência visual local esperada:

- `/tmp/printora-pkg50-account-public.png`: usuário autenticado abriu menu do topo > `Perfil` e acessou a aba `Público`;
- `/tmp/printora-pkg50-public-profile.png`: página pública `/u/{slug}` validada sem ocorrências visíveis de dados sensíveis.

Fechamento do pacote:

```bash
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

### PKG-51 - Impressoras públicas do usuário

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- usuário tentando publicar impressora de outro usuário recebe bloqueio;
- publicação exige variante canônica válida;
- variante `blocked` ou `obsolete` não permite nova publicação;
- despublicar remove/desativa comunidades derivadas;
- impressora privada não aparece em perfil público, comunidade, busca pública nem página direta `/p/{printer_id}`;
- imagens públicas inválidas, HTTP, localhost ou IP privado são rejeitadas;
- contrato público de impressora não expõe Moonraker, IP, SSH, agente, token, credencial, organização ou permissão;
- perfil `private` não lista impressoras e remove vínculo público de comunidade;
- fluxo principal de publicação/despublicação mantém busca e comunidades consistentes.
- `/?section=social` lista impressoras públicas reais com filtros canônicos e não contém ação principal de publicar/despublicar.

Evidência visual esperada:

- detalhe da impressora com área `Publicação da impressora`;
- aba `Resumo` do detalhe da impressora sem formulários de publicação, configuração técnica ou material abertos por padrão; os formulários devem aparecer somente após `Editar publicação`, `Criar configuração`, `Criar perfil` ou `Editar`;
- resumo da impressora, Operação e Manutenção em mobile claro/escuro sem texto vertical, sobreposição, scroll horizontal ou grids de desktop comprimidos;
- prévia pública antes de publicar;
- página pública real `/p/{printer_id}`;
- páginas públicas standalone `/p/{printer_id}` e `/u/{slug}` respeitando o tema claro/escuro persistido;
- página direta de impressora privada retornando indisponível;
- payload público inspecionado sem dados sensíveis.

### PKG-52 - Comunidades automáticas

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- publicar impressora associa usuário às comunidades de fabricante, modelo e variante;
- despublicar remove/desativa vínculos de comunidade;
- trocar variante remove vínculo da variante antiga e cria vínculo da nova;
- impressora privada e perfil `private` não entram em comunidade, busca, perfil público nem página direta;
- contagens de membros, impressoras e mods não incluem impressoras privadas;
- comunidade não concede permissão operacional e payload não retorna Moonraker, IP, SSH, agente, token, credencial, organização ou permissão;
- estados `active`, `uncurated`, `obsolete` e `merged` são tratados; `obsolete` e `merged` não recebem novos vínculos;
- filtros por fabricante, modelo, variante e componente usam catálogo canônico;
- contrato autenticado `/api/social/communities/{slug}` retorna comunidade, membros, impressoras públicas, filtros canônicos e contagens;
- feed/arquivos/mods iniciais aparecem como estados operacionais seguros, sem tela quebrada.

Evidência visual esperada:

- `/?section=social` na aba `Comunidades` com lista de comunidades, filtros, escopo, status, contagens e ação de abrir;
- `/c/{slug}` com cabeçalho, contexto técnico, abas, contagens e impressoras públicas;
- aba `Mods` com mods públicos quando existirem e placeholder quando vazia;
- comunidade obsoleta/mesclada sem membros/impressoras ativas e destino de merge quando configurado;
- payload `/api/social/communities/{slug}` inspecionado sem dados sensíveis.

### PKG-53 - Grafo social, amizades e bloqueios

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- seguir e deixar de seguir são idempotentes;
- solicitar amizade, aceitar, recusar, cancelar solicitação pendente e desfazer amizade;
- usuário não cria relação consigo mesmo;
- bloquear encerra follow e amizade existentes;
- bloqueio impede follow, solicitação de amizade e visualização autenticada de perfil/impressoras públicas;
- desbloqueio não restaura follow nem amizade automaticamente;
- perfil `private` não entra em descoberta; `unlisted` só aparece por slug direto;
- diretório de makers sem termo lista somente perfis `public` e mostra contagem de impressoras públicas;
- busca/descoberta de perfis respeita bloqueio e não expõe email, WhatsApp, organização ou permissões;
- payloads de relacionamento não retornam dados operacionais ou sensíveis;
- relações entre usuários de organizações diferentes não concedem acesso a impressora, Moonraker, agente, SSH, token, organização, ownership ou permissão;
- histórico mínimo de abuso/moderação é persistido em `catalog_audit_events` sem payload sensível.

Evidência visual esperada:

- `/u/{slug}` autenticado com ações `Seguir`, `Deixar de seguir`, `Solicitar amizade`, `Aceitar`, `Recusar`, `Cancelar solicitação`, `Desfazer amizade`, `Bloquear` e `Desbloquear`;
- `/?section=social` autenticado com abas `Comunidades`, `Impressoras`, `Makers` e `Relações`;
- aba `Makers` com busca/lista de perfis públicos, bio curta e contagem de impressoras públicas, sem formulário de edição de perfil;
- aba `Relações` com resumo de seguindo, seguidores, amigos e solicitações, sem substituir as ações do perfil público;
- perfil bloqueado retorna indisponível para usuário autenticado bloqueado;
- busca de perfis não lista `private`, não mostra usuário bloqueado e mantém payload público sanitizado;

### PKG-54 - Feed técnico por comunidade

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- feed é sempre consultado por comunidade real;
- endpoint `/api/social/communities/{slug}/feed` retorna paginação, filtros técnicos e ordenação;
- tipos iniciais incluem post técnico, dúvida, mod, resultado de impressão, anúncio de arquivo e aviso de curadoria;
- item privado não aparece no feed público;
- comunidades obsoletas ou mescladas não retornam feed ativo;
- payload público não expõe Moonraker, SSH, token, credencial, organização, permissão ou host operacional;
- UI `/c/{slug}` possui aba `Feed` com filtros, ordenação, paginação e estados de carregamento, vazio e erro.

Evidência visual esperada:

- `/c/{slug}` na aba `Feed` com aviso de curadoria fixado;
- filtros de tipo, componente, material, firmware e problema visíveis;
- paginação funcional quando houver mais itens;
- payload inspecionado sem dados operacionais sensíveis.

### PKG-55 - Posts, comentários, reações e discussões técnicas

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- criação, edição e remoção lógica de post;
- comentário e resposta em árvore curta de um nível;
- reação simples em post;
- marcação de comentário como solução quando o post é dúvida;
- histórico mínimo de edição, remoção e solução;
- usuário sem permissão não edita conteúdo de outro usuário;
- moderador de comunidade consegue moderar discussão da comunidade;
- HTML/script malicioso é rejeitado;
- remoção lógica preserva encadeamento;
- payload não expõe Moonraker, SSH, token, credencial, organização, permissão ou host operacional.

Evidência visual esperada:

- `/c/{slug}` na aba `Feed` com formulário de nova discussão;
- card de feed com contagem de comentários/reações e botão `Discussão`;
- painel de discussão com editar/remover post, comentar, responder, editar/remover comentário e marcar solução;
- erro legível quando usuário sem sessão/permissão tenta ação mutável.
- tentativa de acessar impressora operacional por relação social continua bloqueada.

### PKG-64 - Busca, tags e descoberta de conteúdo

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- `/api/social/search` indexa comunidades, discussões, biblioteca, configurações técnicas, perfis de material e catálogo;
- conteúdo privado não aparece em resultados, tags ou facetas;
- filtros por tipo, tag, material, componente, licença e arquivo retornam somente conteúdo público elegível;
- resultado informa tipo, comunidade/contexto técnico, tags, popularidade e URL pública;
- `/api/social/tags` lista tags públicas normalizadas;
- UI `/?section=social`, aba `Descoberta`, possui busca, filtros, facetas, ordenação, paginação, loading, estado vazio e abertura de resultado.

Evidência visual esperada:

- aba `Descoberta` em desktop e mobile sem sobreposição;
- filtros/facetas aplicados alteram a lista;
- payload público inspecionado sem Moonraker, agente, SSH, token, IP operacional, organização, permissão ou identificadores internos de pacote/lote/backlog.

### PKG-65 - Ranking, recomendações e reputação técnica

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- `/api/social/recommendations` retorna conteúdo público com score determinístico e motivos visíveis;
- `/api/social/reputation` retorna reputação técnica derivada de sinais públicos;
- downloads, favoritos, soluções e reações contribuem para score;
- favorito/download próprio não aumenta score nem reputação;
- índice e sinais materializados são reutilizados quando a fonte pública não mudou;
- sinal negativo de denúncia/moderação é modelado para reduzir exposição quando existir;
- conteúdo privado e dados operacionais não entram em score, recomendação ou reputação.

Evidência visual esperada:

- aba `Descoberta` mostra `Recomendações técnicas` com tipo, título, motivo, score, reputação e ação de abertura;
- desktop e mobile sem sobreposição;
- payload público inspecionado sem Moonraker, agente, SSH, token, IP operacional, organização, permissão ou identificadores internos.

### PKG-66 - Moderação, denúncias e curadoria

Validação automatizada obrigatória para fechamento:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_social_catalog.py -k 'social_moderation' -q
cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- usuário autenticado cria denúncia para entidade social existente;
- usuário comum não acessa fila administrativa de moderação;
- administrador lista denúncias, aplica ação com motivo e registra histórico;
- ocultação/bloqueio/remove usa estado lógico e não apaga conteúdo;
- restauração recoloca conteúdo elegível na leitura pública;
- tags, comunidades e variações de catálogo podem ser bloqueadas ou restauradas por curadoria;
- `catalog_audit_events` guarda trilha auditável sem payload sensível.

Evidência visual esperada:

- tela `Catálogo` mostra painel de `Moderação` apenas para administrador;
- painel tem filtro de estado, lista de denúncias, detalhe, motivo obrigatório, ações com ícones e histórico recente;
- usuário comum permanece em leitura de catálogo sem ver fila administrativa;
- desktop e mobile sem sobreposição de texto ou controles.

### PKG-67 - Notificações sociais e acompanhamento de conteúdo

Validação automatizada obrigatória para fechamento:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_social_catalog.py -k 'social_notifications or notification_routes' -q
cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- usuário pode acompanhar post e receber notificação social de interação;
- preferências por tipo desligam notificação in-app e preservam digest configurável;
- bloqueio social impede emissão de notificação entre os usuários envolvidos;
- rotas autenticadas retornam central, preferências, follows e digest;
- marcar tudo como lido zera contagem de não lidas;
- follow/relação e comentário geram notificações sem expor email, Moonraker, token ou dado operacional.

Evidência visual esperada:

- tela `Social` mostra aba `Notificações` separada de alertas operacionais;
- aba possui filtro por estado, lista, digest, acompanhamentos e preferências por tipo;
- desktop e mobile sem sobreposição ou overflow horizontal.

### PKG-68 - Privacidade, segurança social e antiabuso

Validação automatizada obrigatória para fechamento:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_social_catalog.py -k 'social_safety or social_profile_discovery_visibility_blocking or moderation_queue' -q
cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q
npm --prefix frontend run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- preferência de descoberta remove perfil de listagens e busca por nome, mantendo URL direta autorizada;
- busca, perfil, impressoras públicas e relações continuam respeitando bloqueio social;
- rate limit persistente bloqueia abuso repetido e retorna `429` com `Retry-After`;
- abuso repetido gera sinal administrativo acionável sem email, IP bruto, token ou payload operacional;
- endpoint `/api/social/me/safety` permite usuário ajustar controles sociais;
- endpoint `/api/social/moderation/abuse-signals` é restrito ao administrador;
- payloads públicos e administrativos não expõem Moonraker, SSH, agente, token, organização, permissão ou credenciais.

Evidência visual esperada:

- `Conta > Perfil > Público` com bloco separado de `Segurança social`;
- controles de descoberta, seguidores, mensagens, menções e histórico de downloads sociais visíveis e responsivos;
- indicadores de limites acionados e sinais ativos sem expor dados técnicos internos;
- tela sem sobreposição em desktop e mobile.

### PKG-56 a PKG-61 - Biblioteca legada antes de Projetos de impressão

Os cenários abaixo registram a validação histórica da biblioteca social implementada antes da DEC-20260618-01. Para qualquer implementação nova ou reteste após PKG-77, a raiz do domínio deve ser `Projeto de impressão`; comunidade não cadastra/upload/fatia/envia arquivo como fluxo principal. Evidências antigas em `/c/{slug}` aba `Arquivos` devem virar compatibilidade/redirect, leitura legada ou migração para `Projetos de impressão`.

### PKG-56 - Biblioteca base de arquivos STL/3MF

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- criação de item com dono obrigatório, licença e visibilidade explícita;
- arquivos declarados como STL, 3MF ou pacote ZIP em modo `metadata_only`;
- vínculo com comunidade e variante do catálogo quando informado;
- arquivo privado não aparece em comunidade pública nem em perfil para terceiros;
- item de amigos aparece somente para amizade aceita;
- edição e arquivamento lógico restritos ao dono ou administrador;
- registro de download incrementa histórico sem expor payload sensível;
- nomes de arquivo com caminho relativo ou extensão inválida são rejeitados.

Evidência visual esperada:

- `/c/{slug}` na aba `Arquivos` com lista de biblioteca e formulário de cadastro separado;
- card de arquivo com licença, versão, metadados técnicos, arquivos declarados, downloads e ações;
- `/u/{slug}` com seção `Biblioteca` separada de `Impressoras públicas`;
- ausência de nomes internos e de dados operacionais sensíveis no payload/render.

### PKG-57 - Upload seguro, validação e quarentena de arquivos 3D

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- upload bruto sem multipart em item existente da biblioteca;
- limite de 25 MB;
- extensão permitida somente STL, 3MF ou ZIP;
- assinatura básica de STL, ZIP e 3MF;
- bloqueio de ZIP vazio, path perigoso, excesso de entradas, tamanho descompactado excessivo e razão de compressão suspeita;
- checksum SHA-256 e deduplicação básica;
- arquivo válido entra em quarentena e não é marcado como validado;
- arquivo inválido fica rejeitado com motivo acionável;
- upload por usuário sem permissão é bloqueado.

Evidência visual esperada:

- `/c/{slug}` na aba `Arquivos` com input de arquivo local aceitando `.stl,.3mf,.zip`;
- card exibindo `Metadados`, `Quarentena`, `Validado` ou `Rejeitado`;
- erro legível quando upload ou validação falha;
- ausência de path local/sessão/segredo no render.

### PKG-58 - Visualização 3D, thumbnails e análise técnica de modelos

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- análise STL binária determinística sem executar código externo;
- extração de dimensões, bounding box, volume aproximado, malhas e triângulos;
- geração de thumbnail SVG controlado por metadados;
- alerta de suporte provável e escala/dimensão suspeita;
- falha de análise fica restrita ao arquivo e não quebra o item/biblioteca;
- endpoint exige arquivo em quarentena e permissão de dono/administrador;
- build frontend valida render de preview e estados técnicos no card.

Evidência visual esperada:

- `/c/{slug}` na aba `Arquivos` com botão `Analisar` em arquivos quarentenados;
- card exibindo preview SVG, dimensões, volume, triângulos e alertas;
- estado `analysis_failed` exibido de forma controlada quando o arquivo não é analisável.

### PKG-59 - Licenças, autoria e atribuição de modelos

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- item público/comunitário exige autoria declarada, licença e aceite de termos;
- item privado pode permanecer como rascunho sem publicação pública;
- fonte pública é validada como URL externa segura;
- texto de atribuição rejeita markup/script;
- remix referencia item de origem ativo e não pode referenciar o próprio item;
- cards de comunidade e perfil exibem licença/autoria junto ao download.

Evidência visual esperada:

- formulário de `Arquivos` com `Autor original`, `Fonte pública`, `Crédito e atribuição` e aceite de `Termos`;
- card da biblioteca com licença, autor, fonte e origem de remix quando houver;
- download sempre acompanhado de licença visível.

### PKG-60 - Versionamento, remix e derivados de modelos

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
backend/.venv/bin/python -m pytest backend/tests/test_schema_versioning.py backend/tests/test_update_self.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- cadastro do item cria versão inicial imutável;
- nova versão preserva snapshot de arquivos e changelog sem sobrescrever versão anterior;
- versão anterior pode ser promovida como atual por rollback lógico;
- download de versão específica incrementa contador da versão sem perder contador geral;
- criação e promoção de versão exigem dono do item ou administrador;
- schema mais recente registra `050_social_library_versions.sql`.

Evidência visual esperada:

- card da aba `Arquivos` com bloco `Histórico de versões`;
- versão atual destacada;
- formulário compacto para nova versão com changelog;
- ações de download de versão específica e uso de versão anterior.

### PKG-61 - Coleções, favoritos, downloads e listas de impressão

Validação automatizada obrigatória para fechamento:

```bash
backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q
backend/.venv/bin/python -m pytest backend/tests/test_schema_versioning.py backend/tests/test_update_self.py -q
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Cenários cobertos:

- favorito fica isolado por usuário e aparece no resumo do organizador;
- coleção privada não aparece no organizador de outro usuário;
- coleção de comunidade exige comunidade válida;
- item adicionado à coleção referencia item visível e versão existente;
- lista de impressão só aceita impressora do dono;
- item de lista de impressão referencia versão específica do modelo;
- status da lista cobre `want_to_print`, `printed` e `problem`;
- histórico de downloads autenticado fica no resumo do usuário e preserva versão.

Evidência visual esperada:

- aba `Arquivos` com bloco `Coleções e listas`;
- criação de coleção separada do cadastro de modelo;
- criação de lista de impressão separada do cadastro de modelo;
- card de modelo com ações de favoritar, adicionar à coleção e adicionar à lista.

## Update do agente

Validação focada:

```bash
cd backend && uv run pytest tests/test_agent_support.py tests/test_agent_updates.py -q
cd frontend && npm run build
```

Aceite:

- agente `0.1.8+` cria job remoto `remote_agent_update_check`;
- agente legado com SSH configurado tenta update automático pelo backend;
- agente legado sem SSH configurado orienta comando manual somente como último caso;
- manifesto e binário servido têm SHA-256 compatível.

## Métricas do host do agente

Validação focada:

```bash
cd agent && go test ./internal/agent
cd backend && uv run --extra dev pytest tests/test_agent_support.py tests/test_agent_updates.py tests/test_agent_install.py -q
cd frontend && npm run build
```

Aceite:

- agente Linux envia `capabilities.host_metrics` cacheado por 5 minutos no heartbeat;
- snapshot informa memória do host, rede agregada do host e CPU/RSS por serviço detectado;
- coleta usa leitura local de `/proc`, sem shell remoto, sem G-code, sem Moonraker mutável e sem payload sensível;
- tela `Detalhe do agente > Dispositivo do agente` mostra o snapshot atual sem criar histórico dedicado de métricas.

## Reinstalação do agente

Validação focada:

```bash
cd backend && uv run --extra dev pytest tests/test_agent_pairing.py tests/test_agent_install.py -q
cd frontend && npm run build
```

Aceite:

- `POST /api/agent/pairing/exchange` retorna erro estruturado e acionável quando a mesma identidade de host já estiver pareada;
- instalador Linux trata body JSON, texto, HTML ou vazio em erro HTTP sem `JSONDecodeError`;
- mensagem do instalador orienta gerar novo comando ou revogar/remover agente antigo sem vazar token, credencial ou payload;
- UI separa `Agentes pareados`, `Online agora` e `Tokens de instalação`;
- remover token de instalação não sugere remoção de agente já pareado;
- fluxo de instalação alerta quando a impressora já tem agente pareado ativo/offline.

## Instalação 0.1.5

Validação offline:

```bash
./scripts/ensure_node_runtime.sh --plan
./scripts/install_printora.sh --plan
./scripts/install_printora_autostart.sh --plan
```

Aceite:

- `--plan` não altera arquivos;
- plano informa se usará Node atual ou Node 22 via `nvm`;
- plano de autostart informa o mecanismo do ambiente atual;
- `--apply --yes` prepara dependências e configura boot automático;
- Linux/Raspberry usa `systemd` com `Restart=always`;
- Linux/Raspberry configura `/etc/sudoers.d/printora-restart` com permissão mínima para `systemctl restart/status printora.service` sem senha;
- Android/Termux usa `Termux:Boot` e `tmux`;
- macOS usa `launchd` com `KeepAlive`;
- Windows usa tarefa agendada `Printora`;
- Node antigo não substitui o Node global do sistema, preservando serviços como Spoolman.

## Updater 0.1.6

Aceite do fluxo visual:

- tela de releases mostra apenas a ação `Atualizar agora` para nova release;
- o plano obrigatório do backend continua sendo criado antes do apply, mas não aparece como botão separado;
- modal planejado mostra revisão, backups previstos e confirmação, sem linha do tempo;
- linha do tempo aparece somente durante update, falha, conclusão ou rollback;
- em execução, etapas pendentes ficam ocultas e entram na lista conforme o script marca cada etapa;
- modal do updater não cria rolagem interna dentro da linha do tempo.

## Instalador 0.1.7

Aceite para dependências frontend:

- `npm install` roda com o Node isolado do Printora quando `.printora-node-env` existir;
- falha `npm ERR! code ENOTEMPTY` em `frontend/node_modules` não trava a instalação;
- o retry limpa somente `frontend/node_modules` do Printora e não altera Node/npm global;
- `package-lock.json` é preservado;
- serviços externos, incluindo Spoolman, não são modificados.

## Instalador 0.1.8

Aceite para Raspberry/Linux:

- release inclui `frontend/dist` versionado;
- instalador usa `frontend/dist/index.html` existente e pula `npm install`/`npm run build` por padrão;
- build local só roda com `PRINTORA_REBUILD_FRONTEND=1` ou quando `frontend/dist` estiver ausente;
- instalação não aparenta travar em `tsc -b && vite build` em Raspberry.

## Instalação Resiliente E Recuperação De Update

Aceite:

- porta padrão do Printora é `8069` em runner, instalador, frontend, Docker e documentação;
- instaladores públicos por plataforma (`install-macos.sh`, `install-linux.sh`, `install-android-termux.sh`, `install-windows.ps1`) verificam dependências, mostram itens OK e perguntam antes de instalar ausentes;
- `scripts/bootstrap_dev.sh --apply` seleciona Python `3.11+` mesmo quando `python3` global é antigo;
- venv `backend/.venv` criada com Python incompatível é recriada;
- instalador atualiza `pip`, `setuptools` e `wheel` dentro da venv local antes de instalar o backend;
- `scripts/install_printora_autostart.sh --apply --yes` valida `/health` depois de configurar o boot;
- `scripts/doctor_install.sh` roda sem alterar arquivos de app e mostra Python, Node, porta, banco, serviço e logs;
- `GET /api/system/install-diagnostics` retorna diagnóstico copiável com versão, ambiente, porta, paths, checks e ação sugerida;
- em Raspberry, `GET /api/system/install-diagnostics` inclui `raspberry_throttling` via `vcgencmd get_throttled`, sinalizando normal, throttled atual ou throttling histórico sem executar ação mutável;
- tela `Configurações > Diagnóstico da instalação` permite recarregar e copiar o diagnóstico técnico;
- `scripts/unlock_update.sh` cria backup do `printora.db` e marca updates `running` como `failed`;
- `POST /api/system/update/reconcile` reconcilia update `running` antigo e retorna contagem de runs ainda em execução;
- tela `Configurações > Histórico de updates` tem ação para reconciliar updates travados.
- scripts de update validam `/openapi.json` após restart para confirmar que o backend reiniciado está na versão alvo, evitando frontend novo com backend antigo.

## Setup Do Zero Via SSH

Aceite do PKG-34:

- placa virgem sem sistema operacional fica explicitamente fora do acesso SSH; o fluxo deve orientar preparar mídia/boot antes do provisionamento remoto;
- `POST /api/setup/ssh/preflight` executa somente comandos read-only por SSH e retorna `safe_mode=ssh_read_only_preflight`;
- `POST /api/setup/ssh/plan` retorna `safe_mode=ssh_dry_run_plan` e comandos planejados prefixados por `PLAN`;
- senha, token e conteúdo de chave privada não entram no payload, histórico, logs ou banco;
- `key_path` pode ser usado para execução local do comando SSH, mas não é persistido no histórico;
- histórico `GET /api/setup/ssh/history` lista preflights e planos sem segredos;
- preflight classifica SSH, SO, systemd, ferramentas base, ferramentas de build, Klipper, Moonraker, `printer_data` e `can0`;
- plano separa preparação de mídia, dependências, Klipper, Moonraker, UI web, Printora, CAN e firmware futuro;
- o PKG-34 não executa instalação real, `apt`, edição de arquivo, restart, flash, G-code, alteração de Klipper/Moonraker ou gravação de firmware.

Validação focada:

```bash
cd backend && uv run pytest tests/test_setup_wizard.py -q
cd frontend && npm run build
```

## Setup CAN/U2C/can0

Aceite do PKG-35:

- `POST /api/setup/can/preflight` executa somente coleta read-only via SSH e retorna `safe_mode=can_read_only_preflight`;
- diagnóstico coleta ferramentas, sudo sem senha, módulos CAN, USB/U2C, links, `ip -details -statistics link show can0`, serviços, estado de impressão e UUIDs CAN quando o tooling existir;
- `POST /api/setup/can/plan` retorna `safe_mode=can_dry_run_plan` e todos os comandos mutáveis aparecem apenas como `PLAN`;
- plano diferencia U2C ausente, módulos ausentes, `can0` ausente, bitrate divergente, impressão em andamento e host sem systemd;
- `POST /api/setup/can/apply` exige confirmação `CONFIGURAR CAN0` e `PRINTORA_CAN_SETUP_MODE=remote`; sem isso registra tentativa bloqueada;
- apply real cria backup remoto antes de escrever `/etc/systemd/system/can0.service`, faz `daemon-reload`, `enable`, `restart` e valida `can0`;
- apply bloqueia se detectar impressão em andamento via Moonraker local;
- histórico `GET /api/setup/can/history` não persiste senha, token, chave privada ou `key_path`;
- o pacote não executa build de firmware, flash, G-code, alteração de Klipper/Moonraker, restart de Klipper/Moonraker ou gravação de `printer.cfg`.

Validação focada:

```bash
cd backend && uv run pytest tests/test_setup_can.py -q
cd frontend && npm run build
```

## Wizard Remoto De Firmware

Aceite do PKG-36:

- `POST /api/setup/firmware/plan` exige preset existente e confirmação da variante física para liberar plano pronto;
- plano gera `.config` determinístico a partir do preset, calcula `sha256`, define artefatos remotos e retorna comandos somente como `PLAN`;
- plano não executa `make`, flash, restart, update, G-code, alteração de Moonraker/Klipper ou edição de `printer.cfg`;
- `POST /api/setup/firmware/build` exige confirmação `BUILD_FIRMWARE_NO_FLASH` e `PRINTORA_REMOTE_FIRMWARE_BUILD_MODE=remote`; sem isso registra tentativa bloqueada;
- build remoto salva `.config` gerado em diretório controlado, faz backup de `<klipper_path>/.config`, executa `make clean && make`, copia binário, calcula hashes, consulta UUIDs CAN quando possível e restaura `.config`;
- falha de build preserva log copiável e restaura `.config` por trap;
- histórico `GET /api/setup/firmware/history` não persiste senha, token, chave privada ou `key_path`;
- UUID capturado é sugestão revisável e nunca grava automaticamente em `printer.cfg`;
- flash real fica fora do PKG-36.

## Flash Supervisionado

Aceite do PKG-37:

- `POST /api/setup/flash/preflight` executa somente leitura remota e bloqueia sem checklist físico, artefato existente, impressora parada, método suportado e UUID visível;
- `POST /api/setup/flash/plan` retorna comandos somente como `PLAN`, frase de confirmação específica por placa/método e rollback manual antes da execução;
- `POST /api/setup/flash/execute` exige a frase gerada no plano e `PRINTORA_REMOTE_FLASH_MODE=remote`; sem isso registra tentativa bloqueada;
- execução real inicial suporta somente `can_katapult`; `usb_dfu` e `manual` ficam bloqueados até implementação própria;
- flash CAN/Katapult não edita `printer.cfg`, não reinicia serviços, não executa update e não envia G-code;
- falha de flash deve retornar `requires_recovery` ou `blocked` com log copiável e rollback manual;
- histórico `GET /api/setup/flash/history` não persiste senha, token, chave privada ou `key_path`;
- validação em hardware real acompanhado continua obrigatória antes de tratar o pacote como operacional em campo.

Validação focada:

- `cd backend && uv run pytest tests/test_setup_flash.py`;
- `cd frontend && npm run build`;
- fechamento: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

## Validação Final Da Base Klipper

Aceite do PKG-38:

- `POST /api/setup/final-validation/run` executa somente leitura via SSH;
- coleta serviços, Moonraker/Klipper, `can0`, UUIDs, configs, temperaturas, Update Manager e logs recentes sem G-code e sem mutação;
- status diferencia aprovado para calibração, aprovado com observação, bloqueado e requer intervenção manual;
- relatório Markdown sanitizado remove caminhos locais, IPs/URLs e padrões sensíveis;
- histórico `GET /api/setup/final-validation/history` não persiste senha, token, chave privada ou `key_path`;
- validação real em hardware acompanhado continua obrigatória antes de homologar o fluxo em campo.

Validação focada:

- `cd backend && uv run pytest tests/test_setup_final_validation.py`;
- `cd frontend && npm run build`;
- fechamento: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 CHECK_STRICT_RUNTIME_NAMES=1 ./check.sh`.

Validação focada:

```bash
cd backend && uv run pytest tests/test_setup_firmware.py -q
cd frontend && npm run build
```

O check inicial valida:

- existência dos documentos principais;
- ausência de marcadores básicos de segredo;
- formato básico do `PATHS.toml`;
- compilação sintática do backend Python;
- validade do `frontend/package.json`;
- permissão executável do `check.sh`.

## Modelo De Testes

### Unitário

Testes unitários devem cobrir regras puras, parsers, normalização de payloads, repositórios SQLite com banco temporário e serviços sem depender de rede real.

### Cobertura mínima por criticidade

- P0/crítico: regra de negócio, contrato de API, persistência, erro/rollback e validação manual do fluxo principal quando aplicável.
- P1/alto: teste automatizado da regra ou endpoint afetado e validação focada.
- P2/P3: validação proporcional, com teste automatizado quando houver risco de regressão.

### Dados de teste e fixtures

Fixtures devem ficar em `backend/tests/fixtures` ou `frontend/tests/fixtures`, ser determinísticas e não depender de dump real, horário real, ordem implícita ou dados de produção.

## Banco Local

Mudanças de banco devem ser feitas por scripts `.sql` idempotentes em `backend/sql/`.

Validações:

- `initialize_database()` pode rodar mais de uma vez;
- `initialize_database()` registra scripts SQL aplicados em `schema_versions`;
- `initialize_database()` cria `app_version` com versão do app e revisão de schema;
- `initialize_database()` preserva dados em banco existente e cria backup no mesmo `data_dir` antes de scripts pendentes;
- falha durante aplicação de SQL restaura o banco original a partir do backup automático;
- validação pós-schema usa `PRAGMA integrity_check` e registra resultado em `schema_integrity_checks`;
- falha de `integrity_check` bloqueia conclusão de `initialize_database()`;
- reexecutar `initialize_database()` não duplica registros de versão;
- `GET /api/system/version` retorna somente metadados públicos de versão/schema, sem `data_dir`, caminho do banco, lista de scripts SQL ou resultado detalhado de integridade;
- `GET /api/system/version/internal` exige usuário de suporte e retorna os detalhes internos de schema para diagnóstico local/suporte;
- tabelas multi-impressora existem;
- endpoints não armazenam credenciais;
- fixtures ficam em `backend/tests/fixtures/`.
- snapshots ficam vinculados a `printer_id`;
- listagem de snapshot retorna resumo, não payload completo.
- comparação de snapshots rejeita snapshots de outra impressora.
- comparação classifica componentes falhando como bloqueio e repos `dirty` como risco.
- checklist pós-update retorna origem dos dados, bloqueia fallback/offline e não executa comandos mutáveis.
- checklist pós-update real por impressora deve retornar `data_state=live` quando Moonraker estiver acessível e manter smoke manual pendente.
- descoberta de impressoras aceita somente redes privadas `/24` ou menores.
- descoberta de impressoras rejeita rede pública e rede grande demais.
- descoberta de impressoras marca cadastro existente por hostname resolvido para IP.
- auditoria read-only retorna origem dos dados, classifica achados e usa último snapshot quando Moonraker está offline.
- health check permite impressora ready sem bloqueios.
- health check bloqueia Klipper não ready ou último diff crítico.
- health check classifica warning runtime de firmware MCU obsoleto como
  monitoramento e preserva MCU, recurso ausente e versões na evidência.
- health check bloqueia erro runtime crítico de comunicação MCU, protocolo,
  shutdown, temporização ou temperatura; saída normal do console não vira alerta.
- agente coleta `/server/gcode_store` somente por GET, limita a 200 entradas,
  envia no máximo 20 alertas deduplicados/sanitizados e não falha o health quando
  o histórico do console estiver indisponível.
- health check classifica repo `dirty` como monitoramento.
- health check normaliza memória real em kB do Moonraker e reporta armazenamento mesmo quando espaço livre não é exposto.
- backup dry-run cria histórico sem ler/copiar arquivos.
- políticas e histórico de backup ficam escopados por impressora.
- execução local de backup cria `.zip` usando apenas diretórios temporários em teste.
- execução local bloqueia política `dry_run_only` e destino dentro da origem.
- comparação de backups `.zip` é read-only e identifica arquivos adicionados, removidos e alterados.
- plano de restore de backup fica bloqueado e não extrai/sobrescreve arquivos.
- gate de restore aceita confirmação textual, mas permanece bloqueado e não extrai/sobrescreve arquivos.
- relatório sanitizado remove IP, URL, caminho local e valores sensíveis detectáveis.
- relatório sanitizado inclui health, snapshots, diff e histórico de backup sem dados privados.
- relatório sanitizado expõe `source` sanitizado e não vaza URL/IP/caminho/segredo no Markdown real por impressora.
- eventos de manutenção ficam vinculados à impressora correta.
- tarefa preventiva inicia pendente, ao concluir gera evento e fica em dia.
- registro manual de Z-offset calcula delta contra valor anterior compatível.
- Z-offset gera alerta `monitorar` ou `revisar` quando a variação passa do limite.
- histórico de Z-offset fica escopado por impressora.
- wizard de Z-offset retorna roteiro manual e não executa comandos.
- wizard de Z-offset recomenda revisão quando delta é alto.
- registro manual CAN calcula delta contra leitura anterior da mesma interface.
- registro manual CAN classifica `tx_retries` crescente como monitoramento.
- registro manual CAN classifica `rx_error` ou `tx_error` crescente como problema.
- registro manual CAN classifica barramento fora de `ERROR-ACTIVE` como problema.
- histórico CAN fica escopado por impressora.
- resumo CAN sem leituras retorna `data_state=no_data`.
- comparação CAN entre duas leituras manuais calcula deltas e classificação sem executar comando no host.
- comparação CAN pela UI deve escolher duas leituras da mesma interface.
- auditoria de plugins usa último snapshot Moonraker/Update Manager.
- auditoria de plugins funciona sem snapshot e não executa comandos no host.
- auditoria de plugins classifica KTC-Easy como perigoso remover agora e Auto Speed como legado/lixo técnico.
- auditoria de plugins transforma componentes fora do catálogo em item investigável com evidência e gates.
- catálogo de presets de firmware inclui placas comuns BTT, Mellow e Fysetc.
- manifesto Esoterical CANBus cobre as páginas conhecidas do menu público, usa apenas domínio `canbus.esoterical.online`, mantém status `catalogada`, `ignorada_com_motivo` ou `bloqueada_com_motivo` e registra hash por página catalogada.
- comando `python3 scripts/build_canbus_manifest.py` roda em dry-run por padrão; somente `--write` atualiza `backend/app/data/firmware_canbus_manifest.json`.
- schema Pydantic `FirmwareCatalog` valida o catálogo local com source, manifesto, workflows, hardware, troubleshooting, update flows, Katapult, CAN speed, hardwares sem preset e metadata de geração.
- normalização automática `python3 scripts/build_firmware_catalog.py` gera catálogo local a partir do manifesto em dry-run por padrão, cobrindo 56 hardwares, 9 workflows, 5 fluxos de update e 12 guias de troubleshooting sem executar comandos mutáveis.
- cobertura 100% do menu público exige que toda URL do manifesto tenha status, hash/título/categoria quando catalogada e representação no catálogo como hardware, workflow, update flow ou troubleshooting conforme a categoria.
- mapeamento de presets locais exige que hardwares com preset conhecido preencham `preset_ids` e que hardwares sem preset apareçam em `known_hardware_without_local_preset` e no inventário focado na impressora ativa.
- endpoint read-only `/api/firmware/catalog` entrega resumo validado do catálogo local com contadores por categoria/status/role, sem depender do site externo em runtime.
- inventário `/api/printers/{printer_id}/firmware/hardware-inventory` enriquece placas detectadas e cadastradas com referências compactas do catálogo e preserva deduplicação por UUID/nome/MCU.
- fechamento do PKG-30 exige testes de manifesto completo, schema, normalização por categoria, presets existentes/ausentes, endpoints, runtime local sem site externo, dry-run dos scripts e exclusão de comandos mutáveis das referências extraídas.
- validação de cobertura do PKG-30: `cd backend && uv run pytest tests/test_canbus_manifest.py tests/test_firmware.py -q`.
- validação completa de fechamento do PKG-30: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
- cadastro de placa de firmware herda MCU, conexão e método de flash do preset.
- placas CAN exigem UUID CAN.
- placas de firmware ficam escopadas por impressora.
- dry-run de build de firmware gera checklist e comandos planejados sem executar comandos.
- dry-run de build exige placa cadastrada.
- histórico de dry-run de build fica escopado por impressora.
- preflight de build de firmware valida paths/tooling local de forma read-only e mantém execução bloqueada.
- build local fica bloqueado quando `PRINTORA_FIRMWARE_BUILD_MODE` está desabilitado.
- build local exige confirmação textual quando o modo local está habilitado.
- PKG-33 exige validação incremental dos presets derivados do catálogo: hardwares cobertos ganham `preset_ids`, hardwares pendentes permanecem em `known_hardware_without_local_preset` e nenhum comando mutável é executado.
- PKG-33 Lote 1 valida que o catálogo saiu de 11 para 23 hardwares com preset local, mantendo 33 pendentes classificados por adaptador CAN, mainboard e toolhead.
- PKG-33 Lote 1 valida que os novos presets BTT, Fysetc e Mellow aparecem em `/api/firmware/board-presets` com MCU, arquitetura, comunicação, conexão, output esperado e método futuro de flash.
- PKG-33 exige schema de build config validável sem ambiente real, classificando presets como completo, faltando dados ou inválido.
- PKG-33 Lote 2 valida que `FirmwareBuildConfig` é versionado e expõe arquitetura, MCU, modelo de processador, bootloader, clock, interface de comunicação, conexão CAN/USB/serial, arquivo `.config` e output esperado.
- PKG-33 Lote 2 valida que `/api/firmware/board-presets` mantém consumidores existentes e adiciona `build_config`, `build_config_status` e `build_config_validation`.
- PKG-33 Lote 2 valida preset completo, preset com dado faltante e schema inválido com erro claro, sem executar `make`, build real, flash, SSH, restart ou update.
- PKG-33 exige snapshots determinísticos do `.config` gerado para presets completos, sem depender de relógio, host Klipper, ordem implícita ou site externo.
- PKG-33 Lote 3 valida snapshot exato do `.config` para pelo menos um preset STM32 e um preset RP2040.
- PKG-33 Lote 3 valida `GET /api/firmware/board-presets/{preset_id}/config-preview` retornando preview em memória, `artifact_saved=false`, sem executar comando externo e sem escrever em diretório Klipper.
- PKG-33 Lote 3 valida que preset com `build_config` incompleto bloqueia a geração de `.config` com erro acionável.
- PKG-33 exige que dry-run de build planeje `.config`, backup, diretório de trabalho, output, log e comandos sem executar `make`, SSH, flash, restart, update ou cópia para Klipper.
- PKG-33 Lote 4 valida que dry-run com preset completo retorna `preset_id`, `preset_build_config_status`, `generated_config_path`, `config_backup_path`, `work_dir`, `expected_build_output`, `binary_output_path`, `log_path` e comandos `PLAN ...` sem executar processo externo.
- PKG-33 Lote 4 valida que dry-run com preset incompleto falha com erro claro, não grava histórico e não executa comando externo.
- PKG-33 Lote 4 valida que o histórico de build continua filtrado por impressora e identifica a placa de cada plano.
- PKG-33 exige que build real continue bloqueado por padrão; quando houver lote de build controlado, testes devem usar ambiente fake/tmpdir e validar confirmação textual, backup, restauração de `.config`, log e binário salvo sem flash.
- PKG-33 Lote 5 valida que build local real fica bloqueado por modo `disabled`, bloqueia e registra confirmação ausente/incorreta, usa `.config` gerado pelo preset, salva backup, preview, log e binário em `output_root/local-build/<placa>/`, restaura `.config` em sucesso e falha e não planeja flash, restart ou SSH.
- PKG-33 Lote 6 valida a tela Firmware com foco na impressora ativa: placas detectadas/cadastradas antes do catálogo, badge de preset completo/incompleto, preview de `.config`, dry-run de build, build local protegido por confirmação e ausência de chamadas/botões de flash, SSH, restart ou update.
- fechamento do PKG-33 exige testes focados de firmware, validação manual da tela Firmware e `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
- dry-run de flash usa binário de build quando informado e não executa comandos.
- dry-run de flash rejeita build de outra placa.
- preflight de flash lê Moonraker/Klipper, bloqueia impressão em andamento e nunca libera execução real neste lote.
- plano de recuperação de firmware é manual, bloqueado e não executa flash, restart, SSH ou comandos locais.
- catálogo de calibração é criado por SQL idempotente.
- catálogo de calibração classifica modo de execução, risco e bloqueio durante impressão.
- catálogo de calibração pode ser filtrado por categoria.
- histórico manual de calibração fica escopado por impressora.
- histórico manual rejeita chave de teste inexistente.
- sequência de calibração marca testes concluídos e pendentes sem enviar G-code.
- preflight de calibração usa leitura real Moonraker/Klipper, bloqueia durante impressão e nunca libera envio de G-code neste lote.
- execução de calibração exige operador presente, revisão de G-code, confirmação textual, preflight live e registra comandos enviados.
- execução de calibração monitora Moonraker/Klipper após o envio e trata timeout de transporte como sucesso quando o estado final fica confirmado.
- retorno final da execução de calibração fica disponível para preencher o registro manual do resultado.
- execução de calibração bloqueia Moonraker offline, impressão em andamento e comando fora da allowlist.
- artefatos de systemd, Mainsail e Update Manager existem e apontam para serviço local.
- instalador Raspberry roda em dry-run por padrão.
- bootstrap dev macOS/Linux roda em dry-run por padrão.
- instalador Linux recusa macOS/Windows e hosts sem systemd.
- Docker Compose define porta, volume e modo seguro por padrão.
- validador de integração Mainsail/Moonraker/systemd roda offline e verifica artefatos de instalação.
- frontend organiza os painéis em navegação lateral por domínio.
- frontend mantém as ações existentes sem executar comandos novos na troca de seção.
- frontend mantém a impressora ativa na topbar e usa esse contexto no restante do sistema.
- cadastro/detecção de impressora acontece em modal, sem poluir o dashboard.
- frontend separa Monitoramento, Calibração, Firmware, Manutenção, Relatórios e Configurações.
- frontend mostra orientação objetiva de uso em cada seção.
- operação read-only real deve retornar `safe_mode=read_only`, `can_send_commands=false`, painéis populados e ações bloqueadas por impressora.
- fallback de último estado operacional deve preservar objetos conhecidos do snapshot para matriz de capacidades.
- histórico de temperatura por snapshot deve ser ordenado e não consultar Moonraker ao montar os pontos históricos.
- matriz de capacidade deve usar objetos reais/último snapshot sem pressupor Voron específica, mantendo ações sem objeto conhecido como `unknown`.
- preflight final por ação operacional deve usar leitura live, bloquear impressão em andamento, bloquear capacidade ausente e manter `can_execute=false`.
- releases do Printora usam fixtures em `backend/tests/fixtures/` e `frontend/tests/fixtures/`.
- `GET /api/system/releases` retorna `safe_mode=read_only`, versão instalada, canal, última release, changelog resumido e status `up_to_date`, `outdated` ou `unknown`.
- `GET /api/system/update/status` é somente leitura e retorna `update_supported=false`.
- falha de rede, GitHub offline ou rate limit retornam payload seguro e não quebram a aplicação.
- a tela Configurações carrega o restante da UI mesmo quando releases falham.
- a tela Configurações tem somente ação de verificação de releases/status e não chama rota mutável de update.
- plano do updater do próprio Printora cria histórico em `app_update_runs` e etapas em `app_update_steps` sem alterar arquivos.
- plano do updater detecta Android/Termux e Unix, e rejeita ambiente desconhecido.
- histórico do updater lista runs e permite abrir um run com suas etapas.
- histórico/apply/rollback do updater reconciliam run `running` órfão após reboot: fecha como sucesso se a versão instalada já for o alvo, e como falha somente quando estiver antigo e a versão não bater.

Testes automatizados adicionais:

```bash
cd backend
. .venv/bin/activate
pytest
```

```bash
cd frontend
npm run test:releases
npm run build
```

## Execução Local Do MVP

Backend:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8069 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Abrir:

```text
http://127.0.0.1:5178
```

## Testes Manuais Futuros

### Auditoria

- Rodar auditoria em ambiente Klipper real.
- Confirmar que não altera arquivos.
- Confirmar classificação dos achados.
- Validar `GET /api/audit/read-only` com Moonraker real.
- Confirmar que falha de conexão vira `precisa_confirmacao`, não erro fatal.

### Auditoria Do Host

- Validar `GET /api/audit/host-read-only` com `PRINTORA_HOST_AUDIT_MODE=disabled`.
- Validar parser de `systemctl`, CAN, Git e symlinks via testes unitários.
- Validar em Raspberry com `PRINTORA_HOST_AUDIT_MODE=local`.
- Validar em desenvolvimento com `PRINTORA_HOST_AUDIT_MODE=ssh` e chave SSH.
- Confirmar que não há `restart`, `update`, `flash`, `rm`, `mv`, `cp` ou G-code no script read-only.

### Backups

- Criar backup.
- Confirmar arquivos incluídos.
- Confirmar que segredos não vazam.
- Testar restauração por arquivo em ambiente controlado.

### Manutenção

- Criar tarefa preventiva.
- Concluir tarefa.
- Confirmar que evento aparece no diário.
- Marcar rotina do catalogo como `N/A`, confirmar que sai da grade principal, aparece no filtro `N/A` e volta ao plano ao acionar `Desfazer`.
- Confirmar que rotinas relacionadas exibem badges de area no card, que o filtro de area junta tarefas proximas e que a ordenacao por area, titulo, criticidade e vencimento reorganiza a grade unica.
- Confirmar que nenhuma ação foi enviada para Klipper/Moonraker.

### Z-offset

- Registrar primeiro valor de Z-offset para chapa/material/nozzle.
- Registrar segundo valor compatível.
- Confirmar delta e alerta.
- Confirmar que nenhum G-code foi enviado e nenhum arquivo Klipper foi alterado.
- Gerar wizard e confirmar que comandos aparecem apenas como orientação.

### CAN

- Registrar uma leitura manual de `can0` com `rx_error=0`, `tx_error=0` e `tx_retries=0`.
- Registrar nova leitura com `tx_retries` maior e confirmar alerta de monitoramento.
- Registrar nova leitura com `rx_error` ou `tx_error` maior e confirmar alerta de problema.
- Confirmar que o app não executou SSH, `ip`, G-code, restart, update ou flash.

### Mods E Plugins

- Capturar snapshot Moonraker.
- Abrir painel de mods e plugins.
- Confirmar que itens do Update Manager aparecem como detectados.
- Confirmar classificação de KTC-Easy/StealthChanger, KAMP, `led_effect`, Crowsnest, Sonar, Timelapse, Auto Speed, TapChanger e TMC Autotune.
- Confirmar que nenhuma remoção, update, restart ou edição de config foi executada.

### Atualizacoes Da Impressora

- Silenciar uma versao pendente de qualquer componente do Update Manager e confirmar que o card continua com `Reanalisar`, `Atualizar` e `Rollback` quando aplicavel.
- Confirmar que `Atualizar` usa icone diferente de `Reanalisar` e visual secundario alinhado a `Marcar feita` da Manutencao.
- Confirmar que o silencio abre modal visual do Printora, sem `confirm` nativo do navegador.
- Confirmar que, apos confirmar o silencio, o card do componente mostra estado de execucao e o botao muda para `Silenciando...` ate a requisicao concluir ou falhar.
- Confirmar que a rota de silencio persiste a versao exibida no card sem consultar Moonraker, inclusive quando o host configurado nao resolve.
- Confirmar que sucesso/falha de silencio e reativacao aparece como toast temporario.
- Confirmar que a versao silenciada sai dos contadores da Home, topbar, Central de alertas, Health Check, Checklist pos-update, Auditoria e Relatorios.
- Reativar o alerta e confirmar que os contadores voltam.
- Simular nova versao remota, pacote, atraso, warning ou anomalia e confirmar que o silencio anterior nao se aplica.

### Releases Do Printora

- Iniciar backend com fixture de update disponível:

```bash
PRINTORA_RELEASE_SOURCE_MODE=fixture \
PRINTORA_RELEASE_FIXTURE_PATH=/Users/brenomayder/projects/printora/backend/tests/fixtures/github_releases.json \
PRINTORA_DATA_DIR=/tmp/printora-releases-outdated \
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8091
```

- Abrir `http://127.0.0.1:8091`, entrar em Configurações e confirmar:
  - card `Releases do Printora` aparece;
  - versão instalada aparece;
  - última release aparece como `v0.2.0`;
  - canal aparece como `stable`;
  - status aparece como `update disponível`;
  - changelog resumido aparece;
  - lista de releases de produção aparece;
  - existe botão `Verificar releases`;
  - não existe botão para atualizar/aplicar update.
- Repetir com fixture `github_releases_current.json` e confirmar status `já atualizado`.
- Simular rede indisponível ou rate limit e confirmar que Configurações, Moonraker, Klipper e demais painéis continuam visíveis.
- Confirmar pelo DevTools/log do backend que a tela chama apenas `GET /api/system/releases` ou `GET /api/system/update/status` e não faz `POST`, `PUT` ou `DELETE` para rotas de update.

### Firmware Manager

- Abrir Firmware com impressora ativa offline e confirmar que o resumo local do catálogo aparece, enquanto a leitura ao vivo informa falha do Moonraker.
- Abrir Firmware com impressora ativa online e confirmar que MCUs/placas detectadas e cadastradas aparecem antes de qualquer referência de catálogo.
- Confirmar que o catálogo aparece apenas como sugestão/referência compacta por placa da impressora ativa, não como lista genérica de presets ou hardwares.
- Confirmar status de preset local existente e aviso de preset ausente nas referências do catálogo.
- Abrir link do guia Esoterical CANBus e confirmar que ele é apenas referência técnica.
- Confirmar que nenhuma ação de build, flash, update, SSH, restart ou alteração local é executada a partir das referências do catálogo.
- Abrir lista de presets.
- Cadastrar uma Octopus USB-CAN bridge com UUID CAN.
- Cadastrar um EBB CAN com UUID CAN.
- Confirmar que MCU, método de flash futuro e arquivo `.config` aparecem no painel.
- Confirmar que nenhum build, flash, SSH, restart ou update foi executado.
- Gerar dry-run de build para uma placa.
- Confirmar checklist, comandos planejados, backup `.config` planejado e caminho do binário.
- Confirmar que nenhum `make`, cópia de arquivo, SSH, restart, update ou flash foi executado.
- Rodar preflight de build para uma placa.
- Confirmar checks de Klipper, Makefile, `.config`, config da placa, `make` e modo local sem criar diretórios ou executar comandos.
- Para PKG-33, confirmar placa com preset completo, placa com preset incompleto, geração/preview de `.config`, dry-run com artefatos planejados e bloqueio explícito de build real por padrão.
- Para PKG-33, confirmar que a tela Firmware mostra o estado do preset por placa da impressora ativa, sem listar o catálogo completo como fluxo principal.
- Para PKG-33 Lote 6, confirmar impressora offline, impressora online, placa com preset completo, placa sem preset, botão de `.config`, botão de dry-run, artefatos/log de build concluído e ausência de flash, SSH, restart e update na tela.
- Tentar execução local sem habilitar modo local e confirmar status bloqueado.
- Em ambiente controlado futuro, habilitar modo local e exigir confirmação textual antes de executar build.
- Gerar dry-run de flash para uma placa.
- Confirmar checklist, UUID CAN, interface CAN, binário e comandos planejados.
- Confirmar que nenhum flash, restart, SSH, update ou validação de MCU ao vivo foi executado.
- Rodar preflight de flash para uma placa com a impressora ligada.
- Confirmar Moonraker/Klipper ready, impressão parada, binário/método/UUID e `can_execute_flash=false`.

### Firmware Dry-Run

- Cadastrar placa.
- Selecionar preset.
- Rodar dry-run.
- Confirmar que nenhum flash foi feito.
- Confirmar log completo.

### Firmware Flash

Executar somente em ambiente autorizado.

Critérios:

- impressora parada;
- backup criado;
- UUID validado;
- binário gerado;
- flash concluído;
- MCU voltou;
- Klipper ready.

### Calibração E Testes

- Abrir painel de calibração.
- Confirmar que homing, QGL, probe accuracy, bed mesh, primeira camada, flow, pressure advance, input shaper e testes de qualidade aparecem.
- Confirmar que itens com G-code mostram o código apenas para revisão.
- Confirmar que nenhum botão de execução de G-code existe nesta etapa.

### Navegação Do Frontend

- Abrir `http://127.0.0.1:5178`.
- Confirmar que existe sidebar com Visão geral, Impressoras, Monitoramento, Calibração, Firmware, Manutenção, Relatórios e Configurações.
- Confirmar que trocar de seção muda os painéis visíveis sem recarregar a página.
- Confirmar que a impressora ativa fica selecionável na topbar.
- Confirmar que a topbar mostra alertas, configuração de impressora e atualização.
- Confirmar que Visão geral mostra decisão operacional e checklist.
- Confirmar que Visão geral mostra dashboard de impressoras.
- Confirmar que `Adicionar impressora` abre modal.
- Confirmar que `Buscar na rede` lista candidatos Moonraker dentro do modal sem cadastrar automaticamente.
- Confirmar que Monitoramento concentra Health Check, CAN, Moonraker, Klipper e auditorias.
- Confirmar que Firmware mostra placas da impressora ativa, presets associados, dry-runs e referências compactas do catálogo local, sem listar mods/plugins no conteúdo principal.
- Confirmar que Calibração mostra o centro de testes/calibração Voron em cards.
- Confirmar que Calibração preserva os cards como fluxo principal, mostra número de sequência nos cards, busca textual, filtros por tipo/uso, ação Pular e perfil aprovado de primeira camada.
- Confirmar que cada item mostra risco, modo de execução, pré-condições e critérios de sucesso.
- Registrar resultado manual de um teste.
- Confirmar que o histórico mostra status, material, chapa, nozzle, valor observado e notas.
- Com operador presente, revisar G-code, marcar operador presente, informar `EXECUTE_CALIBRATION_GCODE` e executar apenas teste seguro selecionado.
- Confirmar que a execução aparece no histórico com comandos enviados ou motivo de bloqueio.
- Confirmar que a tela de Calibração mostra cards por teste, ajuda expandida em modal e execução/registro em modais, sem tutorial técnico fixo na página.
- Em Operação, validar preflight e execução controlada de ações como Home, QGL, movimento, temperatura, fan, LED, speed factor e extrusion factor somente com a impressora parada e operador presente.
- Em Operação > Miscellaneous, validar que fans, output pins e LEDs aparecem quando os valores vierem do agente e que a tela mostra falha de coleta quando o Moonraker detectar objetos sem status dinamico.
- Em Operação ociosa, validar que o card `Impressão` mostra a lista de G-codes recentes quando o agente/Moonraker retornam arquivos e não preserva thumbnail, progresso ou fatos do job anterior.
- Em Operação, validar que leituras concorrentes da mesma impressora reutilizam a mesma requisição, que o carregamento inicial não mostra Moonraker offline e que versão ainda não recebida não gera aviso falso de agente desatualizado.
- Confirmar que o app mostra capacidade, bloqueadores, G-code planejado e histórico da tentativa; comandos são enviados somente quando Moonraker está online, Klipper/Klippy estão `ready`, não há impressão em andamento e a capacidade foi confirmada.

### UI

- Abrir app em navegador normal.
- Abrir app pelo Mainsail.
- Validar layout desktop.
- Validar layout no navegador embutido do OrcaSlicer.

### Integração Raspberry

- Rodar `./scripts/install_raspberry.sh` sem `--apply`.
- Confirmar que a saída mostra `DRY-RUN`.
- Confirmar que nenhum serviço foi instalado/iniciado.
- Revisar `packaging/systemd/printora.service`.
- Revisar `packaging/mainsail/navi.json`.
- Revisar `packaging/moonraker/update_manager_printora.conf`.
- Confirmar que `docs/INSTALL_RASPBERRY.md` contém rollback.

### Instalação Multiplataforma

- Rodar `./scripts/run_app.sh --status`.
- Rodar `./scripts/run_app.sh --no-open`.
- Confirmar `GET http://127.0.0.1:8069/health`.
- Rodar `./scripts/run_app.sh --stop`.
- Rodar `./scripts/run_app.sh --foreground --no-open` em terminal dedicado e confirmar que a aplicação permanece online enquanto o processo estiver aberto.
- Rodar `./scripts/bootstrap_dev.sh` sem `--apply`.
- Confirmar que a saída mostra `DRY-RUN`.
- No macOS, confirmar data dir em `~/Library/Application Support/Printora`.
- Revisar `scripts/bootstrap_windows.ps1`.
- Revisar `scripts/run_app_windows.ps1`.
- No Windows, rodar `.\scripts\run_app_windows.ps1 --status`.
- No Windows, abrir `Abrir Printora.bat` e confirmar `GET http://127.0.0.1:8069/health`.
- Revisar `Dockerfile` e `docker-compose.yml`.
- Confirmar que `README.md` direciona para guias públicos separados por sistema operacional e que `docs/INSTALL_MULTIPLATFORM.md` funciona como índice.

### Updater Do Printora

- Confirmar que `GET /api/system/version` retorna versão do app e schema aplicado sem caminhos locais.
- Confirmar que `GET /api/system/version/internal` exige usuário de suporte para expor detalhes internos de schema.
- Confirmar que `GET /api/system/releases` funciona com fixture local e com rede indisponível.
- Confirmar que a tela Configurações mostra versão instalada, última release e changelog.
- Chamar `POST /api/system/update/plan` com tag alvo e confirmar que apenas o banco local registra plano/etapas.
- Chamar `GET /api/system/update/history` e `GET /api/system/update/runs/{run_id}` e confirmar que o plano aparece com etapas pendentes.
- Rodar plano de update e confirmar que nenhum arquivo é alterado.
- Confirmar que o plano lista backup do banco, versão alvo, rebuild backend, rebuild frontend, aplicação SQL e restart.
- Executar update em ambiente descartável com banco contendo duas impressoras.
- Confirmar que `printora.db` é preservado e backup `before-update` é criado.
- Confirmar que scripts SQL novos são aplicados uma única vez.
- Confirmar que `/health` responde após o update.
- Confirmar que `/api/printers` mantém as impressoras cadastradas.
- Simular falha durante rebuild frontend e confirmar que o banco original permanece disponível.
- Simular falha durante aplicação SQL e confirmar que o backup do banco está disponível.
- No Android/Termux, confirmar que o updater preserva a porta configurada e reinicia as sessões `tmux`.
- No Android/Termux, validar `scripts/android_update_printora.sh --plan --tag vX.Y.Z` e confirmar JSON parseável sem alteração de arquivos.
- Validar `POST /api/system/update/apply` com confirmação `ATUALIZAR PRINTORA`, tag estável e ambiente Android/Termux, confirmando persistência de run/steps e histórico de sucesso ou falha.
- Confirmar que `POST /api/system/update/apply` rejeita confirmação inválida, tag inválida e ambiente desconhecido.
- Na tela Configurações, confirmar que release disponível mostra `Planejar update`, abre modal de plano, só habilita `Aplicar update` após digitar `ATUALIZAR PRINTORA`, faz polling do run, mostra progresso sem despejar JSON bruto e atualiza releases/histórico automaticamente ao concluir.
- Se a conexão cair durante o restart do Printora, confirmar que a modal continua rechecando automaticamente e atualiza para concluído quando a versão alvo responder, sem exigir reload manual.
- Na tela Configurações, confirmar que `not_supported` exibe mensagem clara e não libera apply quebrado.
- No Android/Termux físico, validar `scripts/android_update_printora.sh --apply --tag vX.Y.Z`, conferindo backup do banco em `~/.local/share/printora/backups`, pasta anterior `~/Printora.previous-update-<timestamp>`, restart das sessões `tmux` e `/health`.
- Validação real Android/Termux em 2026-05-23:
  - aparelho ADB `RXCW10ATDBN`;
  - URL validada `http://printora.local:8069/`;
  - `GET /api/system/releases` retornou `installed_version=0.1.0`, `latest_release_available=true` e release estável `v0.1.1`;
  - `POST /api/system/update/plan` criou run planejado sem alterar arquivos;
  - `POST /api/system/update/apply` retornou run `running` e disparou o script destacado;
  - backup do banco criado em `/data/data/com.termux/files/home/.local/share/printora/backups/printora.db.before-update-20260523T011445Z`;
  - pasta anterior preservada em `/data/data/com.termux/files/home/Printora.previous-update-20260523T011445Z`;
  - `/health` respondeu em `127.0.0.1:8069`, `192.168.15.16:8069` e `printora.local:8069`;
  - `GET /api/system/version` retornou `version=0.1.1` e `schema_revision=18`;
  - banco manteve duas impressoras: `Voron 0.2` e `Voron 2.4`;
  - run 7 ficou `succeeded` diretamente no SQLite, com steps `succeeded`;
  - observação: ao atualizar para uma tag antiga que ainda não contém os endpoints `/api/system/update/*`, o polling HTTP pós-restart pode receber 404; a UI deve orientar recarregar/validar por `/health` e a próxima release versionada deve incluir os endpoints novos.
- No Android/Termux físico, validar rollback com `scripts/android_update_printora.sh --rollback --previous-path ~/Printora.previous-update-<timestamp> --db-backup <backup>`.
- No macOS/Linux/Raspberry, validar `scripts/update_printora.sh --plan --tag vX.Y.Z` com:
  - macOS/local sem systemd;
  - Linux/Raspberry com `printora.service` em systemd;
  - Linux sem systemd com `tmux` ou `scripts/run_app.sh`.
- No macOS/Linux/Raspberry, validar `scripts/update_printora.sh --apply --tag vX.Y.Z` em ambiente descartável, confirmando backup de banco, preservação da pasta anterior, checkout da tag, aplicação de SQL, build frontend e restart sem reiniciar Klipper/Moonraker.
- Validar que backend aplica update em ambiente `unix` com confirmação `ATUALIZAR PRINTORA`, tag estável e histórico persistido.
- Validar rollback Unix com `scripts/update_printora.sh --rollback --previous-path <previous> --db-backup <backup>`.
- No Windows, validar `scripts/update_printora_windows.ps1 --Plan --Tag vX.Y.Z` e confirmar JSON parseável sem alteração de arquivos.
- No Windows, validar `scripts/update_printora_windows.ps1 --Apply --Tag vX.Y.Z` em ambiente descartável, conferindo backup de `%LOCALAPPDATA%\Printora\printora.db`, pasta anterior `Printora.previous-update-<timestamp>`, reinstalação backend/frontend, runner Windows reiniciado e `/health`.
- Validar que backend aplica update em ambiente `windows` com confirmação `ATUALIZAR PRINTORA`, tag estável e histórico persistido.
- Validar rollback Windows com `scripts/update_printora_windows.ps1 --Rollback --PreviousPath <previous> --DbBackup <backup>`.
- Confirmar que o updater Windows usa `ExecutionPolicy Bypass` somente no escopo do processo.
- Validar `POST /api/system/update/rollback`:
  - rejeita confirmação diferente de `ROLLBACK PRINTORA`;
  - rejeita paths relativos, raiz, pasta atual do projeto e nomes que não pareçam backup de update;
  - cria run auditável de rollback;
  - marca o run original como `rolled_back` quando a execução síncrona conclui;
  - mantém histórico e steps anteriores.
- Na tela Configurações, confirmar que histórico mostra runs, detalhes, steps, logs sanitizados e botão `Rollback` somente para run `succeeded` com pasta anterior disponível.
- Confirmar que logs de update não expõem credenciais, chaves SSH, tokens ou senhas.
- Confirmar que rollback exige confirmação explícita e registra histórico.

### Endpoint De Versão Do Sistema

- Iniciar o backend local.
- Chamar `GET http://127.0.0.1:8069/api/system/version`.
- Confirmar que a resposta inclui `app_name`, `version`, `data_dir`, `database_path`, `schema_current`, `applied_sql_scripts` e `latest_validation`.
- Confirmar que `applied_sql_scripts` lista apenas nome do script, ordem de execução e data de aplicação.
- Confirmar que `latest_validation.status` está `ok` e `latest_validation.result` contém `ok`.
- Confirmar que a resposta não inclui conteúdo de tabelas operacionais, payloads JSON do banco, segredos, tokens ou credenciais.

### PKG-39 - Autenticação, Usuários E Organização

- Validar que `backend/sql/026_auth_identity.sql` cria usuários, organizações, membros, sessões, desafios 2FA, step-up tokens e credenciais de agente de forma idempotente.
- Validar cadastro com email e senha obrigatórios, e contatos opcionais sem bloquear criação.
- Validar que senha não aparece em texto puro no banco, logs ou resposta de API.
- Validar login com senha correta, rejeição de senha incorreta, logout e sessão expirada/inválida.
- Validar que `GET /api/auth/me` retorna 401 sem bearer token e retorna o usuário autenticado com bearer válido.
- Validar que usuário anônimo no frontend vê apenas login/cadastro, sem sidebar, seletor de impressora ou telas internas.
- Validar que usuário sem organização continua válido para uso individual.
- Validar criação de organização opcional e vínculo de membro por usuário `owner` ou `admin`.
- Validar que impressora privada do usuário não aparece para outro usuário autenticado.
- Validar que impressora vinculada à organização aparece para membro da organização.
- Validar que outro usuário autenticado sem vínculo recebe lista vazia/404 em rotas por impressora e não recebe fallback do Moonraker global.
- Validar que históricos de setup e update do próprio Printora são filtrados por usuário/organização.
- Validar que usuário fora da organização não pode emitir credencial de agente vinculada a ela.
- Validar setup, ativação, login e desativação de 2FA opcional.
- Validar step-up auth para ação destrutiva: usuário com 2FA exige código; usuário sem 2FA exige senha.
- Validar que step-up token é curto e de uso único.
- Validar que timezone do usuário é persistida no perfil e usada na formatação de datas da UI, sem alterar o valor bruto salvo no banco.
- Validar que erros temporários de autenticação/perfil aparecem como toast, não como banner fixo no topo.
- Validar que credencial completa de agente é exibida apenas na criação e armazenada somente por hash.
- Validar que operação destrutiva chamada com sessão autenticada exige `step_up_token`.
- Testes automatizados focados: `cd backend && uv run pytest tests/test_auth.py tests/test_schema_versioning.py tests/test_update_self.py -q`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-40 - Gestão Cloud De Impressoras

- Validar cadastro cloud com nome, URL Moonraker, modelo, localização, tags, observações e organização opcional.
- Validar que organização é opcional: impressora individual fica visível apenas ao dono.
- Validar que impressora vinculada à organização fica visível para membros autorizados e retorna 404 para usuário fora do vínculo.
- Validar `GET /api/printers` e `GET /api/printers/{printer_id}` com status cloud derivado de agente/token: `sem_agente`, `aguardando_pareamento`, `online`, `offline` ou `revogado`.
- Validar que o cadastro cloud não tenta conectar no Moonraker automaticamente; conexão direta continua apenas em teste/discovery/status explícito.
- Validar edição de modelo, tags, localização, observações e organização sem expor credencial SSH.
- Validar UI da tela Impressoras com lista, detalhe resumido, criação/edição, status, tags, último contato e último snapshot.
- Testes automatizados focados: `cd backend && uv run pytest tests/test_auth.py -q`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-41 - Pareamento Seguro Do Agente

- Validar que `backend/sql/029_agent_pairing.sql` cria tokens, agentes e eventos sem armazenar token/credencial em texto puro.
- Validar geração de token por usuário autorizado na impressora e bloqueio para usuário sem acesso.
- Validar que token expirado, revogado ou já usado falha com mensagem clara.
- Validar troca de token por credencial operacional uma única vez.
- Validar que a credencial completa do agente não aparece na listagem após a troca ou rotação.
- Validar heartbeat, snapshot e jobs com credencial ativa.
- Validar que agente revogado não autentica em heartbeat, snapshot ou jobs.
- Validar que rotação invalida credencial antiga e aceita a nova.
- Validar UI da tela Impressoras para gerar/copiar/ocultar token, revogar token, revogar agente e rotacionar credencial.
- Testes automatizados focados: `cd backend && uv run pytest tests/test_agent_pairing.py -q`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-42 - Agente Remoto Base

- Validar `agent/cmd/printora-agent` com comandos `config-sample`, `store-credential`, `doctor`, `once` e `run`.
- Validar que o arquivo de credencial exige permissão restrita e não aceita `0644` em Linux/macOS.
- Validar que o cliente Moonraker usa somente `GET` em endpoints read-only.
- Validar heartbeat autenticado com `Authorization: Bearer <credencial>`.
- Validar snapshot read-only básico com `server/info`, `printer/info`, `print_stats`, temperaturas e Update Manager quando disponível.
- Validar fila local JSONL com limite e retry sem armazenar segredo.
- Validar redaction em logs para `ptr_agent_*`, `ptr_pair_*` e `ptr_sess_*`.
- Validar `doctor` classificando config, permissão, credencial, Moonraker e API.
- Validar cross-build Linux ARM64: `cd agent && GOOS=linux GOARCH=arm64 go build ./cmd/printora-agent`.
- Testes automatizados focados: `cd agent && go test ./...`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-43 - Canal Remoto Agente-Servidor

- Validar que `backend/sql/030_agent_channel.sql` cria `agent_jobs` com correlation ID único e índices por impressora/agente/status.
- Validar que `GET /api/agent/jobs/next` retorna apenas jobs da impressora do agente autenticado.
- Validar que agente de outra impressora não lista, ack, nack, conclui ou falha job alheio.
- Validar WebSocket `/api/agent/ws` com `Authorization: Bearer <credencial>` e fechamento para credencial inválida.
- Validar mensagens v1: `hello`, `heartbeat`, `snapshot`, `job`, `ack`, `nack`, `result`, `error` e `backpressure`.
- Validar rejeição de versão incompatível com erro explícito.
- Validar que resultado repetido de job já concluído permanece idempotente e não duplica execução.
- Validar limite de payload de 64 KB para criação e resultado.
- Validar que logs/eventos não persistem payload completo nem segredos, apenas tipo/status/correlation ID.
- Validar fallback polling repetido do agente quando WebSocket falhar e reconexão contínua com backoff limitado.
- Validar que leituras concorrentes com mesma impressora, agente, tipo e payload reutilizam somente o job ativo, enquanto jobs mutáveis equivalentes continuam independentes.
- Validar que heartbeat não renova job `in_progress`; ausência de resultado deve
  permitir a expiração de qualquer execução órfã mesmo com agente online.
- Testes automatizados focados: `cd backend && uv run pytest tests/test_agent_channel.py tests/test_agent_pairing.py -q` e `cd agent && go test ./...`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-44 - Instalador Online Assistido Do Agente

- Validar que a tela Impressoras gera plano de instalação apenas para usuário com acesso à impressora.
- Validar que o comando contém token curto de pareamento, endpoint público do script, URL publica do binario do agente e URL local do Moonraker.
- Validar que o token curto é consumido uma única vez por `/api/agent/pairing/exchange`.
- Validar que `GET /api/printers/{printer_id}/agent/install-status` mostra pendente sem agente, aguardando heartbeat após pareamento e validado após heartbeat com versão esperada.
- Validar que o instalador notifica `/api/agent/heartbeat` após instalar e iniciar o serviço, sem vazar credencial/token em log.
- Validar que `GET /api/agent/install/linux.sh` entrega o script sem segredo embutido.
- Validar `backend/scripts/install_agent_linux.sh --preflight` em modo seguro, sem vazar `PRINTORA_PAIRING_TOKEN`.
- Validar que uninstall remove serviço/binário e preserva diretórios de configuração/dados/logs.
- Validar frontend build para tela Impressoras com comandos de preflight, install e uninstall, botao de copiar em cada bloco e URL Moonraker padrão `http://127.0.0.1:7125` editável.
- Testes automatizados focados: `cd backend && uv run pytest tests/test_agent_install.py tests/test_agent_pairing.py -q`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-45 - Atualização Automática Do Agente

- Validar manifesto público `GET /api/agent/update/manifest` com versão mínima, recomendada, bloqueios e faixa de protocolo.
- Validar que relatório `POST /api/agent/update/reports` exige credencial operacional do agente.
- Validar que histórico `GET /api/printers/{printer_id}/agent/update-history` respeita ownership/organização.
- Validar que `POST /api/printers/{printer_id}/agents/{agent_id}/update-check` cria job direcionado, respeita ownership/organização e bloqueia agente antigo com orientação manual.
- Validar que agente ignora release sem plataforma compatível ou sem versão superior.
- Validar que versão bloqueada pelo servidor impede aplicação.
- Validar que protocolo incompatível impede aplicação.
- Validar que download sem SHA-256 ou com hash inválido bloqueia a troca do binário.
- Validar que update bem-sucedido faz backup e troca somente o binário do agente.
- Validar que health pós-update falho restaura o binário anterior.
- Validar que restart automático, quando habilitado, reinicia somente o serviço do agente.
- Validar que logs/relatórios não expõem token, credencial ou payload sensível.
- Testes automatizados focados: `cd backend && uv run pytest tests/test_agent_updates.py tests/test_agent_pairing.py -q` e `cd agent && go test ./...`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-46 - Paridade Funcional Remota

- Validar matriz `GET /api/printers/{printer_id}/remote/parity` com executor `agent`.
- Validar estados `implemented`, `cached`, `offline`, `blocked` e `not_supported` quando aplicável.
- Validar bloqueio para usuário sem acesso à impressora.
- Validar criação de jobs remotos somente para funcionalidades read-only ou dry-run.
- Validar que `mutable_operation`, `firmware_build_apply` e payload grande de backup retornam bloqueio explícito.
- Validar jobs read-only via agente: auditoria, snapshot, health, temperaturas, Update Manager, CAN e validação final.
- Validar relatório sanitizado via agente sem token, credencial, senha ou segredo.
- Validar previews remotos de backup, operação e firmware sem executar comando mutável.
- Validar que estado offline usa último job concluído como `cached` quando existir.
- Testes automatizados focados: `cd backend && uv run pytest tests/test_agent_parity.py tests/test_agent_channel.py tests/test_agent_pairing.py -q` e `cd agent && go test ./...`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-47 - Operação Segura Remota

- Validar matriz `GET /api/printers/{printer_id}/remote/operations` com ações, criticidade, risco e rollback.
- Validar que usuário sem acesso à impressora não cria preflight, execução ou cancelamento.
- Validar criação de job `remote_mutation_preflight` com confirmação única, expiração e payload sem segredo.
- Validar que execução não é criada sem preflight remoto concluído com sucesso.
- Validar que confirmação textual incorreta bloqueia execução.
- Validar que preflight com `printing=true` ou `can_execute=false` bloqueia execução.
- Validar que jobs mutáveis pendentes podem ser cancelados e deixam de ser entregues ao agente.
- Validar que o agente executa somente `remote_mutation_preflight` e `remote_mutation_execute`, sem shell genérico.
- Validar que o agente bloqueia execução se o preflight local detectar Moonraker indisponível, impressão em andamento ou estado incompatível.
- Validar UI da tela Impressoras para risco/rollback, preflight, confirmação, execução e cancelamento.
- Testes automatizados focados: `cd backend && uv run pytest tests/test_remote_operations.py tests/test_agent_channel.py tests/test_agent_pairing.py -q` e `cd agent && go test ./...`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-48 - Observabilidade E Suporte Do Agente

- Validar painel `GET /api/printers/{printer_id}/agent/support` com estado online/offline, heartbeat, versão, protocolo, fila e falhas.
- Validar isolamento por usuário/organização em suporte, doctor e pacote de suporte.
- Validar alertas para agente ausente, offline, revogado, desatualizado, protocolo incompatível, fila acumulada e falha recorrente.
- Validar doctor remoto `POST /api/printers/{printer_id}/agent/support/doctor` criando job `remote_doctor`.
- Validar agente executando `remote_doctor` sem vazar credencial, token ou segredo no resultado.
- Validar pacote `GET /api/printers/{printer_id}/agent/support/bundle` com payloads, resultados, erros e log tail sanitizados.
- Validar política de retenção documentada de 180 dias para eventos/jobs de agente.
- Validar UI da tela Impressoras para saúde do agente, alertas, doctor remoto e pacote de suporte.
- Testes automatizados focados: `cd backend && uv run pytest tests/test_agent_support.py tests/test_agent_pairing.py tests/test_agent_channel.py -q` e `cd agent && go test ./...`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-69 - Armazenamento, Cotas, Retenção E Custos De Arquivos

- Validar que upload da biblioteca consulta cota antes de gravar arquivo definitivo ou quarentena.
- Validar que falha de cota não deixa objeto local órfão em `library_uploads/quarantine`.
- Validar relatório `GET /api/social/me/library/storage` com política, uso, cota restante, custo estimado, plano de retenção e plano futuro de object storage.
- Validar revisão `POST /api/social/me/library/storage/retention-reviews` como `dry_run`, auditável e sem exclusão automática.
- Validar que arquivo referenciado por versão atual fica bloqueado no plano de retenção.
- Validar que o painel de armazenamento fica em `Projetos de impressão > Meus projetos`; comunidade mostra apenas projetos compartilhados e não contém upload/gestão principal de arquivo.
- Testes automatizados focados: `cd backend && uv run --extra dev pytest ../backend/tests/test_social_catalog.py -k 'library_storage or library_upload_quarantine' -q` e `cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-70 - Ponte Controlada Com Engine De Fatiamento

- Validar que `GET /api/slicing/engine` retorna bloqueio claro quando OrcaSlicer/PrusaSlicer não estiver configurado.
- Validar que o detector aceita binário configurado por `PRINTORA_SLICER_ENGINE_PATH` e lê versão sem vazar home local, token ou segredo.
- Validar que `POST /api/slicing/dry-run` não executa fatiamento real, não cria G-code e retorna contrato de entrada/saída com comando previsto.
- Validar que payload com referência sensível é rejeitado antes de registrar dry-run.
- Validar que checks de engine e dry-runs são registrados em tabelas auditáveis.
- Validar UI de Administração com painel read-only, estado bloqueado/pronto, botão com ícone e texto sem identificadores internos.
- Testes automatizados focados: `cd backend && uv run --extra dev pytest ../backend/tests/test_slicing.py -q`.
- Validação frontend focada: `npm --prefix frontend run build`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-71 - Pipeline De Fatiamento Por Perfil E Impressora

- Validação histórica/legada: criação de job com usuário, impressora, perfil opcional, item/modelo legado, dimensões e qualidade. Após PKG-77 a PKG-81, criação diária de job deve partir de projeto e snapshot imutável.
- Validar bloqueio de item/modelo legado ou projeto maior que o volume útil catalogado da impressora.
- Validar bloqueio de perfil incompatível com a variação catalogada da impressora.
- Validar execução com engine ausente gerando falha acionável e log rastreado, sem G-code falso.
- Validar execução com engine configurada em worker isolado, registrando artefatos `gcode`, `log` e `metadata`.
- Validar cancelamento de job planejado ou em execução.
- Validar UI de Administração como diagnóstico/fallback responsivo para jobs, estados, erros, artefatos e ações técnicas. Após PKG-77 a PKG-81, formulário principal de criação fica em `Projetos de impressão`.
- Testes automatizados focados: `cd backend && uv run --extra dev pytest ../backend/tests/test_slicing.py ../backend/tests/test_slicing_pipeline.py -q`.
- Validação de schema/update: `cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q`.
- Validação frontend focada: `npm --prefix frontend run build`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-72 - Preflight De Impressão A Partir De Arquivo Fatiado

- Validar parser seguro de G-code usando fixture controlada em `backend/tests/fixtures/gcode/preflight_abs_cube.gcode`.
- Validar extração de dimensões máximas, temperaturas, filamento, nozzle, tempo estimado e checksum do artefato.
- Validar bloqueio quando job não está concluído, G-code pertence a outra impressora ou artefato G-code não existe.
- Validar bloqueio de temperatura perigosa e G-code sem comandos imprimíveis.
- Validar warnings para divergência entre G-code e perfil de material.
- Validar criação de job remoto `remote_gcode_preflight` quando há agente ativo.
- Validar refresh para aprovado quando o agente retorna `can_execute=true`.
- Validar bloqueio quando o agente retorna impressão em andamento ou blockers.
- Validar UI de Administração com ação `Preflight`, blockers, warnings, metadados resumidos e checklist.
- Testes automatizados focados: `cd backend && uv run --extra dev pytest ../backend/tests/test_print_preflight.py ../backend/tests/test_slicing_pipeline.py -q`.
- Validação de schema/update: `cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q`.
- Validação frontend focada: `npm --prefix frontend run build`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-73 - Envio Seguro De G-code Para Impressora

- Validar que envio exige preflight aprovado e recente.
- Validar bloqueio quando o preflight expirou, não pertence ao job/impressora ou o checksum do G-code mudou.
- Validar `save_only` criando entrega auditada sem iniciar impressão.
- Validar `save_and_print` exigindo confirmação textual correta ou step-up válido.
- Validar que o frontend não recebe conteudo bruto do G-code no resultado da entrega.
- Validar rollback remoto apenas para arquivo salvo sem impressão iniciada.
- Validar agente Go com upload multipart para `/server/files/upload` e remoção por `/server/files/gcodes/<arquivo>`.
- Validar UI de Administração com status de entrega, confirmação inline, salvar, iniciar e remover arquivo.
- Testes automatizados focados: `cd backend && uv run --extra dev pytest ../backend/tests/test_print_delivery.py ../backend/tests/test_print_preflight.py -q`.
- Validação do agente: `cd agent && go test ./...`.
- Validação frontend focada: `npm --prefix frontend run build`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-78 - Meus Projetos, Upload E Links Externos

- Validar criação de projeto pessoal sem comunidade.
- Validar upload multi-arquivo STL/3MF/ZIP com arquivo principal e peça opcional.
- Validar que arquivo rejeitado/falho bloqueia só o arquivo afetado e não torna o projeto inteiro ingerenciável quando há arquivo válido.
- Validar link externo como referência sem arquivo local e bloqueado para fatiamento/envio.
- Validar listagem `Meus projetos` com projetos próprios e salvos por referência.
- Validar painel de armazenamento pessoal com uso/cota/quantidade de arquivos.
- Validar snapshot imutável criado em criação, edição, upload e link externo.
- Validar arquivamento lógico sem apagar arquivos.
- Validar responsividade da tela `Projetos de impressão` em desktop e mobile.
- Testes automatizados focados: `cd backend && uv run --extra dev pytest ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q`.
- Validação frontend focada: `npm --prefix frontend run build`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-79 - Publicação, Venda E Vitrine De Projetos

- Validar que projeto privado, rascunho, em revisão ou rejeitado não aparece em busca pública, comunidade ou detalhe público anônimo.
- Validar que projeto gratuito público só entra na vitrine quando a publicação estiver aprovada.
- Validar premium com preço preparado entrando em revisão e ficando oculto até aprovação administrativa.
- Validar patrocinado exigindo transparência explícita antes de revisão/aprovação.
- Validar que compartilhamento em comunidade não muda visibilidade, publicação ou classificação comercial.
- Validar que pagamento real não aparece como ativo nem é simulado.
- Validar UI `Publicação e vitrine` em desktop/mobile com badges de premium/patrocinado.
- Testes automatizados focados: `cd backend && uv run --extra dev pytest ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q`.
- Validação frontend focada: `npm --prefix frontend run build`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-80 - Fatiamento A Partir De Projeto Salvo

- Validar criação de job a partir de `Projetos de impressão > Meus projetos`, sem entrar em Administração.
- Validar que o job aponta para projeto, versão/snapshot, arquivos selecionados, usuário, impressora, qualidade e perfil/material quando informado.
- Validar que alteração posterior do projeto não altera snapshot do job nem seleção de arquivos gravada.
- Validar que link externo sem arquivo local validado fica desabilitado na UI e bloqueado no backend.
- Validar que seleção com arquivo inválido ou não fatiável bloqueia só aquele arquivo, não o projeto inteiro quando há arquivo válido.
- Validar incompatibilidade de impressora/perfil/dimensões antes da criação do job.
- Validar engine ausente como erro acionável apontando Administração para configuração.
- Validar lista de jobs no detalhe do projeto, estado, snapshot e ação de preflight quando o job estiver completo.
- Validar responsividade do painel `Fatiamento` em desktop/mobile sem overflow horizontal.
- Testes automatizados focados: `cd backend && uv run --extra dev pytest ../backend/tests/test_slicing_pipeline.py ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q`.
- Validação frontend focada: `npm --prefix frontend run build`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-81 - Envio Para Impressora E Histórico Por Projeto

- Validar que preflight aparece no detalhe do projeto e fica associado ao job/snapshot do projeto.
- Validar que `Salvar G-code` e `Enviar` ficam no fluxo de `Projetos de impressão > Meus projetos`, não como ação principal de Administração ou Comunidade.
- Validar que `Enviar` só habilita com confirmação textual esperada ou autorização reforçada quando aplicável.
- Validar que G-code não é salvo/enviado sem preflight aprovado quando a política exigir.
- Validar status de entrega, arquivo remoto e rollback apenas quando o modo/status for seguro.
- Validar histórico filtrado no projeto com status, qualidade, perfil/material, resultado, falha e feedback.
- Validar feedback privado/público e foto HTTPS opcional.
- Validar que histórico público sanitizado não expõe impressora privada, agente, Moonraker, token, IP, path, organização ou permissão.
- Validar que sinais públicos apontam ao projeto central e não a cópia por comunidade.
- Validar responsividade do fluxo de envio/histórico em desktop/mobile sem overflow horizontal.
- Testes automatizados focados: `cd backend && uv run --extra dev pytest ../backend/tests/test_print_history.py ../backend/tests/test_print_delivery.py ../backend/tests/test_slicing_pipeline.py ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q`.
- Validação frontend focada: `npm --prefix frontend run build`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-132 - Fluxo ponta a ponta de impressão

- Validar seleção parcial e múltipla com quantidade de 1 a 100 por arquivo.
- Validar snapshot imutável de projeto, versão, arquivo/checksum, quantidade,
  impressora, spool e revisão executável do perfil.
- Validar que spool de outro usuário/inativo bloqueia e mudança de revisão gera
  aviso no preflight.
- Validar que job de projeto sem aprovação visual não passa no preflight.
- Validar que aprovação pertence ao checksum e alteração do G-code exige nova
  revisão.
- Validar isolamento por owner no download privado do G-code e cabeçalhos sem
  cache.
- Validar preflight local/remoto, confirmação, upload, retry idempotente,
  unicidade de entrega, histórico canônico, retomada e rollback seguro.
- Validar que estado/arquivo exibido pertence ao job e impressora selecionados.
- Validar resultado, telemetria sanitizada, consumo vinculado e feedback.
- Validar `Reimprimir igual` preservando snapshot e perfil, criando novo job e
  exigindo nova aprovação/preflight/confirmação.
- Validar desktop 1440x900 e mobile 390x844, teclado, foco, mensagens simples e
  ausência de overflow horizontal.
- Smoke físico seguro: usar peça/material controlados, operador presente,
  confirmar impressora ociosa e observar primeira camada; não automatizar a
  confirmação humana.
- Focado: `backend/.venv/bin/python -m pytest -q backend/tests/test_slicing_pipeline.py backend/tests/test_print_preflight.py backend/tests/test_print_delivery.py backend/tests/test_print_history.py` e `npm --prefix frontend run build`.
- Fechamento: `./check.sh` integral.

### PKG-82 - Arquivos G-code Por Impressora

- Validar contrato backend/agente para listagem de `/gcodes` com arquivos, diretórios, tamanhos, datas e metadados quando o Moonraker retornar.
- Validar que a listagem não baixa o G-code completo de todos os arquivos.
- Validar tabela da aba `Arquivos G-code` com busca, ordenação, filtros, refresh, seleção e espaço livre.
- Validar colunas de altura, camada, bico, filamento, uso, tempo estimado, última duração, slicer, temperaturas e último início/fim.
- Validar thumbnails sem distorção e fallback quando ausentes.
- Validar estados online, offline, sem permissão, agente antigo e timeout sem dados antigos apresentados como atuais.
- Validar responsividade em desktop grande, notebook, mobile, tema claro, tema escuro e navegador embutido.
- Testes automatizados focados: `cd backend && uv run --extra dev pytest ../backend/tests/test_gcode_files.py ../backend/tests/test_operation.py -q`; `cd agent && go test ./...`.
- Validação frontend focada: `npm --prefix frontend run build`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-83 - Detalhe E Ações De Arquivo G-code

- Validar que clique em arquivo abre modal/drawer com thumbnail, metadados, histórico e ações.
- Validar ações read-only: baixar, copiar caminho, abrir prévia e ver histórico.
- Validar ações mutáveis protegidas: imprimir, renomear, mover, duplicar e excluir.
- Validar que excluir, mover, renomear, sobrescrever e iniciar impressão exigem confirmação explícita.
- Validar que impressão ativa bloqueia ações incompatíveis.
- Validar preflight antes de impressão quando a política exigir.
- Validar auditoria segura sem token, IP, path sensível ou G-code bruto em logs persistidos.
- Validar falhas de Moonraker/agente com mensagem acionável e sem ação parcialmente aplicada.
- Testes automatizados focados: backend de arquivos/ações e permissões do contrato novo.
- Validação frontend focada: `npm --prefix frontend run build`.
- Validação focada executada em 2026-07-20: `cd backend && uv run --extra dev pytest ../backend/tests/test_gcode_files.py ../backend/tests/test_operation.py ../backend/tests/test_agent_install.py ../backend/tests/test_agent_updates.py ../backend/tests/test_agent_support.py -q`; `cd agent && go test ./...`; `npm --prefix frontend run build`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-84 - Preview E Simulação De G-code Reutilizáveis

- Validar preview com G-codes reais e fixtures controladas, incluindo arquivo completo, até camada selecionada, camada atual e progresso por `file_position`.
- Validar que a cena não inventa teto, parede, fechamento ou volume que não exista no G-code.
- Validar peça 100% renderizada completa.
- Validar camada atual com material já impresso abaixo e destaque visual sem esconder geometria real.
- Validar classificação de linhas quando disponível: perímetro, superfície, preenchimento, suporte, saia/brim, deslocamento e retração.
- Validar navegação com mouse/touch, zoom, pan, barras de deslocamento e navegador 3D sem sobreposição.
- Validar tema claro/escuro com fundo, grade, peça, linhas e controles coerentes.
- Validar limites de performance em arquivo grande sem travar UI nem aumentar polling do agente.
- Validar nome Unicode cujo cabeçalho chegue alterado: o backend deve usar o
  nome canônico apenas quando existir job de cache ativo e autenticado com a
  mesma chave; chave sem correspondência deve continuar recusada.
- Validar recuperação automática após falha transitória `409`, `5xx` ou `524`,
  com espera progressiva, cancelamento ao desmontar a tela e coalescência de
  jobs equivalentes; erro permanente como `404` não deve ser repetido.
- Testes automatizados focados: parser/normalizador de G-code e fixtures de renderização quando aplicável.
- Validação frontend focada: `npm --prefix frontend run build`.
- Validação focada executada em 2026-07-20: `npm --prefix frontend run test:gcode-preview`; `npm --prefix frontend run build`. Não foi executada ação live ou mutável na impressora porque ela estava imprimindo.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-85 - Operação Ociosa Enxuta E Ponte Para Arquivos

- Validar estados `printing`, `paused`, `standby`, `offline`, `sem leitura` e `erro`.
- Validar que `Operação` ociosa não mostra preview vazio, progresso antigo, fatos nulos ou tabela completa de arquivos.
- Validar estado compacto com último trabalho confiável, poucos arquivos recentes e CTA para `Arquivos G-code`.
- Validar que `Temperaturas`, `Machine`, `Ações protegidas`, `Miscellaneous`, sistema e CAN não criam buracos por causa do estado da impressão.
- Validar que operação ao vivo continua priorizando preview, temperaturas, limites e ações seguras.
- Validar mensagens de timeout/agente offline sem erro bruto de infraestrutura.
- Validar layout em monitor grande, notebook, mobile, tema claro, tema escuro e navegador embutido.
- Validação frontend focada: `npm --prefix frontend run build`.
- Validação focada executada em 2026-07-20: `npm --prefix frontend run build`. Não foi executada ação live ou mutável na impressora porque ela estava imprimindo.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

## Validação Da Evolução Arquitetural

Gates transversais para todos os pacotes:

- testar autorização backend e isolamento owner/organização/tenant em leitura,
  escrita, busca, cache, objeto, evento, exportação e suporte;
- testar sessão/token, revogação, expiração, replay, CSRF/CORS e step-up aplicáveis;
- testar injeção, mass assignment, paginação/limite, enumeração e rate limit;
- testar SSRF/DNS rebinding e uploads com traversal, archive/parser bomb,
  content-type falso e conteúdo hostil;
- executar scan de segredo/dependência, gerar SBOM e verificar checksum/assinatura do artefato;
- validar que log, trace, evento, backup e pacote de suporte não contêm segredo/PAN/dado indevido;
- executar revisão independente nos fluxos financeiros, físicos, sensíveis e automatizados.

### PKG-86 - Qualificação Do Servidor E Publicação Sem Indisponibilidade

- validar privilégios, firewall, portas, NTP, disco, I/O, RAM, CPU, quotas e backup externo;
- provar que blue/green usam release, frontend, venv, lockfile e unit independentes;
- falhar readiness e provar que candidato não recebe tráfego;
- executar `nginx -t`, troca atômica, drain e rollback sob carga;
- testar compatibilidade N/N-1 de schema, evento e contrato;
- testar reconnect com jitter, ack e deduplicação dos agentes;
- matar candidato/ativo e provar continuidade sem restauração de dados;
- testar disco/log/WAL próximo da quota e alerta antes de indisponibilidade;
- fechamento: carga/soak, deploy controlado, rollback e smoke público P0/P1.

Evidência de fechamento em 2026-07-22:

- suíte completa, scans de dependência/segredo e SBOM passaram no workflow;
- dois ciclos blue/green e rollback passaram com zero request falho sob carga;
- candidato sem readiness não recebeu tráfego e o ativo morto recuperou pelo N-1;
- escrita posterior ao deploy foi preservada e não houve duplicidade de ACK/job;
- backup externo criptografado restaurou 4,04 GiB em isolamento com
  `integrity=ok`;
- smoke público de `/health` e `/ready` passou após a remoção do runtime legado;
- evidência operacional detalhada em
  `docs/audits/CLOUD_BLUE_GREEN_READINESS_2026-07-22.md`.

### PKG-87 - Monólito Modular, Contratos E Fronteiras

- congelar contratos HTTP/WebSocket/evento dos fluxos P0/P1;
- validar ausência de ciclo e imports proibidos entre domínio, aplicação, API e infraestrutura;
- validar isolamento entre persistence adapters cloud e local;
- validar page/form/state/client sem routing, regra e persistência misturados;
- executar testes de caracterização antes/depois de cada extração;
- impedir duas implementações canônicas do mesmo caso de uso;
- verificar limites de arquivo/função e remoção de bridges antigas;
- fechamento: suíte completa, contratos N/N-1 e smoke publicado.

Evidência de fechamento em 2026-07-22:

- inventário reproduzível: 133 módulos, 322 endpoints, 337 contratos e 100
  tabelas, todos com owner, sem ciclo de import;
- snapshots OpenAPI/realtime v1 permaneceram idênticos após as extrações;
- contratos e ports puros não importam FastAPI nem drivers de persistência;
- application service de jobs foi testado isoladamente de HTTP e banco;
- layering React estrito passou e ficou habilitado por padrão;
- regressões direcionadas de identidade, comunidade, agentes, backup e frontend
  passaram; evidência em `docs/audits/MODULAR_ARCHITECTURE_2026-07-22.md`.

### PKG-88 - PostgreSQL Cloud Sem Perda De Dados

- comparar contagem, min/max, sequences, checksum por lote, FK, órfãos e consultas semânticas;
- testar tipos SQLite/PostgreSQL: data/hora, booleano, JSON, decimal, null e collation;
- testar snapshot mais alterações concorrentes, watermark e outbox SQLite atômica;
- executar leitura sombra/canário e bloquear divergência não explicada;
- testar cutover sob escrita e rollback para release PostgreSQL-compatible;
- provar que nenhuma escrita pós-cutover depende de snapshot SQLite;
- restaurar backup/WAL PostgreSQL em ambiente isolado;
- escanear zero SQLite no perfil cloud e testar SQLite somente no perfil local;
- fechamento: integridade total, carga, restore, suíte cloud/local e smoke.

Evidência de fechamento em 2026-07-22:

- dois relatórios completos fecharam 100/100 tabelas e 187/187 FKs, nos
  watermarks `8167` e `10067`, sem checksum divergente ou sequence insegura;
- o cutover alcançou o watermark final `11494` sob lock da origem;
- backup físico/lógico/WAL restaurou 101 tabelas e 74 versões em cluster isolado,
  fora de recovery e com zero FK inválida;
- canário, health, readiness, catálogo, versão, social, autenticação e manifesto
  passaram no host real;
- deploy e rollback PostgreSQL preservaram os eventos `282037` a `282228`, com
  `data_restored=false`;
- gate PostgreSQL-only, modo local, suíte completa e frontend ficaram
  bloqueantes; detalhes em
  `docs/audits/POSTGRESQL_CLOUD_TRANSITION_2026-07-22.md`.

### PKG-89 - Outbox, Workers, Redis E Realtime Distribuído

- testar atomicidade negócio/outbox, inbox e schemas versionados;
- testar duplicidade, ordenação, timeout, backoff, dead-letter e replay;
- matar worker, expirar lease e validar um único efeito efetivo;
- reiniciar/esvaziar Redis e validar recomposição/degradação sem perda canônica;
- testar WebSocket em múltiplas instâncias, reconnect, ack e retomada do agente;
- saturar filas e validar backpressure/quotas sem derrubar P0/P1;
- drenar workers N/N-1 antes de contrair schema/evento;
- escanear zero registry/fila autoritativa em memória;
- fechamento: carga/soak, falha controlada, suíte completa e smoke.

Evidência de fechamento em 2026-07-22:

- testes focados cobrem atomicidade negócio/outbox, inbox, ordenação,
  deduplicação, lease expirado, completion token, retry, dead-letter e replay;
- idempotência HTTP reproduz resposta e rejeita chave reutilizada com payload
  divergente;
- fencing de sessão entre duas instâncias mantém somente um owner canônico e
  persiste último ACK;
- Redis ausente degrada sem bloquear negócio; cache, rate limit, presença e
  pub/sub foram exercitados também contra processo Redis efêmero real;
- carga SQLite controlada concluiu 500/500 jobs, oito consumidores, zero
  duplicidade e 170,38 jobs/s; PostgreSQL remoto concluiu outros 500/500, zero
  duplicidade, 10,29 jobs/s e p95 de claim em 484,162 ms;
- saturação acima da quota foi recusada, lease expirado retomou na tentativa 2 e
  rejeitou completion token antigo;
- restart de Redis preservou contagens PostgreSQL e manteve apps/workers ativos;
- rollback N-1 e forward-deploy drenaram/reiniciaram quatro classes sem restore;
- smoke público: 500 requisições, zero erro e p95 de 953,159 ms.

### PKG-90 - Objetos, Quarentena E Busca Reconstruível

- testar upload streaming, limite, interrupção, checksum, quarentena e promoção atômica;
- testar path traversal, content type, arquivo hostil, URL expirada e acesso cruzado;
- reconciliar manifesto/metadado/conteúdo e detectar órfãos nos dois sentidos;
- restaurar metadados e objetos juntos a partir da cópia externa;
- testar índice com permissão, tenant, bloqueio, remoção e moderação;
- apagar/reconstruir índice e comparar cobertura/relevância controlada;
- falhar storage/busca e validar degradação dos fluxos não críticos;
- escanear zero path/índice/consulta cloud aposentado;
- fechamento: carga, segurança, restore, suíte completa e smoke.

### PKG-91 - Núcleo Financeiro, Pagamentos E Pedidos

- testar partidas dobradas, inteiro/moeda/arredondamento e reconciliação;
- testar webhook assinado/inválido, repetido, fora de ordem, atrasado e replay;
- testar timeout e concorrência entre pedido, provedor e ledger;
- testar captura, cancelamento, reembolso, disputa, chargeback e repasse;
- testar limites de reembolso/repasse, saldo negativo e comandos idempotentes;
- provar ausência de PAN/CVV em request persistido, log, trace e backup;
- testar segregação de função, step-up, auditoria, LGPD e retenção;
- validar sandbox/reconciliação real antes de dinheiro real;
- fechamento: revisão independente de segurança, carga, restore e smoke ponta a ponta.

Comando de fechamento:

```bash
cd backend && uv run --extra dev pytest -q tests/test_finance_*.py
scripts/validate-finance-safety.sh
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 CHECK_STRICT_SECRETS=1 CHECK_STRICT_RUNTIME_NAMES=1 ./check.sh
```

Evidência remota deve usar somente sandbox e dados sintéticos: criar pedido de
projeto de teste, gerar checkout hospedado, capturar, reconciliar, reembolsar e
confirmar ledger balanceado. Não marcar fiscal/jurídico como aprovado sem revisão
humana e não habilitar dinheiro real.

No release ativo, executar `scripts/cloud/probe-finance-sandbox.py` com o ambiente
da aplicação. A prova preserva os registros sintéticos para auditoria, valida
replay, reembolso, reconciliação, segregação do repasse, saldo e ausência de
coluna para cartão/payload bruto. Ela não remove nem altera dados anteriores.

### PKG-92 - Fabricação, Qualidade, Logística E Cadeia De Custódia

- testar snapshot/licença da ordem, aceite e estados formais;
- executar `pytest -q tests/test_manufacturing_workflow.py`: cobre snapshot e
  replay da cotação, reserva atômica, salto inválido, segregação da qualidade,
  expedição somente aprovada, tracking repetido, entrega e recall;
- confirmar que endereço não aparece no overview/log e que token/payload do
  transportador são reduzidos a ciphertext/hash/digest;
- em smoke Cloud usar somente ordem sintética; não conectar nem comandar
  impressora, agente, Moonraker, Klipper ou MCU.
- testar concorrência de capacidade/material e idempotência;
- impedir expedição sem qualidade aprovada;
- testar retrabalho, cancelamento, falha, incidente e recall;
- testar webhook de tracking repetido/fora de ordem;
- validar privacidade de endereço/documento/evidência e retenção;
- testar compensação financeira sem escrita direta no ledger;
- fechamento: segurança física, carga, recuperação e smoke ponta a ponta.

### PKG-93 - Escala, Resiliência, Backup E Recuperação

- distribuir requests/WebSockets entre instâncias e matar uma durante carga;
- saturar pools e validar backpressure, circuit breaker, timeout e bulkhead;
- restaurar PostgreSQL, objetos, configuração e secrets references em isolamento;
- simular perda de processo, banco, disco, configuração e host;
- medir RPO/RTO real usando backup/WAL externo e reconciliar;
- provar que chave/credencial de restore sobrevive à perda do host;
- executar carga de pico, soak e caos de processo;
- fechamento: capacidade residual, restore, suíte completa e smoke P0/P1.

### PKG-94 - Analytics, Moderação Multilíngue E Inteligência Isolada

- executar `pytest -q tests/test_data_intelligence.py`: cobre sanitização,
  finalidade, evento divergente, deduplicação, lineage, replay idempotente,
  anonimização sem delete, PT/EN/ES, revisão humana, recurso, modelo, canário,
  drift, kill switch, fallback determinístico, busca geométrica e quotas;
- executar `scripts/cloud/probe-analytics-intelligence.py` com dados sintéticos,
  serviço isolado controlado e monitoramento simultâneo de `/ready`;
- validar role impedindo analytics/ML de escrever no OLTP;
- testar replay/deduplicação, lineage, consentimento, remoção e anonimização;
- revisar moderação multilíngue, falsos positivos, recurso e decisão humana;
- validar dataset/licença, modelo offline, bias, canário, drift e rollback;
- acionar kill switch e provar fallback determinístico;
- saturar analytics/ML e provar quotas sem afetar P0/P1;
- testar retenção/limpeza de dataset e modelo temporário;
- fechamento: privacidade, segurança, carga, suíte completa e smoke.

O probe remoto preserva a evidência sintética, não executa `DELETE`, não acessa
impressora/agente/Moonraker/Klipper/MCU e restaura o estado anterior do modelo
após exercitar o kill switch. A retenção é comprovada inicialmente por preview;
remoção física exige confirmação separada e não faz parte do pacote.

### PKG-95 - Consolidação E Erradicação Legada

- executar scanner por perfil em código, imports, lockfiles, env, SQL, filesystem, units, workflows, docs e testes;
- exigir zero flag/bridge/adapter temporário; adapters locais válidos ficam restritos ao perfil local;
- gerar SBOM, revisar dependências/segredos/roles e remover serviço sem owner;
- reconciliar dados, objetos, jobs, auditorias, índices e retenção;
- executar restore integral, deploy/rollback sob carga e provar preservação de escrita;
- repetir carga, soak, caos, segurança e smoke público;
- revisar contratos/consumidores, arquivos grandes, SOLID e documentação final;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` deve passar antes do commit exclusivo.

## Validação Da Confiança Operacional Pós-Arquitetura

Os sete gates obrigatórios dos pacotes `PKG-96` a `PKG-99` são: Node suportado,
cobertura mínima, E2E em navegador, hardware/agente real, soak prolongado,
fuzzing/mutation testing e pentest independente. Um relatório deve separar
claramente teste local, CI, ambiente isolado, produção read-only, hardware real
e ação mutável autorizada.

### PKG-96 - Agente 0.1.34 E Paridade Real

- comparar diff do agente desde o artefato `0.1.33`;
- validar que versão, manifesto, binário, UI e documentação informam `0.1.34`;
- construir duas vezes por plataforma e comparar conforme política de build reproduzível;
- gerar SBOM, checksum, assinatura e verificar antes de publicar/instalar;
- rejeitar manifesto com plataforma sem URL, hash, assinatura ou binário testado;
- executar `go test ./...`, race detector nos módulos concorrentes e scans;
- testar matriz `0.1.33`/`0.1.34` versus protocolo atual/N-1;
- testar reconnect, jitter, polling, recebimento persistido antes do ACK,
  fencing, deduplicação, retomada e sincronização durável do journal;
- testar que impressão, pausa ou Moonraker indisponível bloqueiam o update antes
  do download/troca do binário;
- instalar canário real somente com impressora ociosa;
- provar pelo navegador que `Instalar canário` seleciona exatamente `0.1.34` e
  que `Reverter para` seleciona exatamente a recomendada N-1, sem SSH;
- no script remoto controlado, validar preflight Moonraker, SHA-256, Ed25519,
  backup do binário e restart exclusivo de `printora-agent`;
- validar heartbeat/snapshot/job e isolamento da impressora;
- executar rollback real para `0.1.33` e reaplicar `0.1.34`;
- comprovar que Klipper/Moonraker/MCU/host não reiniciaram;
- confirmar versão instalada pela UI e backend;
- executar gate completo, publicar manifesto e smoke público.

Não avançar se:

- o mesmo número de versão possuir hashes/conteúdos diferentes;
- plataforma anunciada não tiver artefato funcional;
- agente antigo perder compatibilidade durante a janela;
- update/rollback afetar impressão ou outro serviço;
- canário apresentar duplicidade, perda de job ou reconnect em loop.

### PKG-97 - Node, Cobertura, E2E, Fuzzing, Mutation E Pentest

- executar `scripts/run-coverage-gate.sh`; o comando coleta Python/Go/frontend,
  valida mínimo global/crítico e compara com `quality/coverage-baseline.json`;
- preservar os relatórios em `.artifacts/coverage` e no artefato CI por 30 dias;
- executar teste negativo com Node incompatível e exigir falha antes do build;
- executar local/CI com a mesma versão Node suportada e instalação limpa;
- falhar em warning classificado como crítico e em orçamento de bundle excedido;
- coletar cobertura Python, Go e frontend por arquivo/domínio/criticidade;
- ativar limiar global, limiar P0 e não regressão em `PATHS.toml`;
- impedir exclusão artificial de código crítico para elevar percentual;
- executar E2E em navegador real para anônimo, usuário e papéis privilegiados;
- validar que autorização administrativa vem do contrato autenticado, que
  identidade configurada não pode ser reivindicada por cadastro público e que o
  provisionador exige arquivo de senha `0600`;
- validar preparação idempotente do handoff com sete contas sintéticas, duas
  organizações, segregação financeira/produção, bloqueio do usuário comum,
  manifesto sem segredo e rejeição incondicional de produção;
- executar dois usuários/organizações e provar isolamento ponta a ponta;
- validar desktop/mobile, tema claro/escuro, teclado e acessibilidade;
- no logout, confirmar a resposta do backend e impedir que uma leitura de sessão
  concorrente restaure o usuário após a revogação;
- injetar offline, timeout, 429, 5xx, reconnect e dependência degradada;
- executar property-based testing/fuzzing em parsers, uploads, URL/SSRF,
  webhooks, idempotência, paginação, G-code e protocolos;
- guardar corpus/seed mínimo reproduzível sem dado sensível;
- executar mutation testing nas regras P0/P1;
- repetir suíte crítica para detectar flakiness;
- executar pentest independente com escopo autorizado, salvo dispensa explícita
  do owner registrada em decisão e no relatório final;
- quando executado, corrigir e retestar todo achado crítico/alto;
- registrar médios com owner, prazo, mitigação e risco aceito; quando dispensado,
  registrar como não testado o escopo que somente o pentest cobriria;
- executar scans de segredo/dependência/SBOM e gate completo.

Comandos bloqueantes implantados:

```bash
scripts/run-e2e-gate.sh
scripts/run-property-fuzz-gate.sh
scripts/run-mutation-gate.sh
scripts/run-pkg97-test-gates.sh
```

Property/fuzz executa perfil determinístico e perfil aleatório com seed
reproduzível. Mutation mede somente mutantes efetivamente testados no score,
publica `stats.json` e a enumeração completa em `survivors.txt`; sobreviventes
não podem desaparecer por filtro e devem receber teste, justificativa ou backlog.

Não avançar se:

- Node incompatível terminar com sucesso;
- cobertura estiver desativada, zerada ou regredir;
- E2E P0 estiver ausente, flaky ou depender de dado produtivo instável;
- fuzz encontrar crash/hang/leak/traversal/SSRF não resolvido;
- mutation score crítico ficar abaixo do limiar;
- pentest deixar crítico/alto aberto ou ser dispensado sem risco residual e
  escopo não testado explícitos;
- relatório contiver segredo, PAN/CVV ou dado pessoal real.

### PKG-98 - Hardware Real E Soak De 72 Horas

- documentar impressora, agente, versões, arquivo, material e estado inicial;
- capturar baseline do host, Raspberry, agente, Moonraker, Klipper e browser;
- validar impressão ativa somente read-only;
- validar ociosa/pausada/concluída/cancelada/offline/timeout;
- com a impressora ociosa, testar ações protegidas e confirmações;
- testar restart/update/rollback somente do agente;
- desconectar/reconectar rede e Moonraker de forma controlada;
- validar operação, arquivos, preview, preflight, entrega e histórico reais;
- comprovar ausência de duplicidade em comando/job/upload/histórico;
- validar desktop/mobile, temas e acessibilidade no fluxo real;
- executar soak inicial de 24 horas;
- monitorar erro, p95/p99, CPU, RSS, FD, goroutines, conexões, filas, Redis,
  PostgreSQL, objetos, busca, disco, WAL e logs;
- validar carga representativa com um único pool/keep-alive durante toda a
  janela, incluindo reutilização entre lotes, e manter o modo de conexão fria
  separado para diagnóstico de DNS/TCP/TLS;
- simular fechamento remoto de conexão keep-alive no GET idempotente de health,
  comprovar uma única reconexão, erro final zero e retry sanitizado na evidência;
  a segunda falha consecutiva deve permanecer fail-closed;
- manter o event loop responsivo enquanto autenticação e polling de jobs
  executam I/O síncrono de repositório; a regressão deve bloquear o repositório
  de forma controlada e comprovar que outra coroutine continua avançando;
- rerenderizar Arquivos G-code com nova referência de callback de UI sem
  disparar outra listagem remota enquanto impressora e filtros não mudarem;
- consolidar a evidência JSONL com falha fechada para duração mínima, zero erro,
  SLO por lote, observações aprovadas e tendências sanitizadas sem fingerprint,
  URL, token, IP, path ou payload;
- corrigir qualquer regressão e reiniciar a janela afetada;
- executar soak final contínuo de 72 horas;
- executar gate completo e smoke público após o soak.

Não avançar se:

- ação mutável for executada durante impressão sem autorização;
- Klipper/Moonraker/MCU reiniciarem por efeito do teste do agente;
- houver perda/duplicidade, dado antigo apresentado como atual ou backlog crescente;
- recurso/log/WAL/conexão crescer sem estabilizar;
- ocorrer erro P0 ou violação de SLO;
- o período final for soma de janelas interrompidas.

### PKG-99 - RPO, Restore E Desastre

- medir intervalo real de WAL/backup/objetos/configuração antes da mudança;
- configurar WAL contínuo e alertas de atraso;
- provar pior caso de RPO físico `<= 5 minutos`;
- preservar RPO zero em deploy/cutover;
- executar backup base/lógico/objetos/configuração com checksum;
- restaurar em cluster isolado e limitado por CPU/I/O;
- validar schema, revisions, FKs, sequences, objetos, configuração e busca;
- simular perda de processo, banco, Redis, storage, disco, segredo e host;
- restaurar usando somente cópia/chave/custódia externas;
- medir RTO completo e exigir `<= 15 minutos` no volume atual;
- validar alerta antes de violar RPO/RTO;
- executar carga simultânea para provar que frequência não degrada produção;
- executar preview de retenção sem prune automático;
- exigir confirmação explícita separada para qualquer exclusão;
- revisar runbook e exercício com responsável independente;
- executar gate completo, restore e smoke público.

Não avançar se:

- backup depender do host que está sendo simulado como perdido;
- RPO/RTO ultrapassar meta;
- restore usar snapshot incompatível sem bloquear readiness;
- busca/objetos/configuração não reconciliar;
- aumento de frequência degradar SLO;
- prune/exclusão ocorrer sem preview e confirmação;
- host único for documentado como alta disponibilidade física.

### PKG-20 Validado Em 2026-05-22

Testes automatizados executados:

- `cd backend && . .venv/bin/activate && pytest tests/test_schema_versioning.py`
- `cd backend && . .venv/bin/activate && pytest tests/test_printers.py tests/test_schema_versioning.py`
- `cd backend && . .venv/bin/activate && pytest`
- `./check.sh`

Validação manual/local executada:

- Startup do FastAPI com `PRINTORA_DATA_DIR="$HOME/Library/Application Support/Printora"`.
- Banco validado: `$HOME/Library/Application Support/Printora/printora.db`.
- Impressoras antes do startup: 2.
- Impressoras depois do startup: 2.
- `GET /api/system/version` retornou `schema_current.revision=16` e `latest_validation.status=ok`.
- Resultado: inicialização preservou as impressoras cadastradas e aplicou o schema versionado sem perda de dados.

## Critérios Para Não Avançar

Não avançar se:

- `./check.sh` falhar;
- houver risco de flash sem confirmação;
- houver alteração de config sem backup;
- relatório expuser segredo;
- app não conseguir distinguir leitura de mutação.
## Validação Do Programa Comunitário Plurianual

O inventário histórico em `docs/community/COMMUNITY_BACKLOG.md` decompõe ideias
em lentes genéricas, mas não define cobertura obrigatória. Ao reativar uma ideia
no portfólio, `TESTES.md` deve receber cenários específicos proporcionais ao
risco e ao fluxo real.

Mínimo por prioridade:

- `P0`: unitário, contrato/API, permissão, abuso, privacidade, acessibilidade, mobile, falha segura, rollback, revisão independente, piloto controlado e evidência com especialista;
- `P1`: regra, contrato, acessibilidade, mobile/offline, equidade, estados de tela e validação com usuários representativos;
- `P2`: regra, API, integração, permissões, estados de tela, responsividade e fluxo principal real;
- `P3`: contrato comercial, fraude, pagamento, cancelamento, imposto, disputa, acessibilidade e transparência de taxa;
- `P4`: experimento isolado com hipótese, opt-in, privacidade, orçamento, critério de parada e nenhuma dependência crítica.

Nenhum experimento pode usar produção, criança, dado biométrico, comando de impressora ou dispositivo assistivo sem fluxo específico aprovado. Métrica de sucesso deve ser acompanhada de métrica de dano e recortes de equidade quando aplicável.

## Matriz Responsiva Do Shell E Detalhe

O gate E2E deve validar com backend real e dados sintéticos isolados:

- as quinze rotas autenticadas em 320x568, 390x844, 768x1024, 1024x768 e
  1440x900;
- perfil público, impressora pública e as seis abas da comunidade nas mesmas
  cinco dimensões;
- ausência de elementos visíveis fora do viewport, exceto dentro de um
  container com rolagem horizontal explícita;
- abertura e seleção das nove abas do detalhe da impressora em 320 px;
- abertura sem overflow da Central de alertas, cadastro de impressora, registro
  livre de manutenção e quatro modais de relatório/backup/restore;
- cabeçalho e barra de abas inteiramente contidos no viewport;
- lista de agentes como cartões rotulados em largura reduzida;
- administrador da plataforma com leitura dos overviews de Finanças e
  Fabricação antes da atribuição de papéis operacionais;
- ações financeiras e produtivas sensíveis ainda protegidas pelos papéis
  específicos e autenticação reforçada aplicável;
- ausência de plataforma do host, URL interna e tecnologia de infraestrutura
  nas superfícies operacionais cobertas.
- rótulos da Visão geral não podem ultrapassar a própria caixa e invadir o
  valor, mesmo quando o documento não possui overflow horizontal;
- Arquivos G-code deve usar fixture com metadados completos e vazios, validar
  cartões em 320 e 390 px, omitir apenas valores ausentes e limitar a altura
  para impedir a reprodução de uma tabela desktop vertical infinita;
- títulos e descrições do upload/gerenciador devem ocupar blocos separados,
  sem colisão visual.
- metadados do agente devem normalizar listas JSON e sequências de materiais,
  remover repetições e omitir marcadores técnicos de valor desconhecido.
- uma leitura operacional antiga offline nao pode sobrepor health atual online;
- com agente online e Moonraker ainda nao confirmado, a revalidacao deve ser
  sequencial, sem sobreposicao, com intervalo de 3 segundos.

Além do gate, a aceitação visual deve usar navegador real nas cinco dimensões,
abrir cada aba e registrar qualquer diferença entre DOM, screenshot e ação
efetivamente executável.

## Portabilidade Das Consultas Operacionais

Consultas compartilhadas entre SQLite de teste e PostgreSQL Cloud devem manter:

- booleanos PostgreSQL comparados por parâmetro booleano, nunca por literal
  inteiro;
- consultas agregadas com todas as chaves externas necessárias no `GROUP BY`;
- teste focado do adaptador e do repositório afetado;
- smoke do endpoint no PostgreSQL real após a publicação.

## PKG-100: Arquivos G-code

- provar que a montagem da aba dispara uma única listagem e que busca/filtro
  cancelam a leitura anterior;
- validar paginação, ordenação, diretório e enriquecimento concorrente limitado;
- testar path traversal, extensões, limite de 96 MB, digest e escopo por
  impressora do upload temporário;
- comprovar streaming cloud-agente-Moonraker sem G-code no payload persistido;
- impedir sobrescrita sem confirmação e impedir imprimir/preaquecer quando o
  preflight detectar estado incompatível;
- cobrir pasta, metascan, fila, lote, editor e frases exatas/step-up;
- executar build/budget, testes backend/agente, `./check.sh`, smoke público e
  aceite navegável nas duas impressoras;
- nos testes físicos, usar arquivo inofensivo e não iniciar impressão real até
  confirmar que a impressora está ociosa.

Aceite de 2026-07-24:

- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`: aprovado, com 22/22
  E2E, 627 testes Python, testes Go e gates de frontend;
- produção no commit `4e53912`, workflow `30102603946` aprovado e agentes
  `0.1.36`;
- Voron 0.2: Moonraker online, listagem única paginada, detalhe e preview 3D,
  upload de `printora-pkg100-safe-smoke.gcode`, impressão protegida registrada
  como `succeeded` e estado final `complete`;
- Voron 2.4: Moonraker online, listagem única paginada, detalhe e preview 3D,
  upload do mesmo arquivo inofensivo, ação de impressão HTTP 200 registrada
  como `succeeded` e estado final `complete`;
- o arquivo de smoke contém somente mensagens no display e espera de 1 segundo,
  sem comandos de movimento, extrusão ou aquecimento.

## PKG-101: Layout, design system e coerência visual

- provar que `GET /api/design-system/v1/capabilities` exige a conta
  administradora da plataforma, devolve `403` para usuário comum, mantém
  contrato `1.x`, retorna exatamente oito capacidades e ocupa menos de 64 KiB;
- provar que usuário comum não vê o menu e não renderiza o laboratório ao abrir
  uma rota direta, enquanto a conta administradora preserva o fluxo completo;
- validar unicidade e cobertura contígua de `CAP-18-01`–`CAP-18-08`,
  `COM-0953`–`COM-1008` e `SCR-0137`–`SCR-0144`;
- cobrir lista, busca/filtro, detalhe e editor em rotas separadas, incluindo
  entrada direta e navegação voltar/avançar;
- testar parse defensivo, limite de 32 KiB, salvamento idempotente, restauração
  confirmada e conflito de revisão entre abas;
- exercitar densidades, cards, tabela, galeria, formulário longo e os estados
  loading, vazio, erro, sucesso, parcial, offline, acesso negado e conflito;
- validar teclado, foco, landmarks, leitor de tela, temas, zoom 400%, redução de
  movimento e ausência de overflow em 320, 375, 768, 1024 e 1440 px;
- executar screenshot desktop/mobile em tema claro e escuro e comparar o
  laboratório com a referência aprovada;
- provar que não existe endpoint mutável, comando físico, PII, telemetria
  individual, SQL ou dependência de pacote posterior;
- executar testes focados, build/budget, E2E autenticado, validador de
  dependências e `./check.sh`.

## PKG-102: Acessibilidade universal

- provar que catálogo e preferências exigem autenticação, mantêm contrato
  `1.x`, payload limitado e cobertura exata de `CAP-09-01`–`CAP-09-08`,
  `COM-0449`–`COM-0504` e `SCR-0065`–`SCR-0072`;
- executar primeira aplicação e reexecução dos scripts
  `086_accessibility_preferences.sql` e
  `postgresql/018_accessibility_preferences.sql`, incluindo constraints,
  execução concorrente e retomada sem `DROP`, `DELETE` ou duplicidade;
- testar defaults sem escrita, primeira gravação, gravação inalterada,
  atualização, `Idempotency-Key`, revisão divergente e isolamento entre dois
  usuários;
- rejeitar owner externo, campo desconhecido, enum inválido, escala fora de
  100%–200%, payload sem chave idempotente e sessão ausente;
- cobrir preferências, explicações opcionais e editor em rotas separadas,
  navegação voltar/avançar e entrada direta nas oito famílias;
- garantir que `CAP`, `COM`, `SCR`, revisão, contrato e rollback não sejam
  renderizados na interface do cliente e que a entrada exista somente no menu
  pessoal aberto pelo avatar;
- validar loading, vazio, erro, sucesso, parcial, offline, acesso negado e
  conflito; timeout, `429` e `5xx` preservam a entrada e oferecem recuperação;
- validar semântica, nomes, landmarks, regiões vivas, ordem/foco, teclado,
  switch equivalente, rótulos para voz, contraste, zoom 400%, temas, redução de
  movimento, legendas, transcrição, audiodescrição e linguagem simples;
- validar alternativa textual da amostra 3D e exportações SVG/BRF menores que
  32 KiB, sem HTML arbitrário, upload ou persistência;
- bloquear overflow em 320, 375, 768, 1024 e 1440 px e comparar screenshots
  desktop/mobile; Axe não permite violações críticas ou sérias;
- executar testes backend/frontend focados, build/budget, E2E autenticado,
  validador de dependências e `./check.sh`;
- teste com pessoas representativas e publicação são evidências externas
  separadas. Ausência deve ser registrada como risco residual, sem equivalência
  a teste executado.

## PKG-104: Segurança mínima e verificável

- validar schema aditivo SQLite/PostgreSQL, reexecução, constraints, retenção e
  ausência de `DROP`, `DELETE`, cascade ou prune;
- provar sessão opaca, ownership na revogação, revogação coletiva e revogação
  total após troca de senha;
- provar MFA pendente, step-up por finalidade, expiração, replay negado e
  consumo exatamente uma vez sob concorrência;
- validar isolamento de owner/organização e rejeitar criação, convite ou aceite
  indevido de papel owner;
- testar exportação determinística sem hashes, tokens ou segredos; testar
  desativação lógica idempotente preservando auditoria;
- negar job genérico de host, exigir administrador e step-up em mutações
  físicas e exercitar quoting de parâmetros de shell;
- validar checksum, assinatura, identidade de chave, protocolo, rollback do
  binário e bloqueio durante impressão;
- provar bloqueio social bidirecional, denúncia, remoção lógica, recurso do
  autor, decisão terminal, restauração e retenção;
- testar rate limit, falha fechada da autenticação, sanitização recursiva de
  logs/bundles, incidente simulado e rollback por flag;
- testar IDOR cruzado em backup, manutenção, snapshot e firmware;
- validar busca SQLite para conteúdo público, associação comunitária e bloqueio
  bidirecional, além de ocultar chaves internas de armazenamento na API pública;
- rejeitar archive bomb, metadado externo excessivo, origem de update divergente,
  release do agente fora da origem e redirecionamento externo;
- validar workflow sem interpolação direta de input no shell, sem TOFU por
  `ssh-keyscan` e com `PRINTORA_SSH_KNOWN_HOSTS` obrigatório;
- provar que instaladores não executam conteúdo remoto por pipe ou substituição
  de comando;
- executar testes focados, regressão Python/Go/frontend, build/budget,
  auditoria de segurança sobre o estado final e `./check.sh`.

## PKG-114: Materiais, spools e qualidade básica

- aplicar e reaplicar os scripts SQLite e PostgreSQL, validar tabelas, índices,
  constraints, triggers imutáveis e registro de versão sem perda de dados;
- provar CRUD local owner-scoped, revisão otimista, arquivamento lógico e
  rejeição de leitura ou mutação por outro usuário;
- importar a mesma resposta do Spoolman repetidamente sem duplicar spool e
  impedir edição do cache canônico pelo Printora;
- confirmar que falha do agente, Moonraker ou Spoolman devolve estado
  acionável e preserva integralmente os spools locais;
- registrar consumo planejado sem reduzir peso e consumo confirmado com
  redução atômica exatamente uma vez; repetir chave idempotente idêntica deve
  retornar o mesmo evento e payload divergente deve conflitar;
- bloquear consumo maior que o disponível e preservar ledger/peso na falha;
- validar compatibilidade `unknown`, `incompatible` e `compatible` com perfil,
  material, impressora, peso e ventilação, sem regra de negócio no frontend;
- registrar medida nominal, real e tolerância e derivar resultado de forma
  determinística; histórico confirmado permanece imutável;
- validar alertas de peso, armazenamento, secagem, ventilação, validade e
  descarte com linguagem acionável e sem promessa física indevida;
- validar job read-only do agente por `/server/spoolman/status` e
  `/server/spoolman/proxy`, sem cloud conectar diretamente à rede privada;
- validar lista, vazio, criação/edição separadas, detalhe, consumo, qualidade,
  falha do Spoolman, teclado, Axe e ausência de overflow em desktop e celular;
- executar testes focados backend/Go/frontend, build/budget, E2E autenticado,
  validador de dependências e `./check.sh`.

### PKG-131 - Perfis OrcaSlicer locais reproduzíveis

- validar exatamente 14 perfis V24 0.6 e 14 derivados V02 0.4;
- comparar cada derivado com sua fonte, herança, impressoras compatíveis e
  larguras de extrusão nunca menores que 0,4 mm;
- executar o instalador sem `--apply` e confirmar validação sem escrita local;
- aplicar somente em diretório temporário controlado, confirmando backup,
  máquina, processos, seleção preservada e rejeição de host com credenciais;
- executar `backend/.venv/bin/python -m pytest -q
  backend/tests/test_orcaslicer_profiles.py` e o gate completo no fechamento.

### PKG-141 - Captura guiada de objeto por fotos

- validar criação, retomada, conclusão, cancelamento e expiração da sessão por
  owner, incluindo negação e não enumeração entre usuários/organizações;
- validar upload direto/repetido, checksum, idempotency key, assinatura real do
  arquivo, limites, quota, quarentena e ausência de duplicidade após retry;
- validar JPEG, PNG e HEIC somente quando o decoder homologado estiver presente;
  formato não suportado falha antes de persistir artefato processável;
- validar remoção de localização EXIF e preservação somente de metadados
  necessários, sem foto, nome sensível ou storage key em log/erro;
- validar fixtures controladas de foco, movimento, exposição, duplicidade,
  resolução, orientação, cobertura e ângulos ausentes;
- validar marcador de escala, medida conhecida, unidade e incerteza; sem escala,
  bloquear alegação de dimensão real;
- validar retenção de rascunho, exportação do owner e rotina de cleanup em
  dry-run/fixture, sem exclusão física não autorizada;
- validar UI de `Digitalizar objeto` em 320, 375, 768, 1024 e 1440 px, câmera e
  seleção de arquivos, perda/retomada de rede, teclado, leitor de tela, zoom 400%
  e redução de movimento;
- validar distribuição mínima por altura, contador de posições cobertas e
  recomendação da próxima volta; quantidade total desequilibrada não conclui;
- validar que o protocolo padrão mostra exatamente 24 posições nomeadas, em
  três voltas de oito, libera uma próxima posição por vez, permite substituir
  posição reprovada e recusa índice acima do total da sessão;
- validar que listagem, criação e detalhe de projeto são estados separados, que
  `Abrir projeto` remove a grade da tela e que o detalhe oferece retorno e
  navegação por responsabilidade sem coluna lateral;
- executar threat model de upload, conteúdo ilegal, pessoa no quadro, EXIF,
  abuso de quota, IDOR e storage privado;
- fechamento exige benchmark de captura real versionado, testes backend/frontend,
  contrato/SQL N/N-1 e `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-153 - Reconstrução 3D por múltiplas fotos

- validar máquina de estados do job, tentativa, cancelamento, timeout,
  reconciliação e terminais sem transição inválida;
- validar outbox/worker com crash entre etapas, lease, retry seguro,
  backpressure, quota e concorrência sem duplicar job, cobrança ou artefato;
- validar webhook autenticado, replay, corpo excessivo, evento fora de ordem,
  polling concorrente e resposta divergente reconciliada pela fonte;
- validar adapter com fixtures gravadas, contrato comum, versão fixada,
  circuit breaker e falha isolada de cada engine/provider;
- no gateway Tripo, validar quatro vistas na ordem documentada, checkpoint por
  correlação, reaproveitamento da tarefa paga no retry, divergência de
  fingerprint, duas execuções concorrentes com uma única criação remota e
  estados finais do polling sem chamada real no teste comum;
- validar preview e aplicação supervisionada da retenção, removendo somente
  checkpoint concluído e expirado e preservando ativo, recente, legado,
  inválido, symlink e arquivo com lock concorrente;
- validar egress allowlist/SSRF, URLs assinadas, rotação de segredo, logs
  sanitizados e ausência de fotos/payload bruto em bundle de suporte;
- validar provenance com fontes, checksums, engine, modelo/versão, parâmetros,
  custo e regiões observadas/inferidas;
- comparar pipeline próprio e provider elegível no mesmo benchmark, medindo
  conclusão, cobertura, geometria/escala, duração, recurso e custo;
- validar que Raspberry Pi e agente não recebem job pesado, fotos ou credencial
  do provider;
- validar UI de fila, estágios, cancelamento, erro acionável, retomada e preview
  bruto sem percentual inventado;
- validar que ausência de classificação espacial gera aviso explícito e que a
  pessoa pode comparar amostras determinísticas da forma inicial e corrigida;
- fechamento exige testes domínio/worker/adapter/API/segurança/carga/UI,
  canário controlado, compatibilidade N/N-1, retenção/cleanup e
  `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### PKG-154 - Qualificação e entrega de modelo imprimível

- validar fixtures de malha manifold e non-manifold, watertight e aberta,
  normais invertidas, componentes soltos, faces degeneradas, buracos,
  auto-interseção, escala inválida e espessura insuficiente;
- validar limites de CPU, memória, faces, tempo e tamanho para parser/reparo,
  sem travar API nem aceitar arquivo parcial como aprovado;
- validar que cada reparo gera nova revisão, parent, parâmetros, checksum e
  diff; original e revisão anterior permanecem íntegros;
- validar repetibilidade e reexecução idempotente de limpeza, normais,
  fechamento controlado, remoção de componentes e decimação;
- validar escala, medida conhecida, dimensões críticas, unidade, incerteza e
  bloqueio de alegação mecânica sem confirmação;
- validar mapa e alternativa textual para regiões observadas, inferidas e
  reparadas; IA não altera artefato sem ação e aprovação humana;
- validar snapshot imutável, manifesto, provenance, checksum, download STL/3MF
  e job de fatiamento preso à versão aprovada;
- validar que download não exige impressora e que fatiamento exige os mesmos
  preflights e permissões do fluxo normal de projeto;
- executar piloto físico controlado com instrumento identificado e registrar
  erro por eixo, material, perfil, resultado e classes não suportadas;
- validar opt-out, retenção, denúncia, falha do provider/reparo e rollback por
  flags separadas sem afetar projetos ou fatiamentos comuns;
- validar UI bruto/qualificado em desktop/mobile, acessibilidade, confirmação de
  limitações e ausência de publicação/fatiamento/envio automáticos;
- validar que aprovação humana exige checksum vigente, forma conferida, aceite
  de limitações e medida com desvio máximo de 3%, e que finalidade mecânica é
  recusada;
- validar que o mesmo objeto promovido vira arquivo fatiável e snapshot do
  projeto sem dupla contagem de armazenamento, e que a tela recarrega o projeto
  antes de oferecer continuidade para o fatiamento normal;
- validar que somente histórico concluído/falho do arquivo aprovado aceita
  piloto físico, exige instrumento e ao menos um eixo, calcula erro por eixo,
  preserva snapshots de material/perfil/impressora, é idempotente e não aceita
  resultado `passed` quando o maior desvio ultrapassa 3%;
- fechamento exige testes backend/frontend/worker/SQL/contrato/segurança,
  benchmark físico revisado, rollback ensaiado e
  `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
