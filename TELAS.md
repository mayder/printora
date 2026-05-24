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
| Operacao | `operation` | `/?section=operation`, `/#operation` | `frontend/src/screens/OperationScreen.tsx` | Painel operacional read-only, temperaturas, toolhead, extrusor, fans e acoes protegidas | Exige impressora ativa online | existente |
| Monitoramento | `monitoring` | `/?section=monitoring`, `/#monitoring` | `frontend/src/screens/MonitoringScreen.tsx` | Telemetria ao vivo de temperatura, progresso, sistema, fans e CAN sem formularios operacionais | Exige impressora ativa online | existente |
| Atualizacoes | `updates` | `/?section=updates`, `/#updates` | `frontend/src/screens/UpdatesScreen.tsx` | Update Manager da impressora, checklist pos-update, update com confirmacao, progresso e historico | Exige impressora ativa online | existente |
| Calibracao | `calibration` | `/?section=calibration`, `/#calibration` | `frontend/src/screens/CalibrationScreen.tsx` | Z-offset, wizard manual, registro de resultados e sequencia de calibracao | Exige impressora ativa online | existente |
| Testes | `tests` | `/?section=tests`, `/#tests` | `frontend/src/screens/TestsScreen.tsx` | Centro de testes Voron, ajuda, preflight e execucao com confirmacao presencial | Exige impressora ativa online | existente |
| Firmware | `firmware` | `/?section=firmware`, `/#firmware` | `frontend/src/screens/FirmwareScreen.tsx` | Placas, presets, dry-run, preflight, build, flash e plano de recuperacao | Exige impressora ativa online | existente |
| Manutencao | `maintenance` | `/?section=maintenance`, `/#maintenance` | `frontend/src/screens/MaintenanceScreen.tsx` | Tarefas preventivas, diario e horas de impressao por impressora | Exige impressora ativa local | existente |
| Relatorios | `reports` | `/?section=reports`, `/#reports` | `frontend/src/screens/ReportsScreen.tsx` | Health, relatorio sanitizado, backups, snapshots, diffs, Moonraker, Klipper e auditoria read-only da impressora | Exige impressora ativa online | existente |
| Configuracoes | `settings` | `/?section=settings`, `/#settings` | `frontend/src/screens/SettingsScreen.tsx` | Registro tecnico CAN, releases, update/rollback do Printora e diagnostico avancado do host | Nao exige impressora ativa | existente |

## Componentes e modais por dominio

| Dominio | Arquivo | Responsabilidade |
|---|---|---|
| Composicao de modais | `frontend/src/components/modals/AppModals.tsx` | Monta os modais por dominio sem conter conteudo de tela |
| Alertas | `frontend/src/components/modals/AlertCenterModal.tsx` | Central de alertas consolidada |
| Impressoras | `frontend/src/components/modals/PrinterModal.tsx` | Cadastro, edicao, descoberta e teste de conexao |
| Atualizacoes do Printora | `frontend/src/components/modals/SelfUpdateModal.tsx` | Plano, aplicacao e rollback do proprio Printora |
| Atualizacoes da impressora | `frontend/src/components/modals/UpdateDialogModal.tsx` | Confirmacao e progresso de update via Moonraker |
| Manutencao concluida | `frontend/src/components/modals/MaintenanceDoneModal.tsx` | Conclusao de tarefa preventiva e ajuste do proximo lembrete |
| Manutencao livre | `frontend/src/components/modals/MaintenanceFreeModal.tsx` | Registro livre de manutencao, falha, ajuste ou nota |
| Calibracao ajuda | `frontend/src/components/modals/CalibrationHelpModal.tsx` | Ajuda operacional de um teste de calibracao |
| Calibracao execucao | `frontend/src/components/modals/CalibrationExecuteModal.tsx` | Preflight e confirmacao presencial para envio de G-code |
| Calibracao resultado | `frontend/src/components/modals/CalibrationResultModal.tsx` | Historico e registro manual de resultado de calibracao |

## Hooks e services

