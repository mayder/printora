# DEMANDAS.md

Backlog executável ativo do Printora. Os pacotes consolidados `PKG-01` a
`PKG-100` foram preservados integralmente em
`DEMANDAS_CONSOLIDADAS_PKG_01_100.md` e não foram apagados.

## Cobertura Do Programa Comunitário

- 55 pacotes comunitários: `PKG-101` a `PKG-155`;
- 55 frentes estratégicas e 440 capacidades;
- 3.080 requisitos atômicos, `COM-0001` a `COM-3080`;
- 440 famílias de tela, `SCR-0001` a `SCR-0440`;
- 1.320 estados principais separados de lista, detalhe e cadastro/edição;
- prioridades P0 a P4 preservadas como atributo de impacto;
- numeração topológica: todo pacote depende somente de IDs menores;
- nenhum requisito foi copiado parcialmente: cada ID pertence a um único pacote.

Fontes complementares obrigatórias:

- `docs/community/MASTER_PLAN.md`: objetivo, fases, layout e métricas;
- `docs/community/PLATFORM_BENCHMARK.md`: comparação e padrões externos;
- `docs/community/COMMUNITY_BACKLOG.md`: requisitos atômicos completos;
- `docs/community/COMMUNITY_SCREENS.md`: telas, rotas e estados;
- `docs/community/PRIORITIES.md`: prioridade por impacto social;
- `docs/community/PACKAGE_ARCHITECTURE.csv`: owner, colaboradores, área
  frontend e risco de cada pacote;
- `docs/community/PACKAGE_EXECUTION_STANDARD.md`: Definition of Ready,
  padrões de implementação e Definition of Done bloqueantes;
- `docs/community/PACKAGE_MODELING_REVIEW.md`: revisão transversal e riscos residuais;
- `docs/community/SUMMARY.json`: totais verificáveis.

## Decisão Sobre O Número 101

O pacote de evidências residuais cogitado em conversa nunca foi registrado.
As dispensas históricas permanecem nos PKG-97 e PKG-98. O `PKG-101` agora
inicia as fundações comunitárias com layout e design system.

## Ordem Recomendada De Implementação

A lista abaixo já é topológica. Executar em ordem numérica. Pacotes podem ser
trabalhados em janelas diferentes somente quando todas as dependências de IDs
menores estiverem concluídas e não houver edição concorrente do mesmo contrato,
schema, rota ou componente compartilhado.

- PKG-101 [P1]: Layout, design system e coerência visual
- PKG-102 [P1]: Acessibilidade universal
- PKG-103 [P1]: Mobilidade, PWA e uso em campo
- PKG-104 [P0]: Segurança da plataforma e das impressoras
- PKG-105 [P0]: Privacidade e soberania de dados
- PKG-106 [P2]: Analytics de produto e impacto social
- PKG-107 [P0]: Moderação e segurança comunitária
- PKG-108 [P0]: Integridade, confiança e combate a fraude
- PKG-109 [P1]: Internacionalização e inclusão linguística
- PKG-110 [P1]: Onboarding e ativação progressiva
- PKG-111 [P0]: Segurança de modelos e uso responsável
- PKG-112 [P0]: Proteção de crianças e adolescentes
- PKG-113 [P1]: Qualidade, metrologia e rastreabilidade
- PKG-114 [P2]: Materiais, spools e ciência de processo
- PKG-115 [P1]: Fabricação local e capacidade produtiva
- PKG-116 [P0]: Tecnologia assistiva e autonomia
- PKG-117 [P0]: Resposta humanitária e resiliência local
- PKG-118 [P1]: Educação maker e aprendizagem ao longo da vida
- PKG-119 [P1]: Escolas, bibliotecas e makerspaces
- PKG-120 [P1]: Reparo, peças de reposição e economia circular
- PKG-121 [P1]: Sustentabilidade e uso responsável de materiais
- PKG-122 [P2]: Identidade, perfil e presença avançada
- PKG-123 [P2]: Grafo social e relações contextuais
- PKG-124 [P2]: Comunidades avançadas e governança local
- PKG-125 [P2]: Publicação rica e narrativa de fabricação
- PKG-126 [P2]: Conhecimento técnico e suporte estruturado
- PKG-127 [P2]: Fotos, vídeo, live e mídia técnica
- PKG-128 [P2]: Biblioteca 3D profissional e gestão de ativos
- PKG-129 [P2]: Visualização 3D e inspeção técnica
- PKG-130 [P2]: Customização paramétrica e geração
- PKG-131 [P2]: Fatiamento avançado e perfis reproduzíveis
- PKG-132 [P2]: Fluxo ponta a ponta de impressão
- PKG-133 [P2]: Manutenção colaborativa e confiabilidade
- PKG-134 [P2]: Fazendas de impressão e filas compartilhadas
- PKG-135 [P2]: Coautoria, equipes e colaboração de projeto
- PKG-136 [P2]: Mensagens, chat e presença em tempo real
- PKG-137 [P2]: Eventos, encontros e fabricação coletiva
- PKG-138 [P2]: Feed pessoal e consumo saudável
- PKG-139 [P2]: Busca multimodal e descoberta avançada
- PKG-140 [P2]: Recomendação e personalização responsável
- PKG-141 [P2]: Câmeras, visão computacional e assistência por IA
- PKG-142 [P2]: Integrações e portabilidade do ecossistema 3D
- PKG-143 [P2]: Plataforma de desenvolvedores e extensões
- PKG-144 [P3]: Ferramentas profissionais para criadores
- PKG-145 [P3]: Reputação, reconhecimento e credenciais
- PKG-146 [P3]: Organizações, equipes e presença institucional
- PKG-147 [P3]: Marketplace de modelos, serviços e impressões
- PKG-148 [P3]: Clubes, assinaturas e apoio recorrente
- PKG-149 [P3]: Pedidos, logística e pós-venda
- PKG-150 [P3]: Desafios, concursos e missões coletivas
- PKG-151 [P3]: Financiamento coletivo e pré-venda
- PKG-152 [P3]: Pesquisa aberta e ciência cidadã
- PKG-153 [P4]: Escaneamento, realidade aumentada e espacial
- PKG-154 [P4]: Copilotos e automação assistida
- PKG-155 [P4]: Interfaces futuras e experiências experimentais

## Índice Por Prioridade Social

### P0 — Proteção da vida, autonomia e confiança básica

- PKG-104: Segurança da plataforma e das impressoras
- PKG-105: Privacidade e soberania de dados
- PKG-107: Moderação e segurança comunitária
- PKG-108: Integridade, confiança e combate a fraude
- PKG-111: Segurança de modelos e uso responsável
- PKG-112: Proteção de crianças e adolescentes
- PKG-116: Tecnologia assistiva e autonomia
- PKG-117: Resposta humanitária e resiliência local

### P1 — Acesso, educação, sustentabilidade e infraestrutura social

- PKG-101: Layout, design system e coerência visual
- PKG-102: Acessibilidade universal
- PKG-103: Mobilidade, PWA e uso em campo
- PKG-109: Internacionalização e inclusão linguística
- PKG-110: Onboarding e ativação progressiva
- PKG-113: Qualidade, metrologia e rastreabilidade
- PKG-115: Fabricação local e capacidade produtiva
- PKG-118: Educação maker e aprendizagem ao longo da vida
- PKG-119: Escolas, bibliotecas e makerspaces
- PKG-120: Reparo, peças de reposição e economia circular
- PKG-121: Sustentabilidade e uso responsável de materiais

### P2 — Núcleo comunitário e fabricação conectada

- PKG-106: Analytics de produto e impacto social
- PKG-114: Materiais, spools e ciência de processo
- PKG-122: Identidade, perfil e presença avançada
- PKG-123: Grafo social e relações contextuais
- PKG-124: Comunidades avançadas e governança local
- PKG-125: Publicação rica e narrativa de fabricação
- PKG-126: Conhecimento técnico e suporte estruturado
- PKG-127: Fotos, vídeo, live e mídia técnica
- PKG-128: Biblioteca 3D profissional e gestão de ativos
- PKG-129: Visualização 3D e inspeção técnica
- PKG-130: Customização paramétrica e geração
- PKG-131: Fatiamento avançado e perfis reproduzíveis
- PKG-132: Fluxo ponta a ponta de impressão
- PKG-133: Manutenção colaborativa e confiabilidade
- PKG-134: Fazendas de impressão e filas compartilhadas
- PKG-135: Coautoria, equipes e colaboração de projeto
- PKG-136: Mensagens, chat e presença em tempo real
- PKG-137: Eventos, encontros e fabricação coletiva
- PKG-138: Feed pessoal e consumo saudável
- PKG-139: Busca multimodal e descoberta avançada
- PKG-140: Recomendação e personalização responsável
- PKG-141: Câmeras, visão computacional e assistência por IA
- PKG-142: Integrações e portabilidade do ecossistema 3D
- PKG-143: Plataforma de desenvolvedores e extensões

### P3 — Economia de criadores e crescimento sustentável

- PKG-144: Ferramentas profissionais para criadores
- PKG-145: Reputação, reconhecimento e credenciais
- PKG-146: Organizações, equipes e presença institucional
- PKG-147: Marketplace de modelos, serviços e impressões
- PKG-148: Clubes, assinaturas e apoio recorrente
- PKG-149: Pedidos, logística e pós-venda
- PKG-150: Desafios, concursos e missões coletivas
- PKG-151: Financiamento coletivo e pré-venda
- PKG-152: Pesquisa aberta e ciência cidadã

### P4 — Experimentação responsável

- PKG-153: Escaneamento, realidade aumentada e espacial
- PKG-154: Copilotos e automação assistida
- PKG-155: Interfaces futuras e experiências experimentais

## Política De Backlog

### Quando criar pacote

Criar pacote quando a demanda mudar contrato público, banco, segurança,
operação crítica, UI de fluxo completo, integração externa, rollback ou exigir
mais de um lote para entrega verificável. Não criar pacote paralelo quando o
escopo já pertencer a `PKG-101`–`PKG-155`.

## Contrato De Independência E Idempotência

As regras abaixo são bloqueantes para todos os pacotes:

1. dependências comunitárias devem ser explícitas e ter ID menor;
2. nenhum pacote pode exigir contrato, tabela, tela, worker ou serviço de pacote futuro;
3. o pacote entrega uma fatia vertical utilizável, testável, publicável e reversível;
4. SQL é idempotente e reexecutável; migrations, `DROP` e limpeza destrutiva são proibidos;
5. comandos, jobs, webhooks, filas, imports e retries usam chave idempotente e deduplicação;
6. seeds/upserts não duplicam registros e preservam alterações válidas do usuário;
7. APIs preservam compatibilidade N/N-1 e consumidores antigos durante rollout;
8. reprocessamento após timeout/restart não repete cobrança, publicação, comando físico ou notificação;
9. rollback de código não restaura banco antigo nem apaga dados confirmados;
10. `scripts/validate-demand-package-dependencies.py` bloqueia referência futura, lacuna e pacote sem marcador de entrega isolada.

Idempotência documental é obrigação de implementação, não promessa antecipada.
Cada pacote só pode ser fechado depois de testes reais provarem reexecução segura
nos fluxos mutáveis aplicáveis.

## Contrato Obrigatório De Todos Os Pacotes

Antes do primeiro lote, a janela executora deve:

1. reler `PATHS.toml`, `QUALITY_ROADMAP.md`, `GOVERNANCA.md` e este pacote;
2. cumprir integralmente `docs/community/PACKAGE_EXECUTION_STANDARD.md`;
3. confirmar owner, colaboradores, área frontend e risco na matriz
   `docs/community/PACKAGE_ARCHITECTURE.csv`;
4. auditar código e contratos atuais para reaproveitar capacidades existentes;
5. confirmar IDs `COM`, `CAP` e `SCR` atribuídos ao lote;
6. atualizar `TELAS.md`, `TESTES.md`, `BUGS.md` e `DECISOES.md` quando aplicável;
7. manter frontend sem regra de negócio/persistência e separar lista, detalhe, criação e edição;
8. definir autorização deny-by-default, isolamento, rate limit, retenção, observabilidade e rollback;
9. usar fixtures sintéticas, nunca dump ou segredo de produção;
10. validar mobile a partir de 320 px, teclado, leitor de tela, zoom, contraste, offline e falhas;
11. provar idempotência, compatibilidade N/N-1 e entrega isolada antes do fechamento;
12. revisar integralmente, executar `./check.sh` e criar commit exclusivo.

Cada lote cobre as sete lentes contíguas: produto, tela, mobile,
acessibilidade, confiança, impacto e qualidade. O `SCR` exige lista/filtro,
detalhe, criação e edição separados, além de loading, empty, error, success,
partial, offline, forbidden e conflict quando aplicável.

## PKG-101: Layout, design system e coerência visual

Objetivo:

Uso mais fácil, previsível e inclusivo em toda a plataforma.

Prioridade social: P1.

Rastreabilidade integral:

- capacidades: `CAP-18-01` a `CAP-18-08`;
- requisitos: `COM-0953` a `COM-1008` — 56 itens;
- telas: `SCR-0137` a `SCR-0144` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: nenhum.

Entrega isolada:

- Ao fechar, o `PKG-101` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Design system documentado com tokens semânticos** — `CAP-18-01`, `COM-0953` a `COM-0959`, `SCR-0137`, rota planejada `/community/design_system/design-system-documentado-com-tokens-semanticos`.
2. **Hierarquia visual consistente entre social e operação** — `CAP-18-02`, `COM-0960` a `COM-0966`, `SCR-0138`, rota planejada `/community/design_system/hierarquia-visual-consistente-entre-social-e-operacao`.
3. **Componentes responsivos para cards, tabelas e galerias** — `CAP-18-03`, `COM-0967` a `COM-0973`, `SCR-0139`, rota planejada `/community/design_system/componentes-responsivos-para-cards-tabelas-e-galerias`.
4. **Densidade ajustável para oficina, leitura e administração** — `CAP-18-04`, `COM-0974` a `COM-0980`, `SCR-0140`, rota planejada `/community/design_system/densidade-ajustavel-para-oficina-leitura-e-administracao`.
5. **Padrões de formulário longo com salvamento e revisão** — `CAP-18-05`, `COM-0981` a `COM-0987`, `SCR-0141`, rota planejada `/community/design_system/padroes-de-formulario-longo-com-salvamento-e-revisao`.
6. **Estados loading, vazio, erro, parcial e offline coerentes** — `CAP-18-06`, `COM-0988` a `COM-0994`, `SCR-0142`, rota planejada `/community/design_system/estados-loading-vazio-erro-parcial-e-offline-coerentes`.
7. **Microinterações com feedback e redução de movimento** — `CAP-18-07`, `COM-0995` a `COM-1001`, `SCR-0143`, rota planejada `/community/design_system/microinteracoes-com-feedback-e-reducao-de-movimento`.
8. **Laboratório visual com regressão desktop e mobile** — `CAP-18-08`, `COM-1002` a `COM-1008`, `SCR-0144`, rota planejada `/community/design_system/laboratorio-visual-com-regressao-desktop-e-mobile`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0953`–`COM-1008` possuem evidência;
- as oito famílias `SCR-0137`–`SCR-0144` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Concluído em 2026-07-26. Os dez lotes, `CAP-18-01`–`CAP-18-08`,
  `COM-0953`–`COM-1008` e `SCR-0137`–`SCR-0144` possuem evidência em
  `docs/community/PKG_101_EVIDENCE.md`.
- Contrato backend, lista/filtro, detalhe, editor local, tokens, densidades,
  estados, responsividade, acessibilidade, falhas e regressão visual foram
  implementados e validados.
- Menu, rotas internas e API do Design system ficam restritos à conta
  configurada como administradora da plataforma.
- Nenhum SQL, migration, exclusão de dado, comando físico ou dependência futura
  foi introduzido. Publicação não foi executada e depende de autorização
  separada.

## PKG-102: Acessibilidade universal

Objetivo:

Participação equivalente de pessoas com diferentes capacidades visuais, auditivas, motoras e cognitivas.

Prioridade social: P1.

Rastreabilidade integral:

- capacidades: `CAP-09-01` a `CAP-09-08`;
- requisitos: `COM-0449` a `COM-0504` — 56 itens;
- telas: `SCR-0065` a `SCR-0072` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-101`.

Entrega isolada:

- Ao fechar, o `PKG-102` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Conformidade contínua com wcag e testes com usuários** — `CAP-09-01`, `COM-0449` a `COM-0455`, `SCR-0065`, rota planejada `/community/accessibility/conformidade-continua-com-wcag-e-testes-com-usuarios`.
2. **Navegação integral por teclado, switch e voz** — `CAP-09-02`, `COM-0456` a `COM-0462`, `SCR-0066`, rota planejada `/community/accessibility/navegacao-integral-por-teclado-switch-e-voz`.
3. **Leitor de tela com semântica e anúncios de estado** — `CAP-09-03`, `COM-0463` a `COM-0469`, `SCR-0067`, rota planejada `/community/accessibility/leitor-de-tela-com-semantica-e-anuncios-de-estado`.
4. **Contraste, zoom, redução de movimento e temas adaptativos** — `CAP-09-04`, `COM-0470` a `COM-0476`, `SCR-0068`, rota planejada `/community/accessibility/contraste-zoom-reducao-de-movimento-e-temas-adaptativos`.
5. **Legendas, transcrições e audiodescrição para mídia** — `CAP-09-05`, `COM-0477` a `COM-0483`, `SCR-0069`, rota planejada `/community/accessibility/legendas-transcricoes-e-audiodescricao-para-midia`.
6. **Linguagem simples e modo de baixa carga cognitiva** — `CAP-09-06`, `COM-0484` a `COM-0490`, `SCR-0070`, rota planejada `/community/accessibility/linguagem-simples-e-modo-de-baixa-carga-cognitiva`.
7. **Visualização 3d com alternativa textual e tátil exportável** — `CAP-09-07`, `COM-0491` a `COM-0497`, `SCR-0071`, rota planejada `/community/accessibility/visualizacao-3d-com-alternativa-textual-e-tatil-exportavel`.
8. **Central de preferências acessíveis sincronizada** — `CAP-09-08`, `COM-0498` a `COM-0504`, `SCR-0072`, rota planejada `/community/accessibility/central-de-preferencias-acessiveis-sincronizada`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0449`–`COM-0504` possuem evidência;
- as oito famílias `SCR-0065`–`SCR-0072` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Concluído em 2026-07-26. Os dez lotes, `CAP-09-01`–`CAP-09-08`,
  `COM-0449`–`COM-0504` e `SCR-0065`–`SCR-0072` possuem evidência em
  `docs/community/PKG_102_EVIDENCE.md`.
- Contrato backend, preferências sincronizadas, lista/filtro, detalhe, editor,
  alternativas de mídia/3D, artefato tátil, responsividade, acessibilidade,
  falhas, concorrência e regressão visual foram implementados e validados.
- Os scripts `backend/sql/086_accessibility_preferences.sql` e
  `backend/sql/postgresql/018_accessibility_preferences.sql` são aditivos e
  idempotentes. Nenhuma exclusão de dado ou comando físico foi executado.
- Publicação, SQL remoto e piloto com pessoas representativas não foram
  executados e dependem de autorização e coordenação separadas.

## PKG-103: Mobilidade, PWA e uso em campo

Objetivo:

Acesso confiável em celular, oficina, escola e regiões com conectividade limitada.

Prioridade social: P1.

Rastreabilidade integral:

- capacidades: `CAP-10-01` a `CAP-10-08`;
- requisitos: `COM-0505` a `COM-0560` — 56 itens;
- telas: `SCR-0073` a `SCR-0080` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-101`, `PKG-102`.

Entrega isolada:

