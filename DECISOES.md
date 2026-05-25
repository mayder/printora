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
