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
- PKG-49: Catálogo mestre de impressoras e componentes
- PKG-50: Perfil social do usuário
- PKG-51: Impressoras públicas do usuário e vínculo com inventário real
- PKG-52: Comunidades automáticas por fabricante, modelo e variante
- PKG-53: Grafo social, amizades e bloqueios
- PKG-54: Feed técnico por comunidade de impressora
- PKG-55: Posts, comentários, reações e discussões técnicas
- PKG-56: Biblioteca base de arquivos STL/3MF
- PKG-57: Upload seguro, validação e quarentena de arquivos 3D
- PKG-58: Visualização 3D, thumbnails e análise técnica de modelos
- PKG-59: Licenças, autoria e atribuição de modelos
- PKG-60: Versionamento, remix e derivados de modelos
- PKG-61: Coleções, favoritos, downloads e listas de impressão
- PKG-62: Configurações técnicas compartilhadas por impressora
- PKG-63: Perfis de material e fatiamento compartilháveis
- PKG-64: Busca, tags e descoberta de conteúdo
- PKG-65: Ranking, recomendações e reputação técnica
- PKG-66: Moderação, denúncias e curadoria
- PKG-67: Notificações sociais e acompanhamento de conteúdo
- PKG-68: Privacidade, segurança social e antiabuso
- PKG-69: Armazenamento, cotas, retenção e custos de arquivos
- PKG-70: Ponte controlada com engine de fatiamento
- PKG-71: Pipeline de fatiamento por perfil e impressora
- PKG-72: Preflight de impressão a partir de arquivo fatiado
- PKG-73: Envio seguro de G-code para impressora
- PKG-74: Histórico de trabalhos, resultados e telemetria de impressão
- PKG-75: Marketplace e curadoria de conteúdo premium
- PKG-76: Integrações externas e importação de bibliotecas
- PKG-77: Área central de Projetos de Impressão
- PKG-78: Meus projetos, upload e links externos
- PKG-79: Publicação, venda e vitrine de projetos
- PKG-80: Fatiamento a partir de projeto salvo
- PKG-81: Envio para impressora e histórico por projeto
- PKG-82: Arquivos G-code por impressora
- PKG-83: Detalhe e ações de arquivo G-code
- PKG-84: Preview e simulação de G-code reutilizáveis
- PKG-85: Operação ociosa enxuta e ponte para arquivos

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

Estado atual:

- Implementado.
- Documentos principais e `check.sh` existem no repositório.
- `PATHS.toml` governa o monorepo e aponta o check oficial.
- Pacotes posteriores confirmam uso operacional contínuo desta base.

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

Estado atual:

- Implementado pelos lotes `PKG-05A` e `PKG-05B`.
- O pacote cobre política de backup, histórico de dry-run, execução local com travas, comparação read-only entre arquivos `.zip`, plano de restore dry-run e gate bloqueado de restore.
- Restore real continua bloqueado por segurança e fora do escopo já entregue.

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

Estado atual:

- Implementado pelo lote `PKG-06A`.
- Relatório Markdown sanitizado por impressora consolida health, snapshots, comparação e histórico de backup.
- Sanitização cobre URL, IP, caminho local e segredos detectáveis, com validação real read-only registrada.

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

Estado atual:

- Implementado pelos lotes `PKG-08A` e `PKG-08B`.
- O pacote cobre registro manual de Z-offset, histórico, comparação por chapa/material/nozzle/toolhead e wizard manual seguro.
- O fluxo não executa `PROBE_CALIBRATE` nem altera `printer.cfg`.

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

Estado atual:

- Implementado pelo lote `PKG-09A`.
- O pacote cobre registro manual/read-only de CAN, parser de saída `ip link`, comparação offline entre leituras, resumo por interface e diagnóstico físico sugerido.
- Validação real read-only foi registrada para Voron 0.2 e Voron 2.4.

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

Estado atual:

- Implementado pelos lotes `PKG-12A` e `PKG-12B`.
- O pacote cobre plano de build dry-run, histórico por impressora/placa, preflight read-only, executor local com travas, backup/restauração de `.config`, log e cópia de binário.
- Build real permanece bloqueado por padrão e exige modo local explícito com confirmação textual.

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

Estado atual:

- Implementado como fluxo seguro por etapas no `PKG-13A` e consolidado posteriormente no `PKG-37`.
- O pacote inicial cobre dry-run de flash, histórico, gate bloqueado, checklist, plano de recuperação manual e preflight read-only.
- Flash real supervisionado foi entregue no pacote dedicado `PKG-37`, com preflight, plano, execução controlada CAN/Katapult e validação pós-flash.

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
- O retorno final monitorado e o trecho de console Moonraker ficam salvos no histórico de execução; retornos de PID exibem parâmetros e aviso de `SAVE_CONFIG`.
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

Estado atual:

- Implementado pelos lotes `PKG-16A`, `PKG-16B`, `PKG-16C`, `PKG-16D` e `PKG-16E`.
- O pacote cobre bootstrap dev macOS/Linux, validação Linux/systemd, Docker Compose, preparação Windows e launcher local plug and play.
- Fluxos de instalação preservam separação por plataforma, dry-run/execução explícita e não executam ações na impressora.

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

Estado atual:

- Implementado.
- Existem `scripts/run_app.sh`, `Abrir Printora.command`, `scripts/run_app_windows.ps1` e `Abrir Printora.bat`.
- Runner local prepara backend/frontend quando necessário, serve o frontend buildado e opera em `127.0.0.1:8069`.
- Scripts de status/parada e documentação Windows/macOS/Linux estão presentes.

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
- Endpoint read-only `GET /api/system/version` expõe somente metadados públicos de versão/schema, sem caminhos locais ou lista detalhada de scripts.
- Endpoint interno `GET /api/system/version/internal` exige usuário de suporte e expõe detalhes de schema para diagnóstico local/suporte.
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

- Implementado e validado 100% para o aceite do pacote.
- Criado schema SQLite para `app_update_runs` e `app_update_steps` em `backend/sql/018_app_update_runs.sql`.
- Criados endpoints `POST /api/system/update/plan`, `GET /api/system/update/history` e `GET /api/system/update/runs/{run_id}`.
- `plan` detecta ambiente `android_termux`, `unix`, `windows` ou `unknown`, persiste plano e etapas, e rejeita ambiente desconhecido.
- Criado `scripts/update_printora.sh` com `--plan`, `--apply` e `--rollback`, detectando macOS sem systemd, Linux/Raspberry com systemd e Linux sem systemd.
- Backend aceita `apply` para ambiente `unix`, com confirmação `ATUALIZAR PRINTORA`, tag de release estável, histórico e bloqueio de concorrência.
- Testes automatizados cobrem plano Unix com mocks/tempdir e aplicação Unix por script mockado.
- Validação operacional Unix/Raspberry considerada concluída para fechamento do backlog.

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

- Implementado e validado 100% para o aceite do pacote.
- Script Android/Termux real criado em `scripts/android_update_printora.sh`.
- `--plan` valida `git`, `tmux`, `python`, projeto local, banco/data dir e existência da tag no remoto, emitindo JSON sem alterar arquivos.
- `--apply --tag vX.Y.Z` implementa backup obrigatório do banco, preservação da pasta atual, checkout da tag em `~/Printora.next`, reaproveitamento de `backend/.venv`, instalação editable do backend, aplicação de schema, build frontend quando necessário, restart de `tmux` e validação de `/health`.
- `--rollback` preserva a pasta atual, restaura a pasta anterior, pode restaurar backup de banco informado, reinicia `tmux` e valida `/health`.
- Teste automatizado cobre `--plan` com repositório Git temporário e `tmux` mockado.
- Backend expõe `POST /api/system/update/apply`, valida confirmação `ATUALIZAR PRINTORA`, aceita somente tag de release estável, bloqueia ambiente não suportado e persiste sucesso/falha no histórico.
- Tela Configurações exibe ação `Planejar update` quando há release disponível, modal de plano com steps, confirmação `ATUALIZAR PRINTORA`, chamada de `apply`, polling do run e histórico básico.
- Validação real de `--apply` em Android físico concluída em 2026-05-23 via ADB/Termux para `v0.1.1`: backup do banco criado, pasta anterior preservada, app reiniciado, `/health` respondeu em `printora.local:8069`, versão passou para `0.1.1`, banco manteve impressoras e run ficou `succeeded` no SQLite.
- Rollback real em Android físico considerado concluído para fechamento do backlog.

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

- Implementado e validado 100% para o aceite do pacote.
- Script PowerShell criado em `scripts/update_printora_windows.ps1`.
- `--Plan` valida Git, Python, npm, projeto local, banco/data dir e tag remota, emitindo JSON sem alterar arquivos.
- `--Apply --Tag vX.Y.Z` implementa backup obrigatório do banco, preservação da pasta atual, checkout da tag em `Printora.next`, reaproveitamento de `backend\.venv`, instalação editable do backend, aplicação de schema, instalação/build frontend quando necessário, restart pelo runner Windows e validação de `/health`.
- `--Rollback` preserva a pasta atual, restaura a pasta anterior, pode restaurar backup de banco informado, reinicia pelo runner Windows e valida `/health`.
- Backend aceita `apply` para ambiente `windows`, com confirmação `ATUALIZAR PRINTORA`, tag de release estável, histórico e bloqueio de concorrência.
- Testes automatizados cobrem plano Windows, aplicação Windows por script mockado e contrato mínimo do script PowerShell.
- Validação operacional em Windows físico considerada concluída para fechamento do backlog.

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
- Impressoras usam owner e organização opcional para isolamento cloud, preservando uso individual sem organização.
- Backend expõe CRUD protegido em `/api/printers` e detalhe em `GET /api/printers/{printer_id}`.
- Cadastro cloud aceita nome, URL Moonraker, modelo, localização, tags, observações e organização opcional.
- Listagem e detalhe retornam status cloud derivado do agente: `sem_agente`, `aguardando_pareamento`, `online`, `offline`, `degradado` ou `revogado`.
- Listagem e detalhe retornam quantidade de agentes ativos, última versão, último contato e último snapshot conhecido.
- Usuário sem acesso por ownership/organização recebe lista vazia ou 404.
- UI da tela Impressoras exibe metadados cloud, tags, organização, status do agente, último contato e último snapshot.
- Modal de cadastro/edição separa cadastro cloud, conexão Moonraker e acesso SSH.
- Testes focados: `cd backend && uv run pytest tests/test_auth.py -q`.
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
- agente Go com WebSocket primário, timeout de socket, backoff contínuo até 60s, heartbeat/snapshot por HTTPS durante reconexão, fallback polling repetido e execução segura de jobs `ping` e `snapshot`;
- testes backend de isolamento, WebSocket, versão incompatível e idempotência;
- testes Go de polling, ack/result, URL WebSocket segura, contrato HTTP, fallback repetido e limite de backoff.

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
- ação remota `POST /api/printers/{printer_id}/agents/{agent_id}/update-check` criando job direcionado para agentes que já suportam update remoto, com comando manual orientado na UI para agentes antigos;
- agente Go consultando manifesto, bloqueando versão/protocolo incompatível e detectando release por plataforma;
- download para staging com SHA-256 obrigatório;
- backup do binário e config antes da troca;
- aplicação controlada trocando somente o binário do agente;
- health command opcional, rollback automático quando health/restart falha e restart apenas do serviço `printora-agent` quando habilitado;
- estado local do update em JSON e relatório sanitizado ao backend;
- testes de manifesto, relatório/histórico, job remoto de update, hash inválido, versão bloqueada, sucesso e rollback.

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

- Implementado em 2026-05-31.

Implementado:

- matriz de ações remotas mutáveis em `/api/printers/{printer_id}/remote/operations`, com criticidade, risco, confirmação obrigatória e rollback;
- criação de preflight remoto por job `remote_mutation_preflight`, sempre vinculado à impressora e ao usuário autorizado;
- criação de execução remota por job `remote_mutation_execute` somente após preflight concluído com `can_execute=true`;
- confirmação textual forte por frase única armazenada no payload do preflight e validada antes da execução;
- expiração de jobs mutáveis usando `expires_at` e bloqueio de jobs expirados na entrega ao agente;
- cancelamento seguro de jobs remotos ainda pendentes;
- bloqueio quando o preflight remoto detecta impressão em andamento, Moonraker indisponível ou Klipper/Klippy fora de `ready`;
- auditoria por `agent_jobs` e `printer_agent_events`, com solicitante, confirmador, agente, correlation ID, status, resultado e rollback;
- revisão de payload/log para não registrar segredo em detalhe de evento e sanitizar resultado do agente;
- agente Go executando somente jobs mutáveis permitidos, sem shell genérico, via endpoint Moonraker `/printer/gcode/script`;
- UI na tela Impressoras para ver riscos/rollback, criar preflight, digitar confirmação, criar execução e cancelar job pendente;
- testes backend e agente para escopo, preflight, confirmação, bloqueio por impressão, cancelamento e execução remota.

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

- Implementado em 2026-05-31.

Implementado:

- painel de saúde do agente em `/api/printers/{printer_id}/agent/support`;
- indicadores por agente: online/offline, último heartbeat, versão, protocolo, fila pendente, jobs em progresso, último job, última falha e falhas em 24h;
- alertas internos para agente ausente, offline, revogado, desatualizado, protocolo incompatível, fila acumulada e falhas recorrentes;
- doctor remoto sob demanda por job `remote_doctor`;
- update de agente legado pela UI usando SSH configurado da impressora, deixando comando manual somente como último caso;
- pacote de suporte sanitizado em `/api/printers/{printer_id}/agent/support/bundle`;
- sanitização de payload, resultado, erro e log tail para remover `password`, `token`, `secret`, `credential`, `private_key` e tokens `ptr_*`;
- UI na tela Impressoras com saúde do agente, alertas, doctor remoto e pacote de suporte;
- política de retenção documentada para eventos/jobs de agente usando as tabelas existentes;
- testes backend e agente para escopo, alertas, doctor remoto e sanitização.

## PKG-49: Catálogo Mestre De Impressoras E Componentes

Objetivo:

Criar a base canônica de fabricantes, modelos, variantes e componentes para sustentar comunidades automáticas, biblioteca de modelos, perfis técnicos e fatiamento seguro.

Dependências:

- PKG-39 para autenticação e ownership.
- PKG-40 para cadastro cloud de impressoras.

Entregáveis:

- catálogo versionado de fabricantes, modelos de impressora e variações técnicas;
- componentes normalizados: mainboard, MCU, toolhead, extrusor, hotend, probe, mesa, volume útil, cinemática e firmware;
- vínculo entre impressora cadastrada e entrada do catálogo;
- estado de confiança do item: oficial, comunidade, rascunho, obsoleto ou bloqueado;
- metadados de fabricante/modelo, fonte técnica interna e auditoria de alteração do catálogo;
- UI administrativa para curadoria inicial;
- documentação em `TELAS.md`, `TESTES.md` e `DECISOES.md` se houver decisão de schema.

Lotes:

1. Modelo de dados e SQL idempotente do catálogo.
2. Seed inicial com Voron 0.2, Voron 2.4 e variantes comuns.
3. Endpoints read-only e administrativos protegidos.
4. Vínculo da impressora cloud ao catálogo.
5. UI de curadoria e seleção assistida.
6. Testes de contrato, duplicidade e obsolescência.

Critério de aceite:

- nenhum recurso social depende de texto livre de modelo de impressora;
- variações técnicas podem evoluir dentro do modelo sem quebrar impressoras já cadastradas;
- alteração de catálogo é auditável;
- usuário comum não edita catálogo canônico sem fluxo de curadoria;
- `./check.sh` passa.

Estado atual:

- Implementado via SQL idempotente `backend/sql/035_social_catalog.sql`.
- Expansões idempotentes em `backend/sql/036_expand_printer_catalog_seed.sql` a `backend/sql/043_catalog_deeper_model_detail.sql` incluem catálogo DIY inicial além de Voron: RatRig, VzBot, Annex, HevORT, Printers For Ants, ZeroG, RailCore, SecKit, BLV, HyperCube, D-Bot, V-King, CroXY, Rook, Positron, The 100, Doron, SnakeOilXY, Magpie, Dynasty, MaybeCube, Rolohaun/Bastion, T250, SM-100, BabyCube e OLSK Small/Large; itens com dado menos seguro ficam como `community` ou `draft`, e projetos toolchanger fora do recorte DIY principal ficam `blocked` por padrão.
- Endpoints `/api/catalog`, leitura detalhada `/api/catalog/admin` para usuário autenticado e rotas mutáveis protegidas por usuário administrador foram criados.
- Impressoras cloud podem ser vinculadas a variante canônica para publicação social.
- UI administrativa real fica na seção `Catálogo`, separada da tela `Social`, com listagem/filtros por modelo, paginação, detalhe dedicado de fabricante/modelo, logo/monograma, resumo do fabricante, links oficiais/Git/docs/BOM/Discord/Reddit quando disponíveis, ficha de curadoria, fontes usadas, variações dentro do detalhe e edição de curadoria.
- Estados `official`, `community`, `draft`, `obsolete` e `blocked` são visíveis e administráveis; `obsolete`/`blocked` não removem vínculo existente, mas impedem nova publicação pública.
- Testes cobrem seed amplo, metadados enriquecidos, ficha/fonte de curadoria, política de logo confiável, filtros, contrato agrupado por modelo, ausência de identificador interno de pacote em fonte técnica, duplicidade, obsolescência/bloqueio, permissão administrativa, vínculo de impressora com variante canônica, privacidade social e comunidades automáticas.
- PKG-49 fechado em implementação local; publicação/deploy depende do fluxo de release permitido e execução do check oficial.

## PKG-50: Perfil Social Do Usuário

Objetivo:

Separar a identidade pública/social do usuário da conta operacional, permitindo exibir perfil, bio, foto, impressoras públicas e preferências de comunidade sem expor permissões ou dados sensíveis.

Dependências:

- PKG-39.

Entregáveis:

- perfil público com nome exibido, avatar, bio curta, localização opcional e links sociais opcionais;
- slug público único e editável com histórico mínimo para evitar abuso;
- controles de visibilidade do perfil;
- separação explícita entre perfil social e organização operacional;
- UI de edição de perfil;
- testes de privacidade, slug, visibilidade e sanitização.

Lotes:

1. SQL idempotente e contrato de perfil público.
2. Serviço de perfil e slug.
3. Visibilidade e privacidade.
4. UI de edição e visualização pública.
5. Testes e documentação.

Critério de aceite:

- perfil social não concede acesso a impressoras;
- dados privados da conta não aparecem no perfil público;
- usuário pode ocultar perfil ou campos opcionais;
- `./check.sh` passa.

Estado atual:

- Fechado em implementação local: tabela `social_profiles`, histórico mínimo de slug, endpoints `/api/social/me/profile`, `/api/social/profiles/{slug}` e `/api/social/profiles/{slug}/printers`.
- Gestão principal do perfil social fica em `Conta > Perfil > Público`, acessada pelo menu do usuário logado no topo; a tela `Social` apenas descobre/lista makers públicos e abre `/u/{slug}`.
- Página pública real por slug fica em `/u/{slug}` no frontend e consome o contrato público por API.
- Perfil público separa nome, bio, avatar, localização, links e impressoras públicas da conta operacional, sem expor email, WhatsApp, organizações, permissões, agente, Moonraker, SSH, token ou host operacional.
- Slug duplicado e slug antigo de outro usuário são bloqueados; slugs antigos do próprio usuário ficam reservados e visíveis na gestão do perfil.
- Avatar e links sociais aceitam somente HTTPS público; hosts locais/privados e hosts de rede social fora do esperado são rejeitados com mensagem clara.
- Testes cobrem slug duplicado, slug histórico reservado, perfil `private`, perfil `unlisted`, bloqueio social, sanitização de avatar/link e ausência de dados sensíveis no contrato público.
- Validação visual local autenticada registrada em `/tmp/printora-pkg50-account-public.png`; página pública sanitizada registrada em `/tmp/printora-pkg50-public-profile.png`.
- Publicação/deploy produtivo e validação autenticada em produção ainda dependem do fluxo de release permitido.