- Ao fechar, o `PKG-103` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Navegação mobile nativa com barra inferior contextual** — `CAP-10-01`, `COM-0505` a `COM-0511`, `SCR-0073`, rota planejada `/community/mobile/navegacao-mobile-nativa-com-barra-inferior-contextual`.
2. **Pwa instalável com cache seguro e atualização controlada** — `CAP-10-02`, `COM-0512` a `COM-0518`, `SCR-0074`, rota planejada `/community/mobile/pwa-instalavel-com-cache-seguro-e-atualizacao-controlada`.
3. **Fila offline de rascunhos, fotos e medições** — `CAP-10-03`, `COM-0519` a `COM-0525`, `SCR-0075`, rota planejada `/community/mobile/fila-offline-de-rascunhos-fotos-e-medicoes`.
4. **Sincronização resiliente com conflito explícito** — `CAP-10-04`, `COM-0526` a `COM-0532`, `SCR-0076`, rota planejada `/community/mobile/sincronizacao-resiliente-com-conflito-explicito`.
5. **Captura por câmera, qr code, nfc e scanner 3d** — `CAP-10-05`, `COM-0533` a `COM-0539`, `SCR-0077`, rota planejada `/community/mobile/captura-por-camera-qr-code-nfc-e-scanner-3d`.
6. **Notificações push agrupadas e acionáveis** — `CAP-10-06`, `COM-0540` a `COM-0546`, `SCR-0078`, rota planejada `/community/mobile/notificacoes-push-agrupadas-e-acionaveis`.
7. **Modo economia de dados, bateria e processamento** — `CAP-10-07`, `COM-0547` a `COM-0553`, `SCR-0079`, rota planejada `/community/mobile/modo-economia-de-dados-bateria-e-processamento`.
8. **Experiência para luvas, mãos ocupadas e telas externas** — `CAP-10-08`, `COM-0554` a `COM-0560`, `SCR-0080`, rota planejada `/community/mobile/experiencia-para-luvas-maos-ocupadas-e-telas-externas`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0505`–`COM-0560` possuem evidência;
- as oito famílias `SCR-0073`–`SCR-0080` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-104: Segurança da plataforma e das impressoras

Objetivo:

Prevenção de tomada de conta, vazamento e comando físico indevido sobre equipamentos.

Prioridade social: P0.

Rastreabilidade integral:

- capacidades: `CAP-07-01` a `CAP-07-08`;
- requisitos: `COM-0337` a `COM-0392` — 56 itens;
- telas: `SCR-0049` a `SCR-0056` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-101`, `PKG-102`, `PKG-103`.

Entrega isolada:

- Ao fechar, o `PKG-104` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Autenticação multifator e chaves de acesso** — `CAP-07-01`, `COM-0337` a `COM-0343`, `SCR-0049`, rota planejada `/community/security/autenticacao-multifator-e-chaves-de-acesso`.
2. **Sessões por dispositivo com revogação e risco** — `CAP-07-02`, `COM-0344` a `COM-0350`, `SCR-0050`, rota planejada `/community/security/sessoes-por-dispositivo-com-revogacao-e-risco`.
3. **Step-up para compra, publicação e operação crítica** — `CAP-07-03`, `COM-0351` a `COM-0357`, `SCR-0051`, rota planejada `/community/security/step-up-para-compra-publicacao-e-operacao-critica`.
4. **Isolamento estrito entre social e controle operacional** — `CAP-07-04`, `COM-0358` a `COM-0364`, `SCR-0052`, rota planejada `/community/security/isolamento-estrito-entre-social-e-controle-operacional`.
5. **Assinatura e verificação de artefatos distribuídos** — `CAP-07-05`, `COM-0365` a `COM-0371`, `SCR-0053`, rota planejada `/community/security/assinatura-e-verificacao-de-artefatos-distribuidos`.
6. **Programa de divulgação responsável e resposta a incidentes** — `CAP-07-06`, `COM-0372` a `COM-0378`, `SCR-0054`, rota planejada `/community/security/programa-de-divulgacao-responsavel-e-resposta-a-incidentes`.
7. **Detecção de bots, scraping e abuso de api** — `CAP-07-07`, `COM-0379` a `COM-0385`, `SCR-0055`, rota planejada `/community/security/deteccao-de-bots-scraping-e-abuso-de-api`.
8. **Backup, continuidade e recuperação testada do domínio social** — `CAP-07-08`, `COM-0386` a `COM-0392`, `SCR-0056`, rota planejada `/community/security/backup-continuidade-e-recuperacao-testada-do-dominio-social`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0337`–`COM-0392` possuem evidência;
- as oito famílias `SCR-0049`–`SCR-0056` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Concluído em 2026-07-28. Os dez lotes, `CAP-07-01`–`CAP-07-08`,
  `COM-0337`–`COM-0392` e `SCR-0049`–`SCR-0056` possuem evidência em
  `docs/security/PKG_104_EVIDENCE.md`; validação local aprovada sem SSH,
  deploy ou reinício de serviço existente.

## PKG-105: Privacidade e soberania de dados

Objetivo:

Autonomia do usuário e prevenção de exposição doméstica, biométrica, operacional ou comercial.

Prioridade social: P0.

Rastreabilidade integral:

- capacidades: `CAP-06-01` a `CAP-06-08`;
- requisitos: `COM-0281` a `COM-0336` — 56 itens;
- telas: `SCR-0041` a `SCR-0048` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`.

Entrega isolada:

- Ao fechar, o `PKG-105` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Painel unificado de visibilidade por campo e contexto** — `CAP-06-01`, `COM-0281` a `COM-0287`, `SCR-0041`, rota planejada `/community/privacy/painel-unificado-de-visibilidade-por-campo-e-contexto`.
2. **Consentimento granular para telemetria e personalização** — `CAP-06-02`, `COM-0288` a `COM-0294`, `SCR-0042`, rota planejada `/community/privacy/consentimento-granular-para-telemetria-e-personalizacao`.
3. **Exportação completa e portável da conta** — `CAP-06-03`, `COM-0295` a `COM-0301`, `SCR-0043`, rota planejada `/community/privacy/exportacao-completa-e-portavel-da-conta`.
4. **Exclusão segura com retenções legais explicadas** — `CAP-06-04`, `COM-0302` a `COM-0308`, `SCR-0044`, rota planejada `/community/privacy/exclusao-segura-com-retencoes-legais-explicadas`.
5. **Modo pseudônimo separado da identidade comercial** — `CAP-06-05`, `COM-0309` a `COM-0315`, `SCR-0045`, rota planejada `/community/privacy/modo-pseudonimo-separado-da-identidade-comercial`.
6. **Proteção de localização de impressoras e oficinas** — `CAP-06-06`, `COM-0316` a `COM-0322`, `SCR-0046`, rota planejada `/community/privacy/protecao-de-localizacao-de-impressoras-e-oficinas`.
7. **Cofre de medidas corporais e arquivos sensíveis** — `CAP-06-07`, `COM-0323` a `COM-0329`, `SCR-0047`, rota planejada `/community/privacy/cofre-de-medidas-corporais-e-arquivos-sensiveis`.
8. **Registro legível de acessos, decisões e compartilhamentos** — `CAP-06-08`, `COM-0330` a `COM-0336`, `SCR-0048`, rota planejada `/community/privacy/registro-legivel-de-acessos-decisoes-e-compartilhamentos`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0281`–`COM-0336` possuem evidência;
- as oito famílias `SCR-0041`–`SCR-0048` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-106: Analytics de produto e impacto social

Objetivo:

Decisões orientadas a resultados humanos, não apenas tempo de tela ou volume.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-43-01` a `CAP-43-08`;
- requisitos: `COM-2353` a `COM-2408` — 56 itens;
- telas: `SCR-0337` a `SCR-0344` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-101`, `PKG-104`, `PKG-105`.

Entrega isolada:

- Ao fechar, o `PKG-106` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Métricas de sucesso de impressão e falha evitada** — `CAP-43-01`, `COM-2353` a `COM-2359`, `SCR-0337`, rota planejada `/community/analytics/metricas-de-sucesso-de-impressao-e-falha-evitada`.
2. **Métricas de aprendizagem, resolução e autonomia** — `CAP-43-02`, `COM-2360` a `COM-2366`, `SCR-0338`, rota planejada `/community/analytics/metricas-de-aprendizagem-resolucao-e-autonomia`.
3. **Métricas de reparo, resíduo, energia e vida útil** — `CAP-43-03`, `COM-2367` a `COM-2373`, `SCR-0339`, rota planejada `/community/analytics/metricas-de-reparo-residuo-energia-e-vida-util`.
4. **Métricas de inclusão por território sem reidentificação** — `CAP-43-04`, `COM-2374` a `COM-2380`, `SCR-0340`, rota planejada `/community/analytics/metricas-de-inclusao-por-territorio-sem-reidentificacao`.
5. **Funis de ativação com privacidade e consentimento** — `CAP-43-05`, `COM-2381` a `COM-2387`, `SCR-0341`, rota planejada `/community/analytics/funis-de-ativacao-com-privacidade-e-consentimento`.
6. **Experimentos com hipótese, risco e critério de parada** — `CAP-43-06`, `COM-2388` a `COM-2394`, `SCR-0342`, rota planejada `/community/analytics/experimentos-com-hipotese-risco-e-criterio-de-parada`.
7. **Painel público de impacto com metodologia** — `CAP-43-07`, `COM-2395` a `COM-2401`, `SCR-0343`, rota planejada `/community/analytics/painel-publico-de-impacto-com-metodologia`.
8. **Alertas contra métrica de vaidade e incentivo perverso** — `CAP-43-08`, `COM-2402` a `COM-2408`, `SCR-0344`, rota planejada `/community/analytics/alertas-contra-metrica-de-vaidade-e-incentivo-perverso`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2353`–`COM-2408` possuem evidência;
- as oito famílias `SCR-0337`–`SCR-0344` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-107: Moderação e segurança comunitária

Objetivo:

Redução de assédio, ódio, violência, exploração e circulação de conteúdo ilegal ou perigoso.

Prioridade social: P0.

Rastreabilidade integral:

- capacidades: `CAP-08-01` a `CAP-08-08`;
- requisitos: `COM-0393` a `COM-0448` — 56 itens;
- telas: `SCR-0057` a `SCR-0064` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-106`.

Entrega isolada:

- Ao fechar, o `PKG-107` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Regras comunitárias locais subordinadas à política global** — `CAP-08-01`, `COM-0393` a `COM-0399`, `SCR-0057`, rota planejada `/community/moderation/regras-comunitarias-locais-subordinadas-a-politica-global`.
2. **Fila priorizada por gravidade, alcance e vulnerabilidade** — `CAP-08-02`, `COM-0400` a `COM-0406`, `SCR-0058`, rota planejada `/community/moderation/fila-priorizada-por-gravidade-alcance-e-vulnerabilidade`.
3. **Moderação de texto, imagem, vídeo, áudio e arquivo 3d** — `CAP-08-03`, `COM-0407` a `COM-0413`, `SCR-0059`, rota planejada `/community/moderation/moderacao-de-texto-imagem-video-audio-e-arquivo-3d`.
4. **Equipes por idioma, região e conhecimento técnico** — `CAP-08-04`, `COM-0414` a `COM-0420`, `SCR-0060`, rota planejada `/community/moderation/equipes-por-idioma-regiao-e-conhecimento-tecnico`.
5. **Ações temporárias, graduais e reversíveis quando cabível** — `CAP-08-05`, `COM-0421` a `COM-0427`, `SCR-0061`, rota planejada `/community/moderation/acoes-temporarias-graduais-e-reversiveis-quando-cabivel`.
6. **Recurso independente com prazo e explicação** — `CAP-08-06`, `COM-0428` a `COM-0434`, `SCR-0062`, rota planejada `/community/moderation/recurso-independente-com-prazo-e-explicacao`.
7. **Proteção contra brigading, raids e perseguição coordenada** — `CAP-08-07`, `COM-0435` a `COM-0441`, `SCR-0063`, rota planejada `/community/moderation/protecao-contra-brigading-raids-e-perseguicao-coordenada`.
8. **Relatório periódico de transparência e qualidade decisória** — `CAP-08-08`, `COM-0442` a `COM-0448`, `SCR-0064`, rota planejada `/community/moderation/relatorio-periodico-de-transparencia-e-qualidade-decisoria`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0393`–`COM-0448` possuem evidência;
- as oito famílias `SCR-0057`–`SCR-0064` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-108: Integridade, confiança e combate a fraude

Objetivo:

Proteção da comunidade contra golpes, manipulação, falsificação e conteúdo artificial enganoso.

Prioridade social: P0.

Rastreabilidade integral:

- capacidades: `CAP-05-01` a `CAP-05-08`;
- requisitos: `COM-0225` a `COM-0280` — 56 itens;
- telas: `SCR-0033` a `SCR-0040` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-106`, `PKG-107`.

Entrega isolada:

- Ao fechar, o `PKG-108` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Verificação progressiva de identidade e papel técnico** — `CAP-05-01`, `COM-0225` a `COM-0231`, `SCR-0033`, rota planejada `/community/trust_integrity/verificacao-progressiva-de-identidade-e-papel-tecnico`.
2. **Proveniência de arquivo, imagem, vídeo e resultado de impressão** — `CAP-05-02`, `COM-0232` a `COM-0238`, `SCR-0034`, rota planejada `/community/trust_integrity/proveniencia-de-arquivo-imagem-video-e-resultado-de-impressao`.
3. **Rotulagem de conteúdo gerado ou alterado por ia** — `CAP-05-03`, `COM-0239` a `COM-0245`, `SCR-0035`, rota planejada `/community/trust_integrity/rotulagem-de-conteudo-gerado-ou-alterado-por-ia`.
4. **Detecção de avaliações, downloads e impressões coordenadas** — `CAP-05-04`, `COM-0246` a `COM-0252`, `SCR-0036`, rota planejada `/community/trust_integrity/deteccao-de-avaliacoes-downloads-e-impressoes-coordenadas`.
5. **Selo de teste físico com evidência reproduzível** — `CAP-05-05`, `COM-0253` a `COM-0259`, `SCR-0037`, rota planejada `/community/trust_integrity/selo-de-teste-fisico-com-evidencia-reproduzivel`.
6. **Contestação de autoria e titularidade com prazo** — `CAP-05-06`, `COM-0260` a `COM-0266`, `SCR-0038`, rota planejada `/community/trust_integrity/contestacao-de-autoria-e-titularidade-com-prazo`.
7. **Histórico público de sanções relevantes e recursos** — `CAP-05-07`, `COM-0267` a `COM-0273`, `SCR-0039`, rota planejada `/community/trust_integrity/historico-publico-de-sancoes-relevantes-e-recursos`.
8. **Transparência de recomendação, promoção e patrocínio** — `CAP-05-08`, `COM-0274` a `COM-0280`, `SCR-0040`, rota planejada `/community/trust_integrity/transparencia-de-recomendacao-promocao-e-patrocinio`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0225`–`COM-0280` possuem evidência;
- as oito famílias `SCR-0033`–`SCR-0040` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-109: Internacionalização e inclusão linguística

Objetivo:

Acesso global e preservação de conhecimento técnico local.

Prioridade social: P1.

Rastreabilidade integral:

- capacidades: `CAP-19-01` a `CAP-19-08`;
- requisitos: `COM-1009` a `COM-1064` — 56 itens;
- telas: `SCR-0145` a `SCR-0152` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-101`, `PKG-102`, `PKG-107`.

Entrega isolada:

- Ao fechar, o `PKG-109` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Interface traduzida com fallback e cobertura visível** — `CAP-19-01`, `COM-1009` a `COM-1015`, `SCR-0145`, rota planejada `/community/i18n/interface-traduzida-com-fallback-e-cobertura-visivel`.
2. **Conteúdo multilíngue por versão e autor** — `CAP-19-02`, `COM-1016` a `COM-1022`, `SCR-0146`, rota planejada `/community/i18n/conteudo-multilingue-por-versao-e-autor`.
3. **Tradução assistida com revisão comunitária** — `CAP-19-03`, `COM-1023` a `COM-1029`, `SCR-0147`, rota planejada `/community/i18n/traducao-assistida-com-revisao-comunitaria`.
4. **Glossário técnico por região e processo** — `CAP-19-04`, `COM-1030` a `COM-1036`, `SCR-0148`, rota planejada `/community/i18n/glossario-tecnico-por-regiao-e-processo`.
5. **Busca cruzada entre idiomas e sinônimos** — `CAP-19-05`, `COM-1037` a `COM-1043`, `SCR-0149`, rota planejada `/community/i18n/busca-cruzada-entre-idiomas-e-sinonimos`.
6. **Unidades, datas, moedas e normas locais** — `CAP-19-06`, `COM-1044` a `COM-1050`, `SCR-0150`, rota planejada `/community/i18n/unidades-datas-moedas-e-normas-locais`.
7. **Suporte a escrita bidirecional e fontes apropriadas** — `CAP-19-07`, `COM-1051` a `COM-1057`, `SCR-0151`, rota planejada `/community/i18n/suporte-a-escrita-bidirecional-e-fontes-apropriadas`.
8. **Preservação de idioma original e atribuição da tradução** — `CAP-19-08`, `COM-1058` a `COM-1064`, `SCR-0152`, rota planejada `/community/i18n/preservacao-de-idioma-original-e-atribuicao-da-traducao`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1009`–`COM-1064` possuem evidência;
- as oito famílias `SCR-0145`–`SCR-0152` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-110: Onboarding e ativação progressiva

Objetivo:

Entrada simples para iniciantes sem sacrificar profundidade para especialistas.

Prioridade social: P1.

Rastreabilidade integral:

- capacidades: `CAP-17-01` a `CAP-17-08`;
- requisitos: `COM-0897` a `COM-0952` — 56 itens;
- telas: `SCR-0129` a `SCR-0136` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-101`, `PKG-102`, `PKG-103`, `PKG-104`, `PKG-105`, `PKG-108`, `PKG-109`.

Entrega isolada:

- Ao fechar, o `PKG-110` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Escolha inicial de objetivos, experiência e equipamentos** — `CAP-17-01`, `COM-0897` a `COM-0903`, `SCR-0129`, rota planejada `/community/onboarding/escolha-inicial-de-objetivos-experiencia-e-equipamentos`.
2. **Tour adaptativo baseado no primeiro resultado desejado** — `CAP-17-02`, `COM-0904` a `COM-0910`, `SCR-0130`, rota planejada `/community/onboarding/tour-adaptativo-baseado-no-primeiro-resultado-desejado`.
3. **Checklist de perfil, impressora e primeiro projeto** — `CAP-17-03`, `COM-0911` a `COM-0917`, `SCR-0131`, rota planejada `/community/onboarding/checklist-de-perfil-impressora-e-primeiro-projeto`.
4. **Modo iniciante com termos explicados no contexto** — `CAP-17-04`, `COM-0918` a `COM-0924`, `SCR-0132`, rota planejada `/community/onboarding/modo-iniciante-com-termos-explicados-no-contexto`.
5. **Modo especialista com atalhos e densidade maior** — `CAP-17-05`, `COM-0925` a `COM-0931`, `SCR-0133`, rota planejada `/community/onboarding/modo-especialista-com-atalhos-e-densidade-maior`.
6. **Dados de exemplo removíveis e ambiente de treino** — `CAP-17-06`, `COM-0932` a `COM-0938`, `SCR-0134`, rota planejada `/community/onboarding/dados-de-exemplo-removiveis-e-ambiente-de-treino`.
7. **Retomada exata de fluxo interrompido em outro dispositivo** — `CAP-17-07`, `COM-0939` a `COM-0945`, `SCR-0135`, rota planejada `/community/onboarding/retomada-exata-de-fluxo-interrompido-em-outro-dispositivo`.
8. **Medição de tempo até primeiro valor sem dark patterns** — `CAP-17-08`, `COM-0946` a `COM-0952`, `SCR-0136`, rota planejada `/community/onboarding/medicao-de-tempo-ate-primeiro-valor-sem-dark-patterns`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0897`–`COM-0952` possuem evidência;
- as oito famílias `SCR-0129`–`SCR-0136` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-111: Segurança de modelos e uso responsável

