# TELAS.md

Inventario operacional de telas, rotas, estados e regras de UI do Printora.

O catálogo plurianual de superfícies comunitárias futuras fica em `docs/community/COMMUNITY_SCREENS.md`. Ele não declara rotas implementadas: serve para recortar pacotes, evitar telas gigantes e manter lista, detalhe e cadastro/edição como responsabilidades separadas.

## Regras

- Este arquivo descreve comportamento final de produto, nao implementacao interna.
- Toda tela alterada deve ser revisada antes de concluir entrega.
- Estados `loading`, `empty`, `error`, `success`, `offline` e `partial` devem ser tratados quando aplicaveis.
- Mudanca visual relevante deve ter evidencia visual quando houver navegador disponivel.
- Nomes internos de pacote/lote nao devem aparecer na UI.

## CRUD

CRUD deve separar responsabilidades:

- Listagem e filtros: busca, filtro, ordenacao, paginacao, estado vazio, erro e acoes de linha.
- Detalhamento: leitura completa, historico, metadados, permissoes e acoes contextuais.
- Cadastro: formulario novo, validacao, sucesso, erro e cancelamento.
- Edicao: carregamento do registro, validacao, conflito, sucesso, erro e cancelamento.

Cadastro e edicao podem compartilhar componente de formulario, mas carregamento, permissao e submissao devem ficar fora do formulario compartilhado.

## Organizacao frontend

- O frontend e uma SPA em `/`.
- A tela ativa e definida por `?section=<chave>` ou `#<chave>`.
- Sem `section`, a entrada inicial e `overview`.
- A navegacao oficial fica em `frontend/src/app/navigation.ts`.
- `frontend/src/main.tsx` deve permanecer apenas como bootstrap, shell de navegacao e composicao das telas.
- A SPA renderiza somente a tela ativa para evitar painel inativo preso por estado/CSS.
- Cada tela fica em um arquivo proprio em `frontend/src/screens`.
- Estado, efeitos e orquestracao de API ficam em hooks por dominio em `frontend/src/hooks/domains`; `frontend/src/hooks/usePrintoraApp.ts` apenas compoe shell, contexto e dominios.
- Chamadas HTTP ficam isoladas por dominio em `frontend/src/services`.
- Componentes reutilizados ficam em `frontend/src/components`.
- O menu lateral principal mostra somente telas globais, que nao dependem de uma impressora selecionada: `overview`, `printers`, `agents`, `projects`, `social`, `catalog`, `setup` e `settings`.
- Telas operacionais de impressora nao aparecem no menu lateral; elas ficam como abas internas de `printer-detail`, aberto a partir da lista de impressoras.
- O seletor de impressora da topbar e o rodape lateral sao apenas contexto rapido. Eles nao definem a arquitetura de navegacao nem tornam o menu dependente de impressora; abrir o detalhe de uma impressora nao deve trocar esse contexto rapido.
- A topbar e fixa/sticky e deve conter apenas controles globais: titulo da area atual, alertas da frota, Sobre, tema claro/escuro e conta do usuario no extremo direito.
- A topbar nao deve conter seletor de impressora nem acoes especificas de tela como adicionar impressora, snapshot, instalacao ou reanalise. Essas acoes ficam no corpo da tela/aba correspondente.
- A Central de alertas aberta pela topbar e da frota. Ela usa leitura consolidada por impressora, independente do contexto rapido/registro aberto, e deve permitir filtrar por impressora, mostrar a impressora de origem em cada alerta e abrir a impressora afetada quando o alerta pertencer a um registro especifico. O filtro usa botoes quando a frota tem ate 6 impressoras e select acima disso.
- Secoes que exigem impressora online permanecem acessiveis dentro do detalhe da impressora e devem exibir estado `offline`, `cached`, `blocked` ou `not_supported` quando o agente/Moonraker nao estiver disponivel.
- Ao trocar o registro aberto, dados operacionais preservados pertencentes a outra impressora devem ser limpos imediatamente; resposta atrasada de uma leitura anterior nunca pode substituir o estado do registro atual.
- Com Moonraker offline, a Central de alertas exibe apenas o alerta de offline/conexao; pendencias que dependem da impressora ligada ou de snapshot antigo nao contam como alertas ativos atuais.
- Enquanto a impressora ativa estiver offline, a SPA revalida status e health a cada 60 segundos para liberar as secoes online quando Moonraker voltar.

## Telas atuais

| Tela | Secao | Entrada | Arquivo | Objetivo | Dependencia de impressora | Status |
|---|---|---|---|---|---|---|
| Visao geral | `overview` | `/`, `/?section=overview`, `/#overview` | `frontend/src/screens/OverviewScreen.tsx` | Dashboard global da frota, agentes, alertas e atalhos para abrir registros | Nao exige impressora ativa | existente |
| Impressoras | `printers` | `/?section=printers`, `/#printers` | `frontend/src/screens/PrintersScreen.tsx` | Lista e cadastro das impressoras gerenciadas; cada registro abre detalhe proprio | Nao exige impressora ativa | existente |
| Detalhe da impressora | `printer-detail` | Estado interno da SPA | `frontend/src/screens/PrinterDetailScreen.tsx` | Registro operacional da impressora com acao de voltar para a lista e abas de resumo, operacao, updates, calibracao, firmware, manutencao, diagnostico e agentes; cabecalho e contexto usam sempre o registro aberto, mesmo quando a preferencia global aponta para outra impressora | Exige registro de impressora aberto | existente |
| Agentes | `agents` | `/?section=agents`, `/#agents` | `frontend/src/screens/AgentsScreen.tsx` | Lista de todos os agentes da frota, sem operacoes de impressora no menu global | Nao exige impressora ativa | existente |
| Projetos de impressão | `projects` | `/?section=projects`, `/#projects` | `frontend/src/screens/PrintProjectsScreen.tsx` | Explorar, salvar, referenciar, publicar, fatiar e enviar projetos com um ou vários arquivos STL/3MF/ZIP/link externo a partir da biblioteca pessoal do usuário | Nao exige impressora ativa; fatiamento/envio exige impressora escolhida no fluxo | inicial |
| Detalhe do agente | `agent-detail` | Estado interno da SPA | `frontend/src/screens/AgentDetailScreen.tsx` | Registro de agente com acao explicita de voltar para a lista, impressora vinculada, dispositivo/host, versao, saude, fila, doctor remoto, suporte e credencial | Exige agente aberto | existente |
| Social | `social` | `/?section=social`, `/#social` | `frontend/src/screens/SocialScreen.tsx` | Descoberta pública de makers, impressoras públicas, comunidades automáticas e relações sociais | Nao exige impressora ativa | existente |
| Catálogo | `catalog` | `/?section=catalog`, `/#catalog` | `frontend/src/screens/CatalogAdminScreen.tsx` | Curadoria administrativa do catálogo mestre de fabricantes, modelos, variantes e componentes | Nao exige impressora ativa; edição exige administrador | existente |
| Setup | `setup` | `/?section=setup`, `/#setup` | `frontend/src/screens/SetupScreen.tsx` | Receita guiada para preparar a Pi, habilitar SSH, validar ambiente, configurar CAN/U2C, gerar firmware, executar flash supervisionado, validar base Klipper e cadastrar a impressora | Nao exige impressora ativa | existente |
| Operacao | aba `operation` em `printer-detail` | Interna do detalhe da impressora | `frontend/src/screens/MonitoringScreen.tsx` + `frontend/src/MonitoringDashboard.tsx` | Operacao ao vivo com temperaturas, toolhead, extrusor, progresso, sistema, fans, CAN e acoes protegidas, incluindo `Salvar config` supervisionado para aplicar valores Klipper pendentes; para suporte, exibe backend e estado somente leitura do banco da plataforma | Exige impressora aberta; live exige agente/Moonraker | existente |
| Arquivos G-code | aba `gcode-files` em `printer-detail` | Interna do detalhe da impressora | `frontend/src/screens/GcodeFilesScreen.tsx` | Navegacao completa dos G-codes do Moonraker com pastas, busca, filtros, ordenacao, selecao, espaco livre, thumbnails, metadados, drawer de detalhe, historico e acoes protegidas | Exige impressora aberta; live exige agente `0.1.33` estável ou `0.1.34` canário e Moonraker | existente |
| Atualizacoes | aba `updates` em `printer-detail` | Interna do detalhe da impressora | `frontend/src/screens/UpdatesScreen.tsx` | Update Manager da impressora, checklist pos-update, update com confirmacao, progresso e historico | Exige impressora aberta; live exige agente/Moonraker | existente |
| Calibracao | aba `tests` em `printer-detail` | Interna do detalhe da impressora | `frontend/src/screens/TestsScreen.tsx` | Centro de calibracao Voron em cards numerados por sequencia, busca, filtros por tipo/uso, ajuda expandida, preflight, execucao com confirmacao presencial e perfil Z aprovado | Exige impressora aberta | existente |
| Firmware | aba `firmware` em `printer-detail` | Interna do detalhe da impressora | `frontend/src/screens/FirmwareScreen.tsx` | Inventario de MCUs/placas detectadas, associacao ao modelo fisico, build, flash planejado e referencia CANBus | Exige impressora aberta | existente |
| Manutencao | aba `maintenance` em `printer-detail` | Interna do detalhe da impressora | `frontend/src/screens/MaintenanceScreen.tsx` | Tarefas preventivas, diario e horas de impressao por impressora | Exige impressora aberta | existente |
| Diagnostico da impressora | aba `reports` em `printer-detail` | Interna do detalhe da impressora | `frontend/src/screens/ReportsScreen.tsx` + `frontend/src/screens/reports/*` | Relatorio da impressora, snapshots, relatorio sanitizado, backup/restore seguro, auditoria read-only e registro tecnico CAN da impressora | Exige impressora aberta | existente |
| Administracao | `settings` | `/?section=settings`, `/#settings` | `frontend/src/screens/SettingsScreen.tsx` | Configuracao global do Printora Cloud; releases e historico da plataforma ficam ocultos para usuarios comuns e visiveis apenas para suporte | Nao exige impressora ativa | existente |
| Sobre | `about` | `/?section=about`, `/#about` | `frontend/src/screens/AboutScreen.tsx` | Apresentacao do autor, motivacao do projeto, funcionalidades, roadmap publico, redes sociais e identidade visual | Nao exige impressora ativa | existente |
| Licenca | `license` | `/?section=license`, `/#license` | `frontend/src/screens/LicenseScreen.tsx` | Resumo de licenca open source, limites de garantia e responsabilidade operacional | Nao exige impressora ativa | existente |

