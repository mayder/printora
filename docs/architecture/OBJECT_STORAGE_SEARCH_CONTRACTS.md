# Contratos De Objetos E Busca Cloud

## Fonte Canônica

PostgreSQL decide owner, finalidade, estado, checksum, tamanho, content type e
referências. MinIO armazena bytes privados e versões; uma chave existente nunca é
sobrescrita. Redis não participa de autorização ou existência canônica.

Estados persistidos de objeto: `quarantined`, `rejected`, `analyzed`, `promoted`,
`missing` e `corrupt`; a sessão de upload representa `receiving`, `uploaded`,
`validating`, `expired` e falhas transitórias. Somente `promoted` pode ser baixado, publicado ou consumido pelo
fatiamento. Promoção copia para uma chave content-addressed definitiva, confirma
checksum/tamanho por `HEAD` e muda o estado na mesma transação que cria a
referência. A quarentena não tem rota pública.

## Namespace

- `printora-quarantine`: uploads incompletos ou ainda não aprovados;
- `printora-objects`: arquivos promovidos de biblioteca e projetos;
- `printora-artifacts`: saídas internas de jobs e fatiamento.

Chaves não contêm e-mail, nome, path recebido ou ID sequencial previsível. O
formato dentro de cada bucket é `sha256/<sha256[0:2]>/<sha256>.<extensão>`.

No perfil `cloud`, `PRINTORA_OBJECT_STORAGE_MODE=s3` é obrigatório e não existe
fallback para filesystem. O adapter local permanece somente para desktop,
desenvolvimento e testes. A entrada HTTP é consumida por chunks, rejeita
`Content-Length` inválido e interrompe antes de ultrapassar 25 MiB; nenhum objeto
é criado antes de a recepção terminar.

## Autorização E Download

A aplicação usa uma access key sem administração de servidor. Download exige
referência válida, objeto promovido e permissão recalculada no PostgreSQL. O
cliente recebe token aleatório de uso único por 60 segundos para uma rota fixa da
aplicação e o envia no header `Authorization`; o token não entra em URL ou log de
acesso. Somente o hash é persistido. O cliente não recebe endpoint, bucket, chave
S3 ou credencial.

## Busca

O dado relacional continua canônico. O índice PostgreSQL `tsvector` é uma
materialização reconstruível, atualizada por outbox/job idempotente. A consulta
reaplica visibilidade, tenant, bloqueio e moderação; ranking nunca concede acesso.
Apagar o índice autoriza apenas rebuild, nunca apagar fonte.

O rebuild marca documentos anteriores como inativos e faz upsert da visão atual,
sem `DELETE`. O perfil local mantém `social_search_index`; o perfil Cloud consulta
somente `search_documents`, GIN e `websearch_to_tsquery('simple', ...)`. Eventos
da fonte carregam apenas nome da tabela, ID e operação.

## Backup E Rollback

Backup reúne dump PostgreSQL, manifesto de objetos/versões/checksums e conteúdo
exportado antes da criptografia externa. Restore usa destino isolado e só passa
quando metadado, versão e checksum reconciliam. Rollback de código preserva o
estado atual de banco e buckets.
