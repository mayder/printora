# Incidente de capacidade WAL — 8 de setembro de 2026

**Estado: corrigido, publicado e validado em produção.** Código ativo `3da7f94`;
aceite operacional final em 2026-09-08, conforme evidências abaixo.

## Recuperação emergencial comprovada

Host compartilhado: `187.45.180.181`; cluster dedicado `16/printora`, porta
`5433`. O incidente afetou o Printora e a geração de PDF do Inspect.

| Medida | Antes | Após drenagem, 12:41:42 UTC |
|---|---:|---:|
| Volume `/dev/sda4` | 972.185.931.776 bytes | mesmo volume |
| Espaço disponível | 0 bytes | 511.824.273.408 bytes |
| Ocupação informada por `df` | 100% | 45% |
| Arquivo WAL | 535.193.194.492 bytes | cerca de 22,8 GB, com novos segmentos |
| PostgreSQL | rejeitando conexões | aceitando; fora de recovery |

Causa raiz: a sincronização enviava o arquivo WAL ao Restic, mas não encerrava
o ciclo de vida das cópias locais. Cada segmento tem 16 MiB e o
`archive_timeout=120s` pode produzir aproximadamente 12,1 GB decimais por dia
quando há atividade contínua. O total observado foi de 31.900 segmentos
completos, além de 12 arquivos auxiliares. WAL não equivale ao volume de dados
novos do banco: a troca antecipada arquiva o segmento com seu tamanho integral.
Referência: [arquivamento contínuo do PostgreSQL 16](https://www.postgresql.org/docs/16/continuous-archiving.html).

Foram removidos **30.553 segmentos únicos**, totalizando **512.594.280.448
bytes**, exclusivamente de `/var/lib/postgresql/16/printora-wal-archive`.
Período de modificação: `2026-07-22T20:43:24.961523Z` até
`2026-09-05T12:10:26.884317Z`. Corte fixo:
`2026-09-05T12:12:17.126314Z`; primeiro segmento preservado:
`2026-09-05T12:12:26.746751Z`. A margem mínima de 72 horas foi respeitada.
Nenhum arquivo de `pg_wal`, banco, tabela, objeto, upload, release ou backup
externo foi removido.

A intervenção fez um lote inicial de 256 arquivos cujo conteúdo externo já
estava verificado e era anterior ao início do último backup físico. Depois da
verificação integral, executou sete lotes de 4.096 e um de 1.625 arquivos.
`df`, `pg_isready`, Nginx e health/ready foram conferidos entre os lotes.
O timer de sync foi suspenso somente durante a exclusão supervisionada, com
espera do oneshot e retomada em trap; isso evitou a corrida do lock antigo em
RuntimeDirectory. O lock permanente corrigido fica no diretório de estado.

## Custódia e cadeia

- Snapshot WAL externo fixado:
  `f11846ed1f8caab46f3001d6b2052ac3eff96fe2f9d3d133fad2916588751d5a`.
- Último WAL externo/local no início: `000000010000007C000000C2`.
- Último backup físico encontrado:
  `a09f5949c91b2011d293c5be9e4a4d6c08db22a698fa92c992e6f75dd8ac9fc3`,
  concluído em 27/07; o estado de restore era de 24/07. Ambos estavam vencidos.
- `backup_label` lido do backup físico externo: início em
  `00000001000000070000006D`; manifesto termina em
  `00000001000000070000006E`. Nenhuma lacuna até o WAL final externo.
- Os dois snapshots foram copiados do Restic externo para repositório efêmero
  em RAM, sem alterar a custódia externa: 4.095.622.869 bytes deduplicados,
  38.967 blobs. IDs copiados: `e0a923bd` e `a5b4862d`.
- `restic check --read-data` no conjunto copiado verificou dois snapshots e
  todos os 244 packs resultantes: **no errors were found**. A cópia leu e
  autenticou os blobs da origem e a checagem releu integralmente o conjunto.
- A checagem global inicial foi interrompida por reprocessar 30.994 snapshots
  cumulativos; não é reportada como concluída. Quatro packs órfãos não críticos
  e locks antigos foram observados e preservados; nenhum prune/unlock foi feito.

Inventário, corte, intenção e resultado por arquivo estão preservados no host,
`/var/lib/printora-cloud/recovery/incident-20260908`, e em cópia local privada:
`.artifacts/wal-incident-20260908/server-evidence.tar.gz`.
SHA-256 da cópia local inicial:
`e25c385db1a727d806520febb17ba7d1c233727f92c794d3944be1b79b9fcbf1`.

## Validação dos serviços

PostgreSQL saiu de recovery e apresentou checkpoints concluídos e
`pg_stat_archiver.failed_count=0` após a recuperação. A aplicação continuou
usando `archive_timeout=120s`. Health e ready públicos retornaram HTTP 200.
O journal desde 12:36 UTC não registrou novos `No space left on device` ou
`errno=28` na coleta posterior à drenagem.

Inspect: 51/51 links current válidos, 51/51 workers ativos e 51/51 logins públicos
HTTP 200; maior tempo observado 0,595256 s. Isso comprova disponibilidade
operacional e pública; não representa todas as telas autenticadas de cada cliente.

PDFs regenerados pela aplicação, com cópias anteriores preservadas:

| Cliente / relatório | Tamanho | Páginas | Verificação |
|---|---:|---:|---|
| IRB / 124573 | 78.992 bytes | 3 | geração, download, SHA-256, abertura e renderização |
| ItaMinas / 2258 | 75.149 bytes | 2 | geração, download, SHA-256, abertura e renderização |

## Correção permanente e gates

A correção adiciona retenção local por conteúdo comprovado no Restic, 72 horas
mínimas, sete dias em condição normal, gatilho de 64 GiB/20% livre, batches de
32 arquivos, lock persistente compartilhado, dry-run, evidência sanitizada e
proteção de caminhos/arquivos. O restore resolve snapshots históricos, sem
presumir que o último snapshot ainda contém os arquivos removidos localmente.
Backup e restore intensivos recusam menos de 10% livre. Publicação também
preserva releases enquanto existir o marcador operacional do incidente.

A renovação de backup, restore isolado, instalação do timer e publicação são
gates operacionais separados da recuperação de espaço. Seus resultados finais
serão registrados após execução, sem equivaler código ou CI a aceite produtivo.

Na renovação, o backup físico terminou, mas `pg_dump --file=-` tentou abrir
um arquivo literal chamado `-` no diretório protegido do serviço. O defeito
preexistente foi corrigido removendo essa opção: o dump custom usa stdout por
padrão e continua atravessando o limitador. Um teste executa o pipeline com
conteúdo binário e impede regressão do argumento. Referência:
[pg_dump 16, opção file](https://www.postgresql.org/docs/16/app-pgdump.html).
O pipeline inicial `34230658591` foi cancelado antes da publicação, para
incorporar essa correção. A repetição operacional usa uma cópia isolada do
script, sem substituir a aplicação, com taxa física temporária de 4 MiB/s,
dump de 256 KiB/s, prioridade baixa e interrupção se health/ready falharem.
Os limites permanentes do serviço continuam em 1 MiB/s e 256 KiB/s.

Também foi encontrada falha preexistente na unidade de alerta: `%I` convertia
hífens em barras, rejeitadas pelo contrato sanitizado do emissor. O argumento
passa a usar `%i`, preservando o evento. O destino configurado no host é journal;
não há webhook externo configurado, portanto não se afirma entrega externa.

A segunda tentativa foi interrompida pelo guard de health durante a leitura
final do Restic: os caminhos temporários exclusivos impediam selecionar um
snapshot pai, provocando releitura de todos os WAL locais. A correção fixa como
pai o snapshot WAL externo mais recente e adiciona limite de I/O de 4 MB/s ao
serviço de backup. O conteúdo novo continua sendo lido e autenticado; arquivos
inalterados reutilizam os blobs já custodiados. O pipeline `34232247844` foi
cancelado antes de publicar. Uma nova execução operacional usa 4 MiB/s físico,
1 MiB/s lógico e limite de I/O de 4 MB/s, mantendo a interrupção por health.
O dry-run desse pai no host reconheceu 1.403 arquivos inalterados, 23.303.557.804
bytes, zero blobs novos e terminou em 2,61 s, sem criar snapshot externo.

O backup novo foi confirmado em `2026-09-08T13:52:58Z`, duração de 846 s,
2.003.336.215 bytes de banco e 56 versões de objetos. Snapshot:
`2a455238d263300307f1cbcf10453a4d07e22ecca97e8944bf0bad67d5d80263`.
O manifesto nativo declara Start-LSN `7C/EC000028` e End-LSN `7C/F1021F68`;
o manifesto da aplicação registra WAL final `000000010000007C000000F2`,
depois do dump lógico. O seletor antigo iniciava tarde demais e podia omitir
a continuação do segmento F1. Retenção e restore passaram a usar o Start-LSN
nativo. O teste antigo foi interrompido antes do aceite e reiniciado com esse
seletor e cache Restic compartilhado; o pipeline `34234356408` foi cancelado
antes da publicação para incorporar a correção.

O reteste identificou que o Restic instalado não aceita `--include-file`.
O transporte dos WAL usa agora `--include` repetido, em grupos máximos de 128
caminhos, tanto na retenção quanto no restore. Isso preserva `--verify` e
`--sparse`, sem atualizar o binário nem exceder ARG_MAX. O caso de 257 caminhos
e a recusa de caminhos fora do arquivo dedicado têm regressão automatizada.
Foi confirmado que a release ativa antes da publicação é `e6173bb`, igual à
base de código deste incidente. Não há mudanças de aplicação ou SQL. O marcador
`preserve-schema` evita reaplicar DDL idêntico e recriar triggers; SQL ou grants
diferentes bloqueiam o fluxo, preservando os objetos durante a intervenção.

Rollback: suspender exclusivamente o timer de retenção; manter sync e custódia.
Recompor cópia local pelo snapshot e checksum auditados, se necessário; nunca
restaurar banco antigo sobre escritas novas. O host único permanece sem HA
física, e inconsistência externa bloqueia retenção, exigindo ação operacional.

A extração com limite de 10 MB/s acionou o guard de latência e foi interrompida.
O limite final de restore e retenção é 4 MB/s com prioridade idle. O restore
agora fixa o snapshot completo e o alvo WAL antes do download e consulta o
catálogo uma única vez por processo, eliminando trabalho repetido sem ampliar
o RTO de 900 segundos. O destino continua sendo o disco, em cluster isolado.

O reteste com 4 MB/s também acionou timeout HTTP de 5 s (TCP/TLS concluídos,
sem primeiro byte), revertido ao parar exclusivamente o restore de teste.
Foi provisionado executor de recuperação no disco do host externo, com 705 GiB
livres na inspeção, mantendo rede desativada durante o teste e custódia montada
somente leitura. A imagem usa PostgreSQL 16 e Restic fixados por digest; chave
SSH dedicada permite somente o executor. Essa preparação de infraestrutura de
recuperação não é publicação da aplicação. O fluxo oficial continua condicionado
a um restore real bem-sucedido e aos demais gates. Evidência final pendente.

O primeiro teste de container detectou permissão de travessia na raiz do mount
PostgreSQL temporário; corrigida para 0755, mantendo o cluster próprio em 0700.
A limitação cgroup de I/O exige o disco físico `/dev/sda`, não a partição; essa
configuração foi validada em container vazio antes de retestar. Metadados
AppleDouble do deploy antigo são ignorados no fingerprint e na comparação de
SQL; todos os arquivos efetivos do backend foram comparados e são idênticos.

### Restore externo aprovado

Em `2026-09-08T15:15:21Z`, o teste físico em disco terminou com `status=passed`
em **210 s**, abaixo do RTO de 900 s. Imagem imutável:
`sha256:e2f9832b50ebe872eaa226765071f8b1e28a15c3c3544b93a9028b241ed10a8b`.
Reproduziu 43 segmentos desde `000000010000007C000000EC` até
`000000010000007D00000016`, a partir do backup completo `2a455238…`.
Banco isolado promovido (`in_recovery=false`), 176 tabelas, 99 versões de schema,
zero FKs inválidas; 12 configurações e 56 versões de objetos verificadas por
checksum; 30 referências canônicas reconciliadas; 364 documentos de busca
reconstruídos. Container sem rede, custódia somente leitura, scratch removido.
Evidência privada em `offhost-success-custody.log` e estado do wrapper produtivo
em `offhost-success-production.log`, na pasta local deste incidente.

### Bloqueio adicional de publicação e correção

O workflow `34243801219` aprovou todos os gates de qualidade, mas bloqueou antes
do upload no scanner de dependências: quatro vulnerabilidades alcançáveis da
stdlib Go 1.25.12. Python e dependências produtivas npm passaram. Toolchain
corrigida pontualmente para 1.25.13, mantendo o scanner. Fontes do backend,
objetos, schema, artefatos de agente e imagem de restore não mudaram.
Referências oficiais: https://pkg.go.dev/vuln/GO-2026-6218 e
https://pkg.go.dev/vuln/GO-2026-6090. O pipeline que falhou não publicou aplicação.

## Publicação e validação dos executores instalados

Código publicado: `3da7f949c00c58e4f2423ecd0dbe572dad926c4a`, branch `cloud`.
Workflow oficial: https://github.com/mayder/printora/actions/runs/34246366459,
tentativa 2, concluído com sucesso. Na tentativa 1, a cobertura passou, mas o
GitHub respondeu 403 ao finalizar seu artefato; repetiu-se o job falho e seus
dependentes no mesmo SHA, sem dispensar gates. O scanner Go corrigido terminou
sem vulnerabilidades encontradas. `./check.sh` completo passou, incluindo 821
testes backend, 70 frontend, 36 E2E e mutação de 70,34%; 76 testes focados passaram.

A release ativa e os hashes de nove executores instalados foram comparados com
o commit. Timers de sincronização, retenção e restore habilitados. O teste de
alerta confirmou registro no journal; nenhum webhook externo está configurado.
A unit definitiva de restore passou às `2026-09-08T16:09:32Z` em **206 s totais**
(195 s no disco externo): replay de 70 WAL, de `000000010000007C000000EC` até
`000000010000007D00000031`; todas as validações físicas, configuração, objetos,
FKs, schema e busca aprovadas. A imagem/runner externos correspondem aos scripts
versionados, com hashes preservados na evidência.

Após a publicação, 51/51 endpoints de login Inspect retornaram 200; 51 workers
ativos e 51 links de releases válidos. PDFs regenerados, baixados com checksum
idêntico e renderizados/abertos: IRB 124573, 78.971 bytes, 3 páginas, SHA-256
`fde3efd72f17e71bb19d7740029d97547d0d35c52e8be9c87cbce071ea09d2b3`;
ItaMinas 2258, 75.151 bytes, 2 páginas, SHA-256
`27ae094f37bc1646a7b31d3bf05eb4116a9f7b469156dc1a1afd8104e51cfc40`.
Essa validação dos 51 clientes é pública/operacional; não representa navegação
autenticada de todas as telas de cada tenant. Avisos libpng sobre perfil sRGB
não impediram geração, download ou renderização dos PDFs.

A preparação da chave dedicada havia restringido o diretório de controles a
0700; a conferência final restaurou `/etc/printora-cloud` a 0755, mantendo chaves
e senhas 0600. Ambos os preflights anteriores registraram `candidates=0`, duas
releases protegidas e tamanho inalterado: **nenhuma release foi removida**.
Os marcadores de preservação foram novamente conferidos como usuário `deploy`.


## Prova de retenção e estado final

O WAL `000000010000000000000001` foi recomposto da custódia `f11846ed…` somente
para validar o mecanismo, com tamanho 16 MiB e SHA-256
`77508c586d664f9fad823bcee42a0a6175da5e733b8deae9634b905826fc4645`.
Duas tentativas recusaram a exclusão com o motivo sanitizado agregado do guard;
ambas preservaram o arquivo. A execução seguinte, disparada pelo timer instalado,
registrou `flock(LOCK_EX|LOCK_NB)=0`, intent fsync, unlink exclusivamente do WAL e
`wal_retention_completed removed=1`, terminando com status 0 às **16:20:41 UTC**.
O snapshot de confirmação da exclusão foi
`1981671c8e38319919ec13b5081f5e6d7591b52beb71f8762682706615ea8612`.
Não foi forçada remoção nem dispensada a verificação. A instrumentação somente
observou syscalls do processo existente. Scratch de verificação foi limpo pelo
próprio executor. O WAL recomposto já fazia parte dos 30.553 originais: esse
ciclo adicional de teste tem ganho líquido zero e não aumenta a contagem única.

A auditoria persistente registra intenção e conclusão em
`/var/lib/printora-cloud/recovery/wal-retention/*.jsonl`; inventários originais,
cutoff e comprovantes continuam em `recovery/incident-20260908`. Cópias locais
privadas: `.artifacts/wal-incident-20260908`, incluindo `retention-proof-final.log`,
`retention-lock-trace.log`, `installed-proof.log`, `installed-restore-final.log`
e `final-production-state.log`.

Leitura final às **16:22:21 UTC**:

| Medida | Resultado |
|---|---|
| Volume | 972.185.931.776 bytes; `df` 46% ocupado |
| Disponível | **505.866.477.568 bytes; 52,03% livres**, acima dos 15% exigidos |
| WAL completos locais | 1.467; 24.612.175.872 bytes |
| Primeiro WAL preservado por horário | 2026-09-05 12:12:26.746751 UTC |
| Último WAL local e confirmado externamente | `000000010000007D0000003A` |
| Último check de sincronização | 16:22:01 UTC; status passed, duração 51 s |
| PostgreSQL | pg_isready aceitando; pg_is_in_recovery=false; archive failures=0 |
| Checkpoints | timed avançou de 12 para 13 após a publicação; requested=4 |
| Printora | health, ready e catálogo HTTP 200; serviços e timers ativos |
| Recuperação | monitor passed, sem warnings/failures; backup e restore recentes |
| Erros de espaço | zero novos no journal desde 12:36 UTC e nos logs recentes amostrados |

A diferença entre o espaço logo após a drenagem e o final inclui novos WAL,
preparação de release e artefatos temporários do trabalho. Nenhum dado de usuário,
release ou backup externo foi removido para obter essa folga.

Riscos residuais: o host produtivo continua compartilhado e sem HA física; o
canal de alertas está no journal, sem webhook configurado. Disputa de lock ou
custódia/backup/restore indisponível adia a limpeza e exige acompanhamento da
capacidade. O check de integridade cobriu os snapshots necessários e houve
restore real; não se afirma um check global de todo o histórico Restic. Mudança
futura de backend exige preparar a imagem de recuperação compatível. Rollback:
suspender somente o timer de retenção, mantendo archive/sync/custódia; recompor
WAL pelo snapshot e checksum auditados se necessário. Não restaurar banco antigo
sobre escritas novas nem remover backups externos.
