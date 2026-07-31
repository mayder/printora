# RUNBOOK.md

Runbook operacional do Printora.

## Evolução Arquitetural

Os procedimentos executáveis são adicionados lote a lote pelos pacotes
`PKG-86` a `PKG-95`. A arquitetura, gates e ordem ficam em
`docs/architecture/EVOLUCAO_ARQUITETURAL.md`.

O bootstrap privilegiado, o backup/restore externo, dois ciclos blue/green,
rollback e falhas de processo foram comprovados no host em 22 de julho de 2026.
A publicação cloud usa dois slots independentes e N-1 aquecido; a evidência fica
em `docs/audits/CLOUD_BLUE_GREEN_READINESS_2026-07-22.md`. Isso não representa
alta disponibilidade contra perda física do host.

Regras operacionais obrigatórias durante as transições:

- medir recursos do host antes de instalar novo serviço;
- não colocar destino em produção antes de restore, carga e sombra passarem;
- não fazer dual-write independente dentro do request;
- não restaurar snapshot antigo sobre escritas confirmadas após cutover;
- não excluir banco, tabela, arquivo, objeto ou backup sem confirmação explícita;
- remover bridges/flags/adapters e atualizar este runbook no mesmo pacote;
- manter relatório de integridade e referência legada junto ao release;
- executar tudo por systemd/Nginx no servidor atual, sem pressupor Docker.
- usar venv/frontend/unit imutáveis por release; nunca atualizar dependência do blue em uso;
- manter compatibilidade N/N-1 até requests, WebSockets e workers antigos drenarem;
- manter SQLite somente no perfil local; cloud não pode usá-lo como fallback;
- manter backup/WAL criptografado fora do host e testar restore sem a origem.

O alvo permite continuidade contra falha de processo e durante deploy. Pane
física do host continua exigindo restauração; não há HA física em um único
servidor.

## Pacotes De Confiança Planejados

Ordem para execução em outra janela:

1. `PKG-96`: gerar, publicar, instalar como canário e reverter o agente `0.1.34`;
2. `PKG-97`: tornar Node/cobertura/E2E/fuzz/mutation/pentest gates bloqueantes;
3. `PKG-98`: homologar agente/impressora reais e executar soak final de 72 horas;
4. `PKG-99`: reduzir RPO físico para até 5 minutos e repetir restore de desastre.

Durante `PKG-96` e `PKG-98`, leitura é permitida com impressão ativa; update,
restart do agente ou outra mutação exige impressora ociosa, janela aprovada e
rollback do agente. Esses pacotes não autorizam restart de Klipper/Moonraker,
flash, alteração de firmware ou exclusão de dados.

Pentest/carga/fuzz em produção exigem escopo e autorização separados.
`PKG-97` deve preferir ambiente isolado com dados sintéticos. `PKG-99` executa
restore em cluster temporário limitado; prune continua fora do fluxo automático
e exige preview mais confirmação explícita.

O gate local de cobertura do `PKG-97` é:

```bash
scripts/run-coverage-gate.sh
```

Os relatórios ficam em `.artifacts/coverage`. Regressão exige corrigir teste ou
código; não alterar limiar/baseline apenas para liberar build. Uma mudança
intencional exige decisão registrada e aprovação explícita.

Os demais gates automatizados do pacote são:

```bash
scripts/run-e2e-gate.sh
scripts/run-property-fuzz-gate.sh
scripts/run-mutation-gate.sh
scripts/run-pkg97-test-gates.sh
```

- E2E sobe backend e frontend compilado em porta isolada e grava relatório,
  trace/screenshot/vídeo somente quando aplicável em `.artifacts/e2e`;
- flakiness P0: usar `PRINTORA_E2E_REPEAT_EACH=10` sem retry;
- fuzz: corpus em `backend/tests/fixtures/fuzz-corpus.json`, seed padrão `970099`
  e nenhum dado de produção;
- mutation: limiar em `PATHS.toml`, estatísticas e lista completa de
  sobreviventes em `.artifacts/mutation`;
- o CI instala Chromium, executa os gates e preserva cobertura/E2E/mutation por
  30 dias, inclusive quando houver falha.

Pentest não é substituído por esses gates. Para o fechamento de 2026-07-23, o
owner dispensou explicitamente sua execução e aceitou o risco residual descrito
na `DEC-20260723-10`; nenhum teste interno deve ser apresentado como pentest ou
como prova equivalente. Antes de qualquer teste ativo futuro, exigir fornecedor
independente, autorização escrita, ambiente, alvos, janela, contatos, limites,
tratamento de dados e parada de emergência. Produção permanece fora do escopo
até autorização específica. Usar
`docs/audits/PENTEST_SCOPE_PKG_97_2026-07-23.md` como checklist contratual e
registro de autorização; campos pendentes não autorizam execução.

Ambientes isolados devem declarar administradores sintéticos fora do release:

```bash
PRINTORA_PLATFORM_ADMIN_EMAILS=pentest-admin@example.test
```

A lista aceita emails separados por vírgula. Valor vazio nega toda ação
administrativa; entrada inválida falha fechado. Produção pode manter o default
compatível até a variável ser configurada em janela controlada.

O endpoint público de cadastro rejeita emails dessa lista com `403`. A conta
administrativa deve existir antes da janela e ser provisionada localmente pelo
procedimento operacional do ambiente; nunca compartilhar senha ou sessão no
relatório de pentest.

Em base nova e isolada, criar um arquivo de senha com permissão `0600` e executar
uma única vez:

```bash
cd backend
PRINTORA_PLATFORM_ADMIN_EMAILS=pentest-admin@example.test \
  uv run python -m scripts.provision_platform_admin \
  --data-dir /caminho/isolado \
  --email pentest-admin@example.test \
  --password-file /caminho/seguro/admin-password \
  --display-name "Pentest Admin" \
  --initialize-empty
```

`--initialize-empty` é aceito apenas quando a base ainda não existe. Em base
existente, omitir a opção. A execução é idempotente, não redefine senha e imprime
somente ID, email, caminho da base, estado administrativo e se criou a conta.

Para preparar todas as contas, organizações e papéis do pentest, usar o
procedimento e o template em
`docs/audits/PENTEST_SCOPE_PKG_97_2026-07-23.md`. A preparação automatizada
rejeita produção, exige autorização vigente para target externo, não
sobrescreve manifesto e nunca grava senha ou token.

## Publicacao Cloud

O deploy publico planejado do Printora usa o dominio `print3dmaker.xyz`, com
GoDaddy apenas como registrador, DNS/proxy pela Cloudflare e o backend Python/systemd
atrás de Nginx no servidor. O guia operacional fica em
`docs/DEPLOY_CLOUD.md`.

O workflow `Deploy Printora Cloud` publica o SHA imutável disparado na branch
`cloud`. Primeiro executa o preflight rápido do servidor. Depois executa em
paralelo os gates static, E2E, property/fuzz, mutation e cobertura; empacotamento
e publicação só iniciam quando todos passam. O pytest da cobertura não é
repetido pelo `check.sh`. A publicação cria frontend e venv imutáveis dentro de cada release, sobe o slot
inativo em `8069` ou `8070`, valida `/ready`, `/health` e catálogo, testa a
configuração Nginx, troca o upstream atomicamente e só então drena o slot
anterior. Um preflight definitivo é repetido imediatamente antes do upload.
Se a prontidão de recuperação bloquear essa etapa, o workflow publica o relatório
sanitizado com a causa específica, sem expor credenciais, para evitar reruns
cegos do mesmo SHA.
Não existe fallback para matar processo manualmente ou atualizar venv
compartilhado. O usuário `deploy` só recebe sudo para os comandos fixos do
blue/green e da retenção definidos em
`packaging/sudoers/printora-cloud-deploy`.

Os workflows de deploy e rollback exigem o secret
`PRINTORA_SSH_KNOWN_HOSTS`. Ele deve conter a linha completa da chave pública
do host, obtida fora do workflow e conferida por fingerprint em canal
independente. Ausência do secret falha fechado antes da conexão. Não usar
`ssh-keyscan` durante o deploy, não aceitar chave nova automaticamente e não
substituir o secret sem validação operacional da rotação.

O bundle de produção exclui `.artifacts`, que contém apenas evidências de CI e
é publicado separadamente com retenção de 30 dias. O envio usa keep-alive SSH e
até três tentativas; falha persistente encerra o workflow antes de preparar ou
trocar o slot. Nunca incluir cobertura, traces, cópias temporárias de pytest ou
outros artefatos de validação no release executável.

Bootstrap único, executado por administrador do host depois de backup da
configuração Nginx:

```bash
sudo PRINTORA_POSTGRESQL_PASSWORD_FILE=/etc/printora-cloud/postgresql-password \
  scripts/cloud/bootstrap-postgresql.sh
sudo PRINTORA_BASE_PATH=/var/www/print3dmaker.xyz \
  scripts/cloud/bootstrap-blue-green.sh
sudo /usr/local/sbin/printora-cloud-preflight
```

O preflight só passa com NTP, certificado, logrotate, `restic`, destino externo,
cluster dedicado PostgreSQL, checksums, WAL e permissões válidos. O arquivo
`shared/backup-target.conf` deve ter modo `0600` e referenciar credenciais fora
do Git. A chave de recuperação precisa possuir cópia fora do host.

Retenção de releases:

```bash
sudo /usr/local/sbin/printora-cloud-retain-releases --dry-run
sudo /usr/local/sbin/printora-cloud-retain-releases --apply
```

O dry-run é obrigatório em intervenção manual. A aplicação recusa topologia
incompleta e preserva todo diretório apontado por `current`, `blue`, `green` ou
`replica`; por isso normalmente ficam dois releases, e não apenas um. Depois de
um deploy bem-sucedido, a retenção roda automaticamente e remove somente
diretórios SHA sem vínculo. Banco, storage, backup, WAL e dados compartilhados
ficam fora do escopo. O journal é limitado por
`packaging/systemd/journald-printora-cloud.conf` a 2 GB, com 15% do filesystem
reservado. O monitor registra aviso abaixo de 15% livre e o preflight continua
bloqueando abaixo de 10%.

A base física é semanal e o WAL externo permanece contínuo, com restore isolado
semanal. O gate avisa depois de 25 horas e bloqueia uma base acima de sete dias.
O backup on-host não roda sem o marcador explícito
`/etc/printora-cloud/allow-onhost-full-backup`, reservado a janela de manutenção:
o checkpoint físico degradou o endpoint mesmo limitado a 1 MiB/s no host atual.
Quando autorizado, o backup limita `pg_basebackup` a 1 MiB/s, o stream compactado
do `pg_dump` a 256 KiB/s e usa prioridade de I/O `idle`. Se `health` degradar,
interromper somente `printora-cloud-backup.service`, remover o marcador e manter
os serviços da aplicação intactos.

Validacao pos-deploy:

```bash
curl -fsS https://print3dmaker.xyz/health
curl -fsS https://print3dmaker.xyz/ready
curl -fsS https://print3dmaker.xyz/api/catalog >/dev/null
curl -fsS "https://print3dmaker.xyz/api/social/communities/variant-voron-design-voron-2-4-voron-2-4-r2-350/feed?page_size=1" >/dev/null
```

Rollback de código, sem restaurar banco:

```bash
sudo /usr/local/sbin/printora-cloud-rollback
```

## PostgreSQL Cloud

O runtime cloud usa exclusivamente o cluster PostgreSQL `16/printora` em
`127.0.0.1:5433`. A unit lê a credencial de
`/etc/printora-cloud/postgresql.env`; esse arquivo deve permanecer `root:deploy`
com modo `0640`. Ausência ou URL não PostgreSQL bloqueia a inicialização em vez
de cair para o adapter local.

Diagnóstico read-only:

```bash
systemctl is-active postgresql@16-printora.service
pg_isready -h 127.0.0.1 -p 5433 -d printora_cloud
sudo -u postgres psql -p 5433 -d printora_cloud -X -Atqc \
  "SELECT current_database(), current_setting('data_checksums'), current_setting('archive_mode')"
sudo -u postgres psql -p 5433 -d printora_cloud -X -Atqc \
  "SELECT count(*) FROM pg_constraint WHERE contype = 'f' AND NOT convalidated"
```

Backup externo criptografado, sem prune automático:

```bash
sudo systemctl start printora-cloud-backup.service
sudo journalctl -u printora-cloud-backup.service -n 50 --no-pager
```

Restore supervisionado em cluster efêmero, com limite de recurso no mesmo host:

```bash
sudo systemd-run --wait --collect \
  --unit=printora-cloud-restore-test \
  --property=CPUQuota=20% \
  --property='IOReadBandwidthMax=/dev/sda4 10M' \
  --property='IOWriteBandwidthMax=/dev/sda4 10M' \
  /usr/local/libexec/printora-cloud/restore-postgresql-backup-test.sh
```

O restore deve informar banco fora de recovery, tabelas, versões e zero FK
inválida. Ele não inicia o Printora e remove somente seu diretório temporário.
Rollback de aplicação sempre reutiliza o mesmo PostgreSQL e nunca restaura um
snapshot antigo sobre escritas confirmadas.

A origem anterior e seus backups permanecem preservados fora do runtime. Não os
remover sem relatório de integridade, janela de observação e confirmação
explícita. Evidência do cutover, backup, restore e rollback:
`docs/audits/POSTGRESQL_CLOUD_TRANSITION_2026-07-22.md`.

## Execução Durável, Workers E Redis

O PostgreSQL é canônico para outbox, inbox, idempotência, jobs, leases, sessões
e controle de workers. Redis é dedicado ao Printora, acessível somente pelo
socket `/run/redis-printora/redis.sock` e contém apenas cache, rate limit,
presença e pub/sub recomponíveis. Reiniciar ou esvaziar Redis não autoriza apagar
nem recriar dado de negócio.

Bootstrap privilegiado, depois do PostgreSQL e antes de habilitar workers:

```bash
sudo scripts/cloud/bootstrap-redis.sh
sudo PRINTORA_BASE_PATH=/var/www/print3dmaker.xyz scripts/cloud/bootstrap-blue-green.sh
sudo /usr/local/sbin/printora-cloud-preflight
```

Diagnóstico read-only:

```bash
systemctl is-active redis-printora.service printora-cloud-workers.target
systemctl is-active printora-cloud-worker@outbox.service
systemctl is-active printora-cloud-worker@critical.service
systemctl is-active printora-cloud-worker@default.service
systemctl is-active printora-cloud-worker@bulk.service
redis-cli -s /run/redis-printora/redis.sock ping
sudo -u deploy bash -c 'set -a; source /etc/printora-cloud/postgresql.env; set +a; /usr/local/libexec/printora-cloud/audit-durable-execution.py'
```

O deploy troca o app, atualiza o link `current`, envia `SIGTERM` aos workers,
aguarda o drain e inicia as classes na release imutável nova. Rollback para uma
release N-1 sem worker pausa as units; os jobs continuam no PostgreSQL até uma
release compatível voltar.

Antes de iniciar o slot candidato, o deploy aplica os scripts PostgreSQL
aditivos em transação e sob advisory lock com o papel proprietário. O usuário
runtime apenas valida o schema e permanece sem permissão de DDL.

Pausa e drain são estados canônicos em `worker_controls`. A API administrativa
deny-by-default expõe overview, controle e dead-letter em
`/api/admin/workers`; mutações aceitam `Idempotency-Key`, têm rate limit e não
retornam payload do job. Replay exige o `job_key` exato e gera evento de
auditoria antes de recolocar o item na fila.

Retenção é preview por padrão e nunca roda automaticamente:

```bash
sudo -u deploy bash -c 'set -a; source /etc/printora-cloud/postgresql.env; set +a; /usr/local/libexec/printora-cloud/retention-durable-execution.py'
```

Aplicação física da retenção exige janela, preview revisado, confirmação textual
exata e autorização para excluir os registros expirados. Não executar `--apply`
durante investigação ou sem aceite do responsável.

Falha de Redis:

- agentes retomam jobs pelo PostgreSQL/polling;
- cache é recomposto sob demanda;
- rate limit informa degradação interna e não vira fonte de autorização;
- reiniciar somente `redis-printora.service`; não reiniciar Moonraker, Klipper,
  agente da impressora ou MCU.

Evidência: `docs/audits/DURABLE_EXECUTION_2026-07-22.md`.

## Preview operacional de G-code

