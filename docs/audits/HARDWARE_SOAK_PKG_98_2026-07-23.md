# PKG-98 - Homologação física e soak

Data de abertura: 2026-07-23
Estado: em execução

## Escopo físico e baseline

- Impressora de validação: Voron 0.2, registrada como `Voron 0.2 · Casa`.
- Agente: `0.1.34`, online e com doctor remoto saudável.
- Estado inicial confirmado pela UI em 2026-07-23T20:41Z:
  - Moonraker online `v0.10.0-20-g9008485`;
  - Klipper ready, `v0.13.0-688`, estado `standby`;
  - hotend `28,4 °C`, mesa `27,1 °C`, câmara `27,9 °C`;
  - alvos e potência de hotend/mesa em zero;
  - nenhuma impressão ativa;
  - PostgreSQL ativo;
  - origem ao vivo, sem uso de snapshot antigo.
- Host do agente: placa não Raspberry Pi; métricas específicas de Raspberry não
  são aplicáveis. Doctor confirmou API local e Moonraker saudáveis, fila local
  vazia, protocolo compatível e ausência de alerta.
- Voron 2.4: voltou online com agente `0.1.34` e iniciou uma impressão real.
  Permanece estritamente read-only até concluir e voltar a ficar ociosa/fria.
- UI Cloud antes da correção publicada: detalhe da Voron 0.2 ainda mostrava
  `Registro aberto: Voron 2.4`. A origem era a preferência global antiga; a
  correção `df084dd` faz o shell usar o registro efetivamente aberto.

## Fixture e pré-condição física

- Fixture candidata versionada na própria impressora:
  `Ultra beefed up torque damper_TPU_56m3s.gcode`, 4,15 MB.
- Material indicado pelo nome do arquivo: TPU.
- O arquivo só poderá ser iniciado após confirmação presencial de material
  carregado, mesa livre, peça removida, câmera/host estáveis e autorização do
  operador na janela. O nome do arquivo não substitui essa confirmação.
- Alternativas já presentes: `flap_final_ABS_20m35s.gcode` e
  `StealthBurner_ABS_1h36m.gcode`; também exigem material e geometria física
  confirmados antes do envio.

## Regras de segurança

- Impressão ativa permite somente leitura, atualização de status e captura de
  evidência.
- Ação mutável exige impressora ociosa, fria, preflight aprovado, confirmação
  explícita da UI e operador presente quando houver movimento ou aquecimento.
- Update, rollback e restart são somente do agente Printora.
- É proibido reiniciar ou atualizar Klipper, Moonraker, MCU, firmware, Mainsail
  ou componentes do Update Manager durante esta homologação.
- Uma impressora offline não será usada para simular falha nem receber ação.
- Falha P0, heartbeat vencido, temperatura inesperada, backlog, duplicidade ou
  violação de SLO interrompe e invalida a janela afetada.

## Matriz de estados

| Estado | Evidência | Resultado |
|---|---|---|
| Ociosa/fria | Voron 0.2 em `standby`, hotend/mesa sem alvo | aprovado |
| Offline | Voron 2.4 exibida offline sem ação mutável | aprovado read-only |
| Moonraker/Klipper prontos | leitura ao vivo da Voron 0.2 | aprovado |
| Imprimindo | Voron 2.4 confirmada por resultado remoto: `printing`, hotend ~190 °C e mesa ~75 °C | aprovado read-only; nenhuma ação enviada |
| Pausada | pendente de impressão controlada | pendente |
| Concluída | pendente de impressão controlada e histórico | pendente |
| Cancelada | pendente de cenário seguro e operador presente | pendente |
| Agente reiniciando | pendente de replay exclusivo do agente | pendente |
| Moonraker indisponível | pendente; não reiniciar o serviço para provocar | pendente |
| Rede degradada/reconnect | pendente de falha controlada sem afetar impressão | pendente |

## SLO e limites do soak

- erro HTTP: zero;
- p95 por lote: até `1.500 ms`;
- p99 por lote: até `2.500 ms`;
- heartbeat do agente: até `120 s`;
- backlog ativo agregado: até 25 e sem crescimento contínuo;
- crescimento contra baseline: RSS até 256 MiB, FD até 256 e conexões PostgreSQL
  até 20;
