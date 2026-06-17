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
- prévia pública antes de publicar;
- página pública real `/p/{printer_id}`;
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
- `GET /api/system/version` retorna versão do app, `data_dir`, caminho do banco, scripts SQL aplicados, schema atual e última validação sem conteúdo do banco;
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

- Confirmar que `GET /api/system/version` retorna versão do app, caminho de dados e schema aplicado.
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
- Validar que UI de Comunidades > Arquivos mostra painel de armazenamento organizado, responsivo e separado de cadastro/lista/detalhe.
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

- Validar criação de job com usuário, impressora, perfil opcional, modelo, dimensões e qualidade.
- Validar bloqueio de modelo maior que o volume útil catalogado da impressora.
- Validar bloqueio de perfil incompatível com a variação catalogada da impressora.
- Validar execução com engine ausente gerando falha acionável e log rastreado, sem G-code falso.
- Validar execução com engine configurada em worker isolado, registrando artefatos `gcode`, `log` e `metadata`.
- Validar cancelamento de job planejado ou em execução.
- Validar UI de Administração com formulário responsivo, lista de jobs, estados, erros, artefatos e ações.
- Testes automatizados focados: `cd backend && uv run --extra dev pytest ../backend/tests/test_slicing.py ../backend/tests/test_slicing_pipeline.py -q`.
- Validação de schema/update: `cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q`.
- Validação frontend focada: `npm --prefix frontend run build`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

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