A aba `Operacao` do detalhe da impressora usa cache sob demanda do G-code para
renderizar a prévia 3D no navegador. O agente atua como ponte leve para buscar o
arquivo local no Moonraker/Raspberry; ele não recalcula a cena em todo snapshot
de status.

Validação local:

```bash
npm --prefix frontend run build
cd agent && go test ./...
python3 -m compileall backend/app
./check.sh
RUN_FRONTEND_CHECKS=1 ./check.sh
```

Validação manual publicada:

- atualizar o agente quando o card indicar versão esperada nova;
- abrir `https://print3dmaker.xyz`, entrar em `Impressoras > <impressora> > Operacao`;
- durante impressão, confirmar que o card `Impressão` carrega thumbnail, camada, progresso e preview 3D;
- confirmar que o preview usa o G-code cacheado e não baixa o arquivo completo repetidamente a cada status;
- girar, aproximar, afastar, mover e enquadrar a peça com mouse, toolbar e viewbox nativo;
- se o cache ou agente falhar, a tela deve cair para estado compacto, sem erro bruto e sem reservar área vazia grande.

Impacto operacional:

- atualização do agente reinicia apenas `printora-agent`;
- não reinicia Klipper, Moonraker ou firmware;
- pode interromper leituras do Printora por alguns segundos, mas não deve interromper a impressão em andamento.

Rollback:

- publicar a versão anterior da branch `cloud`;
- se necessário, ocultar `GcodePrintViewer` e voltar a prévia amostrada como fallback principal;
- manter o endpoint/cache como legado inerte até remoção posterior, sem apagar arquivos remotos manualmente.

Feed técnico por comunidade:

```bash
curl -fsS "http://127.0.0.1:8069/api/social/communities/<slug>/feed?order=recommended&page_size=10"
```

O schema do feed é aplicado por `backend/sql/044_social_community_feed.sql`.
O inicializador cria backup automático do SQLite antes de aplicar scripts
pendentes em banco existente. Rollback estrutural exige restaurar o backup do
SQLite anterior ao script `044_social_community_feed.sql`; não execute `DELETE`
manual em itens de feed sem confirmação explícita.

Discussões técnicas:

```bash
curl -fsS "http://127.0.0.1:8069/api/social/posts/<post_id>/discussion"
```

O schema de posts/comentários/reações é aplicado por
`backend/sql/045_social_discussions.sql`. Remoção de post ou comentário é lógica
por `deleted_at`; não execute `DELETE` manual em discussões, comentários,
reações ou histórico sem confirmação explícita. Rollback estrutural exige
restaurar backup SQLite anterior ao script `045_social_discussions.sql`.

Projetos de impressão e compatibilidade legada:

O domínio canônico para conteúdo imprimível é `Projeto de impressão`.
Arquivos, versões, compartilhamentos em comunidade, publicação, jobs de
fatiamento, entregas de G-code e histórico são relações ou derivados do projeto.
Comunidades são apenas canais de descoberta/compartilhamento; Administração é
configuração, diagnóstico, política e fallback operacional.

Os endpoints `/api/social/library*` e telas antigas de comunidade descritos
abaixo existem como base legada/compatibilidade até a migração dos PKG-77 a
PKG-81. Eles não devem orientar implementação nova como se comunidade fosse dona
de arquivo ou projeto. Novos fluxos devem criar/editar/publicar/fatiar/enviar a
partir de `Projetos de impressão`.

Contrato e exploração inicial:

```bash
curl -fsS "http://127.0.0.1:8069/api/print-projects/contract"
curl -fsS "http://127.0.0.1:8069/api/print-projects?limit=5"
curl -fsS "http://127.0.0.1:8069/api/print-projects/<slug>"
curl -fsS "http://127.0.0.1:8069/api/social/communities/<slug>/projects"
```

O schema central inicial é aplicado por
`backend/sql/068_print_projects_core.sql`. Ele cria projetos, arquivos,
versões/snapshots e compartilhamentos N:N com comunidades sem apagar ou migrar
automaticamente tabelas legadas. Rollback funcional remove a entrada de menu e
rotas `/api/print-projects*`, mantendo dados como legado; rollback estrutural
exige restaurar backup SQLite anterior ao script `068_print_projects_core.sql`.

`backend/sql/069_print_project_experience.sql` adiciona salvamentos pessoais de
projeto por referência, sem copiar arquivo. A ação autenticada:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"save_kind":"reference"}' \
  "http://127.0.0.1:8069/api/print-projects/<project_id>/save"
```

Compartilhamento com comunidade é relação N:N:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"community_slug":"<slug>"}' \
  "http://127.0.0.1:8069/api/print-projects/<project_id>/communities"
```

Essas ações não alteram ownership, arquivos, visibilidade, publicação ou
classificação comercial do projeto. Rollback funcional remove UI/rotas novas e
mantém os dados; rollback estrutural exige backup SQLite anterior ao script
`069_print_project_experience.sql`.

Biblioteca de arquivos legada:

```bash
curl -fsS "http://127.0.0.1:8069/api/social/communities/<slug>/library"
curl -fsS -X POST "http://127.0.0.1:8069/api/social/library/<item_id>/downloads"
```

O schema da biblioteca base é aplicado por
`backend/sql/046_social_library_items.sql`. O pacote registra metadados de
STL/3MF/ZIP e histórico de downloads; upload binário, quarentena e análise ficam
em pacote posterior. Remoção de item é arquivamento lógico por `status`; não
execute `DELETE` manual em itens, arquivos ou downloads sem confirmação
explícita. Rollback estrutural exige restaurar backup SQLite anterior ao script
`046_social_library_items.sql`.

Upload e quarentena de arquivos 3D legados:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @modelo.stl \
  "http://127.0.0.1:8069/api/social/library/<item_id>/files/upload?file_name=modelo.stl"
```

O schema de upload é aplicado por `backend/sql/047_social_library_uploads.sql`.
Arquivos válidos ficam em `<data_dir>/library_uploads/quarantine` com nome
derivado de SHA-256; arquivos rejeitados também registram motivo para auditoria.
Não mova arquivo de quarentena para download/fatiamento manualmente. Rollback
funcional remove endpoint/UI de upload e mantém metadados; rollback estrutural
exige backup SQLite anterior ao script `047_social_library_uploads.sql` e
limpeza manual do diretório de quarentena somente após confirmação explícita.

Análise técnica e preview:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  "http://127.0.0.1:8069/api/social/library/files/<file_id>/analysis"
```

O schema de análise é aplicado por `backend/sql/048_social_library_analysis.sql`.
A análise usa apenas parsers controlados de STL/3MF/ZIP e grava metadados em
`analysis_json`, preview SVG em `thumbnail_svg` e timestamp em `analyzed_at`.
Falha de análise deve ficar em `analysis_failed` no arquivo; não bloqueie a
biblioteca inteira. Rollback funcional remove endpoint/UI de análise e mantém
metadados; rollback estrutural exige backup SQLite anterior ao script
`048_social_library_analysis.sql`.

Licenças, autoria e atribuição:

O schema de direitos de uso é aplicado por
`backend/sql/049_social_library_license_attribution.sql`. Itens `public` ou
`community` exigem autoria original, licença e aceite de termos. Fonte pública e
atribuição são metadados do item e devem acompanhar download/listagem. Rollback
funcional remove validações/UI de licença avançada e mantém dados; rollback
estrutural exige backup SQLite anterior ao script
`049_social_library_license_attribution.sql`.

Versionamento legado de arquivos/modelos:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"version_label":"v2","changelog":"Ajuste de encaixe","files":[{"file_kind":"stl","file_name":"modelo-v2.stl"}]}' \
  "http://127.0.0.1:8069/api/social/library/<item_id>/versions"

curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  "http://127.0.0.1:8069/api/social/library/<item_id>/versions/<version_id>/current"

curl -fsS -X POST \
  "http://127.0.0.1:8069/api/social/library/<item_id>/versions/<version_id>/downloads"
```

O schema de versionamento é aplicado por
`backend/sql/050_social_library_versions.sql`. Versões guardam snapshot imutável
de arquivos e metadados em JSON, changelog e marcador de versão atual. Rollback
funcional promove uma versão anterior como atual; não execute `DELETE` manual em
versões ou downloads sem confirmação explícita. Rollback estrutural exige backup
SQLite anterior ao script `050_social_library_versions.sql`.

Organizador legado da biblioteca:

```bash
curl -fsS -H "Authorization: Bearer <token>" \
  "http://127.0.0.1:8069/api/social/me/library/organizer"

curl -fsS -X POST -H "Authorization: Bearer <token>" \
  "http://127.0.0.1:8069/api/social/library/<item_id>/favorite"

curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Peças da Voron","visibility":"private"}' \
  "http://127.0.0.1:8069/api/social/library/collections"

curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"item_id":1,"version_id":1}' \
  "http://127.0.0.1:8069/api/social/library/collections/<collection_id>/items"

curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Fila ABS","printer_id":1}' \
  "http://127.0.0.1:8069/api/social/print-lists"

curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"item_id":1,"version_id":1,"status":"want_to_print"}' \
  "http://127.0.0.1:8069/api/social/print-lists/<print_list_id>/items"
```

O schema do organizador é aplicado por
`backend/sql/051_social_library_organizer.sql`. Coleções privadas e listas de
impressão são sempre filtradas pelo dono; listas legadas referenciam uma versão
específica do item/modelo. No domínio novo, listas devem apontar para projeto e
snapshot. Não execute `DELETE` manual em favoritos, coleções, listas ou
histórico sem confirmação explícita. Rollback estrutural exige backup SQLite
anterior ao script `051_social_library_organizer.sql`.

Histórico de impressão e feedback legado:

```bash
curl -fsS -H "Authorization: Bearer <token>" \
  "http://127.0.0.1:8069/api/slicing/history"

curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"outcome":"worked","visibility":"private","note":"ABS ok"}' \
  "http://127.0.0.1:8069/api/slicing/history/<history_id>/feedback"
```

O schema é aplicado por `backend/sql/065_print_job_history.sql`.
Histórico e feedback têm retenção padrão de 180 dias. Payload público remove
identificador privado da impressora e reduz telemetria. No domínio novo, sinais
públicos devem ser agregados/sanitizados por projeto/material/perfil/tipo
técnico e nunca por cópia de comunidade. Rollback funcional remove endpoints/UI
de histórico e mantém dados como legado; rollback estrutural exige restaurar
backup SQLite anterior ao script `065_print_job_history.sql`.

Marketplace e curadoria comercial legados:

```bash
curl -fsS -X POST \
  -H "Authorization: Bearer <token-admin>" \
  -H "Content-Type: application/json" \
  -d '{"status":"approved","note":"Revisado para destaque premium"}' \
  "http://127.0.0.1:8069/api/social/library/<item_id>/commercial-review"
```

O schema é aplicado por
`backend/sql/066_social_library_commercial_curation.sql`. Conteúdo premium ou
patrocinado público exige revisão aprovada. Patrocinado deve exibir aviso de
transparência. Não há cobrança real neste fluxo. No domínio novo, classificação
comercial pertence ao projeto central e é independente de compartilhamentos em
comunidade. Rollback funcional remove revisão comercial e UI de transparência;
rollback estrutural exige backup SQLite anterior ao script
`066_social_library_commercial_curation.sql`.

Fontes externas e bookmarks legados:

```bash
curl -fsS -H "Authorization: Bearer <token>" \
  "http://127.0.0.1:8069/api/social/external-library/preview?external_url=https://example.com/model.stl"

curl -fsS -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"Modelo externo","external_url":"https://example.com/model.stl","attribution_text":"Fonte externa: example.com","import_mode":"bookmark"}' \
  "http://127.0.0.1:8069/api/social/external-library/references"
```

O schema é aplicado por `backend/sql/067_external_library_imports.sql`.
Bookmark externo não copia arquivo. Importação controlada registra metadados,
licença, atribuição e checksum opcional para deduplicação. Falha de fonte externa
não deve bloquear a biblioteca/projetos locais. Bookmark externo não permite
fatiamento ou envio enquanto não houver arquivo hospedado/importado, validado e
autorizado no projeto. Rollback funcional remove endpoints/UI de
fontes externas; rollback estrutural exige backup SQLite anterior ao script
`067_external_library_imports.sql`.

Configurações técnicas compartilhadas:

```bash
curl -fsS -H "Authorization: Bearer <token>" \
  "http://127.0.0.1:8069/api/social/me/technical-configs"

curl -fsS \
  "http://127.0.0.1:8069/api/social/communities/<slug>/technical-configs"

curl -fsS \
  "http://127.0.0.1:8069/api/social/communities/<slug>/technical-configs/comparison"
```

O schema de configurações técnicas públicas é aplicado por
`backend/sql/052_social_technical_printer_configs.sql`. Esses registros são
perfil social técnico, não permissão operacional, e não devem conter Moonraker,
agente, SSH, token, IP, host, caminho local ou credencial. Remoção pela API é
arquivamento lógico; não execute `DELETE` manual sem confirmação explícita.
Rollback funcional remove endpoints/UI de perfis técnicos e mantém os dados como
legado; rollback estrutural exige backup SQLite anterior ao script
`052_social_technical_printer_configs.sql`.

Busca social e descoberta:

```bash
curl -fsS \
  "http://127.0.0.1:8069/api/social/search?q=Voron&page_size=5"

curl -fsS \
  "http://127.0.0.1:8069/api/social/search?material=ABS&file_kind=stl&page_size=5"

curl -fsS \
  "http://127.0.0.1:8069/api/social/tags"

curl -fsS \
  "http://127.0.0.1:8069/api/social/recommendations?q=Voron&page_size=4"

curl -fsS \
  "http://127.0.0.1:8069/api/social/reputation?limit=5"
```

O schema de busca social é aplicado por
`backend/sql/054_social_search_discovery.sql`. O índice agrega somente conteúdo
público ou comunitário de comunidades, discussões, biblioteca, configurações
técnicas, perfis de material e catálogo. Conteúdo privado não entra no índice.
A curadoria de tags usa `catalog_audit_events` existente, sem nova tabela de
auditoria. Rollback funcional remove endpoints/UI de busca e mantém os dados
como legado; rollback estrutural exige backup SQLite anterior ao script
`054_social_search_discovery.sql`.

O schema de ranking/reputação social é aplicado por
`backend/sql/055_social_ranking_reputation.sql` e estado materializado em
`backend/sql/056_social_materialization_state.sql`. O score é determinístico e usa
sinais públicos derivados de downloads, favoritos, soluções e reações,
ignorando auto-voto. Sinais de denúncia/moderação reduzem exposição quando
existirem. Rollback funcional remove endpoints/UI de recomendações e mantém os
dados como legado; rollback estrutural exige backup SQLite anterior ao script
`055_social_ranking_reputation.sql` e `056_social_materialization_state.sql`.
Se a tabela derivada `social_materialization_state` ficar com schema malformado
durante uma publicação interrompida, a inicialização cria backup `.before-schema`
e reconstrói apenas essa tabela de cache.

O schema de moderação social é aplicado por
`backend/sql/057_social_moderation.sql`. Usuários autenticados podem denunciar
conteúdo social existente por `POST /api/social/reports`; a fila e as ações ficam
restritas ao suporte autorizado em `GET /api/social/moderation/queue` e
`POST /api/social/moderation/reports/{report_id}/actions`.

Operação:

- usar a tela `Catálogo > Moderação` para filtrar denúncias abertas, em revisão,
  resolvidas ou descartadas;
- toda ação exige motivo auditável e registra estado anterior/novo em
  `social_moderation_actions`;
- ocultar, remover e bloquear alteram estado lógico do conteúdo, sem apagar
  linha de dados;
- restaurar reverte o estado lógico quando a entidade suporta restauração;
- curadoria de tags, comunidades e variações de catálogo deve usar estados
  válidos do domínio, nunca `DELETE` manual.

Validação pós-publicação:

```bash
curl -fsS "https://<host>/api/system/version"
curl -fsS -H "Authorization: Bearer <admin-token>" \
  "https://<host>/api/social/moderation/queue"