Objetivo:

Redução de lesões, incêndios, falhas mecânicas e uso indevido de peças críticas.

Prioridade social: P0.

Rastreabilidade integral:

- capacidades: `CAP-02-01` a `CAP-02-08`;
- requisitos: `COM-0057` a `COM-0112` — 56 itens;
- telas: `SCR-0009` a `SCR-0016` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-106`, `PKG-107`, `PKG-108`.

Entrega isolada:

- Ao fechar, o `PKG-111` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Classificação de risco por finalidade do modelo** — `CAP-02-01`, `COM-0057` a `COM-0063`, `SCR-0009`, rota planejada `/community/safety_models/classificacao-de-risco-por-finalidade-do-modelo`.
2. **Bloqueio de promessas médicas ou estruturais sem evidência** — `CAP-02-02`, `COM-0064` a `COM-0070`, `SCR-0010`, rota planejada `/community/safety_models/bloqueio-de-promessas-medicas-ou-estruturais-sem-evidencia`.
3. **Checklist obrigatório para peças em contato com alimentos** — `CAP-02-03`, `COM-0071` a `COM-0077`, `SCR-0011`, rota planejada `/community/safety_models/checklist-obrigatorio-para-pecas-em-contato-com-alimentos`.
4. **Checklist obrigatório para peças infantis e brinquedos** — `CAP-02-04`, `COM-0078` a `COM-0084`, `SCR-0012`, rota planejada `/community/safety_models/checklist-obrigatorio-para-pecas-infantis-e-brinquedos`.
5. **Validação de temperatura, chama e isolamento elétrico** — `CAP-02-05`, `COM-0085` a `COM-0091`, `SCR-0013`, rota planejada `/community/safety_models/validacao-de-temperatura-chama-e-isolamento-eletrico`.
6. **Alerta de fadiga, carga, orientação e anisotropia** — `CAP-02-06`, `COM-0092` a `COM-0098`, `SCR-0014`, rota planejada `/community/safety_models/alerta-de-fadiga-carga-orientacao-e-anisotropia`.
7. **Recall comunitário de arquivo ou versão perigosa** — `CAP-02-07`, `COM-0099` a `COM-0105`, `SCR-0015`, rota planejada `/community/safety_models/recall-comunitario-de-arquivo-ou-versao-perigosa`.
8. **Trilha de incidentes e aprendizado sem exposição da vítima** — `CAP-02-08`, `COM-0106` a `COM-0112`, `SCR-0016`, rota planejada `/community/safety_models/trilha-de-incidentes-e-aprendizado-sem-exposicao-da-vitima`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0057`–`COM-0112` possuem evidência;
- as oito famílias `SCR-0009`–`SCR-0016` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-112: Proteção de crianças e adolescentes

Objetivo:

Ambiente seguro para aprendizagem maker, sem exploração, assédio ou exposição indevida.

Prioridade social: P0.

Rastreabilidade integral:

- capacidades: `CAP-04-01` a `CAP-04-08`;
- requisitos: `COM-0169` a `COM-0224` — 56 itens;
- telas: `SCR-0025` a `SCR-0032` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-106`, `PKG-107`, `PKG-108`, `PKG-109`, `PKG-110`.

Entrega isolada:

- Ao fechar, o `PKG-112` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Contas juvenis com supervisão e consentimento apropriados** — `CAP-04-01`, `COM-0169` a `COM-0175`, `SCR-0025`, rota planejada `/community/child_safety/contas-juvenis-com-supervisao-e-consentimento-apropriados`.
2. **Experiência por faixa etária e conteúdo adequado** — `CAP-04-02`, `COM-0176` a `COM-0182`, `SCR-0026`, rota planejada `/community/child_safety/experiencia-por-faixa-etaria-e-conteudo-adequado`.
3. **Mensagens privadas desativadas ou protegidas por padrão** — `CAP-04-03`, `COM-0183` a `COM-0189`, `SCR-0027`, rota planejada `/community/child_safety/mensagens-privadas-desativadas-ou-protegidas-por-padrao`.
4. **Detecção e escalonamento de aliciamento e exploração** — `CAP-04-04`, `COM-0190` a `COM-0196`, `SCR-0028`, rota planejada `/community/child_safety/deteccao-e-escalonamento-de-aliciamento-e-exploracao`.
5. **Ocultação de localização, escola e rotina pessoal** — `CAP-04-05`, `COM-0197` a `COM-0203`, `SCR-0029`, rota planejada `/community/child_safety/ocultacao-de-localizacao-escola-e-rotina-pessoal`.
6. **Moderação especializada e canal de ajuda acessível** — `CAP-04-06`, `COM-0204` a `COM-0210`, `SCR-0030`, rota planejada `/community/child_safety/moderacao-especializada-e-canal-de-ajuda-acessivel`.
7. **Projetos escolares com identidade coletiva opcional** — `CAP-04-07`, `COM-0211` a `COM-0217`, `SCR-0031`, rota planejada `/community/child_safety/projetos-escolares-com-identidade-coletiva-opcional`.
8. **Painel de responsáveis com controles proporcionais** — `CAP-04-08`, `COM-0218` a `COM-0224`, `SCR-0032`, rota planejada `/community/child_safety/painel-de-responsaveis-com-controles-proporcionais`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0169`–`COM-0224` possuem evidência;
- as oito famílias `SCR-0025`–`SCR-0032` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-113: Qualidade, metrologia e rastreabilidade

Objetivo:

Resultados físicos mais previsíveis, seguros e reproduzíveis.

Prioridade social: P1.

Rastreabilidade integral:

- capacidades: `CAP-16-01` a `CAP-16-08`;
- requisitos: `COM-0841` a `COM-0896` — 56 itens;
- telas: `SCR-0121` a `SCR-0128` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-106`, `PKG-111`.

Entrega isolada:

- Ao fechar, o `PKG-113` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Plano de inspeção por tipo de peça e risco** — `CAP-16-01`, `COM-0841` a `COM-0847`, `SCR-0121`, rota planejada `/community/quality/plano-de-inspecao-por-tipo-de-peca-e-risco`.
2. **Registro de medidas nominais, reais e tolerâncias** — `CAP-16-02`, `COM-0848` a `COM-0854`, `SCR-0122`, rota planejada `/community/quality/registro-de-medidas-nominais-reais-e-tolerancias`.
3. **Fotos padronizadas e evidência de acabamento** — `CAP-16-03`, `COM-0855` a `COM-0861`, `SCR-0123`, rota planejada `/community/quality/fotos-padronizadas-e-evidencia-de-acabamento`.
4. **Amostras de calibração vinculadas ao perfil usado** — `CAP-16-04`, `COM-0862` a `COM-0868`, `SCR-0124`, rota planejada `/community/quality/amostras-de-calibracao-vinculadas-ao-perfil-usado`.
5. **Rastreabilidade de máquina, material, lote e operador** — `CAP-16-05`, `COM-0869` a `COM-0875`, `SCR-0125`, rota planejada `/community/quality/rastreabilidade-de-maquina-material-lote-e-operador`.
6. **Controle estatístico de processo acessível** — `CAP-16-06`, `COM-0876` a `COM-0882`, `SCR-0126`, rota planejada `/community/quality/controle-estatistico-de-processo-acessivel`.
7. **Não conformidade, contenção e ação corretiva** — `CAP-16-07`, `COM-0883` a `COM-0889`, `SCR-0127`, rota planejada `/community/quality/nao-conformidade-contencao-e-acao-corretiva`.
8. **Certificado de fabricação verificável e exportável** — `CAP-16-08`, `COM-0890` a `COM-0896`, `SCR-0128`, rota planejada `/community/quality/certificado-de-fabricacao-verificavel-e-exportavel`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0841`–`COM-0896` possuem evidência;
- as oito famílias `SCR-0121`–`SCR-0128` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-114: Materiais, spools e ciência de processo

Objetivo:

Uso seguro e eficiente de materiais com conhecimento compartilhado.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-39-01` a `CAP-39-08`;
- requisitos: `COM-2129` a `COM-2184` — 56 itens;
- telas: `SCR-0305` a `SCR-0312` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-106`, `PKG-111`, `PKG-113`.

Entrega isolada:

- Ao fechar, o `PKG-114` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Catálogo de materiais, marcas, lotes e propriedades** — `CAP-39-01`, `COM-2129` a `COM-2135`, `SCR-0305`, rota planejada `/community/materials/catalogo-de-materiais-marcas-lotes-e-propriedades`.
2. **Inventário de spools com peso, cor, umidade e localização** — `CAP-39-02`, `COM-2136` a `COM-2142`, `SCR-0306`, rota planejada `/community/materials/inventario-de-spools-com-peso-cor-umidade-e-localizacao`.
3. **Identificação por qr, nfc e balança** — `CAP-39-03`, `COM-2143` a `COM-2149`, `SCR-0307`, rota planejada `/community/materials/identificacao-por-qr-nfc-e-balanca`.
4. **Compatibilidade de material com peça, máquina e ambiente** — `CAP-39-04`, `COM-2150` a `COM-2156`, `SCR-0308`, rota planejada `/community/materials/compatibilidade-de-material-com-peca-maquina-e-ambiente`.
5. **Secagem, armazenamento e validade guiados** — `CAP-39-05`, `COM-2157` a `COM-2163`, `SCR-0309`, rota planejada `/community/materials/secagem-armazenamento-e-validade-guiados`.
6. **Curvas de temperatura, fluxo e retração versionadas** — `CAP-39-06`, `COM-2164` a `COM-2170`, `SCR-0310`, rota planejada `/community/materials/curvas-de-temperatura-fluxo-e-retracao-versionadas`.
7. **Alertas de emissão, ventilação e descarte** — `CAP-39-07`, `COM-2171` a `COM-2177`, `SCR-0311`, rota planejada `/community/materials/alertas-de-emissao-ventilacao-e-descarte`.
8. **Troca, doação e reaproveitamento de sobras locais** — `CAP-39-08`, `COM-2178` a `COM-2184`, `SCR-0312`, rota planejada `/community/materials/troca-doacao-e-reaproveitamento-de-sobras-locais`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2129`–`COM-2184` possuem evidência;
- as oito famílias `SCR-0305`–`SCR-0312` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-115: Fabricação local e capacidade produtiva

Objetivo:

Geração de renda, resiliência de cadeias e produção distribuída próxima da demanda.

Prioridade social: P1.

Rastreabilidade integral:

- capacidades: `CAP-15-01` a `CAP-15-08`;
- requisitos: `COM-0785` a `COM-0840` — 56 itens;
- telas: `SCR-0113` a `SCR-0120` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-106`, `PKG-107`, `PKG-108`, `PKG-113`, `PKG-114`.

Entrega isolada:

- Ao fechar, o `PKG-115` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Mapa de capacidade por processo, material e tolerância** — `CAP-15-01`, `COM-0785` a `COM-0791`, `SCR-0113`, rota planejada `/community/local_manufacturing/mapa-de-capacidade-por-processo-material-e-tolerancia`.
2. **Pedido de fabricação com especificação verificável** — `CAP-15-02`, `COM-0792` a `COM-0798`, `SCR-0114`, rota planejada `/community/local_manufacturing/pedido-de-fabricacao-com-especificacao-verificavel`.
3. **Cotação transparente sem corrida predatória por preço** — `CAP-15-03`, `COM-0799` a `COM-0805`, `SCR-0115`, rota planejada `/community/local_manufacturing/cotacao-transparente-sem-corrida-predatoria-por-preco`.
4. **Roteamento por distância, capacidade e impacto** — `CAP-15-04`, `COM-0806` a `COM-0812`, `SCR-0116`, rota planejada `/community/local_manufacturing/roteamento-por-distancia-capacidade-e-impacto`.
5. **Controle de lote, amostra, inspeção e não conformidade** — `CAP-15-05`, `COM-0813` a `COM-0819`, `SCR-0117`, rota planejada `/community/local_manufacturing/controle-de-lote-amostra-inspecao-e-nao-conformidade`.
6. **Cadeia de custódia de arquivo e propriedade intelectual** — `CAP-15-06`, `COM-0820` a `COM-0826`, `SCR-0118`, rota planejada `/community/local_manufacturing/cadeia-de-custodia-de-arquivo-e-propriedade-intelectual`.
7. **Pagamento por marco com proteção a ambas as partes** — `CAP-15-07`, `COM-0827` a `COM-0833`, `SCR-0119`, rota planejada `/community/local_manufacturing/pagamento-por-marco-com-protecao-a-ambas-as-partes`.
8. **Painel de renda local, prazo, qualidade e inclusão** — `CAP-15-08`, `COM-0834` a `COM-0840`, `SCR-0120`, rota planejada `/community/local_manufacturing/painel-de-renda-local-prazo-qualidade-e-inclusao`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0785`–`COM-0840` possuem evidência;
- as oito famílias `SCR-0113`–`SCR-0120` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-116: Tecnologia assistiva e autonomia

Objetivo:

Saúde, autonomia, inclusão e participação de pessoas com deficiência ou mobilidade reduzida.

Prioridade social: P0.

Rastreabilidade integral:

- capacidades: `CAP-01-01` a `CAP-01-08`;
- requisitos: `COM-0001` a `COM-0056` — 56 itens;
- telas: `SCR-0001` a `SCR-0008` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-102`, `PKG-103`, `PKG-104`, `PKG-105`, `PKG-106`, `PKG-107`, `PKG-108`, `PKG-111`, `PKG-113`, `PKG-114`, `PKG-115`.

Entrega isolada:

- Ao fechar, o `PKG-116` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Catálogo validado de dispositivos assistivos imprimíveis** — `CAP-01-01`, `COM-0001` a `COM-0007`, `SCR-0001`, rota planejada `/community/assistive/catalogo-validado-de-dispositivos-assistivos-imprimiveis`.
2. **Coautoria obrigatória com usuários finais e especialistas** — `CAP-01-02`, `COM-0008` a `COM-0014`, `SCR-0002`, rota planejada `/community/assistive/coautoria-obrigatoria-com-usuarios-finais-e-especialistas`.
3. **Fluxo de medidas corporais com consentimento e minimização** — `CAP-01-03`, `COM-0015` a `COM-0021`, `SCR-0003`, rota planejada `/community/assistive/fluxo-de-medidas-corporais-com-consentimento-e-minimizacao`.
4. **Níveis de evidência clínica e limites de uso** — `CAP-01-04`, `COM-0022` a `COM-0028`, `SCR-0004`, rota planejada `/community/assistive/niveis-de-evidencia-clinica-e-limites-de-uso`.
5. **Rede local de fabricação, ajuste e acompanhamento** — `CAP-01-05`, `COM-0029` a `COM-0035`, `SCR-0005`, rota planejada `/community/assistive/rede-local-de-fabricacao-ajuste-e-acompanhamento`.
6. **Alertas de contraindicação, material e carga mecânica** — `CAP-01-06`, `COM-0036` a `COM-0042`, `SCR-0006`, rota planejada `/community/assistive/alertas-de-contraindicacao-material-e-carga-mecanica`.
7. **Programa de subsídio e doação rastreável** — `CAP-01-07`, `COM-0043` a `COM-0049`, `SCR-0007`, rota planejada `/community/assistive/programa-de-subsidio-e-doacao-rastreavel`.
8. **Registro longitudinal de conforto, segurança e resultado** — `CAP-01-08`, `COM-0050` a `COM-0056`, `SCR-0008`, rota planejada `/community/assistive/registro-longitudinal-de-conforto-seguranca-e-resultado`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0001`–`COM-0056` possuem evidência;
- as oito famílias `SCR-0001`–`SCR-0008` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-117: Resposta humanitária e resiliência local

Objetivo:

Capacidade local de responder a emergências com peças apropriadas, seguras e coordenadas.

Prioridade social: P0.

Rastreabilidade integral:

- capacidades: `CAP-03-01` a `CAP-03-08`;
- requisitos: `COM-0113` a `COM-0168` — 56 itens;
- telas: `SCR-0017` a `SCR-0024` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-103`, `PKG-104`, `PKG-105`, `PKG-106`, `PKG-107`, `PKG-108`, `PKG-109`, `PKG-111`, `PKG-113`, `PKG-114`, `PKG-115`.

Entrega isolada:

- Ao fechar, o `PKG-117` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Modo de emergência ativado por autoridade ou parceiro verificado** — `CAP-03-01`, `COM-0113` a `COM-0119`, `SCR-0017`, rota planejada `/community/humanitarian/modo-de-emergencia-ativado-por-autoridade-ou-parceiro-verificado`.
2. **Catálogo offline de itens humanitários pré-validados** — `CAP-03-02`, `COM-0120` a `COM-0126`, `SCR-0018`, rota planejada `/community/humanitarian/catalogo-offline-de-itens-humanitarios-pre-validados`.
3. **Mapa de demanda, capacidade, materiais e energia disponíveis** — `CAP-03-03`, `COM-0127` a `COM-0133`, `SCR-0019`, rota planejada `/community/humanitarian/mapa-de-demanda-capacidade-materiais-e-energia-disponiveis`.
4. **Coordenação de lotes entre oficinas e voluntários** — `CAP-03-04`, `COM-0134` a `COM-0140`, `SCR-0020`, rota planejada `/community/humanitarian/coordenacao-de-lotes-entre-oficinas-e-voluntarios`.
5. **Controle de qualidade por amostragem e cadeia de custódia** — `CAP-03-05`, `COM-0141` a `COM-0147`, `SCR-0021`, rota planejada `/community/humanitarian/controle-de-qualidade-por-amostragem-e-cadeia-de-custodia`.
6. **Instruções multilíngues de fabricação e uso em campo** — `CAP-03-06`, `COM-0148` a `COM-0154`, `SCR-0022`, rota planejada `/community/humanitarian/instrucoes-multilingues-de-fabricacao-e-uso-em-campo`.
7. **Priorização ética sem leilão ou exploração de escassez** — `CAP-03-07`, `COM-0155` a `COM-0161`, `SCR-0023`, rota planejada `/community/humanitarian/priorizacao-etica-sem-leilao-ou-exploracao-de-escassez`.
8. **Encerramento de missão com prestação de contas e lições** — `CAP-03-08`, `COM-0162` a `COM-0168`, `SCR-0024`, rota planejada `/community/humanitarian/encerramento-de-missao-com-prestacao-de-contas-e-licoes`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0113`–`COM-0168` possuem evidência;
- as oito famílias `SCR-0017`–`SCR-0024` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-118: Educação maker e aprendizagem ao longo da vida

Objetivo:

Formação técnica acessível, pensamento crítico e ampliação de oportunidades educacionais.

Prioridade social: P1.

Rastreabilidade integral:

- capacidades: `CAP-11-01` a `CAP-11-08`;
- requisitos: `COM-0561` a `COM-0616` — 56 itens;
- telas: `SCR-0081` a `SCR-0088` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-102`, `PKG-103`, `PKG-106`, `PKG-107`, `PKG-109`, `PKG-110`, `PKG-111`.

Entrega isolada:

- Ao fechar, o `PKG-118` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Trilhas do primeiro modelo à fabricação avançada** — `CAP-11-01`, `COM-0561` a `COM-0567`, `SCR-0081`, rota planejada `/community/education/trilhas-do-primeiro-modelo-a-fabricacao-avancada`.
2. **Aulas passo a passo com arquivos e checkpoints** — `CAP-11-02`, `COM-0568` a `COM-0574`, `SCR-0082`, rota planejada `/community/education/aulas-passo-a-passo-com-arquivos-e-checkpoints`.
3. **Laboratórios virtuais de cad, slicing e diagnóstico** — `CAP-11-03`, `COM-0575` a `COM-0581`, `SCR-0083`, rota planejada `/community/education/laboratorios-virtuais-de-cad-slicing-e-diagnostico`.
4. **Avaliação prática por evidência de projeto** — `CAP-11-04`, `COM-0582` a `COM-0588`, `SCR-0084`, rota planejada `/community/education/avaliacao-pratica-por-evidencia-de-projeto`.
5. **Mentoria entre pares com salvaguardas** — `CAP-11-05`, `COM-0589` a `COM-0595`, `SCR-0085`, rota planejada `/community/education/mentoria-entre-pares-com-salvaguardas`.
6. **Formação de educadores e planos de aula abertos** — `CAP-11-06`, `COM-0596` a `COM-0602`, `SCR-0086`, rota planejada `/community/education/formacao-de-educadores-e-planos-de-aula-abertos`.
7. **Certificados verificáveis baseados em competência** — `CAP-11-07`, `COM-0603` a `COM-0609`, `SCR-0087`, rota planejada `/community/education/certificados-verificaveis-baseados-em-competencia`.
8. **Biblioteca de erros reais e recuperação guiada** — `CAP-11-08`, `COM-0610` a `COM-0616`, `SCR-0088`, rota planejada `/community/education/biblioteca-de-erros-reais-e-recuperacao-guiada`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0561`–`COM-0616` possuem evidência;
- as oito famílias `SCR-0081`–`SCR-0088` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-119: Escolas, bibliotecas e makerspaces

Objetivo:

Democratização de infraestrutura de fabricação e fortalecimento de centros comunitários de aprendizagem.

Prioridade social: P1.

Rastreabilidade integral:

- capacidades: `CAP-12-01` a `CAP-12-08`;
- requisitos: `COM-0617` a `COM-0672` — 56 itens;
- telas: `SCR-0089` a `SCR-0096` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-112`, `PKG-113`, `PKG-115`, `PKG-118`.

Entrega isolada:

- Ao fechar, o `PKG-119` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Perfil institucional com turmas, oficinas e equipamentos** — `CAP-12-01`, `COM-0617` a `COM-0623`, `SCR-0089`, rota planejada `/community/schools/perfil-institucional-com-turmas-oficinas-e-equipamentos`.
2. **Reserva de máquina, espaço e instrutor** — `CAP-12-02`, `COM-0624` a `COM-0630`, `SCR-0090`, rota planejada `/community/schools/reserva-de-maquina-espaco-e-instrutor`.
3. **Fila pedagógica com aprovação e limites de material** — `CAP-12-03`, `COM-0631` a `COM-0637`, `SCR-0091`, rota planejada `/community/schools/fila-pedagogica-com-aprovacao-e-limites-de-material`.
4. **Contas de turma sem coleta excessiva de dados** — `CAP-12-04`, `COM-0638` a `COM-0644`, `SCR-0092`, rota planejada `/community/schools/contas-de-turma-sem-coleta-excessiva-de-dados`.
5. **Inventário compartilhado e manutenção preventiva** — `CAP-12-05`, `COM-0645` a `COM-0651`, `SCR-0093`, rota planejada `/community/schools/inventario-compartilhado-e-manutencao-preventiva`.
6. **Currículo, projetos e resultados públicos opcionais** — `CAP-12-06`, `COM-0652` a `COM-0658`, `SCR-0094`, rota planejada `/community/schools/curriculo-projetos-e-resultados-publicos-opcionais`.
7. **Rede de empréstimo de ferramentas e componentes** — `CAP-12-07`, `COM-0659` a `COM-0665`, `SCR-0095`, rota planejada `/community/schools/rede-de-emprestimo-de-ferramentas-e-componentes`.
8. **Painel de inclusão, alcance territorial e aprendizagem** — `CAP-12-08`, `COM-0666` a `COM-0672`, `SCR-0096`, rota planejada `/community/schools/painel-de-inclusao-alcance-territorial-e-aprendizagem`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0617`–`COM-0672` possuem evidência;
- as oito famílias `SCR-0089`–`SCR-0096` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-120: Reparo, peças de reposição e economia circular

Objetivo:

Extensão da vida útil de produtos, redução de resíduos e acesso local a reparos.

Prioridade social: P1.

Rastreabilidade integral:

- capacidades: `CAP-13-01` a `CAP-13-08`;
- requisitos: `COM-0673` a `COM-0728` — 56 itens;
- telas: `SCR-0097` a `SCR-0104` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-106`, `PKG-111`, `PKG-113`, `PKG-114`, `PKG-115`.

Entrega isolada:

- Ao fechar, o `PKG-120` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Catálogo por produto, peça, revisão e compatibilidade** — `CAP-13-01`, `COM-0673` a `COM-0679`, `SCR-0097`, rota planejada `/community/repair/catalogo-por-produto-peca-revisao-e-compatibilidade`.
2. **Busca por foto, medidas, código e sintoma** — `CAP-13-02`, `COM-0680` a `COM-0686`, `SCR-0098`, rota planejada `/community/repair/busca-por-foto-medidas-codigo-e-sintoma`.
3. **Manual de desmontagem, risco e remontagem** — `CAP-13-03`, `COM-0687` a `COM-0693`, `SCR-0099`, rota planejada `/community/repair/manual-de-desmontagem-risco-e-remontagem`.
4. **Rede de reparadores e oficinas verificadas** — `CAP-13-04`, `COM-0694` a `COM-0700`, `SCR-0100`, rota planejada `/community/repair/rede-de-reparadores-e-oficinas-verificadas`.
5. **Passaporte de reparo e histórico do objeto** — `CAP-13-05`, `COM-0701` a `COM-0707`, `SCR-0101`, rota planejada `/community/repair/passaporte-de-reparo-e-historico-do-objeto`.
6. **Comparação entre imprimir, comprar, usinar ou reutilizar** — `CAP-13-06`, `COM-0708` a `COM-0714`, `SCR-0102`, rota planejada `/community/repair/comparacao-entre-imprimir-comprar-usinar-ou-reutilizar`.
7. **Incentivo a design reparável e peças abertas** — `CAP-13-07`, `COM-0715` a `COM-0721`, `SCR-0103`, rota planejada `/community/repair/incentivo-a-design-reparavel-e-pecas-abertas`.
8. **Indicadores de resíduos evitados e vida útil ampliada** — `CAP-13-08`, `COM-0722` a `COM-0728`, `SCR-0104`, rota planejada `/community/repair/indicadores-de-residuos-evitados-e-vida-util-ampliada`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0673`–`COM-0728` possuem evidência;
- as oito famílias `SCR-0097`–`SCR-0104` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-121: Sustentabilidade e uso responsável de materiais

Objetivo:

Menos desperdício, energia e emissões, com decisões ambientais verificáveis.

Prioridade social: P1.

Rastreabilidade integral:

- capacidades: `CAP-14-01` a `CAP-14-08`;
- requisitos: `COM-0729` a `COM-0784` — 56 itens;
- telas: `SCR-0105` a `SCR-0112` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-106`, `PKG-113`, `PKG-114`, `PKG-115`, `PKG-120`.

Entrega isolada:

- Ao fechar, o `PKG-121` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Estimativa de material, energia, suporte e falha evitável** — `CAP-14-01`, `COM-0729` a `COM-0735`, `SCR-0105`, rota planejada `/community/sustainability/estimativa-de-material-energia-suporte-e-falha-evitavel`.
2. **Comparação ambiental entre variantes de impressão** — `CAP-14-02`, `COM-0736` a `COM-0742`, `SCR-0106`, rota planejada `/community/sustainability/comparacao-ambiental-entre-variantes-de-impressao`.
3. **Passaporte de material e origem do filamento** — `CAP-14-03`, `COM-0743` a `COM-0749`, `SCR-0107`, rota planejada `/community/sustainability/passaporte-de-material-e-origem-do-filamento`.
4. **Rede de coleta, reciclagem e reaproveitamento local** — `CAP-14-04`, `COM-0750` a `COM-0756`, `SCR-0108`, rota planejada `/community/sustainability/rede-de-coleta-reciclagem-e-reaproveitamento-local`.
5. **Biblioteca de perfis para material reciclado** — `CAP-14-05`, `COM-0757` a `COM-0763`, `SCR-0109`, rota planejada `/community/sustainability/biblioteca-de-perfis-para-material-reciclado`.
6. **Metas pessoais e institucionais de redução de desperdício** — `CAP-14-06`, `COM-0764` a `COM-0770`, `SCR-0110`, rota planejada `/community/sustainability/metas-pessoais-e-institucionais-de-reducao-de-desperdicio`.
7. **Alertas contra greenwashing e métricas não comparáveis** — `CAP-14-07`, `COM-0771` a `COM-0777`, `SCR-0111`, rota planejada `/community/sustainability/alertas-contra-greenwashing-e-metricas-nao-comparaveis`.
8. **Relatório de impacto ambiental por projeto e comunidade** — `CAP-14-08`, `COM-0778` a `COM-0784`, `SCR-0112`, rota planejada `/community/sustainability/relatorio-de-impacto-ambiental-por-projeto-e-comunidade`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-0729`–`COM-0784` possuem evidência;
- as oito famílias `SCR-0105`–`SCR-0112` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-122: Identidade, perfil e presença avançada

Objetivo:

Representação autêntica de makers, organizações e especialidades.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-28-01` a `CAP-28-08`;
- requisitos: `COM-1513` a `COM-1568` — 56 itens;
- telas: `SCR-0217` a `SCR-0224` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-108`, `PKG-109`, `PKG-110`.

Entrega isolada:

- Ao fechar, o `PKG-122` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Perfil modular com portfólio, habilidades e disponibilidade** — `CAP-28-01`, `COM-1513` a `COM-1519`, `SCR-0217`, rota planejada `/community/identity/perfil-modular-com-portfolio-habilidades-e-disponibilidade`.
2. **Identidades pessoal, profissional, educativa e pseudônima** — `CAP-28-02`, `COM-1520` a `COM-1526`, `SCR-0218`, rota planejada `/community/identity/identidades-pessoal-profissional-educativa-e-pseudonima`.
3. **Pronomes, nome social e campos culturais opcionais** — `CAP-28-03`, `COM-1527` a `COM-1533`, `SCR-0219`, rota planejada `/community/identity/pronomes-nome-social-e-campos-culturais-opcionais`.
4. **Destaques, posts fixados e coleção de apresentação** — `CAP-28-04`, `COM-1534` a `COM-1540`, `SCR-0220`, rota planejada `/community/identity/destaques-posts-fixados-e-colecao-de-apresentacao`.
5. **Currículo maker verificável por projetos e contribuições** — `CAP-28-05`, `COM-1541` a `COM-1547`, `SCR-0221`, rota planejada `/community/identity/curriculo-maker-verificavel-por-projetos-e-contribuicoes`.
6. **Status de contratação, mentoria, colaboração e encomenda** — `CAP-28-06`, `COM-1548` a `COM-1554`, `SCR-0222`, rota planejada `/community/identity/status-de-contratacao-mentoria-colaboracao-e-encomenda`.
7. **Qr code e cartão público compartilhável** — `CAP-28-07`, `COM-1555` a `COM-1561`, `SCR-0223`, rota planejada `/community/identity/qr-code-e-cartao-publico-compartilhavel`.
8. **Memorialização, herança e encerramento de conta** — `CAP-28-08`, `COM-1562` a `COM-1568`, `SCR-0224`, rota planejada `/community/identity/memorializacao-heranca-e-encerramento-de-conta`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1513`–`COM-1568` possuem evidência;
- as oito famílias `SCR-0217`–`SCR-0224` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-123: Grafo social e relações contextuais

Objetivo:

Conexões úteis baseadas em confiança, interesse e colaboração real.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-29-01` a `CAP-29-08`;
- requisitos: `COM-1569` a `COM-1624` — 56 itens;
- telas: `SCR-0225` a `SCR-0232` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-107`, `PKG-108`, `PKG-122`.

Entrega isolada:

- Ao fechar, o `PKG-123` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Seguir tema, tag, impressora, projeto e organização** — `CAP-29-01`, `COM-1569` a `COM-1575`, `SCR-0225`, rota planejada `/community/social_graph/seguir-tema-tag-impressora-projeto-e-organizacao`.
2. **Círculos privados para organizar relações** — `CAP-29-02`, `COM-1576` a `COM-1582`, `SCR-0226`, rota planejada `/community/social_graph/circulos-privados-para-organizar-relacoes`.
3. **Conexão por colaboração, mentoria e fabricação** — `CAP-29-03`, `COM-1583` a `COM-1589`, `SCR-0227`, rota planejada `/community/social_graph/conexao-por-colaboracao-mentoria-e-fabricacao`.
4. **Contatos próximos com compartilhamento específico** — `CAP-29-04`, `COM-1590` a `COM-1596`, `SCR-0228`, rota planejada `/community/social_graph/contatos-proximos-com-compartilhamento-especifico`.
5. **Sugestões explicadas por contexto comum** — `CAP-29-05`, `COM-1597` a `COM-1603`, `SCR-0229`, rota planejada `/community/social_graph/sugestoes-explicadas-por-contexto-comum`.
6. **Remoção silenciosa, restrição e silenciamento granular** — `CAP-29-06`, `COM-1604` a `COM-1610`, `SCR-0230`, rota planejada `/community/social_graph/remocao-silenciosa-restricao-e-silenciamento-granular`.
7. **Importação de contatos com consentimento bilateral** — `CAP-29-07`, `COM-1611` a `COM-1617`, `SCR-0231`, rota planejada `/community/social_graph/importacao-de-contatos-com-consentimento-bilateral`.
8. **Visualização privada do próprio grafo e lacunas de rede** — `CAP-29-08`, `COM-1618` a `COM-1624`, `SCR-0232`, rota planejada `/community/social_graph/visualizacao-privada-do-proprio-grafo-e-lacunas-de-rede`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1569`–`COM-1624` possuem evidência;
- as oito famílias `SCR-0225`–`SCR-0232` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-124: Comunidades avançadas e governança local

Objetivo:

Pertencimento, cooperação e autonomia comunitária com responsabilidade.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-20-01` a `CAP-20-08`;
- requisitos: `COM-1065` a `COM-1120` — 56 itens;
- telas: `SCR-0153` a `SCR-0160` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-107`, `PKG-108`, `PKG-109`, `PKG-122`, `PKG-123`.

Entrega isolada:

- Ao fechar, o `PKG-124` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Comunidades criadas por tema, território e finalidade** — `CAP-20-01`, `COM-1065` a `COM-1071`, `SCR-0153`, rota planejada `/community/communities/comunidades-criadas-por-tema-territorio-e-finalidade`.
2. **Canais de fórum, chat, anúncios, recursos e projetos** — `CAP-20-02`, `COM-1072` a `COM-1078`, `SCR-0154`, rota planejada `/community/communities/canais-de-forum-chat-anuncios-recursos-e-projetos`.
3. **Papéis e permissões comunitárias configuráveis** — `CAP-20-03`, `COM-1079` a `COM-1085`, `SCR-0155`, rota planejada `/community/communities/papeis-e-permissoes-comunitarias-configuraveis`.
4. **Onboarding por interesses, regras e canais** — `CAP-20-04`, `COM-1086` a `COM-1092`, `SCR-0156`, rota planejada `/community/communities/onboarding-por-interesses-regras-e-canais`.
5. **Wiki, faq e base de conhecimento mantida pela comunidade** — `CAP-20-05`, `COM-1093` a `COM-1099`, `SCR-0157`, rota planejada `/community/communities/wiki-faq-e-base-de-conhecimento-mantida-pela-comunidade`.
6. **Propostas, enquetes e decisões com histórico** — `CAP-20-06`, `COM-1100` a `COM-1106`, `SCR-0158`, rota planejada `/community/communities/propostas-enquetes-e-decisoes-com-historico`.
7. **Saúde da comunidade, retenção e carga de moderação** — `CAP-20-07`, `COM-1107` a `COM-1113`, `SCR-0159`, rota planejada `/community/communities/saude-da-comunidade-retencao-e-carga-de-moderacao`.
8. **Fusão, arquivamento e sucessão de administradores** — `CAP-20-08`, `COM-1114` a `COM-1120`, `SCR-0160`, rota planejada `/community/communities/fusao-arquivamento-e-sucessao-de-administradores`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1065`–`COM-1120` possuem evidência;
- as oito famílias `SCR-0153`–`SCR-0160` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-125: Publicação rica e narrativa de fabricação

Objetivo:

Conhecimento reproduzível em vez de posts superficiais.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-30-01` a `CAP-30-08`;
- requisitos: `COM-1625` a `COM-1680` — 56 itens;
- telas: `SCR-0233` a `SCR-0240` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-101`, `PKG-102`, `PKG-103`, `PKG-105`, `PKG-107`, `PKG-108`, `PKG-109`, `PKG-122`, `PKG-124`.

Entrega isolada:

- Ao fechar, o `PKG-125` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Editor em blocos para texto, foto, vídeo, arquivo e etapa** — `CAP-30-01`, `COM-1625` a `COM-1631`, `SCR-0233`, rota planejada `/community/publishing/editor-em-blocos-para-texto-foto-video-arquivo-e-etapa`.
2. **Rascunho automático, revisão e publicação agendada** — `CAP-30-02`, `COM-1632` a `COM-1638`, `SCR-0234`, rota planejada `/community/publishing/rascunho-automatico-revisao-e-publicacao-agendada`.
3. **Templates para dúvida, tutorial, make, falha e estudo** — `CAP-30-03`, `COM-1639` a `COM-1645`, `SCR-0235`, rota planejada `/community/publishing/templates-para-duvida-tutorial-make-falha-e-estudo`.
4. **Passo a passo com materiais, ferramentas e tempo** — `CAP-30-04`, `COM-1646` a `COM-1652`, `SCR-0236`, rota planejada `/community/publishing/passo-a-passo-com-materiais-ferramentas-e-tempo`.
5. **Anotação de imagem, vídeo e visualização 3d** — `CAP-30-05`, `COM-1653` a `COM-1659`, `SCR-0237`, rota planejada `/community/publishing/anotacao-de-imagem-video-e-visualizacao-3d`.
6. **Coautoria, tradução e republicação autorizada** — `CAP-30-06`, `COM-1660` a `COM-1666`, `SCR-0238`, rota planejada `/community/publishing/coautoria-traducao-e-republicacao-autorizada`.
7. **Histórico de edição e comparação de versões** — `CAP-30-07`, `COM-1667` a `COM-1673`, `SCR-0239`, rota planejada `/community/publishing/historico-de-edicao-e-comparacao-de-versoes`.
8. **Exportação aberta e preservação de links** — `CAP-30-08`, `COM-1674` a `COM-1680`, `SCR-0240`, rota planejada `/community/publishing/exportacao-aberta-e-preservacao-de-links`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1625`–`COM-1680` possuem evidência;
- as oito famílias `SCR-0233`–`SCR-0240` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-126: Conhecimento técnico e suporte estruturado

Objetivo:

Redução de retrabalho e democratização de conhecimento confiável.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-24-01` a `CAP-24-08`;
- requisitos: `COM-1289` a `COM-1344` — 56 itens;
- telas: `SCR-0185` a `SCR-0192` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-109`, `PKG-118`, `PKG-124`, `PKG-125`.

Entrega isolada:

- Ao fechar, o `PKG-126` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Perguntas e respostas com solução e versões afetadas** — `CAP-24-01`, `COM-1289` a `COM-1295`, `SCR-0185`, rota planejada `/community/knowledge/perguntas-e-respostas-com-solucao-e-versoes-afetadas`.
2. **Árvore de diagnóstico guiada por sintoma** — `CAP-24-02`, `COM-1296` a `COM-1302`, `SCR-0186`, rota planejada `/community/knowledge/arvore-de-diagnostico-guiada-por-sintoma`.
3. **Artigos versionados com revisão técnica** — `CAP-24-03`, `COM-1303` a `COM-1309`, `SCR-0187`, rota planejada `/community/knowledge/artigos-versionados-com-revisao-tecnica`.
4. **Runbooks comunitários por hardware e software** — `CAP-24-04`, `COM-1310` a `COM-1316`, `SCR-0188`, rota planejada `/community/knowledge/runbooks-comunitarios-por-hardware-e-software`.
5. **Duplicidade sugerida antes de publicar dúvida** — `CAP-24-05`, `COM-1317` a `COM-1323`, `SCR-0189`, rota planejada `/community/knowledge/duplicidade-sugerida-antes-de-publicar-duvida`.
6. **Resumo de discussão com fontes e incertezas** — `CAP-24-06`, `COM-1324` a `COM-1330`, `SCR-0190`, rota planejada `/community/knowledge/resumo-de-discussao-com-fontes-e-incertezas`.
7. **Escalonamento para especialista ou fabricante** — `CAP-24-07`, `COM-1331` a `COM-1337`, `SCR-0191`, rota planejada `/community/knowledge/escalonamento-para-especialista-ou-fabricante`.
8. **Qualidade da resposta medida por resolução confirmada** — `CAP-24-08`, `COM-1338` a `COM-1344`, `SCR-0192`, rota planejada `/community/knowledge/qualidade-da-resposta-medida-por-resolucao-confirmada`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1289`–`COM-1344` possuem evidência;
- as oito famílias `SCR-0185`–`SCR-0192` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-127: Fotos, vídeo, live e mídia técnica

