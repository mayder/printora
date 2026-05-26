# BUGS.md

## Bugs Conhecidos

Nenhum bug aberto de implementação registrado.

## Bugs Corrigidos

### Firmware Duplicava Placa Detectada E Navegacao Mantinha Painel Antigo

Sintoma:

- ao associar uma MCU detectada ao modelo fisico, a tela Firmware passava a mostrar a placa cadastrada e a mesma MCU detectada como se fosse outra placa;
- em alguns fluxos, depois de abrir Diagnostico da instalacao, clicar em Calibracao, Testes, Firmware ou Manutencao podia manter o painel anterior visivel.

Causa:

- o inventario comparava placa cadastrada e MCU detectada principalmente pelo nome de MCU/preset, sem casar UUID CAN e nome exibido pelo Klipper;
- a SPA renderizava todas as telas ao mesmo tempo e dependia de CSS para ocultar as inativas.

Correção:

- inventario de firmware agora deduplica placas cadastradas por UUID CAN, nome exibido e MCU;
- cadastro de placa ficou idempotente por UUID CAN ou nome dentro da mesma impressora;
- seletor de Modelo fisico sempre mantém todos os presets disponíveis, priorizando os sugeridos sem esconder os demais;
- shell renderiza somente a tela ativa.

Validação:

- testes focados de firmware;
- build do frontend.

### Instalacao Falhava Com Python Antigo Ou Update Orfao

Sintoma:

- em macOS com Python global antigo, a instalacao criava `backend/.venv` com Python incompatível e falhava no backend;
- algumas instrucoes e scripts ainda apontavam para `8085`, enquanto a porta operacional combinada era `8069`;
- update interrompido podia permanecer como `em execução` e bloquear novas versoes ate intervencao manual no SQLite.

Causa:

- selecao de Python considerava primeiro `python3`, sem validar `>=3.11`;
- venv antiga nao era recriada automaticamente;
- recuperacao de update orfao existia no backend, mas faltava acao explicita para o usuario e script operacional oficial.

Correção:

- scripts passam a selecionar Python `3.11+`, preservando Python antigo do usuario;
- venv local incompatível e recriada;
- padrao `8069` aplicado em scripts, docs, frontend e empacotamento;
- adicionados `scripts/doctor_install.sh`, `scripts/unlock_update.sh`, endpoint de reconciliacao e botao `Reconciliar travados`.

Validação:

- teste automatizado do endpoint `POST /api/system/update/reconcile`;
- `./check.sh`.

### Update Do Printora Ficava Travado Em Execucao Apos Reboot

Sintoma:

- apos update do Printora em Raspberry, desligar/religar a maquina podia deixar um run antigo como `em execução`;
- mesmo com a versão instalada já atualizada, uma nova tentativa de update era bloqueada por `Já existe update em execução`.

Causa:

- o histórico persistido dependia do script finalizar e marcar o run como concluído;
- reboot ou queda de energia durante o script podia interromper a marcação final, mantendo o registro `running` no SQLite.

Correção:

- endpoints de histórico, detalhe, apply e rollback reconciliam runs `running` antes de responder;
- se a versão instalada já corresponde ao alvo do run, o registro órfão é fechado como `succeeded`;
- se a versão não corresponde ao alvo, o registro só é fechado como `failed` quando estiver antigo o suficiente para ser considerado órfão.

Validação:

- `pytest tests/test_update_self.py -q` no backend;
- `./check.sh`.

### Cadastro De Impressora Exibia Failed To Fetch

Sintoma:

- ao abrir o frontend local sem API acessível, a busca de impressoras mostrava apenas `Failed to fetch`;
- em inicializações fora dos scripts oficiais, o backend podia usar o diretório SQLite Linux no macOS e abrir sem as impressoras já cadastradas.

Causa:

- a configuração padrão do backend não acompanhava o diretório operacional usado pelos runners no macOS;
- a UI repassava o erro técnico cru do `fetch` para o operador.

Correção:

- o `data_dir` padrão agora usa `~/Library/Application Support/Printora` no macOS, `%LOCALAPPDATA%/Printora` no Windows e `~/.local/share/printora` no Linux;
- erros de rede do frontend passam a orientar verificar o backend em `http://127.0.0.1:8069`.

Validação:

- `pytest tests/test_schema_versioning.py tests/test_printers.py tests/test_discovery.py -q`;
- `npm --prefix frontend run build`;
- `./check.sh`;
- smoke local em `GET /api/printers` e `GET /api/printers/discover`.

### Tela De Atualizacoes Nao Revalidava Apos Fechar Modal

Sintoma:

- depois de um update chegar ao fim no modal, fechar a janela podia deixar a tela com estado antigo ate recarregar o navegador;
- `Atualizar tudo` continuava aparecendo mesmo com zero ou apenas um componente atualizavel;
- lista de componentes e checklist pos-update ocupavam largura demais em telas grandes.

Causa:

- o fechamento do modal apenas encerrava a janela, sem revalidar o contexto vivo da impressora;
- a acao global nao considerava a quantidade de itens atualizaveis;
- a tela usava linhas em largura total para todos os componentes.

Correção:

- fechamento do modal passou a recarregar Update Manager, health, checklist, operacao e auditoria;
- confirmacao pos-update aguarda revalidacoes do Moonraker antes de marcar o fluxo como concluido;
- `Atualizar tudo` aparece somente com mais de um item atualizavel;
- componentes viraram cards responsivos e o checklist pos-update ocupa a largura total com duas colunas quando houver espaco.

Validação:

- `npm run build` no frontend.

### Menus De Impressora Online Visiveis Com Moonraker Offline

Sintoma:

- quando a impressora ativa estava desligada, o menu ainda exibia secoes que dependem do Moonraker online, como operacao, monitoramento, atualizacoes, calibracao, testes, firmware e relatorios.

Causa:

- a navegacao verificava apenas se havia impressora selecionada, sem considerar o estado real de conectividade retornado pelo health da impressora ativa.

Correção:

- a regra de navegacao passou a diferenciar impressora nao selecionada, conectividade desconhecida, online e offline;
- secoes que exigem Moonraker online ficam ocultas quando o health confirma offline;
- se uma dessas secoes estiver ativa e a impressora ficar offline, a SPA retorna para `overview`.

Validação:

- `npm run build` no frontend.

### Alertas Inflados Com Impressora Offline

Sintoma:

- com Moonraker offline, a Central de alertas ainda contava checklist, auditoria e achados de snapshot antigo como alertas ativos da impressora.

Causa:

- a UI consolidava todos os itens carregados sem diferenciar alerta do estado atual offline de pendencias que exigem a impressora ligada para validação.

Correção:

- quando o health confirma impressora offline, a Central mostra apenas o alerta de offline/conexão;
- alertas dependentes de leitura ao vivo ou snapshot antigo ficam ocultos ate a conexão voltar;
- os contadores da Home passaram a usar a lista efetiva de alertas exibidos.

Validação:

- `npm run build` no frontend.

### Alerta Vermelho Sem Causa Acionavel Na Home

Sintoma:

- a Home mostrava `Nao imprimir`, mas o operador precisava abrir a Central de alertas e interpretar listas tecnicas para saber qual bloqueio estava ativo e como agir.

Causa:

- a tela resumia apenas contadores de bloqueios/alertas e a Central exibia detalhe e acao como texto livre, sem separar causa, evidencia, orientacao e acao do sistema.

Correção:

- a Home passou a destacar o bloqueio ou alerta principal;
- a Central de alertas passou a exibir `Por que aparece`, `Evidencia`, `Como resolver` e botoes de acao por item;
- itens de health/checklist podem ser revalidados, updates podem abrir o fluxo do Update Manager e itens manuais abrem o diagnostico.

Validação:

- `npm run build` no frontend.

### Timeout No Envio De G-code De Calibração

Sintoma:

- a UI marcava falha ao enviar G-code mesmo quando a impressora recebia e executava o comando.