```

Rollback:

- rollback funcional: remover UI/rotas de moderação e manter tabelas como
  legado auditável;
- rollback de ação: aplicar ação `restore` na fila administrativa quando a
  entidade suportar restauração;
- rollback estrutural: restaurar backup SQLite anterior ao script
  `057_social_moderation.sql`;
- não apagar `social_moderation_reports`, `social_moderation_actions` nem
  entidades moderadas sem confirmação explícita.

Retenção:

- denúncias e ações são trilha de auditoria social e seguem a política de
  retenção operacional de auditoria definida no projeto;
- qualquer limpeza futura deve ser job/scritp supervisionado, idempotente e com
  janela de retenção documentada antes da execução.

O schema de notificações sociais é aplicado por
`backend/sql/058_social_notifications.sql`. A central in-app usa
`GET /api/social/notifications`; preferências usam
`PUT /api/social/notifications/preferences`; acompanhamentos usam
`POST /api/social/content-follows` e
`DELETE /api/social/content-follows/{entity_type}/{entity_id}`.

Operação:

- notificações sociais ficam na tela `Social > Notificações`;
- alertas de impressora, agente, Moonraker, firmware, manutenção ou suporte não
  entram na central social;
- usuário pode desligar notificação in-app por tipo;
- usuário pode acompanhar ou silenciar conteúdo específico;
- digest é agrupamento in-app pendente, sem envio externo nesta etapa;
- bloqueio social impede notificação entre usuários bloqueados.

Validação pós-publicação:

```bash
curl -fsS -H "Authorization: Bearer <token>" \
  "https://<host>/api/social/notifications"
```

Rollback:

- rollback funcional: remover a aba, rotas e integrações de emissão, mantendo
  tabelas como legado;
- rollback estrutural: restaurar backup SQLite anterior ao script
  `058_social_notifications.sql`;
- não apagar notificações, preferências ou follows sem confirmação explícita.

Retenção:

- notificações e follows são dados sociais do usuário, não log operacional;
- qualquer limpeza futura deve respeitar preferências/privacidade e ter janela
  de retenção documentada antes da execução.

Perfis de material e fatiamento:

```bash
curl -fsS -H "Authorization: Bearer <token>" \
  "http://127.0.0.1:8069/api/social/me/material-profiles"

curl -fsS \
  "http://127.0.0.1:8069/api/social/communities/<slug>/material-profiles"

curl -fsS \
  "http://127.0.0.1:8069/api/social/material-profiles/<profile_id>/export"
```

O schema de perfis de material/fatiamento é aplicado por
`backend/sql/053_social_material_slicing_profiles.sql`. Perfis compartilhados
guardam marca/tipo de material, nozzle, temperaturas, fluxo, compatibilidade e
parâmetros de fatiamento, mas não aplicam configuração na impressora. Remoção
pela API é arquivamento lógico. Rollback funcional remove endpoints/UI de perfis
de material e mantém os dados como legado; rollback estrutural exige backup
SQLite anterior ao script `053_social_material_slicing_profiles.sql`.

## Comandos principais

```bash
./check.sh
```

O `check.sh` da raiz e o ponto oficial de validacao do monorepo. Ele valida o modelo, compila o backend, valida o pacote frontend e executa checks leves por padrao.

## Desenvolvimento local

Backend:

```bash
./scripts/dev_backend.sh
```

Frontend:

```bash
./scripts/dev_frontend.sh
```

Aplicacao completa:

```bash
./scripts/run_app.sh
```

Diagnostico de instalacao:

```bash
PRINTORA_PORT=8069 ./scripts/doctor_install.sh
```

Em ambiente cloud, esse diagnostico nao fica na tela global. Para host de
impressora, use `Detalhe do agente > Doctor remoto`; para diagnostico local do
servidor, use o script acima no host da instalacao.

Setup do Zero via SSH:

```bash
curl -s -X POST http://127.0.0.1:8069/api/setup/ssh/preflight \
  -H 'Content-Type: application/json' \
  -d '{"host":"btt-pi.local","port":22,"username":"pi","auth_method":"agent","timeout_seconds":12}'

curl -s -X POST http://127.0.0.1:8069/api/setup/ssh/plan \
  -H 'Content-Type: application/json' \
  -d '{"host":"btt-pi.local","port":22,"username":"pi","auth_method":"agent","timeout_seconds":12}'

curl -s http://127.0.0.1:8069/api/setup/ssh/history
```

O PKG-34 exige que a Pi ja tenha Linux, rede e SSH ativo. Placa virgem sem
sistema operacional nao pode ser acessada por SSH; primeiro grave a mídia/boot,
habilite SSH e confirme o primeiro login. O preflight coleta somente dados
read-only. O plano retorna comandos prefixados por `PLAN` e nao executa
instalacao real, `apt`, edicao de arquivo, restart, flash, G-code ou alteracao
de Klipper/Moonraker.

Setup CAN/U2C/can0 via SSH:

```bash
curl -s -X POST http://127.0.0.1:8069/api/setup/can/preflight \
  -H 'Content-Type: application/json' \
  -d '{"target":{"host":"btt-pi.local","port":22,"username":"pi","auth_method":"agent","timeout_seconds":12},"interface_name":"can0","bitrate":1000000}'

curl -s -X POST http://127.0.0.1:8069/api/setup/can/plan \
  -H 'Content-Type: application/json' \
  -d '{"target":{"host":"btt-pi.local","port":22,"username":"pi","auth_method":"agent","timeout_seconds":12},"interface_name":"can0","bitrate":1000000}'

curl -s http://127.0.0.1:8069/api/setup/can/history
```

O apply CAN real fica bloqueado por padrão. Para executar em host real, o
processo do backend precisa estar com `PRINTORA_CAN_SETUP_MODE=remote` e o
payload precisa incluir `confirmation=CONFIGURAR CAN0`. Antes de alterar o host,
o backend roda preflight, bloqueia impressão em andamento quando detectável,
exige `sudo -n`, cria backup remoto de `/etc/systemd/system/can0.service` em
`~/.local/share/printora/can-setup/backups/<timestamp>/`, escreve o serviço
`can0.service`, roda `systemctl daemon-reload`, `enable`, `restart` e valida
`ip -details -statistics link show can0`.

Rollback CAN:

```bash
sudo cp ~/.local/share/printora/can-setup/backups/<timestamp>/can0.service.before /etc/systemd/system/can0.service
sudo systemctl daemon-reload
sudo systemctl restart can0.service
ip -details -statistics link show can0
```

Se não havia serviço anterior, o rollback é desabilitar/remover o serviço criado
e recarregar o systemd:

```bash
sudo systemctl disable --now can0.service
sudo rm -f /etc/systemd/system/can0.service
sudo systemctl daemon-reload
```

Wizard remoto de firmware:

```bash
curl -s -X POST http://127.0.0.1:8069/api/setup/firmware/plan \
  -H 'Content-Type: application/json' \
  -d '{"target":{"host":"btt-pi.local","port":22,"username":"pi","auth_method":"agent","timeout_seconds":12},"preset_id":"btt_octopus_pro_h723_usb_can","board_name":"Octopus Pro H723","board_role":"mainboard","can_interface":"can0","klipper_path":"~/klipper","output_root":"~/.local/share/printora/firmware-setup","variant_confirmed":true}'

curl -s http://127.0.0.1:8069/api/setup/firmware/history
```

O build remoto real fica bloqueado por padrão. Para executar em host real, o
processo do backend precisa estar com `PRINTORA_REMOTE_FIRMWARE_BUILD_MODE=remote`
e o payload precisa incluir `confirmation=BUILD_FIRMWARE_NO_FLASH`. O build:

- salva o `.config` gerado em diretório controlado do Printora;
- cria backup de `<klipper_path>/.config`;
- substitui `.config` apenas durante o build;
- executa `make clean && make`;
- copia o binário para os artefatos Printora;
- calcula hash do `.config` e do binário;
- consulta UUIDs CAN quando `~/klippy-env` e `canbus_query.py` existirem;
- restaura `.config` com `trap` em sucesso ou falha;
- nunca executa flash, restart, update, G-code ou edição de `printer.cfg`.

Rollback firmware build:

```bash
cp ~/.local/share/printora/firmware-setup/<placa>/.config.before-build ~/klipper/.config
rm -rf ~/.local/share/printora/firmware-setup/<placa>
```

Instalação com boot automático:

```bash
./scripts/install-macos.sh
./scripts/install-linux.sh
./scripts/install-android-termux.sh
```

No Windows:

```powershell
.\scripts\install-windows.ps1
```

Os instaladores publicos verificam o ambiente, exibem o que ja esta OK e
perguntam antes de instalar dependencias ausentes. O instalador interno
`scripts/install_printora.sh --apply --yes` continua existindo para automacao.
Ele prepara dependencias, usa Node local via `nvm` quando o Node global for
antigo, procura Python 3.11+ sem remover Python antigo do usuario e configura o
mecanismo de boot do ambiente atual. A porta padrao do Printora e `8069`.

Destravar update local orfao:

```bash
./scripts/unlock_update.sh
```

O script cria backup do `printora.db` no mesmo diretorio antes de marcar runs
`running` como `failed`. Em cloud, a UI de `Administracao > Historico da plataforma`
e informativa; reconciliacao de travados e rotina de suporte/admin via script.

Updater local macOS/Linux/Raspberry:

```bash
./scripts/update_printora.sh --plan --tag v0.1.1
./scripts/update_printora.sh --apply --tag v0.1.1
./scripts/update_printora.sh --rollback --previous-path /caminho/Printora.previous-update-YYYYMMDDTHHMMSSZ
```

O script detecta macOS sem systemd, Linux/Raspberry com systemd e Linux sem systemd. Quando `printora.service` existe, reinicia somente esse serviço; sem systemd, tenta `tmux` ou `scripts/run_app.sh`.
Em Linux/Raspberry com systemd, o run pode ser finalizado antes do restart
efetivo, pois o `systemctl restart printora.service` encerra o processo antigo
que iniciou o update. A validacao operacional depois do restart continua sendo
`/openapi.json` ou o historico em `Administracao > Historico da plataforma`.
Os instaladores Linux/Raspberry criam `/etc/sudoers.d/printora-restart` com
permissao minima para o usuario do servico executar `systemctl restart/status
printora.service` sem senha. Isso e necessario para update automatico do app,
porque o backend roda sem terminal interativo.

Log de update iniciado pela UI:

```bash
~/.local/share/printora/logs/self-update-run-<id>.log
```

No Android/Termux, o banco e os backups ficam em `~/.local/share/printora/`.
Se a UI cair durante o restart, consultar `Administracao > Historico da plataforma`
ou enviar esse log junto com o diagnostico local gerado pelo script.

Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_app_windows.ps1
```

Updater Windows:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\update_printora_windows.ps1 --Plan --Tag v0.1.1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\update_printora_windows.ps1 --Apply --Tag v0.1.1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\update_printora_windows.ps1 --Rollback --PreviousPath C:\caminho\Printora.previous-update-YYYYMMDDTHHMMSSZ
```

O updater Windows usa apenas escopo de processo para a política de execução, cria backup de `%LOCALAPPDATA%\Printora\printora.db`, preserva a pasta anterior do projeto e reinicia pelo runner Windows.

## Catalogo firmware CANBus

O catalogo do PKG-30 usa o guia Esoterical CANBus como fonte publica, mas o runtime do Printora consulta somente arquivos locais versionados em `backend/app/data/`.

## Social, catálogo mestre e comunidades

Endpoints principais:

```bash
curl -s http://127.0.0.1:8069/api/catalog
curl -s "http://127.0.0.1:8069/api/catalog/admin?manufacturer=rat&trust_state=official" -H "Authorization: Bearer <token>"
curl -s http://127.0.0.1:8069/api/social/communities
curl -s "http://127.0.0.1:8069/api/social/communities?manufacturer=voron-design&model=voron-2-4&variant=voron-2-4-r2-350&component=stealthburner" -H "Authorization: Bearer <token>"
curl -s http://127.0.0.1:8069/api/social/communities/<community_slug> -H "Authorization: Bearer <token>"
curl -s http://127.0.0.1:8069/api/social/me/profile -H "Authorization: Bearer <token>"
curl -s http://127.0.0.1:8069/api/social/profiles/<slug>
curl -s http://127.0.0.1:8069/api/social/profiles
curl -s http://127.0.0.1:8069/api/social/profiles/<slug>/printers
curl -s "http://127.0.0.1:8069/api/social/printers?manufacturer=voron&mod=tap"
curl -s http://127.0.0.1:8069/api/public/printers/<printer_id>
curl -s "http://127.0.0.1:8069/api/social/search?q=Voron&page_size=5"
curl -s http://127.0.0.1:8069/api/social/tags
curl -s "http://127.0.0.1:8069/api/social/recommendations?q=Voron&page_size=4"
curl -s "http://127.0.0.1:8069/api/social/reputation?limit=5"
```

Tela Social:

- abrir `/?section=social` autenticado;
- validar abas `Descoberta`, `Comunidades`, `Impressoras`, `Makers` e `Relações`;
- confirmar que a primeira tela não mostra formulário principal de edição de perfil, publicação/despublicação de impressora ou curadoria administrativa de catálogo;
- na aba `Descoberta`, validar busca textual, filtros por tipo/tag/material/componente/licença/arquivo, facetas, ordenação, paginação, estados vazios e abertura do resultado;
- na aba `Descoberta`, validar recomendações técnicas com motivo visível, score, reputação e ausência de auto-voto na explicação;
- na aba `Comunidades`, validar filtros por fabricante, modelo, variante e componente, contagens e abertura de `/c/<community_slug>`;
- na aba `Impressoras`, validar filtros por fabricante, modelo, variante e mod, cards com nome público, variante, mods e dono, e abertura de `/p/<printer_id>`;
- na aba `Makers`, validar diretório/busca de perfis públicos, bio curta, contagem de impressoras públicas e abertura de `/u/<slug>`;
- na aba `Relações`, validar resumo de seguindo, seguidores, amigos e solicitações; ações completas devem permanecer nos perfis públicos ou em `Conta > Perfil`;
- inspecionar payloads públicos e confirmar ausência de Moonraker, SSH, agente, token, IP operacional, organização e permissões.

Perfil social do usuário:

- abrir o menu do usuário logado no topo e entrar em `Perfil`;
- na aba `Público`, conferir separação entre dados da conta operacional e perfil público/social;
- validar nome público, slug, URL final `/u/<slug>`, bio, avatar HTTPS, localização opcional, links permitidos, privacidade e prévia pública;
- trocar slug apenas com ciência de que a URL muda e o slug anterior fica reservado;
- testar rejeição de slug duplicado, slug antigo de outro usuário, avatar/link `http://`, localhost, IP privado e host social não permitido;
- publicar uma impressora no detalhe da impressora real, seção `Publicação da impressora`, com variante canônica, prévia, mods e imagens HTTPS públicas;
- conferir que a impressora aparece em `Conta > Perfil > Público`, em `/u/<slug>`, na busca pública `/api/social/printers` e em `/p/<printer_id>`;
- validar que imagem `http://`, localhost, IP privado ou host interno é rejeitada antes de publicar;
- tornar a impressora privada e confirmar que `/p/<printer_id>` retorna indisponível/404, a busca pública não lista o item e comunidades derivadas ficam sem vínculo ativo;
- abrir `/u/<slug>` sem sessão e confirmar que não aparecem email, WhatsApp, organização, permissão, agente, Moonraker, SSH, token, IP ou host operacional;
- validar `private` como indisponível publicamente e `unlisted` como acessível por URL direta.

Curadoria administrativa:

- abrir `/?section=catalog`;
- filtrar por fabricante, modelo, tamanho/versão, componente, cinemática, firmware ou `trust_state`;
- usuários autenticados comuns podem navegar e consultar detalhes em modo leitura;
- revisar detalhe do fabricante/modelo antes de editar volume útil, componentes, firmware ou estado da variação;
- conferir logo, resumo, links de site, repositório, documentação, BOM, Discord e Reddit quando existirem; se a fonte não estiver segura, manter `community` ou `draft`;
- revisar a ficha de curadoria e as fontes usadas antes de promover um item;
- usar monograma quando não houver logo oficial/GitHub confiável, em vez de inventar imagem;
- promover `community` para `official` somente depois de revisão de fonte/variante;
- manter `draft` quando volume/componentes forem incertos;
- usar `obsolete` para item substituído que ainda pode existir em impressoras vinculadas;
- usar `blocked` para item incorreto, fora do recorte ou inseguro que não deve aparecer em consulta pública nem na curadoria padrão; consultar bloqueados pelo filtro `trust_state=blocked`;
- não apagar variantes com impressoras vinculadas; para merge/rename, criar/curar destino e manter origem como `obsolete` até migração revisada.

Publicação de impressora:

```bash
curl -s -X PUT http://127.0.0.1:8069/api/printers/1/public-profile \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"public_profile_enabled":true,"catalog_variant_id":1,"public_name":"Voron ABS","public_description":"Perfil público","public_mods":["Tap"]}'
```

