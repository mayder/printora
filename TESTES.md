# TESTES.md

## Objetivo

Definir validações mínimas para o Printora.

## Pirâmide de testes

### Unitário

- Testa regra pura, parser, policy, sanitizacao, mapper e calculo.
- Deve ser rapido e deterministico.
- Nao acessa rede, banco real, filesystem real ou UI real.

### Service/use case

- Testa fluxo de negocio com fakes, mocks ou fixtures controladas.
- Cobre caso feliz, validacao, erro de dependencia e permissao quando aplicavel.

### Repository/adapter

- Testa transformacao, query, serializacao e contrato com dependencia externa usando fixture ou banco local controlado.

### Contrato/API

- Testa payload publico, status, erro, paginacao, filtros e compatibilidade com frontend.

### Componente/UI

- Testa estados principais quando houver estrutura de teste disponivel.
- Cobre loading, empty, error, success e interacao principal.

### E2E

- Reservado para fluxo critico, regressao de alto risco ou fechamento de pacote.

## Cobertura mínima por criticidade

- P0/critico: teste automatizado ou evidencia objetiva obrigatoria, `./check.sh` e regressao do fluxo.
- P1/alto: teste automatizado quando viavel e reteste focado.
- P2/medio: reteste direcionado e teste local proporcional.
- P3/baixo: validacao local da alteracao.

Metas percentuais podem ser ativadas em `PATHS.toml` por projeto, mas o minimo universal e evidencia proporcional ao risco.

## Dados de teste e fixtures

- Fixtures ficam em `backend/tests/fixtures` e `frontend/tests/fixtures`.
- Nao usar dump de producao.
- IDs e datas devem ser deterministicas quando possivel.
- Fixture grande demais precisa justificativa.
- Fixture nao pode conter senha, token, chave, URL privada sensivel ou payload real sem sanitizacao.

## Check Local

Comando obrigatório antes de commit:

```bash
./check.sh
```

## Instalação 0.1.5

Validação offline:

```bash
./scripts/ensure_node_runtime.sh --plan
./scripts/install_printora.sh --plan
./scripts/install_printora_autostart.sh --plan
```

Aceite:

- `--plan` não altera arquivos;
- plano informa se usará Node atual ou Node 22 via `nvm`;
- plano de autostart informa o mecanismo do ambiente atual;
- `--apply --yes` prepara dependências e configura boot automático;
- Linux/Raspberry usa `systemd` com `Restart=always`;
- Android/Termux usa `Termux:Boot` e `tmux`;
- macOS usa `launchd` com `KeepAlive`;
- Windows usa tarefa agendada `Printora`;
- Node antigo não substitui o Node global do sistema, preservando serviços como Spoolman.

O check inicial valida:

- existência dos documentos principais;
- ausência de marcadores básicos de segredo;
- formato básico do `PATHS.toml`;
- compilação sintática do backend Python;
- validade do `frontend/package.json`;
- permissão executável do `check.sh`.

## Modelo De Testes

### Unitário

Testes unitários devem cobrir regras puras, parsers, normalização de payloads, repositórios SQLite com banco temporário e serviços sem depender de rede real.

### Cobertura mínima por criticidade

- P0/crítico: regra de negócio, contrato de API, persistência, erro/rollback e validação manual do fluxo principal quando aplicável.
- P1/alto: teste automatizado da regra ou endpoint afetado e validação focada.
- P2/P3: validação proporcional, com teste automatizado quando houver risco de regressão.

### Dados de teste e fixtures

Fixtures devem ficar em `backend/tests/fixtures` ou `frontend/tests/fixtures`, ser determinísticas e não depender de dump real, horário real, ordem implícita ou dados de produção.

## Banco Local

Mudanças de banco devem ser feitas por scripts `.sql` idempotentes em `backend/sql/`.

Validações:

