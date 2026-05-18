# DEMANDAS.md

## Índice De Pacotes

- PKG-01: Base do projeto e documentação operacional
- PKG-01B: Base multi-impressora e fixtures locais
- PKG-01C: Snapshots read-only por impressora
- PKG-01D: Comparação de snapshots
- PKG-02: Auditoria somente leitura do ambiente Klipper
- PKG-03: Checklist pós-update guiado
- PKG-04: Health check da impressora
- PKG-05: Gerenciador de backups
- PKG-06: Relatórios sanitizados
- PKG-06A: Relatório Markdown sanitizado por impressora
- PKG-07: Diário da impressora e manutenção preventiva
- PKG-08: Assistente de primeira camada e Z-offset
- PKG-09: Monitor CAN
- PKG-10: Gestão de mods e plugins
- PKG-11: Firmware Manager - cadastro de placas e presets
- PKG-12: Firmware Manager - build e dry-run
- PKG-13: Firmware Manager - flash controlado
- PKG-14: Integração Mainsail e Update Manager

## PKG-01: Base Do Projeto E Documentação Operacional

Objetivo:

Criar estrutura mínima do projeto, escopo, governança, backlog, testes, bugs e check script.

Entregáveis:

- `ESCOPO.md`
- `CODEX_PATHS.toml`
- `QUALITY_ROADMAP.md`
- `GOVERNANCA.md`
- `DEMANDAS.md`
- `TESTS.md`
- `BUGS.md`
- `check.sh`
- `.gitignore`

Critério de aceite:

- `./check.sh` passa.
- Documentos principais existem.

## PKG-02: Auditoria Somente Leitura Do Ambiente Klipper

Objetivo:

Criar diagnóstico inicial sem alterar nada.

Verificar:

- `printer_data/config`;
- includes quebrados;
- macros suspeitas;
- symlinks quebrados;
- logs recentes;
- plugins externos;
- repos Git;
- systemd;
- Moonraker Update Manager.

Critério de aceite:

- relatório classifica achados em corrigir agora, monitorar, ignorar e precisa confirmação.

Estado atual:

- MVP parcial implementado via `GET /api/audit/read-only`.
- Classificação inicial cobre Klipper, Moonraker, Update Manager e sinais básicos do host.
- Auditoria manual read-only da Voron registrada em `docs/audits/VORON_READONLY_AUDIT_2026-05-18.md`.
- Coletor read-only do host implementado em `GET /api/audit/host-read-only`.
- Próximo incremento: instalar o app em modo `local` na Raspberry para eliminar dependência de SSH.

## PKG-01B: Base Multi-Impressora E Fixtures Locais

Objetivo:

Permitir que o MayderPrintLab seja instalado em uma Raspberry ou em um computador da rede para gerenciar múltiplas impressoras Klipper.

Entregáveis:

- tabela `printers`;
- tabela `printer_snapshots`;
- vínculo opcional entre eventos e impressora;
- endpoints para cadastrar, listar e atualizar impressoras;
- endpoint para ler status Moonraker de uma impressora cadastrada;
- fixtures locais para desenvolvimento sem impressora real.

Critério de aceite:

- múltiplas impressoras podem ser cadastradas no SQLite;
- nenhuma credencial é armazenada;
- leitura de status por impressora usa apenas Moonraker read-only;
- testes automatizados cobrem schema idempotente e CRUD básico.

Estado atual:

- Implementado via SQL idempotente em `backend/sql/001_initial_schema.sql`.
- Implementado repository SQLite em `backend/app/printers.py`.
- Implementado endpoints `/api/printers` e `/api/printers/{printer_id}/moonraker/status`.
- UI inicial permite cadastrar e selecionar impressoras.

## PKG-01C: Snapshots Read-Only Por Impressora

Objetivo:

Salvar leituras reais por impressora para histórico, auditoria comparativa e desenvolvimento offline.

Entregáveis:

- endpoint para capturar snapshot Moonraker;
- endpoint para listar snapshots por impressora;
- endpoint para abrir payload completo de um snapshot;
- resumo sanitizado na listagem;
- fixtures de snapshot Moonraker para testes.

Critério de aceite:

- snapshot usa apenas leitura Moonraker;
- snapshot fica vinculado a uma impressora;
- listagem não despeja payload grande por padrão;
- testes cobrem persistência e resumo.