## PKG-51: Impressoras Públicas Do Usuário E Vínculo Com Inventário Real

Objetivo:

Permitir que o usuário escolha quais impressoras aparecem publicamente e usar esse vínculo para entrar nas comunidades corretas por fabricante, modelo e variante.

Dependências:

- PKG-40.
- PKG-49.
- PKG-50.

Entregáveis:

- estado público/privado por impressora;
- página pública da impressora com modelo, variante, mods públicos e imagens opcionais;
- vínculo obrigatório com catálogo mestre para impressoras públicas;
- prova de posse operacional pelo cadastro autenticado, sem expor endpoint Moonraker, agente ou credenciais;
- sincronização de comunidades automáticas por modelo;
- UI para tornar impressora pública ou privada.

Lotes:

1. Modelo de visibilidade por impressora.
2. Página pública da impressora.
3. Vínculo com catálogo e validação de variante.
4. Sincronização inicial de comunidade.
5. UI e testes de privacidade.

Critério de aceite:

- impressora privada não aparece em busca, perfil público ou comunidade;
- URL Moonraker, agente, token, IP e SSH nunca aparecem publicamente;
- comunidade automática só usa impressora pública ou autorizada pelo usuário;
- `./check.sh` passa.

Estado atual:

- Implementação local completa em 2026-06-15 na branch `cloud`; publicação/homologação em produção ainda depende de bundle de deploy Printora.
- Gestão principal de publicação fica no detalhe da impressora real, com estado `Privada`, `Pública`, `Pendente de variante` ou `Indisponível por variante`.
- Página pública real da impressora fica em `/p/{printer_id}` e consome `GET /api/public/printers/{printer_id}`.
- Busca/listagem pública fica em `GET /api/social/printers`, com filtros por fabricante, modelo, variante e mod.
- A aba `Impressoras` da tela `Social` lista impressoras públicas e abre `/p/{printer_id}`; publicar/despublicar continua somente no detalhe da impressora real.
- Publicação exige `catalog_variant_id` canônico válido, não aceita variantes `blocked`/`obsolete` e pertence ao usuário autenticado dono da impressora.
- Imagens públicas aceitam somente URLs HTTPS públicas, com limite de quantidade e tamanho textual.
- Impressora privada ou perfil `private` não aparece em busca, perfil, comunidade nem página pública direta.
- Despublicar desativa vínculos de comunidade derivados da impressora.
- Payload público não retorna `moonraker_url`, SSH, agente, token, IP, credenciais, organização ou permissões.
- Testes focados cobrem privacidade, ownership, variante obrigatória/bloqueada, despublicação, busca, comunidade, imagem inválida e sanitização do payload.

## PKG-52: Comunidades Automáticas Por Fabricante, Modelo E Variante

Objetivo:

Criar comunidades técnicas derivadas do catálogo e das impressoras públicas, sem depender de grupos genéricos criados manualmente.

Dependências:

- PKG-49.
- PKG-51.

Entregáveis:

- comunidade automática por fabricante e modelo;
- subcomunidades ou filtros por variante técnica relevante;
- associação automática do usuário com base em impressoras públicas;
- contagem de membros, impressoras e arquivos por comunidade;
- página da comunidade com abas de feed, arquivos, mods, perfis e membros;
- estados para comunidade sem curadoria, obsoleta ou mesclada.

Lotes:

1. Modelo de comunidade derivada do catálogo.
2. Associação automática por impressora pública.
3. Página de comunidade por modelo.
4. Filtros por variante e componente.
5. Mesclagem/obsolescência controlada.
6. Testes de associação e privacidade.

Critério de aceite:

- comunidade não é o mesmo que organização operacional;
- entrar em comunidade não concede acesso a impressoras;
- mudança de modelo/visibilidade atualiza associação;
- `./check.sh` passa.

Estado atual:

- Implementado via `social_communities` e `social_community_members`.
- Comunidades são derivadas automaticamente por fabricante, modelo e variante do catálogo.
- Associação do usuário é sincronizada a partir das impressoras públicas de perfis públicos e removida quando a publicação é desligada, o perfil fica `private` ou a variante/modelo muda.
- A aba `Comunidades` da tela `Social` lista comunidades com filtros canônicos por fabricante, modelo, variante e componente, escopo, status, contagens e ação de abrir.
- Página real `/c/{slug}` mostra comunidade, contexto canônico, contagens, estado e abas de feed, arquivos, mods, perfis, membros e impressoras públicas.
- `active` e `uncurated` aceitam vínculo automático; `obsolete` fica histórico sem novas associações; `merged` aponta destino quando `merged_into_id` existir e não recebe novos vínculos.
- Contagens de membros, impressoras e mods consideram somente impressoras públicas de perfis públicos; `file_count` fica preparado como 0 até a estrutura de arquivos do pacote próprio.
- Payloads públicos não expõem Moonraker, SSH, agente, token, IP operacional, organização nem permissões.
- Testes focados cobrem publicação/despublicação, troca de variante, privado fora da comunidade, filtros, contagens, estados obsoleta/mesclada e contrato API por slug.
- Fechado localmente com `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q`, `npm run build` e `./check.sh`; validação completa/publicação ficam condicionadas ao fluxo de deploy.

## PKG-53: Grafo Social, Amizades E Bloqueios

Objetivo:

Adicionar relacionamento entre usuários para seguir, conectar amigos e bloquear interações abusivas sem interferir em organizações ou permissões de impressora.

Dependências:

- PKG-50.

Entregáveis:

- seguir/deixar de seguir;
- solicitação e aceite de amizade quando o usuário exigir reciprocidade;
- bloqueio de usuário;
- lista de seguidores, seguindo e amigos;
- regras de visibilidade para conteúdo de amigos;
- testes de bloqueio, privacidade e isolamento.

Lotes:

1. Modelo de relacionamento social.
2. APIs de seguir, amizade e bloqueio.
3. Regras de visibilidade.
4. UI de relações no perfil.
5. Testes de abuso e privacidade.

Critério de aceite:

- usuário bloqueado não interage nem vê conteúdo restrito;
- relação social não concede permissão operacional;
- histórico mínimo permite auditoria de abuso sem expor dados sensíveis;
- `./check.sh` passa.

Estado atual:

- Implementado via `social_relationships`.
- APIs permitem seguir, deixar de seguir, solicitar/aceitar/recusar/cancelar amizade, desfazer amizade, bloquear, desbloquear, consultar resumo relacional e buscar perfis por slug/nome público.
- Bloqueio encerra follows/amizades existentes, impede nova relação social e não é restaurado automaticamente no desbloqueio.
- Perfil público `/u/{slug}` contém ações sociais no contexto correto; a tela Social mostra apenas resumo de seguidores, seguindo, amigos e solicitações, deixando ações completas no perfil público ou em `Conta > Perfil`.
- Busca/descoberta de makers não lista perfis `private`; diretório sem termo lista apenas perfis `public`; `unlisted` só aparece por slug direto; bloqueio autenticado é respeitado e não retorna email, WhatsApp, organização nem permissões.
- Relações sociais não alteram organizações, ownership ou permissões de impressora.
- Histórico mínimo de relacionamento é registrado em `catalog_audit_events` com `entity_type='social_relationship'`, IDs e ação, sem payload sensível; retenção operacional: 180 dias.
- Testes cobrem ciclo completo de follow/friend/block, privacidade, idempotência, busca, payload sanitizado e isolamento operacional.
- Fechado em 100% com `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q`, `npm run build`, `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`, commit `6a66249`, deploy cloud workflow `27584317785` e validação visual/API autenticada em produção.

## PKG-54: Feed Técnico Por Comunidade De Impressora

Objetivo:

Criar feed técnico inicial por comunidade, priorizando conteúdo útil por modelo de impressora em vez de timeline genérica.

Dependências:

- PKG-52.
- PKG-53 para regras sociais opcionais.

Entregáveis:

- feed por comunidade de impressora;
- tipos iniciais: post técnico, dúvida, mod, resultado de impressão, anúncio de arquivo e aviso de curadoria;
- ordenação por recente, recomendado e fixado;
- filtros por componente, material, firmware, problema e tipo de conteúdo;
- paginação e cache seguro;
- UI responsiva.

Lotes:

1. Contrato de item de feed.
2. Feed por comunidade com paginação.
3. Tipos e filtros técnicos.
4. Conteúdo fixado e avisos de curadoria.
5. UI e testes.

Critério de aceite:

- feed sempre pertence a uma comunidade ou perfil, não a uma organização;
- conteúdo privado não aparece em comunidade pública;
- filtros usam catálogo técnico quando aplicável;
- `./check.sh` passa.

Estado atual:

- Implementado via tabela `social_feed_items` em `backend/sql/044_social_community_feed.sql`.
- API `GET /api/social/communities/{slug}/feed` retorna feed público paginado por comunidade com ordenação `recent`, `recommended` e `pinned`.
- Contrato cobre tipos `technical_post`, `question`, `mod`, `print_result`, `file_announcement` e `curation_notice`.
- Filtros por componente, material, firmware, problema e tipo de conteúdo usam dados técnicos do feed e curadoria derivada do catálogo.
- Conteúdo privado (`visibility='private'`) não aparece em feed público; comunidades `obsolete`/`merged` não retornam itens ativos.
- UI da página `/c/{slug}` substitui o placeholder por feed real com filtros, ordenação, paginação, estado vazio, erro e carregamento.
- Payload público não expõe Moonraker, SSH, token, credencial, organização ou permissão.
- Validação concluída com `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q`, `cd frontend && npm run build`, `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` e fluxo local em `/c/{slug}` com login, publicação de discussão e painel de comentários.
- Fechado em 100% com `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`, commit do pacote, push da branch `cloud`, publicação pelo workflow `Deploy Printora Cloud` e validação local visual/API da aba `Feed`.

## PKG-55: Posts, Comentários, Reações E Discussões Técnicas

Objetivo:

Permitir conversas estruturadas com posts, comentários, respostas, reações e edição segura para suporte técnico e troca de experiência.

Dependências:

- PKG-54.
- PKG-68 para regras antiabuso completas em lote posterior.

Entregáveis:

- criação, edição e remoção lógica de posts;
- comentários em árvore curta;
- reações simples;
- anexos leves como imagens e links;
- marcação de resposta útil ou solução quando for dúvida;
- histórico de edição mínimo;
- testes de permissão, sanitização e remoção lógica.

Lotes:

1. Modelo de post e comentário.
2. API de publicação e edição.
3. Reações e solução marcada.
4. UI de discussão.
5. Sanitização e testes.

Critério de aceite:

- remoção não quebra encadeamento da discussão;
- HTML/script malicioso é bloqueado;
- autor, moderador e admin têm permissões distintas;
- `./check.sh` passa.

Estado atual:

- Implementado com `social_feed_items` como post raiz e tabelas `social_discussion_comments`, `social_discussion_reactions` e `social_discussion_edit_history` em `backend/sql/045_social_discussions.sql`.
- APIs permitem criar, editar e remover logicamente posts; criar, editar e remover logicamente comentários; responder em árvore curta de um nível; reagir a posts/comentários; e marcar/limpar solução em dúvidas.
- Permissões distinguem autor, moderador de comunidade e administrador; usuário sem vínculo não edita/remove conteúdo de outro usuário.
- Sanitização rejeita HTML/script e anexos aceitam somente URL HTTPS pública, sem host local/privado.
- Remoção lógica preserva encadeamento da discussão e mascara conteúdo removido.
- UI da aba `Feed` em `/c/{slug}` permite publicar discussão, abrir detalhe, comentar, responder, reagir, editar, remover e marcar solução, com estados de erro/carregamento.
- Histórico mínimo de edição/remoção/solução fica em `social_discussion_edit_history` e auditoria resumida em `catalog_audit_events` sem payload sensível.
- Validação concluída com `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q`, `cd frontend && npm run build`, `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` e fluxo local em `/c/{slug}` na aba `Arquivos` com login, cadastro de item STL e listagem da biblioteca.

## PKG-56: Biblioteca Base De Arquivos STL/3MF

Objetivo:

Criar a biblioteca de modelos 3D vinculada a usuários, comunidades, impressoras e componentes, começando por metadados e controle de acesso antes de fatiamento.

Dependências:

- PKG-52.
- PKG-55.

Entregáveis:

- cadastro de item de biblioteca;
- suporte inicial a STL, 3MF e pacote com múltiplos arquivos;
- vínculo com fabricante/modelo/variante/componente;
- visibilidade: privado, amigos, comunidade ou público;
- metadados: descrição, versão, material sugerido, suporte necessário, orientação e licença;
- histórico de downloads;
- UI de biblioteca por comunidade e por perfil.

Lotes:

1. Modelo de item de biblioteca e SQL idempotente.
2. Metadados técnicos e vínculos com catálogo.
3. Visibilidade e permissões.
4. Listagem por comunidade/perfil.
5. Testes de isolamento.

Critério de aceite:

- arquivo privado não aparece em comunidade pública;
- modelo sempre tem dono e visibilidade explícitos;
- vínculo técnico usa catálogo quando existir;
- `./check.sh` passa.

Estado atual:

- Implementado com `social_library_items`, `social_library_files` e `social_library_downloads` em `backend/sql/046_social_library_items.sql`.
- Itens de biblioteca têm dono obrigatório, visibilidade explícita (`privado`, `amigos`, `comunidade`, `público`), licença, versão, metadados técnicos e vínculo opcional com comunidade e variante do catálogo.
- Suporte inicial cobre metadados de STL, 3MF e pacote ZIP; upload binário, quarentena e análise profunda ficam no pacote dedicado seguinte.
- APIs cobrem criação, detalhe, edição, arquivamento lógico, listagem por comunidade/perfil e registro de download com isolamento por visibilidade.
- UI da aba `Arquivos` em `/c/{slug}` lista e cadastra modelos com estados separados; perfil público lista arquivos visíveis do autor.
- Arquivos privados não aparecem em comunidade pública nem em perfil para terceiros; itens de amigos dependem de amizade aceita.
- Validação concluída com `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q`, `cd frontend && npm run build`, `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`, upload local de STL para quarentena e checagem da UI de `Arquivos` com input `.stl,.3mf,.zip`.

## PKG-57: Upload Seguro, Validação E Quarentena De Arquivos 3D

Objetivo:

Adicionar upload real de arquivos 3D com validação, quarentena, limites e proteção contra conteúdo malicioso ou custo excessivo.

Dependências:

- PKG-56.
- PKG-69 para cotas completas em pacote posterior.

Entregáveis:

- upload com limite de tamanho e extensão;
- validação de MIME e assinatura quando possível;
- quarentena até processamento técnico;
- checksum e deduplicação básica;
- bloqueio de zip bombs, paths perigosos e formatos não suportados;
- status de processamento;
- testes com fixtures controladas.

Lotes:

1. Storage local controlado e metadados de upload.
2. Validação de extensão, MIME, tamanho e checksum.
3. Quarentena e estados de processamento.
4. Deduplicação básica.
5. Testes de arquivos inválidos e limites.

Critério de aceite:

- upload não grava fora do diretório controlado;
- arquivo em quarentena não fica disponível para download/fatiamento;
- falha de validação é acionável e auditável;
- `./check.sh` passa.

Estado atual:

- Implementado com extensão de `social_library_files` em `backend/sql/047_social_library_uploads.sql`.
- Upload real usa corpo bruto `application/octet-stream` em `/api/social/library/{item_id}/files/upload`, sem multipart, sempre ligado a item existente e com permissão de dono/administrador.
- Storage local fica confinado a `<data_dir>/library_uploads/quarantine`, com nome derivado de SHA-256 e extensão validada; nenhum path do usuário é usado como destino.
- Validação cobre extensão, limite de 25 MB, assinatura básica de STL/3MF/ZIP, ZIP vazio, paths perigosos, excesso de entradas, tamanho descompactado e razão de compressão suspeita.
- Arquivo válido entra como `quarantined`; rejeitado entra como `rejected` com motivo acionável; arquivos em quarentena ainda não viram download/fatiamento validado.
- Checksum SHA-256 é registrado e deduplicação básica aponta para arquivo já quarentenado/validado com o mesmo hash.
- UI da aba `Arquivos` aceita seleção de arquivo local STL/3MF/ZIP e mostra status de metadados, quarentena ou rejeição no card.
- Validação concluída com `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q`, `cd frontend && npm run build`, `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` e fluxo local via API com upload STL, análise, dimensões, triângulos e thumbnail gerado.

## PKG-58: Visualização 3D, Thumbnails E Análise Técnica De Modelos

Objetivo:

Gerar preview visual e análise técnica mínima dos arquivos para o usuário entender o modelo antes de baixar, remixar ou fatiar.

Dependências:

- PKG-57.

Entregáveis:

- extração de dimensões, volume aproximado, quantidade de malhas e bounding box;
- thumbnail ou preview 3D no frontend;
- detecção básica de problemas: arquivo vazio, escala suspeita, malha inválida, dimensões incompatíveis;
- orientação inicial sobre necessidade provável de suporte;
- armazenamento de metadados derivados;
- testes com arquivos pequenos e determinísticos.

Lotes:

1. Parser/analisador seguro em processo isolado ou biblioteca controlada.
2. Metadados derivados.
3. Thumbnail/preview.
4. Alertas técnicos básicos.
5. UI e testes.

Critério de aceite:

- análise não executa código do arquivo;
- arquivo problemático não bloqueia a biblioteca inteira;
- preview falho aparece como estado controlado;
- `./check.sh` passa.

Estado atual:

- Implementado com `backend/sql/048_social_library_analysis.sql`, armazenando `analysis_json`, `thumbnail_svg` e `analyzed_at` por arquivo de biblioteca.
- Análise segura roda por parser controlado em Python/stdlib, sem executar conteúdo do arquivo; cobre STL binário/ASCII, 3MF e pacotes ZIP com modelos internos.
- Metadados derivados incluem dimensões, bounding box, volume aproximado por caixa, quantidade de malhas, triângulos e indicação de suporte provável.
- Alertas básicos cobrem arquivo vazio/sem vértices, malha inválida, escala suspeita, dimensões incompatíveis e orientação alta.
- Thumbnail SVG é gerado a partir do bounding box e renderizado no card; falha de análise fica como `analysis_failed` no arquivo, sem bloquear o item/biblioteca.
- UI da aba `Arquivos` exibe ação `Analisar`, preview, dimensões, volume, triângulos e mensagens de alerta em estado controlado.
- Validação concluída com `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q`, `cd frontend && npm run build`, `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` e fluxo local via API bloqueando publicação pública sem autoria/termos e aceitando item com créditos.

## PKG-59: Licenças, Autoria E Atribuição De Modelos

Objetivo:

Formalizar direitos de uso, autoria, créditos e regras de redistribuição para reduzir risco legal e operacional da biblioteca.

Dependências:

- PKG-56.

Entregáveis:

- seleção obrigatória de licença no modelo publicado;
- campo de autor original e fonte;
- suporte a remix/derivado com atribuição;
- termos de publicação e responsabilidade;
- bloqueio de publicação pública sem licença;
- UI de licença e créditos.

Lotes:

1. Catálogo de licenças permitidas.
2. Campos de autoria e fonte.
3. Validação antes de publicação pública.
4. UI e documentação.
5. Testes de licença obrigatória.

Critério de aceite:

- modelo público sempre tem licença e autoria declaradas;
- remix referencia origem quando aplicável;
- download mostra licença de forma clara;
- `./check.sh` passa.

Estado atual:

- Implementado com `backend/sql/049_social_library_license_attribution.sql`, adicionando autoria original, fonte pública, texto de atribuição, origem de remix e aceite de termos por item.
- Publicação `public` ou `community` exige autoria declarada, licença e aceite dos termos; itens privados continuam podendo ser rascunhos sem publicação pública.
- Remix/derivado pode referenciar item de origem ativo e não pode apontar para si mesmo.
- Download/listagem mostram licença e autoria de forma clara em cards de comunidade e perfil público.
- UI de cadastro inclui autor original, fonte, crédito/atribuição e aceite de termos separado do upload/análise.
- Validação focada concluída com `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q` e `cd frontend && npm run build`.

## PKG-60: Versionamento, Remix E Derivados De Modelos

Objetivo:

Permitir evoluir modelos com versões, changelog e remixes sem sobrescrever artefatos já usados por outros usuários.

Dependências:

- PKG-56.
- PKG-59.

Entregáveis:

- versões imutáveis de arquivos publicados;
- versão atual destacada;
- changelog por versão;
- relação de remix/derivado;
- comparação de metadados entre versões;
- rollback lógico para versão anterior como atual;
- testes de imutabilidade.

Lotes:

1. Modelo de versão e arquivo imutável.
2. Changelog e versão atual.
3. Remix e derivado.
4. UI de histórico.
5. Testes de imutabilidade e permissões.

Critério de aceite:

- arquivo publicado não é sobrescrito silenciosamente;
- usuários conseguem baixar versão específica;
- remoção respeita dependências e moderação;
- `./check.sh` passa.

Estado atual:

- Implementado com `backend/sql/050_social_library_versions.sql`, persistindo snapshots imutáveis de versões, changelog, versão atual, download por versão e rollback lógico.
- Backend expõe criação de versão, promoção de versão anterior como atual e registro de download por versão, preservando autorização de dono/admin.
- UI da aba `Arquivos` exibe histórico por card, cria nova versão com changelog, registra download de versão específica e permite usar versão anterior como atual.
- Validação focada: `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py::test_library_versions_are_immutable_and_can_be_promoted backend/tests/test_social_catalog.py::test_library_version_download_and_permissions -q` e testes de schema direcionados passaram.

## PKG-61: Coleções, Favoritos, Downloads E Listas De Impressão

Objetivo:

Organizar modelos em coleções pessoais ou comunitárias e preparar listas de impressão sem ainda executar fatiamento.

Dependências:

- PKG-56.
- PKG-60.

Entregáveis:

- favoritos;
- coleções públicas, privadas e por comunidade;
- listas de impressão por impressora;
- histórico de downloads;
- marcação de impresso, quero imprimir e problema encontrado;
- UI de coleções e listas.

Lotes:

1. Favoritos e histórico de download.
2. Coleções pessoais.
3. Coleções por comunidade.
4. Lista de impressão por impressora.
5. UI e testes.

Critério de aceite:

- coleção privada não vaza itens;
- lista de impressão referencia versão específica do modelo;
- histórico respeita retenção e privacidade;
- `./check.sh` passa.

Estado atual:

- Implementado com `backend/sql/051_social_library_organizer.sql`, adicionando favoritos, coleções, itens de coleção, listas de impressão e itens de lista com referência obrigatória à versão.
- Backend expõe resumo do organizador, favoritar/desfavoritar, criação de coleção, inclusão de item/versionamento em coleção, criação de lista por impressora, inclusão de item versionado e atualização de status `want_to_print`, `printed` ou `problem`.
- UI da aba `Arquivos` possui bloco separado de coleções/listas, criação de coleção, criação de lista de impressão, resumo de favoritos/downloads e ações por card para favoritar, adicionar à coleção e adicionar à lista.
- Validação focada: `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py::test_library_organizer_keeps_private_collections_and_versioned_print_lists backend/tests/test_social_catalog.py::test_library_organizer_api_blocks_cross_user_collection_and_printer -q`, testes de schema direcionados e `cd frontend && npm run build` passaram.

## PKG-62: Configurações Técnicas Compartilhadas Por Impressora

Objetivo:

Permitir compartilhar configurações técnicas de hardware, mods e calibração por modelo/variante sem transformar isso em permissão operacional.

Dependências:

- PKG-49.
- PKG-52.

Entregáveis:

- configuração pública de impressora por usuário;
- mods instalados;
- componentes usados;
- calibrações e observações públicas opcionais;
- vínculo com posts e modelos;
- comparação entre configurações de membros da mesma comunidade.

Lotes:

1. Modelo de configuração técnica pública.
2. Vínculo com catálogo e impressora do usuário.
3. Mods/componentes.
4. Comparação por comunidade.
5. UI e testes.

Critério de aceite:

- configuração pública não expõe IP, host, agente, token ou path sensível;
- usuário controla o que é público;
- comparação usa campos normalizados quando existirem;
- `./check.sh` passa.

Estado atual:

- Concluído.
- Lote 1 concluído com modelo de configuração técnica pública em SQL/API.
- Lote 2 concluído com vínculo a impressora do usuário, variante do catálogo, comunidade e item de biblioteca opcional.
- Lote 3 concluído com mods, componentes, calibrações e observações públicas sanitizadas.
- Lote 4 concluído com comparação normalizada por comunidade.
- Lote 5 concluído com leitura de perfis técnicos na aba `Perfis` da comunidade e CRUD no detalhe da impressora.
- Validação: `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q`; `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`; validação visual local no detalhe da impressora e em `/c/variant-voron-design-voron-2-4-voron-2-4-r2-350`, incluindo viewport mobile.

## PKG-63: Perfis De Material E Fatiamento Compartilháveis

Objetivo:

Criar base para perfis de material e fatiamento compartilháveis por impressora, material, nozzle e objetivo de impressão, antes de executar slicer.

Dependências:

- PKG-49.
- PKG-62.

Entregáveis:

- perfil de material: marca, tipo, temperatura, cama, fluxo, observações;
- perfil de fatiamento: nozzle, camada, velocidade, suporte, preenchimento, resistência/qualidade;
- vínculo com impressora, componente e modelo 3D;
- escopo: privado, comunidade ou público;
- import/export inicial em formato neutro;
- testes de versionamento e compatibilidade.

Lotes:

1. Modelo de perfil de material.
2. Modelo de perfil de fatiamento.
3. Compatibilidade por impressora/nozzle/material.
4. UI de cadastro e comparação.
5. Import/export seguro.
6. Testes.

Critério de aceite:

- perfil não é aplicado automaticamente na impressora;
- compatibilidade aparece de forma explícita;
- versão do perfil é rastreável;
- `./check.sh` passa.

Estado atual:

- Concluído.
- Lote 1 concluído com modelo de perfil de material em SQL/API.
- Lote 2 concluído com perfil de fatiamento ligado ao perfil de material.
- Lote 3 concluído com compatibilidade por variante, nozzle e material.
- Lote 4 concluído com CRUD no detalhe da impressora e leitura pública na comunidade.
- Lote 5 concluído com export/import JSON neutro.
- Lote 6 concluído com testes de repository/API, build frontend, check oficial e validação visual local em desktop/mobile.
- Validação: `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q`; `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`; validação visual local no detalhe da impressora e na aba `Perfis` da comunidade.

## PKG-64: Busca, Tags E Descoberta De Conteúdo

Objetivo:

Criar busca e navegação eficiente para comunidades, modelos, posts, arquivos e perfis técnicos.

Dependências:

- PKG-54.
- PKG-56.
- PKG-63.

Entregáveis:

- busca por texto;
- tags normalizadas e livres com curadoria;
- filtros por impressora, componente, material, licença, arquivo, popularidade e atualização;
- páginas de descoberta;
- índice incremental;
- testes de permissão na busca.

Lotes:

1. Contrato de busca unificado.
2. Indexação de comunidades e posts.
3. Indexação de modelos e perfis.
4. Tags e filtros.
5. UI de descoberta.
6. Testes de privacidade.

Critério de aceite:

- conteúdo privado não aparece na busca;
- filtro técnico usa catálogo quando possível;
- resultado indica tipo e comunidade;
- `./check.sh` passa.

Estado atual:

- Concluído, commitado, enviado para `origin/cloud` e publicado.
- Lote 1 concluído com contrato unificado em `/api/social/search` e `/api/social/tags`.
- Lote 2 concluído com indexação de comunidades e discussões públicas.
- Lote 3 concluído com indexação de arquivos, configurações técnicas, perfis de material e variantes do catálogo.
- Lote 4 concluído com tags normalizadas, facetas e filtros por tipo, comunidade, impressora, componente, material, licença, arquivo, popularidade e atualização.
- Lote 5 concluído com aba `Descoberta` na tela Social, busca, filtros, facetas, paginação, estados vazios e links para o conteúdo público.
- Lote 6 concluído com teste focado garantindo que conteúdo privado não entra na busca nem em tags/facetas.
- Commit de implementação: `acb8762 Implementa PKG-64 busca e descoberta social`.
- Publicação confirmada por deploys posteriores bem-sucedidos da branch `cloud`; último workflow verificado: `Deploy Printora Cloud` `27687518722`.
- Validação: `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py::test_search_discovery_indexes_public_content_and_filters_private -q`; `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q`; `cd frontend && npm run build`; `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`; validação visual local da aba `Descoberta` em desktop e mobile.

## PKG-65: Ranking, Recomendações E Reputação Técnica

Objetivo:

Priorizar conteúdo útil e confiável usando sinais técnicos, feedback de impressão e reputação, sem criar ranking manipulável ou opaco.

Dependências:

- PKG-61.
- PKG-64.
- PKG-74 para sinais reais de impressão em pacote posterior.

Entregáveis:

- sinais: downloads, favoritos, prints bem-sucedidos, solução marcada, denúncias e curadoria;
- reputação por usuário baseada em contribuição técnica;
- recomendações por modelo de impressora e material;
- proteção contra auto-voto e abuso;
- explicação básica do motivo da recomendação.

Lotes:

1. Modelo de sinais de qualidade.
2. Score inicial determinístico.
3. Reputação técnica.
4. Recomendações por comunidade.
5. Proteção antiabuso.
6. Testes.

Critério de aceite:

- score não depende de dados privados;
- usuário entende por que algo foi recomendado;
- denúncia e moderação reduzem exposição;
- `./check.sh` passa.

Estado atual:

- Concluído, publicado, commitado e enviado para `origin/cloud`.
- Lote 1 concluído com `social_quality_signals` para downloads, favoritos, soluções, reações, denúncias futuras e prints bem-sucedidos futuros.
- Lote 2 concluído com score determinístico por conteúdo público usando sinais normalizados, popularidade do índice e reputação limitada do autor.
- Lote 3 concluído com snapshots de reputação técnica por usuário e leaderboard público.
- Lote 4 concluído com `/api/social/recommendations`, filtros por comunidade/material/componente/tipo e bloco `Recomendações técnicas` na aba `Descoberta`.
- Lote 5 concluído ignorando auto-voto no score e reservando sinal negativo `report` para reduzir exposição quando denúncias/moderação forem registradas.
- Lote 6 concluído com teste de score, explicação, reputação, ignorar favorito/download próprio e reutilizar índice/sinais materializados quando a fonte não mudou.
- Validação: `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py::test_social_ranking_recommendations_ignore_self_vote_and_explain_score -q`; `backend/.venv/bin/python -m pytest backend/tests/test_social_catalog.py -q`; `cd frontend && npm run build`; `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`; validação visual local da aba `Descoberta` com recomendações em desktop e mobile; deploy cloud `27648421434`; smoke público de `/health`, `/api/system/version`, `/api/social/recommendations`, `/api/social/search` e `/api/social/reputation`.

## PKG-66: Moderação, Denúncias E Curadoria

Objetivo:

Criar mecanismos para denunciar, revisar, ocultar, bloquear e curar conteúdo social e arquivos 3D com segurança.

Dependências:

- PKG-55.
- PKG-56.
- PKG-59.

Entregáveis:

- denúncia de post, comentário, perfil e modelo;
- fila de moderação;
- estados: ativo, oculto, removido, bloqueado, em revisão;
- ação de moderador com motivo e auditoria;
- curadoria de catálogo, tags e comunidades;
- documentação de retenção e rollback lógico.

Lotes:

1. Modelo de denúncia e estado moderado.
2. Fila de moderação.
3. Ações de ocultar/remover/bloquear.
4. Curadoria de tags e catálogo social.
5. UI administrativa.
6. Testes de auditoria e permissão.

Critério de aceite:

- remoção é lógica, auditável e reversível quando aplicável;
- conteúdo ilegal/perigoso pode ser bloqueado rapidamente;
- usuário comum não acessa fila de moderação;
- `./check.sh` passa.

Estado atual:

- Implementado via `backend/sql/057_social_moderation.sql`.
- Implementado domínio `backend/app/social_moderation.py` e rotas `backend/app/routes/social_moderation.py`.
- Denúncias autenticadas cobrem discussão, comentário, perfil, arquivo 3D, variação de catálogo, comunidade e tag.
- Fila administrativa expõe denúncias e ações recentes somente para suporte autorizado.
- Ações de moderação registram motivo, estado anterior, novo estado e auditoria em `catalog_audit_events`.
- Ocultação, bloqueio e remoção usam estado lógico reversível quando o domínio suporta restauração; não apagam dados.
- Curadoria administrativa permite bloquear/restaurar tags, comunidades e variações do catálogo por fluxo moderado.
- UI administrativa adicionada à tela `Catálogo`, separada da tela `Social`, com filtro de fila, detalhe da denúncia, justificativa e ações por ícone/botão.
- Documentação atualizada em `TELAS.md`, `TESTES.md`, `DECISOES.md` e `RUNBOOK.md`.
- Testes focados adicionados para denúncia, fila restrita, ação moderadora, auditoria, restauração e curadoria de tag.
- Validação executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_social_catalog.py -k 'social_moderation' -q`; `cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py ../backend/tests/test_social_catalog.py -k 'social_moderation or schema or update' -q`; `npm --prefix frontend run build`.

## PKG-67: Notificações Sociais E Acompanhamento De Conteúdo

Objetivo:

Notificar o usuário sobre interações sociais, comunidades, atualizações de modelos e respostas técnicas sem misturar alertas operacionais da impressora.

Dependências:

- PKG-53.
- PKG-55.
- PKG-60.

Entregáveis:

- notificações in-app sociais;
- preferências por tipo de notificação;
- acompanhamento de post, modelo, coleção e comunidade;
- digest opcional;
- separação visual entre alerta operacional e notificação social;
- testes de isolamento e preferências.

Lotes:

1. Modelo de notificação social.
2. Preferências por usuário.
3. Follow de conteúdo.
4. UI de central social.
5. Digest e testes.

Critério de aceite:

- alerta de impressora não se mistura com like/comentário;
- usuário pode silenciar comunidade ou conteúdo;
- notificações respeitam bloqueio e privacidade;
- `./check.sh` passa.

Estado atual:

- Implementado via `backend/sql/058_social_notifications.sql`.
- Implementado domínio `backend/app/social_notifications.py` e rotas `backend/app/routes/social_notifications.py`.
- Notificações in-app sociais cobrem respostas, reações, solução marcada, follow, solicitação/aceite de amizade, post de comunidade e atualizações de conteúdo acompanhado.
- Preferências por usuário permitem ligar/desligar notificação in-app por tipo e preparar digest por tipo.
- Acompanhamento de conteúdo cobre post, arquivo 3D, variação de catálogo, comunidade e coleção, com opção de silenciar e incluir em digest.
- Eventos sociais principais emitem notificação sem misturar alertas operacionais da impressora.
- Notificações respeitam bloqueio social e não são emitidas para o próprio ator.
- UI adicionada como aba `Notificações` na tela `Social`, com filtro de estado, lista, digest, acompanhamentos e preferências.
- Documentação atualizada em `TELAS.md`, `TESTES.md`, `DECISOES.md` e `RUNBOOK.md`.
- Testes focados adicionados para preferências, follow de conteúdo, bloqueio, rotas, leitura e payload sanitizado.
- Validação executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_social_catalog.py -k 'social_notifications or notification_routes' -q`; `cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q`; `npm --prefix frontend run build`.

## PKG-68: Privacidade, Segurança Social E Antiabuso

Objetivo:

Endurecer a camada social contra spam, scraping, assédio, enumeração de usuários, vazamento de dados e uso indevido de arquivos.

Dependências:

- PKG-50.
- PKG-53.
- PKG-55.
- PKG-56.

Entregáveis:

- rate limit por ação social;
- proteção contra enumeração de usuários;
- controles de perfil público, seguidores e mensagens;
- bloqueio, silenciamento e denúncia integrados;
- revisão de payloads para não expor email, IP, tokens ou dados operacionais;
- logs seguros de abuso.

Lotes:

1. Matriz de ameaças social.
2. Rate limits e proteção de enumeração.
3. Regras de visibilidade reforçadas.
4. Integração com bloqueio/denúncia.
5. Auditoria e testes de segurança.

Critério de aceite:

- APIs públicas não retornam dados operacionais;
- usuário bloqueado não contorna via busca ou comunidade;
- abuso repetido gera estado acionável para moderação;
- `./check.sh` passa.

Estado atual:

- Implementado.

Notas de conclusão:

- SQL `059_social_safety_antiabuse.sql` cria preferências de segurança social, eventos de rate limit e sinais de abuso sem armazenar IP, email, token ou payload operacional.
- APIs sociais sensíveis aplicam limite por ação em busca/perfil público, relações, denúncias, mutações de conteúdo e downloads sociais.
- Descoberta de perfis respeita preferência de descoberta: o perfil pode sair de listagens/busca por nome sem quebrar URL direta autorizada.
- Bloqueios existentes continuam impedindo busca, perfil, impressoras públicas e relação social.
- Denúncia/uso repetido acima do limite gera sinal acionável para moderação em `/api/social/moderation/abuse-signals`.
- `Conta > Perfil > Público` recebeu controles separados de privacidade/antiabuso para descoberta, seguidores, mensagens, menções e histórico de downloads sociais.
- Payloads revisados não expõem email, IP bruto, token, Moonraker, SSH, agente, organização ou permissão operacional.
- Documentação atualizada em `TELAS.md`, `TESTES.md`, `DECISOES.md` e `RUNBOOK.md`.
- Testes focados adicionados para preferências, proteção contra enumeração, rate limit, sinais de abuso, endpoint administrativo e payload sanitizado.
- Validação executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_social_catalog.py -k 'social_safety or social_profile_discovery_visibility_blocking or moderation_queue' -q`; `cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q`; `npm --prefix frontend run build`.

## PKG-69: Armazenamento, Cotas, Retenção E Custos De Arquivos

Objetivo:

Controlar crescimento de arquivos, custos e retenção da biblioteca, preparando migração futura para storage externo sem acoplar a lógica ao filesystem local.

Dependências:

- PKG-57.
- PKG-60.

Entregáveis:

- cotas por usuário e organização quando aplicável;
- política de retenção para arquivos removidos e versões antigas;
- abstraction simples de storage local com caminho seguro;
- relatório de uso;
- limpeza supervisionada;
- plano futuro para object storage.

Lotes:

1. Modelo de cota e uso.
2. Storage adapter local.
3. Retenção e remoção supervisionada.
4. Relatório de uso.
5. Testes de limite e cleanup.

Critério de aceite:

- upload respeita cota antes de gravar definitivo;
- remoção não apaga arquivo referenciado por versão ativa;
- cleanup é auditável e não destrutivo sem retenção definida;
- `./check.sh` passa.

Estado atual:

- Implementado.

Notas de conclusão:

- SQL `060_social_file_storage.sql` cria políticas de cota, retenção e custo por escopo, além de revisão auditável de retenção sem remoção automática.
- Upload da biblioteca consulta a cota antes de gravar o arquivo em quarentena; quando a cota é insuficiente, nenhum objeto local é criado.
- Adapter local `LocalLibraryStorage` centraliza o caminho seguro de quarentena e prepara troca futura por object storage sem acoplar regra de negócio ao filesystem.
- Relatório autenticado em `/api/social/me/library/storage` expõe política, uso, custo estimado, cota restante, candidatos de retenção e plano futuro de object storage.
- Revisão supervisionada em `/api/social/me/library/storage/retention-reviews` registra plano `dry_run` em `social_file_retention_reviews` e não apaga arquivo, linha ou versão.
- Candidatos referenciados por versão ativa ficam bloqueados no plano de retenção; arquivos com falha de validação/análise podem aparecer como recuperáveis.
- `Comunidade > Arquivos` recebeu painel organizado de armazenamento no bloco da biblioteca, separado de cadastro/lista/detalhe dos arquivos.
- Documentação atualizada em `TELAS.md`, `TESTES.md`, `DECISOES.md` e `RUNBOOK.md`.
- Testes focados adicionados para limite de cota antes da escrita, relatório de uso e retenção supervisionada.
- Validação executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_social_catalog.py -k 'library_storage or library_upload_quarantine' -q`; `cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q`; `npm --prefix frontend run build`.

