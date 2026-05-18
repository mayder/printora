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
- PKG-08A: Registro manual de Z-offset
- PKG-08B: Wizard manual de Z-offset
- PKG-09: Monitor CAN
- PKG-09A: Registro manual/read-only de CAN
- PKG-10: Gestão de mods e plugins
- PKG-11: Firmware Manager - cadastro de placas e presets
- PKG-12: Firmware Manager - build e dry-run
- PKG-13: Firmware Manager - flash controlado
- PKG-14: Integração Mainsail e Update Manager
- PKG-15: Centro de calibração e testes Voron

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

Entregáveis:

- tabela de eventos de manutenção por impressora;
- tabela de tarefas preventivas por impressora;
- API para registrar manutenção, falha, ajuste e nota;
- API para criar e concluir tarefas preventivas;
- status objetivo de tarefa pendente ou em dia;
- UI para diário e tarefas preventivas.

Critério de aceite:

- não envia G-code;
- não altera configs;
- não reinicia serviços;
- histórico fica vinculado à impressora correta;
- conclusão de tarefa registra evento no diário;
- `./check.sh` passa.

Estado atual:

- Implementado via `backend/sql/003_maintenance.sql`.
- Implementado em `backend/app/maintenance.py`.
- Endpoints e UI inicial implementados.
- Testes cobrem escopo por impressora e conclusão de tarefa.

## PKG-08: Assistente De Primeira Camada E Z-Offset

Objetivo:

Guiar ajuste de primeira camada.

Itens:

- wizard para `PROBE_CALIBRATE`;
- histórico de Z-offset por chapa/material;
- comparação com valor anterior;
- alerta se mudança for grande;
- notas e fotos opcionais.

## PKG-08A: Registro Manual De Z-offset

Objetivo:

Registrar manualmente valores de Z-offset por impressora, chapa, material e nozzle/toolhead.

Entregáveis:

- tabela `z_offset_records`;
- API para listar e registrar Z-offset;
- cálculo automático de valor anterior e delta;
- alerta `ok`, `monitorar` ou `revisar`;
- UI para histórico e cadastro manual.

Critério de aceite:

- não envia G-code;
- não executa `PROBE_CALIBRATE`;
- não altera `printer.cfg`;
- histórico fica escopado por impressora;
- comparação usa chapa, material e nozzle/toolhead compatíveis;
- `./check.sh` passa.

Estado atual:

- Implementado via `backend/sql/004_z_offset.sql`.
- Implementado em `backend/app/z_offset.py`.
- Endpoints e UI inicial implementados.
- Testes cobrem delta, alerta e escopo por impressora.

## PKG-08B: Wizard Manual De Z-offset

Objetivo:

Guiar o ajuste manual de Z-offset sem executar comandos automaticamente.

Entregáveis:

- endpoint `GET /api/printers/{printer_id}/z-offsets/wizard-plan`;
- roteiro com comandos sugeridos para o usuário executar manualmente;
- comparação com valor anterior compatível;
- recomendação baseada no delta;
- checklist visual no frontend.

Critério de aceite:

- não envia G-code;
- não executa `PROBE_CALIBRATE` automaticamente;
- não altera `printer.cfg`;
- mostra claramente que o fluxo é manual;
- `./check.sh` passa.

Estado atual:

- Implementado plano de wizard em `backend/app/z_offset.py`.
- UI permite avaliar o wizard e marcar checklist manual.
- Testes cobrem roteiro seguro e recomendação.

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

## PKG-09A: Registro Manual/Read-Only De CAN

Objetivo:

Registrar leituras CAN informadas manualmente, comparar com a leitura anterior da mesma interface e classificar risco sem executar comandos no host.

Entregáveis:

- tabela `can_bus_records`;
- API para listar e registrar leituras CAN por impressora;
- cálculo de delta para `rx_error`, `tx_error` e `tx_retries`;
- alerta `ok`, `monitorar` ou `problema`;
- UI para cadastro manual e histórico.

Critério de aceite:

- não executa `ip`, SSH, G-code, restart, update ou flash;
- não zera contadores CAN;
- histórico fica escopado por impressora;
- comparação usa a última leitura da mesma interface CAN;
- `rx_error` ou `tx_error` crescente vira problema;
- `tx_retries` crescente vira monitoramento;
- `./check.sh` passa.

Estado atual:

- Implementado via `backend/sql/005_can_monitor.sql`.
- Implementado em `backend/app/can_monitor.py`.
- Endpoints e UI inicial implementados.
- Testes cobrem delta, alerta e escopo por impressora.

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

Estado atual:

- Implementado `GET /api/printers/{printer_id}/plugins/audit`.
- Auditoria usa o último snapshot Moonraker/Update Manager.
- Catálogo inicial cobre KAMP/adaptive meshing, KTC-Easy/StealthChanger, `led_effect`, Crowsnest, Sonar, Timelapse, Auto Speed, TapChanger e TMC Autotune.
- UI classifica cada item como necessário, opcional, legado/lixo técnico, perigoso remover agora, seguro remover depois de backup ou precisa confirmação.
- O fluxo é read-only e não remove, atualiza, reinicia ou altera configurações.

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