Despublicação:

```bash
curl -s -X PUT http://127.0.0.1:8069/api/printers/1/public-profile \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"public_profile_enabled":false}'
```

O payload público de impressora não retorna Moonraker, SSH, agente, token, IP
ou credencial. Comunidades são sincronizadas automaticamente quando a impressora
é publicada/despublicada. Relações sociais e bloqueios não alteram organizações,
ownership ou permissões operacionais.

Grafo social e bloqueios:

```bash
curl -s -X POST http://127.0.0.1:8069/api/social/relationships/<target_user_id>/follow -H "Authorization: Bearer <token>"
curl -s -X DELETE http://127.0.0.1:8069/api/social/relationships/<target_user_id>/follow -H "Authorization: Bearer <token>"
curl -s -X POST http://127.0.0.1:8069/api/social/relationships/<target_user_id>/friend-request -H "Authorization: Bearer <token>"
curl -s -X POST http://127.0.0.1:8069/api/social/relationships/<requester_user_id>/friend-accept -H "Authorization: Bearer <token>"
curl -s -X POST http://127.0.0.1:8069/api/social/relationships/<requester_user_id>/friend-reject -H "Authorization: Bearer <token>"
curl -s -X DELETE http://127.0.0.1:8069/api/social/relationships/<target_user_id>/friend-request -H "Authorization: Bearer <token>"
curl -s -X DELETE http://127.0.0.1:8069/api/social/relationships/<target_user_id>/friend -H "Authorization: Bearer <token>"
curl -s -X POST http://127.0.0.1:8069/api/social/relationships/<target_user_id>/block -H "Authorization: Bearer <token>"
curl -s -X DELETE http://127.0.0.1:8069/api/social/relationships/<target_user_id>/block -H "Authorization: Bearer <token>"
curl -s http://127.0.0.1:8069/api/social/me/relationships -H "Authorization: Bearer <token>"
curl -s "http://127.0.0.1:8069/api/social/profiles?q=<slug>" -H "Authorization: Bearer <token>"
```

Validação manual/API:

- abrir `/u/<slug>` autenticado e executar seguir/deixar de seguir;
- solicitar amizade, aceitar, recusar, cancelar solicitação pendente e desfazer amizade usando dois usuários;
- bloquear usuário com follow/amizade existente e confirmar que relações foram encerradas;
- confirmar que usuário bloqueado recebe indisponível em `/api/social/profiles/<slug>` e não vê impressoras públicas via busca autenticada;
- desbloquear e confirmar que amizade/follow não voltam automaticamente;
- confirmar que `/api/social/profiles?q=<slug>` não lista perfil `private`, só retorna `unlisted` por slug direto e não mostra email, WhatsApp, organização nem permissão;
- tentar acessar impressora operacional do outro usuário após seguir/amizade e confirmar bloqueio por ownership/permissão;
- revisar `catalog_audit_events` com `entity_type='social_relationship'`: payload deve conter apenas IDs/ação/retenção e não conter email, senha, token, WhatsApp, Moonraker, SSH ou organização.

Rollback do PKG-53:

- desfazer relações por API (`unfollow`, `unfriend`, `unblock`) conforme necessário;
- se um bloqueio indevido afetar visualização pública, desbloquear pelo endpoint de unblock e validar que relações não foram recriadas;
- não apagar linhas de `social_relationships` ou `catalog_audit_events` sem confirmação explícita; histórico social segue retenção operacional de 180 dias;
- se o problema for estrutural, restaurar backup SQLite anterior ao `035_social_catalog.sql`.

Comunidades automáticas:

- abrir `/?section=social` autenticado e validar lista de comunidades com filtros por fabricante, modelo, variante e componente;
- abrir `/c/<community_slug>` e conferir nome, escopo, status, fabricante/modelo/variante, contagens e abas `Feed`, `Projetos`, `Mods`, `Perfis`, `Membros` e `Impressoras públicas`;
- publicar impressora real com variante canônica e confirmar associação às comunidades de fabricante, modelo e variante;
- trocar variante e confirmar que a variante antiga fica sem vínculo ativo e a nova recebe a impressora pública;
- despublicar ou tornar o perfil `private` e confirmar contagens zeradas e ausência da impressora na comunidade;
- validar que `obsolete` fica histórico sem vínculos novos e `merged` aponta destino quando `merged_into_id` existir;
- inspecionar payload de `/api/social/communities/<slug>` e confirmar ausência de Moonraker, agente, SSH, token, IP operacional, organização e permissões.

Rollback do PKG-51:

- despublicar a impressora pelo endpoint acima ou pela área `Publicação da impressora`;
- se necessário, restaurar backup do SQLite anterior ao `035_social_catalog.sql` conforme política de release;
- não apagar impressoras, perfis, variantes ou comunidades manualmente sem confirmação explícita.

Rollback do PKG-52:

- despublicar impressoras afetadas pelo endpoint `/api/printers/<id>/public-profile` com `public_profile_enabled=false`;
- para comunidade com curadoria incorreta, marcar item do catálogo como `obsolete`/`blocked` por curadoria administrativa em vez de apagar linhas;
- para merge incorreto, limpar `merged_into_id` e voltar `status` para `active` ou `uncurated` conforme estado do catálogo, depois rodar sincronização via listagem/detalhe de comunidades;
- se o problema for estrutural de banco, restaurar backup SQLite anterior ao `035_social_catalog.sql`; não executar `DELETE` em comunidades/membros sem confirmação explícita.

Rollback:

- restaurar o backup SQLite criado automaticamente antes do script `035_social_catalog.sql`;
- se o problema estiver só no catálogo ampliado, restaurar backup anterior aos scripts `036_expand_printer_catalog_seed.sql` a `043_catalog_deeper_model_detail.sql` ou reverter esses scripts e manter dados vinculados como legado até curadoria;
- remover a tela `Catálogo`, a inclusão `catalog` na navegação e as rotas administrativas novas se apenas a curadoria precisar ser revertida;
- remover a tela `Social` e as rotas `/api/catalog`, `/api/social/*` se todo o domínio social/catálogo precisar ser revertido no código.

Validação:

```bash
cd backend && uv run --extra dev pytest tests/test_social_catalog.py -q
cd frontend && npm run test:releases
cd frontend && npm run build
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Atualizar manifesto em dry-run:

```bash
python3 scripts/build_canbus_manifest.py --retrieved-at YYYY-MM-DD --timeout 10
```

Gravar manifesto apos revisar o dry-run:

```bash
python3 scripts/build_canbus_manifest.py --write --retrieved-at YYYY-MM-DD --timeout 10
```

Atualizar catalogo local em dry-run:

```bash
cd backend
uv run python ../scripts/build_firmware_catalog.py --manifest ../backend/app/data/firmware_canbus_manifest.json --output ../backend/app/data/firmware_hardware_catalog.json --generated-at YYYY-MM-DD --timeout 12
```

Gravar catalogo apos revisar o dry-run:

```bash
cd backend
uv run python ../scripts/build_firmware_catalog.py --manifest ../backend/app/data/firmware_canbus_manifest.json --output ../backend/app/data/firmware_hardware_catalog.json --generated-at YYYY-MM-DD --timeout 12 --write
```

Validar cobertura e contrato do catalogo:

```bash
cd backend
uv run pytest tests/test_canbus_manifest.py tests/test_firmware.py -q
```

Gerar preview de `.config` de um preset sem salvar arquivo:

```bash
curl -s http://127.0.0.1:8069/api/firmware/board-presets/btt_kraken_h723_usb_can/config-preview
```

O preview de `.config` retorna `content`, `lines`, `config_file`, `build_output` e `artifact_saved=false`. Ele é gerado em memória, não grava arquivo no host, não escreve no diretório Klipper e não executa `make`, flash, SSH, restart ou update.

Preparar dry-run de build de uma placa cadastrada:

```bash
curl -s -X POST http://127.0.0.1:8069/api/firmware/boards/BOARD_ID/build-runs/dry-run \
  -H 'Content-Type: application/json' \
  -d '{"klipper_path":"~/klipper","output_root":"~/printer_data/firmware_builds"}'
```

O dry-run retorna `preset_id`, `preset_build_config_status`, `generated_config_path`, `config_backup_path`, `work_dir`, `expected_build_output`, `binary_output_path`, `log_path`, checklist e comandos `PLAN ...`. Esses comandos são plano revisável, não execução. Preset incompleto bloqueia o dry-run antes de criar histórico.

Executar build pelo agente, sem flash:

```bash
curl -s -X POST http://127.0.0.1:8069/api/firmware/boards/BOARD_ID/build-runs/execute-local \
  -H 'Content-Type: application/json' \
  -d '{"klipper_path":"~/klipper","output_root":"~/.local/share/printora/firmware_builds","confirmation":"EXECUTE_LOCAL_BUILD_NO_FLASH"}'
```

Travas:

- sem confirmação textual exata `EXECUTE_LOCAL_BUILD_NO_FLASH`, o histórico registra `blocked_invalid_build_confirmation`;
- o executor roda no agente pareado, não no servidor da API;
- o executor não faz flash, não reinicia Klipper/Moonraker e não executa update;
- o executor usa apenas o diretório Klipper do host do agente e o `output_root` informado.

Artefatos salvos em `output_root/AGENT/<placa>/`:

- `.config.before-build`: backup da `.config` original;
- `generated/<arquivo>.config`: `.config` determinístico gerado pelo preset;
- `logs/build.log`: saída de `make clean` e `make`, ou erro capturado;
- `<binário>`: cópia do output esperado quando o build termina com sucesso.

Rollback:

- o executor restaura a `.config` original ao final em sucesso ou falha;
- se a operação for interrompida fora do controle do processo, restaurar manualmente `output_root/local-build/<placa>/.config.before-build` para `<klipper_path>/.config`;
- não há flash automático; se o binário gerado estiver incorreto, apagar o diretório de artefatos e repetir depois de corrigir o preset/build config.

Validar fechamento completo do pacote:

```bash
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

## Setup Do Zero - Flash Supervisionado

O flash supervisionado fica em `Setup do Zero > Flash supervisionado` e depende do SSH da Pi, CAN funcional e artefato de firmware gerado/validado.

Fluxo seguro:

1. informar placa, método, artefato remoto, UUID esperado e interface CAN;
2. marcar checklist físico somente após confirmar alimentação, cabos, placa correta, bootloader/Katapult e binário;
3. executar `Preflight flash`;
4. gerar `Plano flash` e revisar bloqueios, comando `PLAN`, frase de confirmação e rollback;
5. para execução real CAN/Katapult, habilitar o backend com `PRINTORA_REMOTE_FLASH_MODE=remote` e digitar exatamente a frase gerada;
6. revisar log, hash, duração e validação pós-flash.

Limites:

- o método real inicial é somente `can_katapult`;
- `usb_dfu` e `manual` ficam bloqueados no backend;
- o fluxo não edita `printer.cfg`, não reinicia Klipper/Moonraker, não executa update e não envia G-code;
- se falhar ou ficar inconclusivo, seguir o rollback manual exibido e colocar a placa novamente em bootloader.

SQL:

- `backend/sql/024_setup_flash_runs.sql` cria histórico local de preflight, plano e execução;
- rollback de schema: restaurar backup `printora.<timestamp>.before-schema.db` criado pelo versionador antes de aplicar scripts pendentes.

## Setup Do Zero - Validação Final

A validação final fica em `Setup do Zero > Validação final` e deve ser executada depois de SSH, CAN, firmware e flash estarem prontos.

O que a validação coleta:

- serviços `klipper`, `moonraker`, `can0` e auxiliares quando `systemctl` existir;
- `server/info`, `printer/info`, `print_stats`, temperaturas e Update Manager via Moonraker local;
- estado da interface CAN;
- UUIDs visíveis e UUIDs referenciados em configs;
- resumo de arquivos `.cfg`, MCUs, includes e identificadores serial/CAN;
- trechos recentes de logs com erros relevantes.

Limites:

- não envia G-code;
- não move eixo;
- não aquece hotend/mesa;
- não reinicia Klipper/Moonraker;
- não altera `printer.cfg` ou includes;
- não executa update.

SQL:

- `backend/sql/025_setup_final_validation_runs.sql` cria histórico local da validação e relatório sanitizado;
- rollback de schema: restaurar backup `printora.<timestamp>.before-schema.db` criado pelo versionador antes de aplicar scripts pendentes.

## Autenticação Cloud E Conta

O desenvolvimento inicial do PKG-39 usa SQLite. A modelagem deve permanecer simples e portátil para migração futura para Postgres quando a operação cloud exigir.

Fluxos:

- cadastro: `POST /api/auth/register` com `email` e `password` obrigatórios; `display_name`, `whatsapp`, `telegram` e `social_links` opcionais;
- login: `POST /api/auth/login`;
- login com 2FA: quando `mfa_required=true`, chamar `POST /api/auth/login/mfa` com `challenge_token` e código;
- sessão atual: `GET /api/auth/me` com `Authorization: Bearer <token>`;
- logout: `POST /api/auth/logout`;
- organização opcional: `POST /api/auth/organizations` e `POST /api/auth/organizations/{id}/members`;
- impressoras: cada registro tem dono e pode ter organização opcional; a API lista apenas impressoras do usuário autenticado ou de organizações das quais ele participa;
- rotas por impressora: antes de ler health, snapshots, operação, manutenção, backup, update, firmware, CAN, calibração, relatórios ou auditoria, a API valida a impressora no escopo do usuário/organização;
- rotas legadas sem `printer_id`: em sessão cloud usam uma impressora visível do usuário; se o usuário não tiver impressora visível, retornam 404 em vez de usar o Moonraker global;
- históricos operacionais: `setup_*_runs` e `app_update_runs` possuem owner e organização opcional para evitar vazamento entre usuários;
- 2FA: `POST /api/auth/mfa/setup`, `POST /api/auth/mfa/enable` e `POST /api/auth/mfa/disable`;
- step-up auth: `POST /api/auth/step-up` antes de ações destrutivas quando houver sessão autenticada;
- credencial de agente: `POST /api/auth/agent-credentials`, retornada completa somente uma vez.

## Gestão Cloud De Impressoras

O PKG-40 mantém o cadastro de impressoras em SQLite e usa owner/organização opcional para isolar acesso.

Fluxos:

- listar impressoras visíveis: `GET /api/printers`;
- criar impressora cloud: `POST /api/printers`;
- detalhar impressora: `GET /api/printers/{printer_id}`;
- editar impressora: `PUT /api/printers/{printer_id}`;
- testar conexão manualmente: `POST /api/printers/test-connection` retorna bloqueio cloud-safe; validação real acontece por agente pareado;
- descobrir Moonraker na rede local: `GET /api/printers/discover` fica bloqueado na API cloud até existir agente de rede dedicado.

Campos cloud:

- `name`, `moonraker_url`, `cloud_model`, `location`, `cloud_tags`, `notes` e `organization_id`;
- `organization_id` é opcional; sem organização a impressora fica individual;
- tags são normalizadas para minúsculas e deduplicadas;
- a credencial SSH pode ser configurada, mas não é retornada pela API.

Status cloud:

- `sem_agente`: nenhum token ativo e nenhum agente ativo;
- `aguardando_pareamento`: token ativo ou agente pareado sem heartbeat;
- `online`: agente ativo com heartbeat recente;
- `offline`: agente ativo sem heartbeat recente;
- `revogado`: apenas agentes revogados conhecidos.

Rollback PKG-40:

- reverter backend/UI/docs do pacote;
- se for necessário desfazer dados de schema, restaurar backup `printora.<timestamp>.before-schema.db` criado pelo versionador antes dos scripts aplicados;
- não apagar impressoras, agentes ou tokens manualmente sem confirmação explícita.

## Pareamento Seguro Do Agente

O PKG-41 usa SQLite e adiciona `backend/sql/029_agent_pairing.sql`.

Fluxos:

- gerar token curto: `POST /api/printers/{printer_id}/pairing/tokens` com sessão do usuário;
- listar pareamento: `GET /api/printers/{printer_id}/pairing`;
- revogar token: `POST /api/printers/{printer_id}/pairing/tokens/{token_id}/revoke`;
- trocar token por credencial operacional: `POST /api/agent/pairing/exchange`;
- heartbeat do agente: `POST /api/agent/heartbeat` com `Authorization: Bearer <credencial>`;
- snapshot do agente: `POST /api/agent/snapshots` com `Authorization: Bearer <credencial>`;
- fila de jobs: `GET /api/agent/jobs/next` com `Authorization: Bearer <credencial>`;
- rotacionar credencial: `POST /api/printers/{printer_id}/agents/{agent_id}/rotate`;
- revogar agente: `POST /api/printers/{printer_id}/agents/{agent_id}/revoke`.