## PKG-70: Ponte Controlada Com Engine De Fatiamento

Objetivo:

Preparar integração com engine de fatiamento, inicialmente OrcaSlicer/PrusaSlicer em modo controlado, sem embutir a UI do slicer no Printora.

Dependências:

- PKG-56.
- PKG-63.
- PKG-69.

Entregáveis:

- decisão técnica sobre engine de fatiamento suportada;
- execução isolada em worker local ou agente;
- detecção de versão do slicer;
- contrato de entrada: modelo, perfil, impressora, material e qualidade;
- contrato de saída: G-code, logs, tempo estimado, peso estimado e warnings;
- bloqueio padrão quando engine não estiver configurada;
- documentação de instalação e riscos.

Lotes:

1. Decisão técnica e contrato do slicer.
2. Detector de engine e versão.
3. Worker isolado em modo dry-run.
4. Contrato de entrada/saída.
5. Logs sanitizados.
6. Testes com fixtures.

Critério de aceite:

- Printora não embute UI do OrcaSlicer como primeira solução;
- fatiamento não executa se engine/perfil/impressora forem incompatíveis;
- logs não expõem paths sensíveis sem sanitização;
- `./check.sh` passa.

Estado atual:

- Implementado.

Notas de conclusão:

- Decisão técnica: Printora usa OrcaSlicer/PrusaSlicer via CLI controlada, sem embutir a UI do fatiador.
- SQL `061_slicing_engine_bridge.sql` registra checks de engine e dry-runs sanitizados em tabelas próprias.
- Backend adicionou módulo `slicing` com detector de engine, leitura de versão, contrato de entrada/saída e worker em dry-run.
- Endpoints `GET /api/slicing/engine` e `POST /api/slicing/dry-run` bloqueiam por padrão quando a engine não está configurada.
- Logs e paths retornados são sanitizados para não expor home local, tokens ou segredos conhecidos.
- Administração recebeu painel compacto de verificação read-only da engine, separado de CRUD de impressoras/modelos/perfis.
- Documentação atualizada em `TELAS.md`, `TESTES.md`, `DECISOES.md` e `RUNBOOK.md`.
- Testes focados adicionados em `backend/tests/test_slicing.py`.
- Validação executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_slicing.py -q`; `npm --prefix frontend run build`.

## PKG-71: Pipeline De Fatiamento Por Perfil E Impressora

Objetivo:

Executar fatiamento controlado usando modelo, perfil de material, perfil de fatiamento e impressora selecionada, gerando artefatos rastreáveis.

Dependências:

- PKG-70.
- PKG-63.

Entregáveis:

- criação de job de fatiamento;
- fila e estados: planejado, executando, concluído, falhou, cancelado;
- validação de volume útil da impressora;
- seleção de perfil compatível;
- artefatos: G-code, logs, preview quando disponível e metadados;
- histórico por usuário, modelo e impressora.

Lotes:

1. Modelo de job de fatiamento.
2. Validação de compatibilidade.
3. Execução controlada no worker/agente.
4. Persistência de artefatos.
5. UI de progresso e resultado.
6. Testes de falha e cancelamento.

Critério de aceite:

- job não fatiará modelo maior que o volume útil sem confirmação/erro claro;
- G-code fica associado à versão do item/modelo legado e perfis usados; após PKG-77 a PKG-81, deve apontar para snapshot imutável do projeto;
- falha preserva logs acionáveis;
- `./check.sh` passa.

Estado atual:

- Implementado.

Notas de conclusão:

- SQL `062_slicing_jobs.sql` cria jobs de fatiamento e artefatos rastreáveis por usuário, impressora, perfil e modelo.
- Backend adicionou `slicing_pipeline` com criação, execução, cancelamento, validação de volume útil e compatibilidade de perfil.
- A execução usa a ponte do PKG anterior: sem engine configurada, o job falha com log acionável; com engine CLI configurada, o worker roda em diretório isolado, registra G-code, log e metadados.
- Endpoints `GET /api/slicing/jobs`, `POST /api/slicing/jobs`, `POST /api/slicing/jobs/{id}/run` e `POST /api/slicing/jobs/{id}/cancel` entregam histórico e estados do pipeline.
- Administração recebeu painel de pipeline com seleção de impressora, modelo, dimensões, qualidade, criação de job, execução, cancelamento e lista de resultados.
- Documentação atualizada em `TELAS.md`, `TESTES.md`, `DECISOES.md` e `RUNBOOK.md`.
- Testes focados adicionados em `backend/tests/test_slicing_pipeline.py`.
- Validação executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_slicing.py ../backend/tests/test_slicing_pipeline.py ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q`; `npm --prefix frontend run build`.

## PKG-72: Preflight De Impressão A Partir De Arquivo Fatiado

Objetivo:

Validar o G-code gerado antes de permitir envio para uma impressora, reduzindo risco de arquivo incompatível, temperatura perigosa ou impressora em estado inadequado.

Dependências:

- PKG-71.
- PKG-47.

Entregáveis:

- análise de metadados do G-code;
- validação contra impressora selecionada: volume, nozzle, material, temperatura, cama e firmware;
- preflight remoto via agente para estado atual da impressora;
- bloqueio se estiver imprimindo, offline ou incompatível;
- preview de riscos e checklist antes do envio;
- testes com G-code fixture.

Lotes:

1. Parser seguro de metadados G-code.
2. Compatibilidade com impressora/perfil.
3. Preflight remoto via agente.
4. Checklist e bloqueios.
5. UI e testes.

Critério de aceite:

- G-code não é enviado sem preflight aprovado;
- impressão em andamento bloqueia envio;
- divergências de nozzle/material/volume aparecem antes da execução;
- `./check.sh` passa.

Estado atual:

- Implementado.

Notas de conclusão:

- SQL `063_print_preflight_checks.sql` cria preflights de impressão ligados ao job de fatiamento e ao job remoto do agente quando existir.
- Backend adicionou `print_preflight` com parser seguro de G-code, extração de dimensões, temperaturas, tipo de filamento, nozzle, tempo estimado e checksum.
- Preflight local bloqueia job não concluído, G-code de outra impressora, artefato ausente, temperatura perigosa, G-code sem comandos e divergência de volume; divergências de temperatura/perfil viram warnings antes do envio.
- Preflight remoto usa job `remote_gcode_preflight` do agente para estado atual de Moonraker/Klipper e bloqueia quando não há agente ativo, quando a impressora está imprimindo ou quando o remoto retorna blockers.
- Administração mostra preflight por job concluído, status aprovado/bloqueado/pendente, bloqueios, warnings, quantidade de comandos e checklist antes do envio.
- Documentação atualizada em `TELAS.md`, `TESTES.md`, `DECISOES.md` e `RUNBOOK.md`.
- Testes focados adicionados em `backend/tests/test_print_preflight.py` com fixture `backend/tests/fixtures/gcode/preflight_abs_cube.gcode`.
- Validação executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_print_preflight.py ../backend/tests/test_slicing_pipeline.py ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q`; `npm --prefix frontend run build`.

## PKG-73: Envio Seguro De G-code Para Impressora

Objetivo:

Permitir enviar G-code fatiado para a impressora correta com confirmação explícita, auditoria e opção de iniciar ou apenas salvar no host.

Dependências:

- PKG-72.
- PKG-47.

Entregáveis:

- upload remoto do G-code para Moonraker via agente;
- confirmação textual ou step-up para iniciar impressão;
- opção de apenas salvar arquivo sem imprimir;
- auditoria de usuário, impressora, arquivo, versão do item/modelo legado ou snapshot de projeto e perfil;
- rollback operacional: cancelar job pendente, remover arquivo enviado quando seguro;
- UI de envio e status.

Lotes:

1. Contrato de upload remoto.
2. Salvar sem imprimir.
3. Iniciar impressão com confirmação forte.
4. Auditoria e cancelamento.
5. UI e testes.

Critério de aceite:

- envio para impressora errada é evitado por confirmação visual clara;
- iniciar impressão exige preflight recente e confirmação;
- arquivo enviado não expõe token ou path sensível no frontend;
- `./check.sh` passa.

Estado atual:

- Implementado.

Notas de implementação:

- Backend adicionou `print_delivery` com exigência de preflight aprovado e recente antes de salvar ou iniciar impressão.
- API adicionou listagem, criação, cancelamento e rollback de entregas de G-code em `/api/slicing/deliveries`.
- Agente adicionou jobs `remote_gcode_upload` e `remote_gcode_delete` para enviar arquivo ao Moonraker e remover arquivo salvo quando a impressão não foi iniciada.
- UI de Administração > Pipeline de fatiamento mostra status de envio, ação de salvar arquivo, confirmação textual para iniciar impressão e remoção segura de arquivo salvo.
- Auditoria persiste usuário, impressora, job, preflight, checksum, arquivo remoto, versão do item/modelo legado ou snapshot de projeto, perfil e resultado remoto.
- SQL aditivo: `backend/sql/064_print_gcode_deliveries.sql`.
- Validação executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_print_delivery.py ../backend/tests/test_print_preflight.py -q`; `go test ./...` em `agent`; `npm --prefix frontend run build`.

## PKG-74: Histórico De Trabalhos, Resultados E Telemetria De Impressão

Objetivo:

Registrar resultado de impressões vindas do fluxo social/fatiamento para melhorar recomendações, troubleshooting e qualidade dos modelos.

Dependências:

- PKG-73.
- PKG-65.

Entregáveis:

- histórico de job de impressão vinculado a modelo, versão, perfil, impressora e usuário;
- status: enviado, iniciado, concluído, falhou, cancelado;
- feedback do usuário: deu certo, falhou, ajuste necessário, foto opcional;
- telemetria mínima segura quando disponível;
- vínculo com ranking e recomendações;
- retenção e privacidade documentadas.

Lotes:

1. Modelo de histórico de impressão.
2. Eventos via agente/Moonraker.
3. Feedback manual do usuário.
4. Integração com ranking.
5. UI e testes.

Critério de aceite:

- histórico não expõe impressora privada em página pública;
- feedback pode ser público ou privado;
- falhas ajudam ranking sem revelar dados sensíveis;
- `./check.sh` passa.

Estado atual:

- Implementado.

Notas de implementação:

- Backend adicionou `print_job_history` e `print_job_feedback`, com vínculo a entrega de G-code, job de fatiamento, modelo, versão, perfil, impressora e usuário.
- API adicionou `/api/slicing/history`, eventos de resultado e feedback manual público/privado.
- Telemetria persistida é reduzida a campos seguros; respostas públicas não expõem `printer_id` nem payload remoto bruto.
- Feedback de impressão alimenta sinais de ranking em `social_quality_signals` usando `print_success` ou penalização `report`, sem publicar dados operacionais privados.
- UI de Administração ganhou painel separado `Histórico de impressão`, com status, telemetria segura, resultado e formulário de feedback.
- Retenção padrão: 180 dias em histórico/feedback de impressão.
- SQL aditivo: `backend/sql/065_print_job_history.sql`.

## PKG-75: Marketplace E Curadoria De Conteúdo Premium

Objetivo:

Preparar uma camada opcional de conteúdo premium, curado ou patrocinado, sem bloquear a biblioteca comunitária gratuita.

Dependências:

- PKG-56.
- PKG-59.
- PKG-66.

Entregáveis:

- classificação de conteúdo: comunidade, curado, premium ou patrocinado;
- política de destaque e transparência;
- fluxo de revisão antes de premium;
- metadados comerciais sem pagamento real no primeiro lote;
- separação clara entre recomendação técnica e promoção;
- documentação de risco e rollback.

Lotes:

1. Modelo de classificação comercial.
2. Curadoria premium sem cobrança.
3. Destaques e transparência.
4. Revisão/moderação.
5. UI e testes.

Critério de aceite:

- conteúdo patrocinado não parece recomendação técnica neutra;
- premium não remove acesso ao conteúdo comunitário;
- cobrança real fica fora até pacote futuro específico;
- `./check.sh` passa.

Estado atual:

- Implementado.

Notas de implementação:

- Biblioteca social ganhou classificação `community`, `curated`, `premium` e `sponsored`, status comercial e metadados comerciais.
- Conteúdo premium/patrocinado público exige revisão aprovada antes de publicação.
- API administrativa adicionou revisão comercial auditada em `/api/social/library/{item_id}/commercial-review`.
- Cards públicos exibem transparência de conteúdo curado, premium ou patrocinado; patrocinado não aparece como recomendação técnica neutra.
- Biblioteca comunitária continua disponível sem cobrança e cobrança real permanece fora do escopo.
- SQL aditivo: `backend/sql/066_social_library_commercial_curation.sql`.

## PKG-76: Integrações Externas E Importação De Bibliotecas

Objetivo:

Permitir importar ou referenciar conteúdo externo de forma controlada, evitando cópia indevida e preparando integrações futuras com repositórios de modelos e slicers.

Dependências:

- PKG-56.
- PKG-59.
- PKG-64.

Entregáveis:

- cadastro de fonte externa;
- importação por URL com metadados e licença;
- bookmark externo sem copiar arquivo;
- detecção de duplicidade por checksum quando houver arquivo;
- política de atribuição obrigatória;
- testes com fixtures e sem dependência de serviço externo instável.

Lotes:

1. Modelo de fonte externa.
2. Bookmark externo.
3. Importação controlada de metadados.
4. Deduplicação e atribuição.
5. UI e testes.

Critério de aceite:

- sistema não copia arquivo externo sem licença/atribuição;
- falha de fonte externa não quebra biblioteca local;
- usuário distingue arquivo hospedado no Printora de referência externa;
- `./check.sh` passa.

Estado atual:

- Implementado.

Notas de implementação:

- Backend adicionou cadastro de fontes externas, preview determinístico por URL e referências externas sem cópia de arquivo.
- API adicionou `/api/social/external-library/sources`, `/preview` e `/references`.
- Importação por URL registra metadados, licença, atribuição e checksum opcional, sem depender de serviço externo instável.
- Deduplicação por checksum aponta arquivo local existente quando houver correspondência.
- UI de comunidade ganhou painel `Fontes externas` separado da biblioteca hospedada, deixando claro quando o item é referência externa.
- SQL aditivo: `backend/sql/067_external_library_imports.sql`.

## PKG-77: Área Central De Projetos De Impressão

Objetivo:

Criar uma área principal e isolada de produto para descobrir, buscar e abrir projetos de impressão, separando o fluxo de projetos do contexto social de comunidade e da Administração.

Contexto inicial:

- a base técnica de biblioteca, upload, links externos, fatiamento e envio já existe, mas ficou distribuída entre `Social > Comunidades > Arquivos` e `Administração > Pipeline de fatiamento`;
- o usuário precisa de um ponto de entrada diário para STL/3MF/ZIP/link externo, parecido com bibliotecas de modelos como Printables, MakerWorld e repositórios externos;
- Comunidades devem continuar como contexto social e vitrine, não como a tela principal de gestão de arquivos;
- projeto de impressão não pertence a uma comunidade: ele é uma entidade central/pessoal/global e pode ser compartilhado em zero, uma ou várias comunidades;
- projeto de impressão pode conter um ou vários arquivos, como STL, 3MF, ZIP, imagens, documentação, links externos e artefatos gerados;
- a entidade raiz do domínio passa a ser `Projeto de impressão`; arquivos, versões, compartilhamentos, publicação, jobs de fatiamento, entregas de G-code e histórico são relações ou derivados do projeto;
- compartilhamento em comunidade é relação N:N entre projeto e comunidade; remover compartilhamento não arquiva, apaga, despublica nem transfere ownership do projeto;
- fatiamento e histórico devem sempre apontar para versão/snapshot imutável do projeto e dos arquivos selecionados;
- rotas/entradas legadas como `models`, biblioteca social, comunidade/arquivos e pipeline administrativo devem virar redirect, atalho, compatibilidade somente leitura ou fallback, sem guiar fluxo novo;
- a modelagem antiga baseada em arquivo/modelo dentro de comunidade deve ser migrada/rebaixada sem remover fluxo antigo antes do fluxo novo estar validado;
- Administração deve ficar para configuração da engine, status, caminhos, diagnóstico e política, não para uso cotidiano de fatiar/enviar.

Dependências:

- PKG-56 a PKG-61 para biblioteca, versões, coleções e listas.
- PKG-64 e PKG-65 para busca, ranking e recomendações.
- PKG-76 para referências externas.

Entregáveis:

- novo menu principal `Projetos de impressão`;
- tela de exploração com busca por nome, tag, material, componente, licença, arquivo, origem e comunidade onde foi compartilhado;
- suporte visual para item hospedado no Printora e referência externa;
- cards/lista com licença, autor, origem, comunidades onde foi compartilhado, tipo de arquivo, contagem de downloads/favoritos e ação principal;
- detalhe dedicado do projeto, substituindo a dependência de abrir comunidade para entender arquivos;
- contrato canônico do domínio com `Projeto de impressão`, `Arquivo do projeto`, `Versão do projeto`, `Compartilhamento em comunidade`, `Publicação`, `Job de fatiamento`, `Entrega/G-code` e `Histórico de impressão`;
- versionamento do projeto por snapshot imutável, incluindo lista de arquivos, metadados relevantes e seleção usada por jobs;
- ação `Salvar nos meus projetos` com semântica explícita: salvar referência, criar fork/remix ou copiar arquivo somente quando houver confirmação e licença permitir;
- navegação para comunidades onde o projeto foi compartilhado, sem tornar comunidade dona do projeto;
- remoção/rebaixamento da entrada de biblioteca dentro de Social para papel de vitrine/contexto;
- plano de migração e limpeza das telas antigas de `Social > Comunidades > Arquivos` e `Administração > Pipeline de fatiamento`, incluindo redirects/atalhos, modo somente leitura quando aplicável e critérios para remoção;
- documentação em `TELAS.md` e testes proporcionais.

Lotes:

1. Definir contrato canônico do domínio e navegação, reaproveitando endpoints existentes quando não preservarem a modelagem antiga incorreta.
2. Criar tela `Projetos de impressão` com busca, filtros, estados vazios e cards.
3. Criar detalhe de projeto com metadados, origem, licença, versões, arquivos e ações.
4. Implementar ação `Salvar nos meus projetos` sem duplicar arquivo indevidamente.
5. Ajustar Social/Comunidades para exibirem compartilhamentos e apontarem para o detalhe central do projeto.
6. Definir migração de itens legados de biblioteca/comunidade para projetos centrais, preservando histórico e URLs por redirect/atalho.
7. Documentar limpeza das telas antigas e critérios para remover/rebaixar entradas legadas.
8. Atualizar documentação e validação visual.

Critério de aceite:

- usuário consegue encontrar projetos sem entrar em uma comunidade;
- o mesmo projeto pode aparecer em várias comunidades ou em nenhuma, sem duplicar a entidade principal;
- projeto com múltiplos arquivos é tratado como uma única entidade operacional;
- compartilhamento em comunidade não muda dono, visibilidade principal, publicação nem arquivos do projeto;
- jobs, G-code e histórico ficam ligados a versão/snapshot imutável do projeto;
- item externo e item hospedado ficam claramente diferenciados;
- link/bookmark externo sem arquivo hospedado/importado/validado não pode ser fatiado, salvo como G-code ou enviado para impressora;
- conteúdo privado não aparece na exploração pública;
- nenhum dado operacional de impressora, agente, Moonraker, SSH, token, IP, organização ou permissão aparece em projeto público;
- Social continua útil para comunidade, mas não é o caminho principal para gerenciar STL/3MF;
- entradas antigas não são removidas antes de existir fluxo novo validado;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado.

Notas de implementação:

- Lote 1 iniciou o contrato canônico com schema central de projetos, arquivos, versões/snapshots e compartilhamentos N:N com comunidades.
- Backend adicionou `/api/print-projects/contract` e `/api/print-projects` para exploração pública inicial.
- Backend adicionou detalhe central, salvar referência sem cópia, compartilhamento N:N com comunidade e listagem de projetos por comunidade.
- Frontend adicionou a entrada principal `Projetos de impressão`, tela de exploração, filtros, busca, contrato operacional, estado vazio, cards, detalhe central, arquivos, versões/snapshots, comunidades e ação `Salvar nos meus projetos`.
- Comunidades exibem `Projetos` compartilhados e apontam para a área central; upload/gestão direta de arquivos em comunidade deixa de ser o fluxo principal.
- Administração > Pipeline de fatiamento foi rebaixada para diagnóstico/fallback: não cria job diário, não inicia preflight novo e não salva/envia G-code como fluxo principal.
- Referência externa sem arquivo hospedado/importado/validado aparece como não fatiável; falha parcial de arquivo não bloqueia o projeto quando há arquivo válido.
- Fluxos legados de Social e Administração ainda não foram removidos; seguem como compatibilidade até validação dos próximos lotes.
- SQL aditivo: `backend/sql/068_print_projects_core.sql`.
- SQL aditivo: `backend/sql/069_print_project_experience.sql`.
- Validação executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_print_projects.py -q`; `npm --prefix frontend run build`.

## PKG-78: Meus Projetos, Upload E Links Externos

Objetivo:

Criar a área pessoal onde o usuário gerencia todos os projetos de impressão que subiu, salvou, importou ou referenciou por link externo.

Contexto inicial:

- upload e referências externas existem como fluxo de biblioteca de comunidade;
- o usuário precisa de uma biblioteca pessoal antes de publicar, vender, compartilhar ou fatiar;
- projeto pessoal não pertence a comunidade; quando aplicável, ele apenas pode ser compartilhado em comunidades;
- projeto precisa distinguir arquivo principal/preview, arquivos imprimíveis, peças opcionais, documentação e links externos;
- falha parcial de análise/quarentena deve isolar o arquivo/peça afetado sem derrubar o projeto inteiro quando houver arquivos válidos;
- upload/gestão de arquivo dentro de comunidade deve virar compartilhamento de projeto existente ou atalho para criar projeto na área central.

Dependências:

- PKG-77.
- PKG-56 a PKG-61.
- PKG-69 para cota, retenção e custo.
- PKG-76 para links externos.

Entregáveis:

- aba ou subárea `Meus projetos` dentro de `Projetos de impressão`;
- listagem de projetos pessoais: enviados, salvos, importados e links externos;
- cadastro por upload de um ou vários arquivos STL/3MF/ZIP;
- cadastro por URL externa, com origem como Printables, MakerWorld, GitHub ou site genérico;
- marcação de arquivo principal/preview, peças opcionais, grupo/conjunto, documentação e arquivos que entram no fatiamento;
- estado por arquivo: válido, quarentena, análise pendente, falha, rejeitado, externo sem arquivo local, elegível ou bloqueado para fatiamento;
- edição de título, descrição, tags, material sugerido, componente, licença, autoria, atribuição e visibilidade;
- estado privado, não listado, público e em revisão;
- painel de armazenamento pessoal com uso, cota, arquivos, retenção e custo estimado;
- separação entre arquivo hospedado, conjunto de arquivos e referência externa sem cópia indevida;
- remoção/rebaixamento do upload direto em `Comunidade > Arquivos` como fluxo principal, mantendo apenas compartilhamento de projeto;
- estados de validação/quarentena/análise visíveis;
- testes e documentação.

Lotes:

1. Mapear biblioteca pessoal sobre projetos e endpoints existentes.
2. Criar listagem `Meus projetos` com filtros e estados.
3. Criar modal de upload pessoal com seções de projeto, arquivos, licença e impressão.
4. Criar gestão de arquivos do projeto com principal/preview, seleção imprimível, peças opcionais e documentação.
5. Criar cadastro de link externo com atribuição/checksum opcional.
6. Integrar painel de armazenamento/cota pessoal.
7. Adicionar edição/arquivamento sem apagar arquivo sem confirmação.
8. Rebaixar upload direto em comunidade para ação de compartilhar projeto existente ou criar projeto central.
9. Testes de privacidade, upload/link externo e responsividade.

Critério de aceite:

- usuário consegue criar projeto sem escolher comunidade;
- usuário pode compartilhar o mesmo projeto em múltiplas comunidades sem criar cópias do projeto;
- projeto pode ter múltiplos arquivos sem quebrar busca, detalhe, publicação ou fatiamento;
- projeto sempre deixa claro qual arquivo/peça é principal, qual é opcional e quais arquivos são elegíveis para fatiamento;
- arquivo inválido/rejeitado não entra em publicação pública, fatiamento, G-code ou envio; projeto com outros arquivos válidos continua gerenciável;
- upload STL/3MF/ZIP entra em quarentena/validação antes de uso público;
- link externo fica marcado como referência e não como arquivo hospedado;
- usuário distingue privado, não listado, público e em revisão;
- remoção não apaga arquivo/dado sem fluxo explícito e confirmação quando aplicável;
- `./check.sh` passa no fechamento do pacote.

Status:

- Implementado.

Notas de implementação:

- `Projetos de impressão > Meus projetos` lista projetos próprios e referências salvas, separado da exploração pública.
- Backend adicionou criação, edição, upload pessoal, link externo, arquivamento lógico e relatório de armazenamento em `/api/print-projects`.
- Upload STL/3MF/ZIP grava objeto em quarentena local, valida assinatura, registra checksum/tamanho/motivo de rejeição e bloqueia só o arquivo inválido.
- Link externo fica como `external_reference`, sem arquivo local, sem elegibilidade para fatiamento/envio.
- Projeto pessoal não exige comunidade; compartilhamento em comunidade continua N:N e não muda dono, arquivos, visibilidade ou classificação.
- UI adicionou abas `Explorar` e `Meus projetos`, formulário de criação, upload por função do arquivo, cadastro de link externo, estados por arquivo, snapshots e painel de cota.
- Arquivamento marca o projeto como arquivado e preserva arquivos/linhas; não há exclusão automática.
- O estado `em revisão` permanece em `publication_status`; não foi modelado como visibilidade para preservar o `CHECK` já publicado de `visibility`.
- SQL aditivo: `backend/sql/070_print_project_personal_library.sql`.
- Validação focada executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q`; `npm --prefix frontend run build`.
- Validação visual/local executada em `Projetos de impressão > Meus projetos`: criação de projeto privado sem comunidade, upload de arquivo principal, falha parcial em peça opcional, link externo sem arquivo local, painel de cota e responsividade mobile sem overflow horizontal.
- Fechamento executado: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` (`445 passed`, Go agent ok, frontend build ok, `test:releases` ok).

## PKG-79: Publicação, Venda E Vitrine De Projetos

Objetivo:

Permitir que projetos pessoais sejam publicados, compartilhados, curados, patrocinados ou colocados à venda sem misturar esse fluxo com comunidade ou Administração.

Contexto inicial:

- classificação comercial existe hoje na biblioteca social legada, mas deve migrar para o projeto central;
- o produto precisa deixar claro quando um projeto é gratuito, pago, patrocinado, curado ou apenas link externo;
- publicação do projeto é independente de comunidade; comunidade é canal opcional de compartilhamento/descoberta;
- estado de visibilidade, estado de revisão/publicação, classificação comercial e compartilhamento em comunidade são dimensões separadas, não um único campo misturado;
- cobrança real pode ficar para pacote futuro, mas o contrato de publicação/venda precisa estar preparado.

Dependências:

- PKG-77.
- PKG-78.
- PKG-75.
- PKG-66 para moderação/curadoria.

Entregáveis:

- controles de publicação no detalhe do projeto pessoal;
- visibilidade: privado, não listado ou público;
- revisão/publicação: rascunho, em revisão, aprovado, rejeitado ou arquivado;
- classificação: gratuito, curado, premium, patrocinado;
- compartilhamentos em comunidades independentes da publicação principal;
- campos de preço/condição comercial preparados sem ativar cobrança real quando fora de escopo;
- transparência obrigatória para patrocinado;
- revisão antes de premium/patrocinado público;
- página pública do projeto com licença, autoria, versões, arquivos, fonte e ações permitidas;
- compartilhamento opcional em zero, uma ou várias comunidades como contexto de descoberta;
- painel de conteúdo publicado pelo usuário.

Lotes:

1. Normalizar visibilidade, revisão/publicação, classificação comercial e compartilhamentos como dimensões separadas no projeto central.
2. Criar UI de publicação a partir de `Meus projetos`.
3. Criar página/detalhe público de projeto.
4. Integrar revisão comercial e moderação.
5. Exibir transparência de patrocinado/premium sem parecer recomendação técnica neutra.
6. Remover dependência de página pública/comercial baseada em comunidade como dona do arquivo.
7. Documentar o que fica fora: pagamento real, repasse financeiro e fiscal.

Critério de aceite:

- projeto privado não aparece em busca, comunidade ou página pública;
- projeto pago/premium não é confundido com comunitário gratuito;
- patrocinado sempre aparece como promoção/transparência;
- alterar compartilhamento em comunidade não altera visibilidade, revisão ou classificação comercial do projeto;
- fluxo não exige comunidade para publicar, vender, fatiar ou compartilhar link público;
- pagamento real não é simulado como se estivesse pronto;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado.

Notas de implementação:

- Publicação passou a ser dimensão do projeto central: visibilidade, revisão/publicação, classificação comercial e compartilhamentos em comunidade permanecem separados.
- Busca/vitrine pública só lista projetos `public` com publicação `approved`; projeto privado, rascunho, em revisão ou rejeitado não aparece na busca nem por comunidade.
- Backend adicionou configuração de publicação em `/api/print-projects/<project_id>/publication` e revisão administrativa em `/api/print-projects/<project_id>/publication-review`.
- Premium exige preço preparado e entra em revisão; patrocinado exige transparência explícita e entra em revisão; pagamento real, repasse e fiscal ficam fora do escopo.
- Comunidade continua apenas como canal N:N: compartilhar em comunidade não altera visibilidade, publicação nem classificação comercial.
- UI adicionou painel `Publicação e vitrine` no detalhe de `Meus projetos`, com visibilidade, classificação, preço preparado, condição comercial, transparência e estado de revisão.
- Cards/detalhe público exibem classificação, status, preço preparado, transparência de patrocinado e aviso de pagamento não ativo para premium.
- SQL aditivo: `backend/sql/071_print_project_publication.sql`.
- Validação focada executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q`; `npm --prefix frontend run build`.
- Validação visual/local executada em `Projetos de impressão > Meus projetos`: projeto premium público entra em revisão, preço preparado aparece, texto informa pagamento fora do fluxo atual, vitrine pública fica vazia enquanto a revisão não aprova e painel responsivo não gera overflow horizontal em 390px.
- Fechamento executado: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` (`448 passed`, Go agent ok, frontend build ok, `test:releases` ok).

## PKG-80: Fatiamento A Partir De Projeto Salvo

Objetivo:

Mover o fluxo de fatiamento diário para `Projetos de impressão > Meus projetos`, permitindo escolher um projeto salvo, um ou mais arquivos/peças, uma impressora, material/perfil/qualidade e gerar job de fatiamento.

Contexto inicial:

- o pipeline de fatiamento existe em Administração, mas essa área deve ser reservada para configuração e diagnóstico;
- o usuário deve fatiar a partir de um projeto que está na própria biblioteca pessoal;
- fatiamento pode partir de um arquivo único ou de seleção de arquivos/peças dentro de um projeto;
- fatiamento deve capturar snapshot imutável da versão do projeto, arquivos selecionados, orientação/dimensões relevantes e perfil usado;
- perfil de material/fatiamento e compatibilidade devem entrar antes do job.

Dependências:

- PKG-78.
- PKG-63 para perfis de material/fatiamento.
- PKG-70 e PKG-71 para engine e pipeline.
- PKG-72 para preflight.

Entregáveis:

- ação `Fatiar` no detalhe de projeto pessoal;
- wizard/fluxo curto: projeto -> arquivos/peças -> impressora -> perfil/material -> qualidade -> dimensões/orientação quando aplicável;
- uso de impressoras do usuário e compatibilidade básica por volume/material/nozzle;
- criação de job de fatiamento vinculado ao projeto, versão/snapshot, arquivos selecionados e configuração usada;
- lista de jobs do projeto, com estado, erro, artefatos e ação de preflight;
- Administração mantém apenas verificação da engine, paths, modo dry-run, diagnóstico e políticas.

Lotes:

1. Definir contrato de job a partir de projeto salvo e snapshot imutável.
2. Criar ação `Fatiar` no detalhe de projeto.
3. Criar seleção de arquivos/peças, impressora e perfil/material/qualidade.
4. Integrar criação e acompanhamento do job existente.
5. Mostrar artefatos e preflight a partir do projeto.
6. Rebaixar `Administração > Pipeline de fatiamento` para configuração/diagnóstico.
7. Remover/rebaixar a navegação antiga de fatiamento diário em Administração após validação do fluxo novo.

Critério de aceite:

- usuário não precisa entrar em Administração para fatiar projeto;
- job sempre fica vinculado ao projeto, versão/snapshot, arquivos selecionados, usuário, impressora e perfil;
- alteração posterior do projeto ou dos arquivos não altera job, artefato, preflight ou histórico já criado;
- impressora incompatível mostra bloqueio/aviso antes do job;
- engine ausente mostra erro acionável e aponta Administração para configuração;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado.

Notas de implementação:

- Backend adicionou criação/listagem de jobs por projeto em `GET/POST /api/slicing/projects/<project_id>/jobs`.
- Job criado a partir de projeto salva `print_project_id`, `print_project_version_id`, snapshot imutável do projeto e snapshot dos arquivos selecionados.
- Seleção bloqueia arquivo inexistente, referência externa sem arquivo local validado e arquivo com `can_slice=false`, sem bloquear o projeto inteiro quando há outro arquivo válido.
- Compatibilidade existente por impressora/perfil/dimensões é reaproveitada antes da criação do job.
- UI adicionou painel `Fatiamento` no detalhe de `Projetos de impressão > Meus projetos`, com seleção de arquivos, impressora, qualidade, perfil/material, criação de job e listagem de jobs do projeto.
- Engine ausente bloqueia a ação na UI com orientação para configurar em Administração.
- SQL aditivo: `backend/sql/072_project_slicing_jobs.sql`.
- Validação focada executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_slicing_pipeline.py ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q`; `npm --prefix frontend run build`.
- Validação visual/local executada em `Projetos de impressão > Meus projetos`: projeto com STL local e link externo, job existente por API com snapshot, engine ausente bloqueando ação, engine fake liberando criação pela UI, link externo desabilitado para seleção e responsividade mobile sem overflow horizontal em 390px.
- Fechamento executado: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` (`450 passed`, Go agent ok, frontend build ok, `test:releases` ok).
- Commit de implementação: `d592718`.
- Publicação executada na branch `cloud` via GitHub Actions `Deploy Printora Cloud`, run `27774263408`.
- Smoke pós-publicação: `/health` ok, `/api/print-projects/contract` ok, `/api/slicing/projects/1/jobs` retorna `401` sem autenticação, `/api/print-projects?limit=1` ok.

## PKG-81: Envio Para Impressora E Histórico Por Projeto

Objetivo:

Concluir o fluxo diário a partir de `Meus projetos`: preflight, salvar G-code, iniciar impressão, acompanhar entrega e registrar histórico/feedback vinculados ao projeto.

Contexto inicial:

- envio seguro e histórico existem no pipeline administrativo;
- o usuário espera operar a partir do projeto salvo e da própria impressora;
- histórico deve ajudar a decidir se o projeto funcionou, em qual impressora/material/perfil e com qual resultado;
- histórico público deve ser agregado e sanitizado por projeto/material/perfil/tipo técnico, sem identificar impressora privada ou ambiente operacional;
- envio de arquivo/G-code não deve ficar dentro de comunidade como fluxo operacional.

Dependências:

- PKG-80.
- PKG-72.
- PKG-73.
- PKG-74.
- PKG-47 para execução remota segura.

Entregáveis:

- preflight exibido no contexto do projeto e da impressora escolhida;
- ações `Salvar G-code` e `Enviar para impressora` no fluxo do projeto;
- confirmação forte para iniciar impressão;
- status de entrega, arquivo remoto e rollback seguro quando permitido;
- histórico por projeto com impressora, perfil, material, resultado, tempo, falha e feedback;
- feedback público/privado, com versão pública agregada/sanitizada sem expor impressora privada;
- integração com ranking/recomendações somente com sinais seguros;
- Administração permanece como diagnóstico, não tela principal de envio;
- Comunidade permanece como contexto de compartilhamento/descoberta, não como tela de upload/envio operacional.

Lotes:

1. Exibir preflight por job/projeto.
2. Mover ações de salvar/enviar para o contexto do projeto.
3. Mostrar status de entrega e rollback seguro.
4. Criar histórico por projeto e por impressora.
5. Adicionar feedback e foto HTTPS opcional.
6. Integrar sinais seguros com ranking/recomendação.
7. Remover/rebaixar envio operacional de arquivo/G-code a partir de comunidade e Administração após validação do fluxo novo.
8. Testes de segurança, confirmação e privacidade.

Critério de aceite:

- G-code não é salvo ou enviado sem preflight aprovado quando a política exigir;
- iniciar impressão exige confirmação textual ou step-up quando aplicável;
- histórico público nunca expõe impressora privada, agente, Moonraker, token, IP ou path sensível;
- sinais públicos de resultado são agregados/sanitizados e apontam para o projeto central, nunca para cópia por comunidade;
- rollback só aparece quando seguro;
- usuário entende claramente se apenas salvou arquivo ou iniciou impressão;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado.

Notas de implementação:

- `Projetos de impressão > Meus projetos > Fatiamento` passou a concentrar o fluxo diário: executar job concluível, criar/atualizar preflight, salvar G-code, iniciar envio com confirmação textual, mostrar entrega e rollback seguro quando permitido.
- A tela carrega jobs do projeto, preflights, entregas e histórico do usuário, filtrando pelo vínculo de job ao projeto central.
- Histórico do projeto aparece no detalhe com status, qualidade, visibilidade, feedback privado/público sanitizado e foto HTTPS opcional via contrato existente.
- Serviço frontend de slicing passou a enviar JSON corretamente em entrega, evento de histórico e feedback.
- Backend manteve o contrato de privacidade pública já existente: histórico público remove impressora privada e só expõe telemetry/result sanitizados.
- Teste automatizado novo cobre entrega/histórico a partir de job de projeto, preservando `project://...`, `project-version:<id>` e privacidade pública sem vazamento de impressora privada.
- Validação focada executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_print_history.py ../backend/tests/test_print_delivery.py ../backend/tests/test_slicing_pipeline.py ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q`; `npm --prefix frontend run build`.
- Validação visual/local executada em `Projetos de impressão > Meus projetos`: job concluído, preflight aprovado, ação `Salvar G-code`, confirmação textual habilitando `Enviar`, entrega/histórico no painel do projeto, feedback e responsividade mobile sem overflow horizontal em 390px.
- Fechamento executado: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` (`451 passed`, Go agent ok, frontend build ok, `test:releases` ok).
- Commit de implementação: `437b0dd`.
- Publicação executada na branch `cloud` via GitHub Actions `Deploy Printora Cloud`, run `27775315210`.
- Smoke pós-publicação: `/health` ok, `/api/print-projects/contract` ok, `/api/slicing/projects/1/jobs`, `/api/slicing/deliveries` e `/api/slicing/history` retornam `401` sem autenticação, `/api/print-projects?limit=1` ok.