As superfícies administrativas condicionais usam `platform_admin` retornado no
contrato autenticado. A UI não compara email nem mantém lista própria de
identidades; o backend continua sendo a fronteira autoritativa e retorna `403`
quando a ação não é permitida.

## Componentes e modais por dominio

| Dominio | Arquivo | Responsabilidade |
|---|---|---|
| Composicao de modais | `frontend/src/components/modals/AppModals.tsx` | Monta os modais por dominio sem conter conteudo de tela |
| Alertas | `frontend/src/components/modals/AlertCenterModal.tsx` | Central de alertas consolidada |
| Impressoras | `frontend/src/components/modals/PrinterModal.tsx` | Cadastro, edicao, descoberta e teste de conexao |
| Atualizacoes do Printora | `frontend/src/components/modals/SelfUpdateModal.tsx` | Plano, aplicacao e rollback do proprio Printora |
| Atualizacoes da impressora | `frontend/src/components/modals/UpdateDialogModal.tsx` | Confirmacao, bloqueio de risco, rollback e progresso de update via Moonraker |
| Manutencao concluida | `frontend/src/components/modals/MaintenanceDoneModal.tsx` | Conclusao de tarefa preventiva e ajuste do proximo lembrete |
| Manutencao livre | `frontend/src/components/modals/MaintenanceFreeModal.tsx` | Registro livre de manutencao, falha, ajuste ou nota |
| Calibracao ajuda | `frontend/src/components/modals/CalibrationHelpModal.tsx` | Ajuda operacional de um teste de calibracao |
| Calibracao execucao | `frontend/src/components/modals/CalibrationExecuteModal.tsx` | Preflight, progresso ao vivo, retorno de console Moonraker e confirmacao presencial para envio de G-code |
| Calibracao resultado | `frontend/src/components/modals/CalibrationResultModal.tsx` | Historico técnico da execução, retorno de console/PID, ação para salvar config pendente, download JSON e limpeza protegida de registros antigos |
| Calibracao autorizacao critica | `frontend/src/components/modals/CalibrationStepUpModal.tsx` | Modal contextual para senha ou codigo 2FA quando uma acao critica de calibracao exige step-up auth |

## Manutencao

- Ao concluir uma rotina preventiva do catalogo, o modal usa horas de impressao como padrao quando a rotina tiver recomendacao por horas e a impressora ativa estiver com leitura de horas disponivel.
- Se a impressora estiver offline ou sem leitura de horas, o modal preserva o padrao em dias para evitar bloqueio operacional.
- Cada card de rotina preventiva possui acao `Como fazer`, abrindo modal com passos, motivo, falhas evitadas e recomendacao propria da rotina no catalogo de manutencao.
- O conteudo de `Como fazer` das rotinas do catalogo vem do backend junto da tarefa; o frontend usa fallback generico apenas para rotinas livres criadas pelo usuario.
- Rotinas do catalogo podem ser marcadas como `N/A` por impressora quando nao se aplicam; elas ficam ocultas dos filtros operacionais, aparecem no filtro `N/A` e podem ser restauradas por `Desfazer`.
- Rotinas do catalogo exibem badges de area fisica no topo do card e podem ser filtradas por area ou ordenadas por area, titulo, criticidade ou vencimento.

## Hooks e services

| Dominio | Hook | Service |
|---|---|---|
| Shell/navegacao | `frontend/src/hooks/domains/useAppShell.ts` | Nao acessa API |
| Impressoras | `frontend/src/hooks/domains/usePrinters.ts` | `frontend/src/services/printerApi.ts` |
| Setup | `frontend/src/hooks/domains/useSetup.ts` | `frontend/src/services/setupApi.ts` |
| Operacao | `frontend/src/hooks/domains/useOperation.ts` | `frontend/src/services/operationApi.ts` |
| Atualizacoes da impressora | `frontend/src/hooks/domains/useUpdates.ts` | `frontend/src/services/updatesApi.ts` |
| Calibracao e Z-offset | `frontend/src/hooks/domains/useCalibration.ts` | `frontend/src/services/calibrationApi.ts`, `frontend/src/services/zOffsetApi.ts` |
| Firmware | `frontend/src/hooks/domains/useFirmware.ts` | `frontend/src/services/firmwareApi.ts` |
| Manutencao | `frontend/src/hooks/domains/useMaintenance.ts` | `frontend/src/services/maintenanceApi.ts` |
| Relatorios, snapshots, backups e CAN tecnico | `frontend/src/hooks/domains/useReports.ts`, `frontend/src/hooks/domains/useSettings.ts` | `frontend/src/services/reportsApi.ts`, `frontend/src/services/backupApi.ts`, `frontend/src/services/canApi.ts`, `frontend/src/services/printerApi.ts` |
| Diagnosticos de impressora/agente | `frontend/src/hooks/domains/useSettings.ts`, `frontend/src/hooks/domains/usePrinters.ts` | `frontend/src/services/diagnosticsApi.ts`, `frontend/src/services/printerApi.ts`, `frontend/src/services/systemApi.ts` |
| Updates do Printora | `frontend/src/hooks/domains/useSelfUpdate.ts` | `frontend/src/services/systemApi.ts` |
| Social | Tela autocontida `frontend/src/screens/SocialScreen.tsx` | `frontend/src/services/socialApi.ts` |
| Catálogo mestre | Tela autocontida `frontend/src/screens/CatalogAdminScreen.tsx` | `frontend/src/services/socialApi.ts` |

## Administracao - Fatiamento e envio

- Esta area e administrativa/diagnostica. O fluxo diario de escolher projeto, selecionar arquivos, fatiar, salvar G-code e enviar para impressora deve ficar em `Projetos de impressão`.
- A area `Pipeline de fatiamento` em Administracao fica restrita a configuracao da engine, paths sanitizados, modo dry-run, status, diagnostico, politicas e fallback operacional.
- Enquanto o fluxo novo nao estiver validado, entradas legadas podem existir como compatibilidade; depois devem virar atalho, leitura tecnica ou ser removidas/rebaixadas.
- Administracao nao e dona de projeto, job diario, envio operacional ou historico principal. Ela apenas mostra diagnostico e politica.
- A UI administrativa nao exibe conteudo bruto do G-code, tokens, paths sensiveis, Moonraker privado ou dados operacionais publicaveis.

## Distribuicao de conteudo

