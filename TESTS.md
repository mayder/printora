# TESTS.md

## Objetivo

Definir validações mínimas para o Printora.

## Check Local

Comando obrigatório antes de commit:

```bash
./check.sh
```

O check inicial valida:

- existência dos documentos principais;
- ausência de marcadores básicos de segredo;
- formato básico do `CODEX_PATHS.toml`;
- compilação sintática do backend Python;
- validade do `frontend/package.json`;
- permissão executável do `check.sh`.

## Banco Local

Mudanças de banco devem ser feitas por scripts `.sql` idempotentes em `backend/sql/`.

Validações:

- `initialize_database()` pode rodar mais de uma vez;
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

Testes automatizados adicionais:

```bash
cd backend
. .venv/bin/activate
pytest
```

```bash
cd frontend
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

## Critérios Para Não Avançar

Não avançar se:

- `./check.sh` falhar;
- houver risco de flash sem confirmação;
- houver alteração de config sem backup;
- relatório expuser segredo;
- app não conseguir distinguir leitura de mutação.
