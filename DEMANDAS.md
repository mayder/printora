# DEMANDAS.md

## Índice De Pacotes

- PKG-01: Base do projeto e documentação operacional
- PKG-01B: Base multi-impressora e fixtures locais
- PKG-01C: Snapshots read-only por impressora
- PKG-01D: Comparação de snapshots
- PKG-01E: Descoberta de impressoras na rede local
- PKG-01F: Compatibilidade com SQLite local legado
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
- PKG-16: Instalador multiplataforma
- PKG-16E: Launcher local plug and play
- PKG-17: Navegação e layout operacional do frontend
- PKG-18: Arquitetura de UX e menu por domínio
- PKG-19: Painéis operacionais estilo Mainsail
- PKG-19A: Operação read-only estilo Mainsail
- PKG-19B: Operação offline e fixtures locais
- PKG-19C: Último estado operacional conhecido
- PKG-19D: Histórico de temperaturas por snapshot
- PKG-19E: Catálogo de ações operacionais bloqueadas
- PKG-19F: Preview dry-run de ações operacionais
- PKG-19G: Histórico local de previews operacionais
- PKG-19H: Gate de execução com confirmação bloqueada
- PKG-19I: Parâmetros editáveis no preview operacional
- PKG-19J: Histórico de tentativas de execução bloqueadas
- PKG-19K: Preflight read-only no gate operacional
- PKG-19L: Compatibilidade genérica de ações operacionais
- PKG-19M: Matriz de capacidade por impressora
- PKG-19N: Preflight final por ação operacional
- PKG-20: Versionamento interno e controle de schema
- PKG-21: Releases do Printora na tela Configurações
- PKG-22: Updater local para macOS, Linux e Raspberry
- PKG-23: Updater Android/Termux
- PKG-24: Updater Windows
- PKG-25: Rollback, histórico e auditoria de updates do Printora
- PKG-26: Instalação 0.1.5 com boot automático
- PKG-27: Fluxo visual do updater 0.1.6
- PKG-28: Retry seguro do npm install 0.1.7
- PKG-29: Frontend pré-buildado para instalação 0.1.8
- PKG-30: Catálogo completo de firmware de impressoras 3D
- PKG-31: Instalação resiliente e recuperação de updates travados
- PKG-32: Desktop App macOS/Windows

## Política De Backlog

### Quando criar pacote

Criar pacote quando a demanda mudar contrato público, banco, segurança, operação crítica, UI de fluxo completo, integração externa, rollback ou exigir mais de um lote para entrega verificável.

## PKG-01: Base Do Projeto E Documentação Operacional

Objetivo:

Criar estrutura mínima do projeto, escopo, governança, backlog, testes, bugs e check script.

Entregáveis:

- `ESCOPO.md`
- `PATHS.toml`
- `QUALITY_ROADMAP.md`
- `GOVERNANCA.md`
- `DEMANDAS.md`
- `TESTES.md`
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
- Auditoria por impressora implementada via `GET /api/printers/{printer_id}/audit/read-only`.
- Classificação inicial cobre Klipper, Moonraker, Update Manager e sinais básicos do host.
- Auditoria por impressora retorna `data_state`, `source` e usa último snapshot quando Moonraker está offline.
- UI exibe origem dos dados da auditoria junto dos achados classificados.
- Testes cobrem classificação, estado `live` e fallback por snapshot offline.
- Validação real read-only executada na Voron 0.2 e Voron 2.4.
- Voron 0.2 ficou sem problemas críticos; Voron 2.4 ficou em `monitorar` por versão Klipper `dirty`.
- Auditoria manual read-only da Voron registrada em `docs/audits/VORON_READONLY_AUDIT_2026-05-18.md`.
- Coletor read-only do host implementado em `GET /api/audit/host-read-only`.
- Próximo incremento: instalar o app em modo `local` na Raspberry para eliminar dependência de SSH.

## PKG-01B: Base Multi-Impressora E Fixtures Locais

Objetivo:

Permitir que o Printora seja instalado em uma Raspberry ou em um computador da rede para gerenciar múltiplas impressoras Klipper.

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

## PKG-01E: Descoberta De Impressoras Na Rede Local

Objetivo:

Facilitar o cadastro de impressoras Klipper/Moonraker na mesma rede local.

Entregáveis:

- endpoint read-only para varrer a rede local privada;
- limitação a redes IPv4 privadas, loopback ou link-local;
- detecção via HTTP `GET /server/info` na porta Moonraker `7125`;
- indicação de impressora já cadastrada;
- botão no frontend para buscar e preencher o formulário de cadastro;
- testes automatizados para limites de rede.

Critério de aceite:

- não envia G-code;
- não altera impressora, Moonraker, Klipper ou configs;
- não cadastra nada automaticamente;
- não varre redes públicas;
- limita varredura a `/24` ou menor;
- `./check.sh` passa.

Estado atual:

- Implementado `GET /api/printers/discover`.
- UI exibe botão `Buscar na rede` e lista candidatos encontrados.
- Descoberta marca impressora já cadastrada mesmo quando o cadastro usa hostname e a varredura encontra o IP resolvido.
- Testes cobrem rede privada `/24`, rejeição de rede pública, rejeição de rede maior que `/24` e correlação hostname/IP de impressora cadastrada.
- Validação real read-only em `192.168.15.0/24` encontrou Voron 2.4 (`192.168.15.10`) e Voron 0.2 (`192.168.15.11`) como já cadastradas.
- Fluxo confirmado sem cadastro automático, G-code, SSH, restart, update, flash ou alteração em Moonraker/Klipper/configs.

## PKG-01F: Compatibilidade Com SQLite Local Legado

Objetivo:

Garantir que instalações locais criadas antes do vínculo de eventos por impressora continuem inicializando.

Entregáveis:

- reparo idempotente da tabela `app_events` legada sem apagar dados;
- preservação dos scripts SQL existentes como fonte do schema alvo;
- teste automatizado com banco antigo contendo `app_events` sem `printer_id`.

Critério de aceite:

- inicialização não falha em banco local legado;
- nenhum dado existente é removido;
- `./check.sh` passa.

Estado atual:

- Implementado reparo idempotente para adicionar `app_events.printer_id` quando ausente.
- Teste automatizado cobre criação do índice esperado após reparo.

## PKG-03: Checklist Pós-Update Guiado

Objetivo:

Criar fluxo orientado para validar impressora após updates.

Entregáveis:

- contrato de checklist com origem dos dados (`live`, `last_snapshot`, `offline` ou `no_data`);
- endpoint global e endpoint por impressora;
- fallback para último snapshot quando a impressora selecionada estiver desligada;
- resposta estável e bloqueante quando Moonraker estiver offline e não houver snapshot;
- itens técnicos, avisos do Update Manager e smoke test manual;
- UI exibindo origem dos dados e decisão final.

Critério de aceite:

- resultado final simples: "seguro imprimir" ou "não imprima ainda".
- não declara seguro quando usa snapshot ou leitura offline;
- funciona para qualquer impressora Klipper/Moonraker cadastrada;
- não envia G-code e não executa comandos mutáveis.

Estado atual:

- Implementado checklist pós-update por impressora.
- Implementado fallback para último snapshot.
- Implementado bloqueio explícito quando Moonraker está offline.
- Frontend exibe resumo, origem dos dados e itens técnicos/manuais.
- Validação real read-only executada na Voron 0.2 e Voron 2.4 com `data_state=live`.
- Ambas retornaram `Seguro imprimir após smoke manual`, sem bloqueadores técnicos e sem avisos do Update Manager.
- Fluxo confirmado sem envio de G-code, restart, update, flash ou comando mutável.

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
- quando Moonraker está offline, usa último snapshot e não declara seguro imprimir;
- quando não há leitura ao vivo nem snapshot, bloqueia com estado offline;
- UI mostra métricas e ações recomendadas.

Estado atual:

- Implementado `GET /api/printers/{printer_id}/health`.
- Health check consolida Klipper, Moonraker, Update Manager, temperatura/host, memória, latência API, snapshots e último diff.
- Implementado fallback para último snapshot quando a impressora está desligada.
- Implementado bloqueio explícito quando não há leitura ao vivo.
- UI exibe decisão operacional, origem dos dados, contadores, métricas e itens de ação.
- Validação real read-only executada na Voron 0.2 e Voron 2.4 com Moonraker/Klipper `ready`.
- Corrigida normalização de memória real reportada em kB pelo Moonraker e detecção de armazenamento via `sd_info`.
- Ambas ficaram sem bloqueios; decisão `monitorar` por latência Moonraker acima do limite de atenção.

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
- Implementado complemento offline do pacote pai: comparação read-only entre `.zip` de backup e plano de restore dry-run por arquivo.
- UI permite comparar arquivos de backup locais e gerar plano de restore bloqueado, sem extrair, sobrescrever ou remover arquivos.
- Implementado gate bloqueado de restore em `POST /api/backup/restore-gate`.
- UI permite validar a confirmação `BLOCK_REAL_RESTORE`, mas o restore real continua bloqueado.
- Gate de restore reaproveita o plano dry-run, mostra rollback futuro obrigatório e não extrai, sobrescreve ou remove arquivos.

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
- Testes cobrem sanitização de IP, URL, fonte do relatório, caminho local e segredo.
- Validação real read-only executada na Voron 0.2 e Voron 2.4 com `data_state=live`.
- Relatórios reais retornaram Markdown sanitizado, `source=<url>` e sem URL, IP, caminho local ou segredo detectável.
- Fluxo confirmado sem alterar impressora, configs, backups ou banco além da leitura normal.

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
- alerta de tarefa vencida ou próxima do vencimento;
- criação idempotente de tarefas preventivas padrão;
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
- Endpoints e UI implementados para eventos, tarefas, resumo e tarefas padrão.
- Tarefas cobrem lubrificação, correias, parafusos, fans, CAN, hotend/nozzle e limpeza de mesa.
- Status cobre `due`, `soon`, `ok` e `unknown`.
- Testes cobrem escopo por impressora, conclusão de tarefa, resumo, alertas e criação idempotente de tarefas padrão.
- Manutenção preventiva ampliada para lembrete por `days` ou `print_hours`, com baseline lido de `/server/history/totals`, fallback tolerante quando Moonraker está offline e status `not_validated`/`needs_review`.
- UI de Manutenção permite concluir rotina ou registro livre com lembrete por dias ou horas de impressão, mantendo registro sem lembrete quando solicitado.

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
- resumo por interface CAN;
- parser manual para saída de `ip -details -statistics link show can0`;
- diagnóstico físico sugerido por alerta;
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
- Endpoints e UI implementados para registro, histórico, resumo e parser manual de saída `ip link`.
- Diagnóstico orienta revisão de cabo, crimpagem, alimentação, terminação e aterramento quando há crescimento de erro.
- Leitura real com `bus_state` diferente de `ERROR-ACTIVE` agora vira `problema`.
- Resumo CAN agora diferencia explicitamente `manual_records` de `no_data`, sem declarar histórico inexistente como leitura real.
- Testes cobrem delta, alerta, `bus_state`, resumo, ausência de dados, parser, escopo por impressora e operação local com impressora offline.
- Implementada comparação offline entre duas leituras CAN manuais da mesma interface/impressora.
- UI compara o par mais recente da mesma interface CAN e avisa quando não há par comparável.
- Validação real read-only executada na Voron 0.2 e Voron 2.4: ambas retornaram `data_state=no_data`, `safe_mode=manual_read_only` e parser manual funcionando sem executar `ip`, SSH ou comando no host.
- Leituras CAN reais registradas: Voron 0.2 `can0` ficou `STOPPED` com alerta `problema`; Voron 2.4 `can0` ficou `ERROR-ACTIVE` com alerta `ok`.

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

Entregáveis:

- catálogo de mods/plugins conhecidos;
- auditoria a partir do último snapshot Moonraker/Update Manager;
- contadores de detectados, arriscados, investigar e desconhecidos;
- ação recomendada por item;
- evidências e gates antes de qualquer remoção futura;
- UI read-only sem remover, atualizar, reiniciar ou alterar configuração.

Critério de aceite:

- usuário vê o que manter, remover, atualizar ou investigar.
- usuário vê componentes fora do catálogo detectados no Update Manager;
- qualquer remoção fica condicionada a backup, busca de referências e validação posterior;
- não executa comandos no host nem no Moonraker.

Estado atual:

- Implementado `GET /api/printers/{printer_id}/plugins/audit`.
- Auditoria usa o último snapshot Moonraker/Update Manager.
- Catálogo inicial cobre KAMP/adaptive meshing, KTC-Easy/StealthChanger, `led_effect`, Crowsnest, Sonar, Timelapse, Auto Speed, TapChanger e TMC Autotune.
- UI classifica cada item como necessário, opcional, legado/lixo técnico, perigoso remover agora, seguro remover depois de backup ou precisa confirmação.
- UI exibe contadores, componentes desconhecidos, ação recomendada, evidência e gates de remoção.
- Componentes fora do catálogo também viram item auditável com ação `investigar`, evidência e gates antes de qualquer remoção.
- Validação real read-only executada na Voron 0.2 e Voron 2.4 a partir dos últimos snapshots Moonraker/Update Manager.
- Voron 0.2 detectou `octoeverywhere` como componente fora do catálogo para investigar; Voron 2.4 detectou `adaptive_meshing_purging`, `klipper-toolchanger-easy` e `led_effect`.
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
- Dry-run mostra comandos planejados, checklist, backup `.config`, output e binário planejado.
- Build real continua bloqueado por padrão e só pode rodar em modo local explícito.

## PKG-12B: Firmware Manager - Executor Local De Build Com Travas

Objetivo:

Preparar execução local de build sem flash, protegida por modo de ambiente e confirmação explícita.

Entregáveis:

- endpoint `POST /api/firmware/boards/{board_id}/build-runs/execute-local`;
- bloqueio padrão via `PRINTORA_FIRMWARE_BUILD_MODE=disabled`;
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
- Executor local salva log resumido no histórico.
- Testes cobrem bloqueio por modo desabilitado, confirmação obrigatória, restauração de `.config` e cópia de binário em ambiente local fake.
- Implementado preflight read-only de build em `POST /api/firmware/boards/{board_id}/build-runs/preflight`.
- UI permite validar diretório Klipper, `Makefile`, `.config`, config da placa, `make`, saída esperada e modo de build.
- Preflight não cria diretórios, não copia arquivos, não executa `make`, não acessa SSH, não reinicia serviço e mantém `can_execute_build=false`.

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

## PKG-13A: Firmware Manager - Flash Dry-Run Bloqueado

Objetivo:

Gerar plano de flash antes de permitir execução real.

Entregáveis:

- tabela `firmware_flash_runs`;
- endpoint para criar dry-run de flash por placa;
- endpoint para listar histórico por impressora;
- uso opcional do binário vindo de um build run;
- comandos planejados por método de flash;
- checklist pré-flash;
- UI para revisar plano de flash.

Critério de aceite:

- não faz flash;
- não reinicia Klipper;
- não acessa SSH;
- não valida MCU ao vivo;
- não altera arquivos;
- rejeita build run de outra placa;
- `./check.sh` passa.

Estado atual:

- Implementado via `backend/sql/008_firmware_flash_runs.sql`.
- Implementado em `backend/app/firmware.py`.
- Implementado `POST /api/firmware/boards/{board_id}/flash-runs/dry-run`.
- Implementado `GET /api/printers/{printer_id}/firmware/flash-runs`.
- UI permite gerar e revisar dry-run de flash.
- Implementado gate `POST /api/firmware/boards/{board_id}/flash-runs/execute`, que exige `BLOCK_REAL_FLASH` e ainda assim registra tentativa bloqueada.
- UI permite validar o gate bloqueado de flash.
- Checklist inclui energia estável, método de flash, UUID/interface CAN, rollback manual e plano de recuperação.
- Flash real permanece não implementado por segurança: não executa flashtool, restart, SSH ou validação ao vivo.
- Flash real continua fora do escopo desta etapa.
- Implementado plano manual de recuperação pós-flash por placa, incluindo pré-condições, passos por método de flash, validação e rollback.
- UI exibe plano de recuperação bloqueado sem executar flash, restart, SSH ou comandos locais.
- Implementado preflight real read-only de flash em `POST /api/firmware/boards/{board_id}/flash-runs/preflight`.
- UI permite validar Moonraker/Klipper ready, impressão parada, binário, método de flash, UUID/interface CAN e política de execução.
- Preflight de flash mantém `can_execute_flash=false` e não executa flash, restart, SSH, update, build, G-code ou validação de MCU ao vivo.

## PKG-14: Integração Mainsail E Update Manager

Objetivo:

Integrar app ao ecossistema.

Itens:

- link no Mainsail custom navigation;
- serviço systemd;
- entrada no Moonraker Update Manager;
- documentação de instalação;
- documentação de rollback.

Critério de aceite:

- backend consegue servir o frontend buildado;
- serviço systemd documentado;
- `.env` de exemplo sem segredo;
- snippet de Update Manager;
- exemplo de custom navigation do Mainsail;
- instalador com dry-run por padrão;
- documentação de instalação e rollback;
- nenhuma instalação é aplicada sem comando explícito;
- `./check.sh` passa.

Estado atual:

- Backend serve `frontend/dist` quando disponível.
- Criado `packaging/env/printora.env.example`.
- Criado `packaging/moonraker/update_manager_printora.conf`.
- Criado `packaging/mainsail/navi.json`.
- Criado `scripts/install_raspberry.sh` com dry-run padrão e `--apply` explícito.
- Criada documentação `docs/INSTALL_RASPBERRY.md`.
- Criado e validado `scripts/validate_integration.sh` para checar systemd, `.env`, Mainsail, Update Manager e documentação sem aplicar instalação.
- Teste automatizado cobre o validador offline.

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

- Implementado centro seguro com catálogo read-only e histórico manual por impressora.
- Execução real de G-code fica limitada ao gate supervisionado, com allowlist, preflight live e confirmação explícita.
- UI mostra resumo, recomenda próximos testes sem aprovação, exibe G-code apenas para revisão e registra resultados manuais.
- Backend rejeita resultado de teste com G-code sugerido se o usuário não confirmar revisão do G-code.
- Implementada sequência recomendada offline por fase, marcando testes concluídos e pendentes por impressora.
- UI exibe sequência sem enviar G-code e sem criar ação mutável.
- Implementado preflight real read-only por teste, com leitura Moonraker/Klipper, bloqueio se estiver imprimindo e `can_execute_gcode=false`.
- UI permite validar preflight do teste selecionado, exibindo checklist, bloqueios e G-code apenas como preview.
- Validação real executada na Voron 0.2 e Voron 2.4 para `probe_accuracy_center`: ambas `ready`, `standby`, sem impressão em andamento, mas G-code bloqueado pelo app.
- Implementado gate de execução real supervisionada por operador em `POST /api/printers/{printer_id}/calibration/execute`.
- UI permite executar G-code catalogado somente com `G-code revisado`, `Operador presente` e confirmação `EXECUTE_CALIBRATION_GCODE`.
- Execução real valida Moonraker/Klipper live, bloqueia impressão em andamento, bloqueia Klipper/Klippy não ready, bloqueia comandos fora da allowlist e registra exatamente comandos enviados.
- Envio de G-code monitora o estado final da impressora após o POST; timeout de transporte não vira falha se Moonraker/Klipper voltarem `ready` e o estado final for confirmado.
- O retorno final monitorado fica salvo no histórico de execução e pode preencher o modal de registro de resultado.
- Histórico de tentativas de execução fica em `GET /api/printers/{printer_id}/calibration/executions`.
- UI de Testes refeita para fluxo por cards: cada teste tem ação principal `Executar` ou `Registrar`, ajuda fica em modal via ícone de interrogação e detalhes técnicos deixam de poluir a tela principal.
- UI de Calibração preserva os cards como fluxo principal, numera a sequência nos cards, expõe busca e filtros por tipo/uso, mantém ação `Pular` e perfil aprovado de primeira camada.

## PKG-15A: Centro De Calibração - Catálogo Read-Only

Objetivo:

Criar a primeira versão segura do catálogo de calibrações e testes.

Entregáveis:

- tabela `calibration_tests`;
- seed inicial idempotente;
- endpoint para listar testes;
- endpoint para consultar teste por chave;
- painel no frontend;
- classificação por categoria, risco e modo de execução;
- pré-condições, critérios de sucesso e G-code sugerido para revisão.

Critério de aceite:

- não envia G-code;
- não reinicia serviços;
- não altera configs;
- não acessa Moonraker para executar nada;
- itens com G-code ficam marcados como `gcode_review_required`;
- itens perigosos ficam bloqueados enquanto imprime;
- `./check.sh` passa.

Estado atual:

- Implementado via `backend/sql/009_calibration_catalog.sql`.
- Implementado em `backend/app/calibration.py`.
- Implementado `GET /api/calibration/tests`.
- Implementado `GET /api/calibration/tests/{test_key}`.
- UI lista o catálogo com pré-condições, critérios e G-code somente para revisão.
- Resumo por impressora consolida categorias, riscos, modos de execução e testes que exigem revisão de G-code.

## PKG-15B: Centro De Calibração - Histórico Manual De Resultados

Objetivo:

Registrar resultados manuais dos testes por impressora, sem executar G-code.

Entregáveis:

- tabela `calibration_test_runs`;
- endpoint para listar histórico por impressora;
- endpoint para registrar resultado manual;
- status `passed`, `warning`, `failed` e `skipped`;
- campos para material, chapa, nozzle/tool, valor observado, notas e confirmação de G-code revisado;
- painel no frontend para registrar e consultar resultados recentes.

Critério de aceite:

- não envia G-code;
- não reinicia serviços;
- não altera configs;
- histórico fica escopado por impressora;
- rejeita chave de teste inexistente;
- `./check.sh` passa.

Estado atual:

- Implementado via `backend/sql/010_calibration_runs.sql`.
- Implementado em `backend/app/calibration.py`.
- Implementado `GET /api/printers/{printer_id}/calibration/runs`.
- Implementado `GET /api/printers/{printer_id}/calibration/executions`.
- Implementado `GET /api/printers/{printer_id}/calibration/summary`.
- Implementado `GET /api/printers/{printer_id}/calibration/tests/{test_key}/preflight`.
- Implementado `POST /api/printers/{printer_id}/calibration/execute`.
- Implementado `POST /api/printers/{printer_id}/calibration/runs`.
- UI permite registrar resultado manual do teste selecionado, valor observado, foto/referência, material, chapa, nozzle/tool e notas.
- Testes automatizados cobrem catálogo, filtros, escopo por impressora, rejeição de teste inexistente, exigência de revisão de G-code e resumo offline.
- Testes automatizados cobrem gate de execução, bloqueio offline e persistência de tentativas.

## PKG-16: Instalador Multiplataforma

Objetivo:

Permitir rodar o Printora em Raspberry, Manta/CB1/Linux, macOS, Windows e Docker com fluxos seguros.

Escopo:

- detectar plataforma;
- preparar ambiente local sem instalar serviço por padrão;
- manter Linux/systemd separado de macOS/Windows;
- oferecer Docker Compose para uso centralizado;
- documentar caminhos de dados por plataforma;
- preservar dry-run por padrão;
- não tocar na impressora durante instalação.

## PKG-16A: Bootstrap Dev macOS/Linux

Objetivo:

Preparar ambiente local no macOS/Linux para testar facilmente fora da Raspberry.

Entregáveis:

- `scripts/mpl_platform.sh`;
- `scripts/bootstrap_dev.sh`;
- detecção de sistema;
- data dir por plataforma;
- instalação de backend/frontend em dry-run por padrão.

Critério de aceite:

- dry-run não cria venv, não instala dependências e não altera serviço;
- `--apply` prepara ambiente local;
- não usa systemd;
- `./check.sh` passa.

Estado atual:

- Implementado `scripts/mpl_platform.sh`.
- Implementado `scripts/bootstrap_dev.sh`.

## PKG-16B: Linux/Raspberry/Manta Systemd

Objetivo:

Tornar o instalador Linux explícito para hosts com systemd.

Entregáveis:

- validação de Linux;
- validação de systemd;
- mensagem clara para macOS/Windows;
- preservação do dry-run por padrão.

Estado atual:

- `scripts/install_raspberry.sh` valida Linux/systemd antes de instalar.

## PKG-16E: Launcher Local Plug And Play

Objetivo:

Permitir abrir a Printora no macOS/Linux/Windows com um único comando ou duplo clique, sem depender de dois terminais separados.

Entregáveis:

- `scripts/run_app.sh`;
- `Abrir Printora.command`;
- `scripts/run_app_windows.ps1`;
- `Abrir Printora.bat`;
- preparação automática de venv/frontend quando ausente;
- início do backend local servindo o frontend buildado;
- modo foreground para atalho clicável manter a aplicação viva;
- comando de status e parada;
- log local no data dir da aplicação.

Critério de aceite:

- `scripts/run_app.sh --no-open` sobe `http://127.0.0.1:8069`;
- `scripts/run_app_windows.ps1 --no-open` sobe `http://127.0.0.1:8069` no Windows;
- `GET /health` responde `ok`;
- `scripts/run_app.sh --stop` para o processo iniciado pelo runner;
- `scripts/run_app_windows.ps1 --stop` para o processo iniciado pelo runner no Windows;
- não executa G-code, restart, update, flash ou alteração de configuração da impressora.

## PKG-16C: Docker Compose

Objetivo:

Permitir rodar o app em qualquer host com Docker.

Entregáveis:

- `Dockerfile`;
- `docker-compose.yml`;
- volume persistente para SQLite;
- porta `8069`.

Estado atual:

- Implementado `Dockerfile`.
- Implementado `docker-compose.yml`.

## PKG-16D: Windows Dev

Objetivo:

Preparar ambiente de desenvolvimento no Windows sem serviço nativo.

Entregáveis:

- script PowerShell;
- dry-run por padrão;
- preparação de Python/frontend/build.

Estado atual:

- Implementado `scripts/bootstrap_windows.ps1`.

## PKG-17: Navegação E Layout Operacional Do Frontend

Objetivo:

Reorganizar o frontend em uma experiência de operação parecida com ferramentas Klipper modernas, evitando uma página única longa e difícil de usar.

Entregáveis:

- sidebar com navegação por domínio;
- topbar contextual por seção e impressora ativa;
- painéis agrupados por grandeza operacional;
- dashboard de impressoras na visão geral;
- cadastro/detecção de impressora em modal;
- preservação das telas e ações existentes;
- responsividade básica para telas menores;
- validação por build do frontend e `./check.sh`.

Critério de aceite:

- usuário consegue navegar por Visão geral, Impressoras, Monitoramento, Calibração, Firmware, Manutenção, Relatórios e Configurações;
- usuário consegue trocar a impressora ativa pela topbar;
- cadastro e detecção de impressoras não poluem o dashboard principal;
- os painéis deixam de aparecer todos ao mesmo tempo;
- nenhuma operação nova é enviada para Klipper/Moonraker;
- nenhum endpoint backend é alterado;
- `./check.sh` passa.

Estado atual:

- Implementado layout com sidebar, topbar contextual, seletor global de impressora, dashboard de impressoras e modal para cadastro/detecção.

## PKG-18: Arquitetura De UX E Menu Por Domínio

Objetivo:

Organizar o Printora como produto operacional, com navegação clara por domínio e contexto permanente da impressora selecionada.

Entregáveis:

- logo e identidade visual no shell principal;
- sidebar com ícones e grupos de menu;
- topbar com contexto da seção, alertas, atualização e configuração de impressora;
- menu único de Calibração para o centro de testes/calibração;
- seção de Monitoramento para saúde, logs, CAN, Moonraker, Klipper e auditorias;
- seção de Firmware restrita à impressora selecionada;
- página inicial como dashboard geral;
- texto de orientação em cada seção.

Critério de aceite:

- usuário entende onde cadastrar impressora, monitorar logs, analisar saúde, calibrar, testar, gerenciar firmware, fazer backup e gerar relatório;
- impressora selecionada governa todas as telas de operação;
- menu não mistura gestão global com operação da impressora;
- nenhuma ação nova é enviada para Klipper/Moonraker;
- `./check.sh` passa.

Estado atual:

- Implementado primeiro redesenho do shell com identidade visual, grupos de menu, ícones, topbar operacional e novas seções por domínio.

## PKG-19: Painéis Operacionais Estilo Mainsail

Objetivo:

Criar uma área operacional para a impressora selecionada com blocos ricos e acionáveis no padrão de uso do Mainsail, mantendo as ações perigosas protegidas por confirmação e sem misturar monitoramento, configuração e operação diária.

Motivação:

Hoje parte dessas informações já existe em health check, monitoramento, atualização e cadastro de impressoras, mas ainda não está organizada em blocos operacionais claros como no Mainsail. O usuário deve conseguir abrir uma tela e entender rapidamente carga do sistema, temperaturas, toolhead, extrusor, fans, LEDs, offsets e ações seguras da impressora ativa.

Entregáveis:

- novo menu ou subárea `Operação` para ações e estado da impressora selecionada;
- painel `System Loads` com host, MCUs, arquitetura, versões, load, frequência, temperatura, CPU, memória, disco e interfaces de rede;
- painel `Temperaturas` com extrusor, mesa, câmara, MCUs, Raspberry Pi, targets e gráfico histórico;
- painel `Toolhead` com posição X/Y/Z, home/QGL, movimentos incrementais, Z-offset e speed factor;
- painel `Extruder` com tool ativa, extrusion factor, pressure advance, smooth time, retract/unretract, comandos de extrusão/retração e limites de segurança;
- painel `Miscellaneous` com fans, caselight, Nevermore, LEDs, display e estados binários relevantes;
- reaproveitamento e melhoria visual dos dados já coletados por health check, Moonraker, CAN e snapshots;
- identificação objetiva do que ainda não existe no backend e precisa de endpoint read-only ou ação controlada;
- botões com ícones e estados claros: desabilitado, loading, sucesso, alerta e erro;
- confirmação moderna para qualquer ação que envie G-code, altere target, mova eixo, faça home, QGL, extrusão, fan ou LED;
- log/histórico local das ações executadas por essa tela;
- responsividade para uso dentro do OrcaSlicer e em navegador.

Critério de aceite:

- a tela mostra somente dados da impressora selecionada;
- ações operacionais ficam separadas de diagnóstico, firmware, backups e relatórios;
- nenhum comando mutável é disparado sem confirmação e feedback visual;
- se a impressora estiver imprimindo, ações de risco ficam bloqueadas ou exigem confirmação explícita;
- o layout usa cards compactos, ícones e organização visual comparável ao Mainsail;
- componentes já existentes são aproveitados quando possível, sem duplicar lógica;
- `./check.sh` passa.

Riscos e controles:

- risco: enviar comando errado para a impressora ativa.
  Controle: contexto fixo da impressora selecionada, confirmação por ação e log.
- risco: transformar o app em clone completo do Mainsail.
  Controle: foco em operação, saúde e confiabilidade; não substituir fluxo principal de impressão.
- risco: ações durante impressão.
  Controle: consultar estado Klipper/Moonraker antes de habilitar comandos.

Estado atual:

- Primeiro lote seguro implementado em `PKG-19A`.
- Modo offline/fixture implementado em `PKG-19B`.
- Fallback para último snapshot implementado em `PKG-19C`.
- Histórico de temperaturas por snapshot implementado em `PKG-19D`.
- Catálogo visual de ações bloqueadas implementado em `PKG-19E`.
- Preview dry-run de ações operacionais implementado em `PKG-19F`.
- Histórico local de previews operacionais implementado em `PKG-19G`.
- Gate de execução com confirmação bloqueada implementado em `PKG-19H`.
- Parâmetros editáveis no preview operacional implementados em `PKG-19I`.
- Histórico de tentativas de execução bloqueadas implementado em `PKG-19J`.
- Preflight read-only no gate operacional implementado em `PKG-19K`.
- Compatibilidade genérica de ações operacionais implementada em `PKG-19L`.
- Matriz de capacidade por impressora implementada em `PKG-19M`.
- Preflight final por ação implementado em `POST /api/printers/{printer_id}/operation/actions/preflight`, com leitura Moonraker/Klipper, capacidade por ação e bloqueios explícitos.
- Ações mutáveis de operação continuam fora do escopo.

## PKG-19A: Operação Read-Only Estilo Mainsail

Objetivo:

Criar o primeiro painel operacional da impressora selecionada, reaproveitando leituras Moonraker sem enviar comandos.

Entregáveis:

- endpoint `GET /api/printers/{printer_id}/operation/status`;
- seção `Operação` no frontend;
- painel `System Loads`;
- painel `Temperaturas`;
- painel `Toolhead`;
- painel `Extruder`;
- painel `Miscellaneous`;
- indicação explícita de modo `read_only` e comandos bloqueados;
- estados vazios para dados ausentes do Moonraker.

Critério de aceite:

- não envia G-code;
- não faz home, QGL, extrusão, fan, LED, restart, update ou flash;
- não altera configs Klipper/Moonraker/Mainsail;
- dados sempre usam a impressora selecionada;
- `./check.sh` passa.

Estado atual:

- Implementado endpoint read-only de operação.
- Implementada seção `Operação` no frontend.
- Implementados painéis System Loads, Temperaturas, Toolhead, Extruder e Miscellaneous.
- Validação real read-only executada na Voron 0.2 e Voron 2.4 com `data_state=live`, Klipper `ready`, comandos bloqueados e 5 leituras de temperatura em cada impressora.
- Ações mutáveis permanecem fora do escopo deste lote.

## PKG-19B: Operação Offline E Fixtures Locais

Objetivo:

Permitir evoluir e validar a tela de Operação quando as impressoras estiverem desligadas.

Entregáveis:

- estado explícito `offline` quando Moonraker estiver indisponível;
- fixture local de operação estilo Voron;
- endpoint `GET /api/operation/fixtures/voron-offline`;
- botão `Exemplo offline` no frontend;
- destaque visual para dados simulados e dados offline;
- dados simulados para System Loads, Temperaturas, Toolhead, Extruder e Miscellaneous.

Critério de aceite:

- não chama Moonraker real ao carregar fixture;
- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- tela continua funcional sem impressora ligada;
- `./check.sh` passa.

Estado atual:

- Implementado endpoint de fixture offline.
- Implementado botão `Exemplo offline` na seção Operação.
- Implementado estado visual para `offline` e `fixture`.
- Testes automatizados cobrem fixture e bloqueio de comandos.

## PKG-19C: Último Estado Operacional Conhecido

Objetivo:

Manter a tela de Operação útil quando a impressora estiver desligada, usando o último snapshot real salvo.

Entregáveis:

- fallback automático para o último snapshot `moonraker_status` da impressora;
- estado `last_snapshot` no contrato de operação;
- inclusão opcional de `operation_objects` nos novos snapshots Moonraker;
- aviso visual no frontend quando os dados vêm de snapshot;
- testes automatizados para montagem da operação a partir de snapshot.

Critério de aceite:

- não chama Moonraker quando está exibindo o fallback de snapshot;
- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- mantém o contexto da impressora selecionada;
- `./check.sh` passa.

Estado atual:

- Implementado fallback automático para último snapshot Moonraker.
- Novos snapshots podem armazenar objetos operacionais read-only.
- Frontend distingue dados `live`, `offline`, `fixture` e `last_snapshot`.
- Snapshots novos preservam também a lista de objetos Klipper conhecidos para manter a matriz de capacidades no fallback.
- Testes automatizados cobrem snapshot operacional e capacidades vindas do último snapshot.

## PKG-19D: Histórico De Temperaturas Por Snapshot

Objetivo:

Exibir tendência recente de temperatura na tela de Operação usando snapshots salvos, sem consultar a impressora.

Entregáveis:

- extração de temperaturas dos snapshots `moonraker_status`;
- fallback para temperatura do host via `proc_stats`;
- campo `temperature_history` no contrato de Operação;
- visual compacto de histórico por sensor;
- testes automatizados para ordenação e extração do histórico.

Critério de aceite:

- não chama Moonraker ao montar histórico de snapshots;
- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- funciona com snapshots antigos sem `operation_objects`;
- `./check.sh` passa.

Estado atual:

- Implementado histórico por snapshot na API de Operação.
- Implementado visual compacto no frontend.
- Testes automatizados cobrem sensores, ordenação e fallback de host.
- Validação real após novos snapshots retornou histórico com 2 pontos por impressora na Voron 0.2 e Voron 2.4.

## PKG-19E: Catálogo De Ações Operacionais Bloqueadas

Objetivo:

Preparar a tela de Operação para comandos estilo Mainsail mostrando quais ações existirão, seus riscos e por que continuam bloqueadas.

Entregáveis:

- campo `actions` no contrato de Operação;
- catálogo inicial para Home XYZ, QGL, movimento, extrusão, temperaturas, fan e LED;
- motivo explícito de bloqueio por estado offline, impressão em andamento ou mutação ainda não implementada;
- cards visuais de ações bloqueadas no frontend;
- testes automatizados para bloqueio de ações.

Critério de aceite:

- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- todos os botões de execução permanecem desabilitados;
- bloqueia ações quando não há leitura ao vivo;
- bloqueia ações quando o estado indica impressão em andamento;
- `./check.sh` passa.

Estado atual:

- Implementado catálogo de ações operacionais no contrato da API.
- Implementada seção visual de ações bloqueadas na tela de Operação.
- Testes automatizados cobrem bloqueios por estado.

## PKG-19F: Preview Dry-Run De Ações Operacionais

Objetivo:

Permitir inspecionar o plano de uma ação operacional antes de qualquer execução real.

Entregáveis:

- endpoint `POST /api/printers/{printer_id}/operation/actions/preview`;
- resposta `dry_run_only` com comandos planejados;
- parâmetros esperados por ação;
- bloqueios explícitos na resposta;
- preview visual no frontend;
- testes automatizados para garantir que o preview não envia G-code.

Critério de aceite:

- não chama Moonraker para executar ação;
- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- retorna `would_send_gcode=false` e `executable=false`;
- informa rollback como desnecessário para preview;
- `./check.sh` passa.

Estado atual:

- Implementado preview dry-run de ações operacionais.
- Frontend exibe comandos planejados, bloqueios e rollback do preview.
- Testes automatizados cobrem o contrato dry-run.

## PKG-19G: Histórico Local De Previews Operacionais

Objetivo:

Registrar localmente os previews de ações operacionais para criar rastreabilidade antes da execução real.

Entregáveis:

- tabela SQLite `operation_action_previews`;
- repositório para salvar e listar previews por impressora;
- endpoint `GET /api/printers/{printer_id}/operation/actions/history`;
- gravação automática do preview dry-run;
- lista visual dos últimos previews na tela de Operação;
- testes automatizados para persistência e escopo por impressora.

Critério de aceite:

- não chama Moonraker para executar ação;
- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- histórico fica isolado por impressora;
- schema é idempotente;
- `./check.sh` passa.

Estado atual:

- Implementada persistência local dos previews.
- Implementado endpoint de histórico por impressora.
- Frontend exibe os últimos previews no painel de Operação.
- Testes automatizados cobrem persistência, escopo e schema.

## PKG-19H: Gate De Execução Com Confirmação Bloqueada

Objetivo:

Criar o contrato de execução segura das ações operacionais sem liberar execução real.

Entregáveis:

- tabela SQLite `operation_action_execution_attempts`;
- endpoint `POST /api/printers/{printer_id}/operation/actions/execute`;
- validação de preview existente e pertencente à impressora;
- validação de frase de confirmação;
- registro local de tentativa bloqueada;
- UI para validar o gate a partir de um preview;
- testes automatizados para confirmação correta e incorreta.

Critério de aceite:

- não chama Moonraker para executar ação;
- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- retorna tentativa `blocked`;
- mantém `would_send_gcode=false` e `executable=false`;
- registra rollback como desnecessário porque nada foi executado;
- schema é idempotente;
- `./check.sh` passa.

Estado atual:

- Implementado gate de execução bloqueada.
- Implementado registro local de tentativas de execução.
- Frontend permite informar frase e validar o bloqueio.
- Testes automatizados cobrem persistência e bloqueio.

## PKG-19I: Parâmetros Editáveis No Preview Operacional

Objetivo:

Permitir configurar parâmetros das ações operacionais antes de gerar o preview dry-run.

Entregáveis:

- inputs por ação para movimento, extrusão, temperatura, fan e LED;
- normalização backend de parâmetros fora do limite;
- preview usando os parâmetros informados;
- histórico armazenando parâmetros normalizados;
- testes automatizados para normalização de parâmetros.

Critério de aceite:

- não chama Moonraker para executar ação;
- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- limites de parâmetros são aplicados no backend;
- `./check.sh` passa.

Estado atual:

- Implementados campos editáveis por ação no frontend.
- Implementada normalização backend de parâmetros.
- Testes automatizados cobrem limites e defaults.

## PKG-19J: Histórico De Tentativas De Execução Bloqueadas

Objetivo:

Exibir e consultar as tentativas bloqueadas de execução operacional por impressora.

Entregáveis:

- listagem backend das tentativas em `operation_action_execution_attempts`;
- endpoint `GET /api/printers/{printer_id}/operation/actions/executions`;
- carregamento do histórico junto com o contexto da impressora;
- atualização do histórico após validar o gate;
- lista visual das últimas tentativas na tela de Operação;
- testes automatizados para escopo por impressora.

Critério de aceite:

- não chama Moonraker para executar ação;
- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- histórico fica isolado por impressora;
- `./check.sh` passa.

Estado atual:

- Implementado endpoint de tentativas bloqueadas.
- Frontend exibe as últimas tentativas no painel de Operação.
- Testes automatizados cobrem listagem por impressora.

## PKG-19K: Preflight Read-Only No Gate Operacional

Objetivo:

Consultar o estado real da impressora antes de qualquer tentativa de execução, sem enviar comandos.

Entregáveis:

- preflight read-only no endpoint de execução;
- leitura de `printer/info`, `server/info` e `print_stats`;
- bloqueio explícito quando Moonraker está offline;
- bloqueio explícito quando há impressão em andamento;
- persistência do resultado de preflight na tentativa bloqueada;
- exibição do preflight na UI.

Critério de aceite:

- usa apenas leitura Moonraker;
- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- mantém a tentativa como `blocked`;
- registra `would_send_gcode=false`;
- `./check.sh` passa.

Estado atual:

- Implementado preflight read-only no gate de execução.
- Tentativas bloqueadas registram estado online/offline e print state.
- Frontend exibe o resumo do preflight.

## PKG-19L: Compatibilidade Genérica De Ações Operacionais

Objetivo:

Evitar acoplamento das ações operacionais a uma Voron específica, mantendo o contrato útil para qualquer impressora Klipper.

Entregáveis:

- metadados de compatibilidade por ação;
- QGL marcado como dependente do comando/macro `QUAD_GANTRY_LEVEL`;
- LED sem nome fixo de objeto;
- parâmetro `led_name` para `SET_LED`;
- sanitização de identificadores usados no preview de G-code;
- exibição dos requisitos de compatibilidade na UI.

Critério de aceite:

- não assume caselight, Nevermore ou nome de LED específico;
- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- preview continua `dry_run_only`;
- `./check.sh` passa.

Estado atual:

- Implementados metadados genéricos de compatibilidade.
- `SET_LED` passou a exigir nome informado em parâmetro.
- Frontend exibe requisitos por ação.
- Testes automatizados cobrem sanitização e preview de LED genérico.

## PKG-19M: Matriz De Capacidade Por Impressora

Objetivo:

Mostrar, por impressora, quais ações parecem suportadas, desconhecidas ou bloqueadas usando apenas dados conhecidos do Moonraker/Klipper.

Entregáveis:

- campo `capabilities` no contrato de Operação;
- matriz por ação com status `supported`, `unknown` ou `blocked`;
- uso de objetos conhecidos do Moonraker e snapshots;
- exibição visual da matriz na tela de Operação;
- QGL/LED/fan/heaters sem pressupor uma Voron específica.

Critério de aceite:

- não envia G-code;
- não executa restart, update, flash, home, QGL, fan, LED ou extrusão;
- ações sem objeto conhecido ficam `unknown`;
- funciona com fixture, snapshot e impressora offline;
- `./check.sh` passa.

Estado atual:

- Implementada matriz de capacidade por ação.

## PKG-19N: Preflight Final Por Ação Operacional

Objetivo:

Validar cada ação operacional contra estado live e capacidades conhecidas antes de qualquer execução futura, sem enviar comandos.

Entregáveis:

- endpoint `POST /api/printers/{printer_id}/operation/actions/preflight`;
- leitura read-only de `printer/info`, `server/info`, `print_stats` e lista de objetos Klipper;
- bloqueio por Moonraker offline, impressão em andamento, Klipper/Klippy não ready e capacidade não confirmada;
- preview do G-code que seria enviado;
- UI com botão `Preflight` em cada ação operacional;
- rollback futuro documentado no retorno.

Critério de aceite:

- não envia G-code;
- não executa home, QGL, movimento, extrusão, temperatura, fan ou LED;
- não reinicia serviço, não aplica update e não altera config;
- mantém `would_send_gcode=false`, `executable=false` e `can_execute=false`;
- ações com macro/objeto ausente ficam bloqueadas;
- `./check.sh` passa.

Estado atual:

- Implementado preflight final por ação.
- Movimento/home usam `toolhead` como capacidade mínima detectável.
- QGL exige objeto/macro `quad_gantry_level`.
- Extruder, heaters, fan e LED exigem objetos Klipper compatíveis.
- Frontend exibe capacidade, bloqueadores e preview bloqueado por ação.
- Frontend exibe suporte/desconhecido por ação.
- Testes automatizados cobrem objetos genéricos, ausência de QGL e matriz preservada via snapshot.
- Validação real confirmou matriz genérica nas duas impressoras: Voron 0.2 sem pressupor QGL e Voron 2.4 com QGL detectado; heaters/LED/fan tratados conforme objetos reais.

## PKG-20: Versionamento Interno E Controle De Schema

Status: implementado.

Objetivo:

Criar a base segura para updates do próprio Printora, permitindo aplicar scripts SQL novos sem perder dados locais.

Entregáveis:

- tabela SQLite `schema_versions`;
- tabela SQLite `app_version`;
- execução idempotente dos scripts `backend/sql/*.sql` com registro de versão aplicada;
- backup automático de `printora.db` antes de qualquer atualização de schema;
- validação de integridade após aplicar SQL;
- endpoint read-only `GET /api/system/version`;
- testes automatizados para banco novo, banco existente e reexecução sem duplicar dados.

Critério de aceite:

- não usa migrations;
- todos os cambios de banco continuam em arquivos `.sql`;
- reexecutar `initialize_database()` não perde dados;
- update de schema cria backup antes de qualquer alteração;
- falha de schema mantém banco anterior disponível para rollback;
- `./check.sh` passa.

Estado atual:

- Implementado.
- Implementado via SQL idempotente em `backend/sql/000_schema_versioning.sql`.
- Implementado histórico de validação em `backend/sql/015_schema_integrity_checks.sql`.
- `initialize_database()` registra scripts SQL aplicados em `schema_versions` com checksum e ordem.
- `app_version` mantém versão instalada e revisão de schema aplicada.
- Banco existente recebe backup local no mesmo `data_dir`, como `printora.<timestamp>.before-schema.db`, antes de scripts pendentes.
- Falha durante aplicação de SQL restaura o arquivo original a partir do backup automático.
- Validação pós-schema usa `PRAGMA integrity_check`, registra resultado em `schema_integrity_checks` e bloqueia conclusão quando falha.
- Reexecução de `initialize_database()` não reaplica scripts já registrados, não duplica metadados e preserva dados existentes.
- Endpoint read-only `GET /api/system/version` expõe versão, `data_dir`, caminho do banco, scripts aplicados, schema atual e última validação, sem conteúdo do banco.
- Testes automatizados cobrem banco novo, banco existente legado, reexecução idempotente e endpoint de versão.

## PKG-21: Releases Do Printora Na Tela Configurações

Status: implementado.

Objetivo:

Permitir que o usuário veja, dentro do Printora, a versão instalada, releases disponíveis e changelog de produção.

Entregáveis:

- configuração de origem de releases por GitHub Releases;
- endpoint `GET /api/system/releases`;
- endpoint `GET /api/system/update/status`;
- card em Configurações com versão instalada, última release e canal ativo;
- lista visual das releases de produção;
- exibição de changelog resumido;
- estados de loading, offline, erro de rede e release já instalada;
- testes automatizados com fixture de releases.

Critério de aceite:

- consulta de release é read-only;
- não executa update automaticamente;
- não usa credenciais obrigatórias para repositório público;
- erro de GitHub/rede não quebra a aplicação;
- UI mostra claramente quando o ambiente já está atualizado;
- `./check.sh` passa.

Estado atual:

- Implementado.
- Consulta de releases é read-only via GitHub Releases ou fixture local.
- Variáveis de configuração adicionadas em Settings e `.env.example`, sem token obrigatório para repositório público.
- `GET /api/system/releases` retorna versão instalada, canal, última release, lista de releases de produção, changelog resumido, status `up_to_date`, `outdated` ou `unknown` e estados `offline`, `rate_limited`, `disabled` ou `error` sem quebrar a aplicação.
- `GET /api/system/update/status` permanece read-only, com `update_supported=false`.
- UI em Configurações mostra card de releases, lista de produção, changelog resumido, estado de carregamento, erro de rede, GitHub offline/rate limit, já atualizado e update disponível.
- A única ação da UI é `Verificar releases`; não há botão para aplicar update.
- Nenhum update de backend, frontend ou banco é executado neste pacote.
- Testes automatizados cobrem parse, latest release, endpoint, erro de rede/rate limit, fixtures frontend e ausência de chamada mutável.

## PKG-22: Updater Local Para macOS, Linux E Raspberry

Objetivo:

Permitir atualizar backend, frontend e banco do Printora a partir da interface em hosts Unix com shell e, quando aplicável, systemd.

Entregáveis:

- script `scripts/update_printora.sh` com modo `--plan`, `--apply` e `--rollback`;
- endpoint `POST /api/system/update/plan`;
- endpoint `POST /api/system/update/apply`;
- progresso persistido por etapa;
- download/checkout de release por tag;
- atualização de venv/backend;
- atualização de dependências frontend e build;
- aplicação segura de scripts SQL;
- restart via systemd quando disponível;
- restart por runner local quando não houver systemd;
- testes automatizados para plano, falha e sucesso simulado.

Critério de aceite:

- update exige confirmação explícita na UI;
- backup do banco é obrigatório antes de aplicar SQL;
- plano mostra versão atual, versão alvo e comandos previstos;
- falha não apaga `printora.db`;
- Raspberry/systemd não reinicia Klipper nem Moonraker;
- `./check.sh` passa.

Estado atual:

- Parcial: updater Unix implementado para macOS/Linux/Raspberry.
- Criado schema SQLite para `app_update_runs` e `app_update_steps` em `backend/sql/018_app_update_runs.sql`.
- Criados endpoints `POST /api/system/update/plan`, `GET /api/system/update/history` e `GET /api/system/update/runs/{run_id}`.
- `plan` detecta ambiente `android_termux`, `unix`, `windows` ou `unknown`, persiste plano e etapas, e rejeita ambiente desconhecido.
- Criado `scripts/update_printora.sh` com `--plan`, `--apply` e `--rollback`, detectando macOS sem systemd, Linux/Raspberry com systemd e Linux sem systemd.
- Backend aceita `apply` para ambiente `unix`, com confirmação `ATUALIZAR PRINTORA`, tag de release estável, histórico e bloqueio de concorrência.
- Testes automatizados cobrem plano Unix com mocks/tempdir e aplicação Unix por script mockado.
- Validação real Unix/Raspberry ainda pendente.