Segurança:

- token de pareamento é persistido somente por hash, possui expiração, uso único e revogação;
- credencial operacional é persistida somente por hash e retornada completa apenas na troca ou rotação;
- eventos de agente guardam somente prefixos/detalhes sanitizados, nunca token completo ou credencial;
- agente revogado ou credencial antiga após rotação recebe 401 em heartbeat, snapshot e jobs.

Rollback:

- para desfazer o pareamento, reverter arquivos do PKG-41;
- se `029_agent_pairing.sql` já tiver sido aplicado e o schema não puder permanecer, restaurar o backup `printora.<timestamp>.before-schema.db` criado pelo versionador antes da aplicação;
- não apagar tokens, agentes ou eventos manualmente sem confirmação explícita.

## Agente Remoto Base

O PKG-42 adiciona o agente em Go em `agent/`.

Build:

```bash
cd agent
go test ./...
GOOS=linux GOARCH=arm64 go build ./cmd/printora-agent
GOOS=linux GOARCH=arm GOARM=7 go build ./cmd/printora-agent
GOOS=linux GOARCH=amd64 go build ./cmd/printora-agent
```

Config inicial:

```bash
printora-agent -config /etc/printora-agent/config.json config-sample
printf '%s\n' 'ptr_agent_xxx' | printora-agent -config /etc/printora-agent/config.json store-credential
chmod 600 /etc/printora-agent/config.json /etc/printora-agent/credential
printora-agent -config /etc/printora-agent/config.json doctor
```

Execução:

```bash
printora-agent -config /etc/printora-agent/config.json once
printora-agent -config /etc/printora-agent/config.json run
```

Canal remoto:

- `run` usa WebSocket outbound em `/api/agent/ws` quando `websocket_enabled=true`;
- se o WebSocket falhar, o agente continua tentando reconectar com backoff ate 60s;
- durante a reconexao, o agente segue enviando heartbeat/snapshot por HTTPS e, se `polling_enabled=true`, faz fallback em `/api/agent/jobs/next`;
- jobs suportados nesta etapa: `ping` e `snapshot`;
- cada job usa `correlation_id` e resultado idempotente;
- payloads acima de 64 KB são rejeitados pelo backend.

Serviço systemd:

```bash
sudo install -m 0755 printora-agent /usr/local/bin/printora-agent
sudo install -m 0644 agent/systemd/printora-agent.service /etc/systemd/system/printora-agent.service
sudo systemctl daemon-reload
sudo systemctl enable --now printora-agent
```

Segurança:

- o agente só abre conexões de saída;
- Moonraker local é acessado pelo agente; a API cloud não acessa Moonraker/SSH/rede local diretamente;
- o status remoto consulta `/server/gcode_store?count=200` somente por GET e
  encaminha no máximo 20 warnings/erros críticos recentes, deduplicados,
  compactados e sanitizados; saída comum do console não sai da rede local;
- firmware MCU obsoleto é alerta de monitoramento. Comunicação perdida,
  incompatibilidade de protocolo, shutdown, temporização e temperatura crítica
  bloqueiam considerar a impressora pronta;
- falha ao consultar o histórico runtime não derruba as demais leituras do
  Moonraker. Validar versão do agente antes de concluir que a ausência de alerta
  representa ausência de warning no Klipper;
- jobs mutáveis usam tipos explícitos ou `remote_host_script` controlado pelo backend, com confirmação/gate quando aplicável;
- credencial operacional fica em arquivo separado com permissão `0600`;
- logs passam por redaction de tokens;
- fila local JSONL é limitada e guarda payload compacto quando a API está indisponível.

Rollback PKG-43:

- reverter os arquivos do PKG-43;
- se `backend/sql/030_agent_channel.sql` já tiver sido aplicado e a tabela não puder permanecer, restaurar o backup `printora.<timestamp>.before-schema.db` criado antes da aplicação do schema;
- no host real, definir `"websocket_enabled": false` mantém o agente no ciclo HTTP/polling enquanto o backend é revertido.

## Instalador Online Assistido Do Agente

Fluxos:

- gerar plano de instalação: `POST /api/printers/{printer_id}/agent/install-plan`;
- consultar validação pós-instalação: `GET /api/printers/{printer_id}/agent/install-status`;
- baixar script público sem segredo: `GET /api/agent/install/linux.sh`.

Uso no host Klipper:

```bash
curl -fsSL https://printora.example.com/api/agent/install/linux.sh | PRINTORA_API_BASE=https://printora.example.com PRINTORA_MOONRAKER_URL=http://127.0.0.1:7125 bash -s -- --preflight
curl -fsSL https://printora.example.com/api/agent/install/linux.sh | sudo PRINTORA_API_BASE=https://printora.example.com PRINTORA_PAIRING_TOKEN=ptr_pair_xxx PRINTORA_MOONRAKER_URL=http://127.0.0.1:7125 PRINTORA_AGENT_BIN_URL=https://releases.example.com/printora-agent-linux-arm64 bash -s -- --apply --yes
```

Segurança:

- o script nunca imprime o token de pareamento;
- o token curto é enviado somente para `/api/agent/pairing/exchange` e vira credencial operacional local;
- config e credencial ficam em `/etc/printora-agent` com permissão `0600`;
- dados de fila ficam em `/var/lib/printora-agent` e logs em `/var/log/printora-agent`;
- o script exige systemd para instalar serviço e não executa G-code, restart de Klipper, update ou flash.

Uninstall:

```bash
curl -fsSL https://printora.example.com/api/agent/install/linux.sh | sudo bash -s -- --uninstall
```

O uninstall para/desabilita o serviço e remove o binário, mas preserva configuração, fila e logs. Apagar esses diretórios exige ação manual explícita.

Rollback PKG-44:

- reverter backend, UI e `backend/scripts/install_agent_linux.sh`;
- no host real, rodar o uninstall acima;
- revogar o agente ou token pela tela Impressoras quando necessário;
- não apagar dados locais do agente sem confirmação.

## Atualização Automática Do Agente

Fluxos cloud:

- manifesto público: `GET /api/agent/update/manifest`;
- solicitar update remoto: `POST /api/printers/{printer_id}/agents/{agent_id}/update-check`;
- relatório do agente: `POST /api/agent/update/reports` com `Authorization: Bearer <credencial>`;
- histórico por impressora: `GET /api/printers/{printer_id}/agent/update-history`.

Config do agente:

```json
{
  "update_enabled": true,
  "update_check_interval_seconds": 3600,
  "update_manifest_url": "https://printora.example.com/api/agent/update/manifest",
  "update_state_file": "/var/lib/printora-agent/update-state.json",
  "update_staging_dir": "/var/lib/printora-agent/updates",
  "job_journal_file": "/var/lib/printora-agent/job-journal.json",
  "agent_binary_path": "/usr/local/bin/printora-agent",
  "agent_service_name": "printora-agent",
  "allow_service_restart": true
}
```

Execução manual:

```bash
sudo printora-agent -config /etc/printora-agent/config.json update-check
```

Publicação do binário do agente:

- somente `linux/arm64` é suportado enquanto não existir artefato funcional e testado para outra plataforma;
- a chave privada Ed25519 fica no bundle privado e nunca entra no release ou no Git;
- gerar duas vezes, comparar, produzir SBOM, checksums e assinaturas:

```bash
PRINTORA_AGENT_RELEASE_VERSION=0.1.34 \
PRINTORA_AGENT_SIGNING_KEY_FILE=/caminho/privado/agent-release-ed25519.pem \
scripts/build-agent-release.sh
```

- o arquivo servido em `releases[].url` precisa ser exatamente o mesmo binário usado para calcular `releases[].sha256`;
- URLs imutáveis usam `/api/agent/update/releases/{version}/linux-arm64`; a rota sem versão permanece apenas como compatibilidade e aponta para a versão recomendada;
- a API confere que arquivo e checksum estático do manifesto são idênticos; divergência bloqueia a resposta em vez de recalcular e esconder erro;
- o manifesto exige assinatura `ed25519-sha256`, fingerprint da chave e release completo;
- publicar `candidate_version` primeiro, mantendo `recommended_version` em N-1; promover somente depois de canário, rollback e observação;
- o canário autenticado usa temporariamente `/api/agent/update/manifest/candidate`; nenhum agente usa esse endpoint por padrão;
- a UI envia `POST .../update-check?channel=candidate` para instalar exatamente
  `candidate_version` e `channel=rollback` para retornar à recomendada N-1;
  ambos geram job remoto controlado, sem SSH, com preflight de
  `print_stats.state`, backup, SHA-256 e Ed25519 antes da troca;
- se o download falhar com checksum ou assinatura inválida, bloquear a instalação e conferir o arquivo servido antes de nova tentativa;
- em ambiente local de teste, não depender de servidor HTTP avulso para o binário quando a API estiver acessível pela impressora.

Execução pela UI:

- abrir `Agentes`, conferir `Versão instalada` e `Versão esperada`;
- clicar `Atualizar` na linha ou `Atualizar agente` no detalhe;
- para canário, clicar `Instalar canário <versão>`; após o heartbeat confirmar
  essa versão, clicar `Reverter para <N-1>` para o teste de rollback;
- o servidor cria um job `remote_agent_update_check` para o agente ativo, tenta entregar imediatamente pelo WebSocket e mantém fallback por heartbeat/polling, sem SSH e sem comando manual para o usuário;
- o agente baixa apenas a versão recomendada, valida SHA-256 e assinatura Ed25519, troca somente `/usr/local/bin/printora-agent` e reinicia apenas `printora-agent` quando `allow_service_restart=true`.

Segurança:

- o update consulta somente o manifesto do agente e baixa o binário indicado para a plataforma do host;
- `sha256`, assinatura, algoritmo e identidade da chave são obrigatórios para aplicar;
- antes do download, `print_stats.state` precisa comprovar estado ocioso;
  impressão, pausa ou indisponibilidade do Moonraker bloqueiam o update;
- versão/protocolo bloqueado pelo servidor impede aplicação;
- antes da troca, o agente preserva backup do binário atual e tenta preservar o config;
- a troca altera apenas o binário do `printora-agent`;
- recebimento é sincronizado no journal antes do ACK, início antes do efeito e
  resultado terminal antes de responder ao cloud; redelivery reenvia sem
  repetir efeito;
- job mutável interrompido depois do ACK é bloqueado como `requires_reconciliation`;
- o journal local sincroniza arquivo/diretório, usa modo `0600` e retenção
  limitada às 200 entradas mais recentes;
- restart automático, quando habilitado, executa apenas `systemctl restart printora-agent`;
- o fluxo não reinicia Klipper, Moonraker, firmware, Raspberry ou impressora;
- falha em health command ou restart restaura o binário anterior quando possível.

Rollback local:

- se o rollback automático não for suficiente, parar o serviço, restaurar `printora-agent.backup-*` de `/var/lib/printora-agent/updates` para `/usr/local/bin/printora-agent` e iniciar `printora-agent`;
- revogar agente pela tela Impressoras se houver suspeita de credencial comprometida;
- não apagar histórico local sem confirmação.

## Paridade Funcional Remota

Fluxos:

- matriz de paridade: `GET /api/printers/{printer_id}/remote/parity`;
- solicitar job remoto: `POST /api/printers/{printer_id}/remote/parity/jobs`;
- execução do agente: `GET /api/agent/jobs/next`, `ack`, `result` e `error`.

Funcionalidades remotas read-only:

- `audit`;
- `snapshot`;
- `health`;
- `temperatures`;
- `update_manager`;
- `can`;
- `final_validation`;
- `sanitized_report`.

Funcionalidades remotas dry-run/preview:

- `backup_preview`;
- `operation_preview`;
- `firmware_preview`.

Bloqueios explícitos até PKG-47:

- `backup_payload`;
- `firmware_build_apply`;
- `mutable_operation`.

Estados:

- `implemented`: agente recente e funcionalidade disponível;
- `cached`: último resultado conhecido existe, mas agente não está recente;
- `offline`: sem agente recente e sem resultado anterior;
- `blocked`: bloqueio de segurança;
- `not_supported`: não suportado pela plataforma/contrato atual.

Segurança:

- o servidor cloud não acessa Moonraker direto no modo remoto; ele agenda job para o agente;
- o agente sanitiza campos com `password`, `token`, `secret`, `credential` e `private_key`;
- payload grande de backup real continua bloqueado até política própria;
- operações mutáveis, build e flash remoto continuam bloqueados até o PKG-47.

## Operação Segura Remota

Fluxos:

- matriz de operações: `GET /api/printers/{printer_id}/remote/operations`;
- solicitar preflight: `POST /api/printers/{printer_id}/remote/operations/preflight`;
- solicitar execução: `POST /api/printers/{printer_id}/remote/operations/execute`;
- cancelar job pendente: `POST /api/printers/{printer_id}/remote/operations/jobs/{job_id}/cancel`;
- execução do agente: `remote_mutation_preflight` e `remote_mutation_execute` via `agent_jobs`.

Gates obrigatórios:

- usuário autenticado com acesso à impressora por ownership ou organização;
- agente ativo pareado com a impressora;
- job de preflight remoto concluído com `can_execute=true`;
- confirmação textual exata do preflight;
- job ainda não expirado;
- estado detectável sem impressão em andamento;
- Klipper e Klippy em `ready` quando retornados pelo Moonraker.

Política de job:

- preflight expira em 10 minutos;
- execução expira em 5 minutos;
- jobs expirados não são entregues em `/api/agent/jobs/next`;
- cancelamento é permitido para job pendente; job em progresso não é cancelado pelo servidor para não mascarar execução já recebida pelo agente.
- leituras de alta frequência com impressora, agente, tipo e payload idênticos
  reutilizam o mesmo job ativo; mutações nunca são coalescidas;
- heartbeat comprova somente vida do agente e não renova lease de job;
- qualquer job `in_progress` sem resultado expira pelo timeout normal, mesmo
  quando o agente continua online;
- fila crescente durante reconnect não deve ser contornada elevando o SLO:
  confirmar que novas leituras equivalentes deixam de aumentar a contagem,
  aguardar expiração/drenagem dos jobs anteriores e repetir integralmente o
  trecho de soak afetado.

Auditoria:

- `agent_jobs` guarda solicitação, confirmação, payload sanitizado, status, agente, resultado e erro;
- `printer_agent_events` registra criação, ack, resultado, erro e cancelamento por impressora/agente;
- detalhes de evento ficam truncados e não devem conter token, senha, chave ou payload sensível.

Rollback:

- a UI mostra rollback antes da confirmação;
- para comandos de aquecimento, enviar alvo `0`;
- para fan, enviar `M107` ou `SPEED=0`;
- para comportamento inesperado de movimento/extrusão, usar Emergency Stop no Mainsail/Klipper e revalidar `printer/info`.

## Observabilidade E Suporte Do Agente

Fluxos:

- painel de suporte: `GET /api/printers/{printer_id}/agent/support`;
- doctor remoto: `POST /api/printers/{printer_id}/agent/support/doctor`;
- pacote sanitizado: `GET /api/printers/{printer_id}/agent/support/bundle`;
- job do agente: `remote_doctor`.

Estados diagnosticáveis:

- sem agente pareado: instalar/parear agente;
- sem heartbeat recente: validar serviço `printora-agent`, rede de saída e credencial local;
- agente revogado: parear novo agente ou rotacionar credencial;
- versão diferente da esperada: executar update do agente;
- protocolo incompatível: atualizar agente antes de novos jobs;
- fila acumulada: verificar WebSocket/polling e conectividade com a API;
- falha recorrente: rodar doctor remoto e revisar última falha;
- Moonraker/Klipper indisponível no doctor: corrigir host local antes de operar remotamente.

Sanitização:

- pacote de suporte remove campos `password`, `token`, `secret`, `credential` e `private_key`;
- tokens `ptr_agent_*`, `ptr_pair_*` e `ptr_sess_*` são redigidos;
- log tail do agente é limitado e sanitizado antes de sair do host;
- pacote de suporte não deve ser usado como backup nem conter payload completo sensível.

Retenção e limpeza:

