# Evidência de RPO físico e recuperação contínua - PKG-99

Data: 2026-07-24

## Escopo

- PostgreSQL físico, WAL, objetos, configuração, Redis recomponível, busca,
  releases e prontidão de desastre;
- destino externo Restic já existente e custódia mantida fora do host;
- publicação blue/green sem restore de dados;
- fora do escopo: impressoras desligadas, agente, Moonraker, Klipper, MCU,
  firmware e qualquer comando físico.

Nenhuma tabela, linha, job, objeto, snapshot, WAL ou release foi excluído. Não
foi executado `forget` efetivo nem `prune`.

## SLO e desenho

| Classe | RPO | RTO | Evidência esperada |
| --- | --- | --- | --- |
| PostgreSQL físico | até 300 s | até 900 s | WAL externo corrente e restore com replay |
| deploy/cutover | zero | até 300 s | blue/green usando banco compartilhado |
| objetos/configuração | até 24 h 15 min | até 900 s | snapshot diário e checksum |
| Redis/busca | zero dado canônico | até 900 s | recomposição e rebuild |

O limite configurado do PostgreSQL é 290 s: 120 s para troca forçada de WAL,
60 s entre disparos e 110 s de timeout efetivo da sincronização. O monitor roda
a cada minuto e falha a partir de 210 s sem confirmação externa corrente.

## Implementação

- `archive_timeout=120s` aplicado por reload, sem reiniciar PostgreSQL;
- snapshot Restic externo do arquivo WAL completo, com validação de presença do
  segmento final e estado sanitizado;
- timers separados para WAL, monitoramento, backup completo e restore semanal;
- falha gera journal crítico com owner `operations` e webhook opcional fora do
  Git;
- backup completo registra idade, duração, tamanho do banco e quantidade de
  versões de objeto sem IDs privados;
- restore semanal usa o snapshot completo mais recente e o WAL contínuo, promove
  cluster isolado e valida configuração, schema, revisões, FKs, objetos, busca e
  replay;
- preview de retenção separado para snapshots completos e WAL, sempre dry-run;
- gate bloqueia `RuntimeMaxSec` inefetivo em serviços `Type=oneshot`.

## Gate local

- 634 testes backend;
- 22 E2E desktop/mobile;
- property/fuzz: 20 testes, corpus versionado e seed reproduzível;
- mutation score: 70,34%, acima do mínimo de 60%;
- cobertura Python: 79,41% global e 84,87% crítica;
- cobertura Go: 56,60% global e 58,10% crítica;
- cobertura frontend crítica: 91,37%;
- Go, build frontend reproduzível, bundle budget e contratos passaram;
- 23 testes focados de packaging/prontidão passaram;
- inventário modular: 174 módulos, 389 contratos e zero ciclo.

## Evidência de produção

Os exercícios foram executados no servidor de produção, sempre em destino
isolado e sem trocar o cluster PostgreSQL atendendo a aplicação:

- configuração PostgreSQL protegida como `root:postgres`, modo `0640`, e
  `archive_timeout=120s` confirmado;
- validação das units pelo systemd aprovada; timers de WAL, monitoramento,
  backup completo e restore semanal ativos;
- sincronização WAL pela unit aprovada com 288 arquivos, duração observada entre
  5 s e 11 s, snapshot externo validado e nenhum erro final;
- backup completo aprovado em 167 s, incluindo cinco classes protegidas e oito
  versões de objetos;
- restore isolado otimizado aprovado em 78 s; a execução pela unit instalada
  terminou em 258 s, saiu de recovery e aprovou as seis reconciliações;
- monitor de recuperação aprovado com RPO configurado de 290 s, atraso de 1 s,
  backup de 293 s, restore de 24 s, zero falha e 10,5% de disco livre;
- drill de alerta gravou evento crítico sanitizado com owner `operations`; não
  havia webhook externo configurado, portanto a entrega comprovada foi o
  journal local;
- as tentativas anteriores que revelaram timeout inefetivo, lock em diretório
  protegido, parsing textual do Restic, replay excessivo e espera por WAL futuro
  foram invalidadas. Cada causa recebeu correção, teste de regressão e nova
  execução integral aprovada;
- nenhum prune, `forget` efetivo, exclusão, cancelamento de job ou alteração de
  impressora foi executado.

O espaço livre de 10,5% está acima do gate de 10%, mas com margem estreita.
Capacidade permanece risco operacional acompanhado; resolver capacidade por
prune sem preview, restore válido e confirmação explícita continua proibido.

Publicação e validação final do runtime:

- release `debd717662666d556094b9df9d0450e304c5c271` publicada pelo workflow
  `30134329186`;
- gate completo, build reproduzível, evidências de qualidade, auditorias,
  SBOM, bundle imutável, preflight privilegiado, blue/green, drain e endpoint
  público aprovados;
- auditoria independente no servidor confirmou o marcador da release, a mesma
  release no slot ativo e na réplica, prontidão de recuperação e preflight;
- probe de worker/Redis passou;
- o primeiro probe active-active revelou que o launcher de carga usava o Python
  do sistema sem `httpx`. A tentativa foi inválida, a instância foi restaurada
  pelo trap e o endpoint público permaneceu saudável;
- após correção para usar o runtime da release, o probe active-active passou com
  300 requisições, pool HTTP compartilhado, zero erro e recuperação da
  instância;
- smoke público final passou com 700 requisições, pool compartilhado, zero erro,
  zero retry, p95 de 84,146 ms e p99 de 499,487 ms;
- `health`, `ready`, catálogo, bundle frontend, versão `0.1.41`, schema `86` e
  última integridade `ok` foram confirmados publicamente.
- a publicação de encerramento `30135648450` foi bloqueada antes do upload
  porque um WAL novo surgiu entre a sincronização e o preflight. O estado tinha
  55 s, dentro do alerta de 210 s e do RPO de 290 s, mas o gate exigia igualdade
  instantânea. O monitor foi corrigido para registrar
  `wal_external_current=false` sem falhar dentro da janela; após 210 s continua
  falhando fechado como `wal_sync_late` e `wal_external_behind`.

IDs privados, paths, fingerprints, credenciais e payloads não foram registrados.

## Retenção e capacidade

A evidência sanitizada registra bytes e arquivos do arquivo WAL, duração da
sincronização, idade, quantidade de snapshots externos e percentual de disco
livre. O preview sugere 48 snapshots horários, 14 diários, 8 semanais e 12
mensais para WAL; qualquer aplicação dessa política exige confirmação separada.

## Limite físico e evolução

O host único não é alta disponibilidade. A cópia externa reduz perda de dados,
mas promoção automática ou RPO físico zero exigem segundo host. Réplica
assíncrona reduz RTO; réplica síncrona pode fornecer RPO zero físico ao custo de
latência e indisponibilidade quando o par não confirma escrita. Nenhuma réplica
foi implantada automaticamente.
