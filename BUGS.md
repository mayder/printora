# BUGS.md

## Bugs Conhecidos

Nenhum bug aberto de implementação registrado.

## Bugs Corrigidos

### Operacao Concluida Nao Mostrava A Ultima Impressao

Sintoma:

- ao terminar uma impressao, a aba Operacao passava para `complete`, mas o card `Impressao` exibia apenas estado generico/lista curta de G-codes;
- o operador perdia o preview 3D e os dados finais da peca recem-impressa.

Causa:

- o frontend tratava `complete` como estado ocioso comum;
- o contrato de G-code usado na lista curta nao preservava `print_end_time`, reduzindo a confiabilidade para escolher o ultimo trabalho concluido.

Correcao:

- `complete` agora seleciona o G-code da operacao finalizada, ou o ultimo arquivo confiavel quando o nome ativo nao estiver disponivel;
- o preview usa o viewer 3D em modo completo e apresenta camada/progresso finais;
- backend e agente preservam `print_end_time` na lista compacta de G-codes.

Validacao:

- `cd backend && uv run --extra dev pytest tests/test_operation.py tests/test_gcode_files.py -q`;
- `cd agent && go test ./internal/agent`;
- `npm --prefix frontend run build`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### Preview De Impressao Avancava Durante QGL Sem Material

Sintoma:

- ao iniciar uma impressao, durante QGL/preparo, o card `Impressao` podia mostrar camadas futuras como ja impressas;
- o problema aparecia mesmo com `display` em 0% e `filamento` em 0 mm.

Causa:

- backend, frontend e agente aceitavam camada informada/estimada quando `print_stats.state=printing`, mesmo antes de qualquer extrusao real;
- o viewer tambem podia tratar progresso ausente como arquivo completo.

Correcao:

- camada e posicao do G-code agora so movimentam a previa quando existe progresso material por filamento ou progresso real do display;
- mensagens de preparo como QGL, homing e bed mesh preservam total de camadas/thumbnail, mas bloqueiam `layer_preview` ate a primeira extrusao;
- o viewer passa a iniciar em zero quando nao ha progresso valido.

Validacao:

- `cd backend && uv run --extra dev pytest tests/test_operation.py -q`;
- `cd agent && go test ./...`;
- `npm --prefix frontend run build`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### Lateral Do Preview De Impressao Ficava Vazia E Truncava Titulos

Sintoma:

- no card `Impressao`, o lado direito deixava area vazia ao lado/abaixo da imagem do modelo;
- os titulos da previsualizacao apareciam abreviados como `T...` e `Ca...`, mesmo com espaco disponivel.

Causa:

- o thumbnail era renderizado como bloco isolado e competia mal com a lista de fatos;
- os titulos do `PrintVisual` usavam limite percentual fixo, encolhendo textos curtos em larguras intermediarias.

Correcao:

- a lateral direita passou a combinar thumbnail, progresso, fatos principais, metadados e Machine em uma composicao mais densa;
- os titulos do visual passaram a usar largura natural quando houver espaco.

Validacao:

- `cd frontend && npm run build`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### Preview 3D Em 100 Por Cento Continuava Parecendo Parcial

Sintoma:

- com a impressao concluida, o card `Impressao` ainda mostrava a cena 3D como poucas linhas;
- thumbnail e cena competiam pela area principal, deixando a cena menor e criando buracos na composicao.

Causa:

- o agente limitava a previsualizacao interativa a uma amostra pequena do G-code;
- o layout tratava thumbnail e cena como visuais equivalentes, em vez de usar a cena como area principal e o thumbnail como apoio.

Correcao:

- agente 0.1.28 aumenta o cache de segmentos do G-code e envia uma amostra interativa mais densa dentro do limite seguro de payload;
- o card `Impressao` passa a renderizar a cena 3D como painel principal e move o thumbnail para a lateral direita com os dados da impressao;
- em impressao completa, o material ja impresso ganha mais contraste para nao parecer apenas a camada atual.

Validacao:

- `cd agent && go test ./...`;
- `cd frontend && npm run build`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### Preview 3D Da Operacao Sobrepunha Controles E Texto

