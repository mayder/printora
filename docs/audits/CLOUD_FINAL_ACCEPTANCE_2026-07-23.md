# Aceite Final Da Arquitetura Cloud

Data: 2026-07-23

## Escopo e segurança

Consolidação dos pacotes arquiteturais sem acesso a impressora, agente,
Moonraker, Klipper, MCU ou Raspberry Pi. Nenhuma tabela, linha, objeto, arquivo,
backup ou release foi excluído. Limpezas destrutivas continuam dependentes de
preview e confirmação específica.

## Manifesto e legado

- topologia e owners consolidados em
  `docs/architecture/FINAL_ARCHITECTURE_MANIFEST.md`;
- scanner integrado ao `check.sh` cobre código, imports, env, SQL, filesystem
  versionado, units, workflows, docs, testes, lockfiles e gerador de SBOM;
- transition outbox, dual-read/write, canário/cutover e scripts SQLite cloud
  estão ausentes;
- contrato interno `database_transition` foi removido em favor de
  `database_runtime`;
- importação controlada com `PRINTORA_RUNTIME_PROFILE=cloud` provou
  `sqlite3` ausente de `sys.modules`;
- SQLite, launcher local, transições de negócio e bridge USB-CAN foram
  classificados como capacidades válidas, não legado cloud.

## Revisão local

- gate estrito: scans de segredo e nomes internos, scanner final, fronteiras
  modulares, contratos OpenAPI/realtime, 566 testes backend, testes Go, build e
  testes frontend aprovados;
- testes focados de schema, packaging e adapter PostgreSQL: 44 aprovados;
- SBOM CycloneDX reproduzível gerado para backend, frontend e agente;
- `npm audit`, `pip-audit` e `govulncheck`: zero vulnerabilidade conhecida;
- nenhum arquivo alterado ultrapassou o limite. Arquivos históricos acima de
  1.000 linhas foram revisados e permanecem dívida incremental com owner, sem
  receber nova responsabilidade neste pacote.

## Evidência acumulada

- deploy/rollback sob escrita: PKG-86, zero perda e indisponibilidade observável;
- reconciliação SQLite/PostgreSQL e remoção da ponte: PKG-88;
- objetos/busca e restore independente: PKG-90 e PKG-93;
- filas, realtime, caos e backpressure: PKG-89 e PKG-93;
- finanças/fabricação: PKG-91 e PKG-92;
- carga analítica isolada: PKG-94, 1.004 eventos e 600 readiness sem erro;
- restore externo integral: 203 s, 146 tabelas, zero FK inválida, objetos e
  documentos reconciliados;
- soak anterior: 120 s, 600 requests sem erro e capacidade residual superior a
  24 GiB de RAM e 110 GiB de disco.

## Publicação e auditoria efetiva

- workflow `29986097612` publicou `73057bf` após gate completo, auditorias de
  dependência, SBOM, preflight, bundle imutável, blue/green e smoke público;
- auditoria read-only: release ativa e réplica iguais, duas instâncias web,
  zero SQLite carregado, 157 tabelas, 87 revisões, zero índice/constraint
  inválida e role analítica `1:0:0`;
- filas: zero job leased/running e zero outbox em processamento; 6 objetos e 6
  referências canônicas;
- preflight final: todas as verificações aprovadas, incluindo backup externo,
  PostgreSQL, Redis recomponível, storage, workers, certificados e capacidade;
- soak de 120 s: 600 requests, zero erro, p95 máximo de 1.489 ms;
- capacidade após soak: cerca de 24 GiB de RAM e 110 GiB de disco disponíveis;
- rollback para N-1 sob 600 requests: zero erro, p95 246 ms,
  `data_restored=false`; a release final foi republicada e a auditoria repetida
  com sucesso.

## Backup e restore final

O primeiro restore repetido identificou corretamente que o snapshot anterior
era anterior ao schema analítico: ele restaurou 146 tabelas/86 revisões, mas a
release atual recusou iniciar a busca sem as 11 tabelas `analytics_*`. O teste
ocorreu em cluster temporário isolado e não alterou produção.

Um novo snapshot externo criptografado `aeebfcc1` foi criado sem apagar os
anteriores. O segundo restore concluiu:

- 12 arquivos de configuração com checksum;
- 157 tabelas e 87 revisões;
- zero foreign key inválida;
- 8 versões de objetos com checksum;
- 6 objetos canônicos reconciliados;
- 364 documentos de busca reconstruídos em 6,711 s;
- cluster isolado promovido e encerrado sem iniciar a aplicação.

O backup antigo não foi excluído; retenção continua uma operação supervisionada
separada.

## Rollback

Rollback troca para N-1 sem restaurar dados. Recuperação física usa backup base,
WAL, objetos versionados e configuração externa criptografada. O host único
continua sendo redundância de processo, não alta disponibilidade física.