Objetivo:

Demonstração visual de processo, falha, aprendizado e resultado físico.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-31-01` a `CAP-31-08`;
- requisitos: `COM-1681` a `COM-1736` — 56 itens;
- telas: `SCR-0241` a `SCR-0248` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-107`, `PKG-108`, `PKG-125`.

Entrega isolada:

- Ao fechar, o `PKG-127` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Upload e processamento resiliente de imagem e vídeo** — `CAP-31-01`, `COM-1681` a `COM-1687`, `SCR-0241`, rota planejada `/community/media/upload-e-processamento-resiliente-de-imagem-e-video`.
2. **Álbuns de progresso, before/after e timelapse** — `CAP-31-02`, `COM-1688` a `COM-1694`, `SCR-0242`, rota planejada `/community/media/albuns-de-progresso-before-after-e-timelapse`.
3. **Vídeo curto técnico com capítulos e arquivos relacionados** — `CAP-31-03`, `COM-1695` a `COM-1701`, `SCR-0243`, rota planejada `/community/media/video-curto-tecnico-com-capitulos-e-arquivos-relacionados`.
4. **Live de impressão, oficina e aula com baixa latência** — `CAP-31-04`, `COM-1702` a `COM-1708`, `SCR-0244`, rota planejada `/community/media/live-de-impressao-oficina-e-aula-com-baixa-latencia`.
5. **Marcadores temporais para falha, ajuste e resultado** — `CAP-31-05`, `COM-1709` a `COM-1715`, `SCR-0245`, rota planejada `/community/media/marcadores-temporais-para-falha-ajuste-e-resultado`.
6. **Legendas, transcrição, tradução e audiodescrição** — `CAP-31-06`, `COM-1716` a `COM-1722`, `SCR-0246`, rota planejada `/community/media/legendas-transcricao-traducao-e-audiodescricao`.
7. **Proteção de rosto, endereço, tela e metadados sensíveis** — `CAP-31-07`, `COM-1723` a `COM-1729`, `SCR-0247`, rota planejada `/community/media/protecao-de-rosto-endereco-tela-e-metadados-sensiveis`.
8. **Download original ou otimizado conforme licença** — `CAP-31-08`, `COM-1730` a `COM-1736`, `SCR-0248`, rota planejada `/community/media/download-original-ou-otimizado-conforme-licenca`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1681`–`COM-1736` possuem evidência;
- as oito famílias `SCR-0241`–`SCR-0248` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-128: Biblioteca 3D profissional e gestão de ativos

Objetivo:

Arquivos confiáveis, organizados, compatíveis e reutilizáveis ao longo do tempo.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-32-01` a `CAP-32-08`;
- requisitos: `COM-1737` a `COM-1792` — 56 itens;
- telas: `SCR-0249` a `SCR-0256` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-111`, `PKG-113`, `PKG-114`, `PKG-125`, `PKG-127`.

Entrega isolada:

- Ao fechar, o `PKG-128` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Estrutura de projeto com peças, conjuntos e variantes** — `CAP-32-01`, `COM-1737` a `COM-1743`, `SCR-0249`, rota planejada `/community/models/estrutura-de-projeto-com-pecas-conjuntos-e-variantes`.
2. **Suporte ampliado a step, cad nativo, svg e documentação** — `CAP-32-02`, `COM-1744` a `COM-1750`, `SCR-0250`, rota planejada `/community/models/suporte-ampliado-a-step-cad-nativo-svg-e-documentacao`.
3. **Dependências entre arquivos, hardware e consumíveis** — `CAP-32-03`, `COM-1751` a `COM-1757`, `SCR-0251`, rota planejada `/community/models/dependencias-entre-arquivos-hardware-e-consumiveis`.
4. **Metadados técnicos obrigatórios por finalidade** — `CAP-32-04`, `COM-1758` a `COM-1764`, `SCR-0252`, rota planejada `/community/models/metadados-tecnicos-obrigatorios-por-finalidade`.
5. **Diff geométrico e de metadados entre versões** — `CAP-32-05`, `COM-1765` a `COM-1771`, `SCR-0253`, rota planejada `/community/models/diff-geometrico-e-de-metadados-entre-versoes`.
6. **Artefatos derivados reproduzíveis e assinados** — `CAP-32-06`, `COM-1772` a `COM-1778`, `SCR-0254`, rota planejada `/community/models/artefatos-derivados-reproduziveis-e-assinados`.
7. **Espelhamento e preservação de projetos abandonados** — `CAP-32-07`, `COM-1779` a `COM-1785`, `SCR-0255`, rota planejada `/community/models/espelhamento-e-preservacao-de-projetos-abandonados`.
8. **Download seletivo, bundle e manifesto verificável** — `CAP-32-08`, `COM-1786` a `COM-1792`, `SCR-0256`, rota planejada `/community/models/download-seletivo-bundle-e-manifesto-verificavel`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1737`–`COM-1792` possuem evidência;
- as oito famílias `SCR-0249`–`SCR-0256` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-129: Visualização 3D e inspeção técnica

Objetivo:

Compreensão do objeto antes de baixar, fabricar ou comprar.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-33-01` a `CAP-33-08`;
- requisitos: `COM-1793` a `COM-1848` — 56 itens;
- telas: `SCR-0257` a `SCR-0264` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-101`, `PKG-102`, `PKG-103`, `PKG-111`, `PKG-128`.

Entrega isolada:

- Ao fechar, o `PKG-129` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Viewer webgl progressivo com fallback acessível** — `CAP-33-01`, `COM-1793` a `COM-1799`, `SCR-0257`, rota planejada `/community/viewer/viewer-webgl-progressivo-com-fallback-acessivel`.
2. **Explosão de conjunto e árvore de peças** — `CAP-33-02`, `COM-1800` a `COM-1806`, `SCR-0258`, rota planejada `/community/viewer/explosao-de-conjunto-e-arvore-de-pecas`.
3. **Medição, corte, seção, espessura e escala** — `CAP-33-03`, `COM-1807` a `COM-1813`, `SCR-0259`, rota planejada `/community/viewer/medicao-corte-secao-espessura-e-escala`.
4. **Mapa de overhang, suporte, ilhas e fragilidade** — `CAP-33-04`, `COM-1814` a `COM-1820`, `SCR-0260`, rota planejada `/community/viewer/mapa-de-overhang-suporte-ilhas-e-fragilidade`.
5. **Comparação lado a lado e sobreposição de versões** — `CAP-33-05`, `COM-1821` a `COM-1827`, `SCR-0261`, rota planejada `/community/viewer/comparacao-lado-a-lado-e-sobreposicao-de-versoes`.
6. **Anotações espaciais e comentários por região** — `CAP-33-06`, `COM-1828` a `COM-1834`, `SCR-0262`, rota planejada `/community/viewer/anotacoes-espaciais-e-comentarios-por-regiao`.
7. **Visualização de material, cor e acabamento** — `CAP-33-07`, `COM-1835` a `COM-1841`, `SCR-0263`, rota planejada `/community/viewer/visualizacao-de-material-cor-e-acabamento`.
8. **Orçamento de desempenho para modelos grandes no mobile** — `CAP-33-08`, `COM-1842` a `COM-1848`, `SCR-0264`, rota planejada `/community/viewer/orcamento-de-desempenho-para-modelos-grandes-no-mobile`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1793`–`COM-1848` possuem evidência;
- as oito famílias `SCR-0257`–`SCR-0264` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-130: Customização paramétrica e geração

Objetivo:

Adaptação local de peças sem exigir domínio completo de CAD.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-34-01` a `CAP-34-08`;
- requisitos: `COM-1849` a `COM-1904` — 56 itens;
- telas: `SCR-0265` a `SCR-0272` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-111`, `PKG-113`, `PKG-128`, `PKG-129`.

Entrega isolada:

- Ao fechar, o `PKG-130` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Parâmetros declarados com unidade, limite e ajuda** — `CAP-34-01`, `COM-1849` a `COM-1855`, `SCR-0265`, rota planejada `/community/parametric/parametros-declarados-com-unidade-limite-e-ajuda`.
2. **Preview instantâneo e validação de geometria** — `CAP-34-02`, `COM-1856` a `COM-1862`, `SCR-0266`, rota planejada `/community/parametric/preview-instantaneo-e-validacao-de-geometria`.
3. **Presets compartilháveis por uso e hardware** — `CAP-34-03`, `COM-1863` a `COM-1869`, `SCR-0267`, rota planejada `/community/parametric/presets-compartilhaveis-por-uso-e-hardware`.
4. **Geração isolada de openscad e engines compatíveis** — `CAP-34-04`, `COM-1870` a `COM-1876`, `SCR-0268`, rota planejada `/community/parametric/geracao-isolada-de-openscad-e-engines-compativeis`.
5. **Fila de geração com cota e cancelamento** — `CAP-34-05`, `COM-1877` a `COM-1883`, `SCR-0269`, rota planejada `/community/parametric/fila-de-geracao-com-cota-e-cancelamento`.
6. **Versão do gerador vinculada ao arquivo resultante** — `CAP-34-06`, `COM-1884` a `COM-1890`, `SCR-0270`, rota planejada `/community/parametric/versao-do-gerador-vinculada-ao-arquivo-resultante`.
7. **Teste automático de combinações limites** — `CAP-34-07`, `COM-1891` a `COM-1897`, `SCR-0271`, rota planejada `/community/parametric/teste-automatico-de-combinacoes-limites`.
8. **Publicação de variação sem quebrar autoria e licença** — `CAP-34-08`, `COM-1898` a `COM-1904`, `SCR-0272`, rota planejada `/community/parametric/publicacao-de-variacao-sem-quebrar-autoria-e-licenca`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1849`–`COM-1904` possuem evidência;
- as oito famílias `SCR-0265`–`SCR-0272` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-131: Fatiamento avançado e perfis reproduzíveis

Objetivo:

Impressões mais confiáveis com parâmetros compreensíveis e comparáveis.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-35-01` a `CAP-35-08`;
- requisitos: `COM-1905` a `COM-1960` — 56 itens;
- telas: `SCR-0273` a `SCR-0280` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-111`, `PKG-113`, `PKG-114`, `PKG-128`, `PKG-129`, `PKG-130`.

Entrega isolada:

- Ao fechar, o `PKG-131` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Contrato obrigatório de presets:

- o preset executável canônico preserva o bundle nativo do OrcaSlicer, inicialmente composto por `process`, `filament` e `machine`, sem reduzir o conteúdo aos campos resumidos do perfil social;
- cada revisão guarda formato/schema do preset, versão da engine, JSON original sanitizado, representação canônica, herança, overrides, compatibilidade e `sha256`;
- campos desconhecidos de uma versão N/N-1 são preservados no round-trip; qualquer conversão para outro slicer informa perdas antes de salvar;
- importação entra privada, cria revisão imutável e nunca instala ou ativa configuração local automaticamente;
- o perfil compartilhável do PKG-63 permanece uma projeção resumida; a revisão nativa do preset é a fonte executável usada pelo fatiamento;
- cada job de fatiamento referencia uma revisão imutável do bundle e registra versão da engine e checksum para permitir reprodução exata;
- exportação para OrcaSlicer deve reconstruir um bundle semanticamente equivalente ao importado, sem incluir host, path local, credencial, token ou dado operacional sensível.

Lotes de capacidade:

1. **Editor completo de perfil com níveis básico e avançado** — `CAP-35-01`, `COM-1905` a `COM-1911`, `SCR-0273`, incluindo importação, persistência, edição e exportação do bundle nativo completo do OrcaSlicer; rota planejada `/community/slicing/editor-completo-de-perfil-com-niveis-basico-e-avancado`.
2. **Herança e diff entre perfil base e ajustes** — `CAP-35-02`, `COM-1912` a `COM-1918`, `SCR-0274`, incluindo diff por revisão entre `process`, `filament` e `machine`; rota planejada `/community/slicing/heranca-e-diff-entre-perfil-base-e-ajustes`.
3. **Compatibilidade entre slicers com perdas explícitas** — `CAP-35-03`, `COM-1919` a `COM-1925`, `SCR-0275`, preservando o original nativo e impedindo conversão silenciosa de campos desconhecidos; rota planejada `/community/slicing/compatibilidade-entre-slicers-com-perdas-explicitas`.
4. **Orientação, suporte e arranjo assistidos** — `CAP-35-04`, `COM-1926` a `COM-1932`, `SCR-0276`, rota planejada `/community/slicing/orientacao-suporte-e-arranjo-assistidos`.
5. **Estimativa comparativa de tempo, custo e resistência** — `CAP-35-05`, `COM-1933` a `COM-1939`, `SCR-0277`, rota planejada `/community/slicing/estimativa-comparativa-de-tempo-custo-e-resistencia`.
6. **Preview por recurso, velocidade, fluxo e ferramenta** — `CAP-35-06`, `COM-1940` a `COM-1946`, `SCR-0278`, rota planejada `/community/slicing/preview-por-recurso-velocidade-fluxo-e-ferramenta`.
7. **Experimentos a/b de perfil com resultado físico** — `CAP-35-07`, `COM-1947` a `COM-1953`, `SCR-0279`, rota planejada `/community/slicing/experimentos-a-b-de-perfil-com-resultado-fisico`.
8. **Reprodução exata por versão de engine e configuração** — `CAP-35-08`, `COM-1954` a `COM-1960`, `SCR-0280`, vinculando job, versão da engine, revisão imutável do bundle e checksums dos presets/artefatos; rota planejada `/community/slicing/reproducao-exata-por-versao-de-engine-e-configuracao`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1905`–`COM-1960` possuem evidência;
- as oito famílias `SCR-0273`–`SCR-0280` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- round-trip de fixtures reais do OrcaSlicer preserva equivalência semântica e campos desconhecidos;
- job executado usa exatamente a revisão, versão da engine e checksums registrados, sem ler um perfil mutável posterior;
- perfil resumido do PKG-63 nunca substitui silenciosamente o bundle nativo executável;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-132: Fluxo ponta a ponta de impressão

Objetivo:

Menos etapas soltas entre descoberta, preparo, fabricação e aprendizado.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-36-01` a `CAP-36-08`;
- requisitos: `COM-1961` a `COM-2016` — 56 itens;
- telas: `SCR-0281` a `SCR-0288` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-111`, `PKG-113`, `PKG-131`.

Entrega isolada:

- Ao fechar, o `PKG-132` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Checkout técnico do projeto para uma impressora** — `CAP-36-01`, `COM-1961` a `COM-1967`, `SCR-0281`, rota planejada `/community/print_workflow/checkout-tecnico-do-projeto-para-uma-impressora`.
2. **Seleção guiada de variante, peças e quantidades** — `CAP-36-02`, `COM-1968` a `COM-1974`, `SCR-0282`, rota planejada `/community/print_workflow/selecao-guiada-de-variante-pecas-e-quantidades`.
3. **Preflight de arquivo, perfil, material e máquina** — `CAP-36-03`, `COM-1975` a `COM-1981`, `SCR-0283`, rota planejada `/community/print_workflow/preflight-de-arquivo-perfil-material-e-maquina`.
4. **Aprovação visual do g-code e riscos detectados** — `CAP-36-04`, `COM-1982` a `COM-1988`, `SCR-0284`, rota planejada `/community/print_workflow/aprovacao-visual-do-g-code-e-riscos-detectados`.
5. **Fila pessoal com prioridade e janela desejada** — `CAP-36-05`, `COM-1989` a `COM-1995`, `SCR-0285`, rota planejada `/community/print_workflow/fila-pessoal-com-prioridade-e-janela-desejada`.
6. **Monitoramento com checkpoints e intervenção segura** — `CAP-36-06`, `COM-1996` a `COM-2002`, `SCR-0286`, rota planejada `/community/print_workflow/monitoramento-com-checkpoints-e-intervencao-segura`.
7. **Registro de resultado, falha, consumo e fotos** — `CAP-36-07`, `COM-2003` a `COM-2009`, `SCR-0287`, rota planejada `/community/print_workflow/registro-de-resultado-falha-consumo-e-fotos`.
8. **Reimpressão reproduzível ou melhoria derivada** — `CAP-36-08`, `COM-2010` a `COM-2016`, `SCR-0288`, rota planejada `/community/print_workflow/reimpressao-reproduzivel-ou-melhoria-derivada`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1961`–`COM-2016` possuem evidência;
- as oito famílias `SCR-0281`–`SCR-0288` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-133: Manutenção colaborativa e confiabilidade

Objetivo:

Equipamentos disponíveis por mais tempo e menor risco de falha recorrente.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-40-01` a `CAP-40-08`;
- requisitos: `COM-2185` a `COM-2240` — 56 itens;
- telas: `SCR-0313` a `SCR-0320` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-113`, `PKG-114`, `PKG-124`, `PKG-132`.

Entrega isolada:

- Ao fechar, o `PKG-133` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Planos de manutenção por modelo, mod e ambiente** — `CAP-40-01`, `COM-2185` a `COM-2191`, `SCR-0313`, rota planejada `/community/maintenance_network/planos-de-manutencao-por-modelo-mod-e-ambiente`.
2. **Procedimentos ilustrados revisados pela comunidade** — `CAP-40-02`, `COM-2192` a `COM-2198`, `SCR-0314`, rota planejada `/community/maintenance_network/procedimentos-ilustrados-revisados-pela-comunidade`.
3. **Diagnóstico por sintomas, logs e histórico** — `CAP-40-03`, `COM-2199` a `COM-2205`, `SCR-0315`, rota planejada `/community/maintenance_network/diagnostico-por-sintomas-logs-e-historico`.
4. **Campanhas de inspeção por falha emergente** — `CAP-40-04`, `COM-2206` a `COM-2212`, `SCR-0316`, rota planejada `/community/maintenance_network/campanhas-de-inspecao-por-falha-emergente`.
5. **Peças e ferramentas necessárias por procedimento** — `CAP-40-05`, `COM-2213` a `COM-2219`, `SCR-0317`, rota planejada `/community/maintenance_network/pecas-e-ferramentas-necessarias-por-procedimento`.
6. **Rede de técnicos e mentores por região** — `CAP-40-06`, `COM-2220` a `COM-2226`, `SCR-0318`, rota planejada `/community/maintenance_network/rede-de-tecnicos-e-mentores-por-regiao`.
7. **Benchmark anônimo de confiabilidade por componente** — `CAP-40-07`, `COM-2227` a `COM-2233`, `SCR-0319`, rota planejada `/community/maintenance_network/benchmark-anonimo-de-confiabilidade-por-componente`.
8. **Lições pós-incidente incorporadas ao catálogo** — `CAP-40-08`, `COM-2234` a `COM-2240`, `SCR-0320`, rota planejada `/community/maintenance_network/licoes-pos-incidente-incorporadas-ao-catalogo`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2185`–`COM-2240` possuem evidência;
- as oito famílias `SCR-0313`–`SCR-0320` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-134: Fazendas de impressão e filas compartilhadas

Objetivo:

Uso eficiente e seguro de várias máquinas por equipes, escolas e pequenos negócios.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-37-01` a `CAP-37-08`;
- requisitos: `COM-2017` a `COM-2072` — 56 itens;
- telas: `SCR-0289` a `SCR-0296` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-113`, `PKG-115`, `PKG-124`, `PKG-132`, `PKG-133`.

Entrega isolada:

- Ao fechar, o `PKG-134` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Painel de frota com agrupamento por local e capacidade** — `CAP-37-01`, `COM-2017` a `COM-2023`, `SCR-0289`, rota planejada `/community/farm/painel-de-frota-com-agrupamento-por-local-e-capacidade`.
2. **Fila multi-impressora com roteamento e prioridades** — `CAP-37-02`, `COM-2024` a `COM-2030`, `SCR-0290`, rota planejada `/community/farm/fila-multi-impressora-com-roteamento-e-prioridades`.
3. **Calendário de disponibilidade, manutenção e operador** — `CAP-37-03`, `COM-2031` a `COM-2037`, `SCR-0291`, rota planejada `/community/farm/calendario-de-disponibilidade-manutencao-e-operador`.
4. **Kits de produção com lotes e quantidades** — `CAP-37-04`, `COM-2038` a `COM-2044`, `SCR-0292`, rota planejada `/community/farm/kits-de-producao-com-lotes-e-quantidades`.
5. **Troca de material e preparação de mesa como tarefas** — `CAP-37-05`, `COM-2045` a `COM-2051`, `SCR-0293`, rota planejada `/community/farm/troca-de-material-e-preparacao-de-mesa-como-tarefas`.
6. **Balanceamento por prazo, custo, energia e desgaste** — `CAP-37-06`, `COM-2052` a `COM-2058`, `SCR-0294`, rota planejada `/community/farm/balanceamento-por-prazo-custo-energia-e-desgaste`.
7. **Controle de qualidade e rastreabilidade por unidade** — `CAP-37-07`, `COM-2059` a `COM-2065`, `SCR-0295`, rota planejada `/community/farm/controle-de-qualidade-e-rastreabilidade-por-unidade`.
8. **Handoff de turno, incidentes e produtividade saudável** — `CAP-37-08`, `COM-2066` a `COM-2072`, `SCR-0296`, rota planejada `/community/farm/handoff-de-turno-incidentes-e-produtividade-saudavel`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2017`–`COM-2072` possuem evidência;
- as oito famílias `SCR-0289`–`SCR-0296` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-135: Coautoria, equipes e colaboração de projeto

Objetivo:

Projetos melhores por contribuição distribuída e autoria reconhecida.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-23-01` a `CAP-23-08`;
- requisitos: `COM-1233` a `COM-1288` — 56 itens;
- telas: `SCR-0177` a `SCR-0184` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-122`, `PKG-123`, `PKG-124`, `PKG-125`, `PKG-128`, `PKG-132`.

Entrega isolada:

- Ao fechar, o `PKG-135` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Equipe de projeto com papéis e permissões granulares** — `CAP-23-01`, `COM-1233` a `COM-1239`, `SCR-0177`, rota planejada `/community/collaboration/equipe-de-projeto-com-papeis-e-permissoes-granulares`.
2. **Convite, solicitação de entrada e saída segura** — `CAP-23-02`, `COM-1240` a `COM-1246`, `SCR-0178`, rota planejada `/community/collaboration/convite-solicitacao-de-entrada-e-saida-segura`.
3. **Tarefas, marcos, dependências e responsáveis** — `CAP-23-03`, `COM-1247` a `COM-1253`, `SCR-0179`, rota planejada `/community/collaboration/tarefas-marcos-dependencias-e-responsaveis`.
4. **Comentários ancorados em arquivo, peça e versão** — `CAP-23-04`, `COM-1254` a `COM-1260`, `SCR-0180`, rota planejada `/community/collaboration/comentarios-ancorados-em-arquivo-peca-e-versao`.
5. **Revisão por pares com aprovação e pedido de alteração** — `CAP-23-05`, `COM-1261` a `COM-1267`, `SCR-0181`, rota planejada `/community/collaboration/revisao-por-pares-com-aprovacao-e-pedido-de-alteracao`.
6. **Branch, merge e resolução visual de conflito de modelo** — `CAP-23-06`, `COM-1268` a `COM-1274`, `SCR-0182`, rota planejada `/community/collaboration/branch-merge-e-resolucao-visual-de-conflito-de-modelo`.
7. **Créditos proporcionais e histórico de contribuição** — `CAP-23-07`, `COM-1275` a `COM-1281`, `SCR-0183`, rota planejada `/community/collaboration/creditos-proporcionais-e-historico-de-contribuicao`.
8. **Handoff, arquivamento e continuidade do projeto** — `CAP-23-08`, `COM-1282` a `COM-1288`, `SCR-0184`, rota planejada `/community/collaboration/handoff-arquivamento-e-continuidade-do-projeto`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1233`–`COM-1288` possuem evidência;
- as oito famílias `SCR-0177`–`SCR-0184` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-136: Mensagens, chat e presença em tempo real

Objetivo:

Colaboração rápida, suporte e vínculos entre makers com controles de segurança.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-21-01` a `CAP-21-08`;
- requisitos: `COM-1121` a `COM-1176` — 56 itens;
- telas: `SCR-0161` a `SCR-0168` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-107`, `PKG-108`, `PKG-122`, `PKG-123`, `PKG-124`.

Entrega isolada:

- Ao fechar, o `PKG-136` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Mensagens diretas com solicitações e filtros** — `CAP-21-01`, `COM-1121` a `COM-1127`, `SCR-0161`, rota planejada `/community/messaging/mensagens-diretas-com-solicitacoes-e-filtros`.
2. **Conversas em grupo com papéis e convite** — `CAP-21-02`, `COM-1128` a `COM-1134`, `SCR-0162`, rota planejada `/community/messaging/conversas-em-grupo-com-papeis-e-convite`.
3. **Chat por projeto, comunidade, evento e trabalho** — `CAP-21-03`, `COM-1135` a `COM-1141`, `SCR-0163`, rota planejada `/community/messaging/chat-por-projeto-comunidade-evento-e-trabalho`.
4. **Threads, respostas, reações e mensagens fixadas** — `CAP-21-04`, `COM-1142` a `COM-1148`, `SCR-0164`, rota planejada `/community/messaging/threads-respostas-reacoes-e-mensagens-fixadas`.
5. **Presença opcional e status de disponibilidade** — `CAP-21-05`, `COM-1149` a `COM-1155`, `SCR-0165`, rota planejada `/community/messaging/presenca-opcional-e-status-de-disponibilidade`.
6. **Compartilhamento seguro de arquivos e previews** — `CAP-21-06`, `COM-1156` a `COM-1162`, `SCR-0166`, rota planejada `/community/messaging/compartilhamento-seguro-de-arquivos-e-previews`.
7. **Busca, exportação e retenção controlada da conversa** — `CAP-21-07`, `COM-1163` a `COM-1169`, `SCR-0167`, rota planejada `/community/messaging/busca-exportacao-e-retencao-controlada-da-conversa`.
8. **Voz, áudio curto e chamada com consentimento** — `CAP-21-08`, `COM-1170` a `COM-1176`, `SCR-0168`, rota planejada `/community/messaging/voz-audio-curto-e-chamada-com-consentimento`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1121`–`COM-1176` possuem evidência;
- as oito famílias `SCR-0161`–`SCR-0168` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-137: Eventos, encontros e fabricação coletiva

Objetivo:

Mobilização comunitária, aprendizagem prática e conexão territorial.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-22-01` a `CAP-22-08`;
- requisitos: `COM-1177` a `COM-1232` — 56 itens;
- telas: `SCR-0169` a `SCR-0176` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-112`, `PKG-115`, `PKG-124`, `PKG-136`.

Entrega isolada:

- Ao fechar, o `PKG-137` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Calendário de eventos online, presenciais e híbridos** — `CAP-22-01`, `COM-1177` a `COM-1183`, `SCR-0169`, rota planejada `/community/events/calendario-de-eventos-online-presenciais-e-hibridos`.
2. **Inscrição, capacidade, lista de espera e check-in** — `CAP-22-02`, `COM-1184` a `COM-1190`, `SCR-0170`, rota planejada `/community/events/inscricao-capacidade-lista-de-espera-e-check-in`.
3. **Mapa com privacidade de localização e acessibilidade** — `CAP-22-03`, `COM-1191` a `COM-1197`, `SCR-0171`, rota planejada `/community/events/mapa-com-privacidade-de-localizacao-e-acessibilidade`.
4. **Agenda, palestrantes, oficinas e materiais necessários** — `CAP-22-04`, `COM-1198` a `COM-1204`, `SCR-0172`, rota planejada `/community/events/agenda-palestrantes-oficinas-e-materiais-necessarios`.
5. **Transmissão, chat, perguntas e gravação** — `CAP-22-05`, `COM-1205` a `COM-1211`, `SCR-0173`, rota planejada `/community/events/transmissao-chat-perguntas-e-gravacao`.
6. **Hackathons, repair cafés e print farms coletivas** — `CAP-22-06`, `COM-1212` a `COM-1218`, `SCR-0174`, rota planejada `/community/events/hackathons-repair-cafes-e-print-farms-coletivas`.
7. **Certificado, fotos e resultados pós-evento** — `CAP-22-07`, `COM-1219` a `COM-1225`, `SCR-0175`, rota planejada `/community/events/certificado-fotos-e-resultados-pos-evento`.
8. **Ferramentas contra no-show, assédio e evento fraudulento** — `CAP-22-08`, `COM-1226` a `COM-1232`, `SCR-0176`, rota planejada `/community/events/ferramentas-contra-no-show-assedio-e-evento-fraudulento`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1177`–`COM-1232` possuem evidência;
- as oito famílias `SCR-0169`–`SCR-0176` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-138: Feed pessoal e consumo saudável

Objetivo:

Descoberta relevante sem vício, manipulação ou perda de controle do usuário.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-25-01` a `CAP-25-08`;
- requisitos: `COM-1345` a `COM-1400` — 56 itens;
- telas: `SCR-0193` a `SCR-0200` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-107`, `PKG-108`, `PKG-122`, `PKG-123`, `PKG-124`, `PKG-125`, `PKG-126`, `PKG-127`, `PKG-135`, `PKG-136`, `PKG-137`.

Entrega isolada:

- Ao fechar, o `PKG-138` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Feed cronológico de contas e comunidades seguidas** — `CAP-25-01`, `COM-1345` a `COM-1351`, `SCR-0193`, rota planejada `/community/feed/feed-cronologico-de-contas-e-comunidades-seguidas`.
2. **Feed recomendado com explicação e controles** — `CAP-25-02`, `COM-1352` a `COM-1358`, `SCR-0194`, rota planejada `/community/feed/feed-recomendado-com-explicacao-e-controles`.
3. **Listas personalizadas e feeds por interesse técnico** — `CAP-25-03`, `COM-1359` a `COM-1365`, `SCR-0195`, rota planejada `/community/feed/listas-personalizadas-e-feeds-por-interesse-tecnico`.
4. **Modo foco sem contadores ou rolagem infinita** — `CAP-25-04`, `COM-1366` a `COM-1372`, `SCR-0196`, rota planejada `/community/feed/modo-foco-sem-contadores-ou-rolagem-infinita`.
5. **Continuar de onde parou com limite diário opcional** — `CAP-25-05`, `COM-1373` a `COM-1379`, `SCR-0197`, rota planejada `/community/feed/continuar-de-onde-parou-com-limite-diario-opcional`.
6. **Não recomendar conteúdo bloqueado, repetido ou já resolvido** — `CAP-25-06`, `COM-1380` a `COM-1386`, `SCR-0198`, rota planejada `/community/feed/nao-recomendar-conteudo-bloqueado-repetido-ou-ja-resolvido`.
7. **Feedback explícito de menos, mais e não tenho interesse** — `CAP-25-07`, `COM-1387` a `COM-1393`, `SCR-0199`, rota planejada `/community/feed/feedback-explicito-de-menos-mais-e-nao-tenho-interesse`.
8. **Auditoria pessoal de por que cada item apareceu** — `CAP-25-08`, `COM-1394` a `COM-1400`, `SCR-0200`, rota planejada `/community/feed/auditoria-pessoal-de-por-que-cada-item-apareceu`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1345`–`COM-1400` possuem evidência;
- as oito famílias `SCR-0193`–`SCR-0200` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-139: Busca multimodal e descoberta avançada

Objetivo:

Encontrar rapidamente conhecimento, pessoas, peças e modelos compatíveis.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-26-01` a `CAP-26-08`;
- requisitos: `COM-1401` a `COM-1456` — 56 itens;
- telas: `SCR-0201` a `SCR-0208` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-105`, `PKG-107`, `PKG-108`, `PKG-122`, `PKG-124`, `PKG-125`, `PKG-126`, `PKG-127`, `PKG-128`, `PKG-138`.

Entrega isolada:

- Ao fechar, o `PKG-139` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Busca unificada por texto, categoria e entidade** — `CAP-26-01`, `COM-1401` a `COM-1407`, `SCR-0201`, rota planejada `/community/search/busca-unificada-por-texto-categoria-e-entidade`.
2. **Busca geométrica por malha ou desenho semelhante** — `CAP-26-02`, `COM-1408` a `COM-1414`, `SCR-0202`, rota planejada `/community/search/busca-geometrica-por-malha-ou-desenho-semelhante`.
3. **Busca por foto, objeto, peça quebrada ou qr code** — `CAP-26-03`, `COM-1415` a `COM-1421`, `SCR-0203`, rota planejada `/community/search/busca-por-foto-objeto-peca-quebrada-ou-qr-code`.
4. **Busca semântica por problema e intenção** — `CAP-26-04`, `COM-1422` a `COM-1428`, `SCR-0204`, rota planejada `/community/search/busca-semantica-por-problema-e-intencao`.
5. **Facetas técnicas combináveis e comparação de resultados** — `CAP-26-05`, `COM-1429` a `COM-1435`, `SCR-0205`, rota planejada `/community/search/facetas-tecnicas-combinaveis-e-comparacao-de-resultados`.
6. **Consultas salvas e alertas de novos resultados** — `CAP-26-06`, `COM-1436` a `COM-1442`, `SCR-0206`, rota planejada `/community/search/consultas-salvas-e-alertas-de-novos-resultados`.
7. **Histórico local e controles de personalização** — `CAP-26-07`, `COM-1443` a `COM-1449`, `SCR-0207`, rota planejada `/community/search/historico-local-e-controles-de-personalizacao`.
8. **Resultados explicados com qualidade e compatibilidade** — `CAP-26-08`, `COM-1450` a `COM-1456`, `SCR-0208`, rota planejada `/community/search/resultados-explicados-com-qualidade-e-compatibilidade`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1401`–`COM-1456` possuem evidência;
- as oito famílias `SCR-0201`–`SCR-0208` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-140: Recomendação e personalização responsável

Objetivo:

Conteúdo útil e compatível, com diversidade e transparência.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-27-01` a `CAP-27-08`;
- requisitos: `COM-1457` a `COM-1512` — 56 itens;
- telas: `SCR-0209` a `SCR-0216` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-105`, `PKG-106`, `PKG-107`, `PKG-108`, `PKG-122`, `PKG-123`, `PKG-138`, `PKG-139`.

Entrega isolada:

- Ao fechar, o `PKG-140` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Recomendação por impressora, material, habilidade e objetivo** — `CAP-27-01`, `COM-1457` a `COM-1463`, `SCR-0209`, rota planejada `/community/recommendations/recomendacao-por-impressora-material-habilidade-e-objetivo`.
2. **Mistura controlada de novidade, relevância e diversidade** — `CAP-27-02`, `COM-1464` a `COM-1470`, `SCR-0210`, rota planejada `/community/recommendations/mistura-controlada-de-novidade-relevancia-e-diversidade`.
3. **Proteção contra bolhas, popularidade e concentração** — `CAP-27-03`, `COM-1471` a `COM-1477`, `SCR-0211`, rota planejada `/community/recommendations/protecao-contra-bolhas-popularidade-e-concentracao`.
4. **Preferências editáveis e perfil de interesse visível** — `CAP-27-04`, `COM-1478` a `COM-1484`, `SCR-0212`, rota planejada `/community/recommendations/preferencias-editaveis-e-perfil-de-interesse-visivel`.
5. **Recomendação local sem enviar dados sensíveis quando possível** — `CAP-27-05`, `COM-1485` a `COM-1491`, `SCR-0213`, rota planejada `/community/recommendations/recomendacao-local-sem-enviar-dados-sensiveis-quando-possivel`.
6. **Testes de viés por idioma, região e tamanho do criador** — `CAP-27-06`, `COM-1492` a `COM-1498`, `SCR-0214`, rota planejada `/community/recommendations/testes-de-vies-por-idioma-regiao-e-tamanho-do-criador`.
7. **Modo descoberta aleatória e curadoria humana** — `CAP-27-07`, `COM-1499` a `COM-1505`, `SCR-0215`, rota planejada `/community/recommendations/modo-descoberta-aleatoria-e-curadoria-humana`.
8. **Desativação total sem degradar funções básicas** — `CAP-27-08`, `COM-1506` a `COM-1512`, `SCR-0216`, rota planejada `/community/recommendations/desativacao-total-sem-degradar-funcoes-basicas`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-1457`–`COM-1512` possuem evidência;
- as oito famílias `SCR-0209`–`SCR-0216` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-141: Câmeras, visão computacional e assistência por IA

Objetivo:

Detecção antecipada de falhas com controle humano e redução de desperdício.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-38-01` a `CAP-38-08`;
- requisitos: `COM-2073` a `COM-2128` — 56 itens;
- telas: `SCR-0297` a `SCR-0304` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-106`, `PKG-107`, `PKG-108`, `PKG-111`, `PKG-113`, `PKG-127`, `PKG-128`, `PKG-129`, `PKG-132`.

Entrega isolada:

- Ao fechar, o `PKG-141` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Configuração guiada de câmera, enquadramento e iluminação** — `CAP-38-01`, `COM-2073` a `COM-2079`, `SCR-0297`, rota planejada `/community/vision_ai/configuracao-guiada-de-camera-enquadramento-e-iluminacao`.
2. **Detecção de spaghetti, descolamento e deslocamento** — `CAP-38-02`, `COM-2080` a `COM-2086`, `SCR-0298`, rota planejada `/community/vision_ai/deteccao-de-spaghetti-descolamento-e-deslocamento`.
3. **Detecção de fumaça ou evento crítico com redundância** — `CAP-38-03`, `COM-2087` a `COM-2093`, `SCR-0299`, rota planejada `/community/vision_ai/deteccao-de-fumaca-ou-evento-critico-com-redundancia`.
4. **Score de confiança e política de alerta, pausa ou bloqueio** — `CAP-38-04`, `COM-2094` a `COM-2100`, `SCR-0300`, rota planejada `/community/vision_ai/score-de-confianca-e-politica-de-alerta-pausa-ou-bloqueio`.
5. **Feedback do usuário sobre falso positivo e falso negativo** — `CAP-38-05`, `COM-2101` a `COM-2107`, `SCR-0301`, rota planejada `/community/vision_ai/feedback-do-usuario-sobre-falso-positivo-e-falso-negativo`.
6. **Processamento local opcional e retenção mínima de imagem** — `CAP-38-06`, `COM-2108` a `COM-2114`, `SCR-0302`, rota planejada `/community/vision_ai/processamento-local-opcional-e-retencao-minima-de-imagem`.
7. **Comparação da peça real com referência esperada** — `CAP-38-07`, `COM-2115` a `COM-2121`, `SCR-0303`, rota planejada `/community/vision_ai/comparacao-da-peca-real-com-referencia-esperada`.
8. **Painel de desempenho, viés e segurança do modelo** — `CAP-38-08`, `COM-2122` a `COM-2128`, `SCR-0304`, rota planejada `/community/vision_ai/painel-de-desempenho-vies-e-seguranca-do-modelo`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2073`–`COM-2128` possuem evidência;
- as oito famílias `SCR-0297`–`SCR-0304` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-142: Integrações e portabilidade do ecossistema 3D

Objetivo:

Menos aprisionamento e fluxo contínuo entre ferramentas que makers já usam.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-41-01` a `CAP-41-08`;
- requisitos: `COM-2241` a `COM-2296` — 56 itens;
- telas: `SCR-0321` a `SCR-0328` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-108`, `PKG-128`, `PKG-131`, `PKG-132`.

Entrega isolada:

- Ao fechar, o `PKG-142` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Conectores oficiais para repositórios de modelos** — `CAP-41-01`, `COM-2241` a `COM-2247`, `SCR-0321`, rota planejada `/community/integrations/conectores-oficiais-para-repositorios-de-modelos`.
2. **Importação assistida com licença e autoria preservadas** — `CAP-41-02`, `COM-2248` a `COM-2254`, `SCR-0322`, rota planejada `/community/integrations/importacao-assistida-com-licenca-e-autoria-preservadas`.
3. **Sincronização opt-in de favoritos, coleções e versões** — `CAP-41-03`, `COM-2255` a `COM-2261`, `SCR-0323`, rota planejada `/community/integrations/sincronizacao-opt-in-de-favoritos-colecoes-e-versoes`.
4. **Envio por um clique a slicers e hosts compatíveis** — `CAP-41-04`, `COM-2262` a `COM-2268`, `SCR-0324`, rota planejada `/community/integrations/envio-por-um-clique-a-slicers-e-hosts-compativeis`.
5. **Integração com cad, git, storage e notas** — `CAP-41-05`, `COM-2269` a `COM-2275`, `SCR-0325`, rota planejada `/community/integrations/integracao-com-cad-git-storage-e-notas`.
6. **Webhooks de projeto, versão, impressão e incidente** — `CAP-41-06`, `COM-2276` a `COM-2282`, `SCR-0326`, rota planejada `/community/integrations/webhooks-de-projeto-versao-impressao-e-incidente`.
7. **Painel de permissões, falhas e última sincronização** — `CAP-41-07`, `COM-2283` a `COM-2289`, `SCR-0327`, rota planejada `/community/integrations/painel-de-permissoes-falhas-e-ultima-sincronizacao`.
8. **Exportação em formato aberto para migração completa** — `CAP-41-08`, `COM-2290` a `COM-2296`, `SCR-0328`, rota planejada `/community/integrations/exportacao-em-formato-aberto-para-migracao-completa`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2241`–`COM-2296` possuem evidência;
- as oito famílias `SCR-0321`–`SCR-0328` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-143: Plataforma de desenvolvedores e extensões

Objetivo:

Inovação aberta sem comprometer segurança, privacidade ou estabilidade.

Prioridade social: P2.

Rastreabilidade integral:

- capacidades: `CAP-42-01` a `CAP-42-08`;
- requisitos: `COM-2297` a `COM-2352` — 56 itens;
- telas: `SCR-0329` a `SCR-0336` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-108`, `PKG-142`.

Entrega isolada:

- Ao fechar, o `PKG-143` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Api pública versionada com escopos mínimos** — `CAP-42-01`, `COM-2297` a `COM-2303`, `SCR-0329`, rota planejada `/community/developer/api-publica-versionada-com-escopos-minimos`.
2. **Portal de documentação, exemplos e changelog** — `CAP-42-02`, `COM-2304` a `COM-2310`, `SCR-0330`, rota planejada `/community/developer/portal-de-documentacao-exemplos-e-changelog`.
3. **Oauth para aplicações de terceiros** — `CAP-42-03`, `COM-2311` a `COM-2317`, `SCR-0331`, rota planejada `/community/developer/oauth-para-aplicacoes-de-terceiros`.
4. **Sandbox com dados sintéticos e impressora simulada** — `CAP-42-04`, `COM-2318` a `COM-2324`, `SCR-0332`, rota planejada `/community/developer/sandbox-com-dados-sinteticos-e-impressora-simulada`.
5. **Sdks e componentes incorporáveis** — `CAP-42-05`, `COM-2325` a `COM-2331`, `SCR-0333`, rota planejada `/community/developer/sdks-e-componentes-incorporaveis`.
6. **Marketplace de extensões revisadas** — `CAP-42-06`, `COM-2332` a `COM-2338`, `SCR-0334`, rota planejada `/community/developer/marketplace-de-extensoes-revisadas`.
7. **Limites, auditoria e revogação por integração** — `CAP-42-07`, `COM-2339` a `COM-2345`, `SCR-0335`, rota planejada `/community/developer/limites-auditoria-e-revogacao-por-integracao`.
8. **Programa de compatibilidade e depreciação previsível** — `CAP-42-08`, `COM-2346` a `COM-2352`, `SCR-0336`, rota planejada `/community/developer/programa-de-compatibilidade-e-depreciacao-previsivel`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2297`–`COM-2352` possuem evidência;
- as oito famílias `SCR-0329`–`SCR-0336` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-144: Ferramentas profissionais para criadores

Objetivo:

Sustentabilidade econômica e melhor relacionamento entre criadores e comunidade.

Prioridade social: P3.

Rastreabilidade integral:

- capacidades: `CAP-44-01` a `CAP-44-08`;
- requisitos: `COM-2409` a `COM-2464` — 56 itens;
- telas: `SCR-0345` a `SCR-0352` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-122`, `PKG-125`, `PKG-127`, `PKG-128`, `PKG-129`, `PKG-135`, `PKG-138`, `PKG-139`, `PKG-140`.

Entrega isolada:

- Ao fechar, o `PKG-144` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Studio de conteúdo, modelos, posts e agenda** — `CAP-44-01`, `COM-2409` a `COM-2415`, `SCR-0345`, rota planejada `/community/creator/studio-de-conteudo-modelos-posts-e-agenda`.
2. **Painel de audiência, retenção e origem de descoberta** — `CAP-44-02`, `COM-2416` a `COM-2422`, `SCR-0346`, rota planejada `/community/creator/painel-de-audiencia-retencao-e-origem-de-descoberta`.
3. **Crm leve de apoiadores e clientes com consentimento** — `CAP-44-03`, `COM-2423` a `COM-2429`, `SCR-0347`, rota planejada `/community/creator/crm-leve-de-apoiadores-e-clientes-com-consentimento`.
4. **Respostas salvas, automações e caixa de entrada unificada** — `CAP-44-04`, `COM-2430` a `COM-2436`, `SCR-0348`, rota planejada `/community/creator/respostas-salvas-automacoes-e-caixa-de-entrada-unificada`.
5. **Kits de mídia, links e vitrine personalizável** — `CAP-44-05`, `COM-2437` a `COM-2443`, `SCR-0349`, rota planejada `/community/creator/kits-de-midia-links-e-vitrine-personalizavel`.
6. **Metas públicas e roadmap do criador** — `CAP-44-06`, `COM-2444` a `COM-2450`, `SCR-0350`, rota planejada `/community/creator/metas-publicas-e-roadmap-do-criador`.
7. **Colaboração e divisão transparente de receita** — `CAP-44-07`, `COM-2451` a `COM-2457`, `SCR-0351`, rota planejada `/community/creator/colaboracao-e-divisao-transparente-de-receita`.
8. **Exportação de dados financeiros e fiscais** — `CAP-44-08`, `COM-2458` a `COM-2464`, `SCR-0352`, rota planejada `/community/creator/exportacao-de-dados-financeiros-e-fiscais`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2409`–`COM-2464` possuem evidência;
- as oito famílias `SCR-0345`–`SCR-0352` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-145: Reputação, reconhecimento e credenciais

Objetivo:

Confiança baseada em contribuição verificável, não apenas popularidade.

Prioridade social: P3.

Rastreabilidade integral:

- capacidades: `CAP-48-01` a `CAP-48-08`;
- requisitos: `COM-2633` a `COM-2688` — 56 itens;
- telas: `SCR-0377` a `SCR-0384` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-106`, `PKG-108`, `PKG-122`, `PKG-123`, `PKG-124`, `PKG-125`, `PKG-126`, `PKG-138`, `PKG-139`, `PKG-140`.

Entrega isolada:

- Ao fechar, o `PKG-145` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Reputação multidimensional por competência** — `CAP-48-01`, `COM-2633` a `COM-2639`, `SCR-0377`, rota planejada `/community/reputation/reputacao-multidimensional-por-competencia`.
2. **Credenciais emitidas por escola, comunidade e parceiro** — `CAP-48-02`, `COM-2640` a `COM-2646`, `SCR-0378`, rota planejada `/community/reputation/credenciais-emitidas-por-escola-comunidade-e-parceiro`.
3. **Badges por contribuição, manutenção e mentoria** — `CAP-48-03`, `COM-2647` a `COM-2653`, `SCR-0379`, rota planejada `/community/reputation/badges-por-contribuicao-manutencao-e-mentoria`.
4. **Níveis que não bloqueiam funções essenciais** — `CAP-48-04`, `COM-2654` a `COM-2660`, `SCR-0380`, rota planejada `/community/reputation/niveis-que-nao-bloqueiam-funcoes-essenciais`.
5. **Endorsement com contexto e expiração** — `CAP-48-05`, `COM-2661` a `COM-2667`, `SCR-0381`, rota planejada `/community/reputation/endorsement-com-contexto-e-expiracao`.
6. **Portfólio de impacto, não só contagem de likes** — `CAP-48-06`, `COM-2668` a `COM-2674`, `SCR-0382`, rota planejada `/community/reputation/portfolio-de-impacto-nao-so-contagem-de-likes`.
7. **Detecção de troca de favores e fazenda de reputação** — `CAP-48-07`, `COM-2675` a `COM-2681`, `SCR-0383`, rota planejada `/community/reputation/deteccao-de-troca-de-favores-e-fazenda-de-reputacao`.
8. **Contestação e correção de credencial incorreta** — `CAP-48-08`, `COM-2682` a `COM-2688`, `SCR-0384`, rota planejada `/community/reputation/contestacao-e-correcao-de-credencial-incorreta`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2633`–`COM-2688` possuem evidência;
- as oito famílias `SCR-0377`–`SCR-0384` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-146: Organizações, equipes e presença institucional

Objetivo:

Coordenação entre empresas, escolas, laboratórios, ONGs e coletivos.

Prioridade social: P3.

Rastreabilidade integral:

- capacidades: `CAP-51-01` a `CAP-51-08`;
- requisitos: `COM-2801` a `COM-2856` — 56 itens;
- telas: `SCR-0401` a `SCR-0408` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-107`, `PKG-108`, `PKG-122`, `PKG-124`, `PKG-135`, `PKG-136`, `PKG-145`.

Entrega isolada:

- Ao fechar, o `PKG-146` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Página institucional com unidades e finalidade** — `CAP-51-01`, `COM-2801` a `COM-2807`, `SCR-0401`, rota planejada `/community/organizations/pagina-institucional-com-unidades-e-finalidade`.
2. **Membros, equipes, papéis e delegação** — `CAP-51-02`, `COM-2808` a `COM-2814`, `SCR-0402`, rota planejada `/community/organizations/membros-equipes-papeis-e-delegacao`.
3. **Portfólio de projetos, equipamentos e capacidade** — `CAP-51-03`, `COM-2815` a `COM-2821`, `SCR-0403`, rota planejada `/community/organizations/portfolio-de-projetos-equipamentos-e-capacidade`.
4. **Vagas, voluntariado, estágio e mentoria** — `CAP-51-04`, `COM-2822` a `COM-2828`, `SCR-0404`, rota planejada `/community/organizations/vagas-voluntariado-estagio-e-mentoria`.
5. **Políticas públicas de segurança, licença e sustentabilidade** — `CAP-51-05`, `COM-2829` a `COM-2835`, `SCR-0405`, rota planejada `/community/organizations/politicas-publicas-de-seguranca-licenca-e-sustentabilidade`.
6. **Relatórios e comunicados oficiais** — `CAP-51-06`, `COM-2836` a `COM-2842`, `SCR-0406`, rota planejada `/community/organizations/relatorios-e-comunicados-oficiais`.
7. **Verificação por domínio e documentação** — `CAP-51-07`, `COM-2843` a `COM-2849`, `SCR-0407`, rota planejada `/community/organizations/verificacao-por-dominio-e-documentacao`.
8. **Transferência de propriedade e continuidade institucional** — `CAP-51-08`, `COM-2850` a `COM-2856`, `SCR-0408`, rota planejada `/community/organizations/transferencia-de-propriedade-e-continuidade-institucional`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2801`–`COM-2856` possuem evidência;
- as oito famílias `SCR-0401`–`SCR-0408` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-147: Marketplace de modelos, serviços e impressões

Objetivo:

Renda para criadores e acesso seguro a bens digitais e físicos.

Prioridade social: P3.

Rastreabilidade integral:

- capacidades: `CAP-46-01` a `CAP-46-08`;
- requisitos: `COM-2521` a `COM-2576` — 56 itens;
- telas: `SCR-0361` a `SCR-0368` — 8 famílias;
- baseline auditado em julho de 2026: `parcial`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-107`, `PKG-108`, `PKG-111`, `PKG-113`, `PKG-115`, `PKG-122`, `PKG-128`, `PKG-132`, `PKG-144`, `PKG-145`, `PKG-146`.

Entrega isolada:

- Ao fechar, o `PKG-147` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Venda avulsa de arquivo digital com licença** — `CAP-46-01`, `COM-2521` a `COM-2527`, `SCR-0361`, rota planejada `/community/marketplace/venda-avulsa-de-arquivo-digital-com-licenca`.
2. **Venda de peça impressa por criador ou parceiro** — `CAP-46-02`, `COM-2528` a `COM-2534`, `SCR-0362`, rota planejada `/community/marketplace/venda-de-peca-impressa-por-criador-ou-parceiro`.
3. **Contratação de design, ajuste e consultoria** — `CAP-46-03`, `COM-2535` a `COM-2541`, `SCR-0363`, rota planejada `/community/marketplace/contratacao-de-design-ajuste-e-consultoria`.
4. **Carrinho, cupom, imposto, moeda e comprovante** — `CAP-46-04`, `COM-2542` a `COM-2548`, `SCR-0364`, rota planejada `/community/marketplace/carrinho-cupom-imposto-moeda-e-comprovante`.
5. **Entrega digital segura e limite de download** — `CAP-46-05`, `COM-2549` a `COM-2555`, `SCR-0365`, rota planejada `/community/marketplace/entrega-digital-segura-e-limite-de-download`.
6. **Disputa, reembolso e proteção contra fraude** — `CAP-46-06`, `COM-2556` a `COM-2562`, `SCR-0366`, rota planejada `/community/marketplace/disputa-reembolso-e-protecao-contra-fraude`.
7. **Avaliação separada de arquivo, vendedor e fabricação** — `CAP-46-07`, `COM-2563` a `COM-2569`, `SCR-0367`, rota planejada `/community/marketplace/avaliacao-separada-de-arquivo-vendedor-e-fabricacao`.
8. **Transparência de taxa, promoção e ranqueamento comercial** — `CAP-46-08`, `COM-2570` a `COM-2576`, `SCR-0368`, rota planejada `/community/marketplace/transparencia-de-taxa-promocao-e-ranqueamento-comercial`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2521`–`COM-2576` possuem evidência;
- as oito famílias `SCR-0361`–`SCR-0368` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-148: Clubes, assinaturas e apoio recorrente

Objetivo:

Financiamento continuado para quem cria conhecimento e modelos úteis.

Prioridade social: P3.

Rastreabilidade integral:

- capacidades: `CAP-45-01` a `CAP-45-08`;
- requisitos: `COM-2465` a `COM-2520` — 56 itens;
- telas: `SCR-0353` a `SCR-0360` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-108`, `PKG-122`, `PKG-144`, `PKG-146`, `PKG-147`.

Entrega isolada:

- Ao fechar, o `PKG-148` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Níveis gratuitos e pagos com benefícios claros** — `CAP-45-01`, `COM-2465` a `COM-2471`, `SCR-0353`, rota planejada `/community/memberships/niveis-gratuitos-e-pagos-com-beneficios-claros`.
2. **Conteúdo, chat e arquivos por nível** — `CAP-45-02`, `COM-2472` a `COM-2478`, `SCR-0354`, rota planejada `/community/memberships/conteudo-chat-e-arquivos-por-nivel`.
3. **Acesso antecipado com liberação pública programada** — `CAP-45-03`, `COM-2479` a `COM-2485`, `SCR-0355`, rota planejada `/community/memberships/acesso-antecipado-com-liberacao-publica-programada`.
4. **Licença comercial por nível e modelo** — `CAP-45-04`, `COM-2486` a `COM-2492`, `SCR-0356`, rota planejada `/community/memberships/licenca-comercial-por-nivel-e-modelo`.
5. **Trial, presente, bolsa e preço regional** — `CAP-45-05`, `COM-2493` a `COM-2499`, `SCR-0357`, rota planejada `/community/memberships/trial-presente-bolsa-e-preco-regional`.
6. **Gestão de inadimplência, pausa e cancelamento simples** — `CAP-45-06`, `COM-2500` a `COM-2506`, `SCR-0358`, rota planejada `/community/memberships/gestao-de-inadimplencia-pausa-e-cancelamento-simples`.
7. **Reconhecimento de apoiador sem pressão pública** — `CAP-45-07`, `COM-2507` a `COM-2513`, `SCR-0359`, rota planejada `/community/memberships/reconhecimento-de-apoiador-sem-pressao-publica`.
8. **Painel de receita recorrente, churn e entrega de benefício** — `CAP-45-08`, `COM-2514` a `COM-2520`, `SCR-0360`, rota planejada `/community/memberships/painel-de-receita-recorrente-churn-e-entrega-de-beneficio`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2465`–`COM-2520` possuem evidência;
- as oito famílias `SCR-0353`–`SCR-0360` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-149: Pedidos, logística e pós-venda

Objetivo:

Entrega previsível de peças físicas e suporte após a compra.

Prioridade social: P3.

Rastreabilidade integral:

- capacidades: `CAP-47-01` a `CAP-47-08`;
- requisitos: `COM-2577` a `COM-2632` — 56 itens;
- telas: `SCR-0369` a `SCR-0376` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-108`, `PKG-113`, `PKG-115`, `PKG-132`, `PKG-134`, `PKG-147`.

Entrega isolada:

- Ao fechar, o `PKG-149` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Configurador de peça, material, cor e acabamento** — `CAP-47-01`, `COM-2577` a `COM-2583`, `SCR-0369`, rota planejada `/community/logistics/configurador-de-peca-material-cor-e-acabamento`.
2. **Prazo calculado por fila e capacidade real** — `CAP-47-02`, `COM-2584` a `COM-2590`, `SCR-0370`, rota planejada `/community/logistics/prazo-calculado-por-fila-e-capacidade-real`.
3. **Etapas de produção com evidência e aprovação** — `CAP-47-03`, `COM-2591` a `COM-2597`, `SCR-0371`, rota planejada `/community/logistics/etapas-de-producao-com-evidencia-e-aprovacao`.
4. **Embalagem, envio, retirada local e rastreamento** — `CAP-47-04`, `COM-2598` a `COM-2604`, `SCR-0372`, rota planejada `/community/logistics/embalagem-envio-retirada-local-e-rastreamento`.
5. **Inspeção de recebimento e aceite do cliente** — `CAP-47-05`, `COM-2605` a `COM-2611`, `SCR-0373`, rota planejada `/community/logistics/inspecao-de-recebimento-e-aceite-do-cliente`.
6. **Reposição por dano, defeito ou incompatibilidade** — `CAP-47-06`, `COM-2612` a `COM-2618`, `SCR-0374`, rota planejada `/community/logistics/reposicao-por-dano-defeito-ou-incompatibilidade`.
7. **Suporte pós-venda ligado à versão fabricada** — `CAP-47-07`, `COM-2619` a `COM-2625`, `SCR-0375`, rota planejada `/community/logistics/suporte-pos-venda-ligado-a-versao-fabricada`.
8. **Logística reversa, reciclagem e descarte responsável** — `CAP-47-08`, `COM-2626` a `COM-2632`, `SCR-0376`, rota planejada `/community/logistics/logistica-reversa-reciclagem-e-descarte-responsavel`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2577`–`COM-2632` possuem evidência;
- as oito famílias `SCR-0369`–`SCR-0376` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-150: Desafios, concursos e missões coletivas

Objetivo:

Mobilização criativa para problemas reais e aprendizado por projeto.

Prioridade social: P3.

Rastreabilidade integral:

- capacidades: `CAP-49-01` a `CAP-49-08`;
- requisitos: `COM-2689` a `COM-2744` — 56 itens;
- telas: `SCR-0385` a `SCR-0392` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-107`, `PKG-108`, `PKG-112`, `PKG-124`, `PKG-135`, `PKG-145`, `PKG-146`, `PKG-147`.

Entrega isolada:

- Ao fechar, o `PKG-150` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Desafios temáticos com problema e critérios claros** — `CAP-49-01`, `COM-2689` a `COM-2695`, `SCR-0385`, rota planejada `/community/contests/desafios-tematicos-com-problema-e-criterios-claros`.
2. **Categorias por idade, recurso e experiência** — `CAP-49-02`, `COM-2696` a `COM-2702`, `SCR-0386`, rota planejada `/community/contests/categorias-por-idade-recurso-e-experiencia`.
3. **Submissão de equipe, versão e evidência física** — `CAP-49-03`, `COM-2703` a `COM-2709`, `SCR-0387`, rota planejada `/community/contests/submissao-de-equipe-versao-e-evidencia-fisica`.
4. **Jurados, votação comunitária e conflito de interesse** — `CAP-49-04`, `COM-2710` a `COM-2716`, `SCR-0388`, rota planejada `/community/contests/jurados-votacao-comunitaria-e-conflito-de-interesse`.
5. **Feedback estruturado para todos os participantes** — `CAP-49-05`, `COM-2717` a `COM-2723`, `SCR-0389`, rota planejada `/community/contests/feedback-estruturado-para-todos-os-participantes`.
6. **Prêmios financeiros, materiais, bolsas e reconhecimento** — `CAP-49-06`, `COM-2724` a `COM-2730`, `SCR-0390`, rota planejada `/community/contests/premios-financeiros-materiais-bolsas-e-reconhecimento`.
7. **Missões sociais com adoção e acompanhamento do resultado** — `CAP-49-07`, `COM-2731` a `COM-2737`, `SCR-0391`, rota planejada `/community/contests/missoes-sociais-com-adocao-e-acompanhamento-do-resultado`.
8. **Arquivo permanente de regras, decisões e projetos** — `CAP-49-08`, `COM-2738` a `COM-2744`, `SCR-0392`, rota planejada `/community/contests/arquivo-permanente-de-regras-decisoes-e-projetos`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2689`–`COM-2744` possuem evidência;
- as oito famílias `SCR-0385`–`SCR-0392` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-151: Financiamento coletivo e pré-venda

Objetivo:

Viabilização transparente de hardware, conteúdo e iniciativas comunitárias.

Prioridade social: P3.

Rastreabilidade integral:

- capacidades: `CAP-50-01` a `CAP-50-08`;
- requisitos: `COM-2745` a `COM-2800` — 56 itens;
- telas: `SCR-0393` a `SCR-0400` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-107`, `PKG-108`, `PKG-122`, `PKG-124`, `PKG-144`, `PKG-145`, `PKG-146`, `PKG-147`, `PKG-149`.

Entrega isolada:

- Ao fechar, o `PKG-151` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Campanha com meta, orçamento, risco e cronograma** — `CAP-50-01`, `COM-2745` a `COM-2751`, `SCR-0393`, rota planejada `/community/crowdfunding/campanha-com-meta-orcamento-risco-e-cronograma`.
2. **Recompensas digitais, físicas e comunitárias** — `CAP-50-02`, `COM-2752` a `COM-2758`, `SCR-0394`, rota planejada `/community/crowdfunding/recompensas-digitais-fisicas-e-comunitarias`.
3. **Protótipo e evidência técnica antes da captação** — `CAP-50-03`, `COM-2759` a `COM-2765`, `SCR-0395`, rota planejada `/community/crowdfunding/prototipo-e-evidencia-tecnica-antes-da-captacao`.
4. **Marcos de liberação e prestação de contas** — `CAP-50-04`, `COM-2766` a `COM-2772`, `SCR-0396`, rota planejada `/community/crowdfunding/marcos-de-liberacao-e-prestacao-de-contas`.
5. **Atualizações, perguntas e votação de apoiadores** — `CAP-50-05`, `COM-2773` a `COM-2779`, `SCR-0397`, rota planejada `/community/crowdfunding/atualizacoes-perguntas-e-votacao-de-apoiadores`.
6. **Gestão de atraso, mudança de escopo e reembolso** — `CAP-50-06`, `COM-2780` a `COM-2786`, `SCR-0398`, rota planejada `/community/crowdfunding/gestao-de-atraso-mudanca-de-escopo-e-reembolso`.
7. **Verificação do responsável e prevenção a fraude** — `CAP-50-07`, `COM-2787` a `COM-2793`, `SCR-0399`, rota planejada `/community/crowdfunding/verificacao-do-responsavel-e-prevencao-a-fraude`.
8. **Relatório final de entrega, impacto e continuidade** — `CAP-50-08`, `COM-2794` a `COM-2800`, `SCR-0400`, rota planejada `/community/crowdfunding/relatorio-final-de-entrega-impacto-e-continuidade`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2745`–`COM-2800` possuem evidência;
- as oito famílias `SCR-0393`–`SCR-0400` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-152: Pesquisa aberta e ciência cidadã

Objetivo:

Experimentos reproduzíveis e colaboração entre comunidade, academia e indústria.

Prioridade social: P3.

Rastreabilidade integral:

- capacidades: `CAP-52-01` a `CAP-52-08`;
- requisitos: `COM-2857` a `COM-2912` — 56 itens;
- telas: `SCR-0409` a `SCR-0416` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-108`, `PKG-109`, `PKG-113`, `PKG-118`, `PKG-119`, `PKG-122`, `PKG-124`, `PKG-125`, `PKG-126`, `PKG-127`, `PKG-128`, `PKG-129`, `PKG-135`, `PKG-142`, `PKG-143`.

Entrega isolada:

- Ao fechar, o `PKG-152` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Protocolo experimental com hipótese e método** — `CAP-52-01`, `COM-2857` a `COM-2863`, `SCR-0409`, rota planejada `/community/open_science/protocolo-experimental-com-hipotese-e-metodo`.
2. **Dataset versionado com licença e dicionário** — `CAP-52-02`, `COM-2864` a `COM-2870`, `SCR-0410`, rota planejada `/community/open_science/dataset-versionado-com-licenca-e-dicionario`.
3. **Registro de máquina, perfil e condições ambientais** — `CAP-52-03`, `COM-2871` a `COM-2877`, `SCR-0411`, rota planejada `/community/open_science/registro-de-maquina-perfil-e-condicoes-ambientais`.
4. **Pré-registro e plano de análise opcional** — `CAP-52-04`, `COM-2878` a `COM-2884`, `SCR-0412`, rota planejada `/community/open_science/pre-registro-e-plano-de-analise-opcional`.
5. **Revisão aberta e réplica independente** — `CAP-52-05`, `COM-2885` a `COM-2891`, `SCR-0413`, rota planejada `/community/open_science/revisao-aberta-e-replica-independente`.
6. **Doi ou identificador persistente por resultado** — `CAP-52-06`, `COM-2892` a `COM-2898`, `SCR-0414`, rota planejada `/community/open_science/doi-ou-identificador-persistente-por-resultado`.
7. **Consentimento e ética para dados humanos** — `CAP-52-07`, `COM-2899` a `COM-2905`, `SCR-0415`, rota planejada `/community/open_science/consentimento-e-etica-para-dados-humanos`.
8. **Painel de replicações, divergências e conhecimento acumulado** — `CAP-52-08`, `COM-2906` a `COM-2912`, `SCR-0416`, rota planejada `/community/open_science/painel-de-replicacoes-divergencias-e-conhecimento-acumulado`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2857`–`COM-2912` possuem evidência;
- as oito famílias `SCR-0409`–`SCR-0416` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-153: Escaneamento, realidade aumentada e espacial

Objetivo:

Conexão entre objeto físico, espaço e modelo digital quando houver valor comprovado.

Prioridade social: P4.

Rastreabilidade integral:

- capacidades: `CAP-53-01` a `CAP-53-08`;
- requisitos: `COM-2913` a `COM-2968` — 56 itens;
- telas: `SCR-0417` a `SCR-0424` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-102`, `PKG-103`, `PKG-104`, `PKG-105`, `PKG-111`, `PKG-113`, `PKG-127`, `PKG-128`, `PKG-129`, `PKG-141`.

Entrega isolada:

- Ao fechar, o `PKG-153` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Captura fotogramétrica guiada pelo celular** — `CAP-53-01`, `COM-2913` a `COM-2919`, `SCR-0417`, rota planejada `/community/ar_scan/captura-fotogrametrica-guiada-pelo-celular`.
2. **Limpeza, escala e reparo assistidos de malha** — `CAP-53-02`, `COM-2920` a `COM-2926`, `SCR-0418`, rota planejada `/community/ar_scan/limpeza-escala-e-reparo-assistidos-de-malha`.
3. **Preview em realidade aumentada no ambiente** — `CAP-53-03`, `COM-2927` a `COM-2933`, `SCR-0419`, rota planejada `/community/ar_scan/preview-em-realidade-aumentada-no-ambiente`.
4. **Comparação do impresso com o modelo por sobreposição** — `CAP-53-04`, `COM-2934` a `COM-2940`, `SCR-0420`, rota planejada `/community/ar_scan/comparacao-do-impresso-com-o-modelo-por-sobreposicao`.
5. **Instrução espacial de montagem e manutenção** — `CAP-53-05`, `COM-2941` a `COM-2947`, `SCR-0421`, rota planejada `/community/ar_scan/instrucao-espacial-de-montagem-e-manutencao`.
6. **Medição de espaço e teste de encaixe** — `CAP-53-06`, `COM-2948` a `COM-2954`, `SCR-0422`, rota planejada `/community/ar_scan/medicao-de-espaco-e-teste-de-encaixe`.
7. **Tour virtual de oficina, laboratório e projeto** — `CAP-53-07`, `COM-2955` a `COM-2961`, `SCR-0423`, rota planejada `/community/ar_scan/tour-virtual-de-oficina-laboratorio-e-projeto`.
8. **Controles de privacidade para imagem do ambiente** — `CAP-53-08`, `COM-2962` a `COM-2968`, `SCR-0424`, rota planejada `/community/ar_scan/controles-de-privacidade-para-imagem-do-ambiente`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2913`–`COM-2968` possuem evidência;
- as oito famílias `SCR-0417`–`SCR-0424` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-154: Copilotos e automação assistida

Objetivo:

Redução de barreiras técnicas mantendo explicação, revisão humana e limites seguros.

Prioridade social: P4.

Rastreabilidade integral:

- capacidades: `CAP-54-01` a `CAP-54-08`;
- requisitos: `COM-2969` a `COM-3024` — 56 itens;
- telas: `SCR-0425` a `SCR-0432` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-104`, `PKG-105`, `PKG-106`, `PKG-107`, `PKG-108`, `PKG-111`, `PKG-113`, `PKG-126`, `PKG-131`, `PKG-132`, `PKG-141`, `PKG-143`.

Entrega isolada:

- Ao fechar, o `PKG-154` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Copiloto de busca e diagnóstico com fontes** — `CAP-54-01`, `COM-2969` a `COM-2975`, `SCR-0425`, rota planejada `/community/automation_ai/copiloto-de-busca-e-diagnostico-com-fontes`.
2. **Assistente de publicação que não inventa evidência** — `CAP-54-02`, `COM-2976` a `COM-2982`, `SCR-0426`, rota planejada `/community/automation_ai/assistente-de-publicacao-que-nao-inventa-evidencia`.
3. **Sugestão de tags, licença e compatibilidade** — `CAP-54-03`, `COM-2983` a `COM-2989`, `SCR-0427`, rota planejada `/community/automation_ai/sugestao-de-tags-licenca-e-compatibilidade`.
4. **Análise preliminar de modelo e printabilidade** — `CAP-54-04`, `COM-2990` a `COM-2996`, `SCR-0428`, rota planejada `/community/automation_ai/analise-preliminar-de-modelo-e-printabilidade`.
5. **Geração assistida de suporte e orientação** — `CAP-54-05`, `COM-2997` a `COM-3003`, `SCR-0429`, rota planejada `/community/automation_ai/geracao-assistida-de-suporte-e-orientacao`.
6. **Resumo de comunidade com incerteza e contestação** — `CAP-54-06`, `COM-3004` a `COM-3010`, `SCR-0430`, rota planejada `/community/automation_ai/resumo-de-comunidade-com-incerteza-e-contestacao`.
7. **Automação configurável com preview e desfazer** — `CAP-54-07`, `COM-3011` a `COM-3017`, `SCR-0431`, rota planejada `/community/automation_ai/automacao-configuravel-com-preview-e-desfazer`.
8. **Central de decisões de ia, dados usados e opt-out** — `CAP-54-08`, `COM-3018` a `COM-3024`, `SCR-0432`, rota planejada `/community/automation_ai/central-de-decisoes-de-ia-dados-usados-e-opt-out`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-2969`–`COM-3024` possuem evidência;
- as oito famílias `SCR-0425`–`SCR-0432` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.

## PKG-155: Interfaces futuras e experiências experimentais

Objetivo:

Exploração responsável de novos meios sem desviar recursos de necessidades sociais urgentes.

Prioridade social: P4.

Rastreabilidade integral:

- capacidades: `CAP-55-01` a `CAP-55-08`;
- requisitos: `COM-3025` a `COM-3080` — 56 itens;
- telas: `SCR-0433` a `SCR-0440` — 8 famílias;
- baseline auditado em julho de 2026: `ausente`;
- requisitos completos: `docs/community/COMMUNITY_BACKLOG.md`;
- telas/rotas/estados completos: `docs/community/COMMUNITY_SCREENS.md`.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes comunitários: `PKG-102`, `PKG-103`, `PKG-104`, `PKG-105`, `PKG-109`, `PKG-127`, `PKG-132`, `PKG-141`, `PKG-153`, `PKG-154`.

Entrega isolada:

- Ao fechar, o `PKG-155` funciona com a base consolidada e somente com as dependências acima; nenhum pacote de ID maior é necessário.
- A entrega possui entrada utilizável, contratos completos, persistência/integrações necessárias, métricas, documentação, testes, rollout e rollback próprios.
- Repetir SQL, request, comando, job, webhook, import, retry ou reconciliação não duplica estado nem efeito externo.

Lotes de capacidade:

1. **Painéis ambientais para oficina e parede** — `CAP-55-01`, `COM-3025` a `COM-3031`, `SCR-0433`, rota planejada `/community/future_interfaces/paineis-ambientais-para-oficina-e-parede`.
2. **Controle por voz com confirmação de ações críticas** — `CAP-55-02`, `COM-3032` a `COM-3038`, `SCR-0434`, rota planejada `/community/future_interfaces/controle-por-voz-com-confirmacao-de-acoes-criticas`.
3. **Interfaces vestíveis para monitoramento passivo** — `CAP-55-03`, `COM-3039` a `COM-3045`, `SCR-0435`, rota planejada `/community/future_interfaces/interfaces-vestiveis-para-monitoramento-passivo`.
4. **Visualização espacial colaborativa de montagem** — `CAP-55-04`, `COM-3046` a `COM-3052`, `SCR-0436`, rota planejada `/community/future_interfaces/visualizacao-espacial-colaborativa-de-montagem`.
5. **Telepresença de mentor em bancada** — `CAP-55-05`, `COM-3053` a `COM-3059`, `SCR-0437`, rota planejada `/community/future_interfaces/telepresenca-de-mentor-em-bancada`.
6. **Simulação física imersiva para treinamento** — `CAP-55-06`, `COM-3060` a `COM-3066`, `SCR-0438`, rota planejada `/community/future_interfaces/simulacao-fisica-imersiva-para-treinamento`.
7. **Interação háptica com modelos e superfícies** — `CAP-55-07`, `COM-3067` a `COM-3073`, `SCR-0439`, rota planejada `/community/future_interfaces/interacao-haptica-com-modelos-e-superficies`.
8. **Programa de experimentos com gate de valor e segurança** — `CAP-55-08`, `COM-3074` a `COM-3080`, `SCR-0440`, rota planejada `/community/future_interfaces/programa-de-experimentos-com-gate-de-valor-e-seguranca`.
9. **Integração, piloto e impacto** — integrar as oito capacidades, executar jornada ponta a ponta, piloto controlado, métricas de benefício/dano, falhas, abuso, privacidade, mobile, acessibilidade e reexecução idempotente.
10. **Fechamento** — revisar os 56 `COM` e oito `SCR`, corrigir regressões, validar dependências, idempotência, rollback, retenção e observabilidade, executar gate completo e criar commit exclusivo.

Critério de aceite:

- os 56 IDs `COM-3025`–`COM-3080` possuem evidência;
- as oito famílias `SCR-0433`–`SCR-0440` preservam separação CRUD e estados aplicáveis;
- nenhuma dependência futura, placeholder obrigatório ou contrato incompleto permanece;
- o pacote pode ser publicado e revertido sem pacote posterior;
- reexecução e concorrência não duplicam registro, evento, cobrança, mensagem, arquivo ou comando físico;
- contratos, regras, permissões, consumidores e compatibilidade N/N-1 estão coerentes;
- desktop/mobile, acessibilidade, offline, timeout, 429, 5xx e conflito são tratados;
- dados sensíveis são minimizados e logs permanecem sanitizados;
- métricas medem benefício humano e dano, não apenas engajamento;
- `./check.sh` e o validador de dependências passam;
- publicação/piloto somente quando autorizados e com rollback verificável.

Rollback:

- desativar entrada/flag reversível sem apagar dados;
- reverter código por release N-1 compatível;
- preservar dados canônicos e reconciliar consumidores;
- nunca executar `DROP`, `DELETE`, prune ou remoção de objeto sem confirmação explícita;
- manter canal de incidente quando houver risco social ou físico.

Estado atual:

- Planejado; implementação não iniciada. Executar somente depois de todas as dependências listadas estarem concluídas.