- A tela `Projetos de impressão` e a entrada principal para projetos com STL/3MF/ZIP, multiplos arquivos, pecas, links externos e artefatos gerados. Ela deve permitir explorar projetos publicos, buscar por conteudo, salvar na conta, abrir detalhe, criar/uploadar projeto proprio, cadastrar link externo, publicar, colocar em revisao/venda quando aplicavel e iniciar fatiamento a partir de projeto salvo.
- `Projetos de impressão` possui pelo menos as areas `Explorar`, `Meus projetos`, `Salvos`, `Listas` e `Jobs de fatiamento`. A navegacao deve ser clara e nao depender de escolher uma comunidade antes.
- Implementação atual: a área `Projetos de impressão` existe no menu principal com contrato canônico, busca pública, filtros por tipo/licença/origem, estado vazio, cards, detalhe central, arquivos, versões/snapshots, comunidades, distinção entre projeto hospedado e referência externa e ação `Salvar nos meus projetos` como referência sem cópia. `Meus projetos` cobre criação, upload, referência externa, armazenamento, publicação comercial e criação/listagem de jobs de fatiamento por projeto.
- A entidade raiz e `Projeto de impressão`. Arquivos do projeto, versoes, compartilhamentos em comunidade, publicacao, jobs de fatiamento, entrega/G-code e historico de impressao sao relacoes ou derivados do projeto.
- Projeto pode conter um ou varios arquivos. A UI deve distinguir arquivo principal/preview, arquivos imprimiveis, pecas opcionais, documentacao, links externos e artefatos gerados.
- `Explorar` lista projetos publicos e referencias externas com filtros por tipo de arquivo, origem, licenca, material, componente, fabricante/modelo/variante, preco/classificacao e comunidades onde foi compartilhado. Item hospedado no Printora e link externo devem ter indicacao visual diferente.
- O detalhe de projeto centraliza titulo, descricao, imagens/preview, arquivos, versoes/snapshots, origem, licenca, autoria, atribuicao, comunidades onde foi compartilhado, tags, compatibilidade, downloads, favoritos, status comercial e acoes `Salvar nos meus projetos`, `Fatiar`, `Publicar/Editar publicação` quando o usuario for dono.
- `Meus projetos` lista tudo que o usuario subiu, salvou, importou ou referenciou. O usuario deve conseguir criar projeto por upload de um ou varios arquivos STL/3MF/ZIP ou por link externo, editar metadados, visibilidade, licenca, autoria, atribuicao, tags, material/componente, arquivar e consultar storage/cota.
- Upload e link externo devem abrir em modal ou estado de cadastro dedicado, separados em secoes `Projeto`, `Arquivos ou links`, `Autoria e licença`, `Publicação` e `Impressão`. O cadastro nao deve exigir comunidade.
- Visibilidade (`privado`, `não listado`, `público`), revisão/publicação (`rascunho`, `em revisão`, `aprovado`, `rejeitado`, `arquivado`), classificação comercial (`gratuito`, `curado`, `premium`, `patrocinado`) e compartilhamento em comunidade sao dimensoes separadas.
- Comunidade nunca e dona do projeto. Compartilhamento em comunidade e relacao N:N; remover compartilhamento nao arquiva, apaga, despublica nem transfere ownership do projeto.
- A ação `Fatiar` parte do detalhe de um projeto salvo e guia o usuario por `projeto -> arquivos/peças -> impressora -> perfil/material -> qualidade -> job -> preflight -> salvar G-code ou enviar`. O fluxo deve usar as impressoras do usuario e mostrar incompatibilidade de volume, material, nozzle ou estado da impressora antes de executar.
- Todo job de fatiamento deve apontar para versao/snapshot imutavel do projeto, arquivos selecionados, orientacao/dimensoes relevantes, perfil usado, usuario e impressora. Alteracoes posteriores no projeto nao alteram jobs, G-code ou historico existentes.
- `Administração > Fatiamento controlado` fica restrito a configuracao, verificacao da engine, paths sanitizados, status, diagnostico, politicas e fallback operacional. Nao e a entrada principal para criar job diario de fatiamento.
- `Social > Comunidades > Projetos` é a vitrine/contexto comunitario de projetos compartilhados na comunidade. A criacao e gestao principal de STL/3MF/link proprio ficam em `Projetos de impressão > Meus projetos`; comunidades apontam para o detalhe central do projeto. A aba/rota legada `Arquivos` só pode existir como redirect/alias temporário.
- Implementação atual de comunidade: a aba visível é `Projetos`, consumindo projetos centrais compartilhados via relação N:N e sem formulário de upload/fatiamento/envio dentro da comunidade.
- Entradas antigas de upload/envio/fatiamento em comunidade ou Administracao devem ser mantidas apenas ate o fluxo novo estar validado. Depois viram atalho, leitura tecnica ou sao removidas/rebaixadas.
- Historico de impressao deve ser acessivel pelo projeto e pela impressora, indicando perfil/material, resultado, falha, feedback e privacidade. Sinais publicos devem ser agregados e sanitizados por projeto/material/perfil/tipo tecnico, sem expor impressora privada, agente, Moonraker, token, IP ou path sensivel.
- Backups de impressora ficam na aba `Diagnostico` do detalhe da impressora, junto de snapshots, comparacoes, relatorio sanitizado e evidencias diagnosticas.
- Auditoria read-only da impressora fica na aba `Diagnostico` do detalhe da impressora.
- Na tela Relatorios, a leitura principal deve explicar para usuario leigo se pode imprimir, por que nao imprimir quando houver bloqueio e qual acao segura seguir.
- Na tela Relatorios, latencia deve ser apresentada como comunicacao Printora-Moonraker na rede local, nao como falha generica de API.
- Na tela Relatorios, lentidao de comunicacao Printora-Moonraker deve ser monitoramento, nao bloqueio de impressao, quando Klipper e Moonraker estao saudaveis na Raspberry.
- Na tela Relatorios, diagnostico de rede/host deve executar pelo agente pareado. A API cloud nao executa SSH, ping, DNS ou HTTP direto para a rede local da impressora.
- Na tela Relatorios, formularios tecnicos de backup, comparacao, restore e relatorio sanitizado devem abrir em modal; a tela principal e leitura diagnostica, nao cadastro.
- Diagnostico de host/dispositivo fica no detalhe do agente, usando doctor remoto e pacote de suporte sanitizado. A administracao global nao mostra diagnostico local de Mac/servidor para operador.
- CAN de operacao fica na aba `Operacao` do detalhe da impressora como leitura operacional; registro tecnico, parser e comparacao manual ficam na aba `Diagnostico` da impressora aberta.
- Na aba Operacao do detalhe da impressora, o card `Impressão` pode exibir a thumbnail do G-code retornada pelo Moonraker e uma prévia navegável renderizada pelo Printora a partir do G-code cacheado/coletado. Em instalação cloud, o agente atua apenas como ponte leve para buscar ou cachear o arquivo/dados locais da Raspberry; rotação, zoom e enquadramento pertencem ao frontend. A prévia deve mostrar a camada atual e o material já impresso abaixo dela, sem recalcular pesado a cada atualização do agente e sem bloquear operação, comando protegido ou impressão quando o arquivo for grande ou a leitura falhar.
- Na aba Operacao do detalhe da impressora, a prévia 3D do G-code deve preservar, quando o agente retornar, a classificação compacta das linhas de extrusão para diferenciar perímetro, preenchimento, superfície, suporte e saia/brim; antes de 100%, a cena deve priorizar o material já impresso e a camada atual, sem criar volume futuro que pareça parte real da peça.
- Na aba Operacao do detalhe da impressora, a prévia 3D por amostragem deve renderizar somente trajetórias reais recebidas do G-code, separadas por tipo de linha, sem sintetizar corpo/pele preenchidos a partir de contornos parciais; qualquer volume sólido inferido a partir de amostras pode criar teto, parede ou buraco inexistente e não deve ser exibido como peça real.
- Na aba Operacao do detalhe da impressora, paridade visual com o G-code Viewer do Mainsail exige usar o contrato real do `@sindarius/gcodeviewer`, com cache/serviço separado para o G-code completo e a posição `file_position` atual. O endpoint de status do agente continua leve e não deve transportar o arquivo completo dentro do resultado periódico. Controles de câmera devem preferir APIs nativas do viewer, inclusive navegador 3D, em vez de coordenadas/câmera sintetizadas pela UI.
- Na aba Operacao do detalhe da impressora, falha de leitura ao vivo, timeout do agente ou ausencia de thumbnail/camada nao deve exibir erro bruto de infraestrutura nem reservar area grande vazia; a UI deve cair para estado compacto e manter somente dados/fatos disponiveis.
- Na aba Operacao do detalhe da impressora, a atualizacao automatica deve aguardar a leitura atual e seus complementos terminarem antes de agendar a proxima; requisicoes lentas nao podem se sobrepor, criar tempestade de jobs ou atrasar snapshots e outras acoes do agente.
- Na aba Operacao do detalhe da impressora, controles de rotação, zoom, pan, barras de deslocamento horizontal/vertical e navegador 3D devem ocupar areas reservadas dentro da prévia, sem cobrir labels, contadores, thumbnail ou dados da impressão; em larguras menores, o card `Impressão` empilha visual, fatos e Machine sem criar buracos grandes.
- Updates da impressora ficam na aba `Atualizacoes` do detalhe da impressora; update do agente fica no detalhe/lista de agentes, por job remoto entregue ao agente via WebSocket com fallback heartbeat/polling e sem SSH; update da plataforma Printora fica fora da operacao comum do usuario final.
- Na aba Operacao do detalhe da impressora, a faixa de KPIs ao vivo deve manter espacamento proprio antes dos blocos de Temperaturas/Impressao; o layout nao pode depender de classe exclusiva da tela standalone de Monitoramento.
- Na aba Operacao do detalhe da impressora, o card `Impressão` fica em faixa propria. Durante impressão, usa a previsualizacao 3D como area principal e coloca thumbnail, progresso, fatos da impressao e limites de `Machine` na lateral direita quando houver largura. Quando a impressao terminar com estado `complete`, deve manter a ultima impressao renderizavel usando o G-code concluido, com progresso completo e dados finais. Em `standby`, `cancelled`, `error` ou sem G-code renderizavel, nao deve reter preview/progresso/fatos antigos nem exibir um bloco grande sem dados; deve mostrar apenas estado compacto, ultimo trabalho confiavel quando houver e poucos G-codes recentes como atalho para a aba completa. Títulos como `Thumbnail` e contador de camada devem aparecer completos quando houver espaço. `Temperaturas` fica abaixo em largura cheia. Nenhum card deve ser esticado para acompanhar a altura de outro card ou criar area vazia interna.
- Na aba Operacao do detalhe da impressora, a lista ociosa de G-code deve ser apenas atalho curto. Tabela completa, filtros, detalhe, preview e ações de arquivo ficam exclusivamente em `Arquivos G-code`.
- A aba `Arquivos G-code` do detalhe da impressora concentra a navegação completa dos arquivos existentes no Moonraker: diretórios, busca, ordenação, filtros, espaço livre, thumbnails, metadados técnicos, histórico e ações por arquivo. A aba `Operacao` pode apontar para ela, mas não deve duplicar a tabela completa.
- Na aba `Arquivos G-code`, o clique em um arquivo abre detalhe em drawer com preview sob demanda, metadados, histórico, preflight remoto e ações protegidas como imprimir, baixar, copiar caminho, renomear, mover, duplicar ou excluir. Ações destrutivas ou de impressão respeitam estado da impressora, permissões, step-up e confirmação explícita; durante impressão ativa, o backend/agente bloqueia mutações antes de chamar Moonraker.
- Na aba `Arquivos G-code`, a prévia sob demanda usa o mesmo viewer 3D reutilizável de `Operacao`, com modos de arquivo completo, até camada selecionada e camada selecionada. O clique em `Prévia` não baixa G-code no polling da tela e não executa ação mutável na impressora.
- Na tela Administracao, `Releases anteriores`, status e `Historico da plataforma` sao conteudo interno de suporte, visivel apenas para `breno@mayder.com.br`; usuarios comuns veem apenas escopo global e operam updates pelos registros de agente.
- A tela Sobre deve ser acessivel pelo icone de informacao no topo em todas as telas; por enquanto nao aparece no menu lateral.
- A tela Sobre deve promover o autor, exibir LinkedIn, Instagram, GitHub do projeto, motivacao, funcionalidades atuais, aviso de teste, versao sem custo, roadmap online futuro e opcoes de marca.
- A tela Licenca deve ser acessivel a partir da tela Sobre e deixar claro o uso open source, ausencia de garantia e responsabilidade do usuario em operacoes criticas.
- A tela Conta deve concentrar autenticação cloud, cadastro, sessão, organizações opcionais, 2FA e step-up auth.
- Usuário autenticado acessa Conta pelo menu do usuário no topo, com nome/ícone e dropdown; Conta não deve aparecer como item do menu lateral.
- Itens do dropdown da conta devem abrir a aba interna correta no primeiro clique, mesmo quando a tela Conta ainda não está montada.
- A área Conta deve separar responsabilidades em estados/telas internas: organizações e perfil.
- O menu do usuário deve expor `Organizações` e `Perfil`; `Perfil` usa abas internas para `Conta`, `Contatos`, `Senha` e `Segurança`, evitando página longa.
- Em `Conta > Perfil`, a aba `Público` concentra a gestão do perfil social do usuário: nome público, slug, URL pública, bio, avatar HTTPS, localização opcional, links permitidos, estado de privacidade, prévia pública e impressoras públicas em contexto.
- Em `Conta > Perfil > Público`, o bloco `Segurança social` concentra privacidade e antiabuso: descoberta em busca/listagens, visibilidade de seguidores, origem permitida para mensagens sociais, menções em conteúdo e histórico de downloads sociais. Esses controles não alteram login, organizações, permissões, agentes ou acesso operacional.
- `Conta > Perfil > Público` deve separar visualmente dados da conta operacional e perfil público/social. Email, WhatsApp, organizações, papéis, permissões, agente, Moonraker, SSH, tokens e hosts operacionais não aparecem na página pública.
- Organizações na Conta devem listar todas as organizações do usuário em tela própria com ações de linha; uso individual continua disponível sem CRUD.
- Organizações na Conta devem separar lista, detalhe, criação e edição; criação/edição abrem em modal, detalhe abre como estado dedicado em largura total e mostra membros, convites por link e impressoras vinculadas em blocos/tabelas separados.
- Organizações na Conta devem permitir editar e excluir somente quando o usuário for `owner`; exclusão deve passar por confirmação destrutiva.
- Convites de organização pendentes devem poder ser cancelados por gestor da organização; convites aceitos ficam apenas como histórico.
- O vínculo de compartilhamento deve ser por impressora, não por agente; remover usuário ou impressora da organização deve estar disponível no detalhe.
- Agentes devem ter tela propria no menu lateral como lista global da frota. Geração de token, comando pronto de instalação, tokens por impressora e suporte da impressora ficam na aba `Agentes` do detalhe da impressora.
- Usuário anônimo deve ver somente o shell mínimo de autenticação, sem menu lateral, seletor de impressora, alertas, telas internas ou dados operacionais.
- Na tela Conta, email e senha são obrigatórios no cadastro; nome, WhatsApp, Telegram e demais contatos são opcionais e não bloqueiam a criação da conta.
- Na tela Conta > Perfil, o usuário pode alterar nome, timezone, WhatsApp, Telegram e redes sociais opcionais; email permanece como identificador de login.
- Na tela Conta > Perfil, alteração de senha exige senha atual e confirmação da nova senha.
- Na tela Conta, organização não é obrigatória para uso individual; quando existir, a UI permite criar organização e vincular usuários com papel `admin` ou `operator`.
- Na tela Conta, o setup de 2FA deve exibir segredo/URI, validar código antes de ativar e exigir código atual para desativar quando 2FA estiver ativo.
- Na tela Conta, autenticação reforçada gera autorização curta para ações críticas; usuários com 2FA usam código, usuários sem 2FA usam senha. Se a autorização faltar durante uma ação crítica de calibração, o usuário deve poder informar senha/código em modal contextual sem sair do fluxo.
- Datas visíveis no sistema devem ser exibidas em formato brasileiro usando a timezone do usuário logado. O banco mantém UTC/texto original; a conversão acontece somente na formatação da UI.
- A tela Social é uma área de descoberta pública e comunidade. Ela responde quais makers, impressoras públicas e comunidades técnicas existem no Printora.
- A tela Social não é administração de conta, não é gestão operacional de impressora e não é curadoria administrativa de catálogo.
- A tela Social consome dados publicados por `Conta > Perfil > Público`, pelo detalhe da impressora e pelo catálogo canônico; ela não contém formulário principal de edição de perfil, ação principal de publicar/despublicar impressora nem edição de curadoria.
- A primeira tela de Social usa abas no topo: `Descoberta`, `Comunidades`, `Impressoras`, `Makers`, `Relações` e `Notificações`, com filtros, cards/listas e estados vazios úteis. Cards de makers mostram avatar/monograma, nome, slug, bio, impressoras públicas, localização e ação principal para abrir o perfil.
- A aba `Descoberta` consome `/api/social/search` e `/api/social/tags`, pesquisa conteúdo público indexado, mostra tipo do resultado, comunidade/contexto técnico, tags, popularidade, data e ação de abertura. Ela possui busca textual em faixa compacta, filtros por tipo, tag, material, componente, licença e arquivo, facetas clicáveis em coluna lateral, ordenação e paginação. Conteúdo privado, dados operacionais, identificadores internos de pacote/lote/backlog e informações sensíveis não devem aparecer.
- A aba `Descoberta` também mostra `Recomendações técnicas` vindas de `/api/social/recommendations`. Cada recomendação exibe tipo, título, motivos do score, score e reputação técnica do contribuidor. A explicação deve ser curta, auditável e baseada somente em sinais públicos; auto-voto não aumenta score.
- A tela Social mostra resumo de relações: seguidores, seguindo, amigos e solicitações; ações completas ficam no perfil público `/u/{slug}` ou em `Conta > Perfil`.
- A aba `Notificações` é exclusiva para notificações sociais in-app. Ela deve exibir filtro de estado, lista de respostas/relações/conteúdo acompanhado, digest pendente, acompanhamentos e preferências por tipo. Alertas operacionais de impressora, agente, Moonraker, manutenção ou firmware não aparecem nessa aba.
- Perfil público, seguidores, amizades, bloqueios, comunidades e impressoras públicas não concedem acesso a organizações, agentes, Moonraker, SSH, tokens ou permissões de impressora.
- No detalhe da impressora real, a área `Publicação da impressora` concentra o `Perfil público da impressora`: publicar/despublicar, edição de nome público, descrição, mods, imagens HTTPS, variante canônica, prévia e URL `/p/{printer_id}`. Na aba `Resumo`, essa área deve abrir como leitura/preview com ação `Editar perfil público`; campos de edição não ficam abertos por padrão.
- A tela Social pode mostrar e descobrir impressoras públicas, mas a ação principal de publicar/despublicar pertence ao inventário real da impressora.
- Uma impressora só pode ser publicada quando estiver vinculada a uma variação técnica do catálogo mestre; a publicação exibe apenas nome público, descrição, mods/imagens opcionais, fabricante, modelo, variação, volume útil e cinemática.
- A página pública do perfil fica em `/u/{slug}` e mostra somente nome público, avatar, bio, localização opcional, links permitidos e impressoras públicas. Perfil `private` retorna indisponível; perfil `unlisted` abre por URL direta, mas não deve ser listado.
- A página pública `/u/{slug}`, quando aberta por usuário autenticado, é o contexto principal das relações sociais e exibe ações claras para seguir/deixar de seguir, solicitar amizade, aceitar, recusar, cancelar solicitação, desfazer amizade, bloquear e desbloquear. Quando acessada pela descoberta Social autenticada, abre embutida no shell principal com menu lateral e seção Social ativa.
- Páginas públicas standalone como `/u/{slug}` e `/p/{printer_id}` devem aplicar o tema claro/escuro persistido no navegador, mesmo sem carregar o shell logado completo.
- Usuário bloqueado não deve ver conteúdo restrito do perfil nem impressoras públicas do bloqueador; desbloquear não restaura automaticamente follows ou amizades.
- A página pública da impressora fica em `/p/{printer_id}` e mostra somente dados públicos autorizados. Impressora privada, inexistente ou de perfil `private` retorna indisponível.
- A busca pública de impressoras usa o contrato `/api/social/printers` e só lista impressoras públicas de perfis públicos, com filtros por fabricante, modelo, variante e mods.
- Comunidades sociais são derivadas automaticamente do catálogo por fabricante, modelo e variante. Elas não são organizações operacionais e não aparecem como controle de permissão.
- A tela `Social` lista comunidades automáticas com filtros canônicos por fabricante, modelo, variante e componente; fabricante/modelo/variante usam combobox pesquisável compacto, dropdown opaco no mesmo padrão visual do Catálogo, lista limitada, marca visual do fabricante por logo/monograma, contexto técnico, contagem de membros, contagem de impressoras públicas, paginação horizontal visível e cards com ação primária alinhada para abrir comunidade.
- A página real da comunidade fica em `/c/{slug}` e consome `/api/social/communities/{slug}`. Quando aberta por usuário autenticado, ela permanece dentro do shell principal com o menu lateral e a seção Social ativa; quando aberta por visitante, usa shell público mínimo. Ela mantém padrão visual próximo da tela Social, mostra marca do fabricante, ação compacta de retorno para Social, nome, escopo, status, fabricante/modelo/variante quando aplicável, contagens de membros/impressoras/arquivos/mods e contexto técnico do catálogo em coluna separada do conteúdo principal.
- A página `/c/{slug}` possui abas: `Feed`, `Projetos`, `Mods`, `Perfis`, `Membros` e `Impressoras públicas`. Feed consome `/api/social/communities/{slug}/feed` com ordenação, filtros técnicos recolhidos atrás do botão `Filtros`, paginação e estados controlados; também permite discussões técnicas autenticadas, mas o formulário de nova discussão só abre em modal pela ação `Nova discussão`, com campos separados entre conteúdo e contexto técnico. `Projetos` lista somente projetos centrais compartilhados naquela comunidade e aponta para o detalhe em `Projetos de impressão`; a comunidade não cadastra, edita, arquiva, publica, fatia nem envia arquivos como fluxo principal.
- Na aba `Projetos`, ações autenticadas permitidas são compartilhar projeto existente, remover o compartilhamento quando autorizado e abrir/criar projeto em `Projetos de impressão`. Remover compartilhamento não apaga o projeto, não altera visibilidade principal, não remove arquivos e não muda ownership.
- Na aba `Projetos`, classificação comercial e transparência vêm do projeto central. Premium/patrocinado exige revisão aprovada na publicação do projeto, e patrocinado deve mostrar aviso de transparência como promoção, não como recomendação técnica neutra.
- Referências externas aparecem como projetos/referências do domínio central. Bookmark externo não permite fatiamento ou envio enquanto não houver arquivo hospedado/importado, validado e autorizado no projeto.
- Na página `/c/{slug}`, a aba `Perfis` mostra configurações técnicas públicas ou comunitárias de impressoras da comunidade por `/api/social/communities/{slug}/technical-configs`, com comparação normalizada de componentes e calibrações por `/api/social/communities/{slug}/technical-configs/comparison`. A tela é de descoberta e comparação; cadastro, edição e arquivamento ficam no detalhe da impressora, no bloco `Configurações técnicas`, junto do perfil público da impressora real. No `Resumo`, a lista fica em leitura e o formulário só abre por `Criar configuração técnica` ou `Editar configuração técnica`. Nenhuma dessas telas exibe Moonraker, agente, SSH, token, IP, host, caminho local, organização ou permissão operacional.
- Na página `/c/{slug}`, a mesma aba `Perfis` também lista perfis de material e fatiamento visíveis por `/api/social/communities/{slug}/material-profiles`, mostrando material, nozzle, temperaturas, fluxo, camada, velocidade, infill, suporte, objetivo e compatibilidade. Cadastro, edição, arquivamento e export ficam no detalhe da impressora, no bloco `Material e fatiamento`; no `Resumo`, a lista fica em leitura e o formulário só abre por `Criar perfil de material` ou `Editar perfil de material`. Esses perfis são orientação compartilhável e nunca aplicam configuração automaticamente na impressora.
- A página `/u/{slug}` lista projetos públicos ou não listados acessíveis do perfil, separada da lista de impressoras públicas e sem exibir projetos, arquivos ou histórico privados. Endpoints legados de biblioteca só podem existir como compatibilidade/redirect para o domínio de projetos.
- Comunidade `obsolete` fica visível como histórico, sem membros/impressoras ativas. Comunidade `merged` aponta a comunidade destino quando existir e não recebe novas associações.
- Comunidade nunca exibe Moonraker, agente, SSH, token, IP operacional, organização, permissões ou qualquer dado privado da impressora.
- Bloqueios sociais devem encerrar interações sociais existentes e não devem apagar histórico operacional, organização, inventário ou auditoria de impressora.
- Rate limits sociais devem aparecer para o usuário como bloqueio temporário acionável, sem expor score, IP, hashes internos ou regras de detecção. Sinais de abuso ficam restritos à moderação administrativa.
- A tela Catálogo é a superfície administrativa de curadoria do catálogo canônico, separada da tela Social.
- A tela Catálogo deve separar lista/filtros por modelo e detalhe de fabricante/modelo. A listagem principal deve ser uma tabela em largura total, com ação de linha por ícone para abrir detalhe; o detalhe deve substituir a listagem como tela/estado dedicado, com ação explícita de voltar.
- A listagem do Catálogo deve ter limite de registros por página, paginação visível e preservação de filtros/página na URL; ao voltar do detalhe, o usuário retorna para a mesma página e filtros aplicados. Em mobile, a tabela vira cards rotulados para evitar corte horizontal de dados e acoes.
- No mobile, grids técnicos de detalhe de impressora, Operação e Manutenção devem empilhar cards, filtros, tabelas e ações protegidas sem criar colunas implícitas, texto vertical ou estouro horizontal.
- Filtros do Catálogo devem usar combobox pesquisável para fabricante, modelo, tamanho/versão, componente, cinemática, firmware e estado de confiança. Fabricante restringe os modelos disponíveis e modelo restringe as variações; campo de texto livre não é o fluxo principal para selecionar fabricante/modelo.
- A tela Catálogo deve exibir fabricante, logo/monograma, resumo, site, repositório, documentação, Discord e Reddit quando disponíveis. O detalhe do modelo deve exibir página do modelo, Git do projeto, documentação, BOM, canais de comunidade, descrição, notas de curadoria, ficha de curadoria, fontes usadas, variações técnicas, volume útil, cinemática, firmware, componentes e `trust_state`. Identificadores internos de pacote ou campos de origem técnica não devem aparecer para o usuário.
- Logos só devem aparecer quando forem fonte oficial, GitHub org/usuário do fabricante ou imagem de projeto confiável. Quando houver dúvida, a UI usa monograma do fabricante/modelo.
- Usuário comum autenticado pode navegar no Catálogo, filtrar, abrir detalhes de fabricante/modelo/variação e usar variantes para publicação/consulta; criação, edição e promoção de curadoria do catálogo canônico ficam restritas ao administrador.
- Usuário administrador vê, na tela Catálogo, um painel separado de `Moderação` com filtro de estado, lista de denúncias, detalhe da entidade denunciada, justificativa auditável, ações de revisar/ocultar/restaurar/bloquear/descartar e histórico recente. Usuário comum não vê o painel e a rota administrativa retorna bloqueio.
- O painel de moderação é uma fila operacional: listagem/filtro, detalhe da denúncia, ação com motivo e histórico ficam visualmente separados e não substituem as telas de detalhe do conteúdo moderado.
- Estados administráveis do catálogo: `official`, `community`, `draft`, `obsolete` e `blocked`. Itens obsoletos/bloqueados não devem quebrar impressoras já vinculadas.
- Na tela Impressoras, o cadastro/edição da impressora separa metadados cloud, conexão Moonraker e SSH. Metadados incluem modelo, localização, tags, observações e organização opcional.
- Na tela Impressoras, a lista mostra dados de frota e acoes de linha para editar, abrir detalhe, ler status, gerar snapshot e trocar contexto rapido. Acoes de linha usam a impressora da propria linha; contexto rapido nao deve ser pre-requisito. Status, token, instalação, pareamento e saúde de agente ficam no detalhe da impressora ou no detalhe do agente.
- Na tela Impressoras, loading de leitura de status, snapshot ou refresh de agente deve ficar restrito ao card da impressora acionada; uma impressora offline ou lenta nao pode bloquear `Detalhar` ou acoes de outra impressora online.
- Na tela Agentes, a lista global deve mostrar versão instalada e versão esperada, com ação contextual para atualizar o agente selecionado. Agente ativo sempre recebe job remoto `remote_agent_update_check`; a UI não deve pedir SSH nem comando manual para update.
- No detalhe do agente, `Versão esperada` continua sendo a recomendada
  globalmente e `Canário disponível` informa a versão candidata. Quando há
  candidato diferente da versão instalada, `Instalar canário` cria o job web
  direcionado; depois da instalação, `Reverter para` cria rollback web para a
  recomendada N-1. Nenhuma dessas ações usa SSH ou promove a frota.