- eventos de agente e jobs usados para suporte têm retenção operacional definida de 180 dias;
- o endpoint de pacote não apaga dados;
- limpeza deve ser rotina operacional manual/supervisionada enquanto não existir job dedicado, para evitar apagar histórico útil sem confirmação.

Segurança:

- senhas usam PBKDF2 e nunca são retornadas;
- tokens de sessão, desafios 2FA, step-up tokens e credenciais de agente são persistidos por hash;
- segredo TOTP é protegido por chave local `auth_secrets.key`, fora do Git;
- credencial de agente completa não aparece na listagem, somente prefixo/status;
- operações da tela Operação chamadas com sessão autenticada exigem step-up token para envio de G-code.
- endpoints operacionais exigem sessão quando já existe ao menos um usuário ativo no banco; bancos locais sem usuários preservam o modo local de desenvolvimento.

## Segurança social e antiabuso

Escopo:

- controles do usuário ficam em `Conta > Perfil > Público`, bloco `Segurança social`;
- endpoints de runtime:
  - `GET /api/social/me/safety`;
  - `PUT /api/social/me/safety`;
  - `GET /api/social/moderation/abuse-signals` restrito ao administrador;
- endpoints públicos sensíveis aplicam rate limit por ação: busca/perfil, relações, denúncias, mutações sociais e downloads sociais.

Banco:

- ordem: `059_social_safety_antiabuse.sql` depois de `058_social_notifications.sql`;
- tabelas: `social_user_safety_settings`, `social_rate_limit_events`, `social_abuse_signals`;
- impacto: adiciona preferências e trilha antiabuso sem alterar organizações, permissões, agentes, Moonraker, SSH ou ownership de impressoras.

Validação:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_social_catalog.py -k 'social_safety or social_profile_discovery_visibility_blocking or moderation_queue' -q
cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q
npm --prefix frontend run build
```

Smokes úteis:

```bash
curl -s -H "Authorization: Bearer <token>" http://127.0.0.1:8069/api/social/me/safety
curl -s -H "Authorization: Bearer <admin-token>" http://127.0.0.1:8069/api/social/moderation/abuse-signals
```

Privacidade e retenção:

- `social_rate_limit_events.subject_hash` guarda hash do sujeito da ação; não guardar IP bruto, email, token, senha ou payload operacional;
- `social_abuse_signals.metadata_json` deve conter apenas ação, severidade e contexto mínimo sanitizado;
- retenção operacional recomendada: eventos de rate limit por 30 dias e sinais de abuso por 180 dias;
- limpeza futura deve ser rotina supervisionada e nunca apagar dados sem confirmação explícita.

Rollback:

- reverter `backend/app/social_safety.py`, `backend/app/routes/social_safety.py`, integrações em rotas sociais, UI de `AuthScreen.tsx`, `socialApi.ts`, `types/social.ts` e documentação;
- se `059_social_safety_antiabuse.sql` já tiver sido aplicado e for necessário remover schema, restaurar backup SQLite anterior criado pelo versionador;
- não executar `DELETE` ou `DROP TABLE` manual sem confirmação explícita.

## Armazenamento social legado, cotas e retenção

Escopo:

- arquivos legados da biblioteca social usam storage local em `PRINTORA_DATA_DIR/library_uploads`;
- após PKG-77 a PKG-81, o painel e a política operacional pertencem a `Projetos de impressão > Meus projetos`, reaproveitando ou migrando esse storage;
- upload consulta cota antes de gravar o objeto em quarentena;
- relatório autenticado: `GET /api/social/me/library/storage`;
- revisão supervisionada: `POST /api/social/me/library/storage/retention-reviews`.

Banco:

- ordem: `060_social_file_storage.sql` depois de `059_social_safety_antiabuse.sql`;
- tabelas: `social_file_storage_policies`, `social_file_retention_reviews`;
- impacto: adiciona política de cota/retenção/custo e trilha de revisão sem alterar permissões, agentes, Moonraker, SSH ou vínculos de impressoras.

Validação:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_social_catalog.py -k 'library_storage or library_upload_quarantine' -q
cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q
npm --prefix frontend run build
```

Smokes úteis:

```bash
curl -s -H "Authorization: Bearer <token>" http://127.0.0.1:8069/api/social/me/library/storage
curl -s -X POST -H "Authorization: Bearer <token>" http://127.0.0.1:8069/api/social/me/library/storage/retention-reviews
```

Retenção e custo:

- política global padrão: 1 GB por usuário, 180 dias de retenção e custo estimado por GB/mês;
- revisão de retenção é `dry_run` auditável e não apaga arquivo físico, linha de banco ou versão;
- arquivo referenciado por versão ativa deve permanecer bloqueado no plano de retenção;
- object storage futuro deve preservar checksum, tamanho, dono e chave lógica antes de trocar adapter.

Rollback:

- reverter `backend/app/social_storage.py`, `backend/app/routes/social_storage.py`, integração em `social_catalog.py`, UI de biblioteca e documentação;
- se `060_social_file_storage.sql` já tiver sido aplicado e for necessário remover schema, restaurar backup SQLite anterior criado pelo versionador;
- não executar `DELETE`, `DROP TABLE` ou remoção manual de arquivos sem confirmação explícita e backup.

## Fatiamento Controlado

Escopo:

- detectar OrcaSlicer/PrusaSlicer por CLI local ou caminho configurado;
- registrar checks de engine e dry-runs sanitizados;
- manter fatiamento real bloqueado até haver pipeline de job, perfil, impressora e preflight.

Configuração:

```bash
export PRINTORA_SLICER_ENGINE_PATH="/caminho/para/orcaslicer"
```

Endpoints:

- status da engine: `GET /api/slicing/engine`;
- dry-run do contrato: `POST /api/slicing/dry-run`.

Banco:

- ordem: `061_slicing_engine_bridge.sql` depois de `060_social_file_storage.sql`;
- tabelas: `slicing_engine_checks`, `slicing_dry_run_logs`;
- impacto: adiciona trilha auditável de detecção/dry-run sem alterar impressoras, agentes, Moonraker, dados legados de biblioteca ou projetos/arquivos existentes.

Validação:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_slicing.py -q
npm --prefix frontend run build
```

Smoke útil:

```bash
curl -s http://127.0.0.1:8069/api/slicing/engine
```

Rollback:

- reverter `backend/app/slicing.py`, `backend/app/routes/slicing.py`, integração no `main.py`, serviço frontend de slicing, painel de Administração e documentação;
- se `061_slicing_engine_bridge.sql` já tiver sido aplicado e for necessário remover schema, restaurar backup SQLite anterior criado pelo versionador;
- não executar `DROP TABLE` ou limpeza manual de histórico sem confirmação explícita.

## Pipeline De Fatiamento

Escopo:

- manter compatibilidade/diagnóstico de jobs legados até a migração para `Projetos de impressão`;
- novos jobs diários devem nascer no fluxo do projeto, com snapshot imutável, arquivos selecionados, impressora, perfil e qualidade;
- validar volume útil catalogado e compatibilidade de perfil;
- executar worker controlado quando a engine CLI estiver configurada;
- registrar artefatos `gcode`, `log` e `metadata`;
- permitir cancelamento de job planejado/em execução.

Endpoints:

- listar jobs: `GET /api/slicing/jobs`;
- criar job: `POST /api/slicing/jobs`;
- executar job: `POST /api/slicing/jobs/<id>/run`;
- cancelar job: `POST /api/slicing/jobs/<id>/cancel`.

Banco:

- ordem: `062_slicing_jobs.sql` depois de `061_slicing_engine_bridge.sql`;
- tabelas: `slicing_jobs`, `slicing_job_artifacts`;
- impacto: adiciona histórico e artefatos rastreáveis; não envia arquivo para impressora e não altera Moonraker/Klipper. A UI principal de criação/acompanhamento deve migrar para `Projetos de impressão`; Administração fica como diagnóstico/fallback.

Validação:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_slicing.py ../backend/tests/test_slicing_pipeline.py -q
cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q
npm --prefix frontend run build
```

Rollback:

- reverter `backend/app/slicing_pipeline.py`, endpoints de jobs em `backend/app/routes/slicing.py`, serviço frontend de slicing, painel de pipeline e documentação;
- se `062_slicing_jobs.sql` já tiver sido aplicado e for necessário remover schema, restaurar backup SQLite anterior criado pelo versionador;
- não executar `DROP TABLE`, remoção manual de artefatos ou limpeza de histórico sem confirmação explícita.

## Preflight De Impressão

Escopo:

- analisar metadados de G-code gerado por job concluído;
- validar volume, temperatura, nozzle/material quando houver metadados;
- criar preflight remoto via agente para confirmar estado Moonraker/Klipper;
- bloquear envio quando não há agente online, quando a impressora está imprimindo ou quando há incompatibilidade;
- exibir checklist antes de qualquer envio.

Endpoints:

- listar preflights: `GET /api/slicing/preflights`;
- criar preflight para job: `POST /api/slicing/jobs/<job_id>/preflight`;
- atualizar retorno remoto: `POST /api/slicing/preflights/<preflight_id>/refresh`.

Banco:

- ordem: `063_print_preflight_checks.sql` depois de `062_slicing_jobs.sql`;
- tabela: `print_preflight_checks`;
- impacto: adiciona histórico de preflight e vínculo opcional com `agent_jobs`; não envia G-code e não altera Moonraker/Klipper.

Validação:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_print_preflight.py ../backend/tests/test_slicing_pipeline.py -q
cd backend && uv run --extra dev pytest ../backend/tests/test_schema_versioning.py ../backend/tests/test_update_self.py -q
npm --prefix frontend run build
```

## Envio Seguro De G-code

Escopo:

- enviar G-code fatiado somente a partir de preflight aprovado e recente;
- salvar arquivo no host via agente sem iniciar impressão;
- iniciar impressão somente com confirmação textual ou step-up válido;
- auditar usuário, impressora, job, preflight, checksum, arquivo remoto, snapshot/projeto ou versão legada, perfil e resultado remoto;
- remover automaticamente somente arquivo salvo sem impressão iniciada.

Endpoints:

- listar entregas: `GET /api/slicing/deliveries`;
- criar entrega: `POST /api/slicing/deliveries`;
- cancelar entrega pendente: `POST /api/slicing/deliveries/<delivery_id>/cancel`;
- remover arquivo salvo sem impressão: `POST /api/slicing/deliveries/<delivery_id>/rollback`.

Banco:

- ordem: `064_print_gcode_deliveries.sql` depois de `063_print_preflight_checks.sql`;
- tabela: `print_gcode_deliveries`;
- impacto: adiciona auditoria de entrega; não altera jobs antigos nem apaga artefatos.

Agente:

- `remote_gcode_upload` executa preflight remoto novamente e envia multipart para `/server/files/upload`;
- `remote_gcode_delete` remove arquivo salvo por `/server/files/gcodes/<arquivo>`;
- resultado remoto é sanitizado e não retorna `gcode_content`.

Rollback:

- se a entrega estiver `pending_remote`, cancelar o job antes do agente iniciar;
- se o modo for `save_only` e status `saved`, usar rollback automático para remover o arquivo remoto;
- se a impressão foi iniciada, rollback automático é bloqueado; usar controles do Moonraker/Klipper para pausar/cancelar com operador presente.

Validação:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_print_delivery.py ../backend/tests/test_print_preflight.py -q
cd agent && go test ./...
npm --prefix frontend run build
```

### Projetos de impressão pessoais

Endpoints autenticados:

- listar área pessoal: `GET /api/print-projects/me`;
- relatório de armazenamento pessoal: `GET /api/print-projects/me/storage`;
- criar projeto: `POST /api/print-projects`;
- editar metadados: `PATCH /api/print-projects/<project_id>`;
- upload pessoal: `POST /api/print-projects/<project_id>/files/upload?file_name=<nome>&file_role=<funcao>` com corpo `application/octet-stream`;
- adicionar referência externa: `POST /api/print-projects/<project_id>/external-links`;
- arquivar projeto: `DELETE /api/print-projects/<project_id>`.

Banco:

- ordem: `070_print_project_personal_library.sql` depois de `069_print_project_experience.sql`;
- efeito: adiciona metadados de quarentena/upload/rejeição nos arquivos de projeto e índices de checksum/storage;
- não apaga projeto, arquivo, versão, comunidade ou referência salva.

Validação:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q
npm --prefix frontend run build
```

Rollback:

- reverter `backend/app/print_projects.py`, `backend/app/routes/print_projects.py`, serviço/tipos/tela de projetos no frontend e documentação;
- se `070_print_project_personal_library.sql` já tiver sido aplicado e for necessário remover colunas/índices, restaurar backup SQLite anterior criado pelo versionador;
- não executar `DROP TABLE`, recriação manual de tabela ou remoção de arquivos de quarentena sem confirmação explícita.

### Publicação e vitrine de projetos

Endpoints autenticados:

- configurar publicação do projeto: `PUT /api/print-projects/<project_id>/publication`;
- revisar publicação comercial/curadoria: `POST /api/print-projects/<project_id>/publication-review`.

Regras:

- a busca pública lista somente projetos `visibility=public`, `publication_status=approved` e não arquivados;
- premium exige preço preparado e revisão antes de exposição pública;
- patrocinado exige transparência explícita e revisão antes de exposição pública;
- pagamento real, repasse financeiro e fiscal não estão ativos neste fluxo;
- compartilhamento em comunidade não altera visibility/publication/commercial_class.

Banco:

- ordem: `071_print_project_publication.sql` depois de `070_print_project_personal_library.sql`;
- efeito: adiciona preço preparado, moeda, termos, transparência e histórico de revisão de publicação no projeto central;
- não altera comunidades, arquivos ou ownership.

Validação:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q
npm --prefix frontend run build
```

Rollback:

- reverter `backend/sql/071_print_project_publication.sql`, regras de publicação em `backend/app/print_projects.py`, rotas novas, painel de publicação no frontend e documentação;
- se o SQL já tiver sido aplicado e for necessário remover colunas/tabela, restaurar backup SQLite anterior criado pelo versionador;
- não executar `DROP TABLE`, recriação de `print_projects` ou remoção manual de revisões sem confirmação explícita.

### Fatiamento por projeto salvo

Endpoints autenticados:

- listar jobs do projeto: `GET /api/slicing/projects/<project_id>/jobs`;
- criar job do projeto: `POST /api/slicing/projects/<project_id>/jobs`.

Contrato operacional:

- o projeto precisa pertencer ao usuário ou estar salvo por ele;
- o projeto precisa ter `current_version_id`;
- `selected_file_ids` deve conter arquivos do projeto com arquivo local validado e `can_slice=true`;
- referência externa sem arquivo hospedado/importado/validado é bloqueada para fatiamento;
- o job grava `print_project_id`, `print_project_version_id`, snapshot do projeto e snapshot dos arquivos selecionados;
- alterações posteriores no projeto ou nos arquivos não reescrevem jobs já criados.

Banco:

- ordem: `072_project_slicing_jobs.sql` depois de `071_print_project_publication.sql`;
- efeito: adiciona vínculo opcional de `slicing_jobs` com projeto, versão/snapshot e arquivos selecionados;
- não apaga jobs antigos nem altera artefatos, preflights, entregas ou histórico.

