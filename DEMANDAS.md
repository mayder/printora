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
- PKG-14A: Silêncio de versão do Update Manager
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
- PKG-33: Presets e geração segura de firmware a partir do catálogo
- PKG-34: Provisionamento da Raspberry/BTT Pi via SSH
- PKG-35: Setup CAN/U2C/can0
- PKG-36: Wizard de firmware por hardware real
- PKG-37: Flash supervisionado de firmware
- PKG-38: Validação final da impressora Klipper
- PKG-39: Autenticação, usuários e organização
- PKG-40: Gestão cloud de impressoras
- PKG-41: Pareamento seguro do agente
- PKG-42: Agente remoto base
- PKG-43: Canal remoto agente-servidor
- PKG-44: Instalador online assistido do agente
- PKG-45: Atualização automática do agente
- PKG-46: Paridade funcional remota
- PKG-47: Operação segura remota
- PKG-48: Observabilidade e suporte do agente

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

- Implementado e validado operacionalmente.
- MVP inicial implementado via `GET /api/audit/read-only`.
- Auditoria por impressora implementada via `GET /api/printers/{printer_id}/audit/read-only`.
- Classificação inicial cobre Klipper, Moonraker, Update Manager e sinais básicos do host.
- Auditoria por impressora retorna `data_state`, `source` e usa último snapshot quando Moonraker está offline.
- UI exibe origem dos dados da auditoria junto dos achados classificados.
- Testes cobrem classificação, estado `live` e fallback por snapshot offline.
- Validação real read-only executada na Voron 0.2 e Voron 2.4.
- Voron 0.2 ficou sem problemas críticos; Voron 2.4 ficou em `monitorar` por versão Klipper `dirty`.
- Auditoria manual read-only da Voron registrada em `docs/audits/VORON_READONLY_AUDIT_2026-05-18.md`.
- Coletor read-only do host implementado em `GET /api/audit/host-read-only`.
- Execução local na Raspberry validada fora deste ciclo, eliminando a pendência de dependência de SSH para o aceite do pacote.

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
- UI e API permitem marcar rotina do catalogo como `N/A` por impressora, ocultando do plano preventivo principal e mantendo reversao por `Desfazer`.
- UI de Manutenção exibe tags de area fisica nos cards e permite filtrar por area ou ordenar a grade unica por area, titulo, criticidade e vencimento, preservando filtros de status e `N/A`.

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

## PKG-14A: Silêncio De Versão Do Update Manager

Objetivo:

Permitir que o usuário suspenda alertas de uma versão específica de qualquer componente do Update Manager sem bloquear a ação manual de atualizar depois.

Critério de aceite:

- silêncio é por impressora, componente e identidade concreta da versão;
- nova versão remota, atraso, pacote, warning ou anomalia reativa o alerta automaticamente;
- card da tela Atualizações permanece visível com `Reanalisar`, `Atualizar`, `Rollback` quando existir e `Reativar alerta`;
- Home, topbar, Central de alertas, Health Check, Checklist pós-update, Auditoria e Relatórios não contam versão silenciada como alerta ativo;
- `./check.sh` passa no fechamento.

Estado atual:

- Implementado com tabela SQLite `update_alert_silences`.
- Endpoints criados para silenciar e reativar alerta por componente.
- Agregadores de update, health, checklist, auditoria e relatório respeitam o silêncio ativo.
- UI da tela Atualizações mantém ações disponíveis e exibe estado `versão silenciada`.
- Testes automatizados cobrem chave de versão, expiração, persistência e filtros nos agregadores.

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

## PKG-19O: Execução Operacional Controlada

Objetivo:

Transformar a tela Operação em painel de operação funcional estilo Mainsail, mantendo preflight e histórico local antes de enviar G-code.

Entregáveis:

- endpoint de execução direta protegida para ação operacional;
- envio de G-code via Moonraker apenas quando preflight live permite;
- registro de preview e tentativa executada/bloqueada;
- ações para movimento, home, QGL, extrusão, temperaturas, fan, LED, speed factor, limites de velocidade/aceleração, extrusion factor e pressure advance;
- UI em painéis Toolhead, Extrusor, Machine e Miscellaneous, sem duplicar os painéis principais de temperaturas/fans;
- controles de percentual com botões de incremento/decremento;
- inputs sem spinner visual bruto do navegador.

Critério de aceite:

- bloqueia quando Moonraker está offline, Klipper/Klippy não estão ready, há impressão em andamento ou capacidade não está confirmada;
- registra comandos enviados, resposta/monitoramento do Moonraker e histórico da tentativa;
- comandos de update, restart, flash e alteração de config continuam fora da tela Operação;
- `./check.sh` passa.

Estado atual:

