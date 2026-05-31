# TELAS.md

Inventario operacional de telas, rotas, estados e regras de UI do Printora.

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
- Secoes que exigem impressora online sao ocultadas da navegacao quando a leitura de health da impressora ativa confirma Moonraker offline; se o usuario estiver nelas nesse momento, a SPA volta para `overview`.
- Durante o carregamento inicial, secoes que exigem impressora online permanecem ocultas ate o health confirmar Moonraker online.
- Com Moonraker offline, a Central de alertas exibe apenas o alerta de offline/conexao; pendencias que dependem da impressora ligada ou de snapshot antigo nao contam como alertas ativos atuais.
- Enquanto a impressora ativa estiver offline, a SPA revalida status e health a cada 60 segundos para liberar as secoes online quando Moonraker voltar.

## Telas atuais

| Tela | Secao | Entrada | Arquivo | Objetivo | Dependencia de impressora | Status |
|---|---|---|---|---|---|---|
| Visao geral | `overview` | `/`, `/?section=overview`, `/#overview` | `frontend/src/screens/OverviewScreen.tsx` | Dashboard geral da frota e da impressora selecionada, com risco principal, horas acumuladas e atalhos seguros | Opcional | existente |
| Impressoras | `printers` | `/?section=printers`, `/#printers` | `frontend/src/screens/PrintersScreen.tsx` | Cadastro, descoberta, teste de conexao e selecao da impressora ativa | Nao exige impressora ativa | existente |
| Setup | `setup` | `/?section=setup`, `/#setup` | `frontend/src/screens/SetupScreen.tsx` | Receita guiada para preparar a Pi, habilitar SSH, validar ambiente, configurar CAN/U2C, gerar firmware, executar flash supervisionado, validar base Klipper e cadastrar a impressora | Nao exige impressora ativa | existente |
| Operacao | `monitoring` | `/?section=monitoring`, `/#monitoring`; legado `/?section=operation` redireciona para esta tela | `frontend/src/screens/MonitoringScreen.tsx` + `frontend/src/MonitoringDashboard.tsx` | Operacao ao vivo com temperaturas, toolhead, extrusor, progresso, sistema, fans, CAN e acoes protegidas | Exige impressora ativa online | existente |
| Atualizacoes | `updates` | `/?section=updates`, `/#updates` | `frontend/src/screens/UpdatesScreen.tsx` | Update Manager da impressora, checklist pos-update, update com confirmacao, progresso e historico | Exige impressora ativa online | existente |
| Calibracao | `tests` | `/?section=tests`, `/#tests`; legado `/?section=calibration` redireciona para `tests` | `frontend/src/screens/TestsScreen.tsx` | Centro de calibracao Voron em cards numerados por sequencia, busca, filtros por tipo/uso, ajuda expandida, preflight, execucao com confirmacao presencial e perfil Z aprovado | Exige impressora ativa online | existente |
| Firmware | `firmware` | `/?section=firmware`, `/#firmware` | `frontend/src/screens/FirmwareScreen.tsx` | Inventario de MCUs/placas detectadas, associacao ao modelo fisico, build, flash planejado e referencia CANBus | Exige impressora ativa; leitura ao vivo depende de Moonraker online | existente |
| Manutencao | `maintenance` | `/?section=maintenance`, `/#maintenance` | `frontend/src/screens/MaintenanceScreen.tsx` | Tarefas preventivas, diario e horas de impressao por impressora | Exige impressora ativa local | existente |
| Relatorios | `reports` | `/?section=reports`, `/#reports` | `frontend/src/screens/ReportsScreen.tsx` + `frontend/src/screens/reports/*` | Relatorio leigo da impressora com decisao de imprimir, motivo, metricas explicadas, diagnostico de rede/DNS/SSH read-only, snapshots, relatorio sanitizado, backup/restore seguro e auditoria read-only | Exige impressora ativa online | existente |
| Configuracoes | `settings` | `/?section=settings`, `/#settings` | `frontend/src/screens/SettingsScreen.tsx` | Registro tecnico CAN, releases, update/rollback do Printora, diagnostico da instalacao com energia/throttling Raspberry e diagnostico avancado do host | Nao exige impressora ativa | existente |
| Sobre | `about` | `/?section=about`, `/#about` | `frontend/src/screens/AboutScreen.tsx` | Apresentacao do autor, motivacao do projeto, funcionalidades, roadmap publico, redes sociais e identidade visual | Nao exige impressora ativa | existente |
| Licenca | `license` | `/?section=license`, `/#license` | `frontend/src/screens/LicenseScreen.tsx` | Resumo de licenca open source, limites de garantia e responsabilidade operacional | Nao exige impressora ativa | existente |

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
| Calibracao execucao | `frontend/src/components/modals/CalibrationExecuteModal.tsx` | Preflight e confirmacao presencial para envio de G-code |
| Calibracao resultado | `frontend/src/components/modals/CalibrationResultModal.tsx` | Historico e registro manual de resultado de calibracao |

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
| Relatorios, snapshots e backups | `frontend/src/hooks/domains/useReports.ts` | `frontend/src/services/reportsApi.ts`, `frontend/src/services/backupApi.ts`, `frontend/src/services/printerApi.ts` |
| CAN e diagnostico | `frontend/src/hooks/domains/useSettings.ts` | `frontend/src/services/canApi.ts`, `frontend/src/services/diagnosticsApi.ts`, `frontend/src/services/printerApi.ts`, `frontend/src/services/systemApi.ts` |
| Updates do Printora | `frontend/src/hooks/domains/useSelfUpdate.ts` | `frontend/src/services/systemApi.ts` |

