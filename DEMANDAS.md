# Backlog Ativo Do Printora

## Fonte De Verdade

Este arquivo contém somente trabalho futuro com valor operacional aprovado.
Pacotes históricos `PKG-01` a `PKG-100` permanecem em
`DEMANDAS_CONSOLIDADAS_PKG_01_100.md`.

Fontes bloqueantes:

- `PATHS.toml`;
- `QUALITY_ROADMAP.md`;
- `GOVERNANCA.md`;
- `docs/community/PACKAGE_PORTFOLIO.csv`;
- `docs/community/PACKAGE_ARCHITECTURE.csv`;
- `docs/community/PACKAGE_EXECUTION_STANDARD.md`;
- `docs/community/PACKAGE_MODELING_REVIEW.md`.

O inventário `COMMUNITY_BACKLOG.*` preserva ideias e rastreabilidade histórica,
mas não autoriza implementação, não define prioridade e não exige cobertura
integral. Uma ideia só volta ao backlog após problema real, público afetado,
hipótese mensurável, custo operacional e dependências técnicas serem aprovados.

## Princípio De Produto

O Printora prioriza:

1. preparar projetos e arquivos para impressão;
2. fatiar de forma reproduzível;
3. validar e enviar com segurança;
4. acompanhar o estado real da impressora;
5. registrar resultado e facilitar reimpressão;
6. reduzir falhas por manutenção e diagnóstico;
7. operar materiais, múltiplas impressoras e integrações essenciais.

Rede social genérica, marketplace, pagamentos, CRM, educação formal, eventos,
crowdfunding, realidade aumentada e interfaces experimentais não pertencem ao
backlog ativo.

## Ordem Ativa De Implementação

- PKG-126 [P1]: Conhecimento e evidência técnica
- PKG-133 [P0]: Manutenção, diagnóstico e confiabilidade
- PKG-134 [P1]: Frota e filas de impressão
- PKG-142 [P1]: Integrações e descoberta técnica
- PKG-153 [P1]: Reconstrução 3D por múltiplas fotos
- PKG-154 [P1]: Qualificação e entrega de modelo imprimível

## Portfólio Reavaliado

Estado completo e justificativa por ID:
`docs/community/PACKAGE_PORTFOLIO.csv`.

- Concluídos e preservados: `PKG-101`, `PKG-102`, `PKG-104`, `PKG-110`, `PKG-114`, `PKG-128`, `PKG-131`, `PKG-132`, `PKG-141`.
- Ativos: `PKG-126`,
  `PKG-133`, `PKG-134`, `PKG-142`,
  `PKG-153`, `PKG-154`.
- Fundidos em ativos: `PKG-105`, `PKG-107`, `PKG-108`, `PKG-111`,
  `PKG-113`, `PKG-121`, `PKG-125`, `PKG-127`, `PKG-129`, `PKG-139`.
- Adiados sem autorização de implementação: `PKG-109`, `PKG-130`,
  `PKG-135`, `PKG-143`.
- Demais IDs entre `PKG-103` e `PKG-155`: cancelados.

Cancelar ou fundir um pacote futuro não remove código existente. Funcionalidade
já publicada só pode ser removida por demanda própria, inventário de
consumidores, validação e rollback.

## Política De Dependências

- Número do pacote é identidade histórica, não ordem automática.
- Dependências são técnicas, explícitas e registradas em
  `PACKAGE_ARCHITECTURE.csv`.
- Pacote cancelado, fundido ou adiado não pode ser dependência.
- Pacote ativo pode depender de concluído ou de ativo anterior na ordem.
- Nenhuma implementação deve recriar escopo de pacote cancelado.
- Descoberta de escopo novo pausa o lote e exige decisão de produto.

## Quando criar pacote

Criar ou reativar pacote somente quando o trabalho entregar fluxo, contrato,
regra, persistência, segurança ou integração multi-módulo com valor comprovado
e rollback próprio. Bug simples, texto, ajuste visual, teste ou melhoria local
permanece demanda pequena. Se uma melhoria crescer, registrar problema,
baseline, hipótese, dependências, risco e decisão antes de alterar o portfólio.