Critério de aceite:

- cadastrar placas por impressora;
- listar presets sem acessar a impressora;
- preservar UUID CAN, interface CAN, arquivo `.config` e método futuro de flash;
- não executar build, flash, SSH, restart ou update;
- `./check.sh` passa.

Estado atual:

- Implementado via `backend/sql/006_firmware_boards.sql`.
- Implementado catálogo inicial de presets em `backend/app/firmware.py`.
- Implementado `GET /api/firmware/board-presets`.
- Implementado `GET/POST /api/printers/{printer_id}/firmware/boards`.
- UI permite cadastrar placas por impressora e consultar presets disponíveis.
- Esta etapa é apenas inventário local; build e flash continuam fora do escopo.

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

## PKG-12A: Firmware Manager - Plano De Build Dry-Run

Objetivo:

Gerar plano e histórico do build de firmware sem executar comandos.

Entregáveis:

- tabela `firmware_build_runs`;
- endpoint para criar dry-run por placa;
- endpoint para listar histórico por impressora;
- comandos planejados;
- checklist pré-build;
- caminhos planejados para backup da `.config`, output e binário;
- UI para revisar o plano.

Critério de aceite:

- não executa `make`, `cp`, `mkdir`, SSH, restart, update ou flash;
- não altera arquivos locais ou remotos;
- histórico fica escopado por impressora e placa;
- plano mostra claramente comandos que seriam executados em etapa futura;
- `./check.sh` passa.

Estado atual:

- Implementado via `backend/sql/007_firmware_build_runs.sql`.
- Implementado em `backend/app/firmware.py`.
- Implementado `POST /api/firmware/boards/{board_id}/build-runs/dry-run`.
- Implementado `GET /api/printers/{printer_id}/firmware/build-runs`.
- UI permite gerar e revisar dry-runs de build.
- Build real continua fora do escopo desta etapa.

## PKG-12B: Firmware Manager - Executor Local De Build Com Travas

Objetivo:

Preparar execução local de build sem flash, protegida por modo de ambiente e confirmação explícita.

Entregáveis:

- endpoint `POST /api/firmware/boards/{board_id}/build-runs/execute-local`;
- bloqueio padrão via `MAYDER_PRINT_LAB_FIRMWARE_BUILD_MODE=disabled`;
- confirmação textual `EXECUTE_LOCAL_BUILD_NO_FLASH`;
- backup da `.config` antes de sobrescrever;
- restauração da `.config` ao final;
- cópia do binário gerado para diretório de builds;
- registro de sucesso, falha ou bloqueio no histórico.

Critério de aceite:

- em modo padrão `disabled`, nenhum comando é executado;
- em modo `local`, build só roda com confirmação textual;
- não faz flash;
- não reinicia serviços;
- não acessa SSH;
- restaura `.config` original depois do build;
- `./check.sh` passa.

Estado atual:

- Implementado executor local no backend, bloqueado por padrão.
- UI exige confirmação textual antes de habilitar o botão de execução local.
- Testes cobrem bloqueio por modo desabilitado e confirmação obrigatória.

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

## PKG-15: Centro De Calibração E Testes Voron

Objetivo:

Criar uma área dedicada para testes de qualidade, calibrações e ajustes finos recomendados pela documentação Voron e pela comunidade Klipper.

Escopo planejado:

- levantar e catalogar os testes oficiais/recomendados pela Voron;
- levantar calibrações relevantes do Klipper;
- organizar sequência desde início da calibração até ajuste fino;
- armazenar G-code bruto dos testes;
- permitir execução guiada de G-code no momento certo;
- registrar resultado, fotos/notas e recomendação por teste;
- relacionar testes com material, perfil, nozzle, input shaper, pressure advance, temperatura e primeira camada.

Exemplos de grupos de testes:

- validação mecânica inicial;
- homing e endstops;
- QGL/Z tilt quando aplicável;
- probe accuracy;
- bed mesh;
- primeira camada;
- extrusion/flow;
- pressure advance;
- input shaper;
- velocidade/aceleração;
- ringing/ghosting;
- cooling/bridging;
- dimensional accuracy;
- tolerâncias e artefatos de qualidade.

Critério de aceite futuro:

- nenhum G-code é enviado sem confirmação explícita;
- bloquear execução se a impressora estiver imprimindo;
- mostrar G-code completo antes de executar;
- registrar exatamente o que foi enviado;
- registrar resultado e rollback/ação segura quando aplicável;
- permitir modo dry-run;
- separar testes genéricos Klipper, testes Voron e testes específicos por impressora.

Estado atual:

- Pacote criado apenas no backlog.
- Execução real deixada para o final do roadmap.
- Antes da implementação, será necessário listar as fontes, testes, calibrações, ajustes finos e G-codes brutos.