- disco livre: falha somente se estiver abaixo de 15% e de 50 GiB; o primeiro
  probe real mediu 11,8%, mas ainda cerca de 114 GB livres;
- nenhum novo job de agente falho, dead letter, correlation ID duplicado ou
  restart de processo;
- serviços obrigatórios, Redis, PostgreSQL, storage, busca e agente sempre
  saudáveis.

O observador `c2836de` grava JSONL sanitizado com p95/p99, heartbeat, filas,
conexões, banco, busca, objetos, WAL, logs, CPU, RSS, FD, tasks, reinícios e
disco. Identifica o agente apenas por fingerprint, não persiste URL de banco,
token, IP, path privado ou payload e encerra o soak ao primeiro gate violado.

## Cronologia

- `df084dd`: corrigido o contexto visual da impressora aberta.
- `c2836de`: implementada telemetria fail-closed e retenção do soak.
- `efca67d`: calibrado o gate combinado de disco após o probe real confirmar
  cerca de 114 GB livres apesar de 11,8% de reserva percentual.
- Deploy da instrumentação: workflow `30043834953` concluído com sucesso.
- Probe pós-deploy: aprovado, com agente `0.1.34` ativo, heartbeat de 3,6 s,
  backlog 1, zero dead letter, zero correlação duplicada, serviços obrigatórios
  ativos e observador sem falha.
- Primeira janela curta: invalidada antes do soak prolongado. Não houve erro
  HTTP, mas o gerador enviava rajadas de concorrência 20 e só depois esperava,
  embora declarasse 5 req/s; p95 observado de 2.407 ms excedeu o SLO de
  1.500 ms. A janela não será somada nem reaproveitada.
- Correção: `load-smoke.py` passou a distribuir o início das requisições pela
  taxa configurada. O reteste público focado fez 25 requisições a 5 req/s,
  sem erro, p95 de 319 ms e p99 de 339 ms.
- Validação read-only durante impressão: a Voron 2.4 tinha agente distinto,
  `0.1.34` e heartbeat atual. O último resultado remoto sanitizado confirmou
  `printing`, hotend em cerca de 190 °C e mesa em cerca de 75 °C. Nenhum
  comando, atualização ou reinício foi enviado à impressora.
- Incidente visual: ao trocar da Voron 0.2 para a 2.4, a aba Operação preservou
  temporariamente o status da 0.2 enquanto a nova leitura aguardava resposta.
  A causa era falta de escopo e ordenação na preservação assíncrona do hook.
  A correção limpa dados de outra impressora imediatamente e ignora respostas
  atrasadas de requisições anteriores. O workflow `30046125403` publicou
  `11ab762`; o reteste real 0.2 -> 2.4 mostrou estado vazio/read-only imediato,
  sem dado cruzado e com todos os comandos bloqueados enquanto aguardava leitura.
- Incidente de fila: o reteste revelou reconnect do WebSocket da Voron 2.4
  durante leituras longas. Pollings concorrentes acumularam 147 jobs pendentes,
  violando o limite de backlog antes do soak. A impressão permaneceu intocada.
  A correção coalesce leituras ativas pelo mesmo escopo e preserva jobs mutáveis
  independentes; a janela curta continua invalidada até publicação e drenagem.
- Incidente temporal pós-publicação: uma leitura read-only real mostrou que jobs
  `pending` antigos continuavam ativos. O vencimento UTC sem offset era comparado
  ao `CURRENT_TIMESTAMP` textual no fuso da sessão PostgreSQL, adiando a
  expiração em três horas. A correção usa instante UTC tipado para `expires_at`
  e timestamp com offset para `updated_at`; nenhuma linha foi excluída e a
  janela permanece invalidada até republicação, drenagem natural e reteste.
- Incidente de lease implícito: após `ecdec49`, 289 pendências expiraram pelo
  fluxo normal e o backlog caiu para cinco, mas um
  `remote_gcode_files_list` permaneceu `in_progress` por mais de duas horas
  porque o heartbeat renovava seu timestamp sem provar progresso. Heartbeat
  passa a representar somente liveness; qualquer job sem resultado expira em
  cinco minutos. Nenhuma linha foi cancelada ou excluída manualmente.