## PKG-126: Conhecimento e evidência técnica

Objetivo:

Transformar falha, solução, manutenção e resultado em conhecimento
reproduzível ligado à versão e ao contexto técnico.

Valor para o usuário:

Encontrar soluções aplicáveis mais rápido e evitar repetir diagnóstico sem
evidência.

Prioridade: P1.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes concluídos: `PKG-104`, `PKG-114`.
- Pacotes ativos: nenhum.

Escopo incluído:

- pergunta, sintoma, diagnóstico, solução confirmada e versões afetadas;
- tutorial ou runbook com ferramentas, etapas, riscos e resultado;
- fotos e vídeos curtos como evidência;
- vínculo com impressora pública sanitizada, componente, material e perfil;
- busca por erro, sintoma, componente e versão;
- autoria, licença, revisão e histórico.

Fora do escopo:

- live, streaming ou plataforma de vídeo;
- editor social genérico e publicação agendada;
- certificação, mentoria, chat ou escalonamento comercial;
- resumo por IA sem fontes e validação.

Lotes:

1. **Caracterização** — consolidar discussão, moderação, busca e mídia existentes.
2. **Contrato técnico** — sintoma, contexto, versão, evidência e solução.
3. **Publicação reproduzível** — pergunta, tutorial e runbook.
4. **Mídia controlada** — upload curto, sanitização, quota e retenção.
5. **Busca e resolução** — filtros técnicos e confirmação de solução.
6. **Fechamento** — moderação, acessibilidade, regressão e rollback.

Critério de aceite:

- conteúdo técnico aponta contexto e versão aplicáveis;
- solução marcada preserva histórico e autoria;
- upload valida tipo, tamanho, checksum e quarentena;
- localização, token, rosto ou metadado sensível não são publicados por padrão;
- retry e reexecução idempotente não duplicam post, mídia ou notificação;
- busca não enumera conteúdo privado;
- contrato, moderação, mídia, busca e `./check.sh` passam.

Rollback:

- desativar criação nova e manter conteúdo existente somente leitura;
- restaurar editor simples sem perder revisão ou mídia já confirmada;
- preservar objetos canônicos e remover apenas staging efêmero expirado.

Estado atual:

- posts, discussões, solução, busca, upload e moderação já existem parcialmente;
- `PKG-125` e `PKG-127` foram fundidos neste pacote.

## PKG-133: Manutenção, diagnóstico e confiabilidade

Objetivo:

Reduzir parada, recorrência de falha e diagnóstico manual usando histórico real
da impressora.

Valor para o usuário:

Saber o que verificar, quando manter e quais alterações precederam uma falha.

Prioridade: P0.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes concluídos: `PKG-104`, `PKG-114`, `PKG-132`.
- Pacotes ativos: nenhum.

Escopo incluído:

- plano e tarefa de manutenção por impressora e componente;
- evento, falha, ajuste, peça e ferramenta usada;
- diagnóstico por sintomas, logs sanitizados e histórico;
- correlação com update, configuração, material e trabalho;
- recorrência e lembrete acionável;
- procedimento técnico versionado ligado ao PKG-126.

Fora do escopo:

- rede regional de técnicos;
- benchmark público de componente;
- ordem comercial de serviço;
- remediação autônoma;
- alteração de Klipper sem preflight e confirmação.

Lotes:

1. **Caracterização** — consolidar manutenção, health, snapshots e relatórios.
2. **Modelo de componente e evento** — identidade, estado e invariantes.
3. **Plano e recorrência** — agenda, condição, atraso e conclusão.
4. **Diagnóstico correlacionado** — sintoma, mudança, log e trabalho.
5. **Procedimento e evidência** — passos, risco, ferramenta e resultado.
6. **Fechamento** — regressão, falha real controlada, observabilidade e rollback.