- Implementado endpoint `execute-direct` para ações operacionais.
- Implementado envio controlado via Moonraker com preflight, histórico e monitoramento pós-envio.
- Frontend passou a operar por painéis funcionais estilo Mainsail.
- Testes backend e build frontend validados por `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

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

- Implementado e validado operacionalmente.
- Fluxo de instalação resiliente e recuperação de updates travados considerado fechado, incluindo diagnóstico oficial, `unlock_update.sh`, reconciliação de updates órfãos e uso estável do updater.

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

- Implementado localmente.
- Criada área `Setup do Zero` sem dependência de impressora ativa.
- Backend expõe `POST /api/setup/ssh/preflight`, `POST /api/setup/ssh/plan` e `GET /api/setup/ssh/history`.
- Preflight usa SSH read-only com `BatchMode=yes`, timeout, `bash -s` e coleta apenas SO, usuário, grupos, ferramentas, versões, disco, portas, serviços, paths, CAN e USB.
- Autenticação aceita `agent` ou `key_path`; senha, token e conteúdo de chave privada não são aceitos nem persistidos.
- Histórico local `setup_ssh_runs` salva tipo, status, alvo, usuário, porta, método de autenticação, resumo e plano sem segredos.
- Plano dry-run explicita que placa virgem não aceita SSH e precisa de mídia de boot/OS/rede/SSH antes do provisionamento remoto.
- Plano gera etapas revisáveis para dependências base, Klipper, Moonraker, Mainsail/Fluidd, Printora, CAN e firmware futuro, com comandos prefixados por `PLAN`.
- Nenhuma instalação real, `apt`, edição de arquivo, restart, flash, G-code, alteração de Klipper/Moonraker ou gravação de firmware é executada neste pacote.
- Testes focados cobrem parser, classificação de checks, boundary de placa virgem, comandos dry-run e ausência de persistência de `key_path`.
- Validação de fechamento: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

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

- Implementado para fechamento local do PKG-30.
- Manifesto versionado representa 83 páginas do menu público do Esoterical CANBus, com URL, título, categoria, hash, data de captura e status controlado.
- Catálogo local normalizado cobre 56 hardwares, 9 workflows, 5 fluxos de atualização, 12 guias de troubleshooting, Katapult, CAN speed e metadata de geração.
- Mapeamento de presets locais identifica 11 hardwares com preset existente e mantém 45 hardwares em `known_hardware_without_local_preset`, sem criar presets automaticamente.
- Backend do Firmware Manager expõe resumo read-only do catálogo local em `/api/firmware/catalog` e inventário enriquecido em `/api/printers/{printer_id}/firmware/hardware-inventory`, mantendo dependência runtime somente em dados locais.
- Tela Firmware consome o catálogo como referência compacta para placas da impressora ativa, sem transformar o catálogo em lista genérica e sem executar build, flash, update, SSH ou alteração local a partir dessas referências.
- Validação automatizada do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
- Validação manual pendente para aceite operacional em impressora real: abrir Firmware com uma impressora online, confirmar placas detectadas/cadastradas, sugestão de modelo físico, status de preset local/faltante, links do guia e ausência de ações mutáveis disparadas pelo catálogo.

## PKG-33: Presets E Geração Segura De Firmware A Partir Do Catálogo

Objetivo:

Transformar o catálogo local do PKG-30 em presets reais de build para placas suportadas, gerar `.config` determinístico, preparar build seguro por dry-run e manter build real bloqueado por padrão, sem flash automático.

Motivo da numeração:

- `PKG-31` já está reservado para instalação resiliente e recuperação de updates travados.
- `PKG-32` já está reservado para o aplicativo desktop macOS/Windows.
- `PKG-33` é o próximo número livre e mantém o pacote de firmware pós-PKG-30 sem sobrescrever backlog existente.

Entregáveis:

- inventário dos 45 hardwares do catálogo que ainda estão em `known_hardware_without_local_preset`;
- priorização inicial de presets BTT, Fysetc e Mellow mais comuns;
- presets locais com MCU, bootloader/Katapult quando aplicável, comunicação, arquivo `.config` esperado, output de build esperado e método futuro de flash;
- schema de build config com opções equivalentes ao `make menuconfig`, validável sem executar `make`;
- validação de suficiência para classificar cada preset como completo, faltando dados ou inválido;
- gerador determinístico de `.config` a partir de preset completo;
- testes de snapshot para `.config` gerado;
- dry-run de build reforçado com preset usado, `.config` planejado, backup planejado, diretório de trabalho, output esperado e comandos planejados;
- artefatos de `.config`, logs e binário previstos em diretório controlado do Printora quando o fluxo avançar para build local;
- UI da tela Firmware exibindo por placa da impressora ativa: preset completo, faltando dados, gerar config, preparar build e build concluído quando houver artefato;
- documentação de operação, validação, riscos e rollback em `TESTES.md`, `TELAS.md` e `RUNBOOK.md` quando o respectivo lote alterar comportamento observável.

Lotes:

1. Cobertura de presets: listar hardwares sem preset, priorizar BTT/Fysetc/Mellow e adicionar presets locais incrementais.
2. Schema de build config: definir contrato equivalente ao `make menuconfig` e validar suficiência de presets.
3. Gerador de `.config`: gerar arquivo determinístico sem rodar `make` e cobrir com snapshots.
4. Build dry-run reforçado: planejar comandos, diretórios, backup, `.config`, logs e binário sem executar comandos mutáveis.
5. Build real controlado: manter bloqueado por padrão, exigir modo local e confirmação textual, salvar logs/binário e restaurar `.config`, sem flash.
6. UI Firmware: exibir estado de preset, geração de config, preparação de build e resultado de build sem transformar catálogo em lista principal.

Critério de aceite:

- `PKG-31` e `PKG-32` permanecem preservados com seus escopos atuais;
- hardwares sem preset continuam rastreáveis até receberem preset local;
- presets completos têm dados suficientes para gerar `.config`;
- geração de `.config` é determinística, testada por snapshot e não depende de relógio, ambiente real ou ordem implícita;
- dry-run de build não executa `make`, cópia para Klipper, SSH, restart, update, flash ou alteração local/remota;
- build real permanece bloqueado por padrão e só pode avançar em lote específico com modo local explícito e confirmação textual;
- `.config` real do Klipper não é sobrescrito sem backup e restauração documentados no lote de build controlado;
- tela Firmware continua guiada pela impressora ativa e não vira lista genérica de catálogo/presets;
- `./check.sh` passa no fechamento do pacote.

Escopo fora:

- flash automático ou execução real de flash;
- SSH real obrigatório;
- build real por padrão;
- alteração em impressora real sem confirmação explícita;
- update de Klipper, Moonraker, Mainsail ou sistema operacional;
- restart de Klipper, Moonraker ou systemd;
- suporte a qualquer placa sem preset validado;
- dependência do site Esoterical CANBus em runtime.

Validação:

- por lote, rodar testes focados de firmware e validação manual proporcional ao risco;
- para presets e catálogo, validar schema, mapeamento `preset_ids` e permanência dos hardwares ainda sem preset;
- para `.config`, validar snapshots determinísticos;
- para dry-run, validar ausência de comandos mutáveis e histórico escopado por impressora/placa;
- para UI, validar Firmware offline, online, placa com preset completo, placa sem preset e ausência de flash/SSH/restart/update;
- no fechamento, rodar `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

Estado atual:

- Lote 1 implementado localmente.
- Inventário inicial do lote confirmou 45 hardwares sem preset local: 3 adaptadores CAN, 25 mainboards e 17 toolheads.
- Foram adicionados 12 presets priorizados para BTT, Fysetc e Mellow: BTT Kraken H723, BTT Manta M5P G0B1, BTT Manta M8P v2 H723, BTT SKR-3 H743, Fysetc Spider v2.2 F446, Fysetc Spider v2.3 F446, Fysetc Spider v3.0 H7, Fysetc H36 G0B1, Fysetc SB Combo V2 F072, Mellow Fly-Super8 Pro H723, Mellow Fly SB2040 v3 RP2040 e Mellow Fly SHT36 v3 RP2040.
- Catálogo local passou a mapear 23 hardwares com preset local e mantém 33 hardwares em `known_hardware_without_local_preset`: 3 adaptadores CAN, 17 mainboards e 13 toolheads.
- Lote 1 não executa build, flash, SSH, `make`, restart, update ou alteração em impressora real.
- Lote 2 implementado localmente.
- Criado schema `FirmwareBuildConfig` versionado para opções equivalentes ao `make menuconfig`: arquitetura, MCU, modelo de processador, bootloader, clock, interface de comunicação, conexão CAN/USB/serial, arquivo `.config` e output esperado.
- Endpoint `/api/firmware/board-presets` expõe `build_config`, `build_config_status` e `build_config_validation`, classificando presets como `complete`, `missing_data` ou `invalid`.
- Validação de suficiência cobre preset completo, campos faltantes e schema inválido sem executar `make`, build real, flash, SSH, restart ou update.
- Lote 3 implementado localmente.
- Criado gerador determinístico de `.config` em memória a partir de `FirmwareBuildConfig`, com snapshots para preset STM32 e RP2040.
- Endpoint `GET /api/firmware/board-presets/{preset_id}/config-preview` retorna preview seguro com `content`, `lines`, metadata do preset e `artifact_saved=false`.
- Preview bloqueia preset incompleto com erro claro e não salva arquivo, não escreve em Klipper, não executa comandos externos e não depende de data/hora ou ambiente local.
- Lote 4 implementado localmente.
- Dry-run de build reforçado em `POST /api/firmware/boards/{board_id}/build-runs/dry-run` com preset usado, status de suficiência, `.config` gerado planejado, backup planejado, diretório de trabalho, output esperado, log planejado, binário planejado e comandos `PLAN ...` não executáveis.
- Histórico em `GET /api/printers/{printer_id}/firmware/build-runs` mantém o escopo por impressora/placa e reexpõe os metadados planejados sem nova persistência.
- Dry-run e preflight bloqueiam preset sem build config completo antes de montar plano de build; nenhum `make`, build real, SSH, flash, restart, update ou cópia para Klipper é executado.
- Lote 5 implementado localmente.
- Build local real continua bloqueado por padrão e só executa com `PRINTORA_FIRMWARE_BUILD_MODE=local` e confirmação textual `EXECUTE_LOCAL_BUILD_NO_FLASH`.
- Executor local usa o `.config` determinístico gerado pelo preset, salva esse arquivo em `output_root/local-build/<placa>/generated/`, faz backup da `.config` atual, substitui temporariamente a `.config` do Klipper local, executa somente `make clean` e `make`, restaura a `.config` em sucesso ou falha, salva log em `logs/build.log` e copia o binário esperado para o diretório de artefatos.
- Histórico registra bloqueio por modo, bloqueio por confirmação inválida, sucesso e falha sem executar flash, restart, SSH, update ou alteração em impressora remota.
- Lote 6 implementado localmente.
- Tela Firmware continua guiada pela impressora ativa e mostra por placa cadastrada o estado do preset, ação de visualizar `.config`, validação de build, preparação de dry-run e resumo de artefato/log quando existir build.
- UI de build local controlado expõe `klipper_path`, `output_root` e confirmação textual, mas a decisão de executar/bloquear permanece no backend.
- Botões e chamadas de flash foram removidos da tela Firmware deste pacote; a UI não aciona flash, SSH, restart ou update.
- PKG-33 fechado localmente.
- Escopo entregue sem alterar PKG-30: catálogo local segue versionado e read-only em runtime; PKG-33 apenas transforma parte do catálogo em presets/build config, geração de `.config`, dry-run, build local controlado e UI segura por impressora ativa.
- Validação de fechamento: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
- Pendência fora do aceite automatizado: validação manual em impressora real offline/online antes de considerar uso operacional em hardware real.

