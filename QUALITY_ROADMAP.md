# QUALITY_ROADMAP.md

## Fonte De Verdade

Este arquivo define o fluxo de desenvolvimento do Printora.

Ordem de leitura obrigatória:

1. `PATHS.toml`
2. `QUALITY_ROADMAP.md`
3. `GOVERNANCA.md`
4. `DEMANDAS.md`

## Estratégia Técnica Inicial

O projeto deve começar como documentação e especificação operacional. Código só deve ser criado depois que os fluxos críticos estiverem descritos e priorizados.

Arquitetura alvo:

```text
backend: Python/FastAPI ou Node
frontend: app web responsivo
database: SQLite
service: systemd
integration: Moonraker HTTP/WebSocket API
update: Moonraker Update Manager
ui entry: Mainsail custom navigation
```

Este bloco registra a arquitetura inicial/local que originou o produto. A
arquitetura cloud plurianual oficial é
`docs/architecture/EVOLUCAO_ARQUITETURAL.md`: monólito modular, blue/green,
PostgreSQL, Redis recomponível, fila/outbox durável, storage S3-compatible e
workers no servidor atual. Depois do cutover, SQLite não permanece como fallback
cloud; o perfil local/offline pode manter adapter SQLite próprio, isolado por
testes de arquitetura e sem import/configuração cruzada com o cloud.

## Regras De Desenvolvimento

- Não criar automações destrutivas sem dry-run.
- Não fazer flash de firmware sem checklist explícito.
- Não alterar configs Klipper sem backup.
- Não armazenar senhas, tokens, chaves ou dados sensíveis em Git.
- Toda operação mutável deve gerar log e histórico.
- Toda operação de risco deve ter rollback documentado.
- Preferir simplicidade e manutenção sobre abstrações prematuras.

## Branch, Commit E PR

- Branch principal: `main`.
- Se a branch atual for `main` ou `hml`, pedir autorização explícita antes de editar, commitar, publicar ou abrir PR.
- Branches de trabalho devem usar prefixo `mayder/`.
- Commits devem ser pequenos e lógicos.
- Mensagens de commit em modo imperativo.
- Antes de commit, executar:

```bash
./check.sh
```

Se `./check.sh` falhar, não commitar.

## Pull Request

Quando houver PR, incluir:

- Contexto: por que a mudança existe.
- Resumo: o que mudou.
- Escopo: áreas tocadas.
- Checks: comando executado e resultado.
- Testes: o que foi validado.
- Riscos e rollback.

## Critérios De Qualidade

- Documentação clara.
- Fluxos reproduzíveis.
- Logs úteis.
- Backup antes de alteração.
- Erros com mensagens acionáveis.
- Integração segura com Moonraker.
- Operações perigosas protegidas por confirmação.

## Gates Para Implementação

Antes de implementar código:

- `ESCOPO.md` deve conter o escopo atualizado.
- `DEMANDAS.md` deve conter os pacotes priorizados.

## Modelo IA, SOLID e monorepo

### Leitura mínima por tipo de tarefa

Para reduzir tokens, a IA deve ler primeiro `PATHS.toml` e depois apenas os arquivos aplicáveis:

| Tipo | Ler |
|---|---|
| Pacote/lote | `QUALITY_ROADMAP.md`, `GOVERNANCA.md`, `DEMANDAS.md` |
| Bug simples | `BUGS.md`, arquivo afetado, `TESTES.md` se houver teste próximo |
| Bug complexo | `BUGS.md`, `TESTES.md`, `GOVERNANCA.md`, código afetado |
| UI/tela | `TELAS.md`, `TESTES.md`, código da tela |
| Arquitetura | `ESCOPO.md`, `DECISOES.md`, código real |
| Operação/deploy | `GOVERNANCA.md`, `RUNBOOK.md` |

Se surgir risco de segurança, banco, contrato público, operação crítica ou rollback, ampliar a leitura.