- Na aba `Agentes` do detalhe da impressora, o pareamento separa explicitamente `Agentes pareados` de `Tokens de instalação`: agente pareado é o vínculo do host no backend; token é apenas credencial curta de instalação. A tela deve listar agentes pareados com status, versão, último contato, botão `Revogar agente` para agentes ativos e `Remover agente` para agentes revogados. Remover token nunca deve sugerir que remove agente.
- Na aba `Agentes` do detalhe da impressora, se existir agente ativo/offline já pareado para a impressora, o fluxo de instalação deve alertar que reinstalar no mesmo host exige revogar/remover o agente antigo antes de gerar ou executar novo comando.
- Na aba `Agentes` do detalhe da impressora, o pareamento permite gerar token curto para a impressora aberta, copiar o token uma única vez por toast e botão no token recém-criado, listar tokens de instalação por prefixo/status, revogar tokens ativos, remover tokens inativos da gestão visual, listar agentes pareados, revogar agente, rotacionar credencial e remover agentes revogados da gestão visual sem apagar auditoria.
- Na aba `Agentes` do detalhe da impressora, a instalação assistida gera comando de preflight, comando de instalação com token curto, URL publica do binario do agente, comando de uninstall, botoes de copiar por bloco de comando e mostra validação pós-instalação por agente ativo, versão e heartbeat.
- No detalhe do agente, saúde e suporte mostram estado online/offline, versão, protocolo, fila, falhas, alertas, doctor remoto e pacote de suporte sanitizado.
- No detalhe do agente, o bloco `Dispositivo do agente` mostra plataforma, versão instalada/esperada, status Moonraker em card legível, API, fila/log local, leitura Raspberry de energia/throttling quando o doctor remoto retornar `raspberry_throttling` e snapshot cacheado de consumo do host enviado pelo agente a cada 5 minutos. O snapshot separa CPU/RSS por serviço detectado, usa gauges/barras para consumo atual e deixa claro que a rede é agregada do host, sem histórico dedicado.
- No detalhe do agente, datas visíveis devem ser exibidas no formato brasileiro usando a timezone do usuário logado enquanto não houver internacionalização dedicada.
- No detalhe do agente, credencial operacional completa aparece somente no momento de troca/rotação; depois a UI mostra apenas prefixo, status, plataforma e último contato.
- Ações operacionais da impressora não ficam na tela Agentes; operação, atualização, calibração, manutenção e firmware pertencem aos menus próprios.
- A tela Setup deve ficar disponivel sem impressora ativa, pois seu objetivo e preparar uma Pi antes do cadastro final da impressora.
- Na tela Setup, o primeiro bloco deve deixar claro que placa virgem sem SO/rede/SSH nao pode ser acessada por SSH; a preparacao de mídia/boot e etapa manual ou futura.
- Na tela Setup, o topo deve exibir uma receita sequencial para usuario leigo, com progresso, etapas manuais marcaveis, passos bloqueados/prontos/feitos e abertura de cada etapa em modal.
- Na tela Setup, a receita deve seguir a ordem: gravar sistema operacional, conectar rede, ativar SSH, informar acesso, validar Pi, configurar CAN/U2C, gerar firmware, conferir cabeamento, executar flash supervisionado, validar base Klipper e cadastrar a impressora.
- Na tela Setup, formulários técnicos, resultados, planos, histórico e orientações detalhadas não devem ficar empilhados na tela principal; eles abrem no modal da etapa correspondente.
- Na tela Setup, cada modal deve funcionar como receita de bolo para usuário leigo, explicando opções, ordem de execução, sinais de sucesso, riscos comuns e fontes oficiais quando houver download/instalação externa.
- Na tela Setup, quando a receita estiver concluída e a impressora cadastrada, a preparação deve ficar recolhida e a tela deve mostrar apenas o estado final com acesso para Impressoras e opção de reabrir a receita.
- Na tela Setup, a UI deve aceitar host, porta, usuario, metodo de autenticacao por agente e timeout, sem campo de senha. Chave/SSH direto pela API nao e caminho cloud.
- Na tela Setup, `Preflight SSH` executa apenas coleta read-only e `Gerar plano` retorna somente plano dry-run com comandos `PLAN`.
- Na tela Setup, o historico deve mostrar alvo, tipo e status sem segredo, senha, token ou caminho de chave privada.
- Na tela Setup, a seção CAN/U2C deve reutilizar o alvo SSH, permitir ajustar interface e bitrate, executar diagnóstico read-only e gerar plano com comandos `PLAN`.
- Na tela Setup, `Aplicar CAN` deve exigir a frase `CONFIGURAR CAN0`; mesmo com a frase, o backend bloqueia quando `PRINTORA_CAN_SETUP_MODE=remote` não estiver habilitado.
- Na tela Setup, o histórico CAN deve mostrar tipo, interface, bitrate, alvo e status sem senha, token ou caminho de chave privada.
- Na tela Setup, a seção Firmware remoto deve permitir escolher preset, nome físico, papel da placa, paths remotos, interface CAN e confirmar variante física antes de gerar plano.
- Na tela Setup, o plano de firmware deve mostrar hash do `.config`, diretório de artefatos, binário esperado e comandos `PLAN`, sem flash.
- Na tela Setup, `Build remoto` deve exigir a frase `BUILD_FIRMWARE_NO_FLASH`; mesmo com a frase, o backend bloqueia quando `PRINTORA_REMOTE_FIRMWARE_BUILD_MODE=remote` não estiver habilitado.
- Na tela Setup, o histórico de firmware deve mostrar placa, preset, alvo e status sem segredo e sem caminho de chave privada.
- Na tela Setup, a seção Flash supervisionado deve reutilizar SSH, placa, interface CAN e artefato do build remoto, mas exigir checklist físico antes do preflight/execução.
- Na tela Setup, o plano de flash deve mostrar frase específica por placa/método, hash do artefato, UUID esperado, comandos `PLAN`, bloqueios e rollback manual.
- Na tela Setup, `Executar flash` deve exigir a frase gerada no plano; mesmo com a frase, o backend bloqueia quando `PRINTORA_REMOTE_FLASH_MODE=remote` não estiver habilitado.
- Na tela Setup, o histórico de flash deve mostrar placa, método, alvo e status sem senha, token ou caminho de chave privada.
- Na tela Setup, a seção Validação final deve reutilizar SSH e interface CAN, aceitar UUIDs esperados, paths de config/log e executar somente coleta read-only.
- Na tela Setup, a validação final deve exibir status de aceite, checks acionáveis e relatório Markdown sanitizado copiável.
- Na tela Setup, o histórico de validação final deve mostrar data, interface, alvo, resumo e status sem segredo ou caminho de chave privada.

