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
- A Voron 2.4 offline não será usada para simular falha nem receber ação.
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
- Soak inicial de 24 horas: não iniciado.
- Soak final contínuo de 72 horas: não iniciado.