- `initialize_database()` pode rodar mais de uma vez;
- `initialize_database()` registra scripts SQL aplicados em `schema_versions`;
- `initialize_database()` cria `app_version` com versão do app e revisão de schema;
- `initialize_database()` preserva dados em banco existente e cria backup no mesmo `data_dir` antes de scripts pendentes;
- falha durante aplicação de SQL restaura o banco original a partir do backup automático;
- validação pós-schema usa `PRAGMA integrity_check` e registra resultado em `schema_integrity_checks`;
- falha de `integrity_check` bloqueia conclusão de `initialize_database()`;
- reexecutar `initialize_database()` não duplica registros de versão;
- `GET /api/system/version` retorna versão do app, `data_dir`, caminho do banco, scripts SQL aplicados, schema atual e última validação sem conteúdo do banco;
- tabelas multi-impressora existem;
- endpoints não armazenam credenciais;
- fixtures ficam em `backend/tests/fixtures/`.
- snapshots ficam vinculados a `printer_id`;
- listagem de snapshot retorna resumo, não payload completo.
- comparação de snapshots rejeita snapshots de outra impressora.
- comparação classifica componentes falhando como bloqueio e repos `dirty` como risco.
- checklist pós-update retorna origem dos dados, bloqueia fallback/offline e não executa comandos mutáveis.
- checklist pós-update real por impressora deve retornar `data_state=live` quando Moonraker estiver acessível e manter smoke manual pendente.
- descoberta de impressoras aceita somente redes privadas `/24` ou menores.
- descoberta de impressoras rejeita rede pública e rede grande demais.
- descoberta de impressoras marca cadastro existente por hostname resolvido para IP.
- auditoria read-only retorna origem dos dados, classifica achados e usa último snapshot quando Moonraker está offline.
- health check permite impressora ready sem bloqueios.
- health check bloqueia Klipper não ready ou último diff crítico.
- health check classifica repo `dirty` como monitoramento.
- health check normaliza memória real em kB do Moonraker e reporta armazenamento mesmo quando espaço livre não é exposto.
- backup dry-run cria histórico sem ler/copiar arquivos.
- políticas e histórico de backup ficam escopados por impressora.
- execução local de backup cria `.zip` usando apenas diretórios temporários em teste.
- execução local bloqueia política `dry_run_only` e destino dentro da origem.
- comparação de backups `.zip` é read-only e identifica arquivos adicionados, removidos e alterados.
- plano de restore de backup fica bloqueado e não extrai/sobrescreve arquivos.
- gate de restore aceita confirmação textual, mas permanece bloqueado e não extrai/sobrescreve arquivos.
- relatório sanitizado remove IP, URL, caminho local e valores sensíveis detectáveis.
- relatório sanitizado inclui health, snapshots, diff e histórico de backup sem dados privados.
- relatório sanitizado expõe `source` sanitizado e não vaza URL/IP/caminho/segredo no Markdown real por impressora.
- eventos de manutenção ficam vinculados à impressora correta.
- tarefa preventiva inicia pendente, ao concluir gera evento e fica em dia.
- registro manual de Z-offset calcula delta contra valor anterior compatível.
- Z-offset gera alerta `monitorar` ou `revisar` quando a variação passa do limite.
- histórico de Z-offset fica escopado por impressora.
- wizard de Z-offset retorna roteiro manual e não executa comandos.
- wizard de Z-offset recomenda revisão quando delta é alto.
- registro manual CAN calcula delta contra leitura anterior da mesma interface.
- registro manual CAN classifica `tx_retries` crescente como monitoramento.
- registro manual CAN classifica `rx_error` ou `tx_error` crescente como problema.
- registro manual CAN classifica barramento fora de `ERROR-ACTIVE` como problema.
- histórico CAN fica escopado por impressora.
- resumo CAN sem leituras retorna `data_state=no_data`.
- comparação CAN entre duas leituras manuais calcula deltas e classificação sem executar comando no host.
- comparação CAN pela UI deve escolher duas leituras da mesma interface.
- auditoria de plugins usa último snapshot Moonraker/Update Manager.
- auditoria de plugins funciona sem snapshot e não executa comandos no host.
- auditoria de plugins classifica KTC-Easy como perigoso remover agora e Auto Speed como legado/lixo técnico.
- auditoria de plugins transforma componentes fora do catálogo em item investigável com evidência e gates.
- catálogo de presets de firmware inclui placas comuns BTT, Mellow e Fysetc.
- cadastro de placa de firmware herda MCU, conexão e método de flash do preset.
- placas CAN exigem UUID CAN.
- placas de firmware ficam escopadas por impressora.
- dry-run de build de firmware gera checklist e comandos planejados sem executar comandos.
- dry-run de build exige placa cadastrada.
- histórico de dry-run de build fica escopado por impressora.
- preflight de build de firmware valida paths/tooling local de forma read-only e mantém execução bloqueada.
- build local fica bloqueado quando `PRINTORA_FIRMWARE_BUILD_MODE` está desabilitado.
- build local exige confirmação textual quando o modo local está habilitado.
- dry-run de flash usa binário de build quando informado e não executa comandos.
- dry-run de flash rejeita build de outra placa.
- preflight de flash lê Moonraker/Klipper, bloqueia impressão em andamento e nunca libera execução real neste lote.
- plano de recuperação de firmware é manual, bloqueado e não executa flash, restart, SSH ou comandos locais.
- catálogo de calibração é criado por SQL idempotente.
- catálogo de calibração classifica modo de execução, risco e bloqueio durante impressão.
- catálogo de calibração pode ser filtrado por categoria.
- histórico manual de calibração fica escopado por impressora.
- histórico manual rejeita chave de teste inexistente.
- sequência de calibração marca testes concluídos e pendentes sem enviar G-code.
- preflight de calibração usa leitura real Moonraker/Klipper, bloqueia durante impressão e nunca libera envio de G-code neste lote.
- execução de calibração exige operador presente, revisão de G-code, confirmação textual, preflight live e registra comandos enviados.
- execução de calibração monitora Moonraker/Klipper após o envio e trata timeout de transporte como sucesso quando o estado final fica confirmado.
- retorno final da execução de calibração fica disponível para preencher o registro manual do resultado.
- execução de calibração bloqueia Moonraker offline, impressão em andamento e comando fora da allowlist.
- artefatos de systemd, Mainsail e Update Manager existem e apontam para serviço local.
- instalador Raspberry roda em dry-run por padrão.
- bootstrap dev macOS/Linux roda em dry-run por padrão.
- instalador Linux recusa macOS/Windows e hosts sem systemd.
- Docker Compose define porta, volume e modo seguro por padrão.
- validador de integração Mainsail/Moonraker/systemd roda offline e verifica artefatos de instalação.
- frontend organiza os painéis em navegação lateral por domínio.
- frontend mantém as ações existentes sem executar comandos novos na troca de seção.
- frontend mantém a impressora ativa na topbar e usa esse contexto no restante do sistema.
- cadastro/detecção de impressora acontece em modal, sem poluir o dashboard.
- frontend separa Monitoramento, Calibração, Testes, Firmware, Manutenção, Relatórios e Configurações.
- frontend mostra orientação objetiva de uso em cada seção.
- operação read-only real deve retornar `safe_mode=read_only`, `can_send_commands=false`, painéis populados e ações bloqueadas por impressora.
- fallback de último estado operacional deve preservar objetos conhecidos do snapshot para matriz de capacidades.
- histórico de temperatura por snapshot deve ser ordenado e não consultar Moonraker ao montar os pontos históricos.
- matriz de capacidade deve usar objetos reais/último snapshot sem pressupor Voron específica, mantendo ações sem objeto conhecido como `unknown`.
- preflight final por ação operacional deve usar leitura live, bloquear impressão em andamento, bloquear capacidade ausente e manter `can_execute=false`.
- releases do Printora usam fixtures em `backend/tests/fixtures/` e `frontend/tests/fixtures/`.
- `GET /api/system/releases` retorna `safe_mode=read_only`, versão instalada, canal, última release, changelog resumido e status `up_to_date`, `outdated` ou `unknown`.
- `GET /api/system/update/status` é somente leitura e retorna `update_supported=false`.
- falha de rede, GitHub offline ou rate limit retornam payload seguro e não quebram a aplicação.
- a tela Configurações carrega o restante da UI mesmo quando releases falham.
- a tela Configurações tem somente ação de verificação de releases/status e não chama rota mutável de update.
- plano do updater do próprio Printora cria histórico em `app_update_runs` e etapas em `app_update_steps` sem alterar arquivos.
- plano do updater detecta Android/Termux e Unix, e rejeita ambiente desconhecido.
- histórico do updater lista runs e permite abrir um run com suas etapas.

