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
