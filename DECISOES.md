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

### DEC-20260614-01 - Social usa catálogo canônico e não permissões operacionais

Status: aceita
Data: 2026-06-14
Contexto: os pacotes PKG-49 a PKG-53 introduzem perfil público, impressoras públicas, comunidades automáticas e grafo social. Esses recursos precisam usar inventário real e modelo canônico sem vazar endpoints, agentes, credenciais ou permissões de operação.
Decisao: criar o domínio `social_catalog` com SQL idempotente próprio. O catálogo mestre versiona fabricante, modelo, variante e componentes. Impressoras públicas exigem `catalog_variant_id`; comunidades são derivadas automaticamente do catálogo e da publicação consentida da impressora; relações sociais ficam isoladas em `social_relationships` e não alteram organizações, ownership ou acesso operacional.
Alternativas consideradas: usar texto livre `cloud_model`; transformar comunidade em organização operacional; misturar perfil público nos campos de conta; criar comunidades manuais antes do catálogo.
Consequencias: recursos sociais ficam consistentes e auditáveis, com menor risco de vazamento operacional. A primeira UI é enxuta e pode evoluir para curadoria avançada sem mudar o contrato base.
Impacto em testes: testes focados cobrem seed do catálogo, privacidade do perfil, vínculo obrigatório de impressora pública, sincronização de comunidade e bloqueio social.
Impacto em rollback: médio; o schema adiciona tabelas sociais e colunas públicas em `printers`. O inicializador cria backup do SQLite antes de aplicar script pendente.
Como reverter: restaurar backup do SQLite anterior ao `035_social_catalog.sql`, remover `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, tela `Social`, serviço `socialApi` e a inclusão da rota no `main.py`.
Referencias: `backend/sql/035_social_catalog.sql`, `backend/app/social_catalog.py`, `frontend/src/screens/SocialScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260615-01 - Curadoria do catálogo mestre fica em superfície administrativa própria