### Adaptação à arquitetura real

Este modelo não impõe uma estrutura universal. Antes de criar ou alterar pastas, a IA deve inspecionar a linguagem, framework, comandos, camadas e convenções saudáveis existentes.

No Printora:

- backend fica em `backend/app`, com testes em `backend/tests` e SQL em `backend/sql`;
- frontend fica em `frontend/src`, com assets públicos em `frontend/public`;
- a raiz governa regras transversais do monorepo;
- documentos completos dentro de módulos devem ser evitados para não gerar divergência.

### Contrato de módulo

Cada módulo deve ter responsabilidade clara:

- `backend`: API, regras de aplicação, integração Moonraker/Klipper, persistência canônica vigente, relatórios, backups, auditoria, firmware e updates.
- `frontend`: UI, estados de tela, navegação, acessibilidade, feedback visual e consumo explícito da API.
- `scripts`: operação local, bootstrap, run e validações do modelo.

Módulo não deve importar detalhe interno de outro módulo sem contrato explícito.

### Nomenclatura oficial do projeto

| Conceito | Nome preferido | Onde |
|---|---|---|
| Entrada HTTP | route/endpoint | `backend/app/main.py` e módulos de API |
| Regra de aplicação | service/function coesa | `backend/app` |
| Persistência | store/repository/sql helper | `backend/app`, `backend/sql` |
| Integração externa | client/adapter | `backend/app/moonraker.py` e equivalentes |
| Payload público | request/response/schema | backend e frontend com contrato explícito |
| Tela | view/page/component | `frontend/src` |
| Estado de tela | state/view model/hook | `frontend/src` |

### Pacote, lote e commit

- Pacote entrega um fluxo, contrato, regra, banco, segurança, integração ou mudança multi-módulo.
- Lote é uma parte pequena de um pacote.
- Durante lotes, rodar teste raso e direcionado.
- No fechamento do pacote, rodar validação completa, revisar regressões e fazer commit.
- O commit de fechamento não exige push.

### Bug e melhoria simples

- Bug simples: menor correção possível, reteste focado e teste automatizado quando houver cobertura próxima ou regra alterada.
- Bug complexo: `./check.sh`, teste automatizado quando viável e regressão do fluxo afetado.
- Documentação, label e texto simples podem usar validação local quando não alteram contrato, regra, banco, permissão ou integração.

### Review de fechamento de pacote

Antes de fechar pacote, revisar:

- escopo entregue;
- diff final;
- bugs e regressões;
- SOLID e separação de responsabilidades;
- testes automatizados e manuais;
- SQL e rollback, se houver;
- docs atualizadas;
- branch e commit.

### Check adaptável por stack

O `check.sh` da raiz chama os validadores do modelo e checks leves. Checks pesados ficam opt-in por variável de ambiente quando forem caros:

```bash
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

### Resposta final curta

Ao concluir uma tarefa, a IA deve responder apenas: o que foi feito, o que falhou ou ficou bloqueado, e como validar.

## Observabilidade mínima da aplicação

Aplicável ao produto em runtime, não ao log do desenvolvimento.

- Registrar eventos úteis para diagnóstico e auditoria operacional.
- Não registrar segredo, token, senha ou payload sensível completo.
- Usar níveis de log coerentes.
- Incluir contexto suficiente para correlacionar ação, impressora, operação e resultado.
- Definir retenção e limpeza para histórico, logs e auditoria.
- Evitar tabela nova apenas para observabilidade quando uma tabela existente resolver com clareza.

## Banco e migrations

Nunca usar migrations. Mudanças de banco devem ser entregues como scripts `.sql` idempotentes em `backend/sql/`, com ordem de execução, validação e rollback documentados.
- `GOVERNANCA.md` deve definir riscos e rollback.
- `TESTES.md` deve definir validação mínima.
- `BUGS.md` deve registrar bugs conhecidos.