## Estado de UI

- A impressora ativa deve ser preservada no navegador e restaurada ao recarregar a tela quando ainda existir no cadastro.
- A Home operacional deve explicar o risco principal quando o estado for `Nao imprimir` ou `Monitorar`, exibindo causa, evidencia e acao segura.
- A Central de alertas deve consolidar Health Check, Update Manager, checklist pos-update, manutencao e auditoria por impressora com botoes de revalidacao, abertura do diagnostico ou fluxo de update quando aplicavel. Ao abrir, o filtro inicia em `Todas as impressoras`.
- Confirmacoes de decisao devem usar modal proprio do Printora; feedback temporario de sucesso/falha/erro deve usar toast. Dialogos nativos do navegador (`alert`/`confirm`) e banners globais fixos no topo nao devem aparecer na UI operacional.
- A tela Operacao deve ser leitura ao vivo para operador leigo: sem cadastro manual, sem checklist pos-update, sem auditoria tecnica e com graficos/indicadores que se atualizam automaticamente.
- Na tela Operacao, temperaturas devem aparecer em tabela compacta com estado, atual, alvo editavel para heaters suportados e potencia, acompanhadas de um unico grafico combinado de evolucao por sensor/heater.
- Na tela Operacao, extrusor, progresso de impressao, sistema, fans e CAN devem ficar na mesma tela para evitar duplicidade entre menus; o progresso de impressao deve alinhar percentual/rotulo, priorizar `virtual_sdcard.progress` quando disponivel e exibir camada atual/total quando Moonraker/Klipper fornecer esse dado. Sistema, CAN e leituras visuais devem ficar abaixo dos controles operacionais quando nao houver acao direta associada.
- O grafico de temperaturas da Operacao deve acumular leituras ao vivo durante a sessao aberta, desenhar tambem quando houver apenas uma leitura e nao depender exclusivamente de snapshots persistidos para mostrar a curva durante uma impressao.
- Na tela Operacao, acoes protegidas devem ficar agrupadas em paineis operacionais estilo Mainsail: Toolhead, Extrusor e Miscellaneous; Toolhead, Extrusor, fans controlaveis, output pins de luz como Caselight e indicadores LED devem ficar nessa area, limites de maquina devem ficar junto do bloco Impressao no topo, e alvos de temperatura devem ficar no painel principal de temperaturas para evitar duplicidade. Fans automaticos (`heater_fan`/`controller_fan`) devem aparecer como leitura quando Moonraker retornar o valor, sem controle manual.
- Em Miscellaneous, quando o Moonraker ou o agente nao retornar a lista dinamica/valores de `fan`, `output_pin` e LED, a tela deve diferenciar ausencia real de dispositivos de falha de coleta, exibindo estado acionavel sem inventar percentual.
- Acoes leves da Operacao (`set_fan`, `set_output_pin`, `set_led`) nao devem exigir autenticacao reforcada e podem ser usadas durante impressao; movimentos, aquecimento e limites continuam protegidos.
- Formularios tecnicos de CAN devem ficar fora da tela Operacao.
- Checklist pos-update deve aparecer na tela Atualizacoes.
- Na tela Atualizacoes, `Atualizar tudo` aparece somente quando houver mais de um componente atualizavel.
- Na tela Atualizacoes, `Atualizar` de componente usa icone distinto de `Reanalisar` e visual secundario alinhado ao botao `Marcar feita` da Manutencao.
- Na tela Atualizacoes, componentes de risco alto como `klipper` e toolchanger mantem a acao `Atualizar`, exibem aviso antes do update e exigem confirmacao literal no modal; o backend tambem bloqueia a chamada sem confirmacao.
- Na tela Atualizacoes, quando o Moonraker informar `rollback_version`, o card exibe rollback do componente com confirmacao literal.
- Na tela Atualizacoes, qualquer componente do Update Manager com pendencia ou aviso pode ter a versao atual silenciada apos confirmacao; o card permanece visivel com `Reanalisar`, `Atualizar`, `Rollback` quando existir e `Reativar alerta`.
- A acao de silenciar/reativar alerta deve mostrar estado de execucao no proprio card e no botao acionado, sem depender apenas de disabled global.
- Silenciar ou reativar alerta usa a versao ja exibida no card e nao deve consultar o Moonraker durante a gravacao do silencio.
- Versoes silenciadas nao contam na Home, topbar, Central de alertas, Health Check, Checklist pos-update, Auditoria ou Relatorios; se a versao remota, pacote, atraso, warning ou anomalia mudar, o alerta volta automaticamente.
- Na tela Atualizacoes, componentes com update pendente aparecem antes dos demais; entre pendentes, os mais atrasados por commits/pacotes ficam acima, preservando a ordem original quando empatar ou quando tudo estiver atualizado.
- Na tela Atualizacoes, os componentes do Update Manager usam cards responsivos em duas ou tres colunas quando houver largura suficiente, e o checklist pos-update ocupa a largura total com duas colunas em telas medias/grandes.
- Na tela Atualizacoes, componentes com origem Git exibem um icone de informacao no titulo para abrir o repositorio do componente em nova aba quando o Moonraker informar `remote_url` ou `owner/repo_name`.
- Ao fechar o modal de update concluido ou revalidado, a tela Atualizacoes deve recarregar status do Update Manager, health, checklist, operacao e auditoria da impressora ativa.
- Auditoria e diagnostico avancado do host devem ficar em telas de diagnostico/configuracao, nao como conteudo principal do Monitoramento.
- Na tela Firmware, a visao principal deve ser guiada pela impressora selecionada: mostrar versoes de Klipper/Moonraker, MCUs/placas detectadas pelo Klipper, placas ja associadas ao modelo fisico e proximas acoes seguras de `.config` e build.
- Na tela Firmware, componentes/plugins do Update Manager nao aparecem no conteudo principal; eles pertencem a Atualizacoes ou diagnostico, nao ao inventario de firmware.
- Na tela Firmware, presets e catalogos genericos nao devem aparecer como lista principal. O usuario deve ver primeiro o que existe na impressora e associar cada MCU detectada ao modelo fisico real uma unica vez.
- Na tela Firmware, uma MCU ja associada nao deve continuar aparecendo como detectada pendente; a deduplicacao deve considerar UUID CAN, nome exibido pelo Klipper e MCU.
- Na tela Firmware, o campo Modelo fisico deve permitir escolher qualquer preset conhecido, mesmo quando houver sugestoes do catalogo.
- Na tela Firmware, o fluxo principal deve ser sequencial e simples: verificar placas pelo agente, associar modelo fisico quando necessario, visualizar `.config`, validar build, preparar dry-run e executar build pelo agente somente com gate do backend.
- A referencia tecnica para catalogo CAN, presets e procedimentos de update/flash e o guia Esoterical CANBus (`https://canbus.esoterical.online/`); o catalogo local deve ser estruturado em dados do projeto e usado para orientar a tela sem depender de navegacao externa em runtime.
- Na tela Firmware, cada MCU/placa da impressora ativa pode exibir sugestoes compactas do catalogo local com link do guia, status de preset local e aviso quando faltar preset; o catalogo completo nao vira lista principal nem aciona build, flash ou update.
- Na tela Firmware, o PKG-33 mostra por placa da impressora ativa se o preset esta completo, faltando dados ou invalido, alem das acoes seguras de gerar/visualizar `.config`, validar build, preparar build dry-run e ver artefatos/logs quando houver build concluido; build real permanece bloqueado pelo backend por padrao e flash automatico nao aparece neste pacote.
- A tela Firmware do PKG-33 nao deve renderizar botoes de flash, SSH, restart ou update; referências de catálogo permanecem apenas como orientação técnica.
- Na tela Firmware, estados de carregamento, erro e vazio devem deixar claro se a tela esta lendo Moonraker, se falhou a leitura ou se ainda nao ha MCU lida para a impressora selecionada.
- Checklist manual do PKG-33 na tela Firmware: abrir com impressora offline e confirmar erro de Moonraker sem esconder o resumo local do catalogo; abrir com impressora online e confirmar MCUs/placas detectadas e cadastradas primeiro; associar modelo fisico sugerido quando existir; confirmar badges de preset completo, faltando dados ou preset ausente; gerar preview de `.config`; preparar dry-run; confirmar artefato/log quando existir build local controlado; confirmar ausencia de botoes/acoes de flash, SSH, restart e update.
- Em Comunidades > Projetos, o fluxo mostra lista de projetos compartilhados, filtros e ação para compartilhar projeto existente ou abrir/criar projeto em `Projetos de impressão`; não há cadastro principal de arquivo, upload direto, fatiamento ou envio operacional dentro da comunidade.
- O painel de armazenamento pertence a `Projetos de impressão > Meus projetos`. Ele deve mostrar uso, cota, espaço disponível, quantidade de arquivos, candidatos de retenção, custo estimado e ação de revisão supervisionada. A revisão não deve prometer exclusão automática nem usar rótulos internos de pacote/lote.
- Em telas responsivas de projetos, formulários, painel de armazenamento e cards de arquivo devem quebrar linha sem sobrepor texto, botões ou métricas.
- Na tela Administração, `Fatiamento controlado` mostra apenas verificação read-only da engine CLI, status, versão, modo dry-run e instrução de instalação. Essa tela não executa fatiamento real, não embute UI de fatiador e não mistura CRUD de projeto, perfil ou impressora.
- O painel de fatiamento controlado deve usar botão com ícone de recarregar para verificação, métricas compactas e resultado acionável. Paths exibidos devem vir sanitizados pelo backend.
- Na tela Administração, `Pipeline de fatiamento` não cria job diário. Ele mostra diagnóstico/fallback de jobs existentes, status da fila, artefatos técnicos e links para abrir `Projetos de impressão`, sem formulário principal de modelo/projeto, perfil ou impressora.
- Implementação atual de Administração: criação de job, preflight novo, salvar G-code e iniciar impressão foram rebaixados da tela administrativa; permanecem leitura, atualização remota pendente, cancelamento de job existente e rollback seguro de arquivo salvo.
- O formulário do pipeline deve quebrar responsivamente em duas colunas e uma coluna no mobile, mantendo botões, labels e campos sem sobreposição.
- Na tela Administração, preflight e entrega aparecem somente como diagnóstico/fallback de job existente. As ações principais de preflight, salvar G-code e enviar pertencem ao fluxo do projeto.
- Enquanto o preflight remoto estiver pendente, a UI deve oferecer atualização explícita sem prometer envio ou impressão.
- `Projetos de impressão > Meus projetos` é a área diária de criação e gestão pessoal de projetos. A tela permite criar projeto sem comunidade, escolher visibilidade privada/não listada/pública, informar licença/tags, enviar STL/3MF/ZIP por função do arquivo, adicionar referência externa e arquivar logicamente.
- Arquivos do projeto mostram função, tipo, estado de validação e estado de fatiamento: elegível, bloqueado, sem arquivo local, em validação ou falha no arquivo.
- Link externo aparece como referência sem arquivo local e nunca como hospedado; a tela deve deixar visível que ele não é fatiável enquanto não houver arquivo validado.
- O painel de armazenamento pessoal em `Meus projetos` mostra uso, cota, arquivos e proporção de uso. Retenção/custo detalhado pode evoluir sobre a política existente, sem prometer exclusão automática.
- Comunidades continuam como descoberta/compartilhamento de projetos. Upload direto de arquivo em comunidade não é fluxo principal e não deve substituir criação em `Projetos de impressão`.
- `Projetos de impressão > Meus projetos > Publicação e vitrine` permite configurar visibilidade, classificação comercial, preço preparado, condição comercial e transparência. Conteúdo premium/patrocinado deve mostrar que cobrança real não está ativa neste fluxo.
- A vitrine pública só exibe projetos aprovados. Patrocinado deve aparecer como promoção identificada, nunca como recomendação técnica neutra. Premium deve ser distinguido de gratuito/comunitário.
- `Projetos de impressão > Meus projetos > Fatiamento` permite selecionar arquivos locais fatiáveis do projeto, escolher impressora, qualidade e perfil/material, criar job e ver jobs do projeto com status e snapshot. Link externo sem arquivo local validado aparece desabilitado e não entra na seleção.
- Quando a engine de fatiamento estiver indisponível, a tela deve bloquear criação de job e apontar Administração como local de configuração/diagnóstico.
- O mesmo painel mostra preflight, entrega e histórico por projeto: `Salvar G-code`, `Enviar`, confirmação textual obrigatória para iniciar impressão, status da entrega, rollback seguro de arquivo salvo e feedback privado/público sanitizado.
- Histórico público no contexto do projeto nunca deve exibir impressora privada, agente, Moonraker, token, IP, path, organização ou permissão.