Testes automatizados adicionais:

```bash
cd backend
. .venv/bin/activate
pytest
```

```bash
cd frontend
npm run test:releases
npm run build
```

## Execução Local Do MVP

Backend:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 0.0.0.0 --port 8085 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Abrir:

```text
http://127.0.0.1:5178
```

## Testes Manuais Futuros

### Auditoria

- Rodar auditoria em ambiente Klipper real.
- Confirmar que não altera arquivos.
- Confirmar classificação dos achados.
- Validar `GET /api/audit/read-only` com Moonraker real.
- Confirmar que falha de conexão vira `precisa_confirmacao`, não erro fatal.

### Auditoria Do Host

- Validar `GET /api/audit/host-read-only` com `PRINTORA_HOST_AUDIT_MODE=disabled`.
- Validar parser de `systemctl`, CAN, Git e symlinks via testes unitários.
- Validar em Raspberry com `PRINTORA_HOST_AUDIT_MODE=local`.
- Validar em desenvolvimento com `PRINTORA_HOST_AUDIT_MODE=ssh` e chave SSH.
- Confirmar que não há `restart`, `update`, `flash`, `rm`, `mv`, `cp` ou G-code no script read-only.

### Backups

- Criar backup.
- Confirmar arquivos incluídos.
- Confirmar que segredos não vazam.
- Testar restauração por arquivo em ambiente controlado.