Critério de aceite:

- conclusão de tarefa gera um único evento auditável;
- diagnóstico diferencia fato atual, snapshot e inferência;
- recomendação não executa comando físico automaticamente;
- dado sensível de log é sanitizado;
- concorrência e reexecução idempotente não duplicam manutenção;
- falha de Moonraker mantém histórico local acessível;
- testes de regra, integração, histórico, UI e `./check.sh` passam.

Rollback:

- voltar à manutenção e health atuais preservando eventos novos;
- desativar correlação sem apagar histórico;
- manter procedimentos somente leitura se o consumidor N-1 não os entender.

Estado atual:

- manutenção, health check, snapshots, auditoria e relatórios já existem;
- o pacote evolui o núcleo atual e não cria rede social de manutenção.

## PKG-134: Frota e filas de impressão

Objetivo:

Coordenar várias impressoras com estado confiável, fila explícita e preparação
humana visível.

Valor para o usuário:

Escolher a máquina correta, evitar conflito de fila e enxergar bloqueios de
material, mesa ou manutenção.

Prioridade: P1.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes concluídos: `PKG-104`, `PKG-114`, `PKG-132`.
- Pacotes ativos: `PKG-133`.

Escopo incluído:

- painel de frota por local, capacidade e estado;
- fila por impressora com prioridade e ordenação determinística;
- material, mesa, operador e manutenção como pré-condições;
- lote simples com quantidade e progresso por unidade;
- handoff e incidente operacional;
- permissão por organização e impressora.

Fora do escopo:

- precificação, cotação ou marketplace;
- otimização autônoma por energia e custo;
- produtividade individual gamificada;
- calendário de espaço, instrutor ou escola;
- controle industrial MES completo.

Lotes:

1. **Caracterização da frota** — inventário, agentes, estado e permissões.
2. **Capacidade e pré-condições** — material, mesa, manutenção e disponibilidade.
3. **Fila determinística** — entrada, prioridade, cancelamento e conflito.
4. **Lote e unidade** — quantidade, resultado e rastreabilidade simples.
5. **Handoff e incidente** — responsabilidade, observação e recuperação.
6. **Fechamento** — concorrência, carga proporcional, smoke e rollback.

Critério de aceite:

- estado de uma impressora nunca aparece associado a outra;
- duas submissões concorrentes não ocupam a mesma posição canônica;
- fila não executa trabalho sem preflight válido;
- mudança de prioridade é autorizada e auditável;
- retry e reexecução idempotente não duplicam item ou comando;
- agente offline degrada para estado explícito, nunca sucesso presumido;
- testes de concorrência, permissão, E2E, carga e `./check.sh` passam.

Rollback:

- desativar fila compartilhada e manter filas individuais;
- preservar trabalhos e posições como histórico;
- impedir novos roteamentos antes de restaurar N-1.

Estado atual:

- múltiplas impressoras, agentes e operação individual já existem;
- o pacote depende de uso real com mais de uma máquina e deve começar por
  caracterização de concorrência.

## PKG-142: Integrações e descoberta técnica

Objetivo:

Reduzir atrito entre Printora e ferramentas realmente usadas, preservando
licença, autoria, versão e permissão.

Valor para o usuário:

Encontrar projeto, arquivo, erro ou perfil e transferi-lo entre ferramentas sem
copiar dado sensível ou perder contexto.

Prioridade: P1.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes concluídos: `PKG-104`, `PKG-114`, `PKG-128`, `PKG-131`, `PKG-132`.
- Pacotes ativos: nenhum.

Escopo incluído:

- integração Moonraker, OrcaSlicer e Spoolman;
- importação controlada de repositórios de modelos;
- busca unificada por projeto, arquivo, impressora, erro, componente e perfil;
- autoria, licença, checksum e versão preservados;
- estado, permissão, última sincronização e erro acionável;
- exportação aberta dos dados pertencentes ao usuário.

Fora do escopo:

- API pública, OAuth e marketplace de extensões;
- busca geométrica ou por foto no catálogo; digitalização de objeto pertence aos
  pacotes `PKG-141`, `PKG-153` e `PKG-154`;
- sincronização irrestrita de diretório local;
- conectores genéricos para CRM, e-commerce ou rede social;
- cópia automática de arquivo externo sem licença.

Lotes:

1. **Inventário de integrações** — contratos, duplicações e consumidores reais.
2. **Moonraker e OrcaSlicer** — versão, falha, permissão e round-trip.
3. **Spoolman** — material canônico, disponibilidade e degradação.
4. **Repositórios externos** — bookmark/import, licença, checksum e origem.
5. **Busca técnica unificada** — índice reconstruível, filtros e autorização.
6. **Fechamento** — timeout, quota, replay, exportação e rollback.

Critério de aceite:

- integração externa possui timeout, quota e erro acionável;
- importação preserva origem, autoria, licença e checksum;
- busca respeita permissão e não enumera item privado;
- cache ou índice pode ser reconstruído da fonte canônica;
- webhook, retry e reexecução idempotente não duplicam objeto ou evento;
- falha de um conector não derruba operação não relacionada;
- contrato, integração, busca, segurança e `./check.sh` passam.

Rollback:

- desativar conector individual sem afetar dados locais;
- preservar referência externa e último estado somente leitura;
- reconstruir índice após voltar à release N-1;
- nunca apagar arquivo importado confirmado sem autorização.

Estado atual:

- Moonraker, OrcaSlicer, bookmark externo, busca e perfis já possuem bases
  parciais;
- `PKG-139` foi fundido neste pacote;
- API pública permanece adiada; IA de reconstrução fica isolada nos pacotes de
  digitalização e não amplia a busca técnica.

## PKG-153: Reconstrução 3D por múltiplas fotos

Objetivo:

Transformar uma captura aprovada em reconstrução 3D rastreável por meio de job
assíncrono, usando fotogrametria como fonte geométrica principal e IA somente
como capacidade explícita, versionada e substituível.

Valor para o usuário:

Gerar uma primeira malha do objeto real sem instalar ferramentas técnicas,
acompanhar o processamento e entender falhas ou regiões inferidas.

Prioridade: P1.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes concluídos: `PKG-104`, `PKG-128`, `PKG-141`.
- Pacotes ativos: nenhum.

Escopo incluído:

- contrato canônico de job, tentativa, estágio, progresso, cancelamento, erro,
  custo e artefato de reconstrução;
- adapter substituível para pipeline próprio de fotogrametria e para provedor
  externo multiview homologado, sem acoplar domínio a fornecedor;
- segmentação de fundo, estimativa de poses, reconstrução esparsa/densa,
  superfície bruta e preview conforme capacidade do engine;
- fila/outbox durável, worker isolado, timeout, backpressure, circuit breaker,
  quota, retry seguro, webhook ou polling autenticado e reconciliação;
- provenance com engine, fornecedor, modelo/versão, parâmetros, fontes,
  checksums, tempo, custo e classificação de regiões observadas ou inferidas;
- artefatos intermediários privados com retenção e limpeza documentadas;
- avaliação comparativa entre pipeline próprio e serviço externo sobre o mesmo
  benchmark antes de escolher o modo padrão.

Fora do escopo:

- declarar a malha bruta pronta para impressão;
- edição CAD, parametrização, rosca ou encaixe mecânico garantido;
- executar carga pesada na Raspberry Pi ou no agente da impressora;
- treinar modelo fundacional próprio;
- publicar, cobrar, fatiar ou comandar impressora automaticamente;
- completar silenciosamente regiões não observadas sem marcar inferência.

Lotes:

1. **Contrato e avaliação técnica** — benchmark, critérios build-versus-buy,
qualidade, latência, custo, privacidade e modo degradado.
2. **Domínio e persistência** — estados, tentativas, idempotência, SQL aditivo,
outbox, artefatos e compatibilidade N/N-1.
3. **Orquestração** — fila, worker, quota, cancelamento, timeout, retry,
reconciliação, correlação e observabilidade sanitizada.
4. **Adapters** — fotogrametria própria e provedor multiview sob contrato comum,
fixtures gravadas e falha isolada.
5. **Preview e provenance** — progresso, malha bruta, cobertura, regiões
inferidas, engine/versão, custo e erro acionável.
6. **Fechamento** — segurança de upload/egress/webhook, carga, retenção,
benchmark comparativo, canário e rollback ensaiado.

Critério de aceite:

- captura aprovada produz job único e rastreável, sem bloquear a API web;
- retry, webhook duplicado, polling concorrente e reexecução idempotente não
  duplicam cobrança, job, tentativa ou artefato canônico;
- timeout, indisponibilidade ou quota do provedor degradam somente a
  reconstrução e oferecem ação de retomar, trocar modo ou cancelar;
- credencial, URL privada, foto, payload bruto e dados de outro owner não
  aparecem em log, evento, erro público ou bundle de suporte;
- saída registra exatamente engine/modelo/versão, parâmetros e checksums das
  fontes; região inferida nunca é apresentada como observada;
- cancelamento impede nova tentativa automática e preserva evidência mínima
  conforme retenção;
- benchmark mede cobertura, erro geométrico/escala quando aplicável, tempo,
  taxa de conclusão e custo, sem usar apenas avaliação visual;
- contrato, worker, adapter, segurança, carga, UI e `./check.sh` passam.

Rollback:

- desativar cada adapter ou todo o início de jobs por feature flag governada;
- deixar jobs existentes em estado terminal ou reconciliação somente leitura;
- manter fotos e artefatos canônicos privados, sem apagar dados no downgrade;
- restaurar release N-1 compatível e reprocessar somente após ação explícita do
  usuário, nunca automaticamente para consumir nova quota.

Estado atual:

- jobs, storage, objetos e infraestrutura de workers possuem bases reutilizáveis;
- contrato, persistência, fila durável, worker, cancelamento cooperativo,
  provenance, artefato privado e adapters por comando estão implementados;
- gateway COLMAP concreto passou em smoke real com dataset oficial, inclusive
  modo CPU esparso identificado como não qualificado; o modo denso continua
  reservado a worker CUDA;
- gateway Tripo implementa quatro vistas determinísticas, credencial isolada,
  polling, download defensivo e checkpoint que reaproveita a tarefa paga no
  retry; seu contrato passou somente com provider simulado;
- o modo seguro permanece desabilitado por padrão e a fixture sintética existe
  somente para contrato/teste, sem alegar reconstrução real;
- pipeline sobre objeto físico e provedor multiview ainda não estão homologados:
  faltam benchmark comparativo do mesmo objeto, credencial e chamada reais,
  carga, canário e retenção operacional antes do fechamento;
- o antigo escopo genérico de AR/escaneamento foi substituído pela demanda
  concreta de reconstrução de objeto por fotos.

## PKG-154: Qualificação e entrega de modelo imprimível

Objetivo:

Converter a reconstrução bruta em uma versão revisada, dimensionalmente
explicável e tecnicamente qualificada para download STL/3MF ou entrada no fluxo
de fatiamento, sempre com aprovação humana.

Valor para o usuário:

Entender se o modelo pode ser impresso, corrigir escala e defeitos comuns,
comparar antes/depois e evitar baixar uma malha visualmente bonita porém
inutilizável ou dimensionalmente enganosa.

Prioridade: P1.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes concluídos: `PKG-104`, `PKG-114`, `PKG-128`, `PKG-131`, `PKG-132`, `PKG-141`.
- Pacotes ativos: `PKG-153`.

Escopo incluído:

- análise determinística de malha: manifold, watertight, normais, componentes,
  faces degeneradas, auto-interseção, escala, bounding box, espessura e buracos;
- reparos reversíveis e versionados: limpeza, orientação de normais, fechamento
  controlado, remoção de componentes soltos, decimação e conversão;