## Pendencias de mapeamento

- Definir rotas dedicadas somente se a SPA deixar de usar `section` por query/hash.
- Separar fluxos de listagem, detalhe, cadastro e edicao quando houver CRUD real fora dos modais existentes.

## Operação Da Plataforma Planejada

Os pacotes arquiteturais não devem expor nomes internos, tecnologia ou comandos
perigosos para usuários comuns. As superfícies abaixo pertencem à Administração
e só entram quando o respectivo backend estiver operacional:

- `Administração > Saúde da plataforma`: instâncias, readiness, versão ativa,
  filas, storage, banco, cache, busca, capacidade e incidentes, sem segredos;
- `Administração > Transição de dados`: progresso read-only, watermark,
  divergências, checksums e gate de cutover; nenhuma exclusão direta pela tela;
- `Administração > Jobs`: filtros, detalhe, tentativas, erro sanitizado,
  dead-letter e reprocessamento idempotente com confirmação;
- `Administração > Armazenamento`: uso/cota, objetos órfãos, integridade,
  quarentena, retenção e restore supervisionado;
- `Administração > Busca`: saúde, atraso do índice, divergência e rebuild seguro;
- `Administração > Finanças`: pedidos, ledger, reconciliação, disputa e repasse,
  separados em lista, detalhe e ações autorizadas;