## PKG-23: Updater Android/Termux

Objetivo:

Permitir atualizar uma instalação Android/Termux do Printora pela UI, respeitando as limitações de portas, tmux e ausência de systemd.

Entregáveis:

- script `scripts/android_update_printora.sh` com modo `--plan`, `--apply` e `--rollback`;
- detecção de Termux, Python, Node, npm, Rust, clang, tmux e porta ativa;
- atualização do projeto em `~/Printora`;
- reaproveitamento seguro de `~/.local/share/printora/printora.db`;
- backup obrigatório do banco antes de schema;
- rebuild/reinstalação do backend quando necessário;
- reinício das sessões `tmux` `printora` e `printora-mdns`;
- manutenção da porta configurada, como `8069`;
- validação final de `/health` e `/api/printers`;
- testes documentados com fixture local.

Critério de aceite:

- não exige root;
- não tenta usar portas abaixo de `1024` sem root;
- update falho preserva banco e versão anterior quando possível;
- UI mostra progresso até conclusão ou falha com ação de rollback;
- `./check.sh` passa.

Estado atual:

- Parcial: script Android/Termux real criado em `scripts/android_update_printora.sh`.
- `--plan` valida `git`, `tmux`, `python`, projeto local, banco/data dir e existência da tag no remoto, emitindo JSON sem alterar arquivos.
- `--apply --tag vX.Y.Z` implementa backup obrigatório do banco, preservação da pasta atual, checkout da tag em `~/Printora.next`, reaproveitamento de `backend/.venv`, instalação editable do backend, aplicação de schema, build frontend quando necessário, restart de `tmux` e validação de `/health`.
- `--rollback` preserva a pasta atual, restaura a pasta anterior, pode restaurar backup de banco informado, reinicia `tmux` e valida `/health`.
- Teste automatizado cobre `--plan` com repositório Git temporário e `tmux` mockado.
- Backend expõe `POST /api/system/update/apply`, valida confirmação `ATUALIZAR PRINTORA`, aceita somente tag de release estável, bloqueia ambiente não suportado e persiste sucesso/falha no histórico.
- Tela Configurações exibe ação `Planejar update` quando há release disponível, modal de plano com steps, confirmação `ATUALIZAR PRINTORA`, chamada de `apply`, polling do run e histórico básico.
- Validação real de `--apply` em Android físico concluída em 2026-05-23 via ADB/Termux para `v0.1.1`: backup do banco criado, pasta anterior preservada, app reiniciado, `/health` respondeu em `printora.local:8069`, versão passou para `0.1.1`, banco manteve impressoras e run ficou `succeeded` no SQLite.
- Rollback real em Android físico ainda pendente.

## PKG-24: Updater Windows

Objetivo:

Permitir atualizar a instalação Windows do Printora pela UI e por PowerShell, preservando banco e rebuildando backend/frontend.

Entregáveis:

- script `scripts/update_printora_windows.ps1` com `--Plan`, `--Apply` e `--Rollback`;
- detecção de Python, npm, Git e PowerShell;
- backup de `%LOCALAPPDATA%\Printora\printora.db`;
- checkout/download da release;
- atualização da venv;
- `npm install` e `npm run build`;
- reinício do processo iniciado pelo runner Windows;
- validação final de `/health`;
- logs em `%LOCALAPPDATA%\Printora\logs`;
- testes manuais documentados em `TESTES.md`.

Critério de aceite:

- update exige confirmação explícita;
- execução usa `ExecutionPolicy Bypass` somente no processo atual;
- falha preserva banco e registra log acionável;
- rollback documentado restaura banco e versão anterior quando possível;
- `./check.sh` passa.

Estado atual:

- Parcial: script PowerShell criado em `scripts/update_printora_windows.ps1`.
- `--Plan` valida Git, Python, npm, projeto local, banco/data dir e tag remota, emitindo JSON sem alterar arquivos.
- `--Apply --Tag vX.Y.Z` implementa backup obrigatório do banco, preservação da pasta atual, checkout da tag em `Printora.next`, reaproveitamento de `backend\.venv`, instalação editable do backend, aplicação de schema, instalação/build frontend quando necessário, restart pelo runner Windows e validação de `/health`.
- `--Rollback` preserva a pasta atual, restaura a pasta anterior, pode restaurar backup de banco informado, reinicia pelo runner Windows e valida `/health`.
- Backend aceita `apply` para ambiente `windows`, com confirmação `ATUALIZAR PRINTORA`, tag de release estável, histórico e bloqueio de concorrência.
- Testes automatizados cobrem plano Windows, aplicação Windows por script mockado e contrato mínimo do script PowerShell.
- Validação real em Windows físico ainda pendente.

## PKG-25: Rollback, Histórico E Auditoria De Updates Do Printora

Objetivo:

Tornar updates do próprio Printora auditáveis, reversíveis e claros para o usuário.

Entregáveis:

- tabela SQLite `app_update_runs`;
- tabela SQLite `app_update_steps`;
- registro de versão anterior, versão alvo, plataforma, início, fim e status;
- registro de caminho do backup do banco;
- endpoint `GET /api/system/update/history`;
- endpoint `POST /api/system/update/rollback`;
- tela em Configurações com histórico de updates;
- botão de rollback quando houver backup e versão anterior disponíveis;
- relatório de falha com etapa, comando lógico, stderr sanitizado e próxima ação;
- testes para histórico, rollback bloqueado e rollback permitido.

Critério de aceite:

- rollback nunca remove histórico;
- logs não expõem segredos;
- usuário consegue distinguir `atualizado`, `falhou` e `rollback aplicado`;
- banco atual não é sobrescrito sem backup;
- rollback exige confirmação explícita;
- `./check.sh` passa.

Estado atual:

- Implementado endpoint `POST /api/system/update/rollback`.
- Rollback por run exige confirmação `ROLLBACK PRINTORA`, localiza `previous_project_path` e `backup_db_path` do run, valida paths seguros e chama o script do ambiente (`android_termux`, `unix` ou `windows`).
- Histórico mantém todos os runs; rollback cria run auditável próprio e, quando executado de forma síncrona, marca o run original como `rolled_back`.
- Tela Configurações mostra histórico, detalhes do run, steps, logs sanitizados e botão de rollback quando há pasta anterior disponível.
- Scripts Android/Unix/Windows registram sucesso do run de rollback quando recebem `PRINTORA_UPDATE_RUN_ID`.
- Testes automatizados cobrem confirmação obrigatória, path inseguro, histórico e mudança de status.
- Validação real de rollback em Android/Unix/Windows físico ainda pendente.

## PKG-26: Instalação 0.1.5 Com Boot Automático

Objetivo:

Simplificar a instalação do Printora e garantir que ele suba automaticamente após reinício do dispositivo, sem alterar dependências globais de serviços existentes como Spoolman.

Entregáveis:

- versão `0.1.5` no backend e frontend;
- `scripts/ensure_node_runtime.sh` para preparar Node compatível via `nvm` por usuário quando necessário;
- `scripts/install_printora.sh` como entrada simples de instalação;
- `scripts/install_printora_autostart.sh` para Android/Termux, Linux/Raspberry e macOS;
- `scripts/install_printora_windows.ps1` e `scripts/install_printora_autostart_windows.ps1` para Windows;
- instaladores públicos assistidos por plataforma (`scripts/install-macos.sh`, `scripts/install-linux.sh`, `scripts/install-android-termux.sh`, `scripts/install-windows.ps1`) verificando dependências, mostrando itens OK e perguntando antes de instalar ausentes;
- `packaging/systemd/printora.service` com `Restart=always`;
- `scripts/run_app.sh` usando Node/npm local de `.printora-node-env` quando existir;
- `scripts/install_raspberry.sh` usando Node local e reiniciando apenas `printora.service`;
- documentação em `docs/INSTALL_MULTIPLATFORM.md`;
- validação em `TESTES.md`.

Critério de aceite:

- instalação tem modo plano antes de aplicar;
- `--apply` exige confirmação explícita (`--yes`);
- Node antigo não troca o Node global;
- Raspberry/Linux configura `systemd` com restart automático;
- Android/Termux configura Termux:Boot e mantém `tmux` para app e mDNS;
- macOS configura `launchd` com `KeepAlive`;
- Windows configura tarefa agendada;
- nenhum serviço de Klipper, Moonraker, Mainsail ou Spoolman é alterado;
- `./check.sh` passa.

Estado atual:

- Implementado para macOS/Linux/Android/Windows em scripts separados.
- Adicionados instaladores públicos assistidos com banner, cores quando suportado pelo terminal e ícone ASCII de sucesso.
- Validação real em Raspberry, Android físico e Windows físico ainda pendente.

## PKG-27: Fluxo Visual Do Updater 0.1.6