| Dominio | Hook | Service |
|---|---|---|
| Shell/navegacao | `frontend/src/hooks/domains/useAppShell.ts` | Nao acessa API |
| Impressoras | `frontend/src/hooks/domains/usePrinters.ts` | `frontend/src/services/printerApi.ts` |
| Operacao | `frontend/src/hooks/domains/useOperation.ts` | `frontend/src/services/operationApi.ts` |
| Atualizacoes da impressora | `frontend/src/hooks/domains/useUpdates.ts` | `frontend/src/services/updatesApi.ts` |
| Calibracao e Z-offset | `frontend/src/hooks/domains/useCalibration.ts` | `frontend/src/services/calibrationApi.ts`, `frontend/src/services/zOffsetApi.ts` |
| Firmware e plugins | `frontend/src/hooks/domains/useFirmware.ts` | `frontend/src/services/firmwareApi.ts`, `frontend/src/services/pluginApi.ts` |
| Manutencao | `frontend/src/hooks/domains/useMaintenance.ts` | `frontend/src/services/maintenanceApi.ts` |
| Relatorios, snapshots e backups | `frontend/src/hooks/domains/useReports.ts` | `frontend/src/services/reportsApi.ts`, `frontend/src/services/backupApi.ts`, `frontend/src/services/printerApi.ts` |
| CAN e diagnostico | `frontend/src/hooks/domains/useSettings.ts` | `frontend/src/services/canApi.ts`, `frontend/src/services/diagnosticsApi.ts`, `frontend/src/services/printerApi.ts` |
| Updates do Printora | `frontend/src/hooks/domains/useSelfUpdate.ts` | `frontend/src/services/systemApi.ts` |

## Distribuicao de conteudo

- Backups ficam em `reports`, junto de snapshots, comparacoes, relatorio sanitizado e evidencias diagnosticas.
- Auditoria read-only da impressora fica em `reports`.
- Diagnostico avancado do host fica em `settings`, colapsado e com ajuda contextual por modal.
- CAN de monitoramento fica em `monitoring` como leitura operacional; registro tecnico, parser e comparacao manual ficam em `settings`, colapsados e com ajuda contextual por modal.
- Updates da impressora ficam em `updates`; updates do proprio Printora ficam em `settings`.

## Estado de UI

- A impressora ativa deve ser preservada no navegador e restaurada ao recarregar a tela quando ainda existir no cadastro.
- A Home operacional deve explicar o risco principal quando o estado for `Nao imprimir` ou `Monitorar`, exibindo causa, evidencia e acao segura.
- A Central de alertas deve consolidar Health Check, Update Manager, checklist pos-update e auditoria com botoes de revalidacao, abertura do diagnostico ou fluxo de update quando aplicavel.
- A tela Monitoramento deve ser leitura ao vivo para operador leigo: sem cadastro manual, sem checklist pos-update, sem auditoria tecnica e com graficos/indicadores que se atualizam automaticamente.
- Formularios tecnicos de CAN devem ficar fora da tela Monitoramento.
- Checklist pos-update deve aparecer na tela Atualizacoes.
- Na tela Atualizacoes, `Atualizar tudo` aparece somente quando houver mais de um componente atualizavel.
- Na tela Atualizacoes, componentes com update pendente aparecem antes dos demais; entre pendentes, os mais atrasados por commits/pacotes ficam acima, preservando a ordem original quando empatar ou quando tudo estiver atualizado.
- Na tela Atualizacoes, os componentes do Update Manager usam cards responsivos em duas ou tres colunas quando houver largura suficiente, e o checklist pos-update ocupa a largura total com duas colunas em telas medias/grandes.
- Ao fechar o modal de update concluido ou revalidado, a tela Atualizacoes deve recarregar status do Update Manager, health, checklist, operacao e auditoria da impressora ativa.
- Auditoria e diagnostico avancado do host devem ficar em telas de diagnostico/configuracao, nao como conteudo principal do Monitoramento.

## Pendencias de mapeamento

- Definir rotas dedicadas somente se a SPA deixar de usar `section` por query/hash.
- Separar fluxos de listagem, detalhe, cadastro e edicao quando houver CRUD real fora dos modais existentes.
