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
- PKG-131 [P1]: Fatiamento avançado e perfis reproduzíveis
- PKG-132 [P0]: Fluxo ponta a ponta de impressão
- PKG-133 [P0]: Manutenção, diagnóstico e confiabilidade
- PKG-134 [P1]: Frota e filas de impressão
- PKG-142 [P1]: Integrações e descoberta técnica

## Portfólio Reavaliado

Estado completo e justificativa por ID:
`docs/community/PACKAGE_PORTFOLIO.csv`.

- Concluídos e preservados: `PKG-101`, `PKG-102`, `PKG-104`, `PKG-110`, `PKG-114`, `PKG-128`.
- Ativos: `PKG-126`, `PKG-131`, `PKG-132`, `PKG-133`, `PKG-134`,
  `PKG-142`.
- Fundidos em ativos: `PKG-105`, `PKG-107`, `PKG-108`, `PKG-111`,
  `PKG-113`, `PKG-121`, `PKG-125`, `PKG-127`, `PKG-129`, `PKG-139`.
- Adiados sem autorização de implementação: `PKG-109`, `PKG-130`,
  `PKG-135`, `PKG-141`, `PKG-143`, `PKG-154`.
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

## PKG-131: Fatiamento avançado e perfis reproduzíveis

Objetivo:

Importar, versionar, comparar e executar perfis de slicer sem perda silenciosa
de configuração.

Valor para o usuário:

Reproduzir uma impressão com a mesma engine, máquina, material e processo,
entendendo exatamente o que mudou.

Prioridade: P1.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes concluídos: `PKG-104`, `PKG-114`, `PKG-128`.
- Pacotes ativos: nenhum.

Escopo incluído:

- bundle nativo sanitizado de máquina, processo e filamento;
- engine, schema, versão, herança, overrides e compatibilidade;
- import/export OrcaSlicer semanticamente equivalente;
- diff compreensível e perdas explícitas entre formatos;
- revisão imutável presa ao job;
- preview e estimativas derivadas do artefato real.

Fora do escopo:

- editor universal de todos os slicers;
- orientação ou suporte por IA;
- conversão silenciosa de parâmetro desconhecido;
- sincronização cloud automática de diretórios locais;
- armazenamento de host, path, token ou credencial.

Lotes:

1. **Contrato canônico** — validar a decisão já registrada e fixtures nativas.
2. **Persistência de revisões** — SQL idempotente, checksum e imutabilidade.
3. **Importação e exportação** — round-trip OrcaSlicer N/N-1.
4. **Herança e diff** — base, override, perda e compatibilidade.
5. **Execução presa à revisão** — job, engine, artefato e resultado.
6. **Fechamento** — regressão, pacote nativo real, rollback e documentação.

Critério de aceite:

- round-trip preserva campos conhecidos e desconhecidos permitidos;
- dado operacional sensível é rejeitado;
- revisão usada pelo job não muda após edição do perfil;
- conversão com perda exige confirmação explícita;
- import repetido e reexecução idempotente não duplicam bundle ou revisão;
- fixture Orca real e controlada reproduz resultado semanticamente equivalente;
- backend, frontend, integração, SQL e `./check.sh` passam.

Rollback:

- desativar importação/edição e preservar revisões somente leitura;
- bloquear novos jobs se a engine compatível não existir;
- restaurar release N-1 sem apagar bundles ou revisões.

Estado atual:

- presets OrcaSlicer já foram versionados em `packaging/orcaslicer/profiles/`;
- a decisão `DEC-20260726-03` define o contrato, mas persistência e fluxo completo
  ainda precisam de auditoria e implementação.

## PKG-132: Fluxo ponta a ponta de impressão

Objetivo:

Fechar a jornada projeto, seleção, fatiamento, preflight, envio, monitoramento,
resultado e reimpressão sem etapas soltas ou estado enganoso.

Valor para o usuário:

Concluir uma impressão segura e reproduzível pelo Printora, com menos troca de
ferramenta e diagnóstico claro quando algo falhar.

Prioridade: P0.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes concluídos: `PKG-104`, `PKG-110`, `PKG-114`, `PKG-128`.
- Pacotes ativos: `PKG-131`.

Escopo incluído:

- seleção de projeto, snapshot, peças e quantidades;
- validação de arquivo, perfil, material e impressora;
- geração e aprovação visual do G-code;
- preflight local e remoto;
- entrega auditada pelo agente;
- monitoramento ligado ao trabalho correto;
- resultado, consumo, evidência e reimpressão.

Fora do escopo:

- marketplace ou pedido comercial;
- roteamento de fazenda;
- pausa ou cancelamento autônomo por IA;
- comando físico vindo de relação social;
- bypass de confirmação, step-up ou estado real do Moonraker.

Lotes:

1. **Caracterização ponta a ponta** — mapear contratos existentes e lacunas.
2. **Seleção e snapshot** — projeto, peças, revisão e perfil imutáveis.
3. **Preflight** — segurança de modelo, material, máquina e estado remoto.
4. **G-code e entrega** — preview, confirmação, upload e journal.
5. **Monitoramento e resultado** — vínculo correto, consumo, falha e evidência.
6. **Reimpressão e fechamento** — reprodução, regressão física segura e rollback.

Critério de aceite:

- uma jornada completa usa um único snapshot rastreável;
- preflight falho não envia nem agenda comando;
- estado exibido pertence à impressora e ao trabalho selecionados;
- retry de upload ou job não duplica arquivo nem comando físico;
- reexecução idempotente preserva uma entrega e um histórico canônicos;
- falha intermediária oferece retomada ou rollback acionável;
- testes unitários, contrato, integração, E2E, smoke físico seguro e
  `./check.sh` passam.

Rollback:

- manter Administração como fallback técnico enquanto o fluxo novo é validado;
- desativar entrada nova e preservar jobs, arquivos e histórico;
- release N-1 continua lendo contratos N/N-1;
- nenhuma reversão física de dados sem backup e confirmação.

Estado atual:

- projetos, slicing, preflight, entrega, G-code, monitoramento e histórico já
  existem em partes;
- este pacote consolida e valida o fluxo real em vez de duplicar endpoints.

## PKG-133: Manutenção, diagnóstico e confiabilidade

Objetivo:

Reduzir parada, recorrência de falha e diagnóstico manual usando histórico real
da impressora.

Valor para o usuário:

Saber o que verificar, quando manter e quais alterações precederam uma falha.

Prioridade: P0.

Dependências:

- Base consolidada: `PKG-01` a `PKG-100`.
- Pacotes concluídos: `PKG-104`, `PKG-114`.
- Pacotes ativos: `PKG-132`.

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
- Pacotes concluídos: `PKG-104`, `PKG-114`.
- Pacotes ativos: `PKG-132`, `PKG-133`.

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
- Pacotes concluídos: `PKG-104`, `PKG-114`, `PKG-128`.
- Pacotes ativos: `PKG-131`, `PKG-132`.

Escopo incluído:

- integração Moonraker, OrcaSlicer e Spoolman;
- importação controlada de repositórios de modelos;
- busca unificada por projeto, arquivo, impressora, erro, componente e perfil;
- autoria, licença, checksum e versão preservados;
- estado, permissão, última sincronização e erro acionável;
- exportação aberta dos dados pertencentes ao usuário.

Fora do escopo:

- API pública, OAuth e marketplace de extensões;
- busca geométrica, por foto ou IA sem demanda comprovada;
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
- API pública e IA permanecem adiadas.
