# DECISOES.md

Registro de decisoes arquiteturais, tecnicas e operacionais relevantes do monorepo Printora.

## Regras

- Registrar escolhas que afetam arquitetura, stack, operacao, testes, seguranca, rollback ou manutencao.
- Nao registrar decisao trivial.
- Se uma decisao substituir outra, marcar a anterior como `substituida`.
- Se uma decisao for revertida, registrar motivo e plano de reversao.
- Decisoes aceitas valem como fonte de verdade ate serem substituidas.

## Modelo

```txt
### DEC-YYYYMMDD-01 - Titulo

Status: proposta | aceita | substituida | revertida
Data:
Contexto:
Decisao:
Alternativas consideradas:
Consequencias:
Impacto em testes:
Impacto em rollback:
Como reverter:
Referencias:
```

## Decisoes

### DEC-20260802-01 - Onboarding deriva conclusão do estado operacional existente

Status: aceita
Data: 2026-08-02
Contexto: setup, cadastro de impressora, Moonraker, pareamento, projetos,
fatiamento e preflight já possuíam contratos próprios. Criar um segundo backend
de wizard duplicaria estado, poderia afirmar sucesso divergente e aumentaria o
risco de expor credenciais ou repetir efeitos.
Decisao: a tela global `onboarding` agrega somente leituras autenticadas dos
contratos existentes. Uma etapa remota conclui apenas com evidência real:
Moonraker conectado, agente online, projeto existente e preflight aprovado. O
único estado novo é o passo de retorno salvo no navegador, sem segredo nem dado
operacional; falha de dependência preserva esse passo e mantém a conclusão como
não confirmada. As ações encaminham para os fluxos canônicos de impressora,
agente e projeto.
Alternativas consideradas: persistir wizard no backend; duplicar cadastro e
pareamento dentro de um formulário único; marcar etapas manualmente; usar dados
de demonstração como sucesso.
Consequencias: a camada guiada pode ser removida sem apagar dados e não cria
novo schema, mas depende da disponibilidade dos endpoints canônicos para
confirmar avanço. A tela é carregada de forma lazy; o orçamento total do bundle
foi ajustado em menos de 1%, preservando os limites por entrada, asset, CSS e
gzip.
Impacto em testes: regra pura, componente e E2E desktop/mobile cobrem ordem,
retomada, timeout, teclado, Axe e overflow; testes existentes continuam cobrindo
token, duplicidade e isolamento do pareamento.
Impacto em rollback: baixo; remover seção, chamada da Visão geral e arquivos do
onboarding restaura integralmente os fluxos técnicos existentes.
Como reverter: reverter a composição da seção e seu service local, sem remover
impressoras, agentes, projetos, jobs ou preflights.
Referencias: `frontend/src/screens/OnboardingScreen.tsx`,
`frontend/src/services/onboardingProgress.ts`, `TELAS.md`, `TESTES.md`,
`docs/community/PKG_110_EVIDENCE.md`.

### DEC-20260802-02 - Spoolman permanece canônico e é lido pelo agente local

Status: aceita
Data: 2026-08-02
Contexto: o Spoolman já é a ferramenta especializada para inventário de
filamento e normalmente está acessível apenas na rede da impressora. Conectar o
cloud diretamente a uma URL privada ampliaria superfície de SSRF e criaria uma
segunda autoridade de peso. Ao mesmo tempo, usuários sem Spoolman precisam de
inventário local simples, consumo confiável e orientação antes de imprimir.
Decisao: o Printora consulta o Spoolman somente pelo agente pareado e pelo proxy
read-only do Moonraker. Registros importados são cache owner-scoped e não podem
ser editados no Printora. Spools locais permanecem editáveis e usam ledger
imutável com chave de idempotência; somente consumo `confirmed` reduz o peso,
uma única vez e de forma atômica. Compatibilidade falha de forma conservadora:
ausência de perfil, peso, máquina ou condição ambiental resulta em `unknown` ou
`incompatible`, nunca em afirmação positiva inventada.
Alternativas consideradas: cloud conectar diretamente ao Spoolman; copiar e
editar o inventário externo; decrementar peso no registro de planejamento;
calcular compatibilidade apenas no frontend.
Consequencias: a integração degrada sem bloquear spools locais, mas depende de
agente e Moonraker disponíveis para sincronizar. Medidas e consumo confirmado
são históricos imutáveis. A nova tela global é lazy; o orçamento total foi
ajustado em aproximadamente 1,2%, mantendo limites individuais e de entrada.
Impacto em testes: schema SQLite/PostgreSQL, owner isolation, importação,
idempotência, concorrência lógica, compatibilidade conservadora, agente Go,
UI unitária e E2E desktop/mobile cobrem o fluxo.
Impacto em rollback: restaurar a release N-1 desativa os consumidores novos,
sem apagar tabelas, IDs externos, consumo ou medidas. O Spoolman continua
canônico durante todo o rollback.
Como reverter: retirar seção e rotas do módulo, desabilitar o job read-only no
agente e preservar o schema aditivo sem executar `DROP` ou `DELETE`.
Referencias: `backend/app/modules/operations/materials/`,
`agent/internal/agent/spoolman.go`, `backend/sql/088_material_inventory.sql`,
`backend/sql/postgresql/020_material_inventory.sql`, `TELAS.md`, `TESTES.md`,
`RUNBOOK.md`, `docs/community/PKG_114_EVIDENCE.md`.

### DEC-20260727-01 - Portfólio ativo substitui execução integral do inventário comunitário

Status: aceita
Data: 2026-07-27
Contexto: o inventário comunitário de 55 frentes foi convertido em 55 pacotes,
440 capacidades, 3.080 requisitos e 440 famílias de tela obrigatórios. A regra
numérica fazia o fluxo de impressão depender de rede social, marketplace,
educação, finanças e experimentos sem demanda comprovada. A marcação `ausente`
também divergia de contratos e telas já existentes.
Decisão: manter o inventário gerado apenas como histórico de ideias e usar
`docs/community/PACKAGE_PORTFOLIO.csv` como estado oficial dos IDs
`PKG-101` a `PKG-155`. `DEMANDAS.md` contém somente dez pacotes ativos.
Dependências passam a ser técnicas e explícitas em
`PACKAGE_ARCHITECTURE.csv`; número não cria dependência. IDs podem ficar
`completed`, `active`, `merged`, `deferred` ou `cancelled`. Pacote não ativo
não autoriza código nem pode ser dependência. Função já existente não é
removida automaticamente.
Alternativas consideradas: executar os 55 pacotes; apagar todo o inventário;
manter a sequência e pular pacotes informalmente; renumerar os pacotes ativos.
Consequências: o backlog volta ao núcleo operacional, preserva rastreabilidade
histórica e permite chegar a fatiamento e impressão sem construir produtos
paralelos. Reativação exige nova decisão e hipótese mensurável.
Impacto em testes: o validador passa a conferir portfólio completo, matriz dos
ativos, destino de fusões, dependências explícitas, ordem topológica e estrutura
de pacote. O gerador continua verificando a reprodução do inventário histórico.
Impacto em rollback: baixo e documental; restaurar a versão anterior dos
documentos e validadores. Não remover nem restaurar runtime ou dados.
Como reverter: reverter conjuntamente `DEMANDAS.md`, portfólio, matriz, padrão,
gerador, validador, testes e documentos de governança.
Referências: `DEMANDAS.md`, `docs/community/PACKAGE_PORTFOLIO.csv`,
`docs/community/PACKAGE_ARCHITECTURE.csv`,
`docs/community/PACKAGE_MODELING_REVIEW.md`.

### DEC-20260726-02 - Deploy paralelo com retenção somente de releases vinculados

Status: aceita
Data: 2026-07-26
Contexto: o servidor acumulou 251 releases imutáveis porque cada publicação
criava um diretório novo e não existia retenção. O preflight de capacidade
estava depois de aproximadamente 16 minutos de gates sequenciais e os testes
Python eram executados uma vez com cobertura e outra pelo `check.sh`.
Decisao: executar preflight de infraestrutura antes da CI; executar static,
E2E, property/fuzz, mutation e cobertura em jobs paralelos sobre o mesmo SHA;
empacotar e publicar somente depois de todos passarem; eliminar a segunda
execução do pytest quando o gate de cobertura já o executou. Após o blue/green,
remover automaticamente apenas diretórios de release sem vínculo por `current`,
`blue`, `green` ou `replica`. Limitar o journal persistente a 2 GB e reservar
15% do filesystem.
Alternativas consideradas: manter todos os releases; preservar os últimos cinco
mesmo sem vínculo; apagar tudo exceto `current`; retirar o gate de capacidade;
continuar com CI sequencial.
Consequencias: normalmente permanecem dois releases, ativo e rollback N-1, sem
acúmulo histórico. Falha de infraestrutura aparece antes de instalar
dependências. Os gates preservam a mesma cobertura, mas o tempo de parede passa
a ser dominado pelo gate paralelo mais lento. Git e bundle verificável são a
fonte para reconstruir releases removidos.
Impacto em testes: testes de topologia da retenção, sintaxe shell/YAML, gate de
empacotamento, `./check.sh` e execução real do workflow.
Impacto em rollback: o rollback imediato N-1 permanece porque todo alvo de
symlink é protegido. Releases antigos removidos exigem reconstrução a partir do
SHA Git; dados, banco, backups e WAL não são removidos.
Como reverter: remover a chamada automática de retenção, restaurar o workflow
sequencial e remover o limite específico do journald. Não restaurar diretórios
antigos sem validar SHA, bundle e dependências.
Referencias: `.github/workflows/deploy-cloud.yml`,
`scripts/cloud/retain-releases.sh`, `scripts/cloud/deploy-blue-green.sh`,
`packaging/systemd/journald-printora-cloud.conf`, `RUNBOOK.md`.

### DEC-20260726-01 - Backlog ativo separado do histórico consolidado

Status: aceita
Data: 2026-07-26
Vigência: parcialmente superada pela `DEC-20260727-01`; permanece válida apenas
para a separação entre histórico `PKG-01..100` e backlog ativo.
Contexto: `DEMANDAS.md` acumulava os detalhes completos de cem pacotes
consolidados e ainda precisava receber o programa comunitário plurianual com 55
frentes, 440 capacidades, 3.080 requisitos atômicos e 440 famílias de tela.
Manter tudo no mesmo fluxo dificultaria localizar trabalho ativo, enquanto
resumir ou apagar os pacotes antigos destruiria contexto, riscos e evidências.
Decisao: preservar integralmente o antigo `DEMANDAS.md` em
`DEMANDAS_CONSOLIDADAS_PKG_01_100.md` e usar `DEMANDAS.md` como backlog
executável ativo. Os pacotes `PKG-101` a `PKG-155` são numerados em ordem
topológica de implementação, dependem somente de IDs menores, correspondem uma
vez cada às 55 frentes e referenciam intervalos exclusivos de `COM`, `CAP` e
`SCR`. Prioridade social P0-P4 permanece atributo independente da numeração. O
número 101 não representa pacote de evidência residual: esse pacote nunca foi
registrado, e as dispensas históricas permanecem nos PKG-97 e PKG-98. O gate
`scripts/validate-demand-package-dependencies.py` impede lacuna, referência
futura e ausência de declaração de entrega isolada.
Alternativas consideradas: manter todos os pacotes no mesmo arquivo; resumir os
pacotes antigos; criar poucos pacotes genéricos sem rastreabilidade atômica;
criar um pacote por cada um dos 3.080 itens.
Consequencias: janelas futuras encontram somente trabalho ativo no arquivo
principal, executam os pacotes em ordem numérica e continuam capazes de
consultar a descrição histórica integral. Cada pacote comunitário possui oito
lotes de capacidade, dependências anteriores explícitas e cobre as sete lentes
de entrega e a família de tela correspondente, evitando perda, sobreposição e
espera por pacote futuro.
Impacto em testes: validação documental de contagem, intervalos sem lacunas,
IDs únicos, links, diff e `./check.sh`; não altera runtime, banco ou servidor.
Impacto em rollback: baixo e somente documental.
Como reverter: restaurar o conteúdo histórico como `DEMANDAS.md` e remover a
separação, preservando o arquivo comunitário antes da reversão.
Referencias: `DEMANDAS.md`, `DEMANDAS_CONSOLIDADAS_PKG_01_100.md`,
`docs/community/COMMUNITY_BACKLOG.md`,
`docs/community/COMMUNITY_SCREENS.md`, `docs/community/MASTER_PLAN.md`.

### DEC-20260720-05 - Operação ociosa mostra atalhos, não gerenciador de arquivos

Status: aceita
Data: 2026-07-20
Contexto: depois da criação de `Arquivos G-code`, a aba `Operacao` não deve competir com o gerenciador completo quando a impressora está ociosa. A mesma área precisa continuar densa e útil durante impressão ativa, sem preservar preview ou progresso antigo.
Decisao: em estado ocioso, `Operacao` mostra somente estado compacto, último trabalho confiável quando houver metadado e poucos atalhos recentes. A tabela completa, filtros, detalhe, preview e ações por arquivo ficam na aba `Arquivos G-code`, aberta por CTA a partir da Operação.
Alternativas consideradas: manter tabela completa na Operação; ocultar todo G-code quando ociosa; duplicar filtros e drawer na Operação; manter preview do job anterior como fallback visual.
Consequencias: a aba Operação fica mais objetiva em standby/offline/erro e reduz risco de acionar gestão de arquivo no lugar errado. O usuário ainda chega rápido aos arquivos, mas o fluxo completo fica no módulo dedicado.
Impacto em testes: build frontend e `RUN_FRONTEND_CHECKS=1 ./check.sh`; validação live/mutável foi evitada durante impressão ativa.
Impacto em rollback: baixo; restaurar a tabela antiga na Operação ou esconder os atalhos não altera backend/agente.
Como reverter: remover o CTA/atalhos compactos de `MonitoringDashboard` e voltar `IdleGcodeFilesPanel` para tabela local ou estado vazio.
Referencias: `frontend/src/components/monitoring/MonitoringDashboard.tsx`, `frontend/src/screens/MonitoringScreen.tsx`, `frontend/src/styles/monitoring.css`, `TELAS.md`.

### DEC-20260720-04 - Preview G-code usa módulo reutilizável com modos explícitos

Status: aceita
Data: 2026-07-20
Contexto: `Operacao`, `Arquivos G-code`, projetos e futuro fatiamento precisam compartilhar a mesma prévia 3D sem duplicar parser, baixar G-code em polling ou acoplar UI de arquivo ao estado live da impressão.
Decisao: manter o `GcodePrintViewer` como componente visual reutilizável e extrair a lógica pura de offsets de camada e alvo de renderização para `frontend/src/components/monitoring/gcodePreview.ts`. O viewer aceita modos explícitos (`progress`, `full`, `until_layer`, `current_layer`) e continua carregando G-code completo apenas sob demanda pelo cache existente.
Alternativas consideradas: manter prévia textual no drawer; duplicar viewer em `Arquivos G-code`; buscar G-code completo junto da listagem; criar nova renderização própria em canvas antes de estabilizar o contrato atual.
Consequencias: a prévia passa a ser consistente entre Operação e gerenciador de arquivos, com menor risco de divergência visual e teste determinístico para seleção de camada/progresso. O custo de renderização continua no navegador quando o usuário abre a prévia, não no agente nem no polling.
Impacto em testes: `frontend/tests/gcodePreview.test.mjs`, build frontend e `RUN_FRONTEND_CHECKS=1 ./check.sh`.
Impacto em rollback: baixo a médio; remover o uso no drawer preserva a prévia operacional, mas os modos do componente comum podem permanecer para progresso live.
Como reverter: ocultar o botão de prévia 3D em `GcodeFilesScreen`, restaurar download/preview textual sob demanda e manter `GcodePrintViewer` apenas em `Operacao`.
Referencias: `frontend/src/components/monitoring/GcodePrintViewer.tsx`, `frontend/src/components/monitoring/gcodePreview.ts`, `frontend/src/screens/GcodeFilesScreen.tsx`, `frontend/tests/gcodePreview.test.mjs`, `TELAS.md`.

### DEC-20260720-03 - Ações de arquivo G-code usam job remoto com preflight

Status: aceita
Data: 2026-07-20
Contexto: a aba `Arquivos G-code` precisa permitir imprimir, renomear, mover, duplicar, excluir, baixar e inspecionar histórico sem expor Moonraker direto ao navegador e sem arriscar a peça em andamento.
Decisao: manter ações somente leitura no navegador/backend sob demanda e criar o job `remote_gcode_file_action` no agente para operações mutáveis. O backend exige usuário autenticado, confirmação textual e step-up para mutações; o agente reexecuta preflight remoto e usa endpoints Moonraker específicos (`/printer/print/start`, `/server/files/move`, `/server/files/copy` e `DELETE /server/files/gcodes/...`) com caminhos relativos sanitizados.
Alternativas consideradas: enviar `SDCARD_PRINT_FILE` por G-code manual; chamar Moonraker direto do frontend; persistir uma nova tabela de auditoria; liberar ações mutáveis apenas pela UI sem preflight no agente.
Consequencias: ações de arquivo ficam rastreáveis em `agent_jobs`, sem G-code bruto em logs persistidos e sem token/IP/caminho absoluto. Durante impressão ativa, o backend bloqueia a UI e o agente bloqueia novamente antes de chamar Moonraker. Agentes antigos ficam marcados como desatualizados até `0.1.33`.
Impacto em testes: testes backend da matriz/contrato de ações, testes Go de bloqueio durante impressão e path de delete em subpasta, build frontend e `./check.sh`.
Impacto em rollback: médio; reverter remove os botões/drawer de ação e o job remoto novo, mantendo a listagem read-only do PKG-82.
Como reverter: ocultar ações protegidas no drawer, remover endpoints `/gcode-files/detail` e `/gcode-files/actions`, remover `remote_gcode_file_action` do agente e publicar agente anterior. Arquivos já alterados pelo Moonraker não devem ser revertidos por automação sem confirmação explícita.
Referencias: `backend/app/gcode_files.py`, `backend/app/routes/operation.py`, `agent/internal/agent/gcode_file_actions.go`, `frontend/src/screens/GcodeFilesScreen.tsx`, `TELAS.md`.

### DEC-20260720-02 - Arquivos G-code usam listagem remota leve e cache curto

Status: aceita
Data: 2026-07-20
Contexto: a aba `Arquivos G-code` precisa listar arquivos, diretórios, metadados e thumbnails do Moonraker sem transformar a aba `Operacao` em gerenciador de arquivos e sem baixar G-code completo em polling.
Decisao: criar o job read-only `remote_gcode_files_list` no agente para consultar `/server/files/list?root=gcodes`, metadados por `/server/files/metadata`, espaço por `/server/files/directory` e thumbnails pequenas sob limite. O agente mantém cache curto de 20 segundos e o backend expõe `/api/printers/{printer_id}/gcode-files`; download/cache do G-code completo continua sob demanda pelo contrato existente de preview.
Alternativas consideradas: continuar usando `operation/status` como fonte completa; baixar G-code completo para extrair metadados; consultar Moonraker diretamente do frontend; persistir cache em SQLite já no primeiro pacote.
Consequencias: a lista completa fica separada da Operação, reduz polling na Raspberry e preserva caminho seguro para agentes antigos. Metadados indisponíveis aparecem como ausência real, e a tela pode evoluir para detalhe/ações sem acoplar UI a Moonraker direto.
Impacto em testes: testes backend do normalizador/contrato, testes Go do agente e build frontend.
Impacto em rollback: baixo; remover a aba/rota nova volta a Operação ociosa ao atalho compacto e mantém o job remoto inerte até agente antigo/novo convergir.
Como reverter: ocultar a aba `gcode-files`, remover chamada ao endpoint novo no frontend e manter o backend retornando `unsupported` para clientes antigos; o agente pode preservar o job como compatibilidade read-only.
Referencias: `backend/app/gcode_files.py`, `backend/app/routes/operation.py`, `agent/internal/agent/gcode_files.go`, `frontend/src/screens/GcodeFilesScreen.tsx`, `TELAS.md`.

### DEC-20260720-01 - Preview operacional renderiza G-code completo no navegador

Status: aceita
Data: 2026-07-20
Contexto: a aba `Operacao` precisa mostrar a peça impressa com paridade visual próxima ao G-code Viewer do Mainsail sem aumentar CPU do agente. A amostragem compacta do agente servia como fallback, mas gerava buracos/volumes falsos e controles customizados de navegação podiam sobrepor texto e miniaturas.
Decisao: cachear/servir o G-code completo sob demanda via agente/backend e renderizar no frontend com `@sindarius/gcodeviewer`, carregando o arquivo uma vez e movendo o progresso por `file_position` com fallback por camada/progresso. O agente fica como ponte de arquivo e não recalcula a cena a cada snapshot. O navegador usa o viewbox nativo da biblioteca; a prévia SVG amostrada fica apenas como fallback compacto.
Alternativas consideradas: reprocessar G-code a cada snapshot; manter parser SVG amostrado como principal; delegar renderização ao agente; construir sólido sintético a partir de linhas parciais.
Consequencias: reduz CPU no agente e melhora paridade com Mainsail, com custo de renderização concentrado no navegador durante o carregamento inicial. Arquivos grandes podem demorar para carregar, mas não bloqueiam comandos protegidos. A precisão visual fica limitada pelo viewer de G-code; reconstrução de malha exatamente igual ao Orca exigiria futuro pipeline com STL/3MF/slicer.
Impacto em testes: build frontend, testes Go do agente, compile backend, `./check.sh` e `RUN_FRONTEND_CHECKS=1 ./check.sh`.
Impacto em rollback: médio; exige rebaixar a UI para fallback amostrado e desativar cache remoto de G-code.
Como reverter: ocultar `GcodePrintViewer`, voltar `PrintPreview` como única prévia operacional e manter endpoint/cache como legado inerte até remover em pacote posterior.
Referencias: `frontend/src/components/monitoring/GcodePrintViewer.tsx`, `backend/app/gcode_cache.py`, `agent/internal/agent/gcode_cache.go`, `TELAS.md`.

### DEC-20260618-01 - Projeto de impressão é a entidade raiz de conteúdo imprimível

Status: aceita
Data: 2026-06-18
Contexto: a modelagem anterior nasceu em torno de biblioteca social, arquivos por comunidade e fluxo de fatiamento/envio em Administração. Esse desenho deixa comunidade parecendo dona do conteúdo, dificulta projetos com múltiplos arquivos STL/3MF/ZIP e mistura descoberta social com operação diária de impressão.
Decisao: adotar `Projeto de impressão` como entidade raiz para conteúdo imprimível. Arquivos do projeto, versões/snapshots, compartilhamentos em comunidade, publicação, jobs de fatiamento, entrega/G-code e histórico de impressão são relações ou derivados do projeto. Comunidade é apenas canal de compartilhamento/descoberta em relação N:N; Administração é apenas configuração, diagnóstico, política e fallback operacional. Jobs, G-code e histórico devem apontar para snapshot imutável do projeto e dos arquivos selecionados.
Alternativas consideradas: manter modelo/arquivo como item da comunidade; criar cópias por comunidade; manter fatiamento diário em Administração; tratar cada STL como projeto independente.
Consequencias: o mesmo projeto pode servir para todo o sistema, aparecer em zero, uma ou várias comunidades sem duplicação e conter múltiplos arquivos/peças. Fluxos legados de comunidade/Administração devem ser migrados, rebaixados ou removidos somente após a área nova estar validada. Decisões anteriores sobre biblioteca social passam a ser interpretadas como base legada a ser reaproveitada/migrada, não como raiz final do domínio.
Impacto em testes: testes dos PKG-77 a PKG-81 devem cobrir projeto multi-arquivo, snapshot imutável, relação N:N com comunidades, privacidade, publicação independente, fatiamento por seleção de arquivos, histórico sanitizado e regressão dos atalhos legados.
Impacto em rollback: médio; a implementação deve manter compatibilidade ou redirects enquanto dados legados existirem. Remoção de telas/rotas antigas só ocorre depois de validação do fluxo novo.
Como reverter: reativar entradas legadas de biblioteca/comunidade/Administração como fluxo principal e tratar projetos como camada de apresentação, mantendo dados criados como legado; reversão física de dados só com backup SQLite e confirmação explícita.
Referencias: `DEMANDAS.md` PKG-77 a PKG-81, `TELAS.md` Distribuição de conteúdo, `backend/sql/068_print_projects_core.sql`, `backend/sql/069_print_project_experience.sql`, `/api/print-projects`.

### DEC-20260618-02 - Job de fatiamento por projeto congela snapshot e arquivos selecionados

Status: aceita
Data: 2026-06-18
Contexto: o fluxo diário de fatiamento saiu de Administração e passou a partir de `Projetos de impressão > Meus projetos`. O usuário pode alterar título, arquivos, publicação e compartilhamentos depois de criar um job, mas artefatos, preflight, entrega e histórico precisam continuar auditáveis.
Decisao: todo job criado a partir de projeto salvo grava `print_project_id`, `print_project_version_id`, snapshot do projeto e snapshot dos arquivos selecionados no momento da criação. Referências externas sem arquivo local validado não entram em seleção de fatiamento. Administração permanece como configuração/diagnóstico/fallback, não como criador principal de job diário.
Alternativas consideradas: referenciar apenas o projeto atual; copiar arquivos para uma entidade nova de job; manter criação diária no pipeline administrativo; aceitar bookmark externo como modelo fatiável.
Consequencias: alterações posteriores no projeto não mudam jobs existentes, e consumidores de preflight/G-code/histórico podem usar o snapshot do job como fonte auditável. O schema adiciona colunas em `slicing_jobs`, mantendo jobs legados sem projeto como compatibilidade.
Impacto em testes: cobrir criação por projeto, snapshot imutável, link externo bloqueado, seleção parcial de arquivos, compatibilidade de impressora/perfil e ausência de engine com erro acionável.
Impacto em rollback: baixo/médio; a aplicação pode voltar a listar jobs legados sem projeto, mas colunas aplicadas devem permanecer ou o banco deve ser restaurado por backup SQLite do versionador.
Como reverter: reverter rotas/serviços/UI de job por projeto e tratar colunas novas como legado técnico; remoção física de colunas/tabelas só por restauração de backup e confirmação explícita.
Referencias: `backend/sql/072_project_slicing_jobs.sql`, `backend/app/slicing_pipeline.py`, `backend/app/routes/slicing.py`, `frontend/src/screens/PrintProjectsScreen.tsx`.

### DEC-20260618-03 - Envio e histórico operacionais pertencem ao projeto

Status: aceita
Data: 2026-06-18
Contexto: preflight, entrega de G-code e histórico já existiam no pipeline administrativo, mas o fluxo diário precisa partir de `Projetos de impressão > Meus projetos` sem transformar Administração ou Comunidade em tela operacional principal.
Decisao: reaproveitar os contratos existentes de preflight, entrega, rollback, histórico e feedback, exibindo e acionando essas etapas no painel do projeto a partir dos jobs vinculados ao snapshot. Administração fica como diagnóstico/fallback. Histórico público continua sendo sanitizado pelo backend e feedback público só aceita foto HTTPS.
Alternativas consideradas: criar rotas duplicadas específicas de projeto para cada etapa; manter envio apenas em Administração; permitir envio a partir de comunidade; expor dados privados no histórico do projeto para facilitar suporte.
Consequencias: a operação diária fica no contexto correto do projeto, com menor duplicação de backend. A UI filtra jobs/preflights/entregas/histórico pelo vínculo do job ao projeto, enquanto o backend preserva as garantias de preflight aprovado, confirmação textual/step-up e sanitização pública.
Impacto em testes: cobrir salvar/enviar a partir de job de projeto, confirmação textual, histórico por projeto, feedback e privacidade pública sem dados de impressora privada.
Impacto em rollback: baixo; contratos de backend seguem compartilhados. Reversão principal remove a superfície operacional do projeto e mantém Administração como fallback técnico.
Como reverter: reverter painel de envio/histórico no projeto e ajustes frontend; manter dados de entrega/histórico como legado auditável.
Referencias: `frontend/src/screens/PrintProjectsScreen.tsx`, `frontend/src/services/slicingApi.ts`, `backend/tests/test_print_history.py`, `backend/app/print_delivery.py`, `backend/app/print_history.py`.

