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

## Telas atuais

| Tela | Modulo | Entrada | Objetivo | Status |
|---|---|---|---|---|
| Home operacional | frontend | `/` | Visao geral da impressora, horas impressas acumuladas e atalhos seguros | existente |
| Auditoria | frontend | a mapear | Diagnostico read-only de ambiente Klipper/Moonraker | existente |
| Snapshots | frontend | a mapear | Captura, listagem e comparacao de snapshots | existente |
| Backups | frontend | a mapear | Plano, historico e operacao segura de backup | existente |
| Manutencao | frontend | a mapear | Diario e manutencao preventiva | existente |
| CAN | frontend | a mapear | Registro e comparacao de estado CAN | existente |
| Z-offset/calibracao | frontend | a mapear | Registro e guia manual de calibracao | existente |
| Firmware | frontend | a mapear | Presets, dry-run, build e fluxo protegido | existente |
| Updates | frontend | a mapear | Releases, update com uma ação principal, progresso sob demanda, historico e rollback do Printora | existente |
| Monitoramento | frontend | a mapear | Telemetria ao vivo de temperatura, progresso, sistema, fans e CAN sem formularios operacionais | existente |

## Estado de UI

- A impressora ativa deve ser preservada no navegador e restaurada ao recarregar a tela quando ainda existir no cadastro.
- A Home operacional deve explicar o risco principal quando o estado for `Nao imprimir` ou `Monitorar`, exibindo causa, evidencia e acao segura.
- A Central de alertas deve consolidar Health Check, Update Manager, checklist pos-update e auditoria com botoes de revalidacao, abertura do diagnostico ou fluxo de update quando aplicavel.
- A tela Monitoramento deve ser leitura ao vivo para operador leigo: sem cadastro manual, sem checklist pos-update, sem auditoria tecnica e com graficos/indicadores que se atualizam automaticamente.
- Formularios tecnicos de CAN devem ficar fora da tela Monitoramento.
- Checklist pos-update deve aparecer na tela Atualizacoes.
- Auditoria e diagnostico avancado do host devem ficar em telas de diagnostico/configuracao, nao como conteudo principal do Monitoramento.

## Pendencias de mapeamento

- Confirmar rotas reais no `frontend/src`.
- Registrar telas por rota com estados e acoes principais.
- Separar fluxos de listagem, detalhe, cadastro e edicao quando houver CRUD real.
