# Printora - Mapa mental completo

## Objetivo

### Produto

- Aplicacao local para operacao segura de impressoras Klipper/Moonraker
- Diagnostico, snapshots, backups, manutencao, CAN, calibracao, firmware e updates
- Conservador por padrao

### IA

- Gastar menos tokens
- Ler arquivos certos
- Respeitar SOLID
- Validar automaticamente o que for possivel
- Evitar documentacao duplicada em monorepo

## Fontes de verdade

### `PATHS.toml`

- Paths oficiais
- Modulos
- Checks
- Ordem de leitura

### `QUALITY_ROADMAP.md`

- Workflow
- SOLID
- Definition of Done
- Pacote/lote
- Commit

### `GOVERNANCA.md`

- Gates
- Riscos
- Rollback
- Seguranca
- Prioridade

### `DEMANDAS.md`

- Backlog
- Pacotes
- Lotes
- Status

## Monorepo

### Raiz

- Governanca transversal
- Backlog transversal
- Testes e criterios
- Runbook
- Decisoes
- Mapas
- Check oficial

### Backend

- Python
- FastAPI
- SQLite
- SQL em `backend/sql`
- Testes em `backend/tests`

### Frontend

- TypeScript
- Vite
- React
- Telas em `frontend/src`
- Testes em `frontend/tests`

## Desenvolvimento

### Pacote

- Quebra em lotes pequenos
- Teste raso por lote
- Teste completo ao fechar
- Review final
- Commit obrigatorio no fechamento

### Bug

- Causa mais provavel
- Hipoteses alternativas
- Menor correcao
- Reteste proporcional ao risco

### UI

- Listagem e filtros
- Detalhamento
- Cadastro
- Edicao
- Formulario pode ser compartilhado
- Evidencia visual quando possivel

## Qualidade

### SOLID

- Responsabilidade unica
- Dependencias explicitas
- Contratos pequenos
- Baixo acoplamento
- Alto coesao

### Testes

- Unitario
- Service/use case
- Repository/adapter
- Contrato/API
- Componente
- E2E apenas para fluxo critico

### Validacao automatica

- Arquivos obrigatorios
- Paths oficiais
- Regras documentais
- Segredos
- Tamanho de arquivo
- Nomes internos no runtime
- Fixtures
- Layering
- Stack

## Operacao

### Seguranca

- Read-only por padrao
- Confirmacao para mutacao
- Backup antes de risco
- Sem segredo em Git
- Sanitizacao de relatorios

### Banco

- Sem migrations
- Scripts `.sql`
- Idempotencia quando possivel
- Rollback documentado

### Observabilidade

- Logs uteis
- Auditoria proporcional ao risco
- Retencao definida
- Limpeza automatica
- Evitar tabela nova sem justificativa