- Publicação da correção: o primeiro workflow (`30053178674`) falhou antes de
  publicar porque o inventário modular preservado não incorporava as seis
  linhas do commit concorrente `211f472`. `78d1637` regenerou somente o
  inventário, e o workflow `30053826438` publicou a release com sucesso.
- Drenagem real pós-publicação: `76440` mudou de `in_progress` para `failed`
  após cinco minutos com `job em execução expirou sem retorno do agente`, e
  `76482` expirou antes do consumo. Não houve `DELETE`, cancelamento ou ajuste
  manual. A leitura web read-only da Voron 0.2 concluiu, o backlog agregado
  chegou a zero e permaneceu abaixo de 25 no ciclo adicional.
- Probe observado aprovado: agente `0.1.34`, heartbeat atual, backlog zero,
  nenhum dead letter, correlação duplicada, restart ou serviço inativo.
- Primeira repetição curta invalidada: quatrocentas requisições públicas sem
  erro, mas o quarto lote mediu p95 de `2.021 ms` e p99 de `3.207 ms`.
  Os dois slots locais passaram com p95 abaixo de `50 ms`; o reteste público
  passou com p95 de `401 ms` e p99 de `1.096 ms`.
- Repetição curta integral aprovada: `600` requisições em seis lotes a
  `5 req/s`, zero erro, observador aprovado e todos os lotes dentro do SLO.
- Primeira janela de 24 horas: invalidada após cinco minutos. O agregador
  sanitizado encontrou no 16º lote p95 de `1.844 ms` e p99 de `2.779 ms`;
  a unit encerrou fail-closed, sem erro HTTP, backlog, restart ou serviço
  inativo. O acompanhamento por recortes recentes não substitui a consolidação
  integral do JSONL.
- Diagnóstico: o gerador público abria uma conexão DNS/TCP/TLS por requisição,
  enquanto browser e agente reutilizam keep-alive. A carga representativa passa
  a usar pool limitado; o modo frio continua separado e o SLO não muda. Nova
  janela só começa após publicação e repetição curta integral.
- Publicação pooled: o workflow `30056598258` publicou `266e951` e o probe
  sanitizado passou com agente `0.1.34`, backlog 1, zero dead letter,
  duplicidade, restart ou serviço inativo. O soak curto foi bloqueado antes da
  primeira requisição: o launcher executava `load-smoke.py` com o Python do
  sistema, que não possui `httpx`, embora a dependência exista no ambiente
  imutável da aplicação. A correção usa explicitamente o Python da release;
  nenhuma janela prolongada foi iniciada ou parcialmente aproveitada.
- Correção do runtime: `7b31c16` passou no gate completo e o workflow
  `30057967799` publicou a release. O probe seguinte passou com backlog zero,
  agente `0.1.34`, serviços ativos e nenhuma duplicidade, dead letter ou
  restart. A repetição curta pooled completou 600 requisições em seis lotes,
  zero erro, pior p95 de `1.003,569 ms` e p99 de `2.005,007 ms`; o resumo
  sanitizado confirmou `connection_modes=["pooled"]` e tendências dentro dos
  limites.
- Nova janela integral de 24 horas: iniciada em `2026-07-24T01:27:10Z`, unit
  `printora-cloud-soak.service`, invocation
  `0f365c644dd147318fc8130aeb89f25f`. A primeira carga e observação passaram;
  qualquer falha invalida integralmente esta janela.
- Segunda janela de 24 horas: invalidada após 19 lotes e 1.900 requisições. Não
  houve erro HTTP, backlog, dead letter, duplicidade, restart ou crescimento
  anormal de recurso, mas o último lote mediu p95 de `2.002,734 ms` e p99 de
  `2.602,830 ms`. O processo de carga ainda encerrava o `httpx.Client` ao fim
  de cada lote, recriando o pool a cada 20 segundos. A correção mantém um único
  processo e pool durante toda a janela e transmite os relatórios por FIFO ao
  observador. Nenhum trecho desta tentativa será aproveitado.