### Manutenção

- Criar tarefa preventiva.
- Concluir tarefa.
- Confirmar que evento aparece no diário.
- Confirmar que nenhuma ação foi enviada para Klipper/Moonraker.

### Z-offset

- Registrar primeiro valor de Z-offset para chapa/material/nozzle.
- Registrar segundo valor compatível.
- Confirmar delta e alerta.
- Confirmar que nenhum G-code foi enviado e nenhum arquivo Klipper foi alterado.
- Gerar wizard e confirmar que comandos aparecem apenas como orientação.

### CAN

- Registrar uma leitura manual de `can0` com `rx_error=0`, `tx_error=0` e `tx_retries=0`.
- Registrar nova leitura com `tx_retries` maior e confirmar alerta de monitoramento.
- Registrar nova leitura com `rx_error` ou `tx_error` maior e confirmar alerta de problema.
- Confirmar que o app não executou SSH, `ip`, G-code, restart, update ou flash.

### Mods E Plugins

- Capturar snapshot Moonraker.
- Abrir painel de mods e plugins.
- Confirmar que itens do Update Manager aparecem como detectados.
- Confirmar classificação de KTC-Easy/StealthChanger, KAMP, `led_effect`, Crowsnest, Sonar, Timelapse, Auto Speed, TapChanger e TMC Autotune.
- Confirmar que nenhuma remoção, update, restart ou edição de config foi executada.

### Releases Do Printora

- Iniciar backend com fixture de update disponível:

```bash
PRINTORA_RELEASE_SOURCE_MODE=fixture \
PRINTORA_RELEASE_FIXTURE_PATH=/Users/brenomayder/projects/printora/backend/tests/fixtures/github_releases.json \
PRINTORA_DATA_DIR=/tmp/printora-releases-outdated \
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8091
```

- Abrir `http://127.0.0.1:8091`, entrar em Configurações e confirmar:
  - card `Releases do Printora` aparece;
  - versão instalada aparece;
  - última release aparece como `v0.2.0`;
  - canal aparece como `stable`;
  - status aparece como `update disponível`;
  - changelog resumido aparece;
  - lista de releases de produção aparece;
  - existe botão `Verificar releases`;
  - não existe botão para atualizar/aplicar update.
- Repetir com fixture `github_releases_current.json` e confirmar status `já atualizado`.
- Simular rede indisponível ou rate limit e confirmar que Configurações, Moonraker, Klipper e demais painéis continuam visíveis.
- Confirmar pelo DevTools/log do backend que a tela chama apenas `GET /api/system/releases` ou `GET /api/system/update/status` e não faz `POST`, `PUT` ou `DELETE` para rotas de update.

### Firmware Manager

- Abrir lista de presets.
- Cadastrar uma Octopus USB-CAN bridge com UUID CAN.
- Cadastrar um EBB CAN com UUID CAN.
- Confirmar que MCU, método de flash futuro e arquivo `.config` aparecem no painel.
- Confirmar que nenhum build, flash, SSH, restart ou update foi executado.
- Gerar dry-run de build para uma placa.
- Confirmar checklist, comandos planejados, backup `.config` planejado e caminho do binário.
- Confirmar que nenhum `make`, cópia de arquivo, SSH, restart, update ou flash foi executado.
- Rodar preflight de build para uma placa.
- Confirmar checks de Klipper, Makefile, `.config`, config da placa, `make` e modo local sem criar diretórios ou executar comandos.
- Tentar execução local sem habilitar modo local e confirmar status bloqueado.
- Em ambiente controlado futuro, habilitar modo local e exigir confirmação textual antes de executar build.
- Gerar dry-run de flash para uma placa.
- Confirmar checklist, UUID CAN, interface CAN, binário e comandos planejados.
- Confirmar que nenhum flash, restart, SSH, update ou validação de MCU ao vivo foi executado.
- Rodar preflight de flash para uma placa com a impressora ligada.
- Confirmar Moonraker/Klipper ready, impressão parada, binário/método/UUID e `can_execute_flash=false`.