Sintoma:

- no card `Impressão`, os controles de rotação/zoom ficavam sobre textos de estado da prévia;
- o navegador 3D aparecia grudado em contador de segmentos;
- em larguras intermediárias, thumbnail, cena de camada e dados da impressão ficavam comprimidos e a cena parecia um emaranhado de linhas.

Causa:

- a prévia usava a mesma área absoluta para botões, notas e contador;
- a cena renderizava o material impresso e a camada atual só como linhas, com pouca diferença visual entre histórico e camada corrente;
- o grid do card mantinha três blocos lado a lado mesmo quando a largura útil já estava reduzida.

Correção:

- controles, navegador e nota parcial passaram a ocupar áreas separadas;
- o viewer reduz o peso das linhas antigas, mantém o material já impresso discreto e destaca a camada atual;
- a grade de `Impressão` empilha fatos/Machine em larguras intermediárias e evita compressão/overlap.

Validação:

- `npm --prefix frontend run build`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### Operacao Ficava Vazia Durante Impressao Com Preview Do G-code

Sintoma:

- durante uma impressao ativa, a aba Operacao mostrava agente online no topo, mas o painel em tempo real ficava como Moonraker offline/sem leitura;
- requests de status podiam ficar pendentes e terminar sem restaurar temperaturas, progresso, thumbnail e Miscellaneous.

Causa:

- `remote_operation_status` passou a incluir thumbnail, camada e cena derivada do G-code;
- respostas de job com dados visuais podiam ultrapassar 64 KB;
- o backend aplicava o mesmo limite de payload de comando ao resultado do job do agente e rejeitava a resposta com 413.

Correção:

- o limite de comando/snapshot permanece em 64 KB;
- resultados de job do agente passam a aceitar ate 512 KB, suficiente para respostas operacionais com preview visual controlado.

Validação:

- `cd backend && uv run --extra dev pytest tests/test_agent_channel.py tests/test_operation.py tests/test_agent_executor.py -q`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### Timeout Da Operacao Parecia Instantaneo

Sintoma:

- a aba Operacao podia mostrar indisponibilidade/timeout muito rapido depois de atualizar;
- quando o WebSocket do agente nao confirmava entrega, a leitura ficava dependente do polling de 10s do agente e podia estourar a janela de 10s da rota;
- falhas rapidas do job do agente ficavam visualmente parecidas com timeout real.

Causa:

- o executor do agente ignorava se o job foi entregue por WebSocket ou ficou apenas enfileirado para polling;
- a rota de Operacao usava a mesma janela curta de leituras simples, mesmo depois de incluir metadata e previsualizacao de G-code;
- a tela recebia mensagens derivadas de `HTTPException` sem contexto suficiente do estado do job.

Correção:

- o executor agora diferencia timeout com job pendente, polling sem entrega via WebSocket e job em andamento;
- a rota de Operacao usa janela maior para `remote_operation_status`, cobrindo polling + leitura pesada;
- mensagens de indisponibilidade foram sanitizadas para explicar o estado sem expor `504` bruto.

Validação:

- `cd backend && uv run --extra dev pytest tests/test_operation.py -q`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### Operacao Offline Mostrava Timeout Cru E Paineis Vazios Grandes

Sintoma:

- quando o agente demorava para responder, a aba Operacao exibia `504: timeout aguardando resposta do agente`;
- sem thumbnail ou previsualizacao de camada, o card de Impressao mantinha dois blocos altos vazios e criava buracos na tela.

Causa:

- o backend propagava `str(HTTPException)`, incluindo o codigo HTTP na mensagem de produto;
- o frontend sempre montava a grade visual de Impressao, mesmo quando nao havia dado renderizavel.

Correção:

- o backend sanitiza timeout do agente em mensagem operacional curta;
- a aba Operacao mostra estado compacto quando nao recebe thumbnail/camada/cena do G-code;
- o aviso offline usa estado informativo, sem alerta bruto de infraestrutura.

Validação:

