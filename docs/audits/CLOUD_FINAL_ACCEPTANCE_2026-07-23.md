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

Pendente da publicação da release final e execução read-only de:

```bash
sudo /usr/local/libexec/printora-cloud/audit-final-architecture.sh
sudo /usr/local/sbin/printora-cloud-preflight
```

O fechamento só será registrado após release ativa/réplica iguais, duas
readiness, units canônicas ativas, zero artefato aposentado, zero SQLite
carregado, zero índice/constraint inválida e role analítica `1:0:0`.

## Rollback

Rollback troca para N-1 sem restaurar dados. Recuperação física usa backup base,
WAL, objetos versionados e configuração externa criptografada. O host único
continua sendo redundância de processo, não alta disponibilidade física.