- Publicação do pool contínuo: o workflow `30061267780` publicou com sucesso
  `0b6e963a55a0001afefa9f479cffdabc75dd4500`; o SHA ativo e as três units foram
  confirmados no host. O smoke público pós-deploy manteve um único pool durante
  120 segundos, completou 700 requisições em sete lotes, sem erro e com todos os
  p95/p99 dentro do SLO. A pior medição foi p95 de `402,356 ms` e p99 de
  `1.187,277 ms`.
- Publicação visual final: o workflow `30069338745` publicou com sucesso a
  release exata `0700533c489087ab83cf26318b1ec8d0c62b0bc6`, incluindo o ajuste
  responsivo e de conteúdo `d524af6`. Gate completo, build reproduzível,
  auditorias, SBOM, blue/green, drain e endpoint público passaram. Produção
  serviu `index-DrJ9_ddD.js`; o Chrome confirmou `Origem no catálogo` e o estado
  vazio de mods em `/c/maker-annex-engineering`, sem erro de console.
- Smoke privado autenticado: uma sessão real existente percorreu `Visão geral`,
  `Impressoras`, `Agentes`, `Projetos de impressão`, `Social`, `Catálogo`,
  `Setup`, `Finanças`, `Fabricação`, `Dados e inteligência` e `Administração`
  no Chrome. Desktop/tema escuro e mobile `390x844`/tema claro exibiram o
  heading correto em todas as áreas, sem erro de console. Tema, viewport e tela
  inicial foram restaurados; nenhum refresh, job ou comando foi disparado.
- Gate de hardware pós-deploy: não iniciado. Voron 0.2 e Voron 2.4 estavam
  intencionalmente desligadas, conforme confirmação do responsável, portanto o
  observador falhou fechado por heartbeat vencido. Nenhuma janela de 24 horas
  foi aberta. Quando uma impressora voltar, será obrigatório repetir probe e
  smoke curto observados antes de iniciar uma nova janela integral.
- Retorno da Voron 2.4: em `2026-07-24T11:04:28Z`, o probe sanitizado confirmou
  agente `0.1.34`, heartbeat de `6,533 s`, backlog 1, zero dead letter,
  duplicidade, restart ou serviço inativo. A impressora permaneceu estritamente
  read-only.
- Duas tentativas observadas de 120 segundos foram invalidadas aos 60 segundos
  por `new_agent_job_failure`, embora os seis lotes de carga somados tivessem
  600 requisições, zero erro e p95/p99 dentro do SLO. A auditoria read-only
  mostrou jobs de consulta criados anteriormente pela tela de detalhe do agente:
  um `remote_moonraker_status` expirou antes do consumo e um
  `remote_gcode_files_list` em execução expirou sem retorno. A tela foi movida
  para Administração para cessar o polling; nenhum job foi excluído ou
  cancelado e o backlog da Voron 2.4 drenou naturalmente até zero.
- Repetição curta observada aprovada: unit
  `printora-cloud-soak-short-110728.service`, invocation
  `892f2a0400e3409c8f6d03f90ead81ec`, janela sanitizada de
  `2026-07-24T11:07:49Z` a `2026-07-24T11:09:49Z`. Foram 700 requisições em
  sete lotes a `5 req/s`, `connection_modes=["pooled"]`, zero erro, pior p95 de
  `777,798 ms`, pior p99 de `1.855,753 ms` e backlog máximo 1. O agente manteve
  heartbeat máximo de `7,605 s`; dead letters, duplicidades, novos jobs falhos,
  restarts e serviços inativos ficaram em zero. Conexões PostgreSQL ficaram em
  1, RSS cresceu cerca de 5,9 MiB e FD em 3, dentro dos limites.
- Retorno da Voron 0.2: o probe de `2026-07-24T11:26:09Z` confirmou agente
  `0.1.34`, heartbeat de `8,779 s`, backlog zero, serviços ativos e nenhuma
  duplicidade, dead letter ou restart.