## PKG-34: Provisionamento Da Raspberry/BTT Pi Via SSH

Objetivo:

Criar um assistente seguro para conectar em uma Raspberry/BTT Pi por SSH, diagnosticar o ambiente e gerar um plano de instalação da stack Klipper sem alterar nada por padrão.

Contexto inicial:

- hardware alvo inicial: BTT Pi v1.2 com U2C, Octopus Pro v1.1 STM32H723 e EBB36 v1.2;
- o Printora já possui instalador local, diagnóstico de instalação, catálogo CANBus e Firmware Manager seguro;
- este pacote não faz flash, não edita configuração Klipper e não instala dependências automaticamente sem confirmação.

Entregáveis:

- cadastro temporário de host SSH sem persistir senha, token ou chave privada;
- teste de conectividade SSH com timeout curto e erro acionável;
- coleta read-only de ambiente: SO, arquitetura, usuário, grupos, Python, Git, systemd, espaço em disco, portas em uso e paths comuns de Klipper;
- detecção read-only de Klipper, Moonraker, Mainsail/Fluidd, KIAUH, CAN tooling, `~/klipper`, `~/moonraker`, `~/printer_data` e serviços systemd;
- endpoint de preflight SSH read-only;
- endpoint de plano dry-run com etapas sugeridas para instalar ou corrigir dependências;
- UI de wizard com host, usuário, porta, autenticação, diagnóstico e plano revisável;
- histórico local de preflights/planos sem segredos;
- documentação em `RUNBOOK.md`, `TESTES.md` e `TELAS.md`.

Lotes:

1. Contrato e segurança SSH: schema, redaction, timeouts, sem persistência de segredo.
2. Preflight read-only remoto: coletar ambiente e detectar stack existente.
3. Plano dry-run de instalação: comandos planejados, riscos, pré-requisitos e rollback esperado.
4. UI do wizard: conexão, diagnóstico, plano e estados de erro.
5. Validação com fixture local e host real acompanhado, sem aplicar mudanças.

Critério de aceite:

- nenhuma senha, chave privada ou token é salvo em banco, log, histórico ou Git;
- preflight não instala pacote, não altera arquivo, não reinicia serviço e não executa flash;
- plano dry-run separa comandos seguros, comandos mutáveis e comandos proibidos;
- erros de SSH, sudo ausente, DNS, porta fechada e host incompatível são explícitos;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado localmente.
- Backend expõe `POST /api/setup/can/preflight`, `POST /api/setup/can/plan`, `POST /api/setup/can/apply` e `GET /api/setup/can/history`.
- Diagnóstico CAN remoto usa SSH read-only e coleta ferramentas (`ip`, `lsusb`, `systemctl`, `sudo`, `modprobe`, `lsmod`, `curl`, `python3`), sudo sem senha, módulos CAN, USB/U2C, links de rede, `ip -details -statistics link show can0`, arquivos de config, serviços, estado de impressão e query de UUID CAN quando Klipper tooling existe.
- Plano dry-run diferencia U2C/USB ausente, módulos CAN ausentes, interface `can0` ausente, bitrate divergente, impressão em andamento, UUID indisponível e host sem systemd.
- Plano gera comandos `PLAN` para carregar módulos, criar serviço systemd de `can0`, backup de `/etc/systemd/system/can0.service`, `systemctl enable/restart` e query de UUID, sem executar nada.
- Apply CAN existe, mas fica bloqueado por padrão: exige confirmação textual `CONFIGURAR CAN0` e variável `PRINTORA_CAN_SETUP_MODE=remote`.
- Apply real, quando habilitado, faz preflight antes, bloqueia impressão detectada, exige `sudo -n`, cria backup remoto em `~/.local/share/printora/can-setup/backups/<timestamp>/`, escreve `/etc/systemd/system/can0.service`, roda `daemon-reload`, `enable`, `restart` e valida com `ip -details -statistics link show can0`.
- Histórico local `setup_can_runs` registra preflight, plan e apply sem senha, token ou chave privada.
- UI `Setup do Zero` ganhou seção CAN/U2C com interface, bitrate, diagnóstico, plano, apply gateado, resultado e histórico CAN.
- Testes focados cobrem parsing de CAN/U2C/UUID, classificação de problemas, bloqueio por impressão, comandos `PLAN`, confirmação explícita e ausência de persistência de `key_path`.
- Nenhum build de firmware, flash, G-code, alteração de Klipper/Moonraker, restart de Klipper/Moonraker ou gravação de `printer.cfg` é executado neste pacote.
- Validação de fechamento: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

## PKG-35: Setup CAN/U2C/can0

Objetivo:

Criar fluxo guiado para preparar e validar CAN na Raspberry/BTT Pi com U2C, mantendo dry-run por padrão e aplicando mudanças somente em lote específico com confirmação e rollback.

Contexto inicial:

- hardware alvo inicial: U2C conectado à BTT Pi v1.2, Octopus Pro H723 e EBB36 v1.2;
- o Printora já possui Monitor CAN e catálogo de troubleshooting CANBus;
- este pacote prepara rede CAN, não compila firmware e não faz flash.

Entregáveis:

- detecção read-only de interfaces CAN, USB, U2C, `can0`, módulos kernel e pacotes necessários;
- leitura de `ip -details -statistics link show can0` quando disponível;
- plano dry-run para criar/ajustar configuração de CAN, bitrate, interface e serviço de boot;
- backup planejado e real antes de qualquer alteração em arquivo de rede/systemd;
- aplicação controlada de configuração CAN em lote posterior, com confirmação textual;
- validação pós-aplicação: `can0` online, bitrate esperado, contadores CAN e consulta de UUID quando Klipper tooling existir;
- troubleshooting guiado para ausência de `can0`, bitrate incorreto, U2C ausente e UUID não encontrado;
- UI com status CAN, plano, apply controlado, validação e rollback;
- documentação em `RUNBOOK.md`, `TESTES.md`, `TELAS.md` e decisão em `DECISOES.md` se o modelo de apply remoto virar padrão.

Lotes:

1. Diagnóstico read-only CAN/U2C remoto.
2. Plano dry-run de configuração `can0`.
3. Backup e rollback de arquivos afetados.
4. Apply controlado com confirmação textual e bloqueios de segurança.
5. Validação pós-setup e troubleshooting.
6. UI de setup CAN integrada ao fluxo da impressora.

Critério de aceite:

- read-only e dry-run não alteram rede, systemd, Klipper, Moonraker ou firmware;
- qualquer alteração real exige confirmação explícita, backup e rollback documentado;
- o fluxo bloqueia execução se houver impressão em andamento ou Klipper/Moonraker em estado incompatível quando detectável;
- diagnóstico diferencia problema de U2C, interface Linux, bitrate, cabeamento, terminação e firmware;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado localmente.
- Backend expõe `POST /api/setup/firmware/plan`, `POST /api/setup/firmware/build` e `GET /api/setup/firmware/history`.
- Wizard remoto usa presets existentes do Firmware Manager e exige confirmação da variante física antes de liberar plano pronto.
- Plano gera `.config` determinístico a partir do preset, calcula `sha256`, define diretório remoto de artefatos, binário esperado, checklist e comandos `PLAN`, sem executar nada.
- Build remoto real fica bloqueado por padrão: exige confirmação textual `BUILD_FIRMWARE_NO_FLASH` e variável `PRINTORA_REMOTE_FIRMWARE_BUILD_MODE=remote`.
- Build remoto, quando habilitado, salva `.config` gerado em diretório controlado, faz backup de `<klipper_path>/.config`, substitui temporariamente `.config`, roda `make clean && make`, copia binário para artefatos, calcula hash, consulta UUIDs CAN quando possível e restaura `.config` via trap em sucesso ou falha.
- Histórico local `setup_firmware_runs` registra plano/build por alvo SSH, placa, papel, preset, interface CAN, paths, hashes, UUIDs e log, sem senha, token ou chave privada.
- UI `Setup do Zero` ganhou seção Firmware remoto com preset, nome físico, papel, paths, confirmação de variante, plano, build gateado, artefatos e histórico.
- Flash automático, restart, update, G-code e alteração de `printer.cfg` ficam fora deste pacote.
- Testes focados cobrem bloqueio sem variante confirmada, vínculo hardware/preset/artefatos, ausência de comando de flash, confirmação de build sem flash e histórico sem `key_path`.
- Validação de fechamento: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

## PKG-36: Wizard De Firmware Por Hardware Real

Objetivo:

Criar um wizard operacional para selecionar hardware real da impressora, gerar `.config`, compilar firmware na Pi e registrar UUIDs/artefatos, sem flash automático.

Contexto inicial:

- hardware alvo inicial: Octopus Pro v1.1 STM32H723 como MCU principal, EBB36 v1.2 STM32G0B1 como toolhead CAN e U2C como adaptador;
- o PKG-33 já cobre presets, `.config` determinístico, dry-run e build local controlado sem flash;
- este pacote adapta o fluxo para hardware real remoto via Pi e mantém flash fora do escopo.

Entregáveis:

- wizard de seleção de hardware real a partir do catálogo/presets existentes;
- confirmação visual de variante física: modelo, revisão, MCU, papel na impressora e conexão esperada;
- geração remota de `.config` em diretório controlado do Printora, sem sobrescrever `.config` do usuário sem backup;
- build remoto controlado no `~/klipper` da Pi, com modo explícito e confirmação textual;
- captura de logs, binário gerado, comando usado, preset, hash e timestamp;
- leitura de UUIDs CAN quando disponível, sem gravar automaticamente em `printer.cfg`;
- associação dos artefatos a impressora, placa e preset;
- UI com etapas por placa: identificar, gerar config, build, artefato, UUID, pronto para flash manual/supervisionado;
- documentação em `RUNBOOK.md`, `TESTES.md` e `TELAS.md`.

Lotes:

1. Contrato de hardware real e vínculo com presets existentes.
2. Wizard de seleção e validação de variante física.
3. Geração remota de `.config` com backup e artefatos.
4. Build remoto controlado sem flash.
5. Captura de UUIDs e associação a placa.
6. UI de progresso e histórico por placa.

Critério de aceite:

- o wizard não assume variante física sem confirmação do usuário;
- build remoto não executa flash, restart, update ou edição de `printer.cfg`;
- todo artefato gerado fica rastreável por impressora, placa, preset e comando;
- falha de build preserva `.config` anterior e mantém log copiável;
- UUID capturado é sugestão revisável, não alteração automática de config;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado localmente e commitado no PKG-36; validação em hardware real permanece operacional.

## PKG-37: Flash Supervisionado De Firmware

Objetivo:

Implementar fluxo de flash real supervisionado, com checklist, confirmação explícita, preflight, backup de artefatos, execução controlada, validação pós-flash e rollback manual documentado.

Contexto inicial:

- flash de firmware é operação crítica e pode deixar MCU offline;
- o Printora já possui gate bloqueado de flash e histórico de tentativas bloqueadas;
- este pacote só deve avançar após PKG-34, PKG-35 e PKG-36 entregarem diagnóstico, CAN e artefatos confiáveis.

Entregáveis:

- checklist obrigatório por tipo de placa: mainboard USB/DFU, mainboard CAN/Katapult, EBB/toolhead CAN e adaptador U2C quando aplicável;
- preflight real read-only: impressora parada, energia estável, MCU identificada, artefato existe, método de flash compatível, rollback documentado;
- comando de flash planejado com preview antes da execução;
- confirmação textual específica por placa e método;
- execução real supervisionada apenas para métodos suportados e testados;
- log completo sanitizado, status, saída do comando, duração e resultado;
- validação pós-flash: UUID/serial esperado, Klipper/Moonraker ready quando aplicável e ausência de erro crítico;
- rollback manual exibido com binário anterior, comando anterior e passos de recuperação;
- UI com estado crítico, travas, execução, validação, falha e rollback;
- documentação em `RUNBOOK.md`, `TESTES.md`, `TELAS.md`, `BUGS.md` se houver risco conhecido e `DECISOES.md` para a política de flash real.

Lotes:

1. Checklist e política de segurança por método de flash.
2. Preflight real read-only por placa.
3. Planejamento de comando e confirmação textual.
4. Execução supervisionada de um método inicial de baixo escopo.
5. Validação pós-flash e histórico.
6. Rollback manual e documentação operacional.
7. UI crítica de flash supervisionado.

Critério de aceite:

- flash real não existe sem checklist completo, preflight aprovado e confirmação textual;
- o fluxo bloqueia flash se houver impressão em andamento, placa ambígua, artefato ausente ou método não suportado;
- logs não expõem segredo e são suficientes para suporte;
- rollback manual é exibido antes e depois da execução;
- falha deixa estado claro: não tentado, em execução, falhou, validado ou requer recuperação manual;
- validação real em hardware acompanhado é obrigatória antes de considerar o pacote operacional;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado localmente.
- Backend expõe `POST /api/setup/flash/preflight`, `POST /api/setup/flash/plan`, `POST /api/setup/flash/execute` e `GET /api/setup/flash/history`.
- Preflight remoto é read-only e valida checklist, artefato remoto, estado de impressão, `flash_can.py`, `klippy-env`, `canbus_query`, UUID esperado e `printer/info`.
- Plano exibe comando `PLAN`, frase específica por placa/método, bloqueios e rollback manual antes da execução.
- Execução real inicial suporta somente CAN/Katapult e fica bloqueada por padrão: exige frase `FLASH_<PLACA>_CAN_KATAPULT`, checklist aprovado, preflight aprovado e `PRINTORA_REMOTE_FLASH_MODE=remote`.
- Métodos USB/DFU e manual aparecem como opções bloqueadas até implementação específica.
- Execução CAN/Katapult copia o artefato para backup remoto de suporte, executa `flash_can.py`, registra log/duração/hash e roda validação pós-flash sem editar `printer.cfg`, sem restart e sem update.
- Histórico local `setup_flash_runs` registra tentativas, plano, comando/log, rollback e status sem senha, token ou caminho de chave privada.
- UI `Setup do Zero` ganhou seção Flash supervisionado com preflight, plano, confirmação, rollback e histórico.
- Validação de fechamento: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