Validação:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_slicing_pipeline.py ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q
npm --prefix frontend run build
```

Rollback:

- reverter `backend/sql/072_project_slicing_jobs.sql`, criação/listagem de jobs por projeto em `backend/app/slicing_pipeline.py` e `backend/app/routes/slicing.py`, serviço frontend de slicing, painel `Fatiamento` em projetos e documentação;
- se o SQL já tiver sido aplicado e for necessário remover colunas/índice, restaurar backup SQLite anterior criado pelo versionador;
- não executar `DROP TABLE`, recriação de `slicing_jobs` ou remoção manual de jobs/artefatos/preflights sem confirmação explícita.

### Envio e histórico por projeto

Fluxo operacional:

- executar o job de fatiamento do projeto até `completed`;
- criar preflight no job concluído;
- salvar G-code ou iniciar impressão somente com preflight aprovado e recente;
- para iniciar impressão, informar a confirmação textual exibida no painel ou usar autorização reforçada quando aplicável;
- registrar histórico e feedback no contexto do projeto, mantendo feedback público sanitizado.

Endpoints reaproveitados:

- executar job: `POST /api/slicing/jobs/<job_id>/run`;
- criar preflight: `POST /api/slicing/jobs/<job_id>/preflight`;
- atualizar preflight remoto: `POST /api/slicing/preflights/<preflight_id>/refresh`;
- salvar/enviar G-code: `POST /api/slicing/deliveries`;
- rollback seguro de arquivo salvo: `POST /api/slicing/deliveries/<delivery_id>/rollback`;
- listar histórico: `GET /api/slicing/history`;
- registrar evento: `POST /api/slicing/history/<history_id>/events`;
- registrar feedback: `POST /api/slicing/history/<history_id>/feedback`.

Privacidade:

- histórico público deve usar payload sanitizado do backend;
- nunca publicar impressora privada, agente, Moonraker, token, IP, path, organização ou permissão;
- foto pública exige URL HTTPS.

Validação:

```bash
cd backend && uv run --extra dev pytest ../backend/tests/test_print_history.py ../backend/tests/test_print_delivery.py ../backend/tests/test_slicing_pipeline.py ../backend/tests/test_print_projects.py ../backend/tests/test_schema_versioning.py::test_initialize_database_registers_sql_scripts_on_new_database -q
npm --prefix frontend run build
```

Rollback:

- reverter painel de envio/histórico em `frontend/src/screens/PrintProjectsScreen.tsx`, ajustes do serviço frontend de slicing, testes e documentação;
- backend de entrega/histórico permanece compatível e compartilhado com Administração como diagnóstico/fallback;
- não remover entregas, histórico, feedback ou agent jobs sem confirmação explícita e backup.

Rollback:

- reverter `backend/app/print_preflight.py`, endpoints de preflight em `backend/app/routes/slicing.py`, serviço frontend de slicing, painel de preflight e documentação;
- se `063_print_preflight_checks.sql` já tiver sido aplicado e for necessário remover schema, restaurar backup SQLite anterior criado pelo versionador;
- não executar `DROP TABLE`, remoção manual de preflights ou limpeza de `agent_jobs` sem confirmação explícita.

Rollback:

- para remover a camada de autenticação, reverter os arquivos do PKG-39;
- se os scripts `026_auth_identity.sql`, `027_printer_ownership.sql` ou `028_operational_ownership.sql` já tiverem sido aplicados e precisar desfazer o schema, restaurar o backup `printora.<timestamp>.before-schema.db` criado pelo versionador antes da aplicação;
- não apagar tabelas ou dados manualmente sem confirmação explícita.

Regras operacionais:

- os scripts executam apenas leitura HTTP do dominio `canbus.esoterical.online` e leitura/escrita local dos JSONs quando `--write` for informado;
- os scripts nao executam flash, build, update, SSH, restart, `make`, G-code ou alteracao de configuracao de impressora;
- o preview de `.config` do PKG-33 e somente leitura em memoria; se a geracao falhar por preset incompleto, corrigir o preset/build config antes de qualquer build futuro;
- o dry-run de build do PKG-33 registra somente plano local com comandos `PLAN ...`; nao grava `.config`, nao copia para Klipper, nao executa `make` e nao abre SSH;
- o build local controlado do PKG-33 pode executar `make clean` e `make` apenas no `klipper_path` local informado, com modo local e confirmacao textual; ele deve restaurar `.config` e salvar log/binario em artefatos Printora, nunca fazer flash, SSH, restart ou update;
- se o site externo mudar menu, conteudo ou disponibilidade, o manifesto deve manter status explicito por URL e a validacao de cobertura deve falhar antes de afetar a UI;
- rollback rapido: restaurar a versao anterior de `backend/app/data/firmware_canbus_manifest.json` e `backend/app/data/firmware_hardware_catalog.json` ou reverter os arquivos do PKG-30 no Git;
- se o catalogo ficar indisponivel ou invalido, a tela Firmware deve preservar o fluxo principal por impressora ativa e exibir estado de erro/sem referencia, sem consultar o site externo em runtime.

## Storage de objetos Cloud

O perfil Cloud usa MinIO privado em loopback. PostgreSQL é a fonte canônica de
owner, referência, estado, tamanho e checksum. A origem local de uma migração
permanece intacta até uma confirmação explícita de remoção.

Comandos no host, executados como `deploy`:

```bash
/usr/local/libexec/printora-cloud/run-object-storage-tool.sh validate
/usr/local/libexec/printora-cloud/run-object-storage-tool.sh migrate --manifest /tmp/object-manifest.json
/usr/local/libexec/printora-cloud/run-object-storage-tool.sh migrate --apply --manifest /tmp/object-manifest-applied.json
/usr/local/libexec/printora-cloud/run-object-storage-tool.sh reconcile
/usr/local/libexec/printora-cloud/run-object-storage-tool.sh search-rebuild
```

Para provar o limite máximo de uma requisição sem ultrapassá-lo:

```bash
PRINTORA_STORAGE_PROBE_SIZE_MIB=25 \
  /usr/local/libexec/printora-cloud/run-object-storage-tool.sh validate
```

O valor aceito fica entre `0` e `25`. A prova cria referências canônicas para a
quarentena e para o promovido; em seguida, `reconcile` deve terminar sem objeto
ausente, corrompido ou órfão. Ela não remove versões ou conteúdo.

- `migrate` sem `--apply` gera somente manifesto e reconciliação dry-run;
- manifesto é criado com modo `0600` e não contém credenciais nem path absoluto;
- `migrate --apply` copia incrementalmente e registra a referência; não remove a origem;
- `reconcile` compara banco, `HEAD`, tamanho, checksum disponível e lista de buckets;
- ausência, corrupção ou órfão faz a reconciliação falhar sem apagar conteúdo;
- `--adopt-prefix` existe somente para adoção supervisionada de objetos conhecidos.
- `search-rebuild` desativa a geração anterior, faz upsert da atual e reporta
  contagem por tipo; não apaga fonte nem documentos anteriores.

Download autorizado usa `POST /api/storage/social-library-files/<id>/tokens` ou
`POST /api/storage/print-project-files/<id>/tokens`. A resposta contém rota fixa,
token de 60 segundos e uso único. O download envia
`Authorization: Bearer <authorization_token>` para `GET /api/storage/download`.
Não colocar o token em query string, path, log ou analytics.

Rollback: reverter o adapter/runtime para a release anterior preservando schema,
buckets, versões e arquivos de origem. Não apagar bucket, versão, objeto, tabela ou
origem local sem confirmação explícita e backup validado.

O backup externo enumera todas as versões e delete markers via S3, exporta cada
conteúdo com SHA-256 e inclui manifesto junto do backup físico/lógico PostgreSQL e
WAL no snapshot Restic criptografado. O teste de restore extrai ambos em destino
isolado, valida todos os checksums, reconcilia `cloud_objects` com o conteúdo e
reconstrói `search_documents`. Ele não inicia a aplicação nem altera produção.

Uma atualização do MinIO deve preservar uma cópia executável do binário anterior,
validar SHA-256 do candidato, reiniciar somente `minio-printora.service`, aguardar
`/minio/health/ready` e executar `reconcile`. Em falha, reinstalar a cópia anterior
e repetir health + reconciliação. Não alterar buckets, metadados ou versões durante
o rollback.

## Finanças em sandbox

O runtime financeiro aceita somente `PRINTORA_PAYMENT_MODE=disabled` ou
`sandbox`. Dinheiro real não é suportado nesta release. O sandbox exige segredo
de webhook fora do Git e checkout hospedado; o Printora não recebe nem persiste
PAN, CVV ou payload bruto de webhook.

Antes de usar o sandbox, o administrador da plataforma atribui papéis separados
pela API autenticada. Operação, aprovação, risco, suporte e auditoria não são
intercambiáveis. Captura, reembolso, disputa, reconciliação, alteração de papel,
fechamento e aprovação/execução de repasse exigem step-up com purpose
`finance_sensitive_action`; o token é de uso único e não entra no digest do
comando.

Gate local:

```bash
scripts/validate-finance-safety.sh
cd backend && uv run --extra dev pytest -q tests/test_finance_*.py
```

O painel `Administração > Finanças` é read-only para consulta e separa pedidos,
ledger, reconciliação, disputas e repasses. A readiness mantém PCI/LGPD, fiscal,
jurídico, continuidade, chargeback, segurança e restore como controles com
evidência por hash. Aprovar controles não habilita dinheiro real.

Rollback: definir modo `disabled`, bloquear novos comandos e publicar a release
anterior. Preservar integralmente pedidos, intents, webhooks por digest, ledger,
reembolsos, disputas, repasses, decisões e auditoria. Não executar `DELETE`,
`UPDATE` manual de ledger ou `DROP TABLE`.

## Fabricação e cadeia de custódia

O domínio produtivo transforma somente pedido pago em cotação e ordem abstrata.
Ele não envia G-code, não agenda job no agente e não acessa Moonraker/Klipper.
Reservas de capacidade e material são atômicas; falta de recurso reverte todo o
aceite. Qualidade exige atores diferentes para inspecionar e aprovar.

Expedição recebe endereço já cifrado. Nunca registrar endereço, documento,
tracking token ou evidência privada em log, comunidade ou relatório público.
Tracking repetido é idempotente. Recall preserva eventos e emite apenas
`finance_command_key`; um operador financeiro decide e executa eventual estorno.

Rollback de código não restaura banco. Bloquear novas cotações/transições,
publicar a release anterior e preservar ordens, reservas, qualidade, custódia,
tracking e incidentes. Não remover registros durante incidente ou recall.

## Escala, resiliência e recuperação Cloud

O upstream ativo possui duas instâncias da mesma release: o slot blue (`8069`)
ou green (`8070`) e `replica` (`8071`). O slot oposto permanece na release N-1
fora do upstream. Isso protege contra falha de processo no mesmo host, mas não
contra perda física de host, disco, Nginx ou PostgreSQL.

Diagnóstico sem mutação:

```bash
cat /var/www/print3dmaker.xyz/shared/active-slot
systemctl is-active printora-cloud@blue printora-cloud@green printora-cloud@replica
curl -fsS http://127.0.0.1:8069/ready
curl -fsS http://127.0.0.1:8070/ready
curl -fsS http://127.0.0.1:8071/ready
sudo nginx -T | grep -A4 'upstream printora_cloud'
sudo /usr/local/sbin/printora-cloud-preflight
```

Perda de processo: o Nginx remove a instância após falha e mantém requests novos
na outra. Reiniciar somente a unit afetada e exigir `/ready`. O ensaio controlado
é `sudo /usr/local/libexec/printora-cloud/probe-active-active.sh`; ele interrompe
apenas a instância Cloud ativa, executa 300 requests e a restaura por `trap`.

Perda de banco: não iniciar fallback local. Bloquear escrita, preservar logs/WAL,
diagnosticar o cluster dedicado e restaurar somente em destino isolado. Retorno
à produção exige reconciliação de tabelas, schema, FKs, objetos e busca.

Perda de configuração: não improvisar segredo. Restaurar os arquivos cifrados do
snapshot Restic em diretório isolado, validar checksums do manifesto e aplicar
individualmente com owner/mode original. A credencial Restic e sua cópia de
custódia ficam fora do host e nunca entram no snapshot ou Git.

Perda de disco ou host: provisionar destino limpo, obter credencial pela custódia
externa, restaurar o snapshot externo mais recente e aplicar WAL até o ponto
disponível. Medir RPO desde `created_at`/último WAL do manifesto até o incidente
e RTO do início do exercício até reconciliação final. O host único não promete
RPO zero físico; RPO zero vale apenas para deploy/cutover.

Backup completo inclui base física, dump lógico, WAL, todas as versões de
objetos e configuração cifrada. A política é 14 diários, 8 semanais e 12 mensais.
`preview-backup-retention.sh` usa `restic forget --dry-run`; nenhuma remoção ou
`prune` pode ocorrer sem revisão do preview e confirmação explícita.

### SLO de recuperação física

| Classe | Fonte canônica | RPO | RTO | Proteção |
| --- | --- | --- | --- | --- |
| escrita PostgreSQL confirmada | PostgreSQL | até 5 min | até 15 min | `archive_timeout=120s`, cópia externa a cada 60 s e execução limitada a 110 s |
| deploy/cutover | release e banco compartilhado | zero | até 5 min | blue/green sem restore de dados |
| objetos e configuração | S3 local e arquivos protegidos | até 24 h 15 min | até 15 min no volume atual | snapshot externo diário com checksum |
| Redis | PostgreSQL e serviços canônicos | zero dado canônico | até 5 min | recomposição; Redis não é restaurado |
| busca | PostgreSQL canônico | zero dado canônico | até 15 min | rebuild após restore |
| release | Git e bundle verificável | último commit publicado | até 15 min | commit, checksum, SBOM e release imutável |

O pior caso configurado do PostgreSQL é `120 + 60 + 110 = 290 segundos`.
`printora-cloud-recovery-monitor.timer` executa a cada minuto e falha a partir
de 210 segundos sem verificação externa válida, antes do limite de 300 segundos.
O alerta tem owner `operations`, sempre grava evento crítico no journal e pode
enviar o mesmo evento sanitizado ao webhook definido fora do Git em
`/etc/printora-cloud/recovery-alert.env`.

Estado operacional:

```bash
sudo systemctl status \
  printora-cloud-wal-sync.timer \
  printora-cloud-recovery-monitor.timer \
  printora-cloud-restore-test.timer \
  printora-cloud-backup.timer
sudo /usr/local/libexec/printora-cloud/recovery-readiness.py
sudo journalctl -u printora-cloud-recovery-monitor.service \
  -u printora-cloud-wal-sync.service --since -30min
```

O relatório público/sanitizado pode conter idade, duração, bytes, quantidade de
WAL e gates. Não copiar `stable_id`, fingerprint, credencial, URL do repositório,
snapshot ID, path privado ou payload para tickets e auditorias.

O backup completo continua diário. O WAL externo é incremental e contínuo; não
executa `forget`, `prune` ou remoção local. O restore isolado semanal consome o
último snapshot completo e a cópia externa contínua de WAL, promove o cluster,
confere schema/revisões/FKs, objetos, configuração e busca, e deve terminar em
até 900 segundos. A unit limita CPU, I/O, memória e tarefas.

### Resposta cronológica a desastre

Owner primário: operações da plataforma. Um segundo responsável valida
custódia, reconciliação e retorno de tráfego.

1. Declarar incidente, horário de corte, classe afetada e responsável. Bloquear
   novas escritas somente se o banco não puder confirmá-las com segurança.
2. Preservar releases, logs, WAL, snapshots e estados de monitor. Não executar
   retenção, prune, cancelamento de job ou correção manual de linha.
3. Em host limpo, instalar a release exata e dependências verificadas. Obter
   credencial e chave exclusivamente pela custódia externa.
4. Restaurar o snapshot completo mais recente e sobrepor todos os WAL externos
   posteriores. Nunca restaurar sobre o cluster original.
5. Promover o cluster isolado e exigir: recovery encerrado, revisões esperadas,
   zero índice/FK inválida, checksums de configuração/objetos válidos e busca
   reconstruída da fonte canônica.
6. Reconciliar objetos, jobs/outbox/inbox, dead letters, duplicidades,
   pagamentos sandbox e fabricação. Redis deve voltar por recomposição.
7. Medir RPO entre a última escrita recuperada e o incidente e RTO entre a
   declaração e o fim da reconciliação. Se qualquer alvo falhar, manter tráfego
   bloqueado e escalar ao owner.
8. Trocar tráfego apenas após dupla revisão, smoke público/privado e plano de
   retorno. Comunicar início, decisão, resultado, risco residual e rollback.

O exercício local usa destino isolado, nunca o cluster em produção:

```bash
sudo systemctl start printora-cloud-wal-sync.service
sudo systemctl start printora-cloud-backup.service
sudo systemctl start printora-cloud-restore-test.service
sudo /usr/local/libexec/printora-cloud/recovery-readiness.py
sudo /usr/local/libexec/printora-cloud/emit-recovery-alert.sh recovery-drill
sudo /usr/local/libexec/printora-cloud/preview-backup-retention.sh
```

O drill de alerta não degrada a aplicação nem altera dados; apenas registra o
evento e usa o webhook externo quando configurado. O preview de retenção não
autoriza exclusão. Qualquer `forget` sem `--dry-run`, prune ou remoção de WAL
exige confirmação explícita separada, evidência de restore válido e hold
revisado.

### Capacidade e segundo host

Monitorar duração e bytes da cópia WAL, crescimento do repositório, espaço
livre, duração do snapshot completo e restore. Se a sincronização exceder 110 s,
se o disco ficar abaixo de 10% livre ou se o restore se aproximar de 900 s, o
gate falha antes de prometer o SLO.

Um segundo host é a evolução recomendada, não parte automática deste pacote.
Requer PostgreSQL da mesma versão, rede privada, armazenamento independente,
custódia própria, slots de replicação monitorados, capacidade equivalente e
exercício de promoção/retorno. Réplica assíncrona reduz RTO e mantém RPO limitado
pelo atraso; RPO físico zero exige réplica síncrona e aceita maior latência de
escrita. O servidor único continua sem classificação de alta disponibilidade.

Ensaios:

```bash
sudo PRINTORA_SOAK_SECONDS=600 /usr/local/libexec/printora-cloud/soak-cloud.sh
sudo -u deploy bash -c 'set -a; source /etc/printora-cloud/postgresql.env; set +a; /usr/local/libexec/printora-cloud/load-durable-execution.py'
sudo -u deploy bash -c 'set -a; source /etc/printora-cloud/postgresql.env; set +a; /usr/local/libexec/printora-cloud/probe-worker-recovery.py'
sudo systemd-run --wait --collect --unit=printora-cloud-restore-test \
  --property=CPUQuota=20% \
  /usr/local/libexec/printora-cloud/restore-postgresql-backup-test.sh