### Firmware Dry-Run

- Cadastrar placa.
- Selecionar preset.
- Rodar dry-run.
- Confirmar que nenhum flash foi feito.
- Confirmar log completo.

### Firmware Flash

Executar somente em ambiente autorizado.

Critérios:

- impressora parada;
- backup criado;
- UUID validado;
- binário gerado;
- flash concluído;
- MCU voltou;
- Klipper ready.

### Calibração E Testes

- Abrir painel de calibração.
- Confirmar que homing, QGL, probe accuracy, bed mesh, primeira camada, flow, pressure advance, input shaper e testes de qualidade aparecem.
- Confirmar que itens com G-code mostram o código apenas para revisão.
- Confirmar que nenhum botão de execução de G-code existe nesta etapa.

### Navegação Do Frontend

- Abrir `http://127.0.0.1:5178`.
- Confirmar que existe sidebar com Visão geral, Impressoras, Monitoramento, Calibração, Testes, Firmware, Manutenção, Relatórios e Configurações.
- Confirmar que trocar de seção muda os painéis visíveis sem recarregar a página.
- Confirmar que a impressora ativa fica selecionável na topbar.
- Confirmar que a topbar mostra alertas, configuração de impressora e atualização.
- Confirmar que Visão geral mostra decisão operacional e checklist.
- Confirmar que Visão geral mostra dashboard de impressoras.
- Confirmar que `Adicionar impressora` abre modal.
- Confirmar que `Buscar na rede` lista candidatos Moonraker dentro do modal sem cadastrar automaticamente.
- Confirmar que Monitoramento concentra Health Check, CAN, Moonraker, Klipper e auditorias.
- Confirmar que Firmware mostra placas, presets, dry-runs e mods/plugins.
- Confirmar que Calibração mostra Z-offset.
- Confirmar que Testes mostra o centro de testes Voron.
- Confirmar que cada item mostra risco, modo de execução, pré-condições e critérios de sucesso.
- Registrar resultado manual de um teste.
- Confirmar que o histórico mostra status, material, chapa, nozzle, valor observado e notas.
- Com operador presente, revisar G-code, marcar operador presente, informar `EXECUTE_CALIBRATION_GCODE` e executar apenas teste seguro selecionado.
- Confirmar que a execução aparece no histórico com comandos enviados ou motivo de bloqueio.
- Confirmar que a tela de Testes mostra cards por teste, ajuda em modal e execução/registro em modais, sem tutorial técnico fixo na página.
- Em Operação, rodar `Preflight` em ações como Home, QGL, movimento, temperatura, fan e LED.
- Confirmar que o app mostra capacidade, bloqueadores e G-code apenas como preview, sem enviar comando.

### UI

- Abrir app em navegador normal.
- Abrir app pelo Mainsail.
- Validar layout desktop.
- Validar layout no navegador embutido do OrcaSlicer.

### Integração Raspberry

- Rodar `./scripts/install_raspberry.sh` sem `--apply`.
- Confirmar que a saída mostra `DRY-RUN`.
- Confirmar que nenhum serviço foi instalado/iniciado.
- Revisar `packaging/systemd/printora.service`.
- Revisar `packaging/mainsail/navi.json`.
- Revisar `packaging/moonraker/update_manager_printora.conf`.
- Confirmar que `docs/INSTALL_RASPBERRY.md` contém rollback.

### Instalação Multiplataforma

- Rodar `./scripts/run_app.sh --status`.
- Rodar `./scripts/run_app.sh --no-open`.
- Confirmar `GET http://127.0.0.1:8085/health`.
- Rodar `./scripts/run_app.sh --stop`.
- Rodar `./scripts/run_app.sh --foreground --no-open` em terminal dedicado e confirmar que a aplicação permanece online enquanto o processo estiver aberto.
- Rodar `./scripts/bootstrap_dev.sh` sem `--apply`.
- Confirmar que a saída mostra `DRY-RUN`.
- No macOS, confirmar data dir em `~/Library/Application Support/Printora`.
- Revisar `scripts/bootstrap_windows.ps1`.
- Revisar `scripts/run_app_windows.ps1`.
- No Windows, rodar `.\scripts\run_app_windows.ps1 --status`.
- No Windows, abrir `Abrir Printora.bat` e confirmar `GET http://127.0.0.1:8085/health`.
- Revisar `Dockerfile` e `docker-compose.yml`.
- Confirmar que `docs/INSTALL_MULTIPLATFORM.md` documenta macOS, Linux, Windows, Docker, Raspberry e Manta/CB1.