- Repetição curta da Voron 0.2 aprovada: unit
  `printora-cloud-soak-short-v02-112625.service`, invocation
  `219add4b4bca48b9ba64a6098a277aba`, janela sanitizada de
  `2026-07-24T11:26:45Z` a `2026-07-24T11:28:45Z`. Foram 700 requisições em
  sete lotes a `5 req/s`, `connection_modes=["pooled"]`, zero erro, pior p95 de
  `889,383 ms`, pior p99 de `1.685,524 ms` e backlog máximo 2. Heartbeat máximo
  foi `5,158 s`; não houve novo job falho, dead letter, duplicidade, restart ou
  serviço inativo. Conexões PostgreSQL chegaram a 4, RSS cresceu cerca de
  8,6 MiB e FD em 4, dentro dos limites.
- Gate imediatamente anterior às 24 horas: Voron 0.2 e Voron 2.4 foram
  revalidadas em `0.1.34`, com heartbeats de `1,895 s` e `8,993 s`, backlog
  zero e observadores aprovados.
- Nova janela integral de 24 horas: iniciada em `2026-07-24T11:29:43Z`, unit
  `printora-cloud-soak.service`, invocation
  `277cf0966b024f42963c2df5d902dfc8`, evidência sanitizada
  `soak-24h-20260724T112943Z.jsonl`. A primeira carga completou 100 requisições
  com zero erro, p95 de `126,418 ms` e p99 de `1.247,100 ms`; a primeira
  observação passou com heartbeat de `5,268 s`, backlog 3, nenhum novo job
  falho, dead letter, duplicidade, restart ou serviço inativo. A janela só será
  válida se a mesma invocation completar continuamente por 86.400 s; qualquer
  falha invalida todo o período e nenhuma tentativa anterior será somada.
- Soak final contínuo de 72 horas: não iniciado.

## Auditoria de fechamento por lote

Esta tabela é o gate de conclusão do pacote. Soak aprovado não substitui a
matriz física, o fluxo real ou o E2E visual.

| Lote | Estado | Evidência atual | Necessário para fechar |
|---|---|---|---|
| 1. Matriz, fixture, limites e segurança | concluído | baseline, fixture candidata, SLO e regras acima | nenhum |
| 2. Leitura durante impressão ativa | concluído | Voron 2.4 em `printing`, temperaturas ao vivo e zero comando enviado | nenhum |
| 3. Ações protegidas e falhas controladas | parcial | fila, expiração, reconnect e bloqueios foram exercitados sem afetar a impressão | validar pausada, concluída, cancelada, agente reiniciando, Moonraker indisponível e rede degradada em janela segura |
| 4. Update/rollback do agente | concluído | `docs/audits/AGENT_RELEASE_0.1.34_2026-07-23.md` comprova `0.1.34 -> 0.1.33 -> 0.1.34` nas duas Voron somente pela web | nenhum |
| 5. Projeto até histórico real | pendente | contratos e testes existem, mas não substituem aceite físico desta janela | validar projeto, G-code, preview, preflight, salvar/enviar e histórico com fixture aprovada |
| 6. E2E visual real | parcial | matriz local, superfícies públicas e onze áreas privadas autenticadas passaram em desktop/escuro e mobile/claro sem erro de console | validar desktop, mobile e temas no fluxo físico de operação, preview, entrega e histórico |
| 7. Soak inicial de 24 horas | em execução | as duas Voron passaram em `0.1.34`; a Voron 0.2 concluiu probe e repetição observada de 120 s/700 requisições; invocation `277cf0966b024f42963c2df5d902dfc8` iniciou com primeira amostra aprovada | completar a mesma invocation continuamente por 86.400 s e consolidar a evidência sanitizada |
| 8. Correções e repetição | em execução | incidentes de UI, fila, UTC, lease, conexão fria, runtime e ciclo do pool foram corrigidos e retestados | reiniciar integralmente qualquer janela que falhar |
| 9. Soak final de 72 horas | pendente | não iniciado | iniciar somente após lotes anteriores e completar continuamente por 259.200 s |
| 10. Consolidação e runbook | pendente | cronologia parcial registrada | consolidar tendências, incidentes, capacidade, evidência sanitizada e operação final |

Ordem segura após as 24 horas: consolidar a janela; confirmar as duas máquinas
ociosas e frias; executar os lotes 3, 5 e 6 sem ação em Klipper, Moonraker, MCU
ou firmware; corrigir e retestar qualquer regressão; então iniciar as 72 horas.