Estado atual:

- Implementado `POST /api/printers/{printer_id}/snapshots/moonraker`.
- Implementado `GET /api/printers/{printer_id}/snapshots`.
- Implementado `GET /api/snapshots/{snapshot_id}`.
- UI inicial permite capturar e listar snapshots.

## PKG-01D: Comparação De Snapshots

Objetivo:

Comparar dois snapshots da mesma impressora para identificar regressões entre leituras, especialmente depois de update, manutenção ou mudança de configuração.

Entregáveis:

- endpoint para comparar dois snapshots por impressora;
- classificação objetiva por severidade;
- comparação de estado Klipper, versões, warnings, componentes falhando, repos `dirty` e temperatura do host;
- UI simples para selecionar snapshot base e atual;
- testes automatizados para mudanças críticas e rejeição de snapshots de outra impressora.

Critério de aceite:

- comparação não executa ações na impressora;
- snapshots precisam pertencer à mesma impressora;
- resultado diferencia informação, monitoramento, risco e bloqueio;
- UI mostra resumo e mudanças sem despejar payload bruto.

Estado atual:

- Implementado `GET /api/printers/{printer_id}/snapshots/diff`.
- Implementada comparação read-only em `backend/app/snapshots.py`.
- UI permite comparar snapshots capturados.

## PKG-03: Checklist Pós-Update Guiado

Objetivo:

Criar fluxo orientado para validar impressora após updates.

Critério de aceite:

- resultado final simples: "seguro imprimir" ou "não imprima ainda".

## PKG-04: Health Check Da Impressora

Objetivo:

Exibir saúde operacional.

Itens:

- CPU/RAM/disco;
- temperatura Raspberry Pi;
- temperatura MCUs;
- serviços falhando;
- Klipper/Moonraker ready;
- latência API;
- alertas.

Critério de aceite:

- resultado final mostra `OK para imprimir`, `monitorar` ou `não imprimir`;
- leitura é por impressora cadastrada;
- não executa G-code, restart, update ou flash;
- usa dados Moonraker e snapshots recentes;
- UI mostra métricas e ações recomendadas.

Estado atual:

- Implementado `GET /api/printers/{printer_id}/health`.
- Health check consolida Klipper, Moonraker, Update Manager, temperatura/host, snapshots e último diff.
- UI exibe decisão operacional, contadores, métricas e itens de ação.

## PKG-05: Gerenciador De Backups

Objetivo:

Criar snapshots seguros de configs e dados relevantes.

Regras:

- backup antes de alterar;
- comparação visual;
- restauração por arquivo;
- histórico.

## PKG-05A: Backup Dry-Run E Histórico

Objetivo:

Preparar o gerenciador de backups sem executar cópia real.

Entregáveis:

- tabela de políticas de backup por impressora;
- tabela de histórico de dry-run;
- API para criar política;
- API para listar políticas;
- API para registrar dry-run seguro;
- UI para criar política e ver histórico;
- exclusões padrão para arquivos sensíveis/gerados.

Critério de aceite:

- não lê, copia, apaga ou restaura arquivos;
- não acessa a Raspberry;
- não armazena senhas, tokens ou chaves;
- histórico fica vinculado à impressora;
- execução real fica bloqueada para etapa futura.

Estado atual:

- Implementado via `backend/sql/002_backup_manager.sql`.
- Implementado `GET/POST /api/printers/{printer_id}/backup/policies`.
- Implementado `GET /api/printers/{printer_id}/backup/runs`.
- Implementado `POST /api/backup/policies/{policy_id}/dry-run`.
- UI permite criar política e registrar dry-run planejado.

## PKG-05B: Execução Local De Backup

Objetivo:

Criar backup real somente quando o app estiver rodando no mesmo host dos arquivos.

Entregáveis:

- política com execução local explicitamente habilitada;
- endpoint de execução local;
- criação de arquivo `.zip`;
- exclusão de logs, temporários, backups, tokens, senhas e segredos por padrão;
- bloqueio quando destino fica dentro da origem;
- histórico com status, quantidade de arquivos, bytes e mensagem.

Critério de aceite:

- política `dry_run_only` bloqueia execução;
- execução não usa SSH;
- execução não reinicia serviços;
- execução não altera configs;
- execução não apaga arquivos;
- testes usam somente diretórios temporários locais.

Estado atual:

- Implementado `POST /api/backup/policies/{policy_id}/execute-local`.
- UI permite executar somente políticas com execução local habilitada.
- Testes cobrem archive criado, bloqueio dry-run e destino inválido.

## PKG-06: Relatórios Sanitizados

Objetivo:

Exportar diagnóstico para comunidade/suporte sem segredos.

Remover:

- senhas;
- tokens;
- chaves;
- URLs privadas;
- dados pessoais.

## PKG-06A: Relatório Markdown Sanitizado Por Impressora

Objetivo:

Gerar um relatório Markdown read-only por impressora para compartilhar diagnóstico em Discord, fórum ou issue pública.

Entregáveis:

- endpoint `GET /api/printers/{printer_id}/reports/sanitized`;
- consolidação de health check, snapshots recentes, última comparação e histórico de backup;
- sanitização de URLs, IPs, caminhos locais de usuário e valores sensíveis detectáveis;
- preview no frontend;
- testes automatizados para sanitização e conteúdo do relatório.

Critério de aceite:

- não altera impressora, configs, backups ou banco além da leitura normal;
- relatório não expõe URL/IP/caminho local/senhas/tokens detectáveis;
- usuário vê a lista de tipos de redação aplicados;
- `./check.sh` passa.

Estado atual:

- Implementado em `backend/app/reports.py`.
- Endpoint e preview no frontend implementados.
- Testes cobrem sanitização de IP, URL, caminho local e segredo.

## PKG-07: Diário Da Impressora E Manutenção Preventiva

Objetivo:

Registrar manutenção, falhas, ajustes e alertas por intervalo.

Itens:

- lubrificação;
- correias;
- parafusos;
- fans;
- conectores CAN;
- hotend/nozzle;
- limpeza de mesa.

## PKG-08: Assistente De Primeira Camada E Z-Offset

Objetivo:

Guiar ajuste de primeira camada.

Itens:

- wizard para `PROBE_CALIBRATE`;
- histórico de Z-offset por chapa/material;
- comparação com valor anterior;
- alerta se mudança for grande;
- notas e fotos opcionais.

## PKG-09: Monitor CAN

Objetivo:

Monitorar saúde CAN e histórico por impressão.

Itens:

- `rx_error`;
- `tx_error`;
- `tx_retries`;
- `ip -details -statistics link show can0`;
- comparação antes/depois;
- diagnóstico físico sugerido.

## PKG-10: Gestão De Mods E Plugins

Objetivo:

Mostrar plugins instalados, ativos, legados e arriscados.

Itens:

- KAMP;
- KTC/StealthChanger;
- `led_effect`;
- Crowsnest;
- Sonar;
- Timelapse;
- Auto Speed;
- TMC Autotune.

Critério de aceite:

- usuário vê o que manter, remover, atualizar ou investigar.

## PKG-11: Firmware Manager - Cadastro De Placas E Presets

Objetivo:

Cadastrar placas e presets.

Itens:

- Octopus;
- EBB;
- SB2209/SB2240;
- Mellow;
- Fysetc;
- presets com MCU, bootloader, pins, build output e flash methods.

## PKG-12: Firmware Manager - Build E Dry-Run

Objetivo:

Compilar firmware sem fazer flash.

Fluxo:

1. validar Klipper;
2. backup de `.config`;
3. aplicar preset;
4. `make clean`;
5. `make`;
6. salvar binário;
7. salvar log.

Critério de aceite:

- dry-run mostra exatamente o que seria feito.

## PKG-13: Firmware Manager - Flash Controlado

Objetivo:

Executar flash com segurança.

Regras:

- bloquear se impressão em andamento;
- validar UUID;
- exigir confirmação;
- salvar backup;
- salvar log;
- validar retorno da MCU;
- reiniciar Klipper;
- confirmar `printer/info ready`.

## PKG-14: Integração Mainsail E Update Manager

Objetivo:

Integrar app ao ecossistema.

Itens:

- link no Mainsail custom navigation;
- serviço systemd;
- entrada no Moonraker Update Manager;
- documentação de instalação;
- documentação de rollback.