### Updater Do Printora

- Confirmar que `GET /api/system/version` retorna versão do app, caminho de dados e schema aplicado.
- Confirmar que `GET /api/system/releases` funciona com fixture local e com rede indisponível.
- Confirmar que a tela Configurações mostra versão instalada, última release e changelog.
- Chamar `POST /api/system/update/plan` com tag alvo e confirmar que apenas o banco local registra plano/etapas.
- Chamar `GET /api/system/update/history` e `GET /api/system/update/runs/{run_id}` e confirmar que o plano aparece com etapas pendentes.
- Rodar plano de update e confirmar que nenhum arquivo é alterado.
- Confirmar que o plano lista backup do banco, versão alvo, rebuild backend, rebuild frontend, aplicação SQL e restart.
- Executar update em ambiente descartável com banco contendo duas impressoras.
- Confirmar que `printora.db` é preservado e backup `before-update` é criado.
- Confirmar que scripts SQL novos são aplicados uma única vez.
- Confirmar que `/health` responde após o update.
- Confirmar que `/api/printers` mantém as impressoras cadastradas.
- Simular falha durante rebuild frontend e confirmar que o banco original permanece disponível.
- Simular falha durante aplicação SQL e confirmar que o backup do banco está disponível.
- No Android/Termux, confirmar que o updater preserva a porta configurada e reinicia as sessões `tmux`.
- No Android/Termux, validar `scripts/android_update_printora.sh --plan --tag vX.Y.Z` e confirmar JSON parseável sem alteração de arquivos.
- Validar `POST /api/system/update/apply` com confirmação `ATUALIZAR PRINTORA`, tag estável e ambiente Android/Termux, confirmando persistência de run/steps e histórico de sucesso ou falha.
- Confirmar que `POST /api/system/update/apply` rejeita confirmação inválida, tag inválida e ambiente desconhecido.
- Na tela Configurações, confirmar que release disponível mostra `Planejar update`, abre modal de plano, só habilita `Aplicar update` após digitar `ATUALIZAR PRINTORA`, faz polling do run, mostra progresso sem despejar JSON bruto e atualiza releases/histórico automaticamente ao concluir.
- Na tela Configurações, confirmar que `not_supported` exibe mensagem clara e não libera apply quebrado.
- No Android/Termux físico, validar `scripts/android_update_printora.sh --apply --tag vX.Y.Z`, conferindo backup do banco em `~/.local/share/printora/backups`, pasta anterior `~/Printora.previous-update-<timestamp>`, restart das sessões `tmux` e `/health`.
- Validação real Android/Termux em 2026-05-23:
  - aparelho ADB `RXCW10ATDBN`;
  - URL validada `http://printora.local:8069/`;
  - `GET /api/system/releases` retornou `installed_version=0.1.0`, `latest_release_available=true` e release estável `v0.1.1`;
  - `POST /api/system/update/plan` criou run planejado sem alterar arquivos;
  - `POST /api/system/update/apply` retornou run `running` e disparou o script destacado;
  - backup do banco criado em `/data/data/com.termux/files/home/.local/share/printora/backups/printora.db.before-update-20260523T011445Z`;
  - pasta anterior preservada em `/data/data/com.termux/files/home/Printora.previous-update-20260523T011445Z`;
  - `/health` respondeu em `127.0.0.1:8069`, `192.168.15.16:8069` e `printora.local:8069`;
  - `GET /api/system/version` retornou `version=0.1.1` e `schema_revision=18`;
  - banco manteve duas impressoras: `Voron 0.2` e `Voron 2.4`;
  - run 7 ficou `succeeded` diretamente no SQLite, com steps `succeeded`;
  - observação: ao atualizar para uma tag antiga que ainda não contém os endpoints `/api/system/update/*`, o polling HTTP pós-restart pode receber 404; a UI deve orientar recarregar/validar por `/health` e a próxima release versionada deve incluir os endpoints novos.