- `cd backend && uv run --extra dev pytest tests/test_operation.py -q`;
- `npm --prefix frontend run build`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### Progresso Da Operacao Perdeu Precisao Do Display E Faltava Metadata Da Peca

Sintoma:

- a aba Operacao passou a mostrar o percentual igual ao Mainsail, adiantado em relacao ao display da impressora;
- o card de Impressao mostrava poucos detalhes da peca em andamento, sem estimativa, restante, camada total/current quando o `print_stats` nao entregava esses campos.

Causa:

- o progresso principal estava priorizando `virtual_sdcard.progress`;
- o agente nao buscava a metadata do G-code atual via `print_stats.filename`, entao o backend nao tinha `estimated_time`, slicer, filamento, altura/camada e dados para fallback de camada.

Correção:

- agente 0.1.24 busca `/server/files/metadata?filename=<arquivo>` quando ha impressao carregada;
- Operacao voltou a priorizar `display_status.progress` como percentual principal e manteve `virtual_sdcard.progress` como progresso de arquivo;
- card de Impressao exibe tempo restante, conclusao estimada, estimativa, progresso de arquivo, filamento, slicer, material e camada derivada de metadata/Z quando necessario.

Validação:

- `cd agent && go test ./...`;
- `cd backend && uv run --extra dev pytest tests/test_operation.py tests/test_agent_updates.py tests/test_agent_install.py tests/test_agent_support.py -q`;
- `npm --prefix frontend run build`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### Agente Nao Entregava Valores De Miscellaneous Com Objetos Dinamicos

Sintoma:

- a aba Operacao detectava objetos Miscellaneous como `T0 Partfan`, `Nevermore`, `Controller Fan` e `Caselight`, mas nao recebia os valores para renderizar controles/leitura.

Causa:

- a query dinamica do agente usava codificacao menos tolerante para nomes de objetos Klipper com espacos;
- fans e output pins dinamicos eram consultados com campos especificos, o que deixava o coletor mais fragil contra variacoes de objeto/field retornadas pelo Moonraker.

Correção:

- agente 0.1.23 consulta objetos dinamicos com `%20` em nomes com espaco;
- fans e output pins dinamicos passam a ser consultados sem restringir campos, preservando `speed`/`value` quando o Moonraker os retorna.

Validação:

- `cd agent && go test ./...`;
- `cd backend && uv run --extra dev pytest tests/test_agent_updates.py tests/test_agent_install.py tests/test_agent_support.py tests/test_operation.py -q`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### Miscellaneous Ficava Vazio Quando O Agente Nao Entregava Status Dinamico

Sintoma:

- a aba Operacao mostrava `Nenhum fan, luz ou LED retornado pelo Moonraker`, mesmo com Caselight/fans visiveis no Mainsail.

Causa:

- o backend renderizava Miscellaneous apenas a partir de valores em `status`;
- quando a lista dinamica de objetos nao vinha do agente, ou quando objetos eram detectados sem valores, a UI tratava como se nao existisse nada configurado.

Correção:

- o contrato de Operacao agora informa `collection_state`, objetos detectados e objetos sem leitura de status;
- a UI mostra estado acionavel quando o agente nao entregou a lista dinamica ou quando detectou objetos sem valores.

Validação:

- `cd backend && uv run --extra dev pytest tests/test_operation.py -q`;
- `npm --prefix frontend run build`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### KPIs Da Operacao Ficavam Encostados No Bloco De Baixo

Sintoma:

- na aba Operacao do detalhe da impressora, a faixa de KPIs ao vivo ficava colada no card de Temperaturas/Impressao.

Causa:

- o `display:grid` e o `gap` do dashboard estavam escopados apenas para `.section-monitoring`;
- quando o mesmo componente abria dentro de `.section-printer-detail`, a regra global `.section-printer-detail .panel-section` tinha mais especificidade e mantinha o painel como bloco sem `gap`.

Correção:

- o layout base de `.monitoring-dashboard` passou a ter seletor especifico tambem para `.section-printer-detail`.

Validação:

- `npm --prefix frontend run build`;
- `./check.sh`.