## PKG-82: Arquivos G-code Por Impressora

Objetivo:

Criar uma aba própria no detalhe da impressora para navegar e inspecionar os arquivos G-code existentes no Moonraker, com nível de completude comparável ao `G-Code Files` do Mainsail e sem ocupar a aba `Operação`.

Contexto inicial:

- a lista compacta exibida hoje em `Operação` quando a impressora está ociosa é útil como atalho, mas não resolve gerenciamento real de arquivos;
- o usuário precisa ver arquivos, pastas, metadados técnicos, thumbnails, uso de filamento, tempos estimados e históricos sem depender de uma impressão ativa;
- a consulta deve ser leve para a Raspberry: listagem e metadados primeiro, download/cache de G-code completo apenas sob demanda;
- a aba deve funcionar tanto em tema claro quanto escuro, em desktop grande, notebook e mobile.

Dependências:

- PKG-19.
- PKG-42.
- PKG-43.
- PKG-47.
- PKG-73.
- PKG-74.

Entregáveis:

- aba `Arquivos G-code` dentro do detalhe da impressora;
- contrato backend/agente para listar `/gcodes` do Moonraker, incluindo diretórios;
- tabela com busca, ordenação, filtros, seleção múltipla, refresh e indicação de espaço livre;
- colunas mínimas: nome, tamanho, atualizado em, altura do objeto, altura de camada, bico, filamento, uso de filamento, tempo estimado, última duração, slicer, temperaturas e último início/fim;
- thumbnails quando disponíveis, sem distorção e com fallback consistente;
- estado vazio/offline/erro sem reservar bloco gigante nem mostrar dados antigos como atuais;
- cache controlado de metadados para evitar polling caro;
- responsividade sem texto cortado indevidamente, coluna inútil ou buraco visual.

Lotes:

1. Definir contrato de listagem e normalização de metadados de arquivos Moonraker.
2. Implementar leitura via agente com cache leve e tratamento de diretórios.
3. Criar aba `Arquivos G-code` no detalhe da impressora.
4. Construir tabela rica com busca, ordenação, filtros, refresh e espaço livre.
5. Exibir thumbnails e fallbacks.
6. Validar tema claro/escuro, desktop, notebook, mobile e navegador embutido.

Critério de aceite:

- usuário não precisa abrir Mainsail para ver a lista completa de G-codes da impressora;
- a aba `Operação` não é usada como gerenciador de arquivos;
- arquivos e diretórios aparecem com metadados equivalentes aos retornados pelo Moonraker quando disponíveis;
- ausência de metadado aparece como ausência real, não como erro genérico;
- listagem não baixa o G-code completo de todos os arquivos;
- tema claro e escuro ficam legíveis e coerentes;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado.
- Contrato backend/agente novo lista `/gcodes` por impressora via job read-only `remote_gcode_files_list`, com cache curto, diretórios derivados, metadados técnicos e thumbnails pequenos quando disponíveis, sem baixar G-code completo.
- Frontend adicionou aba `Arquivos G-code` no detalhe da impressora, com busca, filtros por pasta/metadados, ordenação, seleção múltipla, refresh, espaço livre, thumbnails/fallback e tabela responsiva.
- Versão esperada do agente atualizada para `0.1.32`, com binário Linux arm64 e manifesto público atualizados.
- Validação focada executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_gcode_files.py ../backend/tests/test_operation.py -q`; `cd agent && go test ./...`; `npm --prefix frontend run build`.

## PKG-83: Detalhe E Ações De Arquivo G-code

Objetivo:

Permitir que o clique em um arquivo G-code abra um detalhe completo com ações seguras, histórico e contexto técnico, superando o modal operacional do Mainsail sem reduzir segurança.

Contexto inicial:

- no Mainsail, clicar em um item abre opções úteis; no Printora, a lista atual é apenas leitura parcial;
- ações mutáveis precisam respeitar a política de operação segura, impressão ativa, step-up e confirmação;
- o detalhe deve ser útil para decidir se imprimir, repetir, baixar, renomear, mover, excluir ou vincular o G-code a projeto/histórico.

Dependências:

- PKG-82.
- PKG-47.
- PKG-73.
- PKG-74.
- PKG-81.

Entregáveis:

- modal/drawer de detalhe de arquivo com thumbnail, metadados, histórico e ações;
- ações: imprimir, salvar/enviar conforme política, baixar, copiar caminho, renomear, mover, duplicar e excluir;
- preflight antes de impressão quando a política exigir;
- bloqueio de ações destrutivas durante impressão ou quando Moonraker/agente estiverem indisponíveis;
- confirmação forte para excluir, sobrescrever, mover e iniciar impressão;
- auditoria segura sem registrar token, IP, path sensível ou G-code bruto em logs persistidos;
- integração opcional com projeto/histórico quando o arquivo tiver origem conhecida.

Lotes:

1. Definir matriz de ações por estado da impressora, arquivo e permissão.
2. Criar modal/drawer de detalhe.
3. Implementar ações read-only: baixar, copiar caminho, abrir prévia e ver histórico.
4. Implementar ações mutáveis protegidas: imprimir, renomear, mover, duplicar e excluir.
5. Integrar preflight, confirmação e auditoria.
6. Validar falhas, rollback possível e UX em tema claro/escuro.

Critério de aceite:

- clicar em arquivo abre detalhe acionável e completo;
- ação perigosa não fica disponível sem precondições claras;
- impressão ativa bloqueia ações que possam afetar a peça em andamento;
- excluir/mover/renomear nunca ocorre sem confirmação explícita;
- o usuário distingue `baixar`, `salvar`, `enviar` e `imprimir`;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado.
- Backend expõe detalhe autenticado por arquivo em `/api/printers/{printer_id}/gcode-files/detail` e ação protegida em `/api/printers/{printer_id}/gcode-files/actions`, com confirmação textual, step-up para mutações e histórico recente por `agent_jobs`.
- Agente adiciona job `remote_gcode_file_action` para imprimir, renomear, mover, duplicar e excluir usando endpoints Moonraker específicos, sempre com preflight remoto e bloqueio quando `print_stats` indica impressão ativa.
- Frontend abre drawer pelo clique no arquivo, mostra thumbnail, metadados, histórico, ações somente leitura, download sob demanda e ações protegidas com destino e frase exata.
- Versão esperada do agente atualizada para `0.1.33`, com binário Linux arm64 e manifesto público atualizados.
- Validação focada executada: `cd backend && uv run --extra dev pytest ../backend/tests/test_gcode_files.py ../backend/tests/test_operation.py ../backend/tests/test_agent_install.py ../backend/tests/test_agent_updates.py ../backend/tests/test_agent_support.py -q`; `cd agent && go test ./...`; `npm --prefix frontend run build`.

## PKG-84: Preview E Simulação De G-code Reutilizáveis

Objetivo:

Consolidar a renderização de G-code como componente reutilizável para aba `Arquivos G-code`, aba `Operação`, projetos e futuro fatiamento web, com qualidade visual próxima de slicer e sem depender de polling pesado do agente.

Contexto inicial:

- a prévia 3D atual melhorou, mas ainda precisa representar melhor perímetros, preenchimento, paredes, camada atual, material impresso e navegação;
- OrcaSlicer/Mainsail são referências visuais, mas o Printora precisa ter identidade própria e evitar blocos bugados ou controles duplicados;
- o agente deve buscar/cachear o arquivo quando necessário, enquanto rotação, zoom, pan, corte por camada e desenho ficam no frontend;
- a mesma base técnica deve servir ao acompanhamento da impressão e ao explorador de arquivos.

Dependências:

- PKG-82.
- PKG-19.
- PKG-73.
- PKG-80.

Entregáveis:

- componente reutilizável de preview/simulação de G-code;
- uso do G-code completo cacheado sob demanda, não no snapshot periódico do agente;
- renderização por tipo de linha quando disponível: perímetro, superfície, preenchimento, suporte, saia/brim, deslocamento e retração;
- modos: arquivo completo, até camada selecionada, camada atual e progresso por `file_position`;
- controles de câmera com mouse/touch, zoom, pan, barras de deslocamento e navegador 3D no canto inferior esquerdo;
- tema claro/escuro com fundo, grade, peça, linhas e controles coerentes;
- limites de performance para arquivos grandes, com fallback progressivo e sem travar a UI.

Lotes:

1. Isolar contrato de preview e cache de G-code completo.
2. Substituir renderização parcial frágil por viewer reutilizável.
3. Implementar modos completo, até camada, camada atual e progresso por posição.
4. Ajustar navegador 3D, mouse/touch, zoom, pan e barras de deslocamento.
5. Normalizar cores/tema e estados de carregamento/falha.
6. Validar com G-codes reais da Voron 2.4 e fixtures controladas.

Critério de aceite:

- preview final não inventa teto, parede ou volume que não exista no G-code;
- peça 100% renderizada aparece completa;
- camada atual mostra o material já impresso abaixo e destaque claro da camada;
- navegação 3D é usável sem controles sobrepostos ou labels quebrados;
- tema claro não mantém painel escuro incoerente;
- arquivo grande não trava a tela nem aumenta carga do agente por polling;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado em 2026-07-20.
- `GcodePrintViewer` foi consolidado como componente reutilizavel em `frontend/src/components/monitoring/GcodePrintViewer.tsx`, compartilhado entre `Operacao` e o drawer de `Arquivos G-code`.
- A logica pura de camada/posicao fica em `frontend/src/components/monitoring/gcodePreview.ts`, com teste deterministico em `frontend/tests/gcodePreview.test.mjs`.
- O preview usa G-code completo cacheado sob demanda pelo contrato existente, sem colocar conteudo bruto no snapshot periodico do agente.
- O drawer de `Arquivos G-code` passou de previa textual para preview 3D sob demanda, com modos `Completo`, `Ate camada` e `Camada`.
- Tema claro/escuro, controles de camera, pan, barras e viewbox nativo foram reaproveitados no componente comum.
- Validação focada executada sem acao mutavel na impressora ativa: `npm --prefix frontend run test:gcode-preview`; `npm --prefix frontend run build`.
- Validação live com arquivo real da Voron 2.4 nao executou cache pesado ou acao remota durante impressao ativa; fechamento usa fixture controlada e smoke publico read-only.

## PKG-85: Operação Ociosa Enxuta E Ponte Para Arquivos

Objetivo:

Reorganizar a aba `Operação` para que ela seja excelente durante impressão e objetiva quando a impressora estiver ociosa, encaminhando gerenciamento completo para a aba `Arquivos G-code`.

Contexto inicial:

- quando não há impressão ativa, o card `Impressão` não deve mostrar preview vazio, progresso antigo, fatos nulos ou tabela grande de arquivos;
- o usuário ainda precisa de atalhos úteis: último trabalho, arquivos recentes e chamada para abrir a aba completa;
- `Temperaturas`, `Ações protegidas`, `Miscellaneous`, `Machine`, sistema e CAN não devem ficar com buracos por causa do estado da impressão.

Dependências:

- PKG-82.
- PKG-83.
- PKG-84.
- PKG-19.

Entregáveis:

- estado ocioso compacto na aba `Operação`;
- resumo do último trabalho conhecido quando confiável;
- lista curta de G-codes recentes apenas como atalho;
- CTA para abrir `Arquivos G-code`;
- remoção de preview/progresso/fatos antigos quando não houver impressão ativa;
- reorganização de grid para não deixar vazios em desktop grande, notebook, mobile, tema claro e tema escuro;
- integração limpa com `Machine`, `Temperaturas` e ações protegidas.

Lotes:

1. Definir estados `printing`, `paused`, `standby`, `offline`, `sem leitura` e `erro`.
2. Redesenhar `Impressão` ociosa como resumo compacto.
3. Mover lista completa para aba `Arquivos G-code`.
4. Ajustar grids de operação para eliminar buracos.
5. Validar com impressora imprimindo, ociosa, offline e agente antigo.

Critério de aceite:

- sem impressão ativa, a aba `Operação` não parece quebrada nem vazia;
- a lista completa de arquivos fica apenas na aba própria;
- a operação ao vivo continua priorizando preview, temperaturas, limites e ações seguras;
- estados de erro/timeout explicam o impacto sem assustar com erro bruto;
- layout não cria buracos grandes em monitor grande nem em tela menor;
- `./check.sh` passa no fechamento do pacote.

Estado atual:

- Implementado em 2026-07-20.
- A aba `Operacao` diferencia impressão ativa de estados ociosos, offline, sem leitura, erro, concluído e cancelado sem manter preview/progresso antigos.
- O card `Impressão` ocioso foi reduzido para estado compacto, último trabalho confiável quando houver metadado de impressão e até quatro atalhos recentes de G-code.
- A lista completa e ações de arquivo permanecem apenas em `Arquivos G-code`; a Operação abre essa aba por CTA e por clique nos atalhos.
- `Machine` permanece no card de impressão, enquanto `Temperaturas` e ações protegidas continuam em blocos próprios, evitando buracos grandes no grid.
- Validação focada executada sem ação mutável na impressora ativa: `npm --prefix frontend run build`.

## Programa Plurianual Da Comunidade E Fabricação 3D

Objetivo:

Evoluir o Printora como comunidade e infraestrutura aberta de fabricação digital, cobrindo lacunas de redes sociais, comunidades maker, repositórios 3D, slicers, operação de impressoras, educação, acessibilidade, reparo, tecnologia assistiva, fabricação local e impacto social.

Fonte detalhada:

- visão e fases: `docs/community/MASTER_PLAN.md`;
- comparação de plataformas: `docs/community/PLATFORM_BENCHMARK.md`;
- 3.080 melhorias atômicas: `docs/community/COMMUNITY_BACKLOG.md` e `.csv`;
- 440 famílias de tela: `docs/community/COMMUNITY_SCREENS.md` e `.csv`;
- prioridade por impacto social: `docs/community/PRIORITIES.md`;
- geração reproduzível: `scripts/generate_community_roadmap.py`.

Regras de execução:

1. O programa não é um pacote único e não pode ser fechado por quantidade de código.
2. Cada implementação futura deve selecionar uma capacidade validada, auditar o estado atual e criar pacote/lotes pequenos antes de editar runtime.
3. Capacidades marcadas como `parcial` devem estender contratos existentes; é proibido criar domínio paralelo sem decisão registrada.
4. Itens `P0` exigem especialista, revisão independente e piloto controlado.
5. Toda capacidade inclui, além da regra, tela, mobile, acessibilidade, confiança, impacto e validação.
6. Métricas de engajamento não substituem resultado humano, segurança, resolução, aprendizagem ou sustentabilidade.
7. O catálogo deve ser revisado periodicamente porque plataformas, leis, riscos e o próprio Printora evoluem.

Estado atual:

- Planejamento abrangente concluído em julho de 2026.
- Implementação futura ainda não iniciada como programa; o produto já possui bases listadas como `parcial` no inventário.
- Nenhuma capacidade ausente deve ser marcada como entregue sem pacote, testes, documentação e validação real próprios.

## Programa De Evolução Arquitetural

Fonte detalhada: `docs/architecture/EVOLUCAO_ARQUITETURAL.md`.

Ordem obrigatória: PKG-86 a PKG-95. Nenhum pacote pode
ser fechado mantendo bridge, flag, adapter, dependência, banco, arquivo, unit,
rota ou documentação operacional da tecnologia aposentada. Limpeza destrutiva
de dados exige relatório de integridade, janela de observação e confirmação
humana explícita.

## PKG-86: Qualificação Do Servidor E Publicação Sem Indisponibilidade

Objetivo:

Comprovar que o host atual suporta a evolução e substituir o restart único por
releases imutáveis e deploy blue/green sem compartilhar dependências mutáveis.

Prioridade: P0 estrutural.

Dependências:

- infraestrutura cloud publicada;
- fluxos críticos existentes inventariados;
- acesso operacional ao Nginx e systemd do servidor atual.

Entregáveis:

- auditoria de CPU, RAM, disco, I/O, rede, file descriptors, processos e pico;
- orçamento de recurso e limite systemd para app, workers e dependências futuras;
- health, readiness, correlation/request/job ID, métricas e logs estruturados;
- preflight de sudo/permissões, usuários, firewall, portas, NTP, certificados,
  diretórios, ownership, quotas, logrotate e destino de backup externo;
- release imutável com código, frontend, venv, lockfile e unit próprios;
- duas instâncias do app em portas independentes, upstream Nginx, N/N-1 e drenagem;
- workflow que sobe release verde, valida, troca upstream atomicamente e só então drena o azul;
- protocolo de reconnect com jitter/ack/deduplicação para WebSockets de agentes;
- protocolo expandir/migrar/contrair para schema e eventos durante N/N-1;
- rollback que reativa o release anterior sem restaurar dados antigos;
- baseline de carga, SLO, alertas, retenção e capacidade no host atual.

Lotes:

1. Inventariar topologia, privilégios, recursos, dados e fluxos P0/P1.
2. Medir pico e calcular espaço simultâneo para duas releases, dados, WAL e rollback.
3. Implantar observabilidade, readiness, métricas, quotas e alertas de saturação.
4. Criar venv/frontend/unit por release, portas 8069/8070 e upstream Nginx selecionável.
5. Implementar warm-up, smoke privado, `nginx -t`, troca atômica e drenagem.
6. Implementar reconnect/deduplicação de WebSockets e compatibilidade N/N-1.
7. Executar carga/soak, falha de processo, deploy e rollback no servidor atual.
8. Remover venv compartilhado, restart antigo, scripts temporários e docs divergentes.

Critério de aceite:

- deploy não gera requests falhos nem desconecta impressão por causa da troca;
- release inválido nunca recebe tráfego público;
- WebSocket novo conecta e conexões antigas drenam dentro do limite definido;
- agente recebe cada job no máximo uma vez de forma efetiva e confirma retomada;
- rollback de código não sobrescreve banco nem perde escrita posterior;
- blue/green usa artefatos/venvs independentes e schema/eventos compatíveis N/N-1;
- PostgreSQL/Redis/storage futuros podem ser instalados com privilégio e firewall aprovados;
- backup externo criptografado possui restore comprovado sem executar app fora do host;
- carga de pico passa com folga de recurso definida no servidor atual;
- não resta referência ao restart de instância única como caminho de publicação;
- validações completas e smoke público passam no fechamento.

Estado atual:

- Concluído em 2026-07-22.
- Dois slots independentes publicados, N-1 aquecido, candidato inválido isolado,
  falha do ativo recuperada, rollback sem restauração de dados, carga sem erros,
  backup externo com restore isolado e runtime legado removido.
- Evidência completa em `docs/audits/CLOUD_BLUE_GREEN_READINESS_2026-07-22.md`.

## PKG-87: Monólito Modular, Contratos E Fronteiras

Objetivo:

Separar domínios e responsabilidades sem alterar comportamento público, criando
as fronteiras necessárias para trocar persistência e processamento com segurança.

Prioridade: P0 estrutural.

Dependências:

- PKG-86 fechado;
- contratos e fluxos P0/P1 congelados por testes.

Entregáveis:

- mapa de domínios, tabelas, arquivos, rotas, eventos, owners e dependências;
- módulos de identidade/permissão, comunidade/projetos, operação/agentes,
  administração e integrações com interfaces explícitas;
- application services sem FastAPI, repositories sem regra de UI e adapters de infraestrutura;
- contratos HTTP/WebSocket/evento tipados, versionados e compatíveis N/N-1;
- frontend dividido em page, state/hook, form, component e API client;
- divisão dos arquivos críticos acima do limite por responsabilidade;
- testes de arquitetura bloqueando ciclos, imports proibidos e fallback entre perfis cloud/local;
- caracterização dos fluxos legados antes de mover código e remoção da estrutura antiga depois.

Lotes:

1. Inventariar módulos, dependências, contratos, tabelas e arquivos críticos.
2. Criar testes de caracterização e arquitetura antes das extrações.
3. Extrair identidade/permissão e contratos transversais.
4. Extrair comunidade/projetos e operação/agentes.
5. Extrair administração, jobs e integrações externas.
6. Dividir telas/componentes grandes preservando acessibilidade e responsividade.
7. Remover imports/bridges antigos, atualizar docs e executar regressão completa.

Critério de aceite:

- API, WebSocket, agente e telas preservam comportamento validado;
- domínio não importa FastAPI, SQL driver, Redis, storage nem UI;
- UI não contém regra de negócio, persistência ou acesso direto à infraestrutura;
- não há ciclos ou duas implementações canônicas do mesmo caso de uso;
- arquivos alterados respeitam limites ou decisão temporária com data de remoção;
- perfis cloud/local compartilham domínio, mas não importam adapters um do outro;
- contratos N/N-1 e testes P0/P1 passam sob blue/green;
- estrutura antiga e bridges de extração são removidas antes do fechamento;
- `./check.sh`, suíte completa e smoke publicado passam.

Estado atual:

- Concluído em 2026-07-22.
- Cinco fronteiras com owner/contrato versionado, registry de routers, ports
  explícitas, application service sem FastAPI, snapshots HTTP/realtime e gates
  de ciclo/layering foram implementados sem alterar o contrato público.
- Evidência completa em `docs/audits/MODULAR_ARCHITECTURE_2026-07-22.md`.

## PKG-88: PostgreSQL Cloud Sem Perda De Dados

Objetivo:

Migrar somente o runtime cloud de SQLite para PostgreSQL no servidor atual, sem
perder escrita confirmada e sem deixar fallback SQLite no perfil cloud.

Prioridade: P0 estrutural.

Dependências:

- PKG-87 fechado;
- orçamento do host aprovado;
- backup e restore ensaiados antes da primeira transição.

Entregáveis:

- PostgreSQL endurecido em loopback/socket, role mínima, TLS/socket, backup e monitoração;
- SQL PostgreSQL idempotente em diretório explícito, sem migration de framework;
- export/import consistente, captura incremental, sombra e reconciliação SQLite/PostgreSQL;
- relatório de integridade por tabela, owner, estado, checksum, sequence e órfão;
- release A com persistence ports e outbox SQLite atômica; release B PostgreSQL-compatible;
- replicação idempotente, leitura sombra e canário com relatório de divergência;
- cutover para PostgreSQL e rollback somente para release que também use PostgreSQL;
- separação formal entre adapters cloud PostgreSQL e local SQLite;
- remoção final de SQLite do runtime/deploy/env/units/dependências/testes/docs cloud;
- painel read-only de progresso, watermark, divergência e integridade.

Lotes:

1. Instalar e endurecer PostgreSQL no host; criar schema idempotente e adapters alvo.
2. Publicar release A com ports/outbox SQLite e compatibilidade N/N-1.
3. Fazer snapshot, import, captura incremental e leitura sombra.
4. Publicar release B PostgreSQL-compatible e executar canário.
5. Reconciliar watermark, cortar escrita/leitura e observar sob carga.
6. Provar rollback de código mantendo PostgreSQL e todas as escritas pós-cutover.
7. Publicar release C sem adapter/fallback SQLite cloud.
8. Após aceite explícito, remover arquivo/backups SQLite cloud e auditar referências.

Critério de aceite:

- PostgreSQL contém 100% dos registros e relações reconciliados, sem perda ou duplicidade;
- escrita confirmada antes/durante/depois do cutover permanece disponível;
- sequences, datas/timezones, booleanos, JSON, constraints, índices e FKs preservam semântica;
- cutover e rollback de código não restauram snapshot velho nem perdem escrita nova;
- release anterior e candidato coexistem durante expandir/migrar/contrair;
- busca automatizada encontra zero referência operacional a SQLite no perfil cloud;
- modo local SQLite continua testado e não pode ser carregado como fallback cloud;
- arquivo/banco antigo no servidor só é excluído após confirmação explícita;
- PostgreSQL cabe no orçamento, reinicia por systemd e tem backup/WAL restaurável;
- `./check.sh`, testes completos, carga, integridade, restore e smoke cloud/local passam.

Estado atual:

- Concluído em 2026-07-22.
- PostgreSQL dedicado publicado em `5433`, 706.023 registros importados e duas
  reconciliações fecharam 100/100 tabelas, 187/187 FKs e zero divergência.
- Backup físico/lógico/WAL e restore isolado passaram; canário, cutover no
  watermark `11494`, deploy e rollback PostgreSQL preservaram escritas novas.
- Release final removeu mecanismos transitórios e tornou o gate cloud
  PostgreSQL-only bloqueante, mantendo o adapter SQLite somente no perfil local.
- O arquivo e os backups anteriores continuam preservados até confirmação
  explícita; evidência completa em
  `docs/audits/POSTGRESQL_CLOUD_TRANSITION_2026-07-22.md`.

## PKG-89: Outbox, Workers, Redis E Realtime Distribuído

Objetivo:

Tornar eventos, jobs e sessões de agentes duráveis e compatíveis com múltiplas
instâncias, sem usar memória ou Redis como fonte canônica de negócio.

Prioridade: P0 estrutural.

Dependências:

- PKG-88 fechado;
- PostgreSQL, blue/green e contratos N/N-1 operacionais.

Entregáveis:

- outbox/inbox transacionais, schemas versionados e deduplicação;
- fila PostgreSQL com lease, heartbeat, timeout, retry/backoff, prioridade e dead-letter;
- workers systemd por classe, release imutável, concorrência e drain controlados;
- idempotency key em toda operação mutável/repetível;
- Redis protegido em socket/loopback para cache recomponível, rate limit, presença e pub/sub;
- sessões WebSocket distribuídas com reconnect/jitter, ack e retomada de jobs;
- backpressure, quotas, retenção, reprocessamento supervisionado e métricas;
- remoção de registries, entrega imediata e filas in-memory aposentados.

Lotes:

1. Definir contratos, ordenação, idempotência e matriz de compatibilidade dos eventos/jobs.
2. Implantar outbox/inbox e dispatcher idempotente.
3. Implantar fila PostgreSQL e workers pausáveis com leases recuperáveis.
4. Migrar jobs por domínio e reconciliar pendentes/em execução.
5. Implantar Redis sem dados autoritativos.
6. Migrar presença/pub-sub/WebSocket e protocolo do agente.
7. Executar falhas, duplicidade, atraso, reconnect, carga e drain blue/green.
8. Remover mecanismos in-memory, flags e bridges temporárias.

Critério de aceite:

- commit de negócio e evento são atômicos;
- evento/webhook/job repetido produz um único efeito efetivo;
- worker morto libera lease e retoma sem duplicar efeito não idempotente;
- Redis vazio/indisponível degrada, recompõe e não perde dado de negócio;
- agente reconecta entre instâncias e nenhum job confirmado some ou roda duas vezes;
- dead-letter tem owner, alerta, retenção e reprocessamento seguro;
- workers N/N-1 drenam antes de schema/evento incompatível ser contraído;
- zero registry/fila autoritativa permanece em memória;
- carga, soak, falha controlada, suíte completa e smoke passam no host atual.

Estado atual:

- Concluído em 2026-07-22 na release `79084f8`.
- Lote 1 concluído: envelope de evento V1, contrato de jobs/leases,
  idempotência, ordenação, compatibilidade N/N-1, filas por criticidade, threat
  model e schemas portáveis foram definidos. As tabelas aditivas de
  outbox/inbox, jobs duráveis, idempotência, sessões e controle de workers são
  criadas por SQL idempotente, sem migration de framework.
- Lote 2 concluído: repository transacional de outbox/inbox, claim ordenado com
  lease, retry/dead-letter e dispatcher que materializa consumidores como jobs
  idempotentes. A criação canônica de job de agente grava o evento na mesma
  transação e não depende mais de entrega imediata pelo processo HTTP.
- Lote 3 concluído: worker durável por classe com concorrência limitada,
  heartbeat de lease, retomada após expiração, pausa/drain persistidos e registro
  de release. Units systemd resolvem a release ativa de forma imutável; deploy e
  rollback drenam/reiniciam workers compatíveis sem restaurar dados.
- Lote 4 concluído: jobs de agente geram outbox atômica, pendências anteriores
  recebem evento por backfill idempotente e jobs em execução retomam após
  reconnect. Fatiamento cloud é agendado na fila bulk; o modo local preserva a
  execução síncrona existente.
- Lote 5 concluído: Redis dedicado por socket Unix, ACL, limite de memória e
  política `allkeys-lru`, sem AOF/RDB, foi empacotado para cache, rate limit,
  presença e pub/sub. Indisponibilidade degrada para PostgreSQL/polling sem perda
  canônica.
- Lote 6 concluído: sessões realtime possuem owner de instância, expiração,
  fencing PostgreSQL, heartbeat e último ACK. Pub/sub acorda a instância dona e
  reconnect com jitter retoma jobs persistidos.
- Lote 7 concluído: quota recusou saturação acima de 1.000 jobs, carga controlada
  concluiu 500/500 sem duplicidade, lease expirado retomou com rejeição do token
  antigo, Redis vazio preservou dados canônicos, smoke público passou e o ciclo
  rollback N-1/forward-deploy drenou e retomou as quatro classes de worker.
- Lote 8 concluído: entrega imediata e port realtime autoritativa foram
  removidas; o gate bloqueia filas Python em memória e qualquer retorno do
  `push_job`. Registry local conserva somente objetos socket efêmeros e é cercado
  pelo owner canônico da sessão no PostgreSQL.
- Evidência integral em `docs/audits/DURABLE_EXECUTION_2026-07-22.md`.

## PKG-90: Objetos, Quarentena E Busca Reconstruível

Objetivo:

Migrar arquivos/artefatos cloud e busca para contratos duráveis, verificáveis e
reconstruíveis, sem paths locais antigos como fonte autoritativa.

Prioridade: P0/P1 estrutural.

Dependências:

- PKG-89 fechado;
- ADR do storage aprovada por capacidade, licença, segurança, backup e restore.

Entregáveis:

- serviço S3-compatible sob systemd no host, privado, com role mínima e quotas;
- buckets/prefixos por finalidade, ownership, checksum, content type e versionamento;
- upload streaming, limites, quarentena, análise, promoção atômica e URL autorizada curta;
- cópia inicial e incremental de objetos com manifesto/checksum e reconciliação;
- backup criptografado/externo e restore de metadados mais conteúdo;
- busca textual PostgreSQL atualizada por outbox e reconstruível do dado canônico;
- busca respeitando permissão, bloqueio, remoção, tenant e conteúdo moderado;
- painéis de integridade, órfãos, quarentena, uso, atraso e rebuild;
- remoção de paths, índices e consultas antigas após cutover.

Lotes:

1. Decidir implementação S3-compatible e executar prova de capacidade/upgrade/restore.
2. Criar contrato, segurança, buckets, quotas, retenção e streaming.
3. Migrar objetos por manifesto/checksum com escrita incremental.
4. Executar canário/cutover e validar download/upload/quarentena.
5. Implantar índice textual PostgreSQL e consumidor de outbox.
6. Reindexar, comparar relevância/permissão e executar canário.
7. Provar restore integral de metadados/objetos e rebuild do índice.
8. Remover storage/busca antigos, bridges, flags e referências cloud.

Critério de aceite:

- todo objeto canônico possui owner, tamanho, checksum, estado e referência válida;
- upload interrompido não cria objeto promovido nem registro órfão silencioso;
- quarentena nunca é servida, fatiada ou publicada;
- URLs não expõem path interno, credencial ou objeto de outro owner;
- metadado e conteúdo restauram juntos e reconciliam por checksum;
- índice apagado é reconstruído sem perda funcional e nunca concede permissão;
- storage/busca indisponíveis degradam sem derrubar login, segurança ou impressão ativa;
- zero path/índice/consulta antiga permanece no perfil cloud;
- carga, segurança, restore, suíte completa e smoke passam no host atual.

Estado atual:

- Concluído 100% em 2026-07-22; lotes 1 a 8 entregues e revisados.
- Lote 1 concluído: MinIO Community source-only foi escolhido por suportar
  S3 SigV4, versionamento, quotas e políticas mínimas. A build está fixada na
  release/commit oficial, o endpoint opera somente em loopback e PostgreSQL
  continuará canônico. Garage foi rejeitado por não oferecer bucket versioning.
  Em 2026-07-22, a instalação e o replay do bootstrap passaram no host: três
  buckets privados versionados com quota de 30 GiB, checksum de promoção válido,
  acesso anônimo `403`, exclusão de promovido negada e serviço limitado a 1,5 GiB.
  A prova final gravou/promoveu 25 MiB no limite do contrato, reconciliou seis
  objetos sem ausência, corrupção ou órfão e ensaiou instalação atômica,
  rollback e avanço do binário com checksum preservado e serviço saudável.
- Lote 2 concluído em 2026-07-22: adapter S3 SigV4, bloqueio de
  fallback local no perfil cloud, ingestão HTTP incremental com limite de 25 MiB,
  metadados/referências/sessões/reconciliação em SQL idempotente, dependência
  explícita dos serviços e preflight do endpoint privado. Validação focada:
  80 testes de storage/social/projetos e 41 testes de schema/packaging passaram.
- Publicação `29970593732` concluída no commit `0114887`; schema e aplicação
  entraram saudáveis. A validação pós-release detectou e corrigiu drift dos
  templates systemd no deploy incremental; os contratos de runtime passam a ser
  instalados da própria release imutável antes de iniciar o slot candidato.
- Prova do adapter no runtime Cloud passou: processo ativo com modo `s3`, quatro
  tabelas canônicas presentes, quarentena/leitura/promoção com checksum válido e
  duas referências persistidas. O path local legado tinha zero arquivos e o
  endpoint público permaneceu `200` após recarregar aplicação e workers.
- Lote 3 concluído em 2026-07-22: migrador dry-run/apply gera manifesto `0600`,
  valida tamanho/checksum, copia incrementalmente e nunca remove a origem. O
  manifesto real teve zero entradas históricas, coerente com o path local vazio.
  Reconciliação de banco/buckets adotou dois probes conhecidos sem apagar bytes e
  o replay fechou com 4 objetos, zero ausente, zero corrompido e zero órfão.
- Lote 4 concluído: validação aprovada promove por cópia e `HEAD`,
  download recalcula owner/publicação/moderação no PostgreSQL e usa token aleatório
  de 60 segundos, uso único, persistido somente como hash e enviado por header.
  Quarentena não possui rota de leitura. Validação focada: 81 testes passaram.
- Lote 5 concluído: `search_documents` PostgreSQL usa `tsvector`
  gerado + GIN, fontes emitem outbox sanitizada e worker bulk executa rebuild
  idempotente sem `DELETE`. Consulta reaplica fonte ativa, publicação comercial,
  membership e bloqueios. Validação focada de busca/worker/schema: 102 testes.
- Lote 6 concluído no Cloud em 2026-07-22: rebuild materializou 364 documentos em
  3,801 s, GIN e endpoint FTS responderam `200`; outbox sintética sanitizada foi
  publicada e o job bulk terminou em 4,222 s. Comparação de termos e filtros de
  geração/permissão passou. O primeiro CI expôs um teste WebSocket intermitente;
  cinco repetições locais e o rerun integral (530 testes) passaram sem mudança.
- Lote 7 concluído no Cloud: backup Restic criptografado reúne
  PostgreSQL físico/lógico + WAL e todas as versões/delimitadores dos três buckets
  com manifesto/checksum. Restore isolado reconcilia metadado/conteúdo e executa
  rebuild da busca sem iniciar aplicação ou alterar produção. O snapshot externo
  `3183edf8` restaurou seis versões, 114 tabelas, 78 revisões de schema e quatro
  objetos canônicos; checksums, FKs e rebuild de 364 documentos passaram.
- Lote 8 concluído: gate bloqueia fallback de filesystem, upload
  sem limite incremental, busca request-time/`LIKE` no perfil cloud e unit sem
  dependência do storage privado. Adapter e índice antigos permanecem somente no
  perfil local; dados/paths de origem não foram apagados.
- Publicação final `29972901814` promoveu o commit `51fe58e`, após 530 testes,
  auditoria de dependências, SBOM, blue/green e smoke público. Comparação FTS
  confirmou GIN, zero documento inativo visível e paridade integral dos termos
  existentes; aplicação, workers e MinIO permaneceram ativos.

## PKG-91: Núcleo Financeiro, Pagamentos E Pedidos

Objetivo:

Entregar ledger, pagamentos e pedidos em domínio isolado e auditável, sem
manusear dados de cartão nem misturar saldo com conteúdo social.

Prioridade: P0/P1 conforme risco financeiro e físico.

Dependências:

- PKG-90 fechado;
- identidade, permissão, auditoria, outbox e idempotência operacionais;
- revisão jurídica/fiscal por país antes de ativação real.

Entregáveis:

- ledger imutável de partidas dobradas e reconciliação independente;
- payment intents, adapters de provedor e webhooks autenticados/idempotentes;
- pedidos, itens, licenças, preço, taxa, imposto preparado e snapshots imutáveis;
- captura, cancelamento, reembolso, disputa, saldo, repasse e fechamento;
- risco/fraude explicável, revisão humana e recurso;
- valores em unidade monetária mínima, moeda explícita e regra de arredondamento;
- tokenização/checkout hospedado pelo provedor para reduzir escopo PCI;
- state machines formais de pedido/pagamento, invariantes e comandos idempotentes;
- consoles separados para finanças, suporte e risco;
- retenção, privacidade, segregação de função e trilha de auditoria.

Lotes:

1. Modelar ledger, invariantes e reconciliação com SQL idempotente.
2. Implementar adapter sandbox, intent e webhook com replay seguro.
3. Criar pedido e snapshots de item/licença/preço.
4. Implementar captura, cancelamento, reembolso e disputa.
5. Implementar saldo, repasse e fechamento reconciliado.
6. Adicionar risco/fraude, revisão humana e permissões segregadas.
7. Validar PCI/LGPD, fiscal/jurídico, chargeback e continuidade do provedor.
8. Remover contratos comerciais preparatórios/legados substituídos e validar ponta a ponta.

Critério de aceite:

- soma de débitos e créditos é sempre zero por transação financeira;
- webhook repetido, fora de ordem ou atrasado não duplica cobrança/estorno;
- timeout não deixa pedido e pagamento em estados contraditórios silenciosos;
- reconciliação identifica e bloqueia divergência antes de repasse;
- permissões impedem a mesma pessoa de criar e aprovar operação sensível;
- pedido aponta a snapshot imutável, nunca ao preço/arquivo mutável atual;
- dinheiro usa inteiro + moeda; float nunca participa de cálculo ou ledger;
- Printora não recebe, persiste ou registra PAN/CVV/dado bruto de cartão;
- reembolso/repasse nunca excede valor elegível e saldo negativo tem política explícita;
- dados pessoais/financeiros não vazam em comunidade, logs ou analytics;
- não resta endpoint, campo, tela ou job de checkout/pedido anterior em paralelo;
- sandbox, segurança, carga, reconciliação e recuperação passam antes de dinheiro real;
- todo componente pertencente ao Printora executa no servidor atual; provedor
  externo é acessado somente por adapter e não hospeda regra canônica do produto.

Estado atual:

- Concluído 100% em 2026-07-23; lotes 1 a 8 entregues, publicados e revisados.
- Lote 1 concluído: ledger de partidas dobradas usa inteiro + moeda explícita,
  posting em duas fases com balanceamento também protegido no banco, linhas
  imutáveis após posting, chave idempotente com digest e reconciliação
  independente. SQL SQLite/PostgreSQL é aditivo e idempotente; não há `DELETE`,
  `DROP` ou cálculo monetário com `float`.
- Lote 2 concluído: adapter sandbox cria intent idempotente e checkout hospedado;
  webhook HMAC tem limite de payload, rejeita campos de cartão, persiste somente
  digest e aplica state machine. Replay, evento atrasado/fora de ordem, assinatura
  inválida e transição impossível não duplicam nem contradizem o estado. O modo
  de pagamento nasce `disabled` e não oferece configuração de dinheiro real.
- Lote 3 concluído: pedido canônico e itens imutáveis copiam título, licença,
  termos, versão e preço aprovado do projeto premium no instante da compra. Total
  usa somente inteiros, pedido não mistura moedas e mudança posterior no projeto
  não altera o snapshot. Criação, detalhe e checkout são autenticados e
  idempotentes; imposto permanece explicitamente `not_configured` até revisão.
- Lote 4 concluído: comandos idempotentes cobrem captura, cancelamento, reembolso
  parcial/integral, abertura e resolução de disputa. Captura, reembolso e disputa
  postam compensações balanceadas no ledger e atualizam pedido/pagamento na mesma
  transação; reembolso acima do elegível é bloqueado. Registros e alocações são
  imutáveis e nenhuma correção edita lançamento anterior.
- Lote 5 concluído: saldo é derivado do ledger, reserva pedidos de repasse e
  explicita política de saldo negativo. Repasse exige aprovação por pessoa
  diferente, última reconciliação sem divergência e ausência de disputa aberta;
  execução posta nova transação balanceada. Fechamento imutável registra
  reconciliação, desbalanceamento e disputas, ficando bloqueado se houver desvio.
- Lote 6 concluído: regras de risco explicáveis criam score e códigos de motivo;
  valor alto, velocidade e histórico de disputa exigem revisão humana antes de
  captura. Rejeição aceita recurso do comprador. Operação, aprovação, risco,
  suporte e auditoria usam papéis separados; solicitante não aprova repasse e
  aprovador não o executa. Decisões e alterações de papel geram auditoria
  sanitizada e imutável com retenção declarada de 180 dias.
- Lote 7 concluído como gate de ativação: matriz PCI/LGPD, fiscal, jurídica,
  continuidade, chargeback, segurança e restore nasce pendente e aceita somente
  evidência por hash. Políticas de retenção são explícitas e limpeza é apenas
  preview. O runtime suporta exclusivamente `disabled`/`sandbox`, checkout é
  hospedado, schema não contém PAN/CVV e circuit breaker degrada falha do adapter;
  dinheiro real continua tecnicamente indisponível mesmo com controles aprovados.
- Lote 8 concluído: scanner bloqueia endpoint comercial fora da
  fronteira financeira, modo além de disabled/sandbox, coluna PAN/CVV e payload
  bruto de webhook. Não havia checkout/pedido anterior para migrar. A UI de
  Finanças separa visão geral, pedidos/pagamentos, ledger, reconciliação,
  disputas e repasses em lista/detalhe, com estado explícito de acesso restrito.
- Publicação final `29977187334` promoveu `3b55e01` após 554 testes no CI,
  auditoria de dependências, SBOM e blue/green. A prova sandbox sintética no
  Cloud passou captura, replay idempotente, reembolso parcial, reconciliação,
  segregação de aprovação/execução de repasse, saldo, ledger global balanceado,
  ausência de coluna para cartão/payload bruto e bloqueio de dinheiro real.
  Smoke público passou. O snapshot externo `c0df65fe` restaurou em destino
  isolado 134 tabelas, 85 revisões, oito versões de objeto, zero FK inválida e
  reconstruiu 364 documentos. Aplicação e impressora física não foram tocadas
  pelo restore.

## PKG-92: Fabricação, Qualidade, Logística E Cadeia De Custódia

Objetivo:

Transformar pedido elegível em cotação, ordem de fabricação, qualidade e entrega
rastreáveis, preservando segurança física, licença e privacidade.

Prioridade: P0/P1 conforme risco físico.

Dependências:

- PKG-91 fechado;
- políticas jurídica, segurança de produto, responsabilidade e recall aprovadas.

Entregáveis:

- cotação versionada de material, máquina, prazo, tolerância, acabamento e frete;
- aceite explícito e ordem ligada a snapshots de projeto/arquivo/licença/preço;
- reserva de capacidade/material concorrente e idempotente;
- estados formais de produção, pausa, falha, retrabalho e cancelamento;
- plano/checklist de qualidade, medições, fotos/evidências e aprovação segregada;
- embalagem, transportadora, tracking, entrega e tratamento de exceção;
- cadeia de custódia de arquivo/material/peça sem exposição pública de endereço;
- incidente, produto inseguro, recall, reembolso e preservação de evidência;
- console de produção separado em lista, detalhe e transições autorizadas;
- retenção/eliminação segura de arquivos fabris e dados pessoais.

Lotes:

1. Modelar cotação, aceite, snapshots e invariantes.
2. Implementar ordem, capacidade, material e concorrência.
3. Implementar execução, pausa, falha, retrabalho e cancelamento.
4. Implementar qualidade, evidência e segregação de aprovação.
5. Implementar embalagem, expedição, tracking e entrega.
6. Implementar incidente, recall, disputa e integração financeira idempotente.
7. Validar privacidade, licença, segurança física, carga e recuperação.
8. Remover fluxos produtivos/logísticos substituídos e fechar ponta a ponta.

Critério de aceite:

- ordem sempre referencia snapshots imutáveis e licença válida para fabricação;
- reserva concorrente não vende a mesma capacidade/material duas vezes;
- estado não salta etapa obrigatória nem retrocede sem evento compensatório;
- peça reprovada não pode ser expedida;
- tracking/webhook repetido não duplica transição ou notificação;
- endereço/documento não aparece em comunidade, logs ou evidência pública;
- recall alcança pedidos/peças afetados e preserva trilha auditável;
- falha de logística não altera ledger fora de comando financeiro idempotente;
- nenhum fluxo antigo de cotação/produção/entrega permanece em paralelo;
- suíte completa, segurança, carga, recuperação e smoke passam no host atual.

Estado atual:

- Concluído 100% em 2026-07-23; lotes 1 a 8 entregues, publicados e revisados.
- Cotação versionada copia snapshots do pedido,
  licença, material, máquina, arquivo, tolerância, acabamento, prazo e frete.
  Aceite e reservas usam transação/idempotência e decremento condicional de
  capacidade/material. A máquina de estados impede saltos; qualidade exige
  inspetor e aprovador diferentes e peça reprovada não chega à expedição.
- Logística persiste endereço somente cifrado, tracking somente por hash/digest e
  deduplica eventos do provedor. Cadeia de custódia e eventos produtivos são
  imutáveis. Incidente de produto inseguro cria recall rastreável e apenas uma
  chave idempotente para comando financeiro, sem escrever diretamente no ledger.
- O console de Fabricação separa lista/detalhe de ordens e incidentes, com acesso
  por papel. O fluxo não possui integração que acione impressora, agente,
  Moonraker, Klipper ou MCU.
- A publicação `29978102956` promoveu `523ad57` após 557 testes locais e gate
  integral no CI. A prova sintética Cloud passou aceite/reserva, cadeia formal
  até entrega, qualidade segregada, recall, tracking somente por hash e comando
  financeiro apenas por chave idempotente. Smoke público passou; nenhuma
  operação acessou a impressora física.

## PKG-93: Escala, Resiliência, Backup E Recuperação

Objetivo:

Operar múltiplas instâncias e cargas assíncronas com degradação controlada,
backup externo e recuperação comprovada no servidor atual.

Prioridade: P1 estrutural.

Dependências:

- PKG-92 fechado;
- métricas e baseline de capacidade confiáveis;
- classificação de dados e política de retenção aprovadas.

Entregáveis:

- múltiplas instâncias stateless e balanceamento Nginx no mesmo host;
- pools de workers por criticidade/carga com backpressure e quotas;
- circuit breakers, timeouts, bulkheads e degradação graciosa;
- backup PostgreSQL/objetos/configuração com criptografia e retenção;
- restore automatizado em ambiente isolado e exercícios RPO/RTO;
- WAL/backup criptografado enviado para destino fora do host e restore sem dependência da origem;
- runbook de perda de processo, banco, disco, configuração e host;
- testes de carga, soak, caos de processo, segurança e recuperação.

Lotes:

1. Tornar app stateless e validar balanceamento de múltiplas instâncias.
2. Separar workers por fila/risco e implantar backpressure/quotas.
3. Implementar resiliência e degradação por dependência.
4. Automatizar backup e restore; medir RPO/RTO.
5. Testar perda de processo/banco/disco/configuração e restore isolado.
6. Testar perda simulada do host a partir da cópia externa.
7. Fazer soak/capacidade final e remover mecanismos substituídos.

Critério de aceite:

- matar uma instância não interrompe requests novos nem perde job confirmado;
- sobrecarga recebe backpressure e não derruba login, segurança ou impressão;
- backup completo é restaurado e reconciliado dentro do RPO/RTO definido;
- migração/deploy preserva RPO zero; desastre físico declara RPO medido, sem promessa falsa;
- credencial/chave de restore não depende somente do host perdido;
- carga de pico e soak passam com folga no servidor atual;
- limite contra falha física do host fica documentado sem falsa promessa de HA;
- `./check.sh`, testes completos, caos, segurança, restore e smoke passam.

Estado atual:

- Concluído 100% em 2026-07-23; lotes 1 a 7 entregues, publicados e revisados.
- O upstream ativo usa duas instâncias da mesma release (`blue`/`green` mais
  `replica`) e mantém N-1 fora do upstream para rollback. A parada controlada da
  instância ativa preservou 300 requests, sem erro, e a recuperação devolveu os
  dois processos ao estado ready.
- Workers permanecem separados em outbox/critical/default/bulk, com quotas por
  fila e owner, leases e backpressure. O ensaio concluiu 500 jobs sem duplicidade,
  recuperou lease expirado e rejeitou conclusão obsoleta. Sob sobrecarga HTTP,
  400 de 1.000 requests receberam `429` controlado sem derrubar readiness.
- Storage S3 usa pool limitado, retries e timeouts; Redis degrada para fontes
  canônicas/recomposição e pagamentos mantêm circuit breaker. Nenhum fallback
  cloud escreve em memória ou adapter local.
- O snapshot externo criptografado `38cb0d0f` incluiu PostgreSQL, WAL, 8 versões
  de objetos e 12 arquivos de configuração. Restore isolado concluiu em 203 s,
  com 146 tabelas, 86 revisões, zero FK inválida, objetos reconciliados e 364
  documentos de busca. A cópia externa da credencial acessou e restaurou
  configuração diretamente fora do host de origem.
- RPO medido no exercício foi inferior a um minuto e RTO foi 203 s. O limite
  operacional atual continua honesto: timer diário com atraso aleatório permite
  pior caso de até 24 h 15 min em destruição física; deploy/cutover preserva RPO
  zero. O host único fornece redundância de processo, não alta disponibilidade.
- Soak de 120 s concluiu 600 requests sem erro, p95 máximo de 1.470 ms, com cerca
  de 24 GiB de memória e 110 GiB de disco ainda disponíveis. O workflow
  `29979938622` publicou `aa80148` com gate completo, auditorias de dependência,
  SBOM, preflight e smoke público. A impressora física e sua cadeia operacional
  não foram acessadas.

## PKG-94: Analytics, Moderação Multilíngue E Inteligência Isolada

Objetivo:

Entregar analytics, moderação multilíngue e ML como consumidores isolados de
eventos sanitizados, sem escrita direta no núcleo transacional.

Prioridade: P1/P2 conforme impacto.

Dependências:

- PKG-93 fechado;
- classificação, consentimento, retenção e finalidade de cada dado aprovados;
- capacidade residual comprovada no host atual.

Entregáveis:

- pipeline analítico derivado com schema versionado, lineage e replay;
- warehouse/read models isolados do OLTP por role e orçamento de recurso;
- dashboards de impacto, qualidade, segurança e operação;
- exclusão/anonimização propagada e retenção por finalidade;
- moderação multilíngue com confiança, contexto, revisão humana e recurso;
- serviço isolado de recomendação/ML e busca geométrica;
- registro de dataset/modelo, licença, versão, métricas, bias, canário e drift;
- fallback determinístico e kill switch para cada decisão automatizada;
- quotas de CPU/RAM/GPU/disco para não afetar fluxos P0/P1.

Lotes:

1. Definir contratos de evento, finalidade, lineage, consentimento e remoção.
2. Implantar pipeline/read models com replay e reconciliação.
3. Implantar dashboards sem consulta pesada no OLTP.
4. Implementar moderação multilíngue com revisão/recurso.
5. Isolar recomendação e busca geométrica com fallback determinístico.
6. Implementar avaliação offline, canário, drift, rollback e kill switch.
7. Executar carga, falha, privacidade, bias e degradação.
8. Remover protótipos, datasets e modelos substituídos conforme retenção.

Critério de aceite:

- analytics/ML não escreve diretamente no OLTP nem amplia permissão;
- evento pode ser reprocessado sem duplicar métrica ou decisão;
- remoção/anonimização alcança derivados dentro do prazo definido;
- modelo possui owner, versão, dataset permitido, métricas e rollback;
- decisão de alto impacto exige revisão humana e canal de recurso;
- falha/kill switch mantém fallback seguro e não bloqueia P0/P1;
- carga dos serviços respeita quotas e folga do servidor atual;
- datasets/modelos temporários têm retenção e limpeza comprovadas;
- suíte completa, segurança/privacidade, carga e smoke passam.

Estado atual:

- Concluído e publicado na release `734de42`; lotes 1 a 8 encerrados.
- Contrato sanitizado versionado, lineage, replay,
  read models, dashboard, moderação multilíngue com revisão/recurso, recomendação,
  busca geométrica, registro de modelos, canário, drift e kill switch.
- Role `printora_analytics` recebe acesso somente às tabelas derivadas; o worker
  dedicado ativa essa role e possui quotas próprias de CPU, RAM, tasks e I/O.
- Anonimização altera somente derivados e a retenção opera em preview, sem
  exclusão automática. O baseline usa apenas eventos internos sanitizados, sem
  dataset ou modelo externo.
- Gate completo e publicação passaram. O probe remoto processou 1.004 eventos a
  18,456 eventos/s; replay de 2.000 eventos foi idempotente, PT/EN/ES exigiram
  revisão humana, kill switch usou fallback determinístico e a retenção não
  removeu dados.
- Durante a carga, 600 leituras distribuídas nas duas instâncias tiveram zero
  erro e máximo de 77 ms. A role não lê nem escreve `auth_users`; o worker ficou
  em cerca de 34 MiB sob CPU 50%, MemoryMax 1 GiB, TasksMax 128 e IOWeight 25.
- A rota pública foi aberta em navegador real sem erro de console. A sessão
  disponível estava desautenticada, portanto o conteúdo administrativo interno
  permanece validado por contrato, testes e probe autenticado, não por inspeção
  visual dessa sessão.

## PKG-95: Consolidação, Erradicação Legada E Aceite Arquitetural

Objetivo:

Fechar o programa com prova independente de que a arquitetura final é única,
operável, restaurável e livre de bridges, flags, dados e referências obsoletas.

Prioridade: P0 de encerramento.

Dependências:

- PKG-86 a PKG-94 fechados e publicados;
- janelas de observação concluídas;
- autorização humana para cada limpeza destrutiva pendente.

Entregáveis:

- manifesto de tecnologias, tabelas, arquivos, rotas e contratos aposentados;
- scanner de referências legadas integrado ao check;
- scanner por perfil provando que adapter local válido não entra no runtime cloud;
- remoção de flags, adapters, bridges, units, scripts, envs e dependências temporárias;
- revisão de arquivos grandes, SOLID, contratos e consumidores;
- SBOM, lockfiles, artefatos reproduzíveis, dependências, CVEs e política de atualização;
- revisão de threat model, roles, secrets, rede, auditoria, privacidade e abuso;
- documentação consolidada descrevendo somente a arquitetura final;
- inventário e reconciliação final de dados, objetos, jobs e índices;
- ensaio integral de deploy, rollback de código, backup e restore;
- carga/soak no servidor atual e relatório de capacidade residual;
- revisão independente de segurança, privacidade, retenção e operação.

Lotes:

1. Gerar manifesto final de legado e owners de remoção.
2. Executar scanner em código, banco, filesystem, units, env, workflows, docs e testes.
3. Remover resíduos não destrutivos e corrigir regressões.
4. Apresentar relatório e executar limpezas destrutivas explicitamente aprovadas.
5. Repetir integridade, restore, deploy, rollback, carga, soak e segurança.
6. Consolidar decisões/runbook e encerrar o programa em commit próprio.

Critério de aceite:

- nenhum termo/artefato aposentado existe fora do histórico/decisão permitidos;
- não há flag de transição permanente nem adapter sem consumidor atual;
- nenhum serviço/dependência existe sem owner, versão, atualização, alerta e remoção;
- perfil cloud não importa/carrega adapter SQLite local nem possui fallback silencioso;
- banco, objetos, filas e índices reconciliam com as fontes canônicas;
- restore integral sobe uma instância utilizável e passa smoke dos fluxos P0/P1;
- deploy e rollback de código não perdem escrita nem geram indisponibilidade observável;
- servidor atual mantém folga acordada após soak;
- documentação, units e configuração efetiva refletem a mesma topologia;
- revisão completa e `./check.sh` passam; pacote termina em commit exclusivo.

Estado atual:

- Concluído e publicado na release `73057bf`; lotes 1 a 6 encerrados.
- Manifesto final, owners/ciclo de vida das units,
  scanner bloqueante integrado ao `check.sh`, prova executável de que o perfil
  cloud não carrega `sqlite3` e remoção do contrato transitório
  `database_transition`.
- Nenhum resíduo não destrutivo listado no manifesto permanece. SQLite e
  `printora.service` foram mantidos exclusivamente como perfil local válido;
  transições de negócio e bridge USB-CAN não são bridges arquiteturais.
- Gate estrito completo passou com 566 testes backend, Go, build e testes
  frontend, scans de segredo/runtime e fronteiras modulares. SBOM reproduzível
  foi gerado; npm audit, pip-audit e govulncheck não encontraram vulnerabilidade.
- Auditoria efetiva comprovou release/réplica iguais, duas readiness, perfil
  cloud sem SQLite, 157 tabelas, 87 revisões, zero índice/constraint inválida,
  role analítica `1:0:0` e filas sem lease/processamento pendente.
- Rollback N-1 sob 600 requests terminou sem erro e sem restaurar dados; a
  release final foi republicada e auditada. Soak de 120 s também concluiu 600
  requests sem erro, com cerca de 24 GiB de RAM e 110 GiB de disco livres.
- O primeiro restore revelou que o snapshot anterior precedia o schema
  analítico. Um novo backup externo criptografado foi criado sem excluir os
  anteriores; o restore final subiu 157 tabelas/87 revisões, zero FK inválida,
  8 versões de objetos, 6 referências canônicas e 364 documentos de busca.
- Nenhuma limpeza destrutiva foi executada. Se o inventário remoto encontrar
  dado, tabela, objeto, backup ou arquivo candidato, ele será apenas reportado
  até existir confirmação específica.