Objetivo:

Remover ambiguidade entre planejar e atualizar, e deixar o modal do updater legível em desktop/mobile.

Entregáveis:

- versão `0.1.6` no backend e frontend;
- tela de releases com apenas uma ação principal: `Atualizar agora`;
- criação do plano mantida internamente antes do apply;
- modal planejado sem linha do tempo;
- linha do tempo visível apenas durante execução, falha, conclusão ou rollback;
- etapas pendentes ocultas durante execução;
- scripts Android/Unix marcando etapas conforme executam;
- modal sem rolagem interna aninhada na lista de etapas;
- testes frontend e backend atualizados.

Critério de aceite:

- usuário não vê dois botões para o mesmo fluxo;
- usuário não vê timeline antes de iniciar o update;
- etapas aparecem conforme saem de `pending`;
- fechamento do modal não depende de rolar lista interna;
- `./check.sh` passa.

Estado atual:

- Implementado e validado localmente.

## PKG-29: Frontend Pré-Buildado Para Instalação 0.1.8

Objetivo:

Evitar que a instalação em Raspberry dependa de build TypeScript/Vite local quando a release já pode entregar o frontend pronto.

Entregáveis:

- versão `0.1.8` no backend e frontend;
- `frontend/dist` versionado na release;
- bootstrap e instalador Raspberry pulam `npm install`/`npm run build` quando `frontend/dist/index.html` existe;
- variável `PRINTORA_REBUILD_FRONTEND=1` para forçar rebuild quando necessário;
- documentação de aceite em `TESTES.md`.

Critério de aceite:

- instalação nova no Raspberry não fica parada em `tsc -b && vite build` quando a release traz `frontend/dist`;
- backend continua servindo o frontend de `frontend/dist`;
- usuário ainda consegue forçar rebuild;
- `./check.sh` passa.

Estado atual:

- Implementado e validado localmente.

## PKG-28: Retry Seguro Do Npm Install 0.1.7

Objetivo:

Evitar falha de instalação quando `frontend/node_modules` do Printora fica sujo por instalação anterior, interrupção ou troca de runtime Node.

Entregáveis:

- versão `0.1.7` no backend e frontend;
- helper `scripts/npm_frontend_install.sh`;
- retry automático quando `npm install` falha;
- limpeza limitada a `frontend/node_modules` do Printora;
- integração com bootstrap, instalador Raspberry/Linux, runner local e updater Android/Unix;
- teste automatizado simulando `npm ERR! code ENOTEMPTY`.

Critério de aceite:

- erro `ENOTEMPTY` em `frontend/node_modules/caniuse-lite` não bloqueia a segunda tentativa;
- `package-lock.json` permanece preservado;
- Node/npm global do sistema não é alterado;
- nenhum serviço externo é reiniciado ou modificado;
- `./check.sh` passa.

Estado atual:

- Implementado e validado localmente.

## PKG-31: Instalação Resiliente E Recuperação De Updates Travados

Objetivo:

Reduzir falhas de instalação em macOS, Linux, Android/Termux e Windows e dar ao usuário um caminho oficial para diagnosticar instalação e destravar update órfão sem SQL manual.

Entregáveis:

- porta padrão real `8069` em scripts, docs, frontend e empacotamento;
- seleção automática de Python `3.11+` sem remover Python antigo do usuário;
- recriação automática de venv local quando ela foi criada com Python incompatível;
- upgrade local de `pip`, `setuptools` e `wheel` antes de instalar o backend editable;
- validação pós-autostart com `/health` e orientação para `doctor_install.sh`;
- `scripts/doctor_install.sh` para diagnóstico de Python, Node, porta, banco, serviço e logs;
- endpoint `GET /api/system/install-diagnostics` com diagnóstico copiável;
- painel em Configurações para recarregar e copiar diagnóstico da instalação;
- `scripts/unlock_update.sh` com backup automático do SQLite antes de marcar runs órfãos como `failed`;
- endpoint `POST /api/system/update/reconcile` para reconciliar updates antigos travados;
- botão `Reconciliar travados` no histórico de updates;
- README e guia multiplataforma revisados.

Critério de aceite:

- usuário com Python antigo e Python novo no mesmo macOS consegue instalar sem trocar o Python global;
- instalação usa `8069` por padrão;
- update travado antigo deixa de bloquear novo update via UI ou script oficial;
- nenhum histórico é apagado sem backup;
- `./check.sh` passa.

Estado atual:

- Em implementação nesta branch.

## PKG-32: Desktop App macOS/Windows

Objetivo:

Entregar o Printora como aplicativo desktop instalável para macOS e Windows, com duplo clique, janela própria e backend local iniciado automaticamente, reduzindo dependência de Terminal, navegador externo, Python/Node globais e instruções manuais.

Entregáveis:

- shell desktop para macOS e Windows, preferencialmente Tauri;
- empacotamento do frontend buildado dentro do aplicativo;
- backend local iniciado e supervisionado pelo app desktop em `127.0.0.1:8069`;
- encerramento controlado do backend ao fechar o app, quando ele tiver sido iniciado pelo app;
- detecção de porta ocupada com mensagem acionável;
- tela de erro local quando o backend não subir;
- armazenamento de dados no diretório operacional já definido (`Application Support/Printora` no macOS e `%LOCALAPPDATA%\Printora` no Windows);
- logs locais acessíveis para suporte;
- ícone, nome do aplicativo e metadados de versão;
- build inicial sem assinatura para validação local;
- documentação de instalação/uso no `README.md`, `RUNBOOK.md` e guia multiplataforma;
- validação mínima no `TESTES.md`.

Critério de aceite:

- no macOS, o usuário abre `Printora.app` por duplo clique e a UI carrega sem Terminal;
- no Windows, o usuário abre `Printora.exe` por duplo clique e a UI carrega sem PowerShell;
- o app não exige que o usuário altere Python ou Node globais;
- o backend responde em `/health` antes da janela ser considerada pronta;
- falha de inicialização mostra causa e caminho de log;
- banco local existente é preservado;
- fechamento do app não mata processo externo que não foi iniciado por ele;
- `./check.sh` passa.

Fora de escopo neste pacote:

- assinatura/notarização macOS;
- assinatura de código Windows;
- auto-update completo do aplicativo desktop;
- instalador público `.dmg`, `.msi` ou `.exe` assinado.

Estado atual:

- Planejado.

## PKG-30: Catálogo Completo De Firmware De Impressoras 3D

Objetivo:

Criar uma base local completa, versionada e verificável para atualização de firmware de impressoras 3D, usando o guia Esoterical CANBus (`https://canbus.esoterical.online/`) como primeira fonte. O pacote deve cobrir MCU principal, placas CAN/USB-CAN, EBB/toolheads, Katapult, build, flash, atualização e troubleshooting sem obrigar o usuário a navegar no site.

Entregáveis:

- crawler/scraper controlado para varrer o índice completo do guia Esoterical CANBus;
- manifesto versionado com URL, título, categoria, hash de conteúdo, data de captura e status de cada página catalogada;
- catálogo JSON normalizado para MCUs principais, adaptadores CAN, mainboards/bridges USB-CAN, EBB/toolheads, fluxos de instalação, fluxos de atualização, Katapult, CAN speed e troubleshooting;
- mapeamento entre placas do catálogo e presets locais do Firmware Manager;
- classificação explícita de placas sem preset local para orientar criação futura de preset;
- extração estruturada de MCU, método de conexão, modo de flash, bootloader/Katapult, comandos de validação, links de guia e observações de segurança;
- testes que falham quando uma página conhecida do índice não estiver catalogada ou quando o schema JSON ficar inválido;
- comando de atualização do catálogo em modo dry-run, sem alterar runtime automaticamente;
- documentação em `TELAS.md`, `TESTES.md` e, se houver decisão estrutural relevante, `DECISOES.md`;
- UI da tela Firmware consumindo apenas itens compatíveis com a impressora ativa, sem exibir presets genéricos como fluxo principal.

Critério de aceite:

- todas as páginas do menu público do guia entram no manifesto com status `catalogada`, `ignorada_com_motivo` ou `bloqueada_com_motivo`;
- o catálogo permite identificar pelo menos categoria, vendor, modelo, role, conexão, MCU provável, preset local quando existir e URL de referência para cada hardware suportado pelo guia;
- a tela Firmware continua exibindo somente placas detectadas/cadastradas da impressora ativa;
- o catálogo não executa comandos de flash, build, update, SSH ou alteração de configuração durante a varredura;
- o scraper respeita execução manual/dry-run, timeout, limite de domínio e saída determinística;
- `./check.sh` passa.

Estado atual:

- Planejado.
- Existe base inicial manual em `backend/app/data/firmware_hardware_catalog.json`, mas ela não representa varredura completa do site.