### DEC-20260617-01 - Impressão real alimenta ranking sem expor telemetria privada

Status: aceita
Data: 2026-06-17
Vigência: válida como regra de privacidade/ranking, mas subordinada à DEC-20260618-01; sinais públicos novos apontam para projeto central e snapshot, não para cópia por comunidade.
Contexto: resultados reais de impressão precisam melhorar recomendações e troubleshooting, mas impressora, Moonraker e telemetria detalhada são dados privados.
Decisao: criar histórico de impressão ligado ao fluxo de entrega de G-code, com feedback público ou privado e telemetria mínima segura. Feedback de sucesso/falha atualiza `social_quality_signals` com sinais explicáveis, sem publicar identificador privado de impressora.
Alternativas consideradas: usar apenas downloads/favoritos; expor telemetria completa; criar ranking separado para impressão.
Consequencias: recomendações passam a considerar resultado real de impressão mantendo privacidade e rollback simples por domínio.
Impacto em testes: testes focados devem cobrir privacidade do payload, feedback, atualização de ranking e validação de foto HTTPS.
Impacto em rollback: médio; há novo script SQLite `065_print_job_history.sql`.
Como reverter: remover endpoints/UI de histórico e restaurar backup SQLite anterior ao script `065_print_job_history.sql` se os dados não puderem permanecer como legado.
Referencias: `backend/sql/065_print_job_history.sql`, `backend/app/print_history.py`, `backend/app/routes/slicing.py`, `frontend/src/screens/SettingsScreen.tsx`.

### DEC-20260617-02 - Premium e patrocinado exigem revisão e transparência

Status: aceita
Data: 2026-06-17
Vigência: válida como regra comercial, mas subordinada à DEC-20260618-01; classificação comercial nova pertence ao projeto central, não à comunidade.
Contexto: o marketplace precisa preparar conteúdo premium/curado/patrocinado sem cobrar de fato e sem confundir promoção com recomendação técnica neutra.
Decisao: adicionar classificação comercial no item da biblioteca, revisão administrativa separada e aviso de transparência no payload/UI. Conteúdo premium ou patrocinado só pode ficar público com revisão aprovada.
Alternativas consideradas: criar marketplace separado; permitir premium sem revisão; misturar promoção no ranking técnico.
Consequencias: a biblioteca comunitária segue livre, promoção fica auditável e cobrança real permanece fora do escopo.
Impacto em testes: testes devem cobrir bloqueio de publicação sem revisão, aprovação administrativa e aviso de patrocinado.
Impacto em rollback: médio; há novo script SQLite `066_social_library_commercial_curation.sql`.
Como reverter: remover campos/rota/UI comerciais e restaurar backup SQLite anterior ao script `066_social_library_commercial_curation.sql` se necessário.
Referencias: `backend/sql/066_social_library_commercial_curation.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`.

### DEC-20260617-03 - Integração externa começa como bookmark controlado

Status: aceita
Data: 2026-06-17
Vigência: válida como mecanismo legado/base, mas subordinada à DEC-20260618-01; referências externas novas pertencem a projetos de impressão.
Contexto: importar bibliotecas externas pode gerar risco legal, dependência instável e cópia indevida de arquivo.
Decisao: implementar fonte externa, preview determinístico e referência/bookmark por URL como primeira etapa. O sistema registra metadados, licença, atribuição e checksum opcional, mas não copia arquivo externo sem fluxo futuro específico.
Alternativas consideradas: baixar arquivo externo automaticamente; integrar API de repositórios externos já no primeiro lote; guardar apenas URL livre em descrição.
Consequencias: integração externa fica segura, auditável e sem dependência de serviço externo no teste local.
Impacto em testes: testes devem cobrir atribuição obrigatória, bookmark sem cópia, preview por URL e deduplicação por checksum.
Impacto em rollback: médio; há novo script SQLite `067_external_library_imports.sql`.
Como reverter: remover endpoints/UI de fontes externas e restaurar backup SQLite anterior ao script `067_external_library_imports.sql` se necessário.
Referencias: `backend/sql/067_external_library_imports.sql`, `backend/app/external_library.py`, `backend/app/routes/external_library.py`, `frontend/src/screens/PublicCommunityScreen.tsx`.

### DEC-20260616-14 - Notificacoes sociais ficam separadas de alertas operacionais

Status: aceita
Data: 2026-06-16
Contexto: interacoes sociais, comunidades e conteudo acompanhado precisam notificar o usuario sem competir com alertas de impressora, agente, firmware, Moonraker ou manutencao. Misturar esses fluxos criaria ruido operacional e risco de tratar like/resposta como incidente tecnico.
Decisao: criar o dominio `social_notifications`, com SQL proprio em `058_social_notifications.sql`, central in-app, preferencias por tipo, acompanhamento de conteudo e digest opcional. Eventos sociais principais emitem notificacoes por rota/dominio, respeitando bloqueio social, preferencias e auto-notificacao. A UI fica como aba `Notificacoes` dentro de `Social`, enquanto alertas operacionais continuam nas telas de frota, impressora, agente e administracao.
Alternativas consideradas: reutilizar alertas operacionais existentes; enviar apenas email; criar notificacoes no frontend; misturar notificacoes na topbar global.
Consequencias: o produto preserva a separacao entre operacao tecnica e vida social do conteudo. A primeira versao entrega digest como agrupamento in-app pendente, sem agendamento externo ou envio por email.
Impacto em testes: `backend/tests/test_social_catalog.py` cobre preferencias, follows, bloqueio, emissao por comentarios/relacoes e leitura; build frontend valida a central social.
Impacto em rollback: medio; remover rotas/UI desativa emissao nova, mas notificacoes/follows ja persistidos podem permanecer como legado sem afetar operacao.
Como reverter: reverter `backend/app/social_notifications.py`, `backend/app/routes/social_notifications.py`, integracoes em `backend/app/routes/social_catalog.py`, `backend/sql/058_social_notifications.sql`, aba de notificacoes em `SocialScreen.tsx` e documentacao relacionada.
Referencias: `backend/app/social_notifications.py`, `backend/app/routes/social_notifications.py`, `backend/sql/058_social_notifications.sql`, `frontend/src/screens/SocialScreen.tsx`, `TELAS.md`, `RUNBOOK.md`.

### DEC-20260616-13 - Moderacao social usa fila auditavel e remocao logica

Status: aceita
Data: 2026-06-16
Contexto: conteudo social, arquivos 3D, tags e catalogo precisam de denuncia, revisao e bloqueio rapido sem apagar historico, sem misturar curadoria publica com tela Social e sem criar operacao irreversivel em SQLite/cloud.
Decisao: criar o dominio `social_moderation`, com SQL proprio em `057_social_moderation.sql`, tabelas de denuncias e acoes, rota autenticada para denuncia publica e rotas administrativas para fila/acao. Acoes de ocultar, remover, bloquear, restaurar, descartar e revisar registram motivo, estado anterior, estado novo e auditoria via `catalog_audit_events`. Conteudo moderado muda estado logico em tabelas existentes; exclusao fisica fica fora do fluxo. A UI administrativa fica na tela `Catalogo`, separada da tela `Social`.
Alternativas consideradas: apagar linhas denunciadas; criar moderacao dentro da tela Social; reutilizar apenas `catalog_audit_events` sem fila dedicada; criar tabela de auditoria nova para cada entidade.
Consequencias: moderacao fica reversivel, rastreavel e compativel com rollback por acao restauradora. A fila dedicada facilita triagem e preserva privacidade do usuario comum. Retencao de denuncias e acoes deve seguir politica operacional de auditoria social antes de qualquer limpeza.
Impacto em testes: `backend/tests/test_social_catalog.py` cobre denuncia, permissao administrativa, acao, auditoria, restauracao e curadoria de tag; build frontend valida o painel administrativo.
Impacto em rollback: medio; reverter o dominio remove a fila nova, mas estados logicos aplicados em conteudo permanecem e devem ser restaurados por acao administrativa ou SQL supervisionado antes de desativar o fluxo.
Como reverter: reverter `backend/app/social_moderation.py`, `backend/app/routes/social_moderation.py`, inclusao no `main.py`, `backend/sql/057_social_moderation.sql`, painel de moderacao no Catalogo e documentacao relacionada.
Referencias: `backend/app/social_moderation.py`, `backend/app/routes/social_moderation.py`, `backend/sql/057_social_moderation.sql`, `frontend/src/screens/CatalogAdminScreen.tsx`, `TELAS.md`, `RUNBOOK.md`.

### DEC-20260616-12 - Ranking social usa sinais publicos e explicaveis

Status: aceita
Data: 2026-06-16
Contexto: a descoberta social precisa priorizar conteúdo técnico útil sem usar dados privados, sem depender de algoritmo opaco e sem premiar auto-voto.
Decisao: criar o domínio `social_ranking`, com SQL próprio em `055_social_ranking_reputation.sql` e estado de materialização em `056_social_materialization_state.sql`. O score é determinístico e deriva sinais públicos: downloads, favoritos de outros usuários, soluções marcadas e reações úteis. Auto-voto é ignorado no score; sinais negativos de denúncia/moderação ficam modelados como `report` para reduzir exposição quando o domínio de moderação registrar eventos. A reputação técnica é snapshot derivado desses sinais e a UI mostra motivos curtos por recomendação. Índice social e sinais usam assinatura persistida da fonte para evitar rebuild síncrono em toda consulta pública.
Alternativas consideradas: usar somente ordenação recente; usar ranking por dados privados de impressão; bloquear favoritos próprios no produto; criar serviço externo de recomendação.
Consequencias: recomendações são auditáveis, reversíveis e coerentes com SQLite/cloud atual. O score inicial ainda é simples e deve evoluir quando existirem sinais reais de impressão e moderação completa.
Impacto em testes: `backend/tests/test_social_catalog.py` cobre score, explicação, reputação e ignorar auto-voto.
Impacto em rollback: médio; há novos scripts SQLite `055_social_ranking_reputation.sql` e `056_social_materialization_state.sql`.
Como reverter: remover rotas/UI de recomendações/reputação e restaurar backup SQLite anterior aos scripts `055_social_ranking_reputation.sql` e `056_social_materialization_state.sql` se as tabelas não puderem permanecer como legado.
Referencias: `backend/sql/055_social_ranking_reputation.sql`, `backend/sql/056_social_materialization_state.sql`, `backend/app/social_ranking.py`, `backend/app/routes/social_ranking.py`, `frontend/src/screens/SocialScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-11 - Busca social usa indice publico derivado

Status: aceita
Data: 2026-06-16
Contexto: a descoberta social precisa pesquisar comunidades, discussões, arquivos, configurações técnicas, perfis de material e catálogo sem vazar conteúdo privado nem transformar a UI em regra de negócio.
Decisao: criar o domínio `search_discovery`, com SQL próprio em `054_social_search_discovery.sql`, índice derivado reconstruído pela API de busca e tags normalizadas em tabelas dedicadas. A rota `/api/social/search` retorna somente conteúdo público ou comunitário elegível, com facetas e filtros técnicos; `/api/social/tags` expõe tags públicas e a curadoria administrativa usa `catalog_audit_events` existente. A UI fica como aba `Descoberta` da tela Social, consumindo contrato público sem acesso direto a persistência.
Alternativas consideradas: buscar diretamente em cada tabela no frontend; criar engine externa de busca; indexar conteúdo privado e filtrar depois.
Consequencias: a entrega fica simples para SQLite/cloud atual, com rollback claro e privacidade aplicada antes da resposta. O índice pode evoluir para atualização incremental real quando volume exigir.
Impacto em testes: `backend/tests/test_social_catalog.py` cobre privacidade, filtros técnicos e tags; build frontend valida a aba de descoberta.
Impacto em rollback: médio; há novo script SQLite `054_social_search_discovery.sql`.
Como reverter: remover rotas/UI de busca social e restaurar backup SQLite anterior ao script `054_social_search_discovery.sql` se as tabelas não puderem permanecer como legado.
Referencias: `backend/sql/054_social_search_discovery.sql`, `backend/app/search_discovery.py`, `backend/app/routes/search_discovery.py`, `frontend/src/screens/SocialScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-10 - Perfis de material e fatiamento são compartilháveis, não executáveis

Status: aceita
Data: 2026-06-16
Contexto: o PKG-63 precisa permitir compartilhamento de material e fatiamento por impressora, nozzle, material e objetivo antes de qualquer integração com engine de slicer.
Decisao: criar o domínio `print_profiles`, com SQL próprio em `053_social_material_slicing_profiles.sql`, rotas dedicadas, CRUD no detalhe da impressora e leitura pública na aba `Perfis` da comunidade. O perfil material contém marca, tipo, temperatura, cama, fluxo, compatibilidade e versão; o perfil de fatiamento ligado contém layer height, velocidade, suporte, infill, objetivo e configurações livres. Export/import usa JSON neutro e importação entra privada.
Alternativas consideradas: colocar campos de material dentro da configuração técnica do PKG-62; acoplar perfil diretamente a arquivo de slicer; executar/aplicar perfil automaticamente.
Consequencias: o produto ganha comparação e compartilhamento técnico sem risco operacional. Aplicação automática, engine de fatiamento e formatos específicos ficam para pacotes posteriores.
Impacto em testes: testes focados cobrem criação, compatibilidade, export/import, sanitização e visibilidade comunitária.
Impacto em rollback: médio; há novo script SQLite `053_social_material_slicing_profiles.sql`.
Como reverter: remover rotas/UI de perfis de material e restaurar backup SQLite anterior ao script `053_social_material_slicing_profiles.sql` se a tabela não puder permanecer.
Referencias: `backend/sql/053_social_material_slicing_profiles.sql`, `backend/app/print_profiles.py`, `backend/app/routes/print_profiles.py`, `frontend/src/screens/PrinterDetailScreen.tsx`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-09 - Configuração técnica pública é perfil social separado da operação