- `Administração > Produção`: cotações, ordens, qualidade, logística e incidentes,
  com lista/detalhe e transições explícitas;
- `Administração > Recuperação`: backups, restores ensaiados, RPO/RTO e evidência,
  sem botão destrutivo genérico;
- `Administração > Dados e modelos`: pipelines, versões, canários, drift e
  rollback de ML, sem acesso direto ao banco transacional.

Todas exigem desktop/mobile, teclado, leitor de tela, estados vazio/loading/
erro/degradado, permissão por ação, confirmação forte e auditoria sanitizada.

## Administração > Finanças

- rota/estado: `?section=finance`;
- acesso sem papel financeiro mostra estado restrito, sem consultar ou revelar
  pedido, saldo, ledger ou evidência;
- `Visão geral` mostra contagens e prontidão, deixando explícito que dinheiro real
  está indisponível;
- `Pedidos e pagamentos`, `Ledger`, `Reconciliação`, `Disputas` e `Repasses` são
  estados separados com lista e painel de detalhe; nenhuma edição direta do
  ledger existe;
- operações sensíveis exigem papel específico e autenticação reforçada de uso
  único; solicitar, aprovar e executar repasse pertencem a atores diferentes;
- estados loading, vazio, erro/acesso negado e sucesso são responsivos e operáveis
  por teclado. A tela usa somente o client HTTP compartilhado;