## Distribuicao de conteudo

- Backups ficam em `reports`, junto de snapshots, comparacoes, relatorio sanitizado e evidencias diagnosticas.
- Auditoria read-only da impressora fica em `reports`.
- Na tela Relatorios, a leitura principal deve explicar para usuario leigo se pode imprimir, por que nao imprimir quando houver bloqueio e qual acao segura seguir.
- Na tela Relatorios, latencia deve ser apresentada como comunicacao Printora-Moonraker na rede local, nao como falha generica de API.
- Na tela Relatorios, lentidao de comunicacao Printora-Moonraker deve ser monitoramento, nao bloqueio de impressao, quando Klipper e Moonraker estao saudaveis na Raspberry.
- Na tela Relatorios, quando houver SSH configurado para a impressora, o diagnostico de rede pode executar somente comandos read-only para comparar DNS local do Android, URL cadastrada, IP direto e Moonraker local na Raspberry.
- Na tela Relatorios, formularios tecnicos de backup, comparacao, restore e relatorio sanitizado devem abrir em modal; a tela principal e leitura diagnostica, nao cadastro.
- Diagnostico avancado do host fica em `settings`, colapsado e com ajuda contextual por modal.
- Diagnostico da instalacao fica em `settings`, colapsado, com refresh manual e acao para copiar um resumo tecnico sanitizado.
- CAN de operacao fica em `monitoring` como leitura operacional; registro tecnico, parser e comparacao manual ficam em `settings`, colapsados e com ajuda contextual por modal.
- Updates da impressora ficam em `updates`; updates do proprio Printora ficam em `settings`.
- Na tela Configuracoes, `Releases anteriores` e `Historico de updates` ficam como blocos colapsados lado a lado, no mesmo padrao dos blocos tecnicos.
- No `Historico de updates`, a acao `Reconciliar travados` deve revalidar runs orfaos antigos sem apagar historico e liberar novo update quando nao houver execucao real em andamento.
- A tela Sobre deve ser acessivel pelo icone de informacao no topo em todas as telas; por enquanto nao aparece no menu lateral.
- A tela Sobre deve promover o autor, exibir LinkedIn, Instagram, GitHub do projeto, motivacao, funcionalidades atuais, aviso de teste, versao sem custo, roadmap online futuro e opcoes de marca.
- A tela Licenca deve ser acessivel a partir da tela Sobre e deixar claro o uso open source, ausencia de garantia e responsabilidade do usuario em operacoes criticas.
- A tela Conta deve concentrar autenticação cloud, cadastro, sessão, organizações opcionais, 2FA, step-up auth e credenciais de agente.
- Usuário anônimo deve ver somente o shell mínimo de autenticação, sem menu lateral, seletor de impressora, alertas, telas internas ou dados operacionais.
- Na tela Conta, email e senha são obrigatórios no cadastro; nome, WhatsApp, Telegram e demais contatos são opcionais e não bloqueiam a criação da conta.
- Na tela Conta, organização não é obrigatória para uso individual; quando existir, a UI permite criar organização e vincular usuários com papel `admin` ou `operator`.
- Na tela Conta, o setup de 2FA deve exibir segredo/URI, validar código antes de ativar e exigir código atual para desativar quando 2FA estiver ativo.
- Na tela Conta, autenticação reforçada gera autorização curta para ações críticas; usuários com 2FA usam código, usuários sem 2FA usam senha.
- Na tela Conta, credencial de agente completa aparece somente no momento de criação; depois a UI mostra apenas prefixo, identificação e status.
- Na tela Impressoras, o bloco de pareamento do agente permite gerar token curto para a impressora selecionada, copiar o token uma única vez, listar tokens por prefixo/status, revogar tokens ativos, listar agentes pareados, revogar agente e rotacionar credencial.
- Na tela Impressoras, o bloco de instalação assistida do agente gera comando de preflight, comando de instalação com token curto, comando de uninstall e mostra validação pós-instalação por agente ativo, versão e heartbeat.
- Na tela Impressoras, o bloco de operação remota segura mostra ações mutáveis permitidas por criticidade, risco e rollback, cria preflight remoto, exige confirmação textual exata, cria execução remota somente após preflight aprovado e permite cancelar jobs pendentes.
- Na tela Impressoras, credencial operacional completa aparece somente no momento de troca/rotação; depois a UI mostra apenas prefixo, status, plataforma e último contato.
- A tela Setup deve ficar disponivel sem impressora ativa, pois seu objetivo e preparar uma Pi antes do cadastro final da impressora.
- Na tela Setup, o primeiro bloco deve deixar claro que placa virgem sem SO/rede/SSH nao pode ser acessada por SSH; a preparacao de mídia/boot e etapa manual ou futura.
- Na tela Setup, o topo deve exibir uma receita sequencial para usuario leigo, com progresso, etapas manuais marcaveis, passos bloqueados/prontos/feitos e abertura de cada etapa em modal.
- Na tela Setup, a receita deve seguir a ordem: gravar sistema operacional, conectar rede, ativar SSH, informar acesso, validar Pi, configurar CAN/U2C, gerar firmware, conferir cabeamento, executar flash supervisionado, validar base Klipper e cadastrar a impressora.
- Na tela Setup, formulários técnicos, resultados, planos, histórico e orientações detalhadas não devem ficar empilhados na tela principal; eles abrem no modal da etapa correspondente.
- Na tela Setup, cada modal deve funcionar como receita de bolo para usuário leigo, explicando opções, ordem de execução, sinais de sucesso, riscos comuns e fontes oficiais quando houver download/instalação externa.
- Na tela Setup, quando a receita estiver concluída e a impressora cadastrada, a preparação deve ficar recolhida e a tela deve mostrar apenas o estado final com acesso para Impressoras e opção de reabrir a receita.
- Na tela Setup, a UI deve aceitar host, porta, usuario, metodo de autenticacao por agente/chave e timeout, sem campo de senha.
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
- A Central de alertas deve consolidar Health Check, Update Manager, checklist pos-update e auditoria com botoes de revalidacao, abertura do diagnostico ou fluxo de update quando aplicavel.
- Confirmacoes de decisao devem usar modal proprio do Printora; feedback temporario de sucesso/falha deve usar toast. Dialogos nativos do navegador (`alert`/`confirm`) nao devem aparecer na UI operacional.
- A tela Operacao deve ser leitura ao vivo para operador leigo: sem cadastro manual, sem checklist pos-update, sem auditoria tecnica e com graficos/indicadores que se atualizam automaticamente.
- Na tela Operacao, temperaturas devem aparecer em tabela compacta com estado, atual, alvo editavel para heaters suportados e potencia, acompanhadas de um unico grafico combinado de evolucao por sensor/heater.
- Na tela Operacao, extrusor, progresso de impressao, sistema, fans e CAN devem ficar na mesma tela para evitar duplicidade entre menus; o progresso de impressao deve alinhar percentual/rotulo e exibir camada atual/total quando Moonraker/Klipper fornecer esse dado. Sistema, CAN e leituras visuais devem ficar abaixo dos controles operacionais quando nao houver acao direta associada.
- Na tela Operacao, acoes protegidas devem ficar agrupadas em paineis operacionais estilo Mainsail: Toolhead, Extrusor e Miscellaneous; Toolhead, Extrusor e fans devem ser operaveis nessa area, limites de maquina devem ficar junto do bloco Impressao no topo, e alvos de temperatura devem ficar no painel principal de temperaturas para evitar duplicidade.
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
- Na tela Firmware, o fluxo principal deve ser sequencial e simples: verificar placas, associar modelo fisico quando necessario, visualizar `.config`, validar build, preparar dry-run e executar build local somente com gate do backend.
- A referencia tecnica para catalogo CAN, presets e procedimentos de update/flash e o guia Esoterical CANBus (`https://canbus.esoterical.online/`); o catalogo local deve ser estruturado em dados do projeto e usado para orientar a tela sem depender de navegacao externa em runtime.
- Na tela Firmware, cada MCU/placa da impressora ativa pode exibir sugestoes compactas do catalogo local com link do guia, status de preset local e aviso quando faltar preset; o catalogo completo nao vira lista principal nem aciona build, flash ou update.
- Na tela Firmware, o PKG-33 mostra por placa da impressora ativa se o preset esta completo, faltando dados ou invalido, alem das acoes seguras de gerar/visualizar `.config`, validar build, preparar build dry-run e ver artefatos/logs quando houver build concluido; build real permanece bloqueado pelo backend por padrao e flash automatico nao aparece neste pacote.
- A tela Firmware do PKG-33 nao deve renderizar botoes de flash, SSH, restart ou update; referências de catálogo permanecem apenas como orientação técnica.
- Na tela Firmware, estados de carregamento, erro e vazio devem deixar claro se a tela esta lendo Moonraker, se falhou a leitura ou se ainda nao ha MCU lida para a impressora selecionada.
- Checklist manual do PKG-33 na tela Firmware: abrir com impressora offline e confirmar erro de Moonraker sem esconder o resumo local do catalogo; abrir com impressora online e confirmar MCUs/placas detectadas e cadastradas primeiro; associar modelo fisico sugerido quando existir; confirmar badges de preset completo, faltando dados ou preset ausente; gerar preview de `.config`; preparar dry-run; confirmar artefato/log quando existir build local controlado; confirmar ausencia de botoes/acoes de flash, SSH, restart e update.

## Pendencias de mapeamento

- Definir rotas dedicadas somente se a SPA deixar de usar `section` por query/hash.
- Separar fluxos de listagem, detalhe, cadastro e edicao quando houver CRUD real fora dos modais existentes.