### Lista De Impressoras Bloqueava Acoes Por Loading Global

Sintoma:

- ao abrir Impressoras com uma Voron offline validando agente, os botoes de `Detalhar` da Voron offline e da Voron online ficavam desabilitados;
- o loading exibido no refresh do badge `Agente offline` segurava a lista inteira.

Causa:

- a tela usava o `loading` global da aplicacao para todos os botoes de todos os cards.

Correção:

- acoes de card usam busy local por `printer.id` e tipo de acao;
- `Detalhar`, `Editar` e `Contexto rapido` nao dependem mais do loading de outra impressora;
- refresh de agente, leitura de status e snapshot mostram busy apenas no card acionado.

Validação:

- `npm --prefix frontend run build`;
- `./check.sh`.

### Miscellaneous Da Operacao Nao Refletia Mainsail

Sintoma:

- Caselight aparecia no Printora como LED manual vazio/0%, enquanto no Mainsail estava ligado em 25%;
- fans `fan_generic`, `heater_fan` e `controller_fan` nao apareciam no painel Miscellaneous;
- acao leve de luz/fan podia pedir autenticacao reforcada ou parecer timeout logo apos o clique.

Causa:

- o agente consultava apenas objetos fixos e nao trazia `output_pin`, fans dinamicos e LEDs reais do Moonraker;
- o frontend dependia de um campo manual de LED em vez de renderizar os objetos vivos;
- o endpoint de execucao direta exigia step-up para qualquer acao autenticada.

Correção:

- agente 0.1.22 coleta objetos Mainsail-like de Miscellaneous: `output_pin`, `fan_generic`, `heater_fan`, `controller_fan` e LEDs;
- Operacao classifica Caselight/output pins, fans controlaveis, fans somente leitura e indicadores LED;
- acoes leves `set_fan`, `set_output_pin` e `set_led` nao exigem step-up e podem rodar durante impressao.

Validação:

- `cd backend && uv run --extra dev pytest tests/test_operation.py tests/test_agent_updates.py tests/test_agent_install.py tests/test_agent_support.py -q`;
- `cd agent && go test ./...`;
- `npm --prefix frontend run build`.

### Grafico De Temperatura Da Operacao Ficava Sem Serie

Sintoma:

- durante impressao, a tabela da Operacao mostrava temperaturas corretas, mas o grafico permanecia sem linha;
- o progresso podia seguir uma leitura adiantada de display em vez do progresso real do arquivo virtual.

Causa:

- a tela substituia o status ao vivo a cada refresh e nao acumulava historico local de temperatura;
- quando havia apenas uma leitura, o SVG gerava `polyline` com um unico ponto, que nao desenha linha visivel;
- o backend lia `display_status.progress` antes de considerar `virtual_sdcard.progress`.

Correção:

- a Operacao passa a manter historico local das leituras ao vivo durante a sessao aberta;
- uma leitura isolada desenha linha horizontal para evitar grafico aparentemente vazio;
- o progresso prioriza `virtual_sdcard.progress` e usa `display_status.progress` apenas como fallback.

Validação:

- `cd backend && uv run --extra dev pytest tests/test_operation.py -q`;
- `npm --prefix frontend run build`;
- `./check.sh`.

### Metrica De CPU Do Agente Inflava Consumo

Sintoma:

- a tela de detalhe do agente podia mostrar `printora-agent` consumindo CPU alto em idle, como ~9%, enquanto Moonraker/Klipper apareciam zerados.

Causa:

- o coletor calculava CPU com duas leituras de `/proc` em uma janela curta de 200 ms;
- em Raspberry, o trabalho da própria coleta podia entrar nessa janela e inflar o percentual do processo `printora-agent`.

Correção:

- a coleta passa a guardar a amostra anterior de processos e calcular CPU pelo delta real entre snapshots cacheados;
- a pausa artificial de 200 ms foi removida;
- a primeira coleta não sintetiza percentual de CPU quando ainda não há amostra anterior.

Validação:

- `cd agent && go test ./...`;
- `npm --prefix frontend run build`;
- `./check.sh`.

### Social Travava E Sessao Piscava Login

