# QUALITY_ROADMAP.md

## Fonte De Verdade

Este arquivo define o fluxo de desenvolvimento do Printora.

Ordem de leitura obrigatória:

1. `CODEX_PATHS.toml`
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
- `GOVERNANCA.md` deve definir riscos e rollback.
- `TESTS.md` deve definir validação mínima.
- `BUGS.md` deve registrar bugs conhecidos.