- No Android/Termux físico, validar rollback com `scripts/android_update_printora.sh --rollback --previous-path ~/Printora.previous-update-<timestamp> --db-backup <backup>`.
- No macOS/Linux/Raspberry, validar `scripts/update_printora.sh --plan --tag vX.Y.Z` com:
  - macOS/local sem systemd;
  - Linux/Raspberry com `printora.service` em systemd;
  - Linux sem systemd com `tmux` ou `scripts/run_app.sh`.
- No macOS/Linux/Raspberry, validar `scripts/update_printora.sh --apply --tag vX.Y.Z` em ambiente descartável, confirmando backup de banco, preservação da pasta anterior, checkout da tag, aplicação de SQL, build frontend e restart sem reiniciar Klipper/Moonraker.
- Validar que backend aplica update em ambiente `unix` com confirmação `ATUALIZAR PRINTORA`, tag estável e histórico persistido.
- Validar rollback Unix com `scripts/update_printora.sh --rollback --previous-path <previous> --db-backup <backup>`.
- No Windows, validar `scripts/update_printora_windows.ps1 --Plan --Tag vX.Y.Z` e confirmar JSON parseável sem alteração de arquivos.
- No Windows, validar `scripts/update_printora_windows.ps1 --Apply --Tag vX.Y.Z` em ambiente descartável, conferindo backup de `%LOCALAPPDATA%\Printora\printora.db`, pasta anterior `Printora.previous-update-<timestamp>`, reinstalação backend/frontend, runner Windows reiniciado e `/health`.
- Validar que backend aplica update em ambiente `windows` com confirmação `ATUALIZAR PRINTORA`, tag estável e histórico persistido.
- Validar rollback Windows com `scripts/update_printora_windows.ps1 --Rollback --PreviousPath <previous> --DbBackup <backup>`.
- Confirmar que o updater Windows usa `ExecutionPolicy Bypass` somente no escopo do processo.
- Validar `POST /api/system/update/rollback`:
  - rejeita confirmação diferente de `ROLLBACK PRINTORA`;
  - rejeita paths relativos, raiz, pasta atual do projeto e nomes que não pareçam backup de update;
  - cria run auditável de rollback;
  - marca o run original como `rolled_back` quando a execução síncrona conclui;
  - mantém histórico e steps anteriores.
- Na tela Configurações, confirmar que histórico mostra runs, detalhes, steps, logs sanitizados e botão `Rollback` somente para run `succeeded` com pasta anterior disponível.
- Confirmar que logs de update não expõem credenciais, chaves SSH, tokens ou senhas.
- Confirmar que rollback exige confirmação explícita e registra histórico.

### Endpoint De Versão Do Sistema

- Iniciar o backend local.
- Chamar `GET http://127.0.0.1:8085/api/system/version`.
- Confirmar que a resposta inclui `app_name`, `version`, `data_dir`, `database_path`, `schema_current`, `applied_sql_scripts` e `latest_validation`.
- Confirmar que `applied_sql_scripts` lista apenas nome do script, ordem de execução e data de aplicação.
- Confirmar que `latest_validation.status` está `ok` e `latest_validation.result` contém `ok`.
- Confirmar que a resposta não inclui conteúdo de tabelas operacionais, payloads JSON do banco, segredos, tokens ou credenciais.

### PKG-20 Validado Em 2026-05-22

Testes automatizados executados:

- `cd backend && . .venv/bin/activate && pytest tests/test_schema_versioning.py`
- `cd backend && . .venv/bin/activate && pytest tests/test_printers.py tests/test_schema_versioning.py`
- `cd backend && . .venv/bin/activate && pytest`
- `./check.sh`

Validação manual/local executada:

- Startup do FastAPI com `PRINTORA_DATA_DIR="$HOME/Library/Application Support/Printora"`.
- Banco validado: `$HOME/Library/Application Support/Printora/printora.db`.
- Impressoras antes do startup: 2.
- Impressoras depois do startup: 2.
- `GET /api/system/version` retornou `schema_current.revision=16` e `latest_validation.status=ok`.
- Resultado: inicialização preservou as impressoras cadastradas e aplicou o schema versionado sem perda de dados.

## Critérios Para Não Avançar

Não avançar se:

- `./check.sh` falhar;
- houver risco de flash sem confirmação;
- houver alteração de config sem backup;
- relatório expuser segredo;
- app não conseguir distinguir leitura de mutação.