- assistência por IA limitada a sugestão ou preenchimento destacado, nunca
  substituindo regra geométrica nem aprovação humana;
- revisão de escala e dimensões críticas informadas pelo usuário, com erro,
  confiança, origem da medida e comparação antes/depois;
- visualizador com mapa de cobertura, áreas observadas/inferidas/reparadas,
  alertas, limitações e comparação da malha bruta com a qualificada;
- snapshot imutável do artefato aprovado, manifesto, checksum, provenance,
  download STL/3MF e criação opcional de job de fatiamento;
- piloto físico com objetos de referência medidos por paquímetro e registro de
  resultado, falha, material, perfil e desvio dimensional;
- política explícita para privacidade, retenção, custo, opt-out, revisão humana
  e denúncia de resultado inadequado.

Fora do escopo:

- garantir réplica metrológica, peça mecânica funcional, encaixe, rosca ou
  tolerância sem validação física e CAD apropriado;
- ocultar, suavizar ou completar defeito silenciosamente;
- publicar modelo, iniciar fatiamento ou enviar à impressora sem aprovação;
- edição CAD universal no navegador;
- usar feedback privado para treinamento sem consentimento separado.

Lotes:

1. **Qualidade e tolerância** — invariantes, relatório, benchmark, classes de
uso e linguagem sem promessa indevida.
2. **Pipeline de reparo** — operações determinísticas, reversibilidade,
manifesto, idempotência e limites de recurso.
3. **Revisão métrica** — escala, dimensão conhecida, medidas críticas,
incerteza e bloqueios para uso mecânico.
4. **Assistência e revisão humana** — sugestões, regiões inferidas, comparação,
aceite, rejeição, opt-out e acessibilidade.
5. **Entrega no projeto** — snapshot, STL/3MF, checksum, download, fatiamento,
preflight e histórico sem publicação automática.
6. **Piloto e fechamento** — impressão física de benchmark, comparação com
paquímetro, custo/SLO, segurança, regressão, documentação e rollback ensaiado.

Critério de aceite:

- relatório bloqueia como não qualificada toda malha que viole invariantes
  configurados e explica a recuperação possível;
- operação de reparo é reprodutível, limitada e gera nova versão; original e
  versões anteriores permanecem disponíveis sem sobrescrita;
- retry e reexecução idempotente não duplicam reparo, snapshot, cobrança,
  download ou job de fatiamento;
- visualizador diferencia sem ambiguidade regiões observadas, inferidas e
  reparadas, inclusive por alternativa textual acessível;
- ausência ou incerteza de escala impede alegação de dimensão real e exige
  confirmação antes de exportar para finalidade mecânica;
- STL/3MF aprovado possui manifesto, checksum, unidade e vínculo com captura,
  reconstrução, engine e revisão humana;
- falha do reparo ou IA não altera a malha bruta nem bloqueia projetos,
  uploads, downloads ou fatiamentos não relacionados;
- piloto registra erro dimensional por eixo, taxa de sucesso de reconstrução,
  tempo, custo, falhas e classes de objeto não suportadas;
- backend, frontend, worker, SQL, contrato, segurança, benchmark físico e
  `./check.sh` passam.

Rollback:

- desativar reparo assistido, exportação ou entrada no fatiamento separadamente;
- manter snapshots já aprovados e seus manifestos legíveis em N-1;
- voltar ao download somente da malha bruta com alerta, sem promover seu estado;
- nunca apagar fotos, malhas, versões ou evidência de revisão durante rollback.

Estado atual:

- análise STL, viewer, snapshots, download e fatiamento possuem bases parciais;
- não existe qualificação específica de malha reconstruída, mapa de inferência,
  revisão dimensional ou piloto físico definido;
- a assistência por IA deixa de ser genérica e fica restrita a este fluxo,
  conforme `docs/architecture/RECONSTRUCAO_3D_POR_FOTOS.md`.