Status: aceita
Data: 2026-06-15
Contexto: o catálogo mestre precisa sustentar comunidades, publicação de impressoras, biblioteca de modelos e fatiamento seguro. Misturar curadoria canônica na tela Social deixaria regras administrativas pouco auditáveis e permitiria confundir identidade pública com administração de dados técnicos.
Decisao: manter o domínio `social_catalog`, mas separar a superfície de curadoria na seção `Catálogo`. A API administrativa expõe busca filtrável agrupada por fabricante/modelo, com variações técnicas dentro do detalhe do modelo, e atualização de variações. O contrato administrativo inclui metadados enriquecidos de fabricante/modelo: logo, resumo, site, repositório, documentação, BOM, Discord, Reddit, imagem e notas de curadoria quando confirmados. A UI não exibe campo de origem técnica nem identificador interno de pacote. Os estados válidos são `official`, `community`, `draft`, `obsolete` e `blocked`; `community` exige revisão de fonte antes de virar `official`; `draft` é usado quando volume/componentes ainda têm incerteza; `obsolete` preserva vínculos existentes e bloqueia nova publicação; `blocked` remove o item da consulta pública e fica oculto da curadoria padrão, mas continua acessível por filtro para auditoria/rollback. Merge/rename deve criar nova entrada ou atualizar metadados sem apagar a variante antiga enquanto houver impressora vinculada.
Alternativas consideradas: manter tudo na tela Social; aceitar edição por usuários comuns; apagar variantes bloqueadas; alterar `035_social_catalog.sql` já versionado.
Consequencias: a curadoria fica auditável e reversível, usuário comum não edita catálogo canônico e dados incertos entram como `community`/`draft` sem promessa técnica falsa. O detalhe administrativo expõe `detail_json` e `source_links_json` por modelo para registrar ficha técnica e fontes usadas sem misturar isso com campos internos. Logos só são exibidos quando vierem de fonte oficial, GitHub org/usuário confiável ou imagem confirmada; caso contrário a UI usa monograma.
Impacto em testes: testes cobrem seed amplo DIY, metadados enriquecidos, ficha/fonte de curadoria, política de logo confiável, contrato agrupado por modelo, filtros administrativos, ausência de identificador interno de pacote nas fontes, permissão 403 para usuário comum, duplicidade, obsolescência/bloqueio e vínculo de impressora com variante canônica.
Impacto em rollback: médio; seeds `036_expand_printer_catalog_seed.sql`/`037_expand_diy_catalog_breadth.sql`, metadados `038_catalog_manufacturer_model_metadata.sql`, bloqueio `039_catalog_block_toolchanger_entries.sql`, complemento `040_catalog_add_voron_phoenix_draft.sql`, sanitização `041_catalog_sanitize_internal_sources.sql`, enriquecimentos `042_catalog_enriched_metadata.sql`/`043_catalog_deeper_model_detail.sql` e tela `CatalogAdminScreen` podem ser revertidos sem apagar dados de impressoras existentes.
Como reverter: reverter scripts SQL 036 a 043, endpoints administrativos novos, `frontend/src/screens/CatalogAdminScreen.tsx`, estilos/rota `catalog` e restaurar docs; em banco já aplicado, manter linhas como legado auditável ou restaurar backup SQLite anterior ao script 036.
Referencias: `backend/sql/036_expand_printer_catalog_seed.sql`, `backend/sql/037_expand_diy_catalog_breadth.sql`, `backend/sql/038_catalog_manufacturer_model_metadata.sql`, `backend/sql/039_catalog_block_toolchanger_entries.sql`, `backend/sql/040_catalog_add_voron_phoenix_draft.sql`, `backend/sql/041_catalog_sanitize_internal_sources.sql`, `backend/sql/042_catalog_enriched_metadata.sql`, `backend/sql/043_catalog_deeper_model_detail.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/CatalogAdminScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260530-01 - Setup do Zero começa após Linux e SSH ativo

Status: aceita
Data: 2026-05-30
Contexto: o Printora precisa ajudar no provisionamento de uma Raspberry/BTT Pi para impressoras Klipper, mas uma placa realmente virgem nao possui sistema operacional, rede ou serviço SSH. Prometer instalacao completa via SSH nesse estado seria tecnicamente incorreto.
Decisao: o fluxo `Setup do Zero` fica dividido em fase de preparo de mídia/boot, tratada como etapa manual ou futura, e fase SSH. O PKG-34 implementa apenas a fase SSH com preflight read-only, plano dry-run e historico sem segredos. Instalacao real, CAN, build remoto, flash e validacao final ficam em pacotes posteriores.
Alternativas consideradas: tentar instalar SO via SSH; incluir gravacao de SD/eMMC no mesmo pacote; criar um botao unico que executa KIAUH/instaladores direto.
Consequencias: o produto evita uma promessa impossivel para placa sem OS e cria uma base segura para automatizar instalacao em etapas futuras.
Impacto em testes: testes cobrem boundary de placa virgem, parser read-only, plano dry-run e ausencia de persistencia de `key_path`.
Impacto em rollback: baixo; remover a secao `setup` e as rotas `/api/setup/ssh/*` volta o produto ao estado anterior.
Como reverter: remover tela `SetupScreen`, hook/service/tipos de setup, rota `setup`, modulo `setup_wizard` e script SQL `021_setup_ssh_runs.sql`.
Referencias: `DEMANDAS.md`, `TESTES.md`, `TELAS.md`, `RUNBOOK.md`, `backend/app/setup_wizard.py`, `frontend/src/screens/SetupScreen.tsx`.

### DEC-20260530-02 - Setup CAN remoto exige modo operacional e confirmação

Status: aceita
Data: 2026-05-30
Contexto: configurar `can0` em uma Raspberry/BTT Pi altera rede e systemd, podendo derrubar comunicação com MCUs CAN se executado no momento errado. O fluxo precisa ser útil para setup do zero sem virar ação perigosa por clique acidental.
Decisao: o PKG-35 implementa diagnóstico read-only e plano dry-run por padrão. O apply real só executa com confirmação textual `CONFIGURAR CAN0`, variável de ambiente `PRINTORA_CAN_SETUP_MODE=remote`, preflight aprovado, sem impressão em andamento detectada e `sudo -n` disponível. Antes de escrever `/etc/systemd/system/can0.service`, o fluxo cria backup remoto em `~/.local/share/printora/can-setup/backups/<timestamp>/`.
Alternativas consideradas: manter CAN apenas como plano sem apply; executar apply sempre que o usuário clicar; editar arquivos de rede tradicionais como `/etc/network/interfaces` diretamente.
Consequencias: o produto entrega automação real controlada, mas continua bloqueado por padrão em ambientes comuns. O serviço systemd isolado reduz acoplamento com distribuições diferentes.
Impacto em testes: testes cobrem parsing de CAN/U2C/UUID, bloqueio por impressão, comandos `PLAN`, confirmação explícita e histórico sem `key_path`.
Impacto em rollback: médio; o rollback depende de restaurar o backup do serviço ou remover/desabilitar `can0.service` criado pelo Printora.
Como reverter: remover endpoints `/api/setup/can/*`, modulo `setup_can`, tela CAN em `SetupScreen`, SQL `022_setup_can_runs.sql` e documentação do PKG-35.
Referencias: `backend/app/setup_can.py`, `backend/sql/022_setup_can_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`.

### DEC-20260530-03 - Build remoto de firmware nunca faz flash

Status: aceita
Data: 2026-05-30
Contexto: depois de preparar SSH e CAN, o Printora precisa compilar firmware para placas reais no host da impressora. Misturar build e flash no mesmo passo aumentaria o risco de deixar MCU offline sem validação de artefatos.
Decisao: o PKG-36 implementa seleção de hardware real, geração remota de `.config`, build remoto e captura de artefatos/UUIDs, mas flash permanece fora do pacote. O build real exige `BUILD_FIRMWARE_NO_FLASH`, `PRINTORA_REMOTE_FIRMWARE_BUILD_MODE=remote`, variante física confirmada e restauração automática da `.config` por `trap`.
Alternativas consideradas: manter build apenas local; executar flash logo após build; editar `printer.cfg` automaticamente com UUID capturado.
Consequencias: o usuário ganha artefato rastreável e UUID sugerido sem mutação crítica de MCU ou config da impressora. O próximo pacote pode tratar flash com checklist próprio.
Impacto em testes: testes cobrem bloqueio sem variante confirmada, plano com comandos `PLAN`, ausência de comando de flash, confirmação textual e histórico sem `key_path`.
Impacto em rollback: médio; rollback do build é restaurar `.config.before-build` e apagar artefatos do build remoto.
Como reverter: remover endpoints `/api/setup/firmware/*`, modulo `setup_firmware`, SQL `023_setup_firmware_runs.sql`, UI Firmware remoto em `SetupScreen` e documentação do PKG-36.
Referencias: `backend/app/setup_firmware.py`, `backend/sql/023_setup_firmware_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`.

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

### DEC-20260526-01 - Updates criticos da impressora exigem revisao e rollback visivel

Status: aceita
Data: 2026-05-26
Contexto: update de Klipper junto de plugin de toolchanger pode quebrar compatibilidade de API interna e impedir o Klipper de iniciar, sem aviso suficiente no Mainsail ou no proprio Update Manager.
Decisao: o Printora classifica `klipper` e componentes de toolchanger como risco alto quando ha update pendente, exige confirmacao literal antes de executar pelo backend/UI e exibe rollback por componente quando o Moonraker informa `rollback_version`.
Alternativas consideradas: deixar o fluxo igual ao Mainsail; apenas mostrar um aviso visual sem bloqueio backend; bloquear todos os updates globais.
Consequencias: update critico deixa de ser um clique acidental, mas continua disponivel para usuario tecnico que assumir o risco. Rollback fica operacional na mesma tela quando suportado pelo Moonraker.
Impacto em testes: adicionar testes de classificacao de risco, selecao de componentes de risco em `all` e exposicao de rollback.
Impacto em rollback: baixo; remover o guard e os campos novos restaura o comportamento anterior.
Como reverter: retirar a confirmacao de risco em `backend/app/routes/printer_updates.py`, remover metadados de risco em `backend/app/updates.py` e ocultar botoes/avisos da tela Atualizacoes.
Referencias: `backend/app/updates.py`, `backend/app/routes/printer_updates.py`, `frontend/src/screens/UpdatesScreen.tsx`.

### DEC-20260526-02 - Silencio de update vale por versao concreta do componente

Status: aceita
Data: 2026-05-26
Contexto: uma versao especifica de Klipper, plugin ou outro componente do Update Manager pode estar disponivel, mas ser indesejada no momento por quebrar o ambiente ou exigir rollback manual. O alerta recorrente passa a poluir Home, topbar, Central de alertas, Health, Checklist e Auditoria mesmo quando o usuario decidiu aguardar a proxima versao.
Decisao: permitir silenciar qualquer componente por impressora e por identidade concreta da leitura atual (`component_name` + versoes + atraso/pacotes + warnings/anomalias). Silenciar remove o item dos alertas e contadores ativos, mas mantem o card e as acoes `Reanalisar`, `Atualizar`, `Rollback` e `Reativar alerta`.
Alternativas consideradas: silenciar componente para sempre; esconder o card; transformar silencio em autorizacao de update; manter alerta sempre ativo.
Consequencias: reduz ruido operacional sem esconder a capacidade de atualizar manualmente. Quando a leitura do Update Manager muda, o silencio deixa de combinar e o alerta volta automaticamente.
Impacto em testes: cobrir persistencia SQLite, expiracao por nova versao, agregadores de Health/Checklist/Auditoria e UI da tela Atualizacoes.
Impacto em rollback: baixo; remover a tabela `update_alert_silences`, os endpoints de silencio e os filtros de agregacao restaura o comportamento anterior.
Como reverter: remover `backend/sql/019_update_alert_silences.sql`, `UpdateAlertSilenceRepository`, endpoints `/updates/silences`, filtros `printora_alert_silenced` e controles da tela Atualizacoes.
Referencias: `backend/app/updates.py`, `backend/app/routes/printer_updates.py`, `backend/app/health.py`, `backend/app/checklists.py`, `backend/app/audit.py`, `frontend/src/screens/UpdatesScreen.tsx`.

### DEC-20260526-03 - Feedback operacional usa modal e toast proprios

Status: aceita
Data: 2026-05-26
Contexto: dialogos nativos do navegador quebram a identidade visual do Printora e deixam confirmacoes operacionais importantes fora do padrao da aplicacao.
Decisao: confirmacoes de decisao devem usar modal proprio do shell React; feedback temporario de sucesso/falha deve usar toast. Erros persistentes e diagnosticos continuam inline ou na Central de alertas quando exigem acao ou leitura posterior.
Alternativas consideradas: continuar com `window.confirm`; trocar tudo por toast; usar modal para qualquer mensagem temporaria.
Consequencias: melhora consistencia visual sem esconder falhas que precisam ficar persistentes na tela.
Impacto em testes: validar build frontend e contrato de tela sem `window.confirm` no fluxo de silencio de versao.
Impacto em rollback: baixo; remover `ConfirmDialogModal`, `ToastViewport` e voltar chamadas para feedback inline/nativo.
Como reverter: retirar helpers `confirmAction`/`showToast` do shell e restaurar o fluxo anterior nos hooks.
Referencias: `frontend/src/hooks/usePrintoraApp.ts`, `frontend/src/components/modals/ConfirmDialogModal.tsx`, `frontend/src/components/ToastViewport.tsx`, `frontend/src/hooks/domains/useUpdates.ts`.

### DEC-20260526-04 - Consulta Moonraker nao pode travar a API local

Status: aceita
Data: 2026-05-26
Contexto: chamadas para hosts `.local` podem ficar presas em resolucao mDNS e bloquear o processo local do Printora, fazendo ate `/health` e acoes locais deixarem de responder.
Decisao: a gravacao de silencio de update usa a versao ja exibida no card, sem consultar Moonraker. O cliente Moonraker resolve `.local` fora do loop principal e falha com timeout curto quando a resolucao nao responde.
Alternativas consideradas: pedir reinicio manual sempre que a rota travar; manter consulta live do Moonraker antes de silenciar; trocar a porta/processo sem corrigir DNS.
Consequencias: acoes locais continuam responsivas mesmo com Moonraker lento ou DNS `.local` instavel. O silencio continua expirando quando uma nova leitura do Update Manager muda a identidade da versao.
Impacto em testes: cobrir endpoint de silencio com host Moonraker propositalmente irresolvivel e validar `./check.sh` com testes backend e frontend.
Impacto em rollback: medio; voltar a consulta live no silencio reintroduz risco de travar a UI durante falha de DNS.
Como reverter: remover campos de versao do payload de silencio, voltar a buscar `_current_update_component_payload` na rota e restaurar resolucao `.local` direta no cliente Moonraker.
Referencias: `backend/app/moonraker.py`, `backend/app/routes/printer_updates.py`, `frontend/src/hooks/domains/useUpdates.ts`.

### DEC-20260526-05 - Operacao envia G-code operacional com preflight

Status: aceita
Data: 2026-05-26
Contexto: a tela Operacao estava visualmente parecida com painel de controle, mas ainda funcionava como preview bloqueado. Isso confundia o usuario porque Mainsail permite operar movimento, temperatura, fan e fatores percentuais diretamente.
Decisao: liberar execucao operacional controlada por Moonraker para acoes de operacao da impressora, mantendo preflight live, capacidade confirmada, bloqueio quando ha impressao em andamento, historico local e monitoramento apos envio. Updates, restart, flash e alteracao de config continuam fora da tela Operacao.
Alternativas consideradas: manter apenas preview dry-run; liberar comandos sem preflight; exigir frase manual para cada clique operacional.
Consequencias: a tela passa a operar a impressora de verdade, com risco operacional proporcional a Mainsail. O backend continua bloqueando offline, Klipper/Klippy nao ready, impressao em andamento e capacidade desconhecida.
Impacto em testes: testes backend de operacao foram atualizados para `operation_ready`, preflight executavel e historico de execucao; validacao completa roda com `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
Impacto em rollback: medio; para voltar ao modelo dry-run, restaurar `build_operation_action_preflight` para `would_send_gcode=false`, remover `execute-direct` e voltar botoes da UI para preview.
Como reverter: remover endpoint `/operation/actions/execute-direct`, remover envio via `_send_and_monitor_gcode`, restaurar `can_send_commands=false` e voltar a UI para `Prévia`/`Preflight`.
Referencias: `backend/app/operation.py`, `backend/app/routes/operation.py`, `backend/app/operation_history.py`, `frontend/src/components/monitoring/OperationActions.tsx`.

### DEC-20260527-01 - Catalogo Esoterical CANBus tem schema Pydantic versionado

Status: aceita
Data: 2026-05-27
Contexto: o PKG-30 precisa transformar o guia Esoterical CANBus em catalogo local verificavel, sem depender do site em runtime e sem misturar dados manuais com cobertura nao comprovada.
Decisao: o catalogo local de firmware passa a ter contrato oficial em `FirmwareCatalog`, validado por Pydantic, com `schema_version`, `source`, `manifest`, `workflows`, `hardware`, `troubleshooting`, `update_flows`, `katapult`, `can_speed`, `known_hardware_without_local_preset` e `generation_metadata`. Cada hardware aceita `modelo`, role, conexao, guia, MCUs, metodo de flash, bootloader/Katapult, comandos de validacao, notas de seguranca, presets locais e status de catalogacao.
Alternativas consideradas: manter JSON livre sem contrato; criar tabela SQLite para catalogo; validar apenas no frontend.
Consequencias: a normalizacao, o cruzamento com presets locais, o endpoint read-only e a tela Firmware usam o mesmo contrato validado. O runtime continua lendo arquivo local e nao consulta o site externo.
Impacto em testes: testes backend validam o schema do catalogo, campos obrigatorios do contrato, vinculacao ao manifesto, cobertura do menu publico, dry-run dos scripts, exclusao de comandos mutaveis e runtime sem dependencia externa.
Impacto em rollback: baixo; remover os modelos novos e voltar ao loader JSON livre restaura o comportamento anterior, mas perde validacao de cobertura.
Como reverter: remover `FirmwareCatalog` e campos associados em `backend/app/firmware_catalog.py`, retirar o teste de schema e voltar `firmware_hardware_catalog.json` ao formato minimo anterior.
Referencias: `backend/app/firmware_catalog.py`, `backend/app/routes/firmware.py`, `backend/app/data/firmware_hardware_catalog.json`, `backend/app/data/firmware_canbus_manifest.json`, `backend/tests/test_canbus_manifest.py`, `backend/tests/test_firmware.py`, `scripts/build_canbus_manifest.py`, `scripts/build_firmware_catalog.py`, `frontend/src/screens/FirmwareScreen.tsx`.

### DEC-20260527-02 - Preset de firmware expõe build config versionado

Status: aceita
Data: 2026-05-27
Contexto: o PKG-33 precisa transformar presets locais em entrada segura para geracao futura de `.config`, sem depender de `make menuconfig`, host Klipper real ou estado de impressora.
Decisao: cada `BoardPreset` passa a expor `FirmwareBuildConfig` versionado, com arquitetura, MCU, modelo de processador, bootloader, clock, interface de comunicacao, conexao CAN/USB/serial, arquivo `.config` e output esperado. O backend calcula `build_config_status` e `build_config_validation` para classificar preset completo, faltando dados ou invalido.
Alternativas consideradas: inferir tudo apenas no gerador de `.config`; deixar validacao na UI; persistir configuracao em SQLite antes de existir edicao pelo usuario.
Consequencias: o contrato fica testavel e deterministico no endpoint de presets, sem banco novo e sem executar comandos mutaveis. A UI pode consumir o status sem duplicar regra de suficiencia.
Impacto em testes: testes backend cobrem preset completo, dados faltantes, schema invalido e compatibilidade do endpoint `/api/firmware/board-presets`.
Impacto em rollback: baixo; remover `FirmwareBuildConfig` e os campos calculados volta o preset ao contrato anterior, mas remove a garantia previa para geracao deterministica de `.config`.
Como reverter: remover `FirmwareBuildConfig`, `FirmwareBuildConfigValidation`, `build_config`, `build_config_status` e `build_config_validation` de `backend/app/firmware/models.py`, ajustar tipos frontend e remover testes do Lote 2.
Referencias: `backend/app/firmware/models.py`, `backend/app/firmware/presets.py`, `backend/tests/test_firmware.py`, `frontend/src/types/firmware.ts`.

### DEC-20260527-03 - Build local de firmware é controlado e nunca faz flash

Status: aceita
Data: 2026-05-27
Contexto: o PKG-33 precisa permitir build local real de firmware sem transformar o Printora em ferramenta de flash automático ou mutação remota de impressora.
Decisao: o build local só executa quando `PRINTORA_FIRMWARE_BUILD_MODE=local` e a confirmação textual `EXECUTE_LOCAL_BUILD_NO_FLASH` é enviada. O executor gera `.config` determinístico a partir do preset, faz backup da `.config` atual, executa apenas `make clean` e `make` no `klipper_path` local informado, restaura a `.config` em sucesso ou falha e salva preview, log e binário em `output_root/local-build/<placa>/`. Flash, SSH, restart e update ficam fora do fluxo.
Alternativas consideradas: manter apenas dry-run; aceitar `.config` manual cadastrado; expor flash na mesma UI; executar build sem confirmação textual.
Consequencias: o usuário pode validar build em ambiente local controlado com histórico e rollback, sem risco de flash automático. A UI permanece guiada pela impressora ativa e consome status do backend sem duplicar regra de build.
Impacto em testes: testes backend cobrem bloqueio por modo, bloqueio por confirmação, build fake em tmpdir, restauração de `.config` em sucesso e falha, log/binário salvos e ausência de flash/SSH/restart/update. Fechamento roda `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
Impacto em rollback: médio; remover execução local volta o fluxo para dry-run e preview de `.config`, preservando cadastro de presets.
Como reverter: remover `execute_build_local`, ocultar o bloco de build local da tela Firmware e manter apenas `/build-runs/dry-run`, `/build-runs/preflight` e `/config-preview`.
Referencias: `backend/app/firmware/build_service.py`, `backend/app/firmware/repository.py`, `backend/app/routes/firmware.py`, `frontend/src/screens/FirmwareScreen.tsx`, `RUNBOOK.md`, `TESTES.md`.

### DEC-20260530-04 - Flash supervisionado começa por CAN/Katapult com gate remoto

Status: aceita
Data: 2026-05-30
Contexto: o PKG-37 precisa permitir flash real sem transformar o Printora em executor perigoso por padrão. Flash incorreto pode deixar MCU offline e exige prova de artefato, placa, UUID e rollback.
Decisao: o backend implementa preflight/plan/execute/historico de flash em `Setup do Zero`, mas execução real inicial fica restrita a `can_katapult`. O flash exige checklist físico, UUID visível, artefato remoto existente, impressora parada, frase específica por placa/método e `PRINTORA_REMOTE_FLASH_MODE=remote`. Métodos `usb_dfu` e `manual` ficam bloqueados até política própria.
Alternativas consideradas: liberar qualquer comando manual; manter somente plano sem execução; implementar USB/DFU junto do CAN.
Consequencias: o fluxo entrega uma primeira execução real supervisionada com risco menor e rastreabilidade, sem editar `printer.cfg`, reiniciar serviços, rodar update ou enviar G-code. Hardware real ainda precisa validação acompanhada.
Impacto em testes: testes backend cobrem bloqueios, frase/env, histórico sem `key_path` e ausência de restart/config; frontend build valida contrato da UI.
Impacto em rollback: medio; remover endpoints `/api/setup/flash/*`, modulo `setup_flash`, SQL `024_setup_flash_runs.sql` e seção Flash supervisionado da UI volta o setup ao estado PKG-36.
Como reverter: reverter o commit do PKG-37 e restaurar banco a partir do backup de schema se o script `024_setup_flash_runs.sql` ainda não puder permanecer.
Referencias: `backend/app/setup_flash.py`, `backend/app/routes/setup.py`, `backend/sql/024_setup_flash_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`, `TESTES.md`.

### DEC-20260530-05 - Aceite final do setup é read-only e sanitizado

Status: aceita
Data: 2026-05-30
Contexto: após setup, CAN, firmware e flash, o Printora precisa diferenciar base eletrônica/software pronta de calibração mecânica ainda pendente sem executar comandos perigosos.
Decisao: a validação final executa somente leitura via SSH e Moonraker local, gera checks acionáveis e relatório Markdown sanitizado. O fluxo não envia G-code, não aquece, não move eixo, não reinicia serviços, não edita configs e não executa update.
Alternativas consideradas: usar health check genérico da impressora cadastrada; executar testes de movimento/temperatura; exigir cadastro prévio da impressora.
Consequencias: o setup pode ser fechado antes do cadastro final da impressora, com relatório técnico copiável e risco operacional baixo. Homologação em campo ainda depende de hardware real acompanhado.
Impacto em testes: testes backend cobrem aprovação, bloqueio por UUID ausente, intervenção manual sem UUID e histórico sem `key_path`; frontend build valida o contrato da tela.
Impacto em rollback: baixo; remover endpoints `/api/setup/final-validation/*`, módulo `setup_final_validation`, SQL `025_setup_final_validation_runs.sql` e seção Validação final da UI.
Como reverter: reverter o commit do PKG-38 e restaurar banco a partir do backup de schema se o script `025_setup_final_validation_runs.sql` ainda não puder permanecer.
Referencias: `backend/app/setup_final_validation.py`, `backend/app/routes/setup.py`, `backend/sql/025_setup_final_validation_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`, `TESTES.md`.

### DEC-20260530-06 - Autenticação cloud começa em SQLite com organização opcional

Status: aceita
Data: 2026-05-30
Contexto: o Printora local não exige login, mas a evolução cloud precisa de usuário, sessão, permissões, compartilhamento opcional e base segura para agente remoto. A migração imediata para Postgres aumentaria o custo antes da validação do fluxo.
Decisao: implementar o PKG-39 primeiro em SQLite, com repositório concentrado e SQL simples, evitando dependências desnecessárias de SQLite para facilitar migração futura para Postgres. O modelo é usuário-first: email e senha obrigatórios, contatos opcionais, organização opcional para compartilhamento e papéis mínimos `owner`, `admin` e `operator`.
Alternativas consideradas: migrar já para Postgres; tornar organização obrigatória; manter somente usuário individual sem compartilhamento; deixar 2FA para pacote futuro.
Consequencias: o app local continua funcionando sem login obrigatório, enquanto a área `Conta` entrega cadastro/login, organizações, 2FA, step-up auth e credenciais de agente para o caminho cloud. Rotas operacionais passam a validar sessão quando há usuários cadastrados, rotas por impressora usam o escopo usuário/organização e históricos de setup/update passam a ter owner. A migração futura para Postgres ainda exigirá trabalho de adaptação e validação, mas fica menos arriscada.
Impacto em testes: `backend/tests/test_auth.py` cobre schema, cadastro/login, organização opcional, 2FA, step-up, credencial de agente, bloqueio anônimo de `/api/auth/me`, isolamento por impressora e isolamento de histórico operacional.
Impacto em rollback: médio; remover a camada exige reverter rotas, UI, SQL `026_auth_identity.sql`, `027_printer_ownership.sql`, `028_operational_ownership.sql` e restaurar backup do banco se o schema aplicado não puder permanecer.
Como reverter: reverter arquivos do PKG-39 e restaurar `printora.<timestamp>.before-schema.db` quando for necessário desfazer o schema aplicado.
Referencias: `backend/app/auth.py`, `backend/app/routes/auth.py`, `backend/sql/026_auth_identity.sql`, `backend/sql/027_printer_ownership.sql`, `backend/sql/028_operational_ownership.sql`, `frontend/src/screens/AuthScreen.tsx`, `frontend/src/hooks/domains/useAuth.ts`.

### DEC-20260531-08 - Impressora cloud é cadastro operacional com status derivado do agente

Status: aceita
Data: 2026-05-31
Contexto: o cadastro local de impressoras dependia de Moonraker acessível pela mesma rede, mas o uso cloud precisa permitir cadastrar a impressora antes do agente existir e compartilhar acesso por organização opcional.
Decisao: manter `printers` como entidade canônica, com owner e organização opcional do PKG-39, metadados cloud (`cloud_model`, `cloud_tags`, localização e observações) e status calculado a partir de tokens/agentes/snapshots existentes. O cadastro não tenta conectar no Moonraker automaticamente; descoberta, teste e leitura de status continuam como ações explícitas.
Consequencias: o usuário consegue preparar as duas impressoras na aplicação local por IP da API, instalar/parear agentes depois e ver estados `sem_agente`, `aguardando_pareamento`, `online`, `offline` ou `revogado` sem criar tabela nova de inventário.
Impacto em testes: `backend/tests/test_auth.py` cobre metadados cloud, detalhe escopado, status por token/agente e isolamento para usuário sem acesso.
Como reverter: reverter alterações do PKG-40 em backend/UI/docs; dados existentes de impressoras permanecem preservados e podem ser mantidos até nova decisão.
Referencias: `backend/app/printers.py`, `backend/app/routes/printers.py`, `frontend/src/screens/PrintersScreen.tsx`, `frontend/src/components/modals/PrinterModal.tsx`.

### DEC-20260530-07 - Pareamento do agente usa token curto e credencial operacional por hash

Status: aceita
Data: 2026-05-30
Contexto: o agente precisa parear a partir da rede da impressora, sem o servidor acessar a rede local e sem transformar o token de instalação em credencial permanente.
Decisao: usar token curto de pareamento por impressora, persistido por hash, com expiração, uso único e revogação. A troca pública gera uma credencial operacional `ptr_agent_*`, também persistida por hash, ligada a uma identidade estável do agente. Rotação substitui a credencial ativa e revogação bloqueia heartbeat, snapshot e jobs.
Alternativas consideradas: reutilizar credenciais genéricas do PKG-39; usar token de pareamento como credencial permanente; deixar revogação para pacote futuro.
Consequencias: o usuário consegue instalar/copiar um segredo curto uma vez e o agente passa a autenticar sem expor token permanente. A etapa ainda não instala o agente nem executa comandos remotos; isso fica para pacotes posteriores.
Impacto em testes: `backend/tests/test_agent_pairing.py` cobre uso único, expiração, revogação, ownership, rotação e bloqueio de endpoints do agente revogado.
Impacto em rollback: médio; remover exige reverter rotas, UI, `backend/app/agent_pairing.py` e SQL `029_agent_pairing.sql`, ou restaurar backup do banco anterior ao schema.
Como reverter: reverter arquivos do PKG-41 e restaurar `printora.<timestamp>.before-schema.db` se o schema aplicado não puder permanecer.
Referencias: `backend/app/agent_pairing.py`, `backend/app/routes/agents.py`, `backend/sql/029_agent_pairing.sql`, `frontend/src/screens/PrintersScreen.tsx`, `frontend/src/hooks/domains/usePrinters.ts`.

### DEC-20260531-01 - Agente remoto base em Go

Status: aceita
Data: 2026-05-31
Contexto: o agente precisa rodar em hosts Klipper variados, normalmente Raspberry/BTT Pi, com baixo uso de memória, instalação simples, atualização previsível e sem depender de Python/Node locais.
Decisao: implementar o agente em Go, sem dependências externas, como binário único com CLI `printora-agent`. A base usa config JSON, credencial separada `0600`, HTTP keep-alive, cliente Moonraker read-only, fila JSONL local, logs com redaction e serviço systemd.
Alternativas consideradas: Python para ficar próximo do ecossistema Klipper; Node por reaproveitar stack web; shell scripts para instalação mínima.
Consequencias: distribuição e atualização ficam simples por arquitetura Linux (`arm64`, `armv7`, `amd64`), com menor risco de quebrar venvs Python da impressora. Em troca, integrações futuras precisarão manter contratos Go e testes próprios.
Impacto em testes: `agent/internal/agent/agent_test.go` cobre redaction, permissões, coleta read-only, autenticação Bearer e fila local; `check.sh` passa a executar `go test ./...` em `agent/`.
Impacto em rollback: baixo; remover o agente exige reverter `agent/`, entradas em `PATHS.toml`, `check.sh` e docs. No host real, parar/remover o serviço systemd e o binário.
Como reverter: `sudo systemctl disable --now printora-agent`, remover `/usr/local/bin/printora-agent` e restaurar commit anterior ao PKG-42.
Referencias: `agent/cmd/printora-agent/main.go`, `agent/internal/agent`, `agent/systemd/printora-agent.service`, `agent/docs/README.md`.

### DEC-20260531-02 - Canal remoto usa WebSocket primario e polling de fallback

Status: aceita
Data: 2026-05-31
Contexto: o agente precisa receber comandos rápidos da aplicação web sem abrir portas no host Klipper e sem depender de conectividade WebSocket perfeita em todas as redes.
Decisao: implementar protocolo v1 sobre WebSocket outbound autenticado por credencial operacional do agente, com fallback HTTPS por polling. Jobs ficam persistidos em `agent_jobs`, sempre vinculados a `printer_id` e opcionalmente a `agent_id`, com `correlation_id` único, ack/nack/result/error, limite de payload de 64 KB e resultado idempotente. O agente deve continuar reconectando sozinho com backoff limitado e manter heartbeat/polling HTTPS durante perda de WebSocket para reduzir necessidade de reiniciar a impressora.
Alternativas consideradas: manter apenas polling; abrir socket raw; abrir porta inbound no agente; executar jobs sem persistência.
Consequencias: a latência normal fica baixa por WebSocket e ambientes restritos continuam funcionando por HTTPS. O servidor preserva isolamento por impressora e o agente continua outbound/read-only nesta etapa, aceitando apenas jobs seguros `ping` e `snapshot`. Quedas intermitentes de internet ou proxy nao devem deixar o agente parado esperando reinicio manual.
Impacto em testes: `backend/tests/test_agent_channel.py` cobre isolamento, WebSocket, versão incompatível e idempotência; `agent/internal/agent/agent_test.go` cobre polling, ack/result, URL WebSocket segura, fallback repetido e limite de backoff.
Impacto em rollback: médio; remover exige reverter rotas, serviço de jobs, agente e SQL `030_agent_channel.sql`, ou restaurar backup do banco anterior ao schema se a tabela não puder permanecer.
Como reverter: reverter arquivos do PKG-43, desativar WebSocket no config do agente com `"websocket_enabled": false` durante transição e restaurar `printora.<timestamp>.before-schema.db` se necessário.
Referencias: `backend/app/agent_pairing.py`, `backend/app/routes/agents.py`, `backend/sql/030_agent_channel.sql`, `backend/tests/test_agent_channel.py`, `agent/internal/agent/channel.go`, `agent/internal/agent/api.go`.

### DEC-20260531-03 - Instalador do agente troca token curto no host e preserva dados no uninstall

Status: aceita
Data: 2026-05-31
Contexto: o usuário precisa instalar o agente no host Klipper com o menor erro manual possível, sem transformar o token de pareamento em segredo permanente e sem esconder riscos de systemd, Moonraker, rede ou permissão.
Decisao: gerar um plano de instalação por impressora com token curto, servir um script Linux público sem segredo embutido e fazer a troca do token por credencial operacional no próprio host. O instalador tem `--preflight`, `--apply --yes` e `--uninstall`, exige systemd para serviço, grava config/credencial com permissão restrita e preserva dados locais no uninstall.
Alternativas consideradas: embutir credencial operacional no comando; instalar sem preflight; apagar diretórios no uninstall; deixar a instalação somente documentada.
Consequencias: a instalação fica copiável pela UI e auditável por status de heartbeat, mantendo uso único do token. O pacote ainda não faz auto-update nem resolve distribuição final de binários por release; isso fica para o PKG-45.
Impacto em testes: `backend/tests/test_agent_install.py` cobre isolamento do plano, consumo único do token, status por heartbeat e preflight sem vazamento de token.
Impacto em rollback: baixo; remover exige reverter endpoints/UI/script e, no host real, rodar `--uninstall`. Dados locais do agente permanecem até remoção manual explícita.
Como reverter: revogar tokens/agentes pela tela Impressoras, rodar `curl -fsSL <api>/api/agent/install/linux.sh | sudo bash -s -- --uninstall` no host e reverter arquivos do PKG-44.
Referencias: `backend/scripts/install_agent_linux.sh`, `backend/app/routes/agents.py`, `backend/app/agent_pairing.py`, `backend/tests/test_agent_install.py`, `frontend/src/screens/PrintersScreen.tsx`.

### DEC-20260531-04 - Update do agente troca apenas o binário e exige SHA-256

Status: aceita
Data: 2026-05-31
Contexto: o agente precisa evoluir junto com o servidor cloud, mas roda no host Klipper. Um update quebrado não pode reiniciar Klipper, Moonraker, firmware ou a impressora, e precisa ter rollback local.
Decisao: o agente consulta manifesto público versionado, escolhe release por plataforma, bloqueia versão/protocolo incompatível, exige SHA-256, baixa para staging, preserva backup do binário/config e troca somente o binário do `printora-agent`. Restart automático só é permitido para o serviço `printora-agent` quando `allow_service_restart=true`. Falha em health command ou restart restaura o binário anterior quando possível. A UI cria um job direcionado `remote_agent_update_check` para antecipar a verificação periódica sem acessar a rede local diretamente.
Alternativas consideradas: delegar update ao Moonraker Update Manager; baixar sem hash em ambiente de desenvolvimento; reiniciar todos os serviços do host; deixar update apenas manual.
Consequencias: o update fica automatizável e auditável sem tocar na impressora. A publicação real de binários e assinatura forte ainda depende do fluxo de release do agente, mas o contrato já bloqueia aplicação sem hash.
Impacto em testes: `backend/tests/test_agent_updates.py` cobre manifesto, relatório autenticado e histórico isolado; `backend/tests/test_agent_support.py` cobre job remoto de update direcionado; `agent/internal/agent/agent_test.go` cobre sucesso, hash inválido, rollback por health, versão bloqueada e execução do job remoto.
Impacto em rollback: médio; no host real, restaurar backup local do binário em `/var/lib/printora-agent/updates` e reiniciar apenas `printora-agent`.
Como reverter: desativar `"update_enabled": false` no config, reverter arquivos do PKG-45 e restaurar o binário anterior se necessário.
Referencias: `backend/app/agent_updates.py`, `backend/app/data/agent_update_manifest.json`, `agent/internal/agent/update.go`, `agent/cmd/printora-agent/main.go`, `RUNBOOK.md`.

### DEC-20260531-05 - Paridade remota usa matriz explícita e bloqueia mutações até PKG-47

Status: aceita
Data: 2026-05-31
Contexto: o Printora cloud precisa reutilizar as leituras e previews existentes sem o servidor acessar a rede local da impressora. Ao mesmo tempo, operações mutáveis remotas exigem autorização, preflight e rollback próprios.
Decisao: criar matriz de paridade por impressora com estados explícitos e jobs remotos executados pelo agente. Jobs read-only e dry-run são permitidos; backup real com payload grande, build/flash remoto e operação mutável ficam bloqueados até a camada de segurança do PKG-47.
Alternativas consideradas: tentar chamar Moonraker diretamente do servidor; liberar mutações junto com a paridade; esconder funcionalidades ainda não suportadas da matriz.
Consequencias: a UI/API consegue diferenciar implementado, cached, offline, bloqueado e não suportado, evitando falsa paridade. A execução remota continua outbound pelo agente e payloads são sanitizados antes de sair do host.
Impacto em testes: `backend/tests/test_agent_parity.py` cobre matriz, isolamento, criação de job, estado cached e bloqueio; `agent/internal/agent/agent_test.go` cobre job remoto read-only com sanitização.
Impacto em rollback: baixo; remover rotas e jobs de paridade volta o cloud ao pareamento/canal remoto sem alterar schema.
Como reverter: reverter arquivos do PKG-46; jobs já concluídos permanecem em `agent_jobs` como histórico seguro.
Referencias: `backend/app/agent_parity.py`, `backend/app/routes/agents.py`, `backend/tests/test_agent_parity.py`, `agent/internal/agent/moonraker.go`, `agent/internal/agent/channel.go`.

### DEC-20260531-06 - Operação remota mutável exige preflight e execução em jobs separados

Status: aceita
Data: 2026-05-31
Contexto: operações mutáveis pelo agente podem mover, aquecer ou alterar estado da impressora fora da rede local. A execução não pode depender só de clique na UI nem de confiança implícita no agente.
Decisao: separar toda operação remota mutável em dois jobs persistidos: `remote_mutation_preflight` e `remote_mutation_execute`. O servidor cria execução somente para usuário com acesso à impressora, com preflight concluído, confirmação textual única, job não expirado e resultado `can_execute=true`. O agente reexecuta preflight imediatamente antes de enviar G-code e usa apenas `/printer/gcode/script`, sem shell genérico.
Alternativas consideradas: executar direto depois da confirmação na UI; reaproveitar jobs de paridade; permitir comando arbitrário no agente; criar tabela nova de auditoria.
Consequencias: aumenta a latência operacional, mas reduz risco de ação remota fora de estado seguro. `agent_jobs` e `printer_agent_events` viram a trilha de auditoria principal sem aumentar schema.
Impacto em testes: `backend/tests/test_remote_operations.py` cobre escopo, preflight, confirmação, bloqueio por impressão e cancelamento; `agent/internal/agent/agent_test.go` cobre preflight/execução remota sem shell.
Impacto em rollback: baixo; remover rotas, módulo remoto, UI e handlers do agente volta as mutações remotas ao bloqueio do PKG-46. Jobs históricos permanecem como auditoria.
Como reverter: reverter arquivos do PKG-47 e manter agentes instalados; eles passarão a responder `unsupported job type` se algum job antigo for reenviado.
Referencias: `backend/app/remote_operations.py`, `backend/app/routes/agents.py`, `backend/tests/test_remote_operations.py`, `agent/internal/agent/moonraker.go`, `agent/internal/agent/channel.go`, `frontend/src/screens/PrintersScreen.tsx`.

### DEC-20260531-07 - Suporte do agente usa eventos/jobs existentes e pacote sanitizado

Status: aceita
Data: 2026-05-31
Contexto: suporte precisa diagnosticar agente remoto sem acessar a rede local do cliente e sem criar um novo repositório de logs sensíveis.
Decisao: usar `printer_agents`, `agent_jobs` e `printer_agent_events` como fonte de observabilidade. O painel calcula saúde, fila, falhas e alertas em leitura; `remote_doctor` coleta diagnóstico local pelo agente; o pacote de suporte é exportado sanitizado e não cria tabela nova.
Alternativas consideradas: criar tabela dedicada de logs; enviar logs completos do host; diagnosticar somente por heartbeat; apagar eventos automaticamente no endpoint.
Consequencias: a solução fica simples e auditável, sem duplicar persistência. A limpeza fica definida como retenção operacional de 180 dias e deve ser executada por rotina supervisionada futura, não pelo endpoint de suporte.
Impacto em testes: `backend/tests/test_agent_support.py` cobre escopo, alertas, doctor e sanitização do pacote; `agent/internal/agent/agent_test.go` cobre doctor remoto com log tail sanitizado.
Impacto em rollback: baixo; remover rotas/UI/handler `remote_doctor` preserva os eventos e jobs já existentes.
Como reverter: reverter arquivos do PKG-48; agentes antigos passam a rejeitar `remote_doctor` como job não suportado.
Referencias: `backend/app/agent_support.py`, `backend/app/routes/agents.py`, `backend/tests/test_agent_support.py`, `agent/internal/agent/doctor.go`, `frontend/src/screens/PrintersScreen.tsx`.

### DEC-20260531-08 - Rotas operacionais usam agente como caminho principal

Status: aceita
Data: 2026-05-31
Contexto: a aplicação precisa funcionar em cenário cloud/rede local sem depender de o servidor alcançar diretamente o Moonraker ou SSH da impressora. A impressora selecionada deve ser operada pelo agente pareado como caminho principal.
Decisao: centralizar criação, push e espera de jobs em um executor do agente e migrar status, operação, snapshots, auditoria, relatórios, checklist, calibração, update manager e inventário de firmware para jobs outbound pelo agente. Acesso direto ao Moonraker/SSH permanece apenas como legado/bootstrap de setup ou utilitário local explícito, não como caminho operacional das telas principais.
Alternativas consideradas: manter chamadas diretas com fallback para agente; duplicar lógica por rota; abrir conectividade inbound no host Klipper; permitir shell genérico no agente.
Consequencias: as telas principais passam a depender de agente online e exibem erro quando não há agente, reduzindo risco de isolamento e aproximando o ambiente local do futuro cloud. O agente precisa evoluir junto do servidor, por isso a versão esperada foi atualizada para `0.1.8`.
Impacto em testes: `./check.sh`, `go test ./...`, testes focados de backend e smoke real nas duas impressoras com status, operação, update refresh, calibração, snapshot, firmware inventory e execução segura `M106 S0`.
Impacto em rollback: médio; reverter exige restaurar handlers diretos das rotas e reinstalar agente anterior se necessário. Jobs históricos permanecem em `agent_jobs`.
Como reverter: reverter este commit, reinstalar binário do agente anterior em `/usr/local/bin/printora-agent` nos hosts e reiniciar apenas `printora-agent`.
Referencias: `backend/app/agent_executor.py`, `backend/app/agent_channel.py`, `backend/app/agent_moonraker.py`, `backend/app/routes/operation.py`, `backend/app/routes/calibration.py`, `agent/internal/agent/moonraker.go`, `agent/internal/agent/channel.go`.

### DEC-20260531-09 - Fluxos de impressora em cloud nao usam rede local pela API

Status: aceita
Data: 2026-05-31
Contexto: ao publicar a API em IP publico, ela nao tera acesso a Moonraker, SSH, CAN, arquivos ou rede local da impressora. Qualquer fluxo que ainda roda no servidor da API gera falso positivo local e falha em cloud.
Decisao: desativar descoberta/teste direto pela API, mover setup, CAN, firmware, flash, validacao final, auditoria de host, horas de impressao, backup e build de firmware para jobs do agente. O job `remote_host_script` executa scripts controlados gerados pelo backend no host pareado; os demais fluxos continuam usando jobs Moonraker especificos do agente.
Alternativas consideradas: manter fallback direto para ambiente local; exigir VPN/rede privada entre cloud e impressora; manter SSH via API para setup.
Consequencias: a API passa a bloquear quando nao existe agente pareado/online em vez de tentar rede local. Setup de uma placa sem agente exige primeiro instalar/parear um agente na impressora ou em um futuro agente de rede dedicado para descoberta.
Impacto em testes: backend completo, Go completo e busca por chamadas diretas de Moonraker/SSH nas rotas operacionais.
Impacto em rollback: medio; reverter recoloca caminhos diretos e deve ser evitado em ambiente cloud.
Como reverter: reverter esta decisao e os arquivos de agente/backend relacionados; reinstalar agente anterior se necessario.
Referencias: `backend/app/agent_host.py`, `backend/app/routes/printers.py`, `backend/app/routes/setup.py`, `backend/app/routes/backups.py`, `backend/app/routes/firmware.py`, `backend/app/routes/audit.py`, `agent/internal/agent/host.go`.

### DEC-20260531-10 - Navegacao cloud usa frota e detalhe de registro

Status: aceita
Data: 2026-05-31
Contexto: o Printora deixou de ser apenas uma UI local para uma impressora e passou a operar em ambiente web/cloud com varias impressoras e agentes. A navegacao antiga escondia ou expunha secoes com base em uma impressora ativa global, o que nao escala para frota, agentes remotos e usuarios/organizacoes.
Decisao: o menu principal passa a conter somente areas globais independentes de impressora. `Impressoras` e `Agentes` viram listas de frota; operacao, atualizacoes, calibracao, firmware, manutencao, diagnostico/backups e pareamento ficam dentro do detalhe da impressora. Saude, fila, doctor remoto, suporte e credencial ficam dentro do detalhe do agente. A topbar fica fixa e global, sem seletor de impressora e sem acoes especificas de tela; ela mostra titulo, alertas de frota, Sobre, tema e conta do usuario no extremo direito.
Alternativas consideradas: manter grupo `Impressora ativa` no menu; esconder secoes quando a impressora estiver offline; criar rotas separadas para cada tela operacional ainda dependentes de contexto global.
Consequencias: a UI fica coerente com cloud/frota e evita que telas globais desaparecam por falta de impressora. Acoes contextuais passam a ficar no corpo da tela ou aba especifica. A Central de alertas precisa agregar alertas de frota e permitir abrir a impressora afetada.
Impacto em testes: build frontend deve passar e `./check.sh` valida documentacao/governanca. Validacao visual deve abrir menu global, lista de impressoras, detalhe da impressora e detalhe do agente.
Impacto em rollback: baixo a medio; reverter restaura as secoes operacionais no menu lateral e remove `PrinterDetailScreen`/`AgentDetailScreen`.
Como reverter: reverter alteracoes em `frontend/src/app/navigation.ts`, `frontend/src/hooks/usePrintoraApp.ts`, `frontend/src/main.tsx`, telas novas de detalhe e atualizacoes de `TELAS.md`.
Referencias: `frontend/src/app/navigation.ts`, `frontend/src/screens/PrinterDetailScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `frontend/src/screens/PrintersScreen.tsx`, `frontend/src/screens/AgentsScreen.tsx`, `TELAS.md`.

### DEC-20260531-11 - Update de agente usa job remoto direto

Status: substitui a decisão original de fallback por SSH
Data: 2026-05-31
Atualizacao: 2026-06-01
Contexto: o fallback por SSH gerava falha de credencial e contradizia o objetivo cloud: se o agente já está instalado e online, ele deve receber a ação pelo canal do agente e se autoatualizar.
Decisao: a UI e o backend sempre criam `remote_agent_update_check` para o agente ativo, independentemente da versão reportada. O instalador systemd padrão roda o agente como `root` para que o próprio agente consiga trocar `/usr/local/bin/printora-agent` e reiniciar `printora-agent` sem SSH, senha ou ação manual do usuário.
Alternativas consideradas: manter SSH como ponte para agentes antigos; exigir comando manual; usar sudoers específico para o usuário `printora-agent`; criar shell genérico remoto.
Consequencias: o fluxo fica consistente com cloud e usuário leigo. O agente instalado tem privilégio maior no host, limitado pelo contrato de jobs explícitos e sem shell genérico. Hosts antigos instalados sem permissão suficiente podem precisar reinstalação única do serviço para ganhar o novo modelo.
Impacto em testes: `backend/tests/test_agent_support.py` cobre criação direta do job remoto para agente antigo e atual; build frontend valida remoção dos rótulos de SSH/manual.
Impacto em rollback: médio; voltar ao fallback SSH exige restaurar `_request_legacy_update_via_ssh` e rótulos da UI.
Como reverter: reverter alterações em `backend/app/agent_support.py`, instalador do agente, unit systemd e textos da UI/documentação.
Referencias: `backend/app/agent_support.py`, `backend/scripts/install_agent_linux.sh`, `agent/systemd/printora-agent.service`, `frontend/src/screens/AgentsScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `RUNBOOK.md`.

### DEC-20260601-01 - Administracao cloud separa plataforma, impressora e agente

Status: aceita
Data: 2026-06-01
Contexto: a tela antiga de configuracoes misturava update do Printora, diagnostico local do servidor, CAN da impressora e diagnostico do host onde o agente roda. Em cloud isso confunde operador e expõe informacoes que pertencem a outros contextos.
Decisao: manter `settings` como tela global de Administracao, sem releases da plataforma para usuarios comuns. Versao publicada, releases e historico administrativo da plataforma ficam restritos ao usuario de suporte `breno@mayder.com.br`; a operacao de update visivel ao cliente passa a ser por agente. Registro tecnico CAN passa para `Detalhe da impressora > Diagnostico`. Diagnostico de host/dispositivo passa para `Detalhe do agente`, abastecido por doctor remoto do agente, incluindo leitura Raspberry de energia/throttling quando disponivel.
Alternativas consideradas: manter os blocos colapsados em Configuracoes; criar uma tela global de Diagnostico tecnico; esconder os blocos apenas por permissao.
Consequencias: o operador leigo ve menos acoes perigosas no escopo global. Suporte passa a diagnosticar impressora e agente no registro correto. O doctor remoto precisa evoluir junto do agente para ampliar leituras de hardware.
Impacto em testes: build frontend, testes Go do agente e `./check.sh` devem validar a reorganizacao.
Impacto em rollback: baixo; reverter esta decisao devolve os blocos para Settings e remove a leitura Raspberry do doctor.
Como reverter: reverter alteracoes em `frontend/src/screens/SettingsScreen.tsx`, `frontend/src/screens/ReportsScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `agent/internal/agent/doctor.go` e documentacao.
Referencias: `frontend/src/screens/SettingsScreen.tsx`, `frontend/src/screens/ReportsScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `agent/internal/agent/doctor.go`, `TELAS.md`.

### DEC-20260609-01 - SAVE_CONFIG fica como acao supervisionada

Status: aceita
Data: 2026-06-09
Contexto: calibrações Klipper como `PID_CALIBRATE` retornam valores úteis no console e pedem `SAVE_CONFIG` para gravar no `printer.cfg` e reiniciar o firmware. O Printora precisa guardar o retorno técnico sem aplicar alterações permanentes automaticamente.
Decisao: o agente captura trecho do `/server/gcode_store` após execuções de calibração e o backend salva esse retorno no histórico. Quando o console indicar `SAVE_CONFIG`, a UI mostra os parâmetros e explica que a configuração ainda precisa ser salva. A aplicação oferece `Salvar config` como ação operacional supervisionada, com preflight e confirmação, mas não dispara esse comando automaticamente a partir do resultado de calibração.
Alternativas consideradas: salvar automaticamente após PID; deixar o usuário ir sempre ao Mainsail; armazenar só uma nota manual. 
Consequencias: o histórico passa a guardar evidência técnica do PID e o operador tem caminho explícito para aplicar valores pendentes, preservando controle humano sobre escrita em arquivo e restart do Klipper.
Impacto em testes: `backend/tests/test_calibration.py` cobre extração do console/PID; `backend/tests/test_operation.py` cobre preview `SAVE_CONFIG`; `go test ./...`, build frontend e `./check.sh` validam o fluxo.
Impacto em rollback: médio; remover a ação `save_config` volta a exigir Mainsail para salvar, mas os históricos já registrados permanecem legíveis como JSON.
Como reverter: reverter alterações em `backend/app/routes/calibration.py`, `backend/app/operation.py`, `agent/internal/agent/moonraker.go`, modais de calibração e manifesto/binário do agente.

### DEC-20260609-02 - Remediacao supervisionada de config incluida

Contexto: em instalacoes Klipper com `[include ...]`, `SAVE_CONFIG` pode falhar com conflito quando a secao/opcao gerenciada esta em arquivo incluido, por exemplo `[extruder] control`. Nesse caso o usuario precisa de um caminho seguro para aplicar os valores calculados sem editar arquivo manualmente.

Decisao: quando houver valores calculados em uma calibracao e o `SAVE_CONFIG` falhar por conflito de include, o Printora oferece uma remediacao supervisionada: o agente varre somente `~/printer_data/config`, considera arquivos `.cfg` e `.conf`, ignora comentarios/backups, lista todas as secoes ativas compatíveis, mostra diff por arquivo e aplica apenas os alvos selecionados pelo usuario. A aplicacao exige autenticacao reforcada, cria backup remoto antes de sobrescrever e reinicia o firmware apos aplicar.

Consequencias: o fluxo continua explicito e auditavel, sem alterar arquivos fora da pasta de configuracao da impressora. A primeira implementacao expõe a remediacao para PID do hotend; o backend aceita secao/opcoes genericas para evoluir para outras calibracoes.

Impacto em testes: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

Como reverter: reverter `backend/app/config_remediation.py`, endpoints de remediacao em `backend/app/routes/calibration.py` e componentes/estado de remediacao no frontend.
Referencias: `backend/app/routes/calibration.py`, `backend/app/operation.py`, `agent/internal/agent/moonraker.go`, `frontend/src/components/modals/CalibrationExecuteModal.tsx`, `frontend/src/components/modals/CalibrationResultModal.tsx`.

### DEC-20260601-03 - Update de agente sem SSH e manifesto derivado do artefato publicado

Status: aceita
Data: 2026-06-01
Contexto: o update do agente deve ser simples para usuario leigo e nao pode depender de SSH salvo como ultimo recurso. O manifesto estatico tambem pode ficar divergente do binario realmente servido, causando falha de SHA-256.
Decisao: o endpoint de update do agente cria job `remote_agent_update_check`, tenta entregar imediatamente via WebSocket e mantém fallback por heartbeat/polling. O manifesto publico do agente recalcula URL e SHA-256 a partir do artefato local publicado em `.artifacts/agent` antes de responder.
Consequencias: a UI deixa de sugerir update por SSH. Se o agente estiver online e suportar o job de update, a acao chega imediatamente; se nao estiver, fica pendente para o proximo contato. Agentes legados que ainda nao suportam `remote_agent_update_check` precisam de uma atualizacao/reinstalacao manual unica para entrar no fluxo novo. Falha real passa a vir do resultado do job ou do relatorio do agente, nao do SSH da impressora.
Como reverter: voltar `backend/app/routes/agents.py`, `backend/app/agent_support.py`, `backend/app/agent_updates.py`, `frontend/src/hooks/domains/usePrinters.ts` e documentacao.

### DEC-20260609-02 - Datas usam timezone do usuario na UI

Status: aceita
Data: 2026-06-09
Contexto: dados persistidos em SQLite usam timestamps UTC/texto sem offset em vários módulos. Somar ou subtrair horas no banco corromperia histórico e criaria divergência entre usuários.
Decisao: adicionar `timezone` em `auth_users` e usar esse valor apenas na camada de formatação do frontend. A regra para datas novas e existentes é manter o valor bruto persistido e converter na UI por `formatDateTime`.
Consequencias: cada usuário vê horários no próprio fuso sem regravar históricos. Novas telas devem usar o formatter centralizado em vez de `new Date(...).toLocaleString(...)` local.
Impacto em testes: schema SQL, testes de auth, build frontend e `./check.sh`.
Impacto em rollback: baixo; remover a coluna volta ao fuso padrão do navegador/servidor, mas históricos permanecem intactos.
Como reverter: reverter `backend/sql/034_auth_user_timezone.sql`, campos de auth e formatter de datas do frontend.