Status: aceita
Data: 2026-06-16
Contexto: o PKG-62 precisa permitir que makers compartilhem configurações de impressora, mods, componentes e calibrações sem transformar comunidade em permissão operacional nem expor dados sensíveis da frota.
Decisao: criar o domínio `technical_profiles`, com SQL próprio em `052_social_technical_printer_configs.sql`, rotas dedicadas e leitura na aba `Perfis` da comunidade. O registro referencia usuário, impressora, variante do catálogo, comunidade e item de biblioteca quando existir, mas o payload público contém somente dados técnicos sanitizados. Arquivamento é lógico.
Alternativas consideradas: adicionar tudo em `social_catalog.py`; guardar configurações em JSON dentro de impressoras públicas; expor campos operacionais sanitizados no frontend.
Consequencias: o domínio social ganha comparação técnica por comunidade sem aumentar o módulo social principal e sem risco de virar acesso operacional. A leitura/comparação fica na comunidade; cadastro, edição e arquivamento ficam no detalhe da impressora.
Impacto em testes: testes focados cobrem criação, edição, arquivamento lógico, sanitização de dados sensíveis, visibilidade comunitária e comparação normalizada.
Impacto em rollback: médio; há novo script SQLite `052_social_technical_printer_configs.sql`.
Como reverter: remover rotas/UI de perfis técnicos e restaurar backup SQLite anterior ao script `052_social_technical_printer_configs.sql` se a tabela não puder permanecer.
Referencias: `backend/sql/052_social_technical_printer_configs.sql`, `backend/app/technical_profiles.py`, `backend/app/routes/technical_profiles.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-08 - Organizador da biblioteca separa favoritos, coleções e listas de impressão

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: dados e endpoints existentes podem ser reaproveitados/migrados, mas projetos de impressão são a raiz final.
Contexto: o PKG-61 precisa organizar modelos sem executar fatiamento e sem vazar coleções privadas ou histórico pessoal.
Decisao: criar um organizador social com favoritos por usuário, coleções com visibilidade `private`, `community` ou `public`, listas de impressão por usuário/impressora e itens de lista sempre ligados a uma versão específica de modelo. O histórico de download autenticado entra apenas no resumo do usuário.
Alternativas consideradas: guardar favoritos em JSON no usuário; transformar coleção em feed; permitir lista de impressão sem versão.
Consequencias: a UI consegue organizar modelos sem misturar CRUD de modelo com organização pessoal, e listas permanecem reprodutíveis porque apontam para uma versão imutável.
Impacto em testes: testes cobrem isolamento de coleção privada, bloqueio de impressora de outro usuário, favorito, download histórico e lista por versão.
Impacto em rollback: médio; há novo script SQLite `051_social_library_organizer.sql`.
Como reverter: remover endpoints/UI do organizador e restaurar backup SQLite anterior ao script `051_social_library_organizer.sql` se necessário.
Referencias: `backend/sql/051_social_library_organizer.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-07 - Versionamento de biblioteca por snapshot imutável

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: snapshots de biblioteca viram base legada para snapshots imutáveis de projeto.
Contexto: o PKG-60 precisa permitir evolução de modelos sem sobrescrever artefatos já baixados, citados ou usados como origem de remix.
Decisao: persistir versões em `social_library_versions` com snapshot JSON dos arquivos, metadados do item, changelog, autor da versão e marcador `is_current`. O item mantém os arquivos correntes para listagem simples, mas cada versão preserva seu snapshot; downloads podem apontar para versão específica.
Alternativas consideradas: duplicar item por versão; criar tabela normalizada para cada arquivo de versão; manter apenas `version_label` no item.
Consequencias: rollback lógico fica barato e auditável, downloads por versão ficam mensuráveis e a UI pode mostrar histórico sem misturar rascunho, arquivo corrente e snapshot histórico.
Impacto em testes: testes cobrem imutabilidade do snapshot, download de versão, permissão de criação e promoção de versão anterior.
Impacto em rollback: médio; há novo script SQLite `050_social_library_versions.sql`.
Como reverter: remover endpoints/UI de versão, voltar downloads ao item corrente e restaurar backup SQLite anterior ao script `050_social_library_versions.sql` se necessário.
Referencias: `backend/sql/050_social_library_versions.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-06 - Publicação pública exige autoria, licença e termos

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: regras de autoria/licença continuam válidas, mas aplicadas ao projeto central.
Contexto: o PKG-59 precisa reduzir risco legal da biblioteca e deixar direitos de uso claros antes de downloads e remixes.
Decisao: itens `public` e `community` exigem `original_author_name`, `license` e aceite de termos antes da publicação. Fonte pública, atribuição e origem de remix ficam no item; itens privados podem existir como rascunho sem exposição pública. Remix referencia item ativo e não pode apontar para si mesmo.
Alternativas consideradas: permitir publicação pública com licença padrão implícita; deixar autoria apenas como dono do perfil; postergar remix para versionamento.
Consequencias: downloads e listagens passam a exibir crédito/licença claramente, e pacotes posteriores podem versionar/remixar sem perder cadeia de atribuição.
Impacto em testes: testes cobrem bloqueio sem autoria/termos, persistência de créditos e referência de remix.
Impacto em rollback: médio; há novo script SQLite `049_social_library_license_attribution.sql`.
Como reverter: remover validação de publicação, campos de UI/contrato de autoria/licença avançada e restaurar backup SQLite anterior ao script `049_social_library_license_attribution.sql` se necessário.
Referencias: `backend/sql/049_social_library_license_attribution.sql`, `backend/app/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `frontend/src/screens/PublicProfileScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-05 - Análise 3D usa parser controlado e preview derivado

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: análise por arquivo continua válida, mas arquivo passa a pertencer ao projeto.
Contexto: o PKG-58 precisa entregar dimensões, alertas e preview de modelos sem executar código nem depender de ferramenta externa pesada.
Decisao: analisar STL/3MF/ZIP com parsers controlados em Python/stdlib, lendo vértices e triângulos para derivar bounding box, dimensões, volume aproximado, contagens e alertas. O preview é SVG gerado a partir do bounding box, salvo em `thumbnail_svg`; falha fica restrita ao arquivo como `analysis_failed`.
Alternativas consideradas: usar biblioteca nativa de malha; renderizar WebGL real no servidor; bloquear item inteiro em falha de análise.
Consequencias: análise fica determinística, auditável e segura para arquivos pequenos/médios, com preview útil sem custo de renderização 3D pesada.
Impacto em testes: testes cobrem STL binário determinístico, dimensões, thumbnail, suporte provável e falha isolada por arquivo.
Impacto em rollback: médio; há novo script SQLite `048_social_library_analysis.sql`.
Como reverter: remover endpoint `/api/social/library/files/{file_id}/analysis`, métodos de análise, UI de preview/análise e restaurar backup SQLite anterior ao script `048_social_library_analysis.sql` se necessário.
Referencias: `backend/sql/048_social_library_analysis.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-04 - Upload 3D usa corpo bruto e quarentena local controlada

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: upload bruto/quarentena continua válido, mas entrada principal passa a ser arquivo de projeto, não item de comunidade.
Contexto: o PKG-57 precisa aceitar arquivo 3D real com segurança, mas o ambiente não possui `python-multipart` e o upload deve ficar separado da validação técnica profunda do pacote seguinte.
Decisao: expor upload por corpo `application/octet-stream` em item existente da biblioteca, usando `file_name` na query apenas como metadado validado. O arquivo é salvo em `<data_dir>/library_uploads/quarantine` com nome derivado de SHA-256, nunca por path do usuário. O backend valida extensão, tamanho, assinatura básica, ZIP seguro, checksum e deduplicação; resultado fica como `quarantined` ou `rejected`.
Alternativas consideradas: adicionar dependência multipart; aceitar upload direto para storage público; validar e liberar download imediatamente.
Consequencias: reduz dependência nova, evita path traversal no destino e garante que arquivo real não saia da quarentena antes da análise técnica posterior.
Impacto em testes: testes cobrem upload bruto, limite, ZIP inseguro, rejeição, quarentena, checksum e deduplicação.
Impacto em rollback: médio; há novo script SQLite `047_social_library_uploads.sql` e diretório local de quarentena.
Como reverter: remover endpoint `/api/social/library/{item_id}/files/upload`, método de upload, UI de seleção de arquivo e restaurar backup SQLite anterior ao script `047_social_library_uploads.sql`; limpar diretório de quarentena somente após confirmação explícita.
Referencias: `backend/sql/047_social_library_uploads.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-03 - Biblioteca base separa metadados de upload e quarentena

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: tabelas `social_library_*` permanecem como legado/base de migração.
Contexto: o PKG-56 precisa criar a biblioteca de modelos 3D por comunidade/perfil antes do pacote de upload seguro, validação pesada e quarentena.
Decisao: persistir itens em `social_library_items`, arquivos declarados em `social_library_files` e downloads em `social_library_downloads`. O pacote aceita STL, 3MF e ZIP apenas como metadados `metadata_only`, com dono obrigatório, licença, visibilidade explícita, vínculo opcional com comunidade/variante de catálogo e arquivamento lógico. Upload binário, armazenamento, quarentena, extração técnica e antivírus ficam no pacote dedicado seguinte.
Alternativas consideradas: aceitar upload binário já no cadastro; guardar arquivos em JSON dentro do item; não registrar downloads até haver arquivo real.
Consequencias: a UI já entrega biblioteca navegável sem assumir segurança de arquivo ainda inexistente. A separação reduz risco de aceitar binário sem validação e mantém rollback simples via script SQL.
Impacto em testes: testes cobrem visibilidade, vínculo com catálogo, criação, edição, arquivamento, histórico de download, contrato HTTP e rejeição de nomes de arquivo inseguros.
Impacto em rollback: médio; há novo script SQLite `046_social_library_items.sql`. Rollback funcional remove endpoints/UI de biblioteca e mantém dados como legado; rollback estrutural exige backup SQLite anterior ao script.
Como reverter: remover endpoints `/api/social/library*`, métodos de biblioteca em `social_catalog`, UI de `Arquivos`/perfil, tipos/serviços frontend e restaurar backup SQLite anterior ao script `046_social_library_items.sql` se as tabelas não puderem permanecer.
Referencias: `backend/sql/046_social_library_items.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `frontend/src/screens/PublicProfileScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-02 - Discussões técnicas evoluem o feed sem virar permissão operacional

Status: aceita
Data: 2026-06-16
Contexto: o PKG-55 precisa permitir posts, comentários, reações e soluções técnicas em comunidades públicas, sem transformar comunidade em organização operacional nem apagar histórico quando houver moderação.
Decisao: usar `social_feed_items` como post raiz e adicionar `social_discussion_comments`, `social_discussion_reactions` e `social_discussion_edit_history`. Posts e comentários usam remoção lógica por `deleted_at`; comentários aceitam árvore curta de um nível; solução é marcada no post de tipo dúvida por `solution_comment_id`; permissões distinguem autor, moderador de comunidade e administrador. HTML/script é rejeitado e anexos leves aceitam somente URL HTTPS pública.
Alternativas consideradas: criar um domínio paralelo de fórum; permitir árvore ilimitada; apagar linhas removidas; aceitar HTML sanitizado; usar organização como permissão de moderação.
Consequencias: discussão pública fica auditável, reversível e independente de acesso operacional. Pacotes futuros podem adicionar antiabuso completo, biblioteca e moderação avançada sem quebrar o contrato atual.
Impacto em testes: testes cobrem criação/edição/remoção lógica, comentários/respostas, reação, solução, permissões, sanitização e payload sem dados operacionais.
Impacto em rollback: médio; há novo script SQLite `045_social_discussions.sql`. Rollback funcional remove endpoints/UI de discussão e mantém dados como legado; rollback estrutural exige backup SQLite anterior ao script.
Como reverter: remover endpoints `/api/social/posts/*` e `/api/social/comments/*`, métodos de discussão em `social_catalog`, UI de discussão em `PublicCommunityScreen`, tipos/serviço frontend e restaurar backup SQLite anterior ao script `045_social_discussions.sql` se as tabelas não puderem permanecer.
Referencias: `backend/sql/045_social_discussions.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-01 - Feed técnico é público por comunidade e separado das discussões

Status: aceita
Data: 2026-06-16
Contexto: o PKG-54 precisa transformar a aba `Feed` das comunidades em conteúdo real sem antecipar toda a escrita social do PKG-55 e sem misturar organizações operacionais com comunidades públicas.
Decisao: persistir itens de feed em `social_feed_items`, sempre vinculados a `social_communities`, com tipos técnicos, visibilidade explícita, filtros por componente/material/firmware/problema e ordenações `recent`, `recommended` e `pinned`. O PKG-54 expõe leitura pública paginada e avisos de curadoria derivados do catálogo; criação/edição interativa de posts, comentários e reações fica para o PKG-55.
Alternativas consideradas: manter placeholder até posts completos; criar timeline global; usar organizações como comunidade; guardar feed apenas no frontend.
Consequencias: comunidades ganham leitura útil e segura agora, sem conceder permissão operacional e sem expor conteúdo privado. A tabela permite evoluir para posts/discussões sem quebrar o contrato público.
Impacto em testes: testes cobrem paginação, filtros, ordenação, exclusão de item privado, payload sanitizado e contrato HTTP do feed.
Impacto em rollback: médio; há novo script SQLite idempotente `044_social_community_feed.sql`. Rollback funcional remove endpoint/UI e mantém dados como legado; rollback estrutural restaura backup SQLite anterior ao script.
Como reverter: remover `/api/social/communities/{slug}/feed`, métodos de feed em `social_catalog`, integração da aba `Feed`, tipos/serviço frontend e restaurar backup SQLite anterior ao script `044_social_community_feed.sql` se a tabela não puder permanecer.
Referencias: `backend/sql/044_social_community_feed.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260615-05 - Social e descoberta publica, nao gestao proprietaria

Status: aceita
Data: 2026-06-15
Contexto: os pacotes PKG-49 a PKG-53 foram implementados com contratos separados, mas a tela Social acumulava edição de perfil, publicação de impressora, catálogo, comunidades e relações, criando uma experiência confusa e com risco de misturar descoberta pública com gestão operacional.
Decisao: a seção `Social` passa a ser somente descoberta pública e comunidade. Ela possui abas para `Comunidades`, `Impressoras`, `Makers` e `Relações`, consumindo catálogo canônico, perfis públicos, impressoras publicadas e resumo relacional. Gestão de perfil fica em `Conta > Perfil > Público`; publicar/despublicar impressora fica no detalhe da impressora; curadoria do catálogo fica na seção `Catálogo`/admin; ações sociais completas ficam em `/u/{slug}` ou `Conta > Perfil`.
Alternativas consideradas: manter formulários de gestão dentro de Social; criar uma tela social fake para recursos futuros; transformar Social em administração de catálogo; deixar publicação de impressora fora do inventário real.
Consequencias: a primeira tela Social fica navegável, sem formulário bruto, e reforça que relações sociais não concedem acesso operacional. Recursos futuros devem entrar como conteúdo real ou permanecer ocultos até terem entrega útil.
Impacto em testes: validação cobre ausência de formulário principal de perfil e de ação principal de publicar impressora em Social, filtros canônicos, comunidades reais, impressoras públicas, makers públicos, resumo de relações e ausência de dados sensíveis.
Impacto em rollback: baixo; rollback funcional reverte `frontend/src/screens/SocialScreen.tsx`, estilos sociais e a listagem sem termo de `/api/social/profiles`. Nenhum schema novo foi criado.
Como reverter: restaurar a tela Social anterior e voltar `GET /api/social/profiles` a exigir `q`, mantendo perfil, publicação, catálogo e comunidades nos contextos proprietários já existentes.
Referencias: `frontend/src/screens/SocialScreen.tsx`, `frontend/src/styles/social.css`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `backend/tests/test_social_catalog.py`.

### DEC-20260614-01 - Social usa catálogo canônico e não permissões operacionais

Status: aceita
Data: 2026-06-14
Contexto: os pacotes PKG-49 a PKG-53 introduzem perfil público, impressoras públicas, comunidades automáticas e grafo social. Esses recursos precisam usar inventário real e modelo canônico sem vazar endpoints, agentes, credenciais ou permissões de operação.
Decisao: criar o domínio `social_catalog` com SQL idempotente próprio. O catálogo mestre versiona fabricante, modelo, variante e componentes. Impressoras públicas exigem `catalog_variant_id`; comunidades são derivadas automaticamente do catálogo e da publicação consentida da impressora; relações sociais ficam isoladas em `social_relationships` e não alteram organizações, ownership ou acesso operacional.
Alternativas consideradas: usar texto livre `cloud_model`; transformar comunidade em organização operacional; misturar perfil público nos campos de conta; criar comunidades manuais antes do catálogo.
Consequencias: recursos sociais ficam consistentes e auditáveis, com menor risco de vazamento operacional. A primeira UI é enxuta e pode evoluir para curadoria avançada sem mudar o contrato base.
Impacto em testes: testes focados cobrem seed do catálogo, privacidade do perfil, vínculo obrigatório de impressora pública, sincronização de comunidade e bloqueio social.
Impacto em rollback: médio; o schema adiciona tabelas sociais e colunas públicas em `printers`. O inicializador cria backup do SQLite antes de aplicar script pendente.
Como reverter: restaurar backup do SQLite anterior ao `035_social_catalog.sql`, remover `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, tela `Social`, serviço `socialApi` e a inclusão da rota no `main.py`.
Referencias: `backend/sql/035_social_catalog.sql`, `backend/app/social_catalog.py`, `frontend/src/screens/SocialScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260615-03 - Publicação de impressora pertence ao detalhe do inventário

Status: aceita
Data: 2026-06-15
Contexto: o PKG-51 precisava deixar de tratar publicação de impressora como ação escondida na tela Social. A decisão de expor uma impressora pública deve acontecer onde o usuário reconhece o inventário operacional real, sem vazar campos de operação.
Decisao: manter a API de escrita em `/api/printers/{printer_id}/public-profile`, criar a página pública `/p/{printer_id}` via `GET /api/public/printers/{printer_id}` e concentrar a UI de publicar/despublicar no detalhe da impressora. Busca pública usa `/api/social/printers` e comunidades usam somente impressoras públicas de perfis públicos.
Alternativas consideradas: continuar publicando pela tela Social; criar slug público editável por impressora; expor a página pública apenas dentro de `/u/{slug}`.
Consequencias: a ação fica ligada ao inventário real, a URL pública fica simples e reversível por ID interno não sensível, e a tela Social permanece focada em descoberta/perfis/comunidades.
Impacto em testes: testes cobrem ownership, variante obrigatória/bloqueada, imagem inválida, busca pública, página direta, perfil privado, despublicação e sanitização de payload.
Como reverter: remover a rota pública `/p/{printer_id}`, ocultar a seção de publicação no detalhe da impressora e despublicar registros via endpoint antes de restaurar backup de banco quando necessário.

### DEC-20260615-04 - Comunidades são catálogo público, não organização operacional

Status: aceita
Data: 2026-06-15
Contexto: o PKG-52 precisa transformar comunidades automáticas em produto navegável sem misturar descoberta social com autorização operacional, e sem prometer feed/arquivos/mods completos antes dos pacotes dedicados.
Decisao: comunidades são derivadas de fabricante, modelo e variante do catálogo canônico. Vínculos são criados somente por impressoras públicas de perfis públicos. `active` e `uncurated` aceitam associação automática; `obsolete` fica como histórico sem membros/impressoras ativas; `merged` preserva a origem e aponta `merged_into_id` quando houver destino. A página `/c/{slug}` expõe contexto técnico, contagens e abas esperadas. Feed e arquivos começam como placeholders operacionais seguros; mods usam os mods públicos declarados na publicação da impressora até existir biblioteca dedicada.
Alternativas consideradas: criar grupos manuais genéricos; transformar comunidade em organização/permissão; esconder estados iniciais; apagar comunidades obsoletas; implementar feed/arquivos completos dentro do pacote de comunidade.
Consequencias: a navegação social fica útil e reversível, contagens não incluem impressoras privadas, merge/obsolescência não geram acesso novo e pacotes futuros podem ligar feed/arquivos sem alterar o contrato base.
Impacto em testes: testes cobrem associação por fabricante/modelo/variante, troca de variante, despublicação, filtros canônicos, contagens sem privados, estados `obsolete`/`merged`, contrato por slug e ausência de dados operacionais no payload.
Impacto em rollback: baixo a médio; rollback funcional usa despublicação, estado `obsolete`/`blocked` ou ajuste controlado de `merged_into_id`. Rollback estrutural exige backup SQLite anterior ao `035_social_catalog.sql`.
Como reverter: remover `/c/{slug}` e filtros da tela Social, manter as tabelas como legado, despublicar impressoras afetadas e restaurar backup SQLite apenas se for necessário desfazer o domínio social inteiro.
Referencias: `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/SocialScreen.tsx`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260615-01 - Curadoria do catálogo mestre fica em superfície administrativa própria

Status: aceita
Data: 2026-06-15
Contexto: o catálogo mestre precisa sustentar comunidades, publicação de impressoras, biblioteca de modelos e fatiamento seguro. Misturar curadoria canônica na tela Social deixaria regras administrativas pouco auditáveis e permitiria confundir identidade pública com administração de dados técnicos.
Decisao: manter o domínio `social_catalog`, mas separar a superfície de curadoria na seção `Catálogo`. Usuário autenticado comum pode navegar no catálogo detalhado em modo leitura; criação, edição e promoção de curadoria ficam restritas ao administrador. A API de leitura detalhada expõe busca filtrável agrupada por fabricante/modelo, com variações técnicas dentro do detalhe do modelo, e as rotas mutáveis continuam protegidas por administrador. O contrato inclui metadados enriquecidos de fabricante/modelo: logo, resumo, site, repositório, documentação, BOM, Discord, Reddit, imagem e notas de curadoria quando confirmados. A UI não exibe campo de origem técnica nem identificador interno de pacote. Os estados válidos são `official`, `community`, `draft`, `obsolete` e `blocked`; `community` exige revisão de fonte antes de virar `official`; `draft` é usado quando volume/componentes ainda têm incerteza; `obsolete` preserva vínculos existentes e bloqueia nova publicação; `blocked` remove o item da consulta pública e fica oculto da curadoria padrão, mas continua acessível por filtro para auditoria/rollback. Merge/rename deve criar nova entrada ou atualizar metadados sem apagar a variante antiga enquanto houver impressora vinculada.
Alternativas consideradas: manter tudo na tela Social; aceitar edição por usuários comuns; apagar variantes bloqueadas; alterar `035_social_catalog.sql` já versionado.
Consequencias: a curadoria fica auditável e reversível, usuário comum não edita catálogo canônico e dados incertos entram como `community`/`draft` sem promessa técnica falsa. O detalhe administrativo expõe `detail_json` e `source_links_json` por modelo para registrar ficha técnica e fontes usadas sem misturar isso com campos internos. Logos só são exibidos quando vierem de fonte oficial, GitHub org/usuário confiável ou imagem confirmada; caso contrário a UI usa monograma.
Impacto em testes: testes cobrem seed amplo DIY, metadados enriquecidos, ficha/fonte de curadoria, política de logo confiável, contrato agrupado por modelo, filtros administrativos, ausência de identificador interno de pacote nas fontes, leitura detalhada para usuário comum, permissão 403 para mutação por usuário comum, duplicidade, obsolescência/bloqueio e vínculo de impressora com variante canônica.
Impacto em rollback: médio; seeds `036_expand_printer_catalog_seed.sql`/`037_expand_diy_catalog_breadth.sql`, metadados `038_catalog_manufacturer_model_metadata.sql`, bloqueio `039_catalog_block_toolchanger_entries.sql`, complemento `040_catalog_add_voron_phoenix_draft.sql`, sanitização `041_catalog_sanitize_internal_sources.sql`, enriquecimentos `042_catalog_enriched_metadata.sql`/`043_catalog_deeper_model_detail.sql` e tela `CatalogAdminScreen` podem ser revertidos sem apagar dados de impressoras existentes.
Como reverter: reverter scripts SQL 036 a 043, endpoints administrativos novos, `frontend/src/screens/CatalogAdminScreen.tsx`, estilos/rota `catalog` e restaurar docs; em banco já aplicado, manter linhas como legado auditável ou restaurar backup SQLite anterior ao script 036.
Referencias: `backend/sql/036_expand_printer_catalog_seed.sql`, `backend/sql/037_expand_diy_catalog_breadth.sql`, `backend/sql/038_catalog_manufacturer_model_metadata.sql`, `backend/sql/039_catalog_block_toolchanger_entries.sql`, `backend/sql/040_catalog_add_voron_phoenix_draft.sql`, `backend/sql/041_catalog_sanitize_internal_sources.sql`, `backend/sql/042_catalog_enriched_metadata.sql`, `backend/sql/043_catalog_deeper_model_detail.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/CatalogAdminScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260615-02 - Perfil social e gerido na Conta, com pagina publica sanitizada

Status: aceita
Data: 2026-06-15
Contexto: a primeira UI do PKG-50 colocou a edição do perfil social dentro da tela `Social`, mas o fluxo correto do produto é o usuário abrir o menu do topo e gerenciar dados pessoais em `Conta > Perfil`. A página pública por slug também precisa existir como superfície separada e não pode vazar dados operacionais.
Decisao: mover a edição principal do perfil social para `Conta > Perfil > Público`, mantendo a tela `Social` como referência para comunidades e publicação social. A rota pública frontend passa a ser `/u/{slug}` e consome somente os endpoints públicos `/api/social/profiles/{slug}` e `/api/social/profiles/{slug}/printers`. A API valida avatar e links por HTTPS público, bloqueia hosts locais/privados, restringe hosts de redes sociais conhecidas, reserva slugs antigos e trata `private`, `unlisted` e bloqueio social no acesso público.
Alternativas consideradas: manter edição na tela `Social`; expor perfil público só via JSON; aceitar links livres com sanitização posterior.
Consequencias: a gestão de identidade fica no lugar esperado da conta, o contrato público permanece pequeno e auditável, e a página pública não precisa conhecer conta operacional, organizações, permissões, agente, Moonraker, SSH ou tokens.
Impacto em testes: testes focados cobrem slug duplicado, slug histórico reservado, privacidade, unlisted, bloqueio social, sanitização de avatar/link e ausência de dados sensíveis no contrato público.
Impacto em rollback: baixo a médio; rollback remove a aba `Público` da Conta, a tela `/u/{slug}` e os validadores novos, mantendo a tabela `social_profiles` existente.
Como reverter: restaurar os arquivos `frontend/src/screens/AuthScreen.tsx`, `frontend/src/screens/PublicProfileScreen.tsx`, `frontend/src/screens/SocialScreen.tsx`, `frontend/src/services/socialApi.ts`, `frontend/src/types/social.ts`, `backend/app/social_catalog.py` e `backend/app/routes/social_catalog.py` ao estado anterior e manter os dados de perfil como legado.
Referencias: `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/AuthScreen.tsx`, `frontend/src/screens/PublicProfileScreen.tsx`, `frontend/src/screens/SocialScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260615-03 - Relações sociais não concedem acesso operacional

Status: aceita
Data: 2026-06-15
Contexto: o PKG-53 completa follow, amizade e bloqueio. Essas relações precisam melhorar descoberta social e moderação sem alterar organizações, ownership, permissões de impressora, Moonraker, agente, SSH ou tokens.
Decisao: manter `social_relationships` como grafo social isolado. A API aceita follow/unfollow, solicitação/aceite/recusa/cancelamento de amizade, unfriend e block/unblock; bloqueio encerra follows/amizades existentes e impede novas interações sociais, mas desbloqueio não recria vínculos. Busca de perfis lista `public`, permite `unlisted` por slug direto, nunca lista `private` e filtra bloqueados para viewer autenticado. O histórico mínimo de abuso usa `catalog_audit_events` com `entity_type='social_relationship'`, ação, IDs e `retention_days=180`, sem email, telefone, token, credencial ou payload operacional.
Alternativas consideradas: criar tabela dedicada de moderação; esconder relações na tela Social; fazer amizade conceder acesso a impressoras públicas restritas.
Consequencias: relações ficam auditáveis e reversíveis sem misturar o domínio social com controle operacional. Conteúdo público/restrito respeita privacidade e bloqueio, mas acesso a impressora continua governado por owner/organização/permissões existentes.
Impacto em testes: `backend/tests/test_social_catalog.py` cobre ciclo completo de follow/friend/block, idempotência, payload sanitizado, busca/visibilidade, bloqueio e isolamento operacional.
Impacto em rollback: baixo a médio; relações podem ser encerradas por API sem apagar histórico. Se necessário, restaurar backup SQLite anterior ao script social, sem executar `DELETE` manual sem confirmação explícita.
Como reverter: reverter endpoints e UI de relacionamento em `backend/app/routes/social_catalog.py`, regras em `backend/app/social_catalog.py`, contratos de `frontend/src/services/socialApi.ts`, `frontend/src/types/social.ts`, `frontend/src/screens/PublicProfileScreen.tsx` e `frontend/src/screens/SocialScreen.tsx`.
Referencias: `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicProfileScreen.tsx`, `frontend/src/screens/SocialScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-15 - Segurança social fica em camada dedicada

Status: aceita
Data: 2026-06-16
Contexto: a camada social já possui perfil público, relações, biblioteca, moderação e notificações. O endurecimento contra spam, scraping, assédio, enumeração e vazamento não deve ser espalhado na UI nem misturado com permissões operacionais de impressora.
Decisao: criar `social_safety` como camada dedicada com preferências de privacidade social, eventos de rate limit e sinais de abuso. A busca de perfis respeita `profile_discoverable` sem quebrar URL direta autorizada. Endpoints públicos sensíveis aplicam rate limit por ação e registram somente hashes/metadados seguros. Sinais de abuso ficam em endpoint administrativo separado de moderação, enquanto controles do usuário ficam em `Conta > Perfil > Público`.
Alternativas consideradas: aplicar limites apenas em memória; reutilizar denúncias como rate limit; colocar controles na tela `Social`.
Consequencias: regras antiabuso ficam auditáveis, testáveis e sem dependência de UI. Relações sociais continuam isoladas de organizações, agentes, Moonraker, SSH, tokens e permissões operacionais. Eventos persistidos exigem retenção/limpeza operacional.
Impacto em testes: testes focados cobrem preferências, descoberta, rate limit, sinais de abuso, endpoint administrativo e payload sanitizado.
Impacto em rollback: baixo a médio; rollback remove rotas e integração de rate limit, preservando tabelas como histórico inerte até limpeza supervisionada.
Como reverter: reverter `backend/app/social_safety.py`, `backend/app/routes/social_safety.py`, integrações em rotas sociais, SQL `059_social_safety_antiabuse.sql`, UI de segurança social em `AuthScreen.tsx` e contratos em `socialApi.ts`/`types/social.ts`.
Referencias: `backend/app/social_safety.py`, `backend/app/routes/social_safety.py`, `backend/app/routes/social_catalog.py`, `backend/app/routes/social_moderation.py`, `frontend/src/screens/AuthScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260530-01 - Setup do Zero começa após Linux e SSH ativo

Status: aceita
Data: 2026-05-30
Contexto: o Printora precisa ajudar no provisionamento de uma Raspberry/BTT Pi para impressoras Klipper, mas uma placa realmente virgem nao possui sistema operacional, rede ou serviço SSH. Prometer instalacao completa via SSH nesse estado seria tecnicamente incorreto.
Decisao: o fluxo `Setup do Zero` fica dividido em fase de preparo de mídia/boot, tratada como etapa manual ou futura, e fase SSH. O PKG-34 implementa apenas a fase SSH com preflight read-only, plano dry-run e historico sem segredos. Instalacao real, CAN, build remoto, flash e validacao final ficam em pacotes posteriores.
Alternativas consideradas: tentar instalar SO via SSH; incluir gravacao de SD/eMMC no mesmo pacote; criar um botao unico que executa KIAUH/instaladores direto.
Consequencias: o produto evita uma promessa impossivel para placa sem OS e cria uma base segura para automatizar instalacao em etapas futuras.
Impacto em testes: testes cobrem boundary de placa virgem, parser read-only, plano dry-run e ausencia de persistencia de `key_path`.
Impacto em rollback: baixo; remover a secao `setup` e as rotas `/api/setup/ssh/*` volta o produto ao estado anterior.
Como reverter: remover tela `SetupScreen`, hook/service/tipos de setup, rota `setup`, modulo `setup_wizard` e script SQL `021_setup_ssh_runs.sql`.
Referencias: `DEMANDAS.md`, `TESTES.md`, `TELAS.md`, `RUNBOOK.md`, `backend/app/setup_wizard.py`, `frontend/src/screens/SetupScreen.tsx`.

### DEC-20260530-02 - Setup CAN remoto exige modo operacional e confirmação

Status: aceita
Data: 2026-05-30
Contexto: configurar `can0` em uma Raspberry/BTT Pi altera rede e systemd, podendo derrubar comunicação com MCUs CAN se executado no momento errado. O fluxo precisa ser útil para setup do zero sem virar ação perigosa por clique acidental.
Decisao: o PKG-35 implementa diagnóstico read-only e plano dry-run por padrão. O apply real só executa com confirmação textual `CONFIGURAR CAN0`, variável de ambiente `PRINTORA_CAN_SETUP_MODE=remote`, preflight aprovado, sem impressão em andamento detectada e `sudo -n` disponível. Antes de escrever `/etc/systemd/system/can0.service`, o fluxo cria backup remoto em `~/.local/share/printora/can-setup/backups/<timestamp>/`.
Alternativas consideradas: manter CAN apenas como plano sem apply; executar apply sempre que o usuário clicar; editar arquivos de rede tradicionais como `/etc/network/interfaces` diretamente.
Consequencias: o produto entrega automação real controlada, mas continua bloqueado por padrão em ambientes comuns. O serviço systemd isolado reduz acoplamento com distribuições diferentes.
Impacto em testes: testes cobrem parsing de CAN/U2C/UUID, bloqueio por impressão, comandos `PLAN`, confirmação explícita e histórico sem `key_path`.
Impacto em rollback: médio; o rollback depende de restaurar o backup do serviço ou remover/desabilitar `can0.service` criado pelo Printora.
Como reverter: remover endpoints `/api/setup/can/*`, modulo `setup_can`, tela CAN em `SetupScreen`, SQL `022_setup_can_runs.sql` e documentação do PKG-35.
Referencias: `backend/app/setup_can.py`, `backend/sql/022_setup_can_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`.

### DEC-20260530-03 - Build remoto de firmware nunca faz flash

Status: aceita
Data: 2026-05-30
Contexto: depois de preparar SSH e CAN, o Printora precisa compilar firmware para placas reais no host da impressora. Misturar build e flash no mesmo passo aumentaria o risco de deixar MCU offline sem validação de artefatos.
Decisao: o PKG-36 implementa seleção de hardware real, geração remota de `.config`, build remoto e captura de artefatos/UUIDs, mas flash permanece fora do pacote. O build real exige `BUILD_FIRMWARE_NO_FLASH`, `PRINTORA_REMOTE_FIRMWARE_BUILD_MODE=remote`, variante física confirmada e restauração automática da `.config` por `trap`.
Alternativas consideradas: manter build apenas local; executar flash logo após build; editar `printer.cfg` automaticamente com UUID capturado.
Consequencias: o usuário ganha artefato rastreável e UUID sugerido sem mutação crítica de MCU ou config da impressora. O próximo pacote pode tratar flash com checklist próprio.
Impacto em testes: testes cobrem bloqueio sem variante confirmada, plano com comandos `PLAN`, ausência de comando de flash, confirmação textual e histórico sem `key_path`.
Impacto em rollback: médio; rollback do build é restaurar `.config.before-build` e apagar artefatos do build remoto.
Como reverter: remover endpoints `/api/setup/firmware/*`, modulo `setup_firmware`, SQL `023_setup_firmware_runs.sql`, UI Firmware remoto em `SetupScreen` e documentação do PKG-36.
Referencias: `backend/app/setup_firmware.py`, `backend/sql/023_setup_firmware_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`.

### DEC-20260522-01 - Governanca do monorepo fica na raiz

Status: aceita
Data: 2026-05-22
Contexto: `backend` e `frontend` estavam com copias completas dos documentos do modelo, criando redundancia e risco de divergencia.
Decisao: a raiz do monorepo e a fonte de verdade para `DEMANDAS.md`, `GOVERNANCA.md`, `QUALITY_ROADMAP.md`, `TESTES.md`, `BUGS.md`, `TELAS.md`, `DECISOES.md`, `RUNBOOK.md`, mapas e `check.sh`.
Alternativas consideradas: manter documentacao completa em cada modulo; duplicar apenas alguns arquivos.
Consequencias: a IA le menos arquivos, reduz conflito de regras e executa validacao por um ponto unico.
Impacto em testes: `./check.sh` da raiz passa a validar modelo, backend e frontend.
Impacto em rollback: baixo; restaurar documentos por modulo se algum fluxo exigir.
Como reverter: recriar documentacao especifica no modulo e apontar `PATHS.toml` do modulo para ela.
Referencias: `PATHS.toml`, `QUALITY_ROADMAP.md`, `check.sh`.

### DEC-20260525-01 - Instalacao usa porta 8069 e runtime local isolado

Status: aceita
Data: 2026-05-25
Contexto: instalacoes reais em Android/Termux e macOS falharam por divergencia de porta, Python global antigo, venv criada com Python incompatível e update orfao bloqueando novas versoes.
Decisao: a porta padrao do Printora e `8069`; scripts devem procurar Python `3.11+` sem remover Python antigo do usuario; a venv local deve ser recriada quando incompatível; recuperacao de update travado deve existir por UI e script oficial com backup do SQLite.
Alternativas consideradas: exigir que o usuario troque o Python global; manter comandos SQL manuais para destravar updates; manter `8085` como padrao em desktop.
Consequencias: instalacao fica mais previsivel, preserva sistemas legados do usuario e reduz suporte manual.
Impacto em testes: validar scripts de instalacao, endpoint de reconciliacao e build frontend com a nova acao.
Impacto em rollback: baixo; voltar para `8085` exigiria alterar scripts, docs e testes. Backups do banco sao criados antes do script de destravamento.
Como reverter: restaurar defaults anteriores e remover endpoint/botao/script de reconciliacao.
Referencias: `scripts/mpl_platform.sh`, `scripts/doctor_install.sh`, `scripts/unlock_update.sh`, `frontend/src/screens/SettingsScreen.tsx`, `backend/app/routes/system.py`.

### DEC-20260526-01 - Updates criticos da impressora exigem revisao e rollback visivel

Status: aceita
Data: 2026-05-26
Contexto: update de Klipper junto de plugin de toolchanger pode quebrar compatibilidade de API interna e impedir o Klipper de iniciar, sem aviso suficiente no Mainsail ou no proprio Update Manager.
Decisao: o Printora classifica `klipper` e componentes de toolchanger como risco alto quando ha update pendente, exige confirmacao literal antes de executar pelo backend/UI e exibe rollback por componente quando o Moonraker informa `rollback_version`.
Alternativas consideradas: deixar o fluxo igual ao Mainsail; apenas mostrar um aviso visual sem bloqueio backend; bloquear todos os updates globais.
Consequencias: update critico deixa de ser um clique acidental, mas continua disponivel para usuario tecnico que assumir o risco. Rollback fica operacional na mesma tela quando suportado pelo Moonraker.
Impacto em testes: adicionar testes de classificacao de risco, selecao de componentes de risco em `all` e exposicao de rollback.
Impacto em rollback: baixo; remover o guard e os campos novos restaura o comportamento anterior.
Como reverter: retirar a confirmacao de risco em `backend/app/routes/printer_updates.py`, remover metadados de risco em `backend/app/updates.py` e ocultar botoes/avisos da tela Atualizacoes.
Referencias: `backend/app/updates.py`, `backend/app/routes/printer_updates.py`, `frontend/src/screens/UpdatesScreen.tsx`.

### DEC-20260526-02 - Silencio de update vale por versao concreta do componente

Status: aceita
Data: 2026-05-26
Contexto: uma versao especifica de Klipper, plugin ou outro componente do Update Manager pode estar disponivel, mas ser indesejada no momento por quebrar o ambiente ou exigir rollback manual. O alerta recorrente passa a poluir Home, topbar, Central de alertas, Health, Checklist e Auditoria mesmo quando o usuario decidiu aguardar a proxima versao.
Decisao: permitir silenciar qualquer componente por impressora e por identidade concreta da leitura atual (`component_name` + versoes + atraso/pacotes + warnings/anomalias). Silenciar remove o item dos alertas e contadores ativos, mas mantem o card e as acoes `Reanalisar`, `Atualizar`, `Rollback` e `Reativar alerta`.
Alternativas consideradas: silenciar componente para sempre; esconder o card; transformar silencio em autorizacao de update; manter alerta sempre ativo.
Consequencias: reduz ruido operacional sem esconder a capacidade de atualizar manualmente. Quando a leitura do Update Manager muda, o silencio deixa de combinar e o alerta volta automaticamente.
Impacto em testes: cobrir persistencia SQLite, expiracao por nova versao, agregadores de Health/Checklist/Auditoria e UI da tela Atualizacoes.
Impacto em rollback: baixo; remover a tabela `update_alert_silences`, os endpoints de silencio e os filtros de agregacao restaura o comportamento anterior.
Como reverter: remover `backend/sql/019_update_alert_silences.sql`, `UpdateAlertSilenceRepository`, endpoints `/updates/silences`, filtros `printora_alert_silenced` e controles da tela Atualizacoes.
Referencias: `backend/app/updates.py`, `backend/app/routes/printer_updates.py`, `backend/app/health.py`, `backend/app/checklists.py`, `backend/app/audit.py`, `frontend/src/screens/UpdatesScreen.tsx`.

### DEC-20260526-03 - Feedback operacional usa modal e toast proprios

Status: aceita
Data: 2026-05-26
Contexto: dialogos nativos do navegador quebram a identidade visual do Printora e deixam confirmacoes operacionais importantes fora do padrao da aplicacao.
Decisao: confirmacoes de decisao devem usar modal proprio do shell React; feedback temporario de sucesso/falha deve usar toast. Erros persistentes e diagnosticos continuam inline ou na Central de alertas quando exigem acao ou leitura posterior.
Alternativas consideradas: continuar com `window.confirm`; trocar tudo por toast; usar modal para qualquer mensagem temporaria.
Consequencias: melhora consistencia visual sem esconder falhas que precisam ficar persistentes na tela.
Impacto em testes: validar build frontend e contrato de tela sem `window.confirm` no fluxo de silencio de versao.
Impacto em rollback: baixo; remover `ConfirmDialogModal`, `ToastViewport` e voltar chamadas para feedback inline/nativo.
Como reverter: retirar helpers `confirmAction`/`showToast` do shell e restaurar o fluxo anterior nos hooks.
Referencias: `frontend/src/hooks/usePrintoraApp.ts`, `frontend/src/components/modals/ConfirmDialogModal.tsx`, `frontend/src/components/ToastViewport.tsx`, `frontend/src/hooks/domains/useUpdates.ts`.

### DEC-20260526-04 - Consulta Moonraker nao pode travar a API local

Status: aceita
Data: 2026-05-26
Contexto: chamadas para hosts `.local` podem ficar presas em resolucao mDNS e bloquear o processo local do Printora, fazendo ate `/health` e acoes locais deixarem de responder.
Decisao: a gravacao de silencio de update usa a versao ja exibida no card, sem consultar Moonraker. O cliente Moonraker resolve `.local` fora do loop principal e falha com timeout curto quando a resolucao nao responde.
Alternativas consideradas: pedir reinicio manual sempre que a rota travar; manter consulta live do Moonraker antes de silenciar; trocar a porta/processo sem corrigir DNS.
Consequencias: acoes locais continuam responsivas mesmo com Moonraker lento ou DNS `.local` instavel. O silencio continua expirando quando uma nova leitura do Update Manager muda a identidade da versao.
Impacto em testes: cobrir endpoint de silencio com host Moonraker propositalmente irresolvivel e validar `./check.sh` com testes backend e frontend.
Impacto em rollback: medio; voltar a consulta live no silencio reintroduz risco de travar a UI durante falha de DNS.
Como reverter: remover campos de versao do payload de silencio, voltar a buscar `_current_update_component_payload` na rota e restaurar resolucao `.local` direta no cliente Moonraker.
Referencias: `backend/app/moonraker.py`, `backend/app/routes/printer_updates.py`, `frontend/src/hooks/domains/useUpdates.ts`.

### DEC-20260526-05 - Operacao envia G-code operacional com preflight

Status: aceita
Data: 2026-05-26
Contexto: a tela Operacao estava visualmente parecida com painel de controle, mas ainda funcionava como preview bloqueado. Isso confundia o usuario porque Mainsail permite operar movimento, temperatura, fan e fatores percentuais diretamente.
Decisao: liberar execucao operacional controlada por Moonraker para acoes de operacao da impressora, mantendo preflight live, capacidade confirmada, bloqueio quando ha impressao em andamento, historico local e monitoramento apos envio. Updates, restart, flash e alteracao de config continuam fora da tela Operacao.
Alternativas consideradas: manter apenas preview dry-run; liberar comandos sem preflight; exigir frase manual para cada clique operacional.
Consequencias: a tela passa a operar a impressora de verdade, com risco operacional proporcional a Mainsail. O backend continua bloqueando offline, Klipper/Klippy nao ready, impressao em andamento e capacidade desconhecida.
Impacto em testes: testes backend de operacao foram atualizados para `operation_ready`, preflight executavel e historico de execucao; validacao completa roda com `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
Impacto em rollback: medio; para voltar ao modelo dry-run, restaurar `build_operation_action_preflight` para `would_send_gcode=false`, remover `execute-direct` e voltar botoes da UI para preview.
Como reverter: remover endpoint `/operation/actions/execute-direct`, remover envio via `_send_and_monitor_gcode`, restaurar `can_send_commands=false` e voltar a UI para `Prévia`/`Preflight`.
Referencias: `backend/app/operation.py`, `backend/app/routes/operation.py`, `backend/app/operation_history.py`, `frontend/src/components/monitoring/OperationActions.tsx`.

### DEC-20260527-01 - Catalogo Esoterical CANBus tem schema Pydantic versionado

Status: aceita
Data: 2026-05-27
Contexto: o PKG-30 precisa transformar o guia Esoterical CANBus em catalogo local verificavel, sem depender do site em runtime e sem misturar dados manuais com cobertura nao comprovada.
Decisao: o catalogo local de firmware passa a ter contrato oficial em `FirmwareCatalog`, validado por Pydantic, com `schema_version`, `source`, `manifest`, `workflows`, `hardware`, `troubleshooting`, `update_flows`, `katapult`, `can_speed`, `known_hardware_without_local_preset` e `generation_metadata`. Cada hardware aceita `modelo`, role, conexao, guia, MCUs, metodo de flash, bootloader/Katapult, comandos de validacao, notas de seguranca, presets locais e status de catalogacao.
Alternativas consideradas: manter JSON livre sem contrato; criar tabela SQLite para catalogo; validar apenas no frontend.
Consequencias: a normalizacao, o cruzamento com presets locais, o endpoint read-only e a tela Firmware usam o mesmo contrato validado. O runtime continua lendo arquivo local e nao consulta o site externo.
Impacto em testes: testes backend validam o schema do catalogo, campos obrigatorios do contrato, vinculacao ao manifesto, cobertura do menu publico, dry-run dos scripts, exclusao de comandos mutaveis e runtime sem dependencia externa.
Impacto em rollback: baixo; remover os modelos novos e voltar ao loader JSON livre restaura o comportamento anterior, mas perde validacao de cobertura.
Como reverter: remover `FirmwareCatalog` e campos associados em `backend/app/firmware_catalog.py`, retirar o teste de schema e voltar `firmware_hardware_catalog.json` ao formato minimo anterior.
Referencias: `backend/app/firmware_catalog.py`, `backend/app/routes/firmware.py`, `backend/app/data/firmware_hardware_catalog.json`, `backend/app/data/firmware_canbus_manifest.json`, `backend/tests/test_canbus_manifest.py`, `backend/tests/test_firmware.py`, `scripts/build_canbus_manifest.py`, `scripts/build_firmware_catalog.py`, `frontend/src/screens/FirmwareScreen.tsx`.

### DEC-20260527-02 - Preset de firmware expõe build config versionado

Status: aceita
Data: 2026-05-27
Contexto: o PKG-33 precisa transformar presets locais em entrada segura para geracao futura de `.config`, sem depender de `make menuconfig`, host Klipper real ou estado de impressora.
Decisao: cada `BoardPreset` passa a expor `FirmwareBuildConfig` versionado, com arquitetura, MCU, modelo de processador, bootloader, clock, interface de comunicacao, conexao CAN/USB/serial, arquivo `.config` e output esperado. O backend calcula `build_config_status` e `build_config_validation` para classificar preset completo, faltando dados ou invalido.
Alternativas consideradas: inferir tudo apenas no gerador de `.config`; deixar validacao na UI; persistir configuracao em SQLite antes de existir edicao pelo usuario.
Consequencias: o contrato fica testavel e deterministico no endpoint de presets, sem banco novo e sem executar comandos mutaveis. A UI pode consumir o status sem duplicar regra de suficiencia.
Impacto em testes: testes backend cobrem preset completo, dados faltantes, schema invalido e compatibilidade do endpoint `/api/firmware/board-presets`.
Impacto em rollback: baixo; remover `FirmwareBuildConfig` e os campos calculados volta o preset ao contrato anterior, mas remove a garantia previa para geracao deterministica de `.config`.
Como reverter: remover `FirmwareBuildConfig`, `FirmwareBuildConfigValidation`, `build_config`, `build_config_status` e `build_config_validation` de `backend/app/firmware/models.py`, ajustar tipos frontend e remover testes do Lote 2.
Referencias: `backend/app/firmware/models.py`, `backend/app/firmware/presets.py`, `backend/tests/test_firmware.py`, `frontend/src/types/firmware.ts`.

### DEC-20260527-03 - Build local de firmware é controlado e nunca faz flash

Status: aceita
Data: 2026-05-27
Contexto: o PKG-33 precisa permitir build local real de firmware sem transformar o Printora em ferramenta de flash automático ou mutação remota de impressora.
Decisao: o build local só executa quando `PRINTORA_FIRMWARE_BUILD_MODE=local` e a confirmação textual `EXECUTE_LOCAL_BUILD_NO_FLASH` é enviada. O executor gera `.config` determinístico a partir do preset, faz backup da `.config` atual, executa apenas `make clean` e `make` no `klipper_path` local informado, restaura a `.config` em sucesso ou falha e salva preview, log e binário em `output_root/local-build/<placa>/`. Flash, SSH, restart e update ficam fora do fluxo.
Alternativas consideradas: manter apenas dry-run; aceitar `.config` manual cadastrado; expor flash na mesma UI; executar build sem confirmação textual.
Consequencias: o usuário pode validar build em ambiente local controlado com histórico e rollback, sem risco de flash automático. A UI permanece guiada pela impressora ativa e consome status do backend sem duplicar regra de build.
Impacto em testes: testes backend cobrem bloqueio por modo, bloqueio por confirmação, build fake em tmpdir, restauração de `.config` em sucesso e falha, log/binário salvos e ausência de flash/SSH/restart/update. Fechamento roda `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
Impacto em rollback: médio; remover execução local volta o fluxo para dry-run e preview de `.config`, preservando cadastro de presets.
Como reverter: remover `execute_build_local`, ocultar o bloco de build local da tela Firmware e manter apenas `/build-runs/dry-run`, `/build-runs/preflight` e `/config-preview`.
Referencias: `backend/app/firmware/build_service.py`, `backend/app/firmware/repository.py`, `backend/app/routes/firmware.py`, `frontend/src/screens/FirmwareScreen.tsx`, `RUNBOOK.md`, `TESTES.md`.

### DEC-20260530-04 - Flash supervisionado começa por CAN/Katapult com gate remoto

Status: aceita
Data: 2026-05-30
Contexto: o PKG-37 precisa permitir flash real sem transformar o Printora em executor perigoso por padrão. Flash incorreto pode deixar MCU offline e exige prova de artefato, placa, UUID e rollback.
Decisao: o backend implementa preflight/plan/execute/historico de flash em `Setup do Zero`, mas execução real inicial fica restrita a `can_katapult`. O flash exige checklist físico, UUID visível, artefato remoto existente, impressora parada, frase específica por placa/método e `PRINTORA_REMOTE_FLASH_MODE=remote`. Métodos `usb_dfu` e `manual` ficam bloqueados até política própria.
Alternativas consideradas: liberar qualquer comando manual; manter somente plano sem execução; implementar USB/DFU junto do CAN.
Consequencias: o fluxo entrega uma primeira execução real supervisionada com risco menor e rastreabilidade, sem editar `printer.cfg`, reiniciar serviços, rodar update ou enviar G-code. Hardware real ainda precisa validação acompanhada.
Impacto em testes: testes backend cobrem bloqueios, frase/env, histórico sem `key_path` e ausência de restart/config; frontend build valida contrato da UI.
Impacto em rollback: medio; remover endpoints `/api/setup/flash/*`, modulo `setup_flash`, SQL `024_setup_flash_runs.sql` e seção Flash supervisionado da UI volta o setup ao estado PKG-36.
Como reverter: reverter o commit do PKG-37 e restaurar banco a partir do backup de schema se o script `024_setup_flash_runs.sql` ainda não puder permanecer.
Referencias: `backend/app/setup_flash.py`, `backend/app/routes/setup.py`, `backend/sql/024_setup_flash_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`, `TESTES.md`.

### DEC-20260530-05 - Aceite final do setup é read-only e sanitizado

Status: aceita
Data: 2026-05-30
Contexto: após setup, CAN, firmware e flash, o Printora precisa diferenciar base eletrônica/software pronta de calibração mecânica ainda pendente sem executar comandos perigosos.
Decisao: a validação final executa somente leitura via SSH e Moonraker local, gera checks acionáveis e relatório Markdown sanitizado. O fluxo não envia G-code, não aquece, não move eixo, não reinicia serviços, não edita configs e não executa update.
Alternativas consideradas: usar health check genérico da impressora cadastrada; executar testes de movimento/temperatura; exigir cadastro prévio da impressora.
Consequencias: o setup pode ser fechado antes do cadastro final da impressora, com relatório técnico copiável e risco operacional baixo. Homologação em campo ainda depende de hardware real acompanhado.
Impacto em testes: testes backend cobrem aprovação, bloqueio por UUID ausente, intervenção manual sem UUID e histórico sem `key_path`; frontend build valida o contrato da tela.
Impacto em rollback: baixo; remover endpoints `/api/setup/final-validation/*`, módulo `setup_final_validation`, SQL `025_setup_final_validation_runs.sql` e seção Validação final da UI.
Como reverter: reverter o commit do PKG-38 e restaurar banco a partir do backup de schema se o script `025_setup_final_validation_runs.sql` ainda não puder permanecer.
Referencias: `backend/app/setup_final_validation.py`, `backend/app/routes/setup.py`, `backend/sql/025_setup_final_validation_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`, `TESTES.md`.

### DEC-20260530-06 - Autenticação cloud começa em SQLite com organização opcional

Status: aceita
Data: 2026-05-30
Contexto: o Printora local não exige login, mas a evolução cloud precisa de usuário, sessão, permissões, compartilhamento opcional e base segura para agente remoto. A migração imediata para Postgres aumentaria o custo antes da validação do fluxo.
Decisao: implementar o PKG-39 primeiro em SQLite, com repositório concentrado e SQL simples, evitando dependências desnecessárias de SQLite para facilitar migração futura para Postgres. O modelo é usuário-first: email e senha obrigatórios, contatos opcionais, organização opcional para compartilhamento e papéis mínimos `owner`, `admin` e `operator`.
Alternativas consideradas: migrar já para Postgres; tornar organização obrigatória; manter somente usuário individual sem compartilhamento; deixar 2FA para pacote futuro.
Consequencias: o app local continua funcionando sem login obrigatório, enquanto a área `Conta` entrega cadastro/login, organizações, 2FA, step-up auth e credenciais de agente para o caminho cloud. Rotas operacionais passam a validar sessão quando há usuários cadastrados, rotas por impressora usam o escopo usuário/organização e históricos de setup/update passam a ter owner. A migração futura para Postgres ainda exigirá trabalho de adaptação e validação, mas fica menos arriscada.
Impacto em testes: `backend/tests/test_auth.py` cobre schema, cadastro/login, organização opcional, 2FA, step-up, credencial de agente, bloqueio anônimo de `/api/auth/me`, isolamento por impressora e isolamento de histórico operacional.
Impacto em rollback: médio; remover a camada exige reverter rotas, UI, SQL `026_auth_identity.sql`, `027_printer_ownership.sql`, `028_operational_ownership.sql` e restaurar backup do banco se o schema aplicado não puder permanecer.
Como reverter: reverter arquivos do PKG-39 e restaurar `printora.<timestamp>.before-schema.db` quando for necessário desfazer o schema aplicado.
Referencias: `backend/app/auth.py`, `backend/app/routes/auth.py`, `backend/sql/026_auth_identity.sql`, `backend/sql/027_printer_ownership.sql`, `backend/sql/028_operational_ownership.sql`, `frontend/src/screens/AuthScreen.tsx`, `frontend/src/hooks/domains/useAuth.ts`.

### DEC-20260531-08 - Impressora cloud é cadastro operacional com status derivado do agente

Status: aceita
Data: 2026-05-31
Contexto: o cadastro local de impressoras dependia de Moonraker acessível pela mesma rede, mas o uso cloud precisa permitir cadastrar a impressora antes do agente existir e compartilhar acesso por organização opcional.
Decisao: manter `printers` como entidade canônica, com owner e organização opcional do PKG-39, metadados cloud (`cloud_model`, `cloud_tags`, localização e observações) e status calculado a partir de tokens/agentes/snapshots existentes. O cadastro não tenta conectar no Moonraker automaticamente; descoberta, teste e leitura de status continuam como ações explícitas.
Consequencias: o usuário consegue preparar as duas impressoras na aplicação local por IP da API, instalar/parear agentes depois e ver estados `sem_agente`, `aguardando_pareamento`, `online`, `offline` ou `revogado` sem criar tabela nova de inventário.
Impacto em testes: `backend/tests/test_auth.py` cobre metadados cloud, detalhe escopado, status por token/agente e isolamento para usuário sem acesso.
Como reverter: reverter alterações do PKG-40 em backend/UI/docs; dados existentes de impressoras permanecem preservados e podem ser mantidos até nova decisão.
Referencias: `backend/app/printers.py`, `backend/app/routes/printers.py`, `frontend/src/screens/PrintersScreen.tsx`, `frontend/src/components/modals/PrinterModal.tsx`.

### DEC-20260530-07 - Pareamento do agente usa token curto e credencial operacional por hash

Status: aceita
Data: 2026-05-30
Contexto: o agente precisa parear a partir da rede da impressora, sem o servidor acessar a rede local e sem transformar o token de instalação em credencial permanente.
Decisao: usar token curto de pareamento por impressora, persistido por hash, com expiração, uso único e revogação. A troca pública gera uma credencial operacional `ptr_agent_*`, também persistida por hash, ligada a uma identidade estável do agente. Rotação substitui a credencial ativa e revogação bloqueia heartbeat, snapshot e jobs.
Alternativas consideradas: reutilizar credenciais genéricas do PKG-39; usar token de pareamento como credencial permanente; deixar revogação para pacote futuro.
Consequencias: o usuário consegue instalar/copiar um segredo curto uma vez e o agente passa a autenticar sem expor token permanente. A etapa ainda não instala o agente nem executa comandos remotos; isso fica para pacotes posteriores.
Impacto em testes: `backend/tests/test_agent_pairing.py` cobre uso único, expiração, revogação, ownership, rotação e bloqueio de endpoints do agente revogado.
Impacto em rollback: médio; remover exige reverter rotas, UI, `backend/app/agent_pairing.py` e SQL `029_agent_pairing.sql`, ou restaurar backup do banco anterior ao schema.
Como reverter: reverter arquivos do PKG-41 e restaurar `printora.<timestamp>.before-schema.db` se o schema aplicado não puder permanecer.
Referencias: `backend/app/agent_pairing.py`, `backend/app/routes/agents.py`, `backend/sql/029_agent_pairing.sql`, `frontend/src/screens/PrintersScreen.tsx`, `frontend/src/hooks/domains/usePrinters.ts`.

### DEC-20260531-01 - Agente remoto base em Go

Status: aceita
Data: 2026-05-31
Contexto: o agente precisa rodar em hosts Klipper variados, normalmente Raspberry/BTT Pi, com baixo uso de memória, instalação simples, atualização previsível e sem depender de Python/Node locais.
Decisao: implementar o agente em Go, sem dependências externas, como binário único com CLI `printora-agent`. A base usa config JSON, credencial separada `0600`, HTTP keep-alive, cliente Moonraker read-only, fila JSONL local, logs com redaction e serviço systemd.
Alternativas consideradas: Python para ficar próximo do ecossistema Klipper; Node por reaproveitar stack web; shell scripts para instalação mínima.
Consequencias: distribuição e atualização ficam simples por arquitetura Linux (`arm64`, `armv7`, `amd64`), com menor risco de quebrar venvs Python da impressora. Em troca, integrações futuras precisarão manter contratos Go e testes próprios.
Impacto em testes: `agent/internal/agent/agent_test.go` cobre redaction, permissões, coleta read-only, autenticação Bearer e fila local; `check.sh` passa a executar `go test ./...` em `agent/`.
Impacto em rollback: baixo; remover o agente exige reverter `agent/`, entradas em `PATHS.toml`, `check.sh` e docs. No host real, parar/remover o serviço systemd e o binário.
Como reverter: `sudo systemctl disable --now printora-agent`, remover `/usr/local/bin/printora-agent` e restaurar commit anterior ao PKG-42.
Referencias: `agent/cmd/printora-agent/main.go`, `agent/internal/agent`, `agent/systemd/printora-agent.service`, `agent/docs/README.md`.

### DEC-20260531-02 - Canal remoto usa WebSocket primario e polling de fallback

Status: aceita
Data: 2026-05-31
Contexto: o agente precisa receber comandos rápidos da aplicação web sem abrir portas no host Klipper e sem depender de conectividade WebSocket perfeita em todas as redes.
Decisao: implementar protocolo v1 sobre WebSocket outbound autenticado por credencial operacional do agente, com fallback HTTPS por polling. Jobs ficam persistidos em `agent_jobs`, sempre vinculados a `printer_id` e opcionalmente a `agent_id`, com `correlation_id` único, ack/nack/result/error, limite de payload de 64 KB e resultado idempotente. O agente deve continuar reconectando sozinho com backoff limitado e manter heartbeat/polling HTTPS durante perda de WebSocket para reduzir necessidade de reiniciar a impressora.
Alternativas consideradas: manter apenas polling; abrir socket raw; abrir porta inbound no agente; executar jobs sem persistência.
Consequencias: a latência normal fica baixa por WebSocket e ambientes restritos continuam funcionando por HTTPS. O servidor preserva isolamento por impressora e o agente continua outbound/read-only nesta etapa, aceitando apenas jobs seguros `ping` e `snapshot`. Quedas intermitentes de internet ou proxy nao devem deixar o agente parado esperando reinicio manual.
Impacto em testes: `backend/tests/test_agent_channel.py` cobre isolamento, WebSocket, versão incompatível e idempotência; `agent/internal/agent/agent_test.go` cobre polling, ack/result, URL WebSocket segura, fallback repetido e limite de backoff.
Impacto em rollback: médio; remover exige reverter rotas, serviço de jobs, agente e SQL `030_agent_channel.sql`, ou restaurar backup do banco anterior ao schema se a tabela não puder permanecer.
Como reverter: reverter arquivos do PKG-43, desativar WebSocket no config do agente com `"websocket_enabled": false` durante transição e restaurar `printora.<timestamp>.before-schema.db` se necessário.
Referencias: `backend/app/agent_pairing.py`, `backend/app/routes/agents.py`, `backend/sql/030_agent_channel.sql`, `backend/tests/test_agent_channel.py`, `agent/internal/agent/channel.go`, `agent/internal/agent/api.go`.

### DEC-20260531-03 - Instalador do agente troca token curto no host e preserva dados no uninstall

Status: aceita
Data: 2026-05-31
Contexto: o usuário precisa instalar o agente no host Klipper com o menor erro manual possível, sem transformar o token de pareamento em segredo permanente e sem esconder riscos de systemd, Moonraker, rede ou permissão.
Decisao: gerar um plano de instalação por impressora com token curto, servir um script Linux público sem segredo embutido e fazer a troca do token por credencial operacional no próprio host. O instalador tem `--preflight`, `--apply --yes` e `--uninstall`, exige systemd para serviço, grava config/credencial com permissão restrita e preserva dados locais no uninstall.
Alternativas consideradas: embutir credencial operacional no comando; instalar sem preflight; apagar diretórios no uninstall; deixar a instalação somente documentada.
Consequencias: a instalação fica copiável pela UI e auditável por status de heartbeat, mantendo uso único do token. O pacote ainda não faz auto-update nem resolve distribuição final de binários por release; isso fica para o PKG-45.
Impacto em testes: `backend/tests/test_agent_install.py` cobre isolamento do plano, consumo único do token, status por heartbeat e preflight sem vazamento de token.
Impacto em rollback: baixo; remover exige reverter endpoints/UI/script e, no host real, rodar `--uninstall`. Dados locais do agente permanecem até remoção manual explícita.
Como reverter: revogar tokens/agentes pela tela Impressoras, rodar `curl -fsSL <api>/api/agent/install/linux.sh | sudo bash -s -- --uninstall` no host e reverter arquivos do PKG-44.
Referencias: `backend/scripts/install_agent_linux.sh`, `backend/app/routes/agents.py`, `backend/app/agent_pairing.py`, `backend/tests/test_agent_install.py`, `frontend/src/screens/PrintersScreen.tsx`.

### DEC-20260531-04 - Update do agente troca apenas o binário e exige SHA-256

Status: aceita
Data: 2026-05-31
Contexto: o agente precisa evoluir junto com o servidor cloud, mas roda no host Klipper. Um update quebrado não pode reiniciar Klipper, Moonraker, firmware ou a impressora, e precisa ter rollback local.
Decisao: o agente consulta manifesto público versionado, escolhe release por plataforma, bloqueia versão/protocolo incompatível, exige SHA-256, baixa para staging, preserva backup do binário/config e troca somente o binário do `printora-agent`. Restart automático só é permitido para o serviço `printora-agent` quando `allow_service_restart=true`. Falha em health command ou restart restaura o binário anterior quando possível. A UI cria um job direcionado `remote_agent_update_check` para antecipar a verificação periódica sem acessar a rede local diretamente.
Alternativas consideradas: delegar update ao Moonraker Update Manager; baixar sem hash em ambiente de desenvolvimento; reiniciar todos os serviços do host; deixar update apenas manual.
Consequencias: o update fica automatizável e auditável sem tocar na impressora. A publicação real de binários e assinatura forte ainda depende do fluxo de release do agente, mas o contrato já bloqueia aplicação sem hash.
Impacto em testes: `backend/tests/test_agent_updates.py` cobre manifesto, relatório autenticado e histórico isolado; `backend/tests/test_agent_support.py` cobre job remoto de update direcionado; `agent/internal/agent/agent_test.go` cobre sucesso, hash inválido, rollback por health, versão bloqueada e execução do job remoto.
Impacto em rollback: médio; no host real, restaurar backup local do binário em `/var/lib/printora-agent/updates` e reiniciar apenas `printora-agent`.
Como reverter: desativar `"update_enabled": false` no config, reverter arquivos do PKG-45 e restaurar o binário anterior se necessário.
Referencias: `backend/app/agent_updates.py`, `backend/app/data/agent_update_manifest.json`, `agent/internal/agent/update.go`, `agent/cmd/printora-agent/main.go`, `RUNBOOK.md`.

### DEC-20260531-05 - Paridade remota usa matriz explícita e bloqueia mutações até PKG-47

Status: aceita
Data: 2026-05-31
Contexto: o Printora cloud precisa reutilizar as leituras e previews existentes sem o servidor acessar a rede local da impressora. Ao mesmo tempo, operações mutáveis remotas exigem autorização, preflight e rollback próprios.
Decisao: criar matriz de paridade por impressora com estados explícitos e jobs remotos executados pelo agente. Jobs read-only e dry-run são permitidos; backup real com payload grande, build/flash remoto e operação mutável ficam bloqueados até a camada de segurança do PKG-47.
Alternativas consideradas: tentar chamar Moonraker diretamente do servidor; liberar mutações junto com a paridade; esconder funcionalidades ainda não suportadas da matriz.
Consequencias: a UI/API consegue diferenciar implementado, cached, offline, bloqueado e não suportado, evitando falsa paridade. A execução remota continua outbound pelo agente e payloads são sanitizados antes de sair do host.
Impacto em testes: `backend/tests/test_agent_parity.py` cobre matriz, isolamento, criação de job, estado cached e bloqueio; `agent/internal/agent/agent_test.go` cobre job remoto read-only com sanitização.
Impacto em rollback: baixo; remover rotas e jobs de paridade volta o cloud ao pareamento/canal remoto sem alterar schema.
Como reverter: reverter arquivos do PKG-46; jobs já concluídos permanecem em `agent_jobs` como histórico seguro.
Referencias: `backend/app/agent_parity.py`, `backend/app/routes/agents.py`, `backend/tests/test_agent_parity.py`, `agent/internal/agent/moonraker.go`, `agent/internal/agent/channel.go`.

### DEC-20260531-06 - Operação remota mutável exige preflight e execução em jobs separados

Status: aceita
Data: 2026-05-31
Contexto: operações mutáveis pelo agente podem mover, aquecer ou alterar estado da impressora fora da rede local. A execução não pode depender só de clique na UI nem de confiança implícita no agente.
Decisao: separar toda operação remota mutável em dois jobs persistidos: `remote_mutation_preflight` e `remote_mutation_execute`. O servidor cria execução somente para usuário com acesso à impressora, com preflight concluído, confirmação textual única, job não expirado e resultado `can_execute=true`. O agente reexecuta preflight imediatamente antes de enviar G-code e usa apenas `/printer/gcode/script`, sem shell genérico.
Alternativas consideradas: executar direto depois da confirmação na UI; reaproveitar jobs de paridade; permitir comando arbitrário no agente; criar tabela nova de auditoria.
Consequencias: aumenta a latência operacional, mas reduz risco de ação remota fora de estado seguro. `agent_jobs` e `printer_agent_events` viram a trilha de auditoria principal sem aumentar schema.
Impacto em testes: `backend/tests/test_remote_operations.py` cobre escopo, preflight, confirmação, bloqueio por impressão e cancelamento; `agent/internal/agent/agent_test.go` cobre preflight/execução remota sem shell.
Impacto em rollback: baixo; remover rotas, módulo remoto, UI e handlers do agente volta as mutações remotas ao bloqueio do PKG-46. Jobs históricos permanecem como auditoria.
Como reverter: reverter arquivos do PKG-47 e manter agentes instalados; eles passarão a responder `unsupported job type` se algum job antigo for reenviado.
Referencias: `backend/app/remote_operations.py`, `backend/app/routes/agents.py`, `backend/tests/test_remote_operations.py`, `agent/internal/agent/moonraker.go`, `agent/internal/agent/channel.go`, `frontend/src/screens/PrintersScreen.tsx`.

### DEC-20260531-07 - Suporte do agente usa eventos/jobs existentes e pacote sanitizado

Status: aceita
Data: 2026-05-31
Contexto: suporte precisa diagnosticar agente remoto sem acessar a rede local do cliente e sem criar um novo repositório de logs sensíveis.
Decisao: usar `printer_agents`, `agent_jobs` e `printer_agent_events` como fonte de observabilidade. O painel calcula saúde, fila, falhas e alertas em leitura; `remote_doctor` coleta diagnóstico local pelo agente; o pacote de suporte é exportado sanitizado e não cria tabela nova.
Alternativas consideradas: criar tabela dedicada de logs; enviar logs completos do host; diagnosticar somente por heartbeat; apagar eventos automaticamente no endpoint.
Consequencias: a solução fica simples e auditável, sem duplicar persistência. A limpeza fica definida como retenção operacional de 180 dias e deve ser executada por rotina supervisionada futura, não pelo endpoint de suporte.
Impacto em testes: `backend/tests/test_agent_support.py` cobre escopo, alertas, doctor e sanitização do pacote; `agent/internal/agent/agent_test.go` cobre doctor remoto com log tail sanitizado.
Impacto em rollback: baixo; remover rotas/UI/handler `remote_doctor` preserva os eventos e jobs já existentes.
Como reverter: reverter arquivos do PKG-48; agentes antigos passam a rejeitar `remote_doctor` como job não suportado.
Referencias: `backend/app/agent_support.py`, `backend/app/routes/agents.py`, `backend/tests/test_agent_support.py`, `agent/internal/agent/doctor.go`, `frontend/src/screens/PrintersScreen.tsx`.

### DEC-20260531-08 - Rotas operacionais usam agente como caminho principal

Status: aceita
Data: 2026-05-31
Contexto: a aplicação precisa funcionar em cenário cloud/rede local sem depender de o servidor alcançar diretamente o Moonraker ou SSH da impressora. A impressora selecionada deve ser operada pelo agente pareado como caminho principal.
Decisao: centralizar criação, push e espera de jobs em um executor do agente e migrar status, operação, snapshots, auditoria, relatórios, checklist, calibração, update manager e inventário de firmware para jobs outbound pelo agente. Acesso direto ao Moonraker/SSH permanece apenas como legado/bootstrap de setup ou utilitário local explícito, não como caminho operacional das telas principais.
Alternativas consideradas: manter chamadas diretas com fallback para agente; duplicar lógica por rota; abrir conectividade inbound no host Klipper; permitir shell genérico no agente.
Consequencias: as telas principais passam a depender de agente online e exibem erro quando não há agente, reduzindo risco de isolamento e aproximando o ambiente local do futuro cloud. O agente precisa evoluir junto do servidor, por isso a versão esperada foi atualizada para `0.1.8`.
Impacto em testes: `./check.sh`, `go test ./...`, testes focados de backend e smoke real nas duas impressoras com status, operação, update refresh, calibração, snapshot, firmware inventory e execução segura `M106 S0`.
Impacto em rollback: médio; reverter exige restaurar handlers diretos das rotas e reinstalar agente anterior se necessário. Jobs históricos permanecem em `agent_jobs`.
Como reverter: reverter este commit, reinstalar binário do agente anterior em `/usr/local/bin/printora-agent` nos hosts e reiniciar apenas `printora-agent`.
Referencias: `backend/app/agent_executor.py`, `backend/app/agent_channel.py`, `backend/app/agent_moonraker.py`, `backend/app/routes/operation.py`, `backend/app/routes/calibration.py`, `agent/internal/agent/moonraker.go`, `agent/internal/agent/channel.go`.

### DEC-20260531-09 - Fluxos de impressora em cloud nao usam rede local pela API

Status: aceita
Data: 2026-05-31
Contexto: ao publicar a API em IP publico, ela nao tera acesso a Moonraker, SSH, CAN, arquivos ou rede local da impressora. Qualquer fluxo que ainda roda no servidor da API gera falso positivo local e falha em cloud.
Decisao: desativar descoberta/teste direto pela API, mover setup, CAN, firmware, flash, validacao final, auditoria de host, horas de impressao, backup e build de firmware para jobs do agente. O job `remote_host_script` executa scripts controlados gerados pelo backend no host pareado; os demais fluxos continuam usando jobs Moonraker especificos do agente.
Alternativas consideradas: manter fallback direto para ambiente local; exigir VPN/rede privada entre cloud e impressora; manter SSH via API para setup.
Consequencias: a API passa a bloquear quando nao existe agente pareado/online em vez de tentar rede local. Setup de uma placa sem agente exige primeiro instalar/parear um agente na impressora ou em um futuro agente de rede dedicado para descoberta.
Impacto em testes: backend completo, Go completo e busca por chamadas diretas de Moonraker/SSH nas rotas operacionais.
Impacto em rollback: medio; reverter recoloca caminhos diretos e deve ser evitado em ambiente cloud.
Como reverter: reverter esta decisao e os arquivos de agente/backend relacionados; reinstalar agente anterior se necessario.
Referencias: `backend/app/agent_host.py`, `backend/app/routes/printers.py`, `backend/app/routes/setup.py`, `backend/app/routes/backups.py`, `backend/app/routes/firmware.py`, `backend/app/routes/audit.py`, `agent/internal/agent/host.go`.

### DEC-20260531-10 - Navegacao cloud usa frota e detalhe de registro

Status: aceita
Data: 2026-05-31
Contexto: o Printora deixou de ser apenas uma UI local para uma impressora e passou a operar em ambiente web/cloud com varias impressoras e agentes. A navegacao antiga escondia ou expunha secoes com base em uma impressora ativa global, o que nao escala para frota, agentes remotos e usuarios/organizacoes.
Decisao: o menu principal passa a conter somente areas globais independentes de impressora. `Impressoras` e `Agentes` viram listas de frota; operacao, atualizacoes, calibracao, firmware, manutencao, diagnostico/backups e pareamento ficam dentro do detalhe da impressora. Saude, fila, doctor remoto, suporte e credencial ficam dentro do detalhe do agente. A topbar fica fixa e global, sem seletor de impressora e sem acoes especificas de tela; ela mostra titulo, alertas de frota, Sobre, tema e conta do usuario no extremo direito.
Alternativas consideradas: manter grupo `Impressora ativa` no menu; esconder secoes quando a impressora estiver offline; criar rotas separadas para cada tela operacional ainda dependentes de contexto global.
Consequencias: a UI fica coerente com cloud/frota e evita que telas globais desaparecam por falta de impressora. Acoes contextuais passam a ficar no corpo da tela ou aba especifica. A Central de alertas precisa agregar alertas de frota e permitir abrir a impressora afetada.
Impacto em testes: build frontend deve passar e `./check.sh` valida documentacao/governanca. Validacao visual deve abrir menu global, lista de impressoras, detalhe da impressora e detalhe do agente.
Impacto em rollback: baixo a medio; reverter restaura as secoes operacionais no menu lateral e remove `PrinterDetailScreen`/`AgentDetailScreen`.
Como reverter: reverter alteracoes em `frontend/src/app/navigation.ts`, `frontend/src/hooks/usePrintoraApp.ts`, `frontend/src/main.tsx`, telas novas de detalhe e atualizacoes de `TELAS.md`.
Referencias: `frontend/src/app/navigation.ts`, `frontend/src/screens/PrinterDetailScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `frontend/src/screens/PrintersScreen.tsx`, `frontend/src/screens/AgentsScreen.tsx`, `TELAS.md`.

### DEC-20260531-11 - Update de agente usa job remoto direto

Status: substitui a decisão original de fallback por SSH
Data: 2026-05-31
Atualizacao: 2026-06-01
Contexto: o fallback por SSH gerava falha de credencial e contradizia o objetivo cloud: se o agente já está instalado e online, ele deve receber a ação pelo canal do agente e se autoatualizar.
Decisao: a UI e o backend sempre criam `remote_agent_update_check` para o agente ativo, independentemente da versão reportada. O instalador systemd padrão roda o agente como `root` para que o próprio agente consiga trocar `/usr/local/bin/printora-agent` e reiniciar `printora-agent` sem SSH, senha ou ação manual do usuário.
Alternativas consideradas: manter SSH como ponte para agentes antigos; exigir comando manual; usar sudoers específico para o usuário `printora-agent`; criar shell genérico remoto.
Consequencias: o fluxo fica consistente com cloud e usuário leigo. O agente instalado tem privilégio maior no host, limitado pelo contrato de jobs explícitos e sem shell genérico. Hosts antigos instalados sem permissão suficiente podem precisar reinstalação única do serviço para ganhar o novo modelo.
Impacto em testes: `backend/tests/test_agent_support.py` cobre criação direta do job remoto para agente antigo e atual; build frontend valida remoção dos rótulos de SSH/manual.
Impacto em rollback: médio; voltar ao fallback SSH exige restaurar `_request_legacy_update_via_ssh` e rótulos da UI.
Como reverter: reverter alterações em `backend/app/agent_support.py`, instalador do agente, unit systemd e textos da UI/documentação.
Referencias: `backend/app/agent_support.py`, `backend/scripts/install_agent_linux.sh`, `agent/systemd/printora-agent.service`, `frontend/src/screens/AgentsScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `RUNBOOK.md`.

### DEC-20260601-01 - Administracao cloud separa plataforma, impressora e agente

Status: aceita
Data: 2026-06-01
Contexto: a tela antiga de configuracoes misturava update do Printora, diagnostico local do servidor, CAN da impressora e diagnostico do host onde o agente roda. Em cloud isso confunde operador e expõe informacoes que pertencem a outros contextos.
Decisao: manter `settings` como tela global de Administracao, sem releases da plataforma para usuarios comuns. Versao publicada, releases e historico administrativo da plataforma ficam restritos ao usuario de suporte `breno@mayder.com.br`; a operacao de update visivel ao cliente passa a ser por agente. Registro tecnico CAN passa para `Detalhe da impressora > Diagnostico`. Diagnostico de host/dispositivo passa para `Detalhe do agente`, abastecido por doctor remoto do agente, incluindo leitura Raspberry de energia/throttling quando disponivel.
Alternativas consideradas: manter os blocos colapsados em Configuracoes; criar uma tela global de Diagnostico tecnico; esconder os blocos apenas por permissao.
Consequencias: o operador leigo ve menos acoes perigosas no escopo global. Suporte passa a diagnosticar impressora e agente no registro correto. O doctor remoto precisa evoluir junto do agente para ampliar leituras de hardware.
Impacto em testes: build frontend, testes Go do agente e `./check.sh` devem validar a reorganizacao.
Impacto em rollback: baixo; reverter esta decisao devolve os blocos para Settings e remove a leitura Raspberry do doctor.
Como reverter: reverter alteracoes em `frontend/src/screens/SettingsScreen.tsx`, `frontend/src/screens/ReportsScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `agent/internal/agent/doctor.go` e documentacao.
Referencias: `frontend/src/screens/SettingsScreen.tsx`, `frontend/src/screens/ReportsScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `agent/internal/agent/doctor.go`, `TELAS.md`.

### DEC-20260609-01 - SAVE_CONFIG fica como acao supervisionada

Status: aceita
Data: 2026-06-09
Contexto: calibrações Klipper como `PID_CALIBRATE` retornam valores úteis no console e pedem `SAVE_CONFIG` para gravar no `printer.cfg` e reiniciar o firmware. O Printora precisa guardar o retorno técnico sem aplicar alterações permanentes automaticamente.
Decisao: o agente captura trecho do `/server/gcode_store` após execuções de calibração e o backend salva esse retorno no histórico. Quando o console indicar `SAVE_CONFIG`, a UI mostra os parâmetros e explica que a configuração ainda precisa ser salva. A aplicação oferece `Salvar config` como ação operacional supervisionada, com preflight e confirmação, mas não dispara esse comando automaticamente a partir do resultado de calibração.
Alternativas consideradas: salvar automaticamente após PID; deixar o usuário ir sempre ao Mainsail; armazenar só uma nota manual. 
Consequencias: o histórico passa a guardar evidência técnica do PID e o operador tem caminho explícito para aplicar valores pendentes, preservando controle humano sobre escrita em arquivo e restart do Klipper.
Impacto em testes: `backend/tests/test_calibration.py` cobre extração do console/PID; `backend/tests/test_operation.py` cobre preview `SAVE_CONFIG`; `go test ./...`, build frontend e `./check.sh` validam o fluxo.
Impacto em rollback: médio; remover a ação `save_config` volta a exigir Mainsail para salvar, mas os históricos já registrados permanecem legíveis como JSON.
Como reverter: reverter alterações em `backend/app/routes/calibration.py`, `backend/app/operation.py`, `agent/internal/agent/moonraker.go`, modais de calibração e manifesto/binário do agente.

### DEC-20260609-02 - Remediacao supervisionada de config incluida

Contexto: em instalacoes Klipper com `[include ...]`, `SAVE_CONFIG` pode falhar com conflito quando a secao/opcao gerenciada esta em arquivo incluido, por exemplo `[extruder] control`. Nesse caso o usuario precisa de um caminho seguro para aplicar os valores calculados sem editar arquivo manualmente.

Decisao: quando houver valores calculados em uma calibracao e o `SAVE_CONFIG` falhar por conflito de include, o Printora oferece uma remediacao supervisionada: o agente varre somente `~/printer_data/config`, considera arquivos `.cfg` e `.conf`, ignora comentarios/backups, lista todas as secoes ativas compatíveis, mostra diff por arquivo e aplica apenas os alvos selecionados pelo usuario. A aplicacao exige autenticacao reforcada, cria backup remoto antes de sobrescrever e reinicia o firmware apos aplicar.

Consequencias: o fluxo continua explicito e auditavel, sem alterar arquivos fora da pasta de configuracao da impressora. A primeira implementacao expõe a remediacao para PID do hotend; o backend aceita secao/opcoes genericas para evoluir para outras calibracoes.

Impacto em testes: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

Como reverter: reverter `backend/app/config_remediation.py`, endpoints de remediacao em `backend/app/routes/calibration.py` e componentes/estado de remediacao no frontend.
Referencias: `backend/app/routes/calibration.py`, `backend/app/operation.py`, `agent/internal/agent/moonraker.go`, `frontend/src/components/modals/CalibrationExecuteModal.tsx`, `frontend/src/components/modals/CalibrationResultModal.tsx`.

### DEC-20260601-03 - Update de agente sem SSH e manifesto derivado do artefato publicado

Status: aceita
Data: 2026-06-01
Contexto: o update do agente deve ser simples para usuario leigo e nao pode depender de SSH salvo como ultimo recurso. O manifesto estatico tambem pode ficar divergente do binario realmente servido, causando falha de SHA-256.
Decisao: o endpoint de update do agente cria job `remote_agent_update_check`, tenta entregar imediatamente via WebSocket e mantém fallback por heartbeat/polling. O manifesto publico do agente recalcula URL e SHA-256 a partir do artefato local publicado em `.artifacts/agent` antes de responder.
Consequencias: a UI deixa de sugerir update por SSH. Se o agente estiver online e suportar o job de update, a acao chega imediatamente; se nao estiver, fica pendente para o proximo contato. Agentes legados que ainda nao suportam `remote_agent_update_check` precisam de uma atualizacao/reinstalacao manual unica para entrar no fluxo novo. Falha real passa a vir do resultado do job ou do relatorio do agente, nao do SSH da impressora.
Como reverter: voltar `backend/app/routes/agents.py`, `backend/app/agent_support.py`, `backend/app/agent_updates.py`, `frontend/src/hooks/domains/usePrinters.ts` e documentacao.

### DEC-20260609-02 - Datas usam timezone do usuario na UI

Status: aceita
Data: 2026-06-09
Contexto: dados persistidos em SQLite usam timestamps UTC/texto sem offset em vários módulos. Somar ou subtrair horas no banco corromperia histórico e criaria divergência entre usuários.
Decisao: adicionar `timezone` em `auth_users` e usar esse valor apenas na camada de formatação do frontend. A regra para datas novas e existentes é manter o valor bruto persistido e converter na UI por `formatDateTime`.
Consequencias: cada usuário vê horários no próprio fuso sem regravar históricos. Novas telas devem usar o formatter centralizado em vez de `new Date(...).toLocaleString(...)` local.
Impacto em testes: schema SQL, testes de auth, build frontend e `./check.sh`.
Impacto em rollback: baixo; remover a coluna volta ao fuso padrão do navegador/servidor, mas históricos permanecem intactos.
Como reverter: reverter `backend/sql/034_auth_user_timezone.sql`, campos de auth e formatter de datas do frontend.

### DEC-20260616-16 - Storage social usa cota antes da escrita e retenção supervisionada

Status: aceita
Data: 2026-06-16
Vigência: válida como política de storage/cota, mas subordinada à DEC-20260618-01; a superfície nova é `Projetos de impressão > Meus projetos`.
Contexto: a biblioteca social passou a aceitar arquivos reais em quarentena. Sem cota e retenção, o crescimento de arquivos ficaria sem controle e uma migração futura para object storage exigiria desfazer acoplamento ao filesystem local.
Decisao: criar uma camada dedicada de storage social com política de cota/custo/retenção, adapter local de caminho seguro e relatório autenticado de uso. O upload verifica cota antes de gravar o objeto local. Retenção gera revisão `dry_run` auditável e não apaga arquivo, linha ou versão automaticamente.
Alternativas consideradas: manter limite fixo de 25 MB por upload; apagar arquivos rejeitados imediatamente; implementar bucket externo já neste pacote.
Consequencias: o custo passa a ser mensurável, o usuário recebe feedback de cota e a operação de limpeza fica reversível/supervisionada. Object storage futuro troca adapter e backfill sem alterar contrato social principal.
Impacto em testes: testes de upload/cota, relatório de storage, revisão de retenção, schema versionado, build frontend e `./check.sh`.
Impacto em rollback: médio; reverter remove relatório e bloqueio de cota, mas arquivos já gravados permanecem no diretório local.
Como reverter: reverter `backend/app/social_storage.py`, `backend/app/routes/social_storage.py`, integração de upload em `social_catalog.py`, painel de biblioteca no frontend e documentação. Se `060_social_file_storage.sql` já tiver sido aplicado, restaurar backup SQLite anterior criado pelo versionador; não executar `DELETE` ou `DROP TABLE` sem confirmação explícita.

### DEC-20260616-17 - Fatiamento usa CLI externa controlada sem UI embutida

Status: aceita
Data: 2026-06-16
Vigência: válida como regra de engine controlada, mas subordinada à DEC-20260618-01; fatiamento real diário deve partir de projeto de impressão.
Contexto: o Printora precisa iniciar integração com engine de fatiamento sem transformar o produto em uma tela embutida do OrcaSlicer/PrusaSlicer nem executar comandos reais antes de perfil, impressora e material estarem compatíveis.
Decisao: a primeira ponte suporta OrcaSlicer/PrusaSlicer por CLI detectada no host ou agente, com configuração opcional por `PRINTORA_SLICER_ENGINE_PATH`. O backend expõe somente detecção, versão e dry-run de worker isolado; fatiamento real permanece bloqueado até o pipeline rastreável validar projeto/item legado, perfil, impressora e material.
Alternativas consideradas: embutir a UI do fatiador em iframe/webview; chamar qualquer binário configurado livremente; iniciar geração real de G-code no primeiro pacote.
Consequencias: a integração fica simples, auditável e reversível. O usuário recebe bloqueio claro quando a engine não está instalada, e os próximos pacotes podem acoplar jobs/artefatos sem refazer o contrato.
Impacto em testes: `backend/tests/test_slicing.py`, build frontend, schema versionado e `./check.sh`.
Impacto em rollback: baixo a médio; reverter remove endpoints e painel de engine, mas tabelas já aplicadas permanecem sem afetar impressoras, agentes ou arquivos.
Como reverter: reverter `backend/app/slicing.py`, `backend/app/routes/slicing.py`, integração em `backend/app/main.py`, painel de Administração e documentação. Se `061_slicing_engine_bridge.sql` já tiver sido aplicado e precisar desfazer schema, restaurar backup SQLite anterior criado pelo versionador; não executar `DROP TABLE` sem confirmação explícita.

### DEC-20260616-18 - Jobs de fatiamento persistem artefatos antes de qualquer envio

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: tabelas de job/artefato podem ser reaproveitadas, mas novos jobs diários devem nascer do projeto de impressão com snapshot imutável.
Contexto: o fatiamento precisava ser rastreável por item/modelo legado, perfil, impressora e usuário antes de qualquer preflight ou envio para Moonraker. No desenho substituído, isso evolui para projeto de impressão com snapshot imutável. Sem job persistido, erro de engine, incompatibilidade de volume e artefatos gerados ficariam soltos.
Decisao: criar `slicing_jobs` e `slicing_job_artifacts` como trilha do pipeline. O job começa planejado, pode ser executado/cancelado e só conclui quando o worker registra artefatos. Se a engine não estiver configurada, o job falha com log acionável em vez de criar G-code simulado.
Alternativas consideradas: reaproveitar apenas logs de dry-run; gravar G-code direto no filesystem sem linha de job; acoplar fatiamento ao envio para a impressora.
Consequencias: preflight e envio seguro passam a ter uma origem rastreável. O banco recebe tabelas aditivas e rollback estrutural deve restaurar backup SQLite em vez de remover dados manualmente.
Impacto em testes: `backend/tests/test_slicing_pipeline.py`, schema versionado, build frontend e `./check.sh`.
Impacto em rollback: médio; reverter remove API/UI do pipeline, mas jobs já criados permanecem no SQLite se o SQL tiver sido aplicado.
Como reverter: reverter `backend/app/slicing_pipeline.py`, endpoints de jobs em `backend/app/routes/slicing.py`, painel de pipeline no frontend e documentação. Se `062_slicing_jobs.sql` já tiver sido aplicado e precisar desfazer schema, restaurar backup SQLite anterior criado pelo versionador; não executar `DROP TABLE` sem confirmação explícita.

### DEC-20260616-19 - Preflight de impressão separa análise local e estado remoto

Status: aceita
Data: 2026-06-16
Contexto: G-code gerado por fatiamento precisa ser validado antes de qualquer envio para impressora. A análise do arquivo é local e reproduzível, mas o estado real da impressora depende do agente/Moonraker no momento do envio.
Decisao: persistir `print_preflight_checks` com metadados locais do G-code e, quando houver agente ativo, vincular um job `remote_gcode_preflight`. O preflight só fica aprovado quando não há blockers locais e o agente confirma `can_execute=true`, sem impressão em andamento.
Alternativas consideradas: validar apenas o G-code local; delegar todo preflight ao agente; acoplar preflight diretamente ao envio seguro.
Consequencias: PKG-73 pode exigir preflight aprovado e recente antes de salvar ou iniciar impressão. Ambientes sem agente continuam bloqueados com diagnóstico claro e checklist preservado.
Impacto em testes: `backend/tests/test_print_preflight.py`, fixture G-code, schema versionado, build frontend e `./check.sh`.
Impacto em rollback: médio; reverter remove API/UI de preflight, mas registros aplicados permanecem no SQLite se o script já rodou.
Como reverter: reverter `backend/app/print_preflight.py`, endpoints de preflight em `backend/app/routes/slicing.py`, painel de preflight no frontend e documentação. Se `063_print_preflight_checks.sql` já tiver sido aplicado e precisar desfazer schema, restaurar backup SQLite anterior criado pelo versionador; não executar `DROP TABLE` sem confirmação explícita.

### DEC-20260617-20 - Envio de G-code usa entrega auditada e upload remoto pelo agente

Status: aceita
Data: 2026-06-17
Contexto: depois do preflight aprovado, o Printora precisa salvar ou iniciar impressão sem expor G-code bruto no frontend, sem enviar para impressora errada e com rollback operacional quando o arquivo ainda não foi impresso.
Decisao: persistir `print_gcode_deliveries` como trilha de entrega e usar jobs de agente `remote_gcode_upload` e `remote_gcode_delete`. A entrega exige preflight aprovado e recente; iniciar impressão exige confirmação textual ou step-up válido. O agente reexecuta preflight remoto antes do upload e envia o arquivo por multipart para Moonraker.
Alternativas consideradas: enviar cada linha por `/printer/gcode/script`; acoplar envio diretamente ao preflight; salvar arquivo remoto sem auditoria dedicada.
Consequencias: o envio fica rastreável por usuário, impressora, job, preflight e checksum. O rollback automático só remove arquivo salvo sem impressão iniciada; impressão iniciada continua dependendo de ação operacional no Moonraker/Klipper.
Impacto em testes: `backend/tests/test_print_delivery.py`, testes Go do agente, build frontend, schema versionado e `./check.sh`.
Impacto em rollback: médio; reverter remove API/UI/agent jobs de entrega, mas registros aplicados permanecem no SQLite se o script já rodou.
Como reverter: reverter `backend/app/print_delivery.py`, endpoints de entrega em `backend/app/routes/slicing.py`, jobs `remote_gcode_upload`/`remote_gcode_delete` no agente, painel de entrega no frontend e documentação. Se `064_print_gcode_deliveries.sql` já tiver sido aplicado e precisar desfazer schema, restaurar backup SQLite anterior criado pelo versionador; não executar `DROP TABLE` ou remoção manual de arquivos sem confirmação explícita.

### DEC-20260618-02 - Meus projetos centraliza upload pessoal e referência externa

Status: aceita
Data: 2026-06-18
Contexto: depois da criação da entidade raiz `Projeto de impressão`, upload e links externos precisavam sair do fluxo diário de Comunidade. O usuário deve criar e gerir projeto pessoal antes de publicar, vender, compartilhar, fatiar ou enviar.
Decisao: adicionar rotas autenticadas em `/api/print-projects` para área pessoal, upload STL/3MF/ZIP em quarentena, link externo como `external_reference`, relatório de cota e arquivamento lógico. Comunidade continua N:N apenas para compartilhar/descobrir projeto. Referência externa sem arquivo local validado não é fatiável.
Alternativas consideradas: manter upload principal em Comunidade; criar uma nova entidade paralela de biblioteca pessoal; copiar arquivos ao salvar referência pública.
Consequencias: ownership, arquivos, visibilidade, publicação e comunidade ficam desacoplados. Falha de um arquivo bloqueia só aquele arquivo. Links externos não viram arquivos hospedados por inferência. O estado `em revisão` permanece em publicação, não em visibilidade, para preservar o schema já publicado.
Impacto em testes: `backend/tests/test_print_projects.py`, schema versionado, build frontend e `./check.sh`.
Impacto em rollback: médio; reverter remove as rotas e UI novas, mas arquivos de quarentena já gravados podem permanecer no filesystem local.
Como reverter: reverter `backend/sql/070_print_project_personal_library.sql`, `backend/app/print_projects.py`, `backend/app/routes/print_projects.py`, `frontend/src/screens/PrintProjectsScreen.tsx`, `frontend/src/services/printProjectsApi.ts`, `frontend/src/types/printProjects.ts`, estilos e documentação. Se o SQL já tiver sido aplicado, restaurar backup SQLite anterior; não executar `DROP TABLE`, recriação manual ou limpeza de arquivos sem confirmação explícita.

### DEC-20260618-03 - Publicação comercial de projeto é dimensão separada

Status: aceita
Data: 2026-06-18
Contexto: projetos pessoais precisam ser publicados, curados, patrocinados ou preparados como premium sem transformar Comunidade em dona do projeto e sem simular cobrança real.
Decisao: manter `visibility`, `publication_status`, `commercial_class` e compartilhamentos N:N como dimensões independentes em `print_projects`. A vitrine pública só lista projetos públicos aprovados. Premium exige preço preparado e revisão; patrocinado exige transparência explícita e revisão. Pagamento, repasse financeiro e fiscal ficam fora do escopo.
Alternativas consideradas: usar comunidade como aprovação pública; reaproveitar diretamente os campos comerciais da biblioteca social legada; marcar premium como público sem revisão.
Consequencias: projeto privado ou em revisão não vaza na busca pública. Compartilhar em comunidade não publica nem vende. O contrato já prepara vitrine comercial sem prometer checkout real.
Impacto em testes: `backend/tests/test_print_projects.py`, schema versionado, build frontend e `./check.sh`.
Impacto em rollback: médio; reverter remove controles e regras novas, mas valores comerciais já gravados podem permanecer no SQLite.
Como reverter: reverter `backend/sql/071_print_project_publication.sql`, alterações em `backend/app/print_projects.py`, `backend/app/routes/print_projects.py`, frontend de projetos e documentação. Se o SQL já tiver sido aplicado, restaurar backup SQLite anterior; não executar `DROP TABLE`, recriação manual de `print_projects` ou limpeza de revisões sem confirmação explícita.
### DEC-20260722-01 - Programa comunitário usa inventário atômico gerado e prioridade por impacto social

Status: aceita
Data: 2026-07-22
Vigência: superada pela `DEC-20260727-01`; o inventário permanece histórico,
sem prioridade ou cobertura obrigatória do backlog ativo.
Contexto: a base social entregue nos pacotes anteriores cobre identidade pública, comunidades derivadas do catálogo, discussões, biblioteca, descoberta, moderação, notificações, projetos e fluxo de impressão, mas ainda está longe da amplitude de uma rede comunitária e de uma infraestrutura social de fabricação digital. Colocar milhares de itens diretamente em `DEMANDAS.md` tornaria o backlog oficial impraticável e misturaria planejamento de décadas com pacotes executáveis.

Decisão: manter `DEMANDAS.md` como backlog executável e registrar o universo plurianual em `docs/community/`. O inventário parte de 55 frentes e 440 capacidades revisadas; cada capacidade gera sete itens atômicos — produto, tela, mobile, acessibilidade, confiança, impacto e qualidade — totalizando 3.080 melhorias. Telas futuras são catalogadas separando lista, detalhe e cadastro/edição. A ordem P0-P4 usa impacto social, equidade e redução de dano antes de engajamento ou receita.

Alternativas consideradas: adicionar centenas de pacotes imediatamente; manter apenas uma lista curta de ideias; copiar uma rede social específica; tratar telas e requisitos transversais como detalhe posterior.

Consequências: o projeto ganha cobertura ampla e filtrável sem fingir que tudo já está pronto para implementação. Cada entrega futura ainda precisa de descoberta, pacote pequeno, contrato, testes e validação real. O gerador torna contagens e IDs reproduzíveis, mas o conteúdo precisa de revisão periódica porque plataformas, leis e o produto mudam.

Impacto em testes: `TESTES.md` define gates por prioridade. Itens P0 exigem revisão independente, especialista e piloto controlado; todas as capacidades incluem acessibilidade, mobile, confiança, métrica de impacto e qualidade.

Impacto em rollback: baixo, pois esta decisão é documental. Reverter remove as referências e arquivos de planejamento sem alterar runtime ou banco. Não há SQL.

Como reverter: remover as chaves comunitárias de `PATHS.toml`, as referências em documentos oficiais, `docs/community/` e o gerador, preservando o backlog executável anterior.

Referências: `docs/community/MASTER_PLAN.md`, `docs/community/PLATFORM_BENCHMARK.md`, `docs/community/COMMUNITY_BACKLOG.md`, `docs/community/COMMUNITY_SCREENS.md`, `scripts/generate_community_roadmap.py`.

### DEC-20260722-02 - Evolução usa monólito modular e cutover sem legado permanente

Status: aceita
Data: 2026-07-22
Contexto: a arquitetura atual atende o estágio inicial, mas o programa
comunitário, processamento, realtime, comércio e fabricação exigem persistência
concorrente, jobs duráveis, objetos, recuperação e separação de domínios. O
servidor atual possui Nginx/systemd/Python, não oferece Docker/Node ao usuário de
deploy e hoje reinicia uma única instância Uvicorn.

Decisão: executar a evolução nos pacotes `PKG-86` a `PKG-95`, dividindo cada
risco em pacote fechável: host/blue-green; monólito modular; PostgreSQL cloud;
jobs/realtime; objetos/busca; financeiro; fabricação; escala/recuperação;
analytics/ML; consolidação. PostgreSQL será a fonte relacional cloud, Redis
conterá apenas estado recomponível, a fila durável usará PostgreSQL/outbox e os
serviços rodarão como units systemd no mesmo host. O modo local SQLite continua
suportado em adapter isolado, sem fallback ou referência no runtime cloud.

Alternativas consideradas: manter SQLite e processo único; migrar diretamente
para microsserviços; introduzir Kubernetes; exigir serviços gerenciados; manter
dual-write e adapters antigos indefinidamente.

Consequências: a transição exige releases/venvs imutáveis, expansão/contração
compatível N/N-1, sombra, canário, reconciliação, carga,
restore e observação. Em compensação, evita reescrita big-bang, dependência de
novo servidor e dívida permanente. Redundância no mesmo host cobre processo e
deploy, não falha física do servidor; backup/WAL externo é obrigatório para recuperação.

Impacto em testes: cada etapa exige arquitetura, contrato, integração, carga,
soak, falha controlada, integridade, restauração, segurança e smoke dos fluxos
P0/P1. O check passa a bloquear referências a tecnologias aposentadas.

Impacto em rollback: rollback de código reativa a instância anterior sem
restaurar snapshot velho. O destino e a ponte temporária permanecem apenas na
janela de observação; sua remoção ocorre no mesmo pacote. Banco/arquivo antigo
só é excluído após relatório reconciliado e confirmação humana explícita.

Como reverter: antes de cada cutover, manter upstream azul e origem autoritativa.
Depois do cutover, reativar release compatível e reconciliar eventos pendentes;
nunca sobrescrever escritas novas com backup anterior. Após a limpeza aprovada,
o rollback é forward-fix ou restore completo validado, não retorno ao legado.

Referência: `docs/architecture/EVOLUCAO_ARQUITETURAL.md`.

Revisão de cobertura: `docs/architecture/REVISAO_PACOTES.md`.

### DEC-20260722-03 - Monólito modular usa registry, contratos e ports canônicas

Status: aceita
Data: 2026-07-22
Contexto: routers, modelos Pydantic, repositories SQLite, aplicação e adapters
estavam organizados por arquivo, mas não possuíam owner ou fronteira executável.
Isso impedia trocar persistência e processamento sem importar detalhes internos.

Decisão: adotar cinco módulos — identidade, comunidade, operações,
administração e integrações — registrados por uma composição central ordenada.
Contratos HTTP/realtime v1 e DTOs ficam separados dos repositories; application
services dependem de Protocol ports; FastAPI traduz erros somente no adapter. O
frontend acessa HTTP/storage por clients. Inventário, ciclos, pureza de camada e
snapshots de contrato viram gates do check.

Alternativas consideradas: mover todos os arquivos de uma vez; criar
microsserviços; manter apenas convenção documental; duplicar casos de uso durante
a extração.

Consequências: a API e os eventos preservam compatibilidade N/N-1 e cada nova
tecnologia entra por adapter. Repositories SQLite grandes permanecem adapters
canônicos até o PKG-88, com divisão/remoção limite em 2026-08-31 e gate absoluto
no PKG-95. Não podem nascer facades ou bridges paralelas.

Impacto em testes: inventário modular e snapshots OpenAPI/realtime rodam em todo
`./check.sh`; testes de arquitetura bloqueiam ciclo, framework/driver em camada
pura, owner ausente e acesso HTTP/storage direto na UI.

Impacto em rollback: baixo para composição, pois os routers e contratos públicos
não mudaram. Reverter exige restaurar o registro explícito anterior e os imports,
sem alterar schema ou dados.

Como reverter: reverter os arquivos em `backend/app/modules`, o registry em
`main.py`, os snapshots/gates e o boundary de preferências no frontend como um
conjunto; não restaurar banco nem remover dados.

### DEC-20260722-04 - Cloud usa PostgreSQL dedicado sem fallback de persistência

Status: aceita
Data: 2026-07-22
Contexto: a persistência cloud em SQLite limitava concorrência, recuperação e
execução futura de workers. A migração precisava preservar toda escrita
confirmada enquanto releases N/N-1 coexistiam no mesmo host.

Decisão: tornar o cluster dedicado PostgreSQL `16/printora`, porta `5433` e
loopback, a única fonte relacional do perfil cloud. A unit recebe a URL por
arquivo root, e ausência dessa configuração bloqueia o processo. Deploy e
rollback de código reutilizam o banco atual e nunca restauram snapshot. O
adapter SQLite continua apenas no perfil local. Backup físico, dump lógico e
WAL externo são obrigatórios e o restore roda em cluster efêmero limitado.

Alternativas consideradas: manter SQLite cloud; dual-write permanente; usar o
cluster compartilhado da porta `5432`; retornar ao arquivo anterior no rollback;
contratar banco gerenciado antes de medir o host atual.

Consequências: o cloud ganha FKs, concorrência, WAL e recuperação compatíveis
com workers futuros, sem alterar o modo local. A origem anterior fica preservada
fora do runtime até aceite explícito de exclusão. O mesmo host ainda não fornece
alta disponibilidade física, e ensaios de restore precisam de limite de I/O.

Impacto em testes: reconciliação por tabela/checksum/sequence/FK, canário,
cutover, escrita pós-cutover, rollback sem restore, backup/WAL, restore isolado,
gate PostgreSQL-only e suíte local/cloud tornam-se obrigatórios.

Impacto em rollback: somente rollback de código para release PostgreSQL-compatible.
Falha física exige restore validado do backup externo. É proibido recolocar a
origem antiga em escrita depois do cutover.

Como reverter: publicar a release PostgreSQL-compatible anterior pelo blue/green
e manter o mesmo banco. Não apagar registros novos, não restaurar snapshot sobre
produção e não reativar fallback local no perfil cloud.

### DEC-20260722-05 - Execução distribuída usa PostgreSQL canônico e Redis recomponível

Status: aceita
Data: 2026-07-22
Contexto: jobs de agente, eventos entre módulos e conexões WebSocket precisam
funcionar em dois processos e em workers independentes. O registry de sockets e
a entrega imediata do processo único não fornecem durabilidade nem coordenação.

Decisão: persistir outbox, inbox, jobs, idempotência, sessões e controle de
workers no PostgreSQL. Claims usam lease token, heartbeat, expiração, retry com
backoff, prioridade e dead-letter. Redis fica restrito a cache, rate limit,
presença e pub/sub recomponíveis. O socket local é apenas um recurso efêmero da
instância; após reconnect, o agente retoma o estado canônico no banco.

Alternativas consideradas: Redis como fila canônica; broker externo no primeiro
lote; registry global somente em memória; entrega síncrona dentro do request;
microserviços antes de estabilizar contratos.

Consequências: produtores precisam gravar negócio e outbox na mesma transação;
consumidores precisam de inbox/idempotência. Workers e eventos preservam N/N-1
até drain. Redis pode ser reiniciado sem perda de negócio, ao custo de uma
recomposição breve de presença/cache.

Impacto em testes: atomicidade, duplicidade, ordenação, lease expirado, worker
morto, retry, dead-letter, Redis vazio, reconnect multi-instância, backpressure,
drain e ausência de fila autoritativa em memória são gates do fechamento.

Impacto em rollback: tabelas aditivas podem permanecer inertes. Rollback de
código drena workers e volta para uma release N-1 compatível sem restaurar banco.
Não apagar tabelas ou eventos durante rollback.

Como reverter: pausar os worker controls, drenar leases, publicar a release N-1
e manter as estruturas duráveis para forward-fix ou replay supervisionado.

Referência: `docs/audits/POSTGRESQL_CLOUD_TRANSITION_2026-07-22.md`.

### DEC-20260722-06 - Objetos cloud usam MinIO privado e chaves imutáveis

Status: aceita
Data: 2026-07-22
Contexto: uploads sociais, projetos e artefatos de fatiamento ainda usam paths
locais, enquanto o perfil cloud precisa de quarentena não servível, checksum,
ownership, versionamento, restore conjunto e URLs autorizadas sem expor o host.
O servidor atual possui um único disco e 116 GiB livres; portanto nenhum serviço
local fornece alta disponibilidade física e a cópia externa continua obrigatória.

Decisão: executar MinIO Community `RELEASE.2025-10-15T17-29-55Z`, código-fonte
oficial fixado no commit `9e49d5e7a648f00e26f2246f4dc28e6b07f8c84a`,
como unit systemd privada em `127.0.0.1:9100`. O binário é compilado do código
AGPLv3 sem modificação. Buckets privados separam quarentena, objetos promovidos e
artefatos; versionamento e quotas ficam ativos. A aplicação recebe uma chave de
escopo mínimo, usa chaves content-addressed imutáveis e mantém PostgreSQL como
fonte de ownership, estado, checksum e referências. Downloads passam por token
curto da aplicação; o endpoint S3 nunca é publicado.

Alternativas consideradas: Garage, rejeitado porque não implementa bucket
versioning; filesystem local, rejeitado por manter path autoritativo; Ceph,
rejeitado pelo custo operacional no host único; serviço gerenciado, fora da
restrição atual de executar os componentes do Printora no servidor existente.

Consequências: a aplicação deixa de depender de paths e pode reconstruir busca e
reconciliar conteúdo. Single-node não protege contra perda física do host; backup
externo criptografado e restore de metadados mais objetos são gates. A licença e
o source pin do MinIO devem permanecer inventariados em cada atualização.

Impacto em testes: streaming interrompido, limite, conteúdo hostil, quarentena,
promoção, checksum, ownership, token expirado, órfãos, versionamento, backup,
restore, carga e falha do serviço são obrigatórios.

Impacto em rollback: código N-1 continua lendo a origem preservada somente antes
do cutover. Depois do cutover, rollback reutiliza PostgreSQL e MinIO atuais; não
restaura snapshot antigo nem apaga versões. A origem local permanece read-only
até reconciliação e confirmação explícita para remoção.

Como reverter: pausar promoções, drenar jobs de storage, publicar a release N-1
S3-compatible e manter buckets/metadados intactos. Falha física exige restore
integral validado, nunca retorno silencioso a paths locais.

### DEC-20260722-07 - Busca cloud usa FTS PostgreSQL reconstruível por outbox

Status: aceita
Data: 2026-07-22
Contexto: a busca cloud reconstruía uma tabela SQLite por assinatura durante o
request e consultava texto com `LIKE`. Esse fluxo não escala, pode ficar obsoleto
entre processos e não reaplica todas as permissões no momento da leitura.

Decisão: materializar documentos no PostgreSQL com `tsvector` gerado, índice GIN
e ranking `ts_rank_cd`. Triggers estreitos nas fontes emitem somente um evento
sanitizado na outbox; o dispatcher cria job durável de rebuild. Rebuild desativa
a geração anterior e faz upsert da geração atual, sem apagar fonte ou índice. A
consulta reaplica estado canônico, visibilidade, membership, bloqueio, moderação
e revisão comercial. O modo local preserva sua materialização SQLite.

Alternativas consideradas: Elasticsearch/OpenSearch no mesmo host; rebuild em
todo request; cron sem outbox; consulta `LIKE` permanente; índice como fonte de
autorização.

Consequências: busca deixa de estar no caminho de escrita e pode ser reconstruída
após restore. Eventos repetidos geram trabalho idempotente, não autoridade nova.
Documentos inativos permanecem temporariamente para auditoria/rollback e nunca
aparecem porque `is_active=false` e os filtros canônicos continuam obrigatórios.

Impacto em testes: ranking, acento/termo, outbox repetida, rebuild vazio,
remoção/moderação, membership, bloqueio, relevância e carga passam a ser gates.

Impacto em rollback: a tabela e os triggers podem permanecer inertes. Publicar
release anterior não restaura nem apaga fonte; reativação exige novo rebuild.

Como reverter: pausar jobs `search.rebuild`, publicar a release anterior e manter
`search_documents`/outbox para diagnóstico. Não remover eventos ou documentos.

### DEC-20260722-08 - Finanças usam módulo isolado e ledger imutável

Status: aceita
Data: 2026-07-22
Contexto: preço preparado em projetos não constitui pedido, pagamento, saldo ou
receita. O domínio comercial precisa tolerar duplicidade, timeout e reconciliação
sem derivar dinheiro de conteúdo mutável ou receber dados brutos de cartão.

Decisão: criar a fronteira `finance` dentro do monólito modular. Dinheiro usa
unidade mínima inteira e moeda ISO explícita. Toda alteração de saldo nasce de
uma transação de partidas dobradas, criada como rascunho, validada e então
postada; banco e aplicação exigem débitos iguais a créditos. Transação postada e
lançamentos são imutáveis. Correção ocorre por transação compensatória, nunca
por edição ou exclusão. Pagamento real permanece bloqueado; checkout deve ser
hospedado/tokenizado pelo adapter do provedor.

Alternativas consideradas: saldo mutável em uma coluna; cálculo de receita a
partir do preço atual do projeto; `float`; edição administrativa do ledger;
microserviço financeiro antes de estabilizar contratos.

Consequências: pedido deve carregar snapshot imutável e operações financeiras
precisam de chave idempotente, correlation id, reconciliação e segregação de
função. O módulo social não importa a infraestrutura financeira.

Impacto em testes: invariantes do ledger, concorrência, replay, estados fora de
ordem, reconciliação, compensação, permissões e ausência de PAN/CVV são gates.

Impacto em rollback: tabelas aditivas e postings permanecem para auditoria. Uma
release anterior pode ignorar o módulo, mas não deve alterar ou apagar o ledger.

Como reverter: bloquear novos comandos financeiros, publicar a release anterior
e preservar integralmente contas, transações e lançamentos para forward-fix.

### DEC-20260723-01 - Redundância de processo usa duas instâncias da mesma release

Status: aceita
Data: 2026-07-23
Contexto: blue/green fornecia cutover seguro, mas o upstream atendia por uma
instância primária e mantinha a outra somente como backup de release. A perda do
processo ativo ainda criava uma janela de failover e não exercitava estado
compartilhado entre processos.

Decisão: cada release ativa atende simultaneamente pelo slot blue ou green e por
uma instância `replica` em `8071`. As duas apontam para a mesma release imutável,
PostgreSQL canônico, objetos S3 e Redis recomponível. O slot oposto continua na
release N-1, fora do upstream, como rollback aquecido. Deploy e rollback só
recarregam o Nginx depois que as duas instâncias da release-alvo estão ready.

Alternativas consideradas: continuar com upstream primário/backup; executar as
duas releases diferentes no mesmo upstream; adicionar outro host sem orçamento
e operação autorizados; usar sessão ou fila em memória local.

Consequências: morte de um processo não interrompe requests novos. Sessão,
idempotência, outbox e jobs permanecem no PostgreSQL; presença/cache/pubsub podem
ser recompostos. O mesmo host, disco, Nginx e banco continuam pontos físicos
únicos, portanto isso é redundância de processo e não alta disponibilidade.

Impacto em testes: deploy, rollback, balanceamento, caos de processo, jobs com
lease, backpressure, soak, capacidade e restore externo passam a ser gates.

Impacto em rollback: antes da troca, a réplica retorna atomicamente à release
anterior; falha de readiness preserva o upstream corrente. Banco, objetos e WAL
nunca são restaurados durante rollback de código.

Como reverter: executar `printora-cloud-rollback`, confirmar os dois processos
da release N-1 e manter a release atual como standby. Não alterar dados nem
substituir o upstream manualmente.

### DEC-20260723-02 - Inteligência consome eventos sanitizados sob role restrita

Status: aceita
Data: 2026-07-23
Contexto: analytics, moderação e recomendação precisam evoluir sem transformar
o OLTP em warehouse, ampliar permissões do runtime ou tornar login, impressão,
pedido e segurança dependentes de modelo.

Decisão: eventos analíticos possuem finalidade, versão, digest, pseudônimo e
retenção. O consumidor dedicado executa `SET LOCAL ROLE printora_analytics`; a
role não lê nem escreve tabelas transacionais e acessa somente derivados
`analytics_*`. Contexto de moderação é transitório e vira digest após
classificação. Decisões automatizadas usam baselines determinísticos internos,
registro de owner/dataset/licença/métrica/bias, canário, drift, rollback lógico
e kill switch. Alto impacto nunca aplica ação no conteúdo: exige revisão humana
e permite recurso.

Alternativas consideradas: consultas analíticas diretas no OLTP; credencial com
permissão global; modelo externo sem licença aprovada; moderação automática;
cluster/warehouse adicional antes de existir capacidade e operação justificadas.

Consequências: o primeiro baseline não promete qualidade de um modelo treinado
externamente. Seu valor é isolamento, contrato, auditabilidade e fallback. O
worker possui cgroup próprio e falha sem bloquear P0/P1. Retenção começa com
preview não destrutivo; limpeza real exige confirmação operacional separada.

Impacto em testes: role, sanitização, replay, lineage, anonimização, idiomas,
revisão/recurso, registry, canário/drift, kill switch, quota, carga e readiness
simultânea são gates.

Impacto em rollback: release anterior ignora tabelas aditivas; o helper para o
worker de inteligência o interrompe quando a release N-1 não é compatível.
Eventos e derivados são preservados para forward-fix.

Como reverter: ativar kill switch, interromper somente
`printora-cloud-intelligence.service`, publicar a release anterior e preservar
as tabelas `analytics_*`. Não conceder acesso ao OLTP nem excluir derivados.

### DEC-20260723-03 - Encerramento mantém um runtime cloud e um perfil local explícito

Status: aceita
Data: 2026-07-23
Contexto: o fechamento arquitetural precisava eliminar mecanismos transitórios
sem confundir o adapter SQLite local suportado, transições de domínio ou bridge
USB-CAN física com legado cloud.

Decisão: declarar PostgreSQL, storage S3 compatível, Redis recomponível, filas
duráveis e releases blue/green como topologia cloud única. SQLite e
`printora.service` permanecem somente no perfil local/dispositivo. Um scanner
integrado ao gate bloqueia arquivos e flags da transição, exige owner/ciclo de
vida das units e executa uma importação cloud que falha se `sqlite3` entrar em
`sys.modules`. O status interno do banco passa a se chamar `database_runtime`,
sem contrato transitório.

Alternativas consideradas: remover SQLite e quebrar instalações locais; aceitar
uma allowlist ampla de termos; manter o contrato antigo indefinidamente; fazer
limpeza física junto do scanner.

Consequências: o runtime cloud fica verificável sem falso positivo sobre
hardware ou regras de negócio. Arquivos grandes históricos ficam registrados
como dívida incremental e não podem crescer com capacidades novas. Limpeza de
dado, tabela, objeto, backup ou release continua fora do scanner e exige
confirmação específica.

Impacto em testes: scanner final, perfil de importação, snapshots de contrato,
gate estrito, dependências, SBOM, auditoria remota, restore, rollback, soak e
smoke público são evidências de encerramento.

Impacto em rollback: baixo para o scanner e a documentação. Uma release N-1
pode ainda expor `database_transition`, mas não recebe tráfego junto da nova
release. Dados e adapters locais não são alterados.

Como reverter: publicar a release N-1 por blue/green e preservar o manifesto
para diagnóstico. Não reintroduzir dual-read, dual-write ou fallback SQLite no
perfil cloud.

### DEC-20260723-04 - Confiança pós-arquitetura usa quatro pacotes e sete gates

Status: aceita
Data: 2026-07-23
Contexto: os pacotes 86 a 95 fecharam a arquitetura base, mas o aceite mostrou
limites que não devem ser confundidos com defeitos inexistentes: Node local não
suportado gerava apenas warning, cobertura mínima estava desativada, não havia
E2E amplo em navegador, a homologação final excluía hardware real, o soak era
curto, fuzz/mutation não eram gates e não havia pentest independente. O código
do agente também mudou depois do binário público `0.1.33` sem nova versão.

Decisão: registrar `PKG-96` a `PKG-99`. O primeiro publica agente `0.1.34`
imutável; o segundo fecha Node, cobertura, E2E, fuzz, mutation e pentest; o
terceiro homologa hardware real e soak contínuo de 72 horas; o quarto reduz o
RPO físico e repete recuperação de desastre. Limite de linhas permanece
aplicável a runtime, não a `DEMANDAS.md`.

Alternativas consideradas: reabrir os pacotes arquiteturais concluídos; chamar
os limites de bugs isolados; declarar ausência de defeitos; criar um único
pacote grande sem commits/aceites independentes.

Consequências: o roadmap funcional pode continuar, mas fluxos que dependem do
novo agente, dinheiro real, fabricação real ou promessa de recuperação precisam
respeitar os gates correspondentes. Pentest externo, soak e homologação física
possuem custo e dependências operacionais explícitas.

Impacto em testes: sete gates obrigatórios — Node, cobertura, E2E, hardware real,
soak, fuzz/mutation e pentest — além de RPO/RTO contínuos.

Impacto em rollback: cada pacote mantém rollback próprio. Agente volta para
N-1; gates só podem ser temporariamente revertidos por defeito comprovado do
gate; web usa blue/green sem restore; recuperação preserva WAL/snapshots.

Como reverter: remover apenas o planejamento se ainda não iniciado. Depois de
implementado, reverter por pacote sem reduzir silenciosamente cobertura,
segurança, versão ou proteção de dados.

### DEC-20260723-05 - Release do agente usa Ed25519, candidato separado e journal durável

Status: aceita
Data: 2026-07-23
Contexto: SHA-256 sem assinatura não protege a origem do artefato, um manifesto
com URL/hash vazio anuncia suporte inexistente e redelivery após ACK poderia
repetir efeito mutável quando a resposta final falhasse.

Decisão: suportar somente `linux/arm64` até outra plataforma possuir artefato
testado; fixar a chave pública Ed25519 e seu fingerprint no agente; manter a
chave privada fora do Git; publicar versão candidata separada da recomendada; e
persistir recebimento antes do ACK, início antes do efeito e resultado antes da
resposta ao cloud em journal local sincronizado. Job terminal é apenas
reenviado. Job mutável interrompido depois do ACK exige reconciliação e não é
repetido automaticamente. Update do agente exige estado ocioso confirmado pelo
Moonraker e falha fechado se esse estado estiver indisponível.

Alternativas consideradas: manter apenas SHA-256; carregar chave pública do
mesmo manifesto; substituir o binário sob URL genérica; promover o candidato
diretamente; confiar apenas na deduplicação em memória.

Consequências: a primeira adoção exige endpoint candidato autenticado e canário
operacional. Como o agente N-1 não entende seleção de canal, candidato e rollback
são jobs web controlados com versão exata, preflight Moonraker, SHA-256, Ed25519,
backup e restart exclusivo do serviço; não exigem SSH. O journal guarda no
máximo 200 entradas, modo `0600`, e pode conter somente resultados já
sanitizados pelo agente.

Impacto em testes: build duplo, verificação criptográfica, rejeição de hash/chave
e assinatura, seleção recomendada/candidata, persistência pré-ACK, replay
terminal, interrupção mutável e bloqueio de update durante impressão ou estado
indisponível são gates.

Impacto em rollback: o N-1 permanece versionado e o host preserva backup local.
Rollback troca somente `printora-agent`; banco, Redis, storage, Klipper,
Moonraker, MCU e host não são restaurados ou reiniciados.

Como reverter: voltar ao binário N-1 e manifesto anterior, mantendo os artefatos
e journal para diagnóstico. Não reutilizar `0.1.34` com outro conteúdo.

### DEC-20260723-06 - Cobertura usa baseline real e não regressão por stack

Status: aceita
Data: 2026-07-23
Contexto: Python e Go já possuíam testes relevantes, mas cobertura não era gate.
O frontend possuía verificações por leitura de fonte e poucos testes executáveis;
excluir telas e hooks elevaria artificialmente o percentual.

Decisão: medir todo código executável por stack, excluir somente declarações e
tipos sem runtime, versionar o baseline real e bloquear qualquer regressão.
Python, Go e frontend possuem mínimos globais e recortes críticos superiores. O
frontend inicia com cobertura global baixa explicitamente visível e com 91,36%
nas fronteiras P0 de HTTP, preview G-code e polling.

Alternativas consideradas: exigir percentual alto fictício excluindo código sem
teste; ativar apenas cobertura crítica; manter cobertura informativa; reduzir o
baseline quando código novo não tiver teste.

Consequências: código novo precisa preservar ou elevar o percentual global. A
dívida frontend permanece mensurável e deve cair por testes reais, E2E e lotes
futuros, sem afrouxar o gate. Relatórios CI são retidos por 30 dias.

Impacto em testes: `scripts/run-coverage-gate.sh` executa as três stacks, valida
os mínimos de `PATHS.toml` e compara com `quality/coverage-baseline.json`.

Impacto em rollback: o gate pode ser revertido somente por defeito comprovado do
próprio mecanismo, com incidente e prazo de restauração. Relatórios e baseline
permanecem preservados.

Como reverter: restaurar temporariamente o workflow anterior, sem alterar o
baseline, e corrigir o coletor antes de reativar o gate.

### DEC-20260723-07 - E2E isolado e mutation usam gate mensurável com dívida explícita

Status: aceita
Data: 2026-07-23
Contexto: testes de componente não provavam ordem real de routers, build
frontend servido pelo backend, responsividade ou recuperação de rede. Mutation
testing inicial também mostrou muitos mutantes equivalentes ou sem asserção
específica; exigir score arbitrariamente alto agora incentivaria filtros.

Decisão: executar Playwright em Chromium real contra banco temporário e frontend
recém-compilado, sem retry, em desktop/tema escuro e mobile/tema claro. O gate
mutation atua em identidade, idempotência, pagamento sandbox e validação
comunitária, mede mortos sobre mortos+sobreviventes e inicia em 60%. A enumeração
completa de sobreviventes é artefato obrigatório. O baseline de 197
sobreviventes fica no backlog por domínio: Plataforma/idempotência (79, owner
Plataforma, prazo PKG-100), Pagamentos (54, owner Finanças, prazo PKG-100),
Identidade (37, owner Segurança, prazo PKG-100) e Comunidade/validação (27, owner
Comunidade, prazo PKG-100). Cada lote deve matar mutantes relevantes ou registrar
justificativa antes de elevar, nunca reduzir, o limiar.

Alternativas consideradas: E2E contra backend já aberto pelo desenvolvedor;
retry automático; dados compartilhados entre repetições; mutation apenas
informativo; excluir sobreviventes até atingir percentual alto.

Consequências: o CI instala Chromium e fica mais lento, mas reproduz a aplicação
integrada. A dívida mutation permanece visível e cada sobrevivente continua
enumerado em `survivors.txt`; os quatro grupos cobrem todos os 197 identificados
na execução de 2026-07-23. Pentest independente continua obrigatório e não pode
ser substituído por E2E/fuzz/mutation.

Impacto em testes: `scripts/run-pkg97-test-gates.sh` executa E2E,
property/fuzz e mutation; cobertura continua em gate próprio. Flakiness usa dez
repetições sem retry, e mutation falha abaixo de 60%.

Impacto em rollback: um gate pode ser revertido apenas por defeito comprovado,
com incidente e prazo. Não reduzir limiar, esconder mutantes ou reutilizar banco
de teste contaminado para liberar deploy.

Como reverter: restaurar temporariamente o comando anterior do CI, preservar
artefatos/corpus/seed e corrigir o gate antes de reativá-lo.

### DEC-20260723-08 - Administração de plataforma usa política configurável única

Status: aceita
Data: 2026-07-23
Contexto: nove fronteiras administrativas comparavam diretamente um email
pessoal no código. Isso duplicava autorização, impedia conta administrativa
sintética no ambiente de pentest e tornava uma troca operacional dependente de
alteração e deploy de código.

Decisão: centralizar a verificação em `platform_access.is_platform_admin` e
configurar uma lista normalizada por `PRINTORA_PLATFORM_ADMIN_EMAILS`. A
configuração vazia nega todos; item sintaticamente inválido falha fechado. O
valor legado permanece como default de compatibilidade até a operação definir a
variável fora do release. O handoff de pentest deve usar somente domínio
`example.test`.

Contas presentes nessa lista não podem usar o cadastro público. Elas devem ser
provisionadas diretamente no ambiente por ferramenta operacional autenticada,
antes da abertura da janela, para impedir que terceiros reivindiquem a
identidade administrativa.

Alternativas consideradas: manter comparações por rota; criar papéis diferentes
sem consolidar a política existente; persistir administradores em nova tabela.

Consequências: catálogo, moderação, segurança social, busca, dados,
trabalhadores, fabricação, finanças e suporte interno consultam a mesma
política. O contrato autenticado expõe o booleano `platform_admin` para a UI,
que não mantém lista ou comparação de email. A mudança não cria tabela, migração
ou log persistido. Alterar a lista continua sendo ação privilegiada de
configuração e exige restart controlado.

Impacto em testes: configuração customizada, normalização, deny-all, entrada
inválida, bloqueio do cadastro público e ausência de identidade embutida no
runtime são regressões obrigatórias.

Impacto em rollback: restaurar temporariamente o default anterior na variável
de ambiente; não reintroduzir comparações distribuídas nas rotas.

Como reverter: remover a variável do ambiente para usar o default compatível e
reimplantar, preservando a política central.

### DEC-20260723-09 - Handoff de pentest é sintético, sanitizado e bloqueado em produção

Status: aceita
Data: 2026-07-23
Contexto: o fornecedor independente precisa receber contas, tenants e papéis
reproduzíveis sem usar identidade, dado, segredo, pagamento ou impressora real.
Preparação manual não garante segregação, rastreabilidade ou ausência de token
no material entregue.

Decisão: preparar o ambiente por aplicação idempotente sobre contratos HTTP
reais, com sete contas `example.test`, duas organizações, financeiro sandbox e
papéis separados de suporte/finanças/produção. Target produtivo é sempre
proibido. Target externo exige arquivo de autorização vigente, com referência
ao documento assinado; o manifesto registra seu SHA-256 e exclui senha/sessão.

Consequências: o seed valida permissões reais e produz evidência reproduzível,
mas não executa pentest e não substitui assinatura independente. O arquivo de
senha exige `0600`; manifesto existente não é sobrescrito. Não há tabela, SQL,
migração, dado produtivo ou observabilidade persistida nova.

Como reverter: descartar exclusivamente o ambiente isolado conforme autorização
e retenção acordadas; preservar o manifesto sanitizado e o relatório assinado.

### DEC-20260723-10 - Owner dispensa pentest externo e aceita risco residual

Status: aceita
Data: 2026-07-23
Contexto: o PKG-97 previa pentest independente como gate de fechamento. O owner
determinou explicitamente que essa dependência externa fosse removida do ciclo e
que a continuidade usasse somente os testes internos já implementados.

Decisão: dispensar o lote de execução do pentest para o fechamento do PKG-97.
Preservar o escopo preparado para uso futuro, registrar como não testadas as
fronteiras que exigiriam avaliação independente e não classificar E2E, fuzz,
mutation, scans ou revisão interna como pentest ou prova equivalente.

Alternativas consideradas: manter o pacote bloqueado; autoatestar um pentest;
executar teste ativo em produção sem fornecedor e regras assinadas.

Consequências: PKG-98 e PKG-99 podem avançar, mas permanece risco residual de
falhas exploráveis não identificadas por revisão interna em web, API, realtime,
sessões, autorização, uploads, SSRF, rate limit, multi-tenant, financeiro
sandbox e supply chain. Uma avaliação independente futura continua recomendada,
sem bloquear este ciclo.

Impacto em testes: todos os gates internos, repetição sem retry, scans,
dependências, SBOM, smoke e validações operacionais continuam obrigatórios. O
relatório final deve listar explicitamente o pentest como não executado.

Impacto em rollback: a dispensa pode ser revogada a qualquer momento, reabrindo
o escopo preservado sem desfazer os gates internos ou a evidência existente.

Como reverter: contratar avaliador independente, aprovar o escopo e executar o
handoff sanitizado em ambiente isolado antes de tratar os achados.

### DEC-20260723-11 - Leituras concorrentes do agente usam coalescência por escopo

Status: aceita
Data: 2026-07-23
Contexto: a homologação real do PKG-98 encontrou reconnect do WebSocket durante
uma leitura operacional longa da Voron 2.4. Pollings simultâneos continuavam
criando jobs equivalentes, elevaram a fila acima do SLO e atrasaram ainda mais a
resposta, embora o agente e a impressão permanecessem ativos.

Decisão: jobs read-only de alta frequência reutilizam um job `pending` ou
`in_progress` quando impressora, agente, tipo e payload são idênticos. A decisão
é atômica em PostgreSQL por advisory lock transacional derivado de SHA-256 do
escopo. Jobs mutáveis continuam criando registros independentes e nunca são
coalescidos. A renovação implícita pelo heartbeat foi substituída pela
`DEC-20260723-13`; progresso exige resultado do job. Não há nova tabela, script
SQL ou retenção.

Alternativas consideradas: aumentar o limite do soak; cancelar jobs existentes;
reduzir polling somente na UI; desativar WebSocket; reiniciar o agente durante a
impressão.

Consequências: pollings concorrentes aguardam o mesmo resultado e deixam de
amplificar backlog durante reconnect. O correlation ID original permanece como
identidade do job compartilhado; chamadas posteriores a uma conclusão criam
nova leitura. Falha ou expiração continua fail-closed para todos os aguardantes.

Impacto em testes: aplicação valida a política read-only versus mutação, e o
repositório valida reuso apenas no mesmo payload/escopo.

Impacto em rollback: baixo; reverter a política volta a criar um job por
request, sem alterar schema ou registros existentes.

Como reverter: reverter o serviço/repositório de jobs e monitorar backlog antes
de reabrir polling real.

### DEC-20260723-12 - Expiração de jobs usa instante UTC tipado no PostgreSQL

Status: aceita
Data: 2026-07-23
Contexto: a aceitação real da coalescência encontrou jobs `pending` antigos que
não expiravam. `expires_at` é texto UTC sem offset por compatibilidade com
SQLite, enquanto `CURRENT_TIMESTAMP` no PostgreSQL era convertido em texto no
fuso da sessão. A comparação lexicográfica adiava o vencimento em três horas.

Decisão: no repositório de jobs, PostgreSQL interpreta `expires_at` explicitamente
como timestamp UTC e `updated_at` como instante com offset antes de comparar com
`NOW()`. SQLite preserva a comparação textual UTC existente. A política fica
local ao contrato de jobs e não altera schema, dados ou o adaptador compartilhado.

Consequências: pending vencido falha no próximo acesso normal, in-progress órfão
falha após cinco minutos e jobs ativos continuam elegíveis sem depender do fuso
do processo ou da sessão. Registros existentes são reconciliados sem exclusão.

Impacto em testes: regressões cobrem expiração antes da coalescência e as
expressões PostgreSQL tipadas.

Impacto em rollback: reverter restaura a comparação textual anterior e pode
voltar a atrasar expiração conforme o fuso da sessão.

Como reverter: reverter a decisão e o repositório sem alterar ou remover jobs.

### DEC-20260723-13 - Heartbeat não é lease de execução de job

Status: aceita
Data: 2026-07-23
Contexto: após a correção de expiração UTC, a fila real caiu para cinco jobs,
mas um `remote_gcode_files_list` com mais de duas horas continuava
`in_progress`. O agente seguia vivo e seu heartbeat renovava esse registro,
embora não houvesse resultado nem evidência de progresso.

Decisão: heartbeat atualiza somente liveness, versão, plataforma e capacidades
do agente. Ele não renova `updated_at` de job. Todo `in_progress` sem
`result`/`error` expira após cinco minutos, independentemente de o processo do
agente continuar online. Reconciliação específica do updater por versão
permanece independente.

Alternativas consideradas: manter renovação do job mais antigo; elevar o
timeout; cancelar manualmente a fila; exigir imediatamente um novo protocolo de
lease.

Consequências: executor travado deixa de bloquear indefinidamente jobs
posteriores e a fila se recupera sem exclusão manual. Trabalho que realmente
precise durar mais de cinco minutos deverá adotar lease explícito e vinculado ao
job em uma evolução de protocolo; heartbeat genérico não será usado como prova.

Impacto em testes: heartbeat com dois jobs mutáveis em progresso deve preservar
os dois timestamps, permitindo que a expiração normal trate ambos.

Impacto em rollback: reintroduzir a renovação pode recriar starvation e backlog
sem limite quando o executor travar.

Como reverter: somente após implementar lease explícito por job com deadline,
fencing e teste de executor interrompido.

### DEC-20260723-14 - Soak representativo reutiliza conexões HTTP

Status: aceita
Data: 2026-07-23
Contexto: a primeira janela de 24 horas encerrou após cinco minutos porque um
lote público mediu p95 de 1.844 ms e p99 de 2.779 ms. Os slots locais
permaneceram abaixo de 50 ms e não houve erro, backlog, restart ou serviço
inativo. O gerador abria uma conexão DNS/TCP/TLS nova para cada requisição,
divergindo do comportamento de browser e agente com keep-alive. A segunda
janela revelou que o cliente compartilhado ainda era encerrado e recriado a
cada lote de 100 requisições; no 19º lote, p95 de 2.002 ms e p99 de 2.603 ms
confirmaram que reutilização apenas dentro do lote não representa uma sessão
contínua.

Decisão: a carga representativa de 24/72 horas usa um `httpx.Client`
compartilhado por toda a janela, pool limitado pela concorrência e keep-alive.
O processo de carga permanece vivo entre lotes e transmite cada relatório ao
observador fail-closed. O modo de conexão fria permanece explícito para
diagnóstico separado de DNS/TCP/TLS. O SLO, taxa, lote, concorrência e endpoint
público não são relaxados.

Alternativas consideradas: elevar p95/p99; medir somente os slots locais;
ignorar lotes isolados; manter conexões frias como modelo único.

Consequências: o soak mede a latência do fluxo HTTP real sob conexões
reutilizadas sem transformar handshake em cinco novas conexões por segundo ou
recriar todo o pool a cada 20 segundos. Cold start continua verificável, mas não
é somado à janela representativa.

Impacto em testes: pacing e burst permanecem cobertos; cliente compartilhado
entre múltiplos lotes, erro `httpx`, modo padrão, streaming e smoke integrado
são validados.

Impacto em rollback: reverter restaura uma conexão por requisição e pode
reintroduzir variância de handshake que invalida a janela sem degradação dos
slots.

Como reverter: reverter o gerador e reiniciar integralmente qualquer janela
iniciada com o modelo anterior.

### DEC-20260724-15 - I/O síncrono de jobs não bloqueia o event loop

Status: aceita
Data: 2026-07-24
Contexto: a janela inicial de 24 horas do PKG-98 encerrou após 3.320 segundos
com cinco timeouts e violação de p95/p99. Os dois slots degradaram
simultaneamente em diversas rotas, embora agentes, backlog, PostgreSQL, kernel
e serviços permanecessem saudáveis. A autenticação e cada etapa do polling de
jobs executavam acesso PostgreSQL síncrono diretamente no event loop único.

Decisão: lookup de sessão e operações síncronas do repositório de jobs são
executados no executor de I/O do processo. O fluxo assíncrono continua
responsável por timeout, backoff, coalescência e resposta; schema, protocolo do
agente, número de workers, SLO e timeout público não mudam.

Alternativas consideradas: relaxar p95/p99; aumentar o timeout do gerador;
somar o período inválido; adicionar workers para mascarar o bloqueio; converter
todo o acesso a banco para assíncrono no mesmo incidente.

Consequências: uma consulta ou conexão síncrona deixa de bloquear health,
WebSocket e demais coroutines do slot. O executor padrão limita a concorrência
de threads; saturação ainda produz backpressure sem criar processos ou
conexões sem limite. A migração integral para acesso assíncrono continua sendo
uma evolução possível, não requisito desta correção localizada.

Impacto em testes: teste controlado bloqueia o repositório e exige que o event
loop continue avançando. Autenticação, coalescência, expiração e falhas de jobs
continuam cobertas pelas suítes existentes.

Impacto em rollback: reverter apenas a delegação ao executor restaura o risco
de bloqueio de cabeça de fila; não há alteração de dados, schema ou agente.

Como reverter: reverter a implementação e invalidar qualquer soak iniciado com
a versão revertida antes de reavaliar capacidade.

### DEC-20260724-18 - PKG-98 fecha com dispensa explícita do soak prolongado

Status: aceita com risco residual
Data: 2026-07-24
Contexto: o PKG-98 acumulou probes reais, curtos observados, incidentes
fail-closed e correções publicadas, mas não completou uma janela contínua válida
de 24 horas nem o alvo de 72 horas. No momento do fechamento, as duas
impressoras estavam desligadas e o owner priorizou explicitamente a continuidade
do roadmap.

Decisão: encerrar o PKG-98 sem exigir novas janelas de 24/72 horas. Tentativas
interrompidas permanecem inválidas e não são somadas. Cenários físicos não
exercitados são registrados como escopo não testado, e os testes curtos não são
tratados como equivalentes ao soak.

Consequências: o PKG-99 pode iniciar, mas permanece risco residual de leak,
degradação lenta, backlog tardio e regressões nos estados físicos não
exercitados. A decisão diverge do gate de soak contínuo de `GOVERNANCA.md` e
deve ser revista se esses sinais aparecerem em produção.

Controles compensatórios: observadores fail-closed e SLOs permanecem
versionados; toda cronologia é preservada; a release final passou pelo gate
completo, blue/green e smoke público de 120 segundos; N-1 permanece disponível
para rollback; nenhum comando físico foi executado com as máquinas desligadas.

Como reverter a decisão: reabrir o PKG-98, ligar as duas máquinas em janela
segura, repetir probes e curtos observados e executar novas janelas contínuas
integrais, sem reaproveitar períodos anteriores.

### DEC-20260724-19 - Recuperação física usa WAL externo contínuo e gate fail-closed

Status: aceita
Data: 2026-07-24
Contexto: o snapshot externo diário já restaurava PostgreSQL, objetos e
configuração em destino isolado, mas o pior caso de destruição física do host
permanecia em até 24 h 15 min. O rollback blue/green preservava RPO zero de
deploy, sem resolver perda do servidor.

Decisão: forçar troca de WAL em até 120 segundos, sincronizar o arquivo completo
para o repositório Restic externo a cada 60 segundos e limitar cada execução a
110 segundos. O pior caso configurado fica em 290 segundos. Um monitor
fail-closed executa a cada minuto e alerta a partir de 210 segundos sem
verificação válida. Backup completo permanece diário; restore isolado passa a
ser semanal, limitado a 900 segundos e inclui o WAL contínuo.

O alerta sempre grava evento crítico sanitizado com owner `operations`. Webhook
é opcional e configurado fora do Git; falha do webhook não apaga o alerta local.
Retenção de snapshots completos e WAL possui apenas preview. Nenhum `forget`
efetivo, prune, snapshot, objeto ou WAL é removido sem confirmação explícita
separada.

Consequências: PostgreSQL obtém RPO físico configurado inferior a cinco minutos
e RTO alvo de quinze minutos no volume atual. Objetos/configuração permanecem
na classe diária e Redis/busca continuam recomponíveis a partir das fontes
canônicas. A quantidade de snapshots WAL, bytes locais, duração, atraso e espaço
livre entram no monitoramento. O host único continua sem promessa de alta
disponibilidade.

Controles: units com quotas de CPU/I/O/memória/tarefas; `TimeoutStartSec` efetivo
para oneshot; replay de WAL, schema, revisões, FKs, checksums, objetos e busca no
restore; preflight e auditoria falham com proteção vencida; configuração
PostgreSQL permanece `root:postgres` e não gravável pelo processo do banco.

Rollback: se a frequência degradar produção, preservar integralmente todo WAL e
snapshot, diagnosticar duração/capacidade e restaurar a frequência anterior
somente com proteção equivalente autorizada. Nunca usar restore para rollback de
código nem resolver capacidade com prune não aprovado.

### DEC-20260724-17 - Espera de job coalescido usa um único poller por processo

Status: aceita
Data: 2026-07-24
Contexto: os gates reais do PKG-98 mostraram que várias abas podiam reutilizar
o mesmo job read-only e ainda manter um loop de polling PostgreSQL por request.
Com dezenas de aguardantes do mesmo job, o executor de I/O saturava e degradava
até o `/health`, embora o backlog do agente permanecesse dentro do limite.

Decisão: chamadas do mesmo processo que aguardam o mesmo banco, impressora, job
e timeout compartilham uma única task de polling. Cada consumidor aguarda a
task protegida contra cancelamento individual; resultado, timeout e falha
continuam iguais para todos. Instâncias distintas continuam coordenadas pelo
job persistido e pela coalescência PostgreSQL existente.

Alternativas consideradas: relaxar o SLO; aumentar workers; reaproveitar
resultado concluído por TTL; reduzir apenas o polling da UI; cancelar jobs.

Consequências: o número de consultas de acompanhamento passa a depender dos
jobs ativos por processo, não da quantidade de abas ou rotas aguardando o mesmo
resultado. Não há cache de resultado, mudança de schema, alteração do agente ou
interferência em jobs mutáveis.

Impacto em testes: regressão concorrente exige duas instâncias do serviço
aguardando o mesmo job com uma única leitura de acompanhamento.

Impacto em rollback: baixo; reverter o coordenador restaura um poller por
request e exige invalidar qualquer soak iniciado com a versão revertida.

Como reverter: reverter o coordenador e sua regressão, publicar novamente e
repetir do zero os gates de latência e soak.

### DEC-20260724-16 - Upload G-code passa por staging efêmero e streaming

Status: aceita
Data: 2026-07-24
Contexto: o gerenciador precisa receber arquivos grandes no navegador e
entregá-los a um Moonraker que não é acessível diretamente pela cloud.

Decisão: a cloud grava o corpo em arquivo temporário limitado a 96 MB, registra
somente chave aleatória, nome, tamanho e SHA-256 e entrega essa chave ao agente.
O agente baixa uma única vez e transmite multipart por streaming ao Moonraker.
Após a resposta do download, dados e metadados temporários são removidos. O
conteúdo não entra no banco, job, log ou resposta.

Consequências: o fluxo suporta progresso e arquivos grandes sem ampliar o
payload do protocolo ou a memória do agente. Sobrescrita e upload com impressão
exigem confirmação textual e autenticação reforçada; upload simples continua
reversível pela exclusão manual do arquivo remoto. Os painéis de upload e fila
são carregados em chunk separado; o teto total gzip sobe de 830 KB para 835 KB,
sem alterar os tetos do entrypoint, CSS ou maior asset.

Como reverter: voltar cloud e agente em conjunto para a versão anterior; manter
arquivos já enviados e remover somente temporários expirados.

### DEC-20260724-17 - Evidências de CI não integram o bundle cloud

Status: aceita
Data: 2026-07-24
Contexto: o workflow `30106292559` passou por todos os gates, mas o upload do
release terminou com `Broken pipe` após 22 minutos. O pacote tinha cerca de
1,7 GB porque incorporava `.artifacts`, incluindo cópias temporárias de pytest,
traces e relatórios que já são publicados separadamente pelo CI e não são
consumidos pelo runtime.

Decisão: o release executável exclui integralmente `.artifacts`. As evidências
continuam publicadas pelo CI com retenção de 30 dias. A transferência do bundle
mantém keep-alive SSH e repete no máximo três vezes; falha persistente encerra o
workflow antes da preparação ou troca do slot.

Consequências: o bundle volta a representar somente o conteúdo necessário para
executar a release, reduz tempo e superfície de transferência e preserva o
fail-closed do blue/green. Relatórios de qualidade continuam disponíveis no
artefato próprio do workflow, sem ocupar disco em produção.

Impacto em testes: o contrato de empacotamento exige exclusão de `.artifacts`,
keep-alive e tentativas limitadas. O gate completo e o checksum do bundle
permanecem obrigatórios.

Impacto em rollback: reverter a exclusão reinclui evidências volumosas e
reintroduz risco de interrupção do upload; não altera dados, schema nem slot
ativo.

Como reverter: remover a exclusão e a política de tentativas somente se houver
um consumidor de runtime documentado para `.artifacts` e um transporte
equivalente comprovadamente confiável.

### DEC-20260726-03 - Preset nativo versionado é a fonte executável do fatiamento

Status: aceita
Data: 2026-07-26
Contexto: o perfil resumido criado pelo PKG-63 atende comparação e
compartilhamento, mas não preserva todos os parâmetros necessários para o
Printora reproduzir no futuro um fatiamento feito pelo OrcaSlicer. Retração,
wipe, Z-hop, herança, variantes de extrusor, compatibilidade e campos novos da
engine não podem ser reduzidos a um dicionário parcial sem perda silenciosa.

Decisão: o PKG-131 introduz uma revisão imutável de preset executável que
preserva o bundle nativo do OrcaSlicer (`process`, `filament` e `machine`), o
JSON original sanitizado, uma representação canônica, versão de formato e
engine, herança, overrides, compatibilidade e SHA-256. O perfil social do
PKG-63 permanece como projeção resumida e nunca é a fonte autoritativa de um
job. Cada job de fatiamento referencia a revisão exata do bundle e registra
engine e checksums. Importação entra privada; instalação ou ativação local
continua sendo ação explícita.

Alternativas consideradas: ampliar apenas o campo livre do PKG-63; normalizar
todos os campos do Orca em colunas; guardar somente o JSON nativo sem revisão
canônica; converter imediatamente para um formato universal.

Consequências: o Printora consegue importar/exportar presets do Orca sem perder
campos desconhecidos, produzir diff e herança compreensíveis e reproduzir um
job com a mesma revisão. Conversões para outros slicers precisam declarar
perdas. O armazenamento deve rejeitar host, path local, token, credencial e
outro dado operacional sensível.

Impacto em testes: fixtures controladas do Orca devem cobrir round-trip
semanticamente equivalente, preservação de campos desconhecidos N/N-1,
sanitização, revisão imutável, checksum, herança/diff, autorização e job preso
à revisão original.

Impacto em rollback: médio; desativar importação/edição nativa e voltar o
fatiamento ao estado bloqueado preserva revisões já armazenadas como legado
somente leitura. Nenhuma revisão ou perfil social deve ser apagado.

Como reverter: remover consumidores e rotas do bundle nativo, manter os dados
existentes sem execução e restaurar a versão anterior do serviço. Alteração de
schema futura será entregue por SQL idempotente e rollback por restauração de
backup, nunca por `DROP` ou `DELETE`.

### DEC-20260726-04 - Pacotes comunitários usam padrão e ownership bloqueantes

Status: aceita
Data: 2026-07-26
Vigência: parcialmente superada pela `DEC-20260727-01`; padrão e ownership
continuam bloqueantes somente para pacotes ativos e a cobertura `COM/CAP/SCR`
deixa de ser obrigatória.
Contexto: a ordem topológica e a rastreabilidade dos `PKG-101` a `PKG-155`
impediam dependência futura explícita, mas não fixavam owner, colaboradores,
perfil de risco ou um único padrão de execução. Janelas diferentes poderiam
interpretar backend, frontend, banco e Definition of Done de modos incompatíveis.

Decisão: `docs/community/PACKAGE_ARCHITECTURE.csv` define owner backend
primário, colaboradores, área frontend e risco dos 55 pacotes.
`docs/community/PACKAGE_EXECUTION_STANDARD.md` é bloqueante e concentra
Definition of Ready, modelagem, backend, frontend, SQL, segurança, testes,
compatibilidade, rollout, rollback e handoff. O validador do backlog deve
conferir matriz, dependências e cobertura integral `COM/CAP/SCR`.

Alternativas consideradas: repetir todo o padrão em cada pacote; confiar apenas
no `QUALITY_ROADMAP.md`; criar um módulo técnico por pacote; deixar ownership
para decisão da janela executora.

Consequências: pacotes podem ser executados em janelas separadas com fronteiras
e critérios consistentes, sem transformar número de pacote em módulo. Mudança
de ownership ou risco exige revisão arquitetural explícita. O gate estrutural
reduz divergência documental, mas não substitui testes e evidência da
implementação futura.

Impacto em testes: o check valida 55 linhas únicas, owners permitidos, ausência
de colaborador duplicado, cobertura e unicidade dos IDs, ordem topológica,
estrutura dos dez lotes e referências ao padrão. Testes negativos comprovam que
lacuna, sobreposição, owner inválido e dependência futura falham.

Impacto em rollback: baixo e documental. Reverter remove o novo gate e volta a
permitir interpretação livre, sem alterar runtime ou dados.

Como reverter: reverter matriz, padrão, decisão e extensão do validador no mesmo
commit; não alterar pacotes implementados nem apagar evidências produzidas.

### DEC-20260726-05 - PKG-101 mantém catálogo canônico em código e rascunho local

Status: aceita
Data: 2026-07-26
Contexto: tokens e padrões visuais precisam de versão reproduzível junto da
release. Persistir cada amostra no banco criaria escrita administrativa,
retenção e concorrência sem benefício para um catálogo pequeno e imutável. Ao
mesmo tempo, a pessoa precisa experimentar densidade, estados e formulário sem
arriscar configuração operacional.

Decisão: o domínio compartilhado `design_system` expõe catálogo autenticado,
somente leitura e versionado em código. A interface mantém somente um rascunho
de laboratório sem PII no navegador, com schema versionado, limite de tamanho,
gravação idempotente e conflito entre abas. Não existe endpoint mutável,
telemetria individual, comando físico ou persistência canônica no PKG-101.

Alternativas consideradas: armazenar tokens e rascunhos no PostgreSQL; manter
tudo somente no frontend; permitir publicação global de tokens no pacote.

Consequências: catálogo e release permanecem atômicos, rollback é apenas de
código e o laboratório funciona sem banco novo. A autenticação e o contrato API
continuam testáveis, enquanto repetição local não duplica efeito. Publicação
global ou personalização por organização exigirá pacote próprio e SQL
idempotente, sem alterar retroativamente este contrato.

A tela e seu CSS são carregados sob demanda. O teto total verificável do bundle
passa de 3.400.000 para 3.440.000 bytes e o gzip de 835.000 para 845.000 bytes;
os limites individuais da entrada, stylesheet e asset não aumentam. O build
medido após o recorte fica abaixo dos novos tetos e impede que o catálogo
penalize o carregamento inicial.

Impacto em testes: cobrir invariantes do catálogo, autenticação, contrato N/N-1,
limites do rascunho, parse defensivo, idempotência, conflito entre abas,
offline, teclado, zoom, temas e redução de movimento.

Impacto em rollback: baixo; reverter a release remove a entrada e o endpoint
sem tocar banco ou outros fluxos. Rascunhos locais desconhecidos pela versão
anterior permanecem inertes.

Como reverter: restaurar a release N-1. Não executar SQL, limpeza de banco ou
remoção automática de dados locais.

### DEC-20260726-06 - Preferências acessíveis são sincronizadas por conta

Status: aceita
Data: 2026-07-26
Contexto: o rascunho local do design system não representa uma preferência
pessoal durável e não sincroniza adaptações entre dispositivos. Preferências de
contraste, escala, movimento, semântica e mídia também podem revelar
necessidades pessoais por inferência, portanto não devem virar texto livre,
telemetria individual ou configuração global.

Decisão: o owner `accessibility` expõe catálogo imutável e uma entidade
`AccessibilityPreferences` por usuário autenticado. A persistência aceita
somente enums, booleanos, escala limitada e revisão monotônica. Escritas usam
idempotência e compare-and-swap por revisão; o owner vem da sessão e não do
payload. Os scripts SQLite e PostgreSQL são aditivos e idempotentes, usam
`ON DELETE RESTRICT` e não incluem exclusão ou cleanup.

Alternativas consideradas: manter tudo no navegador; armazenar diagnóstico e
justificativa; criar preferências por organização; reutilizar o rascunho do
PKG-101; criar uma tabela por capacidade.

Consequências: uma conta recebe o mesmo perfil em dispositivos diferentes,
conflitos não sobrescrevem silenciosamente e a aplicação local continua
funcionando durante falha de rede. O payload é pequeno e minimizado, mas deve
ser tratado como dado pessoal sensível por inferência e nunca aparecer em logs.
Configurações da organização e diagnóstico clínico permanecem fora do escopo.
O shell carrega o client de preferências sob demanda e a tela possui chunk
próprio. O teto gzip total passa de 845.000 para 855.000 bytes; os tetos da
entrada, asset individual, stylesheet e total bruto não aumentam.

Impacto em testes: cobrir isolamento entre usuários, primeira escrita,
reexecução, revisão divergente, concorrência, contrato N/N-1, SQL idempotente,
aplicação local, offline, teclado, leitor de tela, zoom, contraste e redução de
movimento.

Impacto em rollback: baixo a médio. A release N-1 ignora a tabela aditiva e as
linhas permanecem preservadas, sem dual-write ou efeito operacional.

Como reverter: restaurar a release N-1 e manter schema/dados sem consumidores.
Não executar `DROP`, `DELETE`, limpeza automática ou restauração de snapshot.

### DEC-20260726-07 - PKG-101 fica restrito ao administrador da plataforma

Status: aceita
Data: 2026-07-26
Contexto: o laboratório do Design system é uma ferramenta interna de avaliação
do PKG-101 e ainda não possui benefício validado para usuários comuns. Expor a
entrada no menu criava expectativa de funcionalidade operacional ligada ao
universo 3D, apesar de o catálogo tratar apenas da coerência visual da interface.

Decisão: menu, rotas internas e endpoint de catálogo exigem a identidade
configurada como administradora da plataforma. A interface oculta a entrada e
direciona usuários comuns à Visão geral; o backend aplica a autorização
independentemente da interface e responde `403`. A regra reutiliza a configuração
central de administradores, sem e-mail fixo no domínio e sem persistência nova.

Alternativas consideradas: manter visível para qualquer usuário autenticado;
ocultar somente o menu; remover imediatamente o PKG-101.

Consequências: somente a conta administradora configurada pode avaliar o
laboratório. Usuários comuns não carregam o catálogo nem acessam o fluxo por URL
direta. A restrição não altera impressoras, STL, fatiamento, banco ou comandos
físicos.

Impacto em testes: cobrir `401` sem sessão, `403` para usuário comum, acesso
completo para administrador, menu oculto e defesa de rota direta.

Impacto em rollback: baixo e sem SQL. Reverter a decisão volta a expor o
catálogo a qualquer usuário autenticado.

Como reverter: reverter em conjunto o guard do endpoint, o filtro de navegação,
a defesa da rota e esta decisão; não remover dados nem rascunhos locais.

### DEC-20260727-01 - Proteção crítica usa step-up por finalidade e retenção aditiva

Status: aceita
Data: 2026-07-27
Contexto: sessões, mutações físicas, privacidade e moderação possuíam controles
parciais, mas não compartilhavam garantia explícita de prova recente, replay,
idempotência, retenção e rollback.

Decisão: ações críticas usam step-up curto, vinculado a uma finalidade permitida
e consumido atomicamente uma vez. Troca de senha revoga todas as sessões.
Exportação é determinística e exclui segredos; exclusão de conta é desativação
lógica com retenção de 180 dias. Recursos de moderação pertencem ao autor do
conteúdo e uma decisão favorável restaura logicamente o item. Setup físico exige
administrador da plataforma e step-up. Os schemas SQLite/PostgreSQL são aditivos
e usam `ON DELETE RESTRICT`. Assinaturas novas do agente cobrem uma carga
canônica com plataforma, versão, SHA-256 e limites de protocolo. Artefatos
legados assinados somente pelo digest permanecem disponíveis para rollback, mas
o auto-update deles fica desativado e o agente rejeita esse escopo.

Alternativas consideradas: confiar na interface; reutilizar um step-up genérico;
apagar imediatamente a conta; permitir jobs arbitrários ao owner; criar painel
administrativo paralelo.

Consequências: replay e concorrência têm efeito único, sessões podem ser
revogadas sem expor token, privacidade e moderação possuem estado verificável e
comandos físicos ganham prova recente. A recuperação dentro da retenção é
operacional e não autoatendimento.

Impacto em testes: concorrência de step-up, idempotência, isolamento, MFA
pendente, sessão, exportação, desativação, bloqueio, recurso, shell, artefato,
rate limit, incidente e rollback.

Impacto em rollback: novas exportações, desativações e recursos podem ser
suspensos por `PRINTORA_PLATFORM_PROTECTION_WRITES_ENABLED=false`, com owner de
operações e expiração máxima de 24 horas. Schema, solicitações e auditoria são
preservados.

Como reverter: restaurar release N-1 compatível, manter tabelas aditivas e
reativar a flag após reteste. Não executar `DROP`, `DELETE`, prune ou restauração
de snapshot.

### DEC-20260728-01 - Fronteiras críticas falham fechado e a origem de release é fixa

Status: aceita
Data: 2026-07-28
Contexto: a auditoria do PKG-104 encontrou identificadores globais sem
revalidação de escopo, operações administrativas permissivas quando ainda não
havia usuário, origem de update influenciada pelo cliente, TOFU de SSH e
instaladores que executavam conteúdo remoto.

Decisão: endpoints administrativos e físicos exigem sessão mesmo no bootstrap;
recursos globais revalidam seu pai no escopo autenticado; toda ação física exige
preview, confirmação do cliente, step-up e impressora ociosa. A aplicação usa
somente o repositório configurado, o agente aceita release e redirecionamento
apenas na origem do manifesto, e os workflows exigem chave SSH conhecida
previamente. Instaladores falham fechado quando o gerenciador necessário não
está instalado.

Alternativas consideradas: manter compatibilidade anônima no primeiro usuário;
aceitar qualquer URL com SHA-256; descobrir chave SSH no workflow; baixar
instaladores oficiais sem verificação adicional.

Consequências: instalações novas exigem provisionamento explícito do
administrador e das dependências, e rotação de host SSH exige atualizar o secret
validado. Em troca, bootstrap, update, deploy e operação física preservam a mesma
fronteira de confiança do estado normal.

Impacto em testes: cobrir negação anônima, IDOR cruzado, origem divergente,
redirecionamento externo, ausência de known hosts, archive bomb, metadado
excessivo, associação comunitária e confirmação física.

Impacto em rollback: reverter a release restaura os fluxos anteriores sem mudar
schema. Não remover tabelas nem dados; se a rotação de chave bloquear deploy,
corrigir o secret por canal operacional e executar novamente o pipeline.

Como reverter: reverter em conjunto guards, escopo, origem de update, política
de known hosts e documentação. Não liberar URL arbitrária como contingência.

### DEC-20260730-01 - Alertas runtime do Klipper usam coleta filtrada pelo agente

Status: aceita
Data: 2026-07-30
Contexto: o Mainsail recebia warnings runtime do Klipper que não faziam parte de
`server_info.warnings` nem dos avisos do Update Manager. O Printora conhecia
versões de host e MCU, mas não exibia alertas como código MCU obsoleto ou erros
críticos recentes do console.

Decisão: o agente consulta o histórico limitado de `/server/gcode_store` junto
do status read-only e filtra na borda somente warnings conhecidos e respostas
críticas `!!`. O payload contém no máximo 20 mensagens compactadas,
deduplicadas e sanitizadas. O backend é autoridade da severidade: firmware MCU
obsoleto monitora; comunicação, protocolo, shutdown, temporização e temperatura
críticos bloqueiam. A Central reutiliza Health Check e abre Monitoramento, sem
nova tabela ou canal WebSocket persistente.

Alternativas consideradas: conectar cada navegador diretamente ao WebSocket do
Moonraker; persistir todo o console; interpretar apenas a diferença de versões;
depender exclusivamente do Mainsail.

Consequências: alertas aparecem no polling consolidado da frota e os resultados
dos jobs preservam evidência mínima. Pode existir atraso de até um ciclo de
health e mensagens antigas podem sair da janela de 200 entradas. Saída normal,
G-code, URL, home path e segredo não devem atravessar o agente.

Impacto em testes: cobrir mensagens reais de MCU obsoleta, famílias críticas,
deduplicação, limite, sanitização, falha do endpoint, decisão do health e ação da
Central.

Impacto em rollback: baixo e sem SQL. A release N-1 ignora os novos campos; o
backend aceita agente antigo sem gerar falso alerta de coleta limpa.

Como reverter: restaurar backend/frontend N-1 e agente N-1. Não há dado ou
schema para remover.

### DEC-20260802-01 - Digitalização por fotos separa captura, reconstrução e qualificação

Status: aceita
Data: 2026-08-02
Contexto: o produto recebeu demanda explícita para enviar várias fotos de um
objeto e obter um STL/3MF utilizável. O portfólio mantinha visão computacional e
IA adiadas e escaneamento cancelado por ausência de benefício comprovado,
hipótese mensurável e fontes técnicas. A demanda agora possui integração direta
com projetos, inspeção 3D e fatiamento, mas qualidade visual não equivale a
precisão dimensional ou imprimibilidade.

Decisão: reativar `PKG-141`, `PKG-153` e `PKG-154` com responsabilidades
separadas. Captura guiada valida fotos, cobertura, escala e privacidade;
reconstrução usa job assíncrono e adapter substituível, com fotogrametria como
fonte geométrica principal e IA explicitamente versionada; qualificação aplica
regras determinísticas, reparos reversíveis, revisão humana e gera snapshot
imutável para STL/3MF ou fatiamento. O agente/Raspberry não executa processamento
pesado. Região inferida ou reparada é diferenciada de região observada. Nenhuma
etapa publica, cobra novamente, fatia ou comanda impressora automaticamente.

Alternativas consideradas: um único pacote ponta a ponta; chamar diretamente um
provider de image-to-3D no frontend; executar Meshroom/COLMAP no agente; aceitar
a saída visual como STL pronto; construir CAD paramétrico automático; manter a
ideia adiada sem benchmark.

Consequências: o fluxo reutiliza projeto, storage, jobs, snapshots, viewer e
fatiamento existentes, mas adiciona fotos privadas, custo de GPU/provider,
retenção, egress, adapters e piloto físico. Três pacotes permitem interromper a
iniciativa após captura ou benchmark sem acoplar dívida ao fatiamento. Não será
divulgada garantia metrológica; peças mecânicas dependem de medidas críticas,
revisão e validação física apropriada.

Impacto em testes: benchmark por classe de objeto, upload/EXIF/IDOR, captura
mobile, escala, jobs/outbox/webhook/retry/custo, provenance, malhas problemáticas,
reparos idempotentes, acessibilidade, download, fatiamento, impressão física,
compatibilidade N/N-1, retenção, incidente e rollback.

Impacto em rollback: cada capacidade possui flag própria. Desabilitar captura,
adapter, reparo, exportação ou integração de fatiamento não remove projetos,
fotos, malhas, snapshots, manifestos ou revisões existentes. Jobs iniciados
devem terminar, cancelar ou reconciliar para estado terminal.

Como reverter: voltar os três pacotes a `deferred`/`cancelled`, retirar novas
entradas da UI e manter dados já criados privados e somente leitura até
exportação/retensão autorizadas. Não executar `DROP`, `DELETE`, prune ou
reprocessamento automático com nova cobrança.

### DEC-20260802-02 - Inspeção de projeto é limitada, determinística e preserva o original

Status: aceita
Data: 2026-08-02
Contexto: projetos multi-arquivo precisam de organização, medidas e sinais
básicos antes do fatiamento, mas analisar malha não pode transformar uma prévia
em garantia mecânica, executar conteúdo não confiável nem substituir o arquivo
canônico por inferência.

Decisão: armazenar peça, montagem, variação e unidade como metadados do arquivo;
inspecionar STL/3MF com limites explícitos e produzir amostra determinística para
viewer progressivo; congelar cada mudança em manifesto canônico com SHA-256. ZIP
usa fallback limitado. Escala e corte no viewer são simulações reversíveis. O
bundle inclui apenas objetos promovidos/validados, manifesto e lista de
checksums. Upload usa idempotência por chave e assinatura, e cota considera
biblioteca e projetos ativos.

Alternativas consideradas: renderizar todo arquivo no cliente; aceitar ZIP como
malha; usar análise sem limites; alterar a malha original ao medir/escalar;
duplicar upload em retry; criar editor CAD no navegador.

Consequências: a pessoa obtém informação essencial mesmo sem preview, arquivos
grandes têm limites previsíveis e snapshots permanecem auditáveis. A análise
básica aponta risco, mas não certifica imprimibilidade, tolerância ou segurança.

Impacto em testes: parser STL/3MF e fallback, limites, idempotência, isolamento
por owner, cota, snapshot/manifesto, bundle/checksums, UI textual/progressiva,
mobile, acessibilidade, contrato e regressão completa.

Impacto em rollback: baixo/médio; scripts são aditivos e N-1 ignora as colunas.
Desativar viewer, inspeção e bundle preserva projetos, arquivos e versões.

Como reverter: restaurar a release N-1 e manter schema/objetos. Em SQLite, usar o
backup anterior ao script somente se reversão física for indispensável. Não
executar `DROP`, `DELETE`, prune nem substituir arquivo canônico.

Referências: `backend/sql/089_project_assets.sql`,
`backend/sql/postgresql/021_project_assets.sql`,
`docs/community/PKG_128_EVIDENCE.md`.

### DEC-20260802-03 - Aprovação visual é vinculada ao checksum e reimpressão recria a jornada

Status: aceita
Data: 2026-08-02
Contexto: concluir o fatiamento não prova que posicionamento, orientação e peças
estão corretos. Reutilizar um G-code ou o estado atual do projeto também poderia
ocultar mudança de artefato, perfil, material ou quantidade.

Decisão: jobs de projeto registram quantidades no snapshot; a revisão visual do
G-code grava data e checksum, e o preflight bloqueia sem essa aprovação ou se o
checksum mudar. Reimpressão cria novo job a partir do snapshot imutável original
e exige nova execução, revisão, preflight e confirmação. Material selecionado é
congelado no input e sua disponibilidade/revisão é revalidada no preflight.

Consequências: a pessoa recebe uma sequência guiada, sem bypass silencioso. Há
uma etapa humana adicional, mas falhas de posicionamento deixam de avançar por
confiança implícita. Jobs legados permanecem legíveis e fluxos sem projeto
continuam compatíveis.

Impacto em testes: quantidades, owner, checksum, alteração de artefato, spool,
clone imutável, idempotência, preflight, entrega, histórico, desktop e mobile.

Impacto em rollback: aditivo. Ocultar as novas ações restaura Administração como
fallback e mantém todas as evidências. Não remover colunas nem dados sem backup.

Referências: `backend/sql/091_print_journey.sql`,
`backend/sql/postgresql/023_print_journey.sql`,
`docs/community/PKG_132_EVIDENCE.md`.

### DEC-20260802-04 - Fotos são normalizadas sem metadados antes da promoção

Status: aceita
Data: 2026-08-02
Contexto: fotos de celular podem conter GPS, comentários, orientação EXIF,
payload disfarçado e resolução desproporcional. Preservar o arquivo original no
objeto canônico aumentaria risco de privacidade e processamento.

Decisão: aceitar inicialmente JPEG e PNG identificados pelo conteúdo. O backend
decodifica, limita pixels, normaliza orientação, recodifica sem metadados e só
então calcula o checksum e promove o objeto privado. HEIC permanece bloqueado
até existir decoder homologado. Qualidade usa resolução, brilho e foco como
sinais acionáveis, nunca como garantia da reconstrução. Reenvio mantém
idempotência e a substituição de uma posição preserva a revisão anterior.

Consequências: há custo controlado de CPU e pequena alteração dos bytes da foto,
compensados pela remoção verificável de EXIF/GPS e por um artefato processável
consistente. O manifesto exportado preserva checksum, posição, altura e escala.

Impacto em testes: assinatura, imagem corrompida, limite de pixels, EXIF,
qualidade, duplicidade, owner, exportação e responsividade.

Impacto em rollback: ocultar a entrada e bloquear novas sessões. Fotos e sessões
existentes permanecem privadas e exportáveis. Não apagar objetos ou tabelas.

Referências: `backend/sql/092_photo_capture.sql`,
`backend/sql/postgresql/024_photo_capture.sql`,
`docs/community/PKG_141_EVIDENCE.md`.

### DEC-20260802-05 - Reconstrução usa gateway por processo com resultado verificável

Status: aceita
Data: 2026-08-02
Contexto: motores locais de fotogrametria e serviços multiview possuem instalação,
GPU, credenciais, cobrança e contratos distintos. Executá-los dentro da API ou
expor detalhes do fornecedor ao domínio dificultaria isolamento, troca e rollback.

Decisão: o domínio cria um job durável na fila `bulk` e seleciona um adapter por
configuração. Integrações reais entram por executável fixo, sem shell, recebendo
manifesto sanitizado em diretório temporário privado e devolvendo JSON sob
contrato versionado. O Printora valida caminho, symlink, formato, tamanho,
checksum, custo e proporções antes de promover a malha. Cancelamento encerra o
processo e uma tentativa antiga não pode substituir o artefato canônico. O modo
padrão é `disabled`; a fixture é sintética e exclusiva de testes locais.

Alternativas consideradas: biblioteca pesada dentro do processo FastAPI;
comando livre fornecido pela requisição; chamada direta do frontend ao provider;
executar na Raspberry Pi; eleger fornecedor antes do benchmark comparativo.

Consequências: API e agente permanecem leves e o motor pode ser trocado sem
alterar o contrato de produto. O gateway precisa cuidar das credenciais fora dos
argumentos e produzir provenance confiável. Nenhum motor será padrão até passar
benchmark real, segurança, carga e canário.

Complemento do provider: o primeiro gateway elegível usa a API multiview Tripo,
sempre desabilitada por padrão. Somente quatro fotos da altura média são
enviadas, em vistas equidistantes, sem textura ou PBR. Um checkpoint privado por
correlação guarda fingerprint e `task_id` para reconciliar polling e evitar nova
tarefa paga após retry. O custo permanece em créditos do provider, sem conversão
inventada para moeda. Essa escolha é reversível pelo adapter e não representa
homologação até existir benchmark real sobre o mesmo objeto.

Como a criação remota não oferece idempotência forte documentada, falhas do
gateway do provider não recebem retry automático do worker. O checkpoint permite
reconciliar uma tarefa cujo identificador já foi recebido; qualquer nova criação
após estado ambíguo exige ação humana. Isso troca disponibilidade automática por
proteção contra cobrança duplicada.

Impacto em testes: idempotência, ownership, fencing, quota, circuit breaker,
timeout, cancelamento cooperativo, contrato do wrapper, provenance, artefato
privado, UI sem percentual inventado e regressão do worker.

Impacto em rollback: definir `PRINTORA_RECONSTRUCTION_MODE=disabled`, bloquear
novos jobs e manter capturas, tentativas e artefatos privados em leitura. Não
remover tabelas ou objetos.

Referências: `backend/sql/093_photo_reconstruction.sql`,
`backend/sql/postgresql/025_photo_reconstruction.sql`,
`docs/community/PKG_153_EVIDENCE.md`.