Sintoma:

- a tela Social demorava para carregar e podia derrubar a navegacao;
- apos F5, a aplicacao podia mostrar login antes de restaurar a sessao e voltar sozinha para Social;
- catalogo, comunidades e makers pareciam sumir quando o backend ficava sem responder.

Causa:

- endpoints publicos de leitura social sincronizavam comunidades e feed padrao no SQLite a cada consulta;
- com concorrencia, essas escritas podiam disputar lock e bloquear o worker unico do backend;
- o frontend renderizava a tela de login enquanto ainda validava token salvo.

Correção:

- sincronizacao de comunidades/feed movida para startup e mutacoes de catalogo/publicacao de impressora;
- leituras sociais passam a consultar dados ja materializados sem escrita por refresh;
- restauracao de sessao ganhou estado explicito antes de exibir login;
- bootstrap da sessao evita carregamento duplicado para o mesmo usuario.

Validação:

- `cd backend && uv run --extra dev pytest ../backend/tests/test_social_catalog.py -q`;
- `cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q`;
- `npm --prefix frontend run build`;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

### Modal Do Updater Ficava Preso Apos Restart

Sintoma:

- durante update Android/Termux, o backend concluia o update, mas a modal podia ficar parada em estado antigo ate recarregar a pagina.

Causa:

- o polling parava na primeira queda de conexao durante o restart e orientava recarregar manualmente.

Correção:

- a tela continua tentando consultar releases, historico e run apos queda temporaria;
- quando detecta a versao alvo instalada, atualiza o modal e o historico sem reload manual.

Validação:

- `npm --prefix frontend run test:releases`;
- `npm --prefix frontend run build`;
- `./check.sh`.

### Updater Raspberry Marcava Sucesso Antes De Restart Sem Permissao

Sintoma:

- em Raspberry com `printora.service` como systemd de sistema, o update podia instalar `printora-backend` novo, marcar o run como concluido, mas manter o app antigo online;
- o terminal mostrava `Failed to restart printora.service: Interactive authentication required`.
- instalacoes futuras ainda dependeriam de ajuste manual de sudoers para o app reiniciar a si mesmo.

Causa:

- o script tratava todo restart systemd como etapa auto-finalizante, mas nao validava antes se o processo tinha permissao nao interativa para reiniciar o servico.
- o instalador Linux/Raspberry nao criava a permissao minima de restart/status do `printora.service` para o usuario do servico.

Correção:

- restart systemd de sistema agora usa `sudo -n systemctl restart printora.service` quando nao roda como root;
- antes de marcar o run como concluido, o script valida `sudo -n -v`;
- se o host exige autenticacao interativa, o update falha com comando manual claro em vez de fingir sucesso.
- instaladores Linux/Raspberry criam `/etc/sudoers.d/printora-restart` validado por `visudo -cf`;
- `doctor_install.sh` avisa quando essa regra estiver ausente.

Validação:

- `backend/.venv/bin/pytest tests/test_unix_update_script.py -q`;
- `bash -n scripts/update_printora.sh`.

### Diagnostico Nao Mostrava Throttling Da Raspberry

Sintoma:

- em Raspberry, o operador nao tinha um sinal direto no Printora para saber se o raio/undervoltage/throttling estava normal, ativo ou apenas registrado no passado.

Causa:

- o diagnostico de instalacao verificava dependencias, porta, banco e updates, mas nao consultava `vcgencmd get_throttled`.

Correção:

- `GET /api/system/install-diagnostics` passa a incluir o item `raspberry_throttling`;
- em Raspberry com `vcgencmd`, o bitmask oficial e decodificado em `ok`, `warning` ou `error`;
- em host que nao e Raspberry, o check aparece como nao aplicavel sem gerar alerta.

Validação:

- `backend/.venv/bin/pytest tests/test_install_diagnostics.py -q`.

### Updater Bloqueava Tag Estavel Quando Consulta De Releases Falhava

Sintoma:

- update para uma tag estavel existente podia falhar com `Tag não pertence às releases estáveis disponíveis`;
- quando o app reiniciava durante update destacado, faltava um arquivo de log direto para suporte.
- em Raspberry/systemd, o update podia aplicar a nova versao, mas ficar preso em `restart_app` ate reconciliacao manual.

Causa:

- o backend exigia que a tag estivesse na lista carregada por `GET /api/system/releases`, mesmo quando a consulta ao GitHub estava indisponivel, desabilitada ou temporariamente defasada;
- execucoes destacadas do updater descartavam stdout/stderr em `/dev/null`.
- o `systemctl restart printora.service` podia encerrar o proprio processo do updater antes de marcar o run como concluido.

Correção:

- quando a consulta de releases nao esta `ok`, o backend aceita apenas tag estrita `vX.Y.Z` e deixa o script oficial validar a existencia da tag no remoto;
- updates e rollbacks destacados passam a gravar log em `~/.local/share/printora/logs/self-update-run-<id>.log`.
- no modo Unix/systemd, o script marca `restart_app` como concluido, `validate_health` como pulado e finaliza o run antes de solicitar o restart do servico.

Validação:

- `backend/.venv/bin/pytest tests/test_update_self.py -q`;
- `./check.sh`.

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

### Flash Supervisionado Sem Validação Em Hardware Real

Impacto:

- o PKG-37 está implementado e validado por testes locais, mas ainda não foi executado em uma BTT Pi/U2C/MCU real acompanhada;
- o fluxo deve ser tratado como pronto para validação operacional, não como homologado em campo.

Mitigação:

- execução real bloqueada por `PRINTORA_REMOTE_FLASH_MODE=remote`;
- exigir checklist, preflight aprovado, UUID visível e frase específica;
- começar apenas pelo método CAN/Katapult;
- seguir rollback manual exibido em caso de falha ou estado inconclusivo.

### Validação Final Sem Hardware Real

Impacto:

- a validação final foi implementada e testada com fixtures locais, mas ainda não foi executada em Pi/U2C/MCUs reais acompanhadas;
- o relatório local prova contrato e segurança do software, não homologação de campo.

Mitigação:

- fluxo estritamente read-only;
- relatório sanitizado;
- estados distinguem bloqueado, intervenção manual, aprovado com observação e aprovado para calibração;
- validar em hardware real antes de usar como aceite operacional definitivo.

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

### Restore PostgreSQL Pode Saturar O Disco Compartilhado

Um restore físico sem limite de I/O no mesmo host elevou a latência do processo
web durante a validação de 2026-07-22. O backup permaneceu íntegro, mas o ensaio
precisou ser interrompido e repetido com limite de leitura/escrita.

Mitigação:

- restaurar somente base, dump, manifesto e o WAL final necessário;
- executar o cluster temporário com CPU e I/O limitados por systemd;
- usar `fsync=off` somente no cluster efêmero descartável de validação;
- encerrar o cluster efêmero sem checkpoint e remover apenas o diretório exato;
- monitorar `/health` público e interromper somente o ensaio se passar de 5 s;
- nunca reduzir durabilidade do cluster PostgreSQL de produção.

### Agente Alterado Sem Nova Versão Pública

Impacto:

- o código do agente recebeu alterações de reconnect/blue-green depois do
  artefato `0.1.33`;
- o manifesto e o SHA-256 público continuam apontando ao binário anterior;
- agentes instalados não recebem essas alterações como uma nova versão.

Mitigação:

- resolver no `PKG-96` com versão `0.1.34`, build reproduzível, assinatura,
  canário real, rollback e atualização do manifesto;
- nunca substituir conteúdo mantendo o mesmo número de versão.

### Gate Frontend Aceita Node Não Suportado E Cobertura Zero

Impacto:

- Vite avisa que Node 18 não é suportado, mas o build pode encerrar com sucesso;
- cobertura mínima está desativada e não bloqueia regressão;
- os testes frontend atuais não equivalem a uma suíte E2E completa.

Mitigação:

- resolver no `PKG-97`;
- falhar antes do build com Node incompatível;
- ativar cobertura, E2E, fuzzing, mutation testing e pentest independente.