Causa provável:

- timeout/erro de transporte do POST para `/printer/gcode/script` era tratado como falha definitiva sem consultar o estado final do Moonraker/Klipper.

Correção:

- após cada envio, o backend monitora o estado final da impressora e registra o retorno final; se a impressora fica `ready`, o comando é tratado como confirmado.

Validação:

- teste automatizado cobre timeout após aceitação do comando e confirmação posterior por estado final.

## Riscos Técnicos Acompanhar

### Cache De Navegadores Embutidos

Apps abertos pelo OrcaSlicer podem manter cache agressivo e service worker antigo.

Impacto:

- mudanças de UI podem demorar a aparecer;
- links externos podem prender o usuário fora do Mainsail.

Mitigação:

- versionar assets;
- evitar dependência de hack em frontend de terceiros;
- preferir app próprio com rota de retorno clara.

### Firmware Flash

Flash incorreto pode deixar MCU fora do CAN.

Mitigação:

- dry-run;
- backup;
- UUID antes/depois;
- rollback documentado;
- confirmação explícita.

### Detecção De Plugins

Plugins podem estar instalados, mas não ativos.

Mitigação:

- diferenciar repo instalado, include ativo, módulo Python ativo e serviço systemd ativo.

### Relatórios Sanitizados

Logs podem conter dados sensíveis.

Mitigação:

- sanitização obrigatória;
- preview antes de exportar.

### Updater Do Próprio Printora

Atualizar backend, frontend e schema a partir da própria aplicação pode deixar o ambiente parcialmente atualizado se houver falha no meio do processo.

Durante o update real no Android/Termux, a conexão HTTP que disparou `POST /api/system/update/apply` pode cair quando as sessões `tmux` forem reiniciadas, mesmo que o script finalize com sucesso.

Validação real em 2026-05-23 encontrou e corrigiu um caso pior: quando o script era executado como filho direto do backend dentro do `tmux printora`, o `tmux kill-session -t printora` podia encerrar também o processo do update antes de marcar o run como `succeeded`.

Rollback é operação destrutiva sobre a pasta atual do projeto e pode restaurar um binário/código que ainda não contém os endpoints novos de histórico. O histórico SQLite não deve ser apagado e a UI deve tolerar queda de conexão durante restart.

Mitigação:

- plano read-only antes de aplicar;
- backup obrigatório do `printora.db`;
- execução Android destacada do processo web antes do restart;
- progresso persistido por etapa;
- rollback explícito;
- rollback exige `ROLLBACK PRINTORA`, paths absolutos seguros e backup gerado pelo updater;
- logs sanitizados.
- UI deve orientar recarregar e consultar `/api/system/update/history` após queda de conexão durante restart.

### GitHub Releases Rate Limit E Cache

Consulta pública ao GitHub Releases pode sofrer rate limit, ficar offline ou retornar dados defasados por cache intermediário.

Impacto:

- tela Configurações pode mostrar `limite do GitHub`, `GitHub offline` ou uma release antiga temporariamente;
- operador pode achar que não há update quando a resposta pública ainda não propagou.

Mitigação:

- consulta é read-only e não bloqueia o restante da tela;
- não há token obrigatório para repositório público;
- UI mantém botão manual `Verificar releases`;
- payload expõe `status`, `update_status` e erro resumido para diagnóstico;
- update real permanece fora do PKG-21.

### Versionamento De Schema SQLite

Aplicar scripts SQL novos em um banco local real pode falhar por corrupção prévia, arquivo bloqueado ou SQL inválido.

Mitigação:

- backup automático de `printora.db` antes de scripts pendentes;
- restauração automática do banco original em falha de aplicação;
- `PRAGMA integrity_check` obrigatório após schema;
- histórico em `schema_versions`, `app_version` e `schema_integrity_checks`.

Rollback:

- parar o app;
- restaurar o backup `printora.<timestamp>.before-schema.db` para `printora.db`;
- reiniciar o app e validar `GET /api/system/version`.