- o container ocupa as 12 colunas do workspace em desktop e toda a largura
  disponível em mobile; o gate E2E bloqueia regressão de colapso lateral.

## Administração > Fabricação

- rota/estado: `?section=manufacturing`;
- acesso exige papel explícito de produção, qualidade, logística ou segurança;
- `Ordens` e `Incidentes e recall` são listas separadas com painel de detalhe;
- endereço cifrado, token de tracking, evidência privada e snapshots de arquivo
  não são retornados pelo overview nem exibidos na tela;
- transições permanecem nas APIs autorizadas e nunca enviam comando direto à
  impressora física; estados vazio, loading, acesso negado e detalhe são responsivos;
- o container ocupa toda a largura do workspace. Em desktop, lista e detalhe
  permanecem em duas colunas sem sobreposição; em mobile, empilham em uma coluna.

## Administração > Dados e inteligência

- rota/estado: `?section=data-intelligence`;
- acesso exige conta administrativa e não revela eventos, modelos ou derivados
  quando a permissão é negada;
- `Dashboard` mostra pipeline, impacto, temporários, retenção e o contrato de
  isolamento sem consultar tabelas transacionais;
- `Moderação` separa lista e detalhe, informa idioma/confiança/rótulos e oferece
  decisão humana; recurso permanece uma etapa independente e revisável;
- `Modelos` separa registro e detalhe com owner, versão, dataset/licença,
  canário, drift, fallback e kill switch;
- `Lineage` separa derivações e detalhe de proveniência e informa replays
  idempotentes;
- estados loading, vazio, acesso negado e detalhe são responsivos. A tela não
  recebe contexto bruto de moderação, subject key, segredo ou payload de OLTP;
- o container ocupa toda a largura do workspace para impedir que dashboard,
  tabelas e detalhes sejam comprimidos na primeira coluna da grade global.

## Boundary De Preferências Locais

Tema e progresso do guia de setup preservam o comportamento visual atual, mas
pages/components não acessam mais `localStorage` diretamente. Leitura, escrita,
parse inválido e limpeza ficam no client de preferências locais; o gate de
layering React impede regressão para acesso direto de HTTP/storage na UI.

## Responsividade E Informação Para O Usuário

- As catorze rotas autenticadas acessíveis diretamente devem permanecer
  operáveis em 320, 390, 768, 1024 e 1440 px, sem conteúdo cortado fora de um
  container de rolagem explícito.
- Perfil público, impressora pública e comunidade pública seguem a mesma matriz.
  As seis abas da comunidade devem abrir sem revelar URL interna ou dados
  operacionais da impressora.
- O cabeçalho e as nove abas do detalhe da impressora devem permanecer dentro
  do viewport. Cada aba precisa ser visível, acionável e indicar sua seleção.
- Modais de alerta, cadastro, manutenção, relatório, backup e restore precisam
  permanecer operáveis no viewport mínimo; rolagem vertical interna é permitida,
  mas conteúdo ou ação não podem escapar horizontalmente.
- A tabela global de agentes usa linhas tabulares somente quando há largura
  útil. Em larguras menores, cada agente vira um cartão com os rótulos Agente,
  Impressora, Status, Versão, Último contato e Ações.
- URL interna do Moonraker, plataforma do host, linha de comando, caminhos,
  consumo bruto de logs/API, linguagem e tecnologia de banco não aparecem nas
  telas operacionais. Dados técnicos permanecem apenas em cadastro, diagnóstico
  ou relatório explicitamente técnico quando forem necessários para a ação.
- O administrador máximo configurado pode abrir os overviews de Finanças e
  Fabricação para teste e supervisão. Ações financeiras ou produtivas sensíveis
  continuam exigindo o papel específico e, quando aplicável, autenticação
  reforçada; acesso máximo não elimina separação de funções.