## PKG-38: Validação Final Da Impressora Klipper

Objetivo:

Criar validação final guiada para confirmar que a impressora montada ficou operacional após setup, CAN, firmware e flash, gerando relatório técnico de aceite.

Contexto inicial:

- hardware alvo inicial: BTT Pi v1.2, U2C, Octopus Pro v1.1 STM32H723 e EBB36 v1.2;
- este pacote consolida os resultados dos pacotes anteriores e não substitui calibração mecânica completa;
- o foco é provar que a base Klipper/Moonraker/Mainsail/Printora está funcional e diagnosticável.

Entregáveis:

- checklist final por impressora: serviços, Moonraker, Klipper, Mainsail/Fluidd, Printora, `can0`, UUIDs, MCUs, configs, temperaturas e erros recentes;
- validação read-only de `printer/info`, `server/info`, logs recentes, update manager e status CAN;
- validação de configuração mínima: includes existentes, MCUs referenciadas, serial/canbus UUIDs presentes e sem erro crítico conhecido;
- relatório sanitizado de aceite com hardware, versões, artefatos de firmware, UUIDs, status CAN, serviços e pendências;
- estados claros: aprovado para calibração, aprovado com observação, bloqueado, requer intervenção manual;
- UI de fechamento do setup com copiar relatório e exportar Markdown sanitizado;
- documentação em `RUNBOOK.md`, `TESTES.md`, `TELAS.md` e vínculo com relatórios sanitizados existentes.

Lotes:

1. Contrato de checklist final e estados de aceite.
2. Coleta read-only de serviços, Moonraker, Klipper, CAN e logs.
3. Validação de config mínima e UUIDs.
4. Relatório sanitizado de aceite.
5. UI de fechamento do setup.
6. Validação em hardware real acompanhado.

Critério de aceite:

- validação final não executa G-code perigoso, não move eixo, não aquece hotend/mesa e não altera configuração;
- relatório remove segredos, tokens, IPs sensíveis e caminhos locais quando necessário;
- bloqueios são acionáveis e apontam o pacote/etapa provável de correção;
- aceite diferencia base eletrônica/software pronta de calibração mecânica ainda pendente;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado localmente.
- Backend expõe `POST /api/setup/final-validation/run` e `GET /api/setup/final-validation/history`.
- Validação final remota é read-only e coleta serviços, `server/info`, `printer/info`, `print_stats`, temperaturas, Update Manager, CAN, UUIDs, resumo de configs e trechos recentes de log.
- O fluxo não envia G-code, não move eixo, não aquece hotend/mesa, não reinicia serviços e não altera arquivos.
- Aceite retorna estados `approved_for_calibration`, `approved_with_notes`, `blocked` e `needs_manual_intervention`.
- Relatório Markdown sanitizado remove caminhos locais, IPs/URLs e padrões sensíveis antes de exibir/copiar.
- Histórico local `setup_final_validation_runs` registra alvo, interface, UUIDs esperados, checks, relatório e status sem senha, token ou caminho de chave privada.
- UI `Setup do Zero` ganhou seção Validação final com UUIDs esperados, paths de config/log, checks, status e copiar relatório.
- Validação de fechamento: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 CHECK_STRICT_RUNTIME_NAMES=1 ./check.sh`.

## PKG-39: Autenticação, Usuários E Organização

Objetivo:

Criar a base de autenticação, identidade e isolamento para o Printora publicado em nuvem ou servidor dedicado, garantindo que cada usuário acesse apenas suas próprias impressoras ou as impressoras de organizações às quais foi vinculado.

Contexto inicial:

- o Printora nasceu como ferramenta local, sem necessidade de login obrigatório;
- a operação remota exige autenticação, ownership, tenant opcional e permissões antes de expor agentes conectados pela internet;
- o modelo principal deve ser usuário-first: email e senha são os únicos campos obrigatórios no cadastro inicial;
- organização deve existir como recurso opcional para compartilhamento: um usuário pode operar sozinho ou criar uma organização e convidar/vincular outros usuários;
- o desenvolvimento inicial deve usar SQLite para acelerar entrega e validação local;
- a modelagem e a camada de persistência devem evitar dependências desnecessárias de SQLite para permitir migração futura para Postgres quando a operação cloud exigir;
- este pacote deve ser entregue antes de cadastro cloud de impressoras, pareamento de agente ou comandos remotos.

Entregáveis:

- base técnica inicial em SQLite, com SQL idempotente e contratos preparados para migração futura para Postgres;
- modelo de usuário com email e senha obrigatórios, e contatos opcionais como WhatsApp, Telegram e outras redes sociais;
- modelo de organização opcional e vínculo usuário-organização;
- login, logout e sessão/JWT com expiração;
- senha armazenada com hash forte, sem segredo em texto puro;
- usuário administrador inicial por bootstrap seguro;
- middleware/dependência de autenticação nos endpoints cloud;
- isolamento por usuário e por organização nas consultas e respostas;
- política mínima de papéis: proprietário/admin e operador, aplicável a organização quando existir;
- autenticação de dois fatores opcional por usuário;
- exigência de autenticação reforçada/step-up para ações destrutivas ou críticas na impressora;
- comunicação segura entre servidor cloud e agente, sem credencial permanente exposta ao usuário;
- UI de login e estado autenticado;
- UI de cadastro com email e senha obrigatórios e contatos opcionais;
- UI/estado para habilitar, desabilitar e validar 2FA opcional;
- fluxo de desafio adicional antes de operações destrutivas quando configurado ou exigido pela ação;
- documentação em `RUNBOOK.md`, `TESTES.md`, `TELAS.md` e decisão em `DECISOES.md` se houver escolha de mecanismo de sessão/token.

Lotes:

1. Decisão de persistência inicial em SQLite e diretrizes de portabilidade futura para Postgres.
2. Modelo de usuário, contatos opcionais, organização opcional e SQL idempotente.
3. Serviço de autenticação, hash de senha e emissão de sessão/JWT.
4. Middleware de autenticação e isolamento por usuário/organização.
5. Bootstrap seguro do primeiro administrador.
6. Autenticação de dois fatores opcional e step-up auth para ações destrutivas.
7. UI de cadastro, login/logout, sessão expirada e estado autenticado.
8. Testes de contrato, permissão, isolamento, 2FA e step-up auth.

Critério de aceite:

- usuário não autenticado não acessa rotas cloud protegidas;
- usuário autenticado só enxerga seus próprios dados ou dados de organizações às quais pertence;
- organização não é obrigatória para uso individual;
- email e senha são os únicos campos obrigatórios no cadastro;
- contatos como WhatsApp, Telegram e redes sociais são opcionais e não bloqueiam cadastro;
- persistência inicial funciona em SQLite sem exigir Postgres para desenvolvimento;
- decisões de schema, tipos e repositórios não bloqueiam migração futura para Postgres;
- senha, token e segredo não aparecem em logs, banco em texto puro, resposta de API ou Git;
- sessão expirada falha com erro acionável e seguro;
- 2FA pode ser habilitado por usuário e exigido como step-up em operações destrutivas;
- operações destrutivas protegidas não executam apenas com sessão simples quando a política exigir autenticação reforçada;
- comunicação agente-servidor usa credencial segura, revogável e não exposta novamente ao usuário;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado localmente.
- Desenvolvimento inicial usa SQLite com script idempotente `backend/sql/026_auth_identity.sql`.
- Isolamento operacional complementado por `backend/sql/027_printer_ownership.sql` e `backend/sql/028_operational_ownership.sql`.
- Backend expõe cadastro, login, logout, sessão bearer, `/api/auth/me`, organizações opcionais, vínculo de membros, setup/enable/disable de 2FA, step-up auth e credenciais de agente.
- Email e senha são obrigatórios no cadastro; nome, WhatsApp, Telegram e redes sociais são opcionais.
- Organização é opcional: usuário pode operar individualmente ou criar organização para compartilhar acesso.
- Impressoras possuem dono e organização opcional; usuário só lista/acessa impressoras próprias ou compartilhadas por organização.
- Rotas operacionais protegidas validam sessão quando houver usuários cadastrados; histórico de setup e update do Printora também fica vinculado ao usuário/organização.
- Endpoints legados sem `printer_id` não caem mais no Moonraker global quando há sessão cloud; usam impressora visível do usuário ou retornam 404.
- Senhas usam hash PBKDF2; tokens, desafios, step-up e credenciais de agente são persistidos por hash.
- Segredo 2FA é protegido localmente e credencial completa do agente é retornada apenas na criação.
- Operações destrutivas da tela Operação passam a exigir step-up quando chamadas com sessão autenticada, preservando o modo local sem login obrigatório.
- Usuário anônimo não vê shell, menu, impressoras ou telas internas; vê apenas login/cadastro.
- UI `Conta` permite cadastro/login, sessão autenticada, organizações, membros, 2FA, step-up e credenciais de agente.
- Testes focados: `cd backend && uv run pytest tests/test_auth.py -q`.
- Build frontend: `npm --prefix frontend run build`.

## PKG-40: Gestão Cloud De Impressoras

Objetivo:

Criar a gestão de impressoras vinculadas a usuários/organizações no Printora publicado, separando o cadastro cloud da descoberta local em rede e preparando o vínculo com agentes remotos.

Contexto inicial:

- o cadastro atual de impressoras é local e depende de acesso de rede ao Moonraker;
- no modelo cloud, a impressora pertence a uma organização e pode estar offline até o agente parear;
- este pacote não instala agente e não executa comandos remotos.

Entregáveis:

- cadastro cloud de impressora por organização;
- campos de identificação operacional: nome, modelo, localização, tags e observações;
- status derivado do agente: sem agente, aguardando pareamento, online, offline, degradado, revogado;
- vínculo entre impressora e agente atual;
- listagem "minhas impressoras" filtrada por organização;
- detalhe da impressora com último contato, último snapshot e capacidade conhecida quando existir;
- revogação/desvinculação segura de agente;
- UI de lista, detalhe, criação e edição separadas;
- atualização de `TELAS.md`, `TESTES.md` e `RUNBOOK.md`.

Lotes:

1. Modelo cloud de impressora e SQL idempotente.
2. Endpoints de CRUD protegidos por organização.
3. Estados operacionais sem agente e com agente.
4. UI de lista/detalhe/criação/edição.
5. Revogação e desvinculação de agente.
6. Testes de isolamento e ownership.

Critério de aceite:

- uma organização não acessa impressoras de outra;
- cadastro cloud não tenta conectar no Moonraker diretamente;
- impressora sem agente aparece claramente como aguardando pareamento;
- revogação impede novas comunicações do agente antigo;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado localmente.
- SQL `backend/sql/029_agent_pairing.sql` cria tokens de pareamento, agentes pareados e eventos sanitizados.
- Backend expõe geração/revogação de token por impressora, troca pública token -> credencial operacional, heartbeat, snapshot e fila vazia autenticados por credencial do agente.
- Token de pareamento é curto, expira, é uso único e pode ser revogado.
- Credencial operacional é retornada apenas na troca ou rotação; listagens mostram somente prefixo/status.
- Agente possui identidade estável, versão, plataforma, capacidades, último contato, revogação e rotação de credencial.
- Agente revogado ou credencial antiga após rotação não autentica em heartbeat, snapshot ou jobs.
- UI na tela Impressoras permite gerar token, copiar segredo uma vez, listar/revogar tokens, listar/revogar agentes e rotacionar credencial.
- Testes focados: `cd backend && uv run pytest tests/test_agent_pairing.py -q`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

## PKG-41: Pareamento Seguro Do Agente

Objetivo:

Implementar o pareamento entre uma impressora cloud e um agente instalado no sistema operacional da impressora, usando token curto de uso único para trocar por uma credencial permanente, revogável e rotacionável.

Contexto inicial:

- o agente precisa ser instalado em ambientes atrás de NAT/firewall;
- o servidor não deve depender de entrar na rede local da impressora;
- o token de pareamento deve ter vida curta e não deve virar credencial operacional permanente.

Entregáveis:

- geração de token curto de pareamento por impressora;
- expiração, uso único e revogação de token;
- endpoint para o agente trocar token por credencial operacional;
- identidade estável do agente com versão, plataforma e capacidades;
- rotação/reemissão de credencial operacional;
- auditoria de pareamento, falha, revogação e rotação;
- UI para gerar, copiar, expirar e revogar token;
- mensagens claras para token expirado, inválido, já usado ou de outra organização.

Lotes:

1. Modelo de token de pareamento e credencial de agente.
2. Geração/expiração/revogação por usuário autorizado.
3. Endpoint de troca token -> credencial operacional.
4. Auditoria e logs sanitizados.
5. UI de pareamento na tela da impressora.
6. Testes de uso único, expiração, ownership e revogação.

Critério de aceite:

- token curto não funciona após expirar, ser usado ou ser revogado;
- credencial operacional não é exibida novamente ao usuário;
- logs não registram token completo nem credencial;
- agente revogado não consegue heartbeat, snapshot ou job;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado localmente.
- Agente criado em Go em `agent/`, sem dependências externas além da biblioteca padrão.
- CLI `printora-agent` suporta `run`, `once`, `doctor`, `config-sample`, `store-credential` e `systemd`.
- Config local JSON e arquivo de credencial separado usam permissões restritas (`0600`).
- Cliente Moonraker coleta somente endpoints read-only locais: `server/info`, `printer/info`, `print_stats`, temperaturas e Update Manager quando disponível.
- Heartbeat e snapshot usam HTTPS/HTTP com keep-alive e credencial operacional Bearer do PKG-41.
- Fila local JSONL limitada guarda eventos pendentes para retry sem persistir segredo.
- Logs rotativos passam por redaction de tokens `ptr_agent_*`, `ptr_pair_*` e `ptr_sess_*`.
- `doctor` diferencia falha de config, permissão, credencial, Moonraker e API.
- Serviço systemd inicial entregue em `agent/systemd/printora-agent.service`.
- Testes Go cobrem redaction, permissão de credencial, coleta read-only, header Bearer e fila local.
- Cross-build validado para `linux/arm64`.
- Fechamento do pacote: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

## PKG-42: Agente Remoto Base

Objetivo:

Criar o agente local do Printora para rodar no sistema operacional da impressora, coletar dados locais do Moonraker/Klipper e manter comunicação segura com o servidor cloud sem depender da mesma rede do usuário.

Contexto inicial:

- o agente deve abrir conexões de saída para o servidor, pois a impressora pode estar atrás de NAT, CGNAT ou firewall;
- o agente precisa ser seguro, atualizável e resiliente a queda de internet;
- este pacote cobre a base local e leituras read-only, não a paridade completa de comandos.

Entregáveis:

- projeto do agente com CLI/serviço compatível com Linux/Raspberry/BTT Pi inicialmente;
- arquivo de configuração local com permissões restritas;
- armazenamento local seguro da credencial operacional;
- cliente local Moonraker HTTP/WebSocket em `127.0.0.1:7125` ou endpoint configurado;
- heartbeat com versão, plataforma, capacidades, uptime e estado local;
- snapshot read-only básico: `server/info`, `printer/info`, `print_stats`, temperaturas e Update Manager quando disponível;
- fila local resiliente para eventos pendentes sem armazenar payload sensível desnecessário;
- logs rotativos e sanitizados;
- comando `doctor` do agente para suporte.

Lotes:

1. Estrutura do agente, config local e CLI `doctor`.
2. Cliente Moonraker read-only e coleta básica.
3. Heartbeat autenticado com credencial operacional.
4. Fila local e retry seguro.
5. Logs rotativos com redaction.
6. Serviço systemd inicial e documentação operacional.
7. Testes locais com fixtures Moonraker.

Critério de aceite:

- agente não exige que o servidor acesse a rede local da impressora;
- agente não executa G-code, restart, update, build ou flash neste pacote;
- queda de internet não perde estado crítico e não vaza segredo em logs;
- `doctor` diferencia falha de config, credencial, rede, Moonraker e permissão;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado em 2026-05-31.

Implementado:

- agente Go em `agent/` com CLI `run`, `once`, `doctor`, `config-sample`, `store-credential` e `systemd`;
- config JSON, credencial separada com permissão `0600`, fila JSONL local e logs com redaction;
- cliente Moonraker read-only para snapshot básico;
- heartbeat e snapshot autenticados via API com HTTP keep-alive;
- serviço systemd inicial e documentação operacional;
- `check.sh` executando `go test ./...` no agente;
- testes Go cobrindo redaction, permissão da credencial, coleta read-only, bearer header e fila local.

## PKG-43: Canal Remoto Agente-Servidor

Objetivo:

Criar o canal remoto rápido e resiliente entre agente e servidor, priorizando WebSocket seguro outbound e mantendo fallback por polling HTTPS para ambientes restritos.

Contexto inicial:

- raw socket manual aumenta custo operacional e segurança sem ganho claro;
- WebSocket seguro permite baixa latência e funciona bem com infraestrutura HTTP comum;
- fallback por polling evita bloquear instalações onde WebSocket esteja indisponível.

Entregáveis:

- endpoint WebSocket autenticado para agentes;
- protocolo de mensagens versionado: hello, heartbeat, snapshot, job, ack, nack, result, error e backpressure;
- fallback HTTPS polling para buscar jobs e enviar resultados;
- correlation ID por mensagem/job;
- controle de versão e capacidades do agente;
- retry, timeout, backoff e idempotência de resultado;
- limites de payload e proteção contra replay;
- testes de contrato e compatibilidade entre versões.

Lotes:

1. Contrato versionado do protocolo agente-servidor.
2. WebSocket autenticado e heartbeat em tempo real.
3. Jobs com ack/nack/result/error.
4. Fallback HTTPS polling.
5. Retry, backoff, idempotência e limites de payload.
6. Testes de contrato, desconexão e versão incompatível.

Critério de aceite:

- agente autenticado recebe apenas jobs da própria impressora/organização;
- reconexão não duplica execução concluída;
- falha de WebSocket usa fallback quando habilitado;
- payload sensível não é logado;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado em 2026-05-31.

Implementado:

- contrato versionado v1 com `hello`, `heartbeat`, `snapshot`, `job`, `ack`, `nack`, `result`, `error` e `backpressure`;
- WebSocket autenticado em `/api/agent/ws` com credencial operacional do agente;
- jobs persistidos em `agent_jobs`, sempre vinculados a `printer_id` e opcionalmente a `agent_id`;
- fallback HTTPS em `/api/agent/jobs/next`, `/ack`, `/nack`, `/result` e `/error`;
- correlation ID único por job, idempotência de resultado concluído e limite de payload de 64 KB;
- agente Go com WebSocket primário, backoff, fallback polling e execução segura de jobs `ping` e `snapshot`;
- testes backend de isolamento, WebSocket, versão incompatível e idempotência;
- testes Go de polling, ack/result, URL WebSocket segura e contrato HTTP.

## PKG-44: Instalador Online Assistido Do Agente

Objetivo:

Disponibilizar instalação online assistida do agente a partir do Printora cloud, com comando por plataforma, token de pareamento, diagnóstico pré-instalação e validação pós-instalação.

Contexto inicial:

- o usuário precisa instalar o agente diretamente no sistema operacional da impressora;
- o fluxo deve reduzir erro manual sem esconder riscos de permissão, systemd, Moonraker ou rede;
- este pacote distribui e ajuda a instalar, mas não implementa auto-update completo.

Entregáveis:

- página de instalação do agente por impressora;
- comando de instalação com token curto de pareamento;
- script de instalação Linux/Raspberry/BTT Pi com dry-run ou preflight;
- criação de usuário/serviço quando aplicável, com permissões mínimas;
- validação de Python/binário, systemd, rede, Moonraker e escrita em diretório local;
- confirmação pós-instalação: agente pareado, heartbeat recebido e versão esperada;
- instruções de uninstall e rollback local;
- documentação em `RUNBOOK.md` e `TELAS.md`.

Lotes:

1. Tela de instalação e comando com token curto.
2. Script instalador Linux com preflight.
3. Registro de serviço e diretórios com permissões corretas.
4. Validação pós-instalação integrada ao pareamento.
5. Uninstall/rollback local documentado.
6. Testes de script em modo seguro e docs.

Critério de aceite:

- instalador não grava token em logs;
- token curto é consumido uma vez e substituído por credencial operacional;
- falha de instalação mostra diagnóstico acionável;
- uninstall remove serviço/binário sem apagar dados do usuário sem confirmação explícita;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado em 2026-05-31.

Implementado:

- tela de instalação assistida na área Impressoras com comandos de preflight, instalação e uninstall;
- endpoint `POST /api/printers/{printer_id}/agent/install-plan` que gera token curto e comando por impressora;
- endpoint `GET /api/printers/{printer_id}/agent/install-status` para validar pareamento, heartbeat e versão esperada;
- endpoint público `GET /api/agent/install/linux.sh` para baixar o script sem segredo embutido;
- script Linux/Raspberry/BTT Pi com `--preflight`, `--apply --yes` e `--uninstall`;
- criação de diretórios, credencial `0600`, serviço systemd e usuário de serviço com permissões mínimas;
- testes de plano, isolamento, consumo único do token, status pós-instalação e redaction do token no preflight;
- documentação em `RUNBOOK.md`, `TELAS.md` e `TESTES.md`.

## PKG-45: Atualização Automática Do Agente

Objetivo:

Preparar o agente para atualização automática segura, com versionamento, verificação de release, download validado, backup, rollback e histórico.

Contexto inicial:

- o agente precisa evoluir junto com o servidor cloud;
- update remoto em software instalado na impressora é fluxo crítico e deve ter rollback;
- o verificador de releases do Printora usa GitHub Releases como fonte pública para releases do app, e o agente deve seguir fonte pública e validável equivalente.

Entregáveis:

- endpoint/manifesto de versão mínima, recomendada e bloqueada do agente;
- verificação periódica de update pelo agente;
- download seguro com hash/assinatura quando disponível;
- backup do binário/config antes de trocar versão;
- aplicação controlada com restart do serviço do agente, sem reiniciar Klipper/Moonraker;
- rollback automático se o agente não voltar saudável;
- histórico local e cloud de update;
- política de compatibilidade de protocolo por versão.

Lotes:

1. Contrato de versões e compatibilidade do agente.
2. Verificação de update e manifesto público.
3. Download validado e staging local.
4. Backup, troca de versão e restart do serviço do agente.
5. Health pós-update e rollback.
6. Histórico e observabilidade do update.
7. Testes de sucesso, falha, rollback e versão bloqueada.

Critério de aceite:

- update do agente não reinicia Klipper, Moonraker ou a impressora;
- hash/assinatura inválida bloqueia aplicação;
- falha pós-update restaura versão anterior quando possível;
- servidor consegue bloquear versões incompatíveis;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado em 2026-05-31.

Implementado:

- manifesto público `/api/agent/update/manifest` com versão mínima, recomendada, bloqueios e compatibilidade de protocolo;
- endpoint autenticado `/api/agent/update/reports` para histórico cloud do update do agente;
- histórico por impressora em `/api/printers/{printer_id}/agent/update-history`, isolado por usuário/organização;
- agente Go consultando manifesto, bloqueando versão/protocolo incompatível e detectando release por plataforma;
- download para staging com SHA-256 obrigatório;
- backup do binário e config antes da troca;
- aplicação controlada trocando somente o binário do agente;
- health command opcional, rollback automático quando health/restart falha e restart apenas do serviço `printora-agent` quando habilitado;
- estado local do update em JSON e relatório sanitizado ao backend;
- testes de manifesto, relatório/histórico, hash inválido, versão bloqueada, sucesso e rollback.

## PKG-46: Paridade Funcional Remota

Objetivo:

Fazer o agente remoto enviar e receber todas as informações que o Printora já trabalha hoje no modo local, preservando segurança, estados offline e contratos existentes.

Contexto inicial:

- o Printora já possui auditoria, snapshots, health, backups, relatórios, CAN, Update Manager, firmware/dry-run, flash supervisionado e validação final;
- o modelo cloud precisa reutilizar esses contratos sem exigir que o servidor acesse a rede local;
- operações mutáveis continuam dependendo dos gates de segurança dos pacotes existentes.

Entregáveis:

- mapa de paridade entre funcionalidades locais existentes e jobs remotos do agente;
- coleta remota de auditoria read-only, snapshots, health, temperaturas, Update Manager, CAN e validação final;
- geração remota de relatórios sanitizados;
- suporte a backups quando aplicável, com política clara de payload e armazenamento;
- jobs remotos para dry-run/preview de ações operacionais existentes;
- suporte a firmware/build/flash apenas respeitando gates já definidos;
- normalização de estados offline usando último estado conhecido;
- testes de contrato por família de funcionalidade.

Lotes:

1. Inventário de contratos locais e matriz de paridade.
2. Jobs read-only: auditoria, snapshots, health e temperaturas.
3. Jobs de Update Manager, CAN e validação final.
4. Relatórios sanitizados via agente.
5. Backups e payloads grandes com limites e retenção.
6. Dry-runs e previews de ações existentes.
7. Integração com firmware/build/flash mantendo gates.
8. Testes de contrato e regressão dos fluxos principais.

Critério de aceite:

- funcionalidades remotas usam o agente como executor local, não acesso direto do servidor ao Moonraker;
- paridade diferencia implementado, bloqueado por segurança, offline e não suportado;
- payload sensível é sanitizado antes de sair da impressora quando aplicável;
- ações críticas continuam exigindo confirmação, preflight, backup e rollback;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado em 2026-05-31.

Implementado:

- matriz de paridade remota em `/api/printers/{printer_id}/remote/parity`;
- criação de jobs remotos seguros em `/api/printers/{printer_id}/remote/parity/jobs`;
- estados `implemented`, `cached`, `offline`, `blocked` e `not_supported` por funcionalidade;
- jobs read-only via agente para auditoria, snapshot, health, temperaturas, Update Manager, CAN e validação final;
- relatório sanitizado via agente;
- previews/dry-runs remotos para backup, operação e firmware sem executar comandos mutáveis;
- bloqueio explícito de backup real grande, build/flash remoto e operação mutável até PKG-47;
- agente Go executando jobs de paridade com sanitização antes do envio;
- testes de contrato backend e agente para isolamento, estado cached/offline/bloqueado e sanitização.

## PKG-47: Operação Segura Remota

Objetivo:

Criar a camada de segurança para executar operações remotas mutáveis via agente, com permissões, confirmação explícita, preflight, auditoria, rollback e bloqueios por estado da impressora.

Contexto inicial:

- operação remota aumenta risco porque o usuário pode acionar ações fora da rede local;
- fluxos perigosos do Printora já exigem confirmação e rollback;
- este pacote consolida autorização e execução segura para comandos remotos.

Entregáveis:

- matriz de permissões por tipo de operação remota;
- preflight obrigatório para ações mutáveis;
- confirmação textual ou equivalente forte para operações críticas;
- bloqueio quando impressora estiver imprimindo ou estado for incompatível;
- auditoria de solicitação, autorização, execução, resultado e rollback;
- política de expiração/cancelamento de jobs mutáveis;
- revisão de logs para não gravar segredo ou payload sensível;
- UI de confirmação remota com riscos e rollback antes da execução.

Lotes:

1. Matriz de operações remotas e criticidade.
2. Permissões e autorização por usuário/organização.
3. Preflight remoto obrigatório.
4. Confirmação forte e expiração de jobs mutáveis.
5. Auditoria e logs seguros.
6. UI de operação remota crítica.
7. Testes de bloqueio, permissão e estado incompatível.

Critério de aceite:

- operação mutável não executa sem usuário autorizado, agente válido, preflight aprovado e confirmação exigida;
- impressão em andamento bloqueia ações críticas quando detectável;
- auditoria permite reconstruir quem pediu, o que foi executado, quando, por qual agente e com qual resultado;
- rollback ou recuperação manual aparece antes de ações críticas;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Planejado.

## PKG-48: Observabilidade E Suporte Do Agente

Objetivo:

Criar superfície operacional para diagnosticar agentes e impressoras remotas, com saúde do agente, versão, latência, fila, falhas recentes, logs sanitizados e pacote de suporte.

Contexto inicial:

- operação cloud com agentes exige diagnóstico claro sem acessar diretamente a rede do cliente;
- suporte precisa diferenciar falha de internet, credencial, agente, Moonraker, Klipper, sistema operacional e versão incompatível;
- observabilidade deve ajudar o produto em runtime, sem vazar dados sensíveis.

Entregáveis:

- painel de saúde do agente por impressora;
- indicadores: online/offline, último contato, versão, protocolo, latência, fila pendente, último job e última falha;
- diagnóstico remoto `doctor` sob demanda;
- logs sanitizados recentes com retenção definida;
- pacote de suporte exportável com dados mínimos;
- alertas internos para agente desatualizado, revogado, sem heartbeat, fila acumulada e falha recorrente;
- documentação de troubleshooting em `RUNBOOK.md`;
- política de retenção/limpeza em `GOVERNANCA.md` ou `DECISOES.md` se houver persistência nova.

Lotes:

1. Modelo de saúde e eventos do agente.
2. Ingestão de métricas mínimas e falhas recentes.
3. Tela de saúde do agente.
4. Doctor remoto e pacote de suporte sanitizado.
5. Alertas internos e estados operacionais.
6. Retenção, limpeza e documentação de suporte.
7. Testes de sanitização, retenção e estados offline.

Critério de aceite:

- painel diferencia falha de agente, servidor, rede, credencial e Moonraker quando houver evidência;
- logs e pacote de suporte não incluem token, senha, chave privada ou payload sensível completo;
- dados persistidos têm retenção e limpeza definidas;
- suporte consegue orientar reinstalação, revogação, update ou correção local a partir do diagnóstico;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Planejado.