sudo /usr/local/libexec/printora-cloud/preview-backup-retention.sh
```

O soak prolongado exige uma impressora de validação explícita, agente na versão
esperada e evidência dentro de `shared/logs`. Ele mede p95/p99 de cada lote,
heartbeat e versão do agente, Redis, filas, dead letters, duplicidade de
correlation ID, conexões e tamanho do PostgreSQL, WAL, serviços, CPU acumulada,
RSS, FD, tasks, reinícios e disco. O observador falha fechado em heartbeat
vencido, serviço indisponível, erro novo, backlog ou crescimento acima dos
limites. O arquivo é sanitizado: identifica o agente somente por fingerprint e
não registra URL de banco, token, IP, path privado ou payload.
`PRINTORA_SOAK_TARGET_RPS` distribui o início das requisições ao longo do lote;
não é uma rajada seguida de espera. O modo burst continua disponível somente
para o smoke curto ao executar `load-smoke.py` sem `--target-rps`.
O soak usa `--connection-mode pooled`: clientes concorrentes compartilham um
único pool durante toda a janela e reutilizam keep-alive entre lotes, como
browser e agente reais. O processo de carga permanece vivo e transmite cada
relatório ao observador; reiniciar o pool a cada lote invalida a
representatividade. O modo
`--connection-mode cold` permanece disponível para medir DNS/TCP/TLS por
requisição, mas sua latência não é somada à janela representativa de 24/72h.
Como o alvo da carga é exclusivamente o `GET /health` idempotente, um
`RemoteProtocolError` causado pelo fechamento remoto de uma conexão keep-alive
recebe uma única reconexão no mesmo pool. A evidência mantém `retry_count` e
`retries` sanitizados; erro HTTP, timeout, segunda falha de protocolo ou falha
da reconexão continuam encerrando o lote e invalidando a janela.
O gate de disco combina os limites: falha somente quando a reserva fica abaixo
de 15% e de 50 GiB, evitando falso bloqueio em volumes grandes sem deixar de
proteger a capacidade absoluta.

```bash
sudo systemd-run --unit=printora-cloud-soak --collect \
  --property=EnvironmentFile=/etc/printora-cloud/postgresql.env \
  --setenv=PRINTORA_SOAK_SECONDS=86400 \
  --setenv=PRINTORA_SOAK_OBSERVE=1 \
  --setenv=PRINTORA_SOAK_AGENT_STABLE_ID='<identificador aprovado>' \
  --setenv=PRINTORA_SOAK_EXPECTED_AGENT_VERSION='0.1.34' \
  /usr/local/libexec/printora-cloud/soak-cloud.sh
systemctl status printora-cloud-soak.service
journalctl -u printora-cloud-soak.service --since today
```

O ensaio inicial usa `86400` segundos e o final usa `259200`, sempre como uma
janela contínua. Qualquer falha encerra a unit e invalida a janela afetada. A
evidência JSONL tem retenção operacional semanal por oito rotações; depois da
janela, copiar somente o resumo sanitizado para `docs/audits/`, sem segredos ou
identificadores privados.

Após a unit terminar com sucesso, consolidar o arquivo JSONL correspondente. O
resumo falha fechado em evidência inválida, erro, SLO violado, observação falha
ou duração insuficiente. Ele publica somente contagens, pior latência e
tendências agregadas; não inclui fingerprint, URL, token, IP, path ou payload.
A tolerância padrão de 60 segundos cobre o intervalo entre a última amostra e o
deadline da unit, mas o status final da unit continua obrigatório para provar a
janela completa.

```bash
/usr/local/libexec/printora-cloud/summarize-soak.py \
  /var/www/print3dmaker.xyz/shared/logs/soak-<UTC>.jsonl \
  --minimum-seconds 86400
```

Redis e busca podem degradar/recompor; PostgreSQL, autenticação, autorização,
ledger, fabricação e ownership nunca degradam para memória local. Storage usa
pool limitado, timeout e retries finitos. Pagamentos usam circuit breaker.
Workers são isolados por fila, concorrência e unit; quotas por fila e owner
aplicam backpressure antes de esgotar recursos.

## Analytics e inteligência isolada

O serviço `printora-cloud-intelligence.service` consome somente
`analytics_events`, ativa `printora_analytics` em cada transação e grava apenas
derivados `analytics_*`. A role deve possuir update em `analytics_events` e
nenhum select/update em `auth_users` ou demais tabelas do OLTP.

Diagnóstico read-only:

```bash
systemctl is-active printora-cloud-intelligence.service
systemctl show printora-cloud-intelligence.service \
  -p CPUQuotaPerSecUSec -p MemoryHigh -p MemoryMax -p TasksMax -p IOWeight
sudo -u postgres psql -p 5433 -d printora_cloud -X -Atqc \
  "SELECT has_table_privilege('printora_analytics','analytics_events','UPDATE'),
          has_table_privilege('printora_analytics','auth_users','SELECT'),
          has_table_privilege('printora_analytics','auth_users','UPDATE')"
```

Probe sintético controlado:

```bash
sudo systemctl stop printora-cloud-intelligence.service
sudo -u deploy bash -c '
  set -a
  source /var/www/print3dmaker.xyz/shared/printora-cloud.env
  source /etc/printora-cloud/postgresql.env
  set +a
  cd /var/www/print3dmaker.xyz/current/backend
  /var/www/print3dmaker.xyz/current/venv/bin/python \
    /usr/local/libexec/printora-cloud/probe-analytics-intelligence.py \
    --run-key probe-AAAAMMDD --events 500
'
sudo systemctl start printora-cloud-intelligence.service
```

Durante o probe, monitorar `/ready` nas duas instâncias ativas. O script usa
somente registros sintéticos, restaura o controle anterior do modelo e não
remove dados. A prova de retenção é `GET
/api/admin/data-intelligence/retention/preview`; qualquer limpeza física exige
preview revisado, confirmação explícita, backup e plano de rollback.

Falha ou drift: ativar kill switch pelo endpoint administrativo, confirmar
fallback determinístico e interromper somente a unit de inteligência se
necessário. Login, autorização, pedido, ledger, fabricação, operação e impressão
não dependem desse serviço. Rollback de código preserva derivados e não restaura
snapshot.

## Validacao por risco

## Aceite final da arquitetura cloud

O manifesto canônico é
`docs/architecture/FINAL_ARCHITECTURE_MANIFEST.md`. O scanner local bloqueia
flags, contratos e arquivos transitórios, exige owner para cada unit, confirma
lockfiles/SBOM fixados e importa o perfil cloud provando que `sqlite3` não foi
carregado:

```bash
scripts/validate-final-architecture.sh
```

Após publicação, executar no servidor sem acessar a cadeia da impressora:

```bash
sudo /usr/local/libexec/printora-cloud/audit-final-architecture.sh
sudo /usr/local/sbin/printora-cloud-preflight
```

O resultado esperado contém `status=passed`, duas réplicas web, zero índice ou
constraint inválida e `analytics_role=1:0:0`. O comando só lê release, units,
readiness, módulos carregados e metadados PostgreSQL. Não remove dados, objetos,
backups ou releases.

Para revalidar recuperação e capacidade, usar o último restore isolado e o soak
documentados nas auditorias cloud. Rollback de código usa
`printora-cloud-rollback`; nunca restaurar snapshot antigo sobre escritas novas.
Qualquer candidato destrutivo deve ser apresentado separadamente com preview,
backup, impacto, confirmação e rollback.

- Documentacao, label ou ajuste local simples: validar arquivo alterado e executar `./check.sh` se a alteracao tocar regra do modelo.
- Bug simples e isolado: reteste focado e check proporcional.
- Bug complexo: `./check.sh`, teste automatizado quando viavel e regressao do fluxo afetado.
- Lote de pacote: teste raso e direcionado.
- Fechamento de pacote: `./check.sh`, review final e commit.

## Banco de dados

- Nao usar migrations.
- Mudancas de banco entram como scripts `.sql` idempotentes em `backend/sql/`.
- Toda mudanca deve ter ordem de execucao, efeito esperado e rollback documentado.

## Operacao segura

- Leitura de logs, snapshots e diagnosticos deve ser read-only por padrao.
- Operacao mutavel em Klipper, Moonraker, systemd, firmware ou arquivos de configuracao exige confirmacao, backup e plano de rollback.
- Logs e relatorios nao podem vazar token, senha, IP privado sensivel, caminho local completo ou payload sensivel sem sanitizacao.

## Publicacao

Antes de publicar:

1. Rodar `./check.sh`.
2. Conferir bugs criticos/altos em `BUGS.md`.
3. Conferir riscos e rollback em `GOVERNANCA.md`.
4. Validar smoke do backend e frontend.
5. Registrar decisao relevante em `DECISOES.md` quando houver mudanca de operacao, arquitetura ou rollback.
6. Garantir que a versao foi atualizada no backend, frontend, lockfiles e frontend pre-buildado.
7. Criar commit de release e tag anotada no formato `vX.Y.Z`.
8. Publicar a branch e a tag no remoto.
9. Criar a GitHub Release da tag publicada; a area interna `Administracao > Plataforma Printora (interno)` consulta GitHub Releases, nao apenas tags Git, e fica restrita ao usuario de suporte.
10. Confirmar que `gh release list` mostra a nova versao como `Latest`.

Exemplo para `v0.1.9`:

```bash
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
git tag -a v0.1.9 -m "Printora v0.1.9"
git push origin main
git push origin v0.1.9
gh release create v0.1.9 --title "Printora 0.1.9" --notes "Release v0.1.9"
gh release list --limit 5
```

Se a GitHub Release nao for criada, o app pode continuar mostrando a release anterior como ultima disponivel mesmo com commit e tag locais corretos.

## PKG-101 — Design System

Validação local focada, sem tocar banco ou impressora:

```bash
cd backend && uv run --extra dev pytest tests/test_design_system.py -q
cd ../frontend && npm run test:unit -- tests/unit/DesignSystemScreen.test.ts tests/unit/DesignStatePanel.test.ts tests/unit/designSystemDraft.test.ts
cd .. && scripts/run-e2e-gate.sh design-system.spec.ts
```

Smoke após publicação autorizada:

1. autenticar com usuário sintético/controlado;
2. abrir `?section=design-system`;
3. consultar `GET /api/design-system/v1/capabilities` e confirmar oito famílias;
4. percorrer uma rota base, `/detail` e `/edit`;
5. salvar e recarregar um rascunho sem observar POST/PUT/PATCH/DELETE do domínio;
6. confirmar foco, tema, densidade, offline e ausência de overflow.

Rollback: restaurar a release N-1. Não executar SQL, apagar rascunho, restaurar
snapshot ou interromper backend, worker, agente, Moonraker ou impressora. O
endpoint é somente leitura e não possui cleanup.

## PKG-102 — Acessibilidade Universal

Validação local focada, sem tocar impressora ou serviço remoto:

```bash
cd backend
uv run --extra dev pytest tests/test_accessibility.py tests/test_module_boundaries.py -q
cd ../frontend
npm run test:unit -- tests/unit/AccessibilityScreen.test.ts tests/unit/accessibilityUtilities.test.ts
cd ..
scripts/run-e2e-gate.sh accessibility.spec.ts
```

Banco:

1. SQLite local aplica `backend/sql/086_accessibility_preferences.sql` no
   bootstrap e cria backup somente quando o script estiver pendente;
2. antes da release cloud, executar
   `backend/sql/postgresql/018_accessibility_preferences.sql` pelo fluxo
   privilegiado documentado;
3. validar tabela, constraints, chave primária `user_id`, revisão, primeira
   escrita, reexecução e conflito;
4. não executar `DROP`, `DELETE`, cascade, cleanup ou restauração de snapshot.

Smoke após publicação autorizada:

1. autenticar com usuário sintético e confirmar oito capacidades;
2. abrir lista, detalhe e editor;
3. salvar preferências com `Idempotency-Key`, repetir a mesma requisição e
   confirmar replay sem nova revisão;
4. recarregar em outro contexto e confirmar sincronização;
5. provocar revisão divergente e confirmar HTTP 409 sem sobrescrita;
6. validar teclado, leitor de tela, 320 px, alto contraste, 200%, movimento
   reduzido, offline e exportação tátil;
7. confirmar que nenhum comando de impressora, agente, Moonraker ou firmware
   foi emitido.

Rollback: restaurar release N-1 e preservar
`accessibility_preferences`. Não interromper backend, worker, agente,
Moonraker ou impressora para limpar preferências. O schema é aditivo e pode
permanecer sem consumidor.

## PKG-104 — Proteção essencial

Validação local:

```bash
cd backend
.venv/bin/python -m pytest -q tests/test_platform_protection.py tests/test_auth.py tests/test_social_catalog.py tests/test_agent_channel.py
cd ../agent
go test ./...
cd ../frontend
PATH=/Users/brenomayder/.nvm/versions/node/v22.22.0/bin:$PATH npm run build
cd ..
PATH=/Users/brenomayder/.nvm/versions/node/v22.22.0/bin:$PATH RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
```

Banco:

1. aplicar `backend/sql/087_platform_protection.sql` no SQLite pelo bootstrap;
2. aplicar `backend/sql/postgresql/019_platform_protection.sql` no PostgreSQL
   pelo fluxo privilegiado;
3. validar coluna MFA pendente, tabelas, índices, constraints, retenção de 180
   dias e registro em `schema_versions`;
4. não executar `DROP`, `DELETE`, cascade, prune ou restauração de snapshot.

Incidente de conta:

1. preservar `request_id`, usuário, sessões opacas e trilhas existentes sem
   copiar token ou payload sensível;
2. revogar todas as sessões da conta e exigir nova senha/MFA;
3. se houver abuso ativo, desativar novas operações com
   `PRINTORA_PLATFORM_PROTECTION_WRITES_ENABLED=false`;
4. registrar owner de operações e expiração em até 24 horas;
5. corrigir ou restaurar a release N-1, reativar a flag e retestar login,
   step-up, exportação e recurso;
6. manter solicitações e auditoria por 180 dias.

Incidente de artefato:

1. bloquear a versão no manifesto sem interromper impressão em andamento;
2. confirmar SHA-256, assinatura, identidade da chave e protocolo;
3. restaurar o binário N-1 pelo backup do agente e executar health check;
4. publicar correção com nova versão; nunca reutilizar artefato ou tag.

Controles adicionais:

1. updates da aplicação usam somente o repositório GitHub configurado; uma URL
   informada pelo cliente não pode trocar a origem;
2. download de release do agente aceita URL relativa ou absoluta somente na
   mesma origem HTTPS do manifesto e rejeita redirecionamento externo;
3. instaladores locais não executam scripts baixados diretamente da rede;
   Homebrew e nvm ausentes devem ser instalados por procedimento verificado;
4. IDs globais de backup, manutenção, snapshot e firmware são revalidados no
   escopo do usuário antes de leitura ou mutação;
5. diagnóstico, fatiamento e mutações de update falham fechado sem sessão;
6. toda ação física exige preview, confirmação do cliente e step-up, e permanece
   bloqueada enquanto houver impressão ativa.

Rollback: a flag suspende apenas novas exportações, desativações e recursos. Ela
não apaga dados nem desfaz ações já concluídas. Preservar schema e auditoria,
restaurar release N-1 compatível e reativar em até 24 horas.
