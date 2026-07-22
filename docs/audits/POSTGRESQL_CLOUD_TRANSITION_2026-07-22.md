# Evidência Da Transição PostgreSQL Cloud

Data: 2026-07-22.

## Topologia Publicada

- cluster dedicado PostgreSQL 16 `16/printora`, porta `5433`, somente loopback;
- data checksums e archive mode ativos;
- role owner sem login e role mínima exclusiva da aplicação;
- 101 tabelas físicas, sendo 100 tabelas de aplicação e uma estrutura transitória
  mantida sem uso até autorização de limpeza de dados;
- 187 chaves estrangeiras validadas e 26 sequences sincronizadas;
- o PostgreSQL compartilhado da porta `5432` e suas aplicações não foram alterados.

## Migração E Integridade

- snapshot consistente importado: 706.023 registros em 100 tabelas de aplicação;
- primeiro relatório alinhado: watermark `8167`, 100/100 tabelas, zero checksum
  divergente, zero FK inválida e zero sequence insegura;
- canário PostgreSQL privado validou health, readiness, catálogo, versão, social,
  autenticação e manifesto sem receber tráfego público;
- segundo relatório após iniciar o canário: watermark `10067`, 100/100 tabelas,
  187/187 FKs e zero divergência;
- cutover executado sob lock final da origem no watermark `11494`, sem restaurar
  snapshot e sem apagar a origem anterior.

## Backup E Recuperação

- backup físico com `pg_basebackup`, WAL por streaming e arquivo externo;
- dump lógico customizado com checksum no mesmo snapshot de recuperação;
- snapshot externo criptografado `98ca79cc`, sem prune ou retenção destrutiva;
- restore real em cluster temporário isolado: banco fora de recovery, 101 tabelas,
  74 versões registradas e zero FK inválida;
- o ensaio não iniciou a aplicação e removeu somente o diretório temporário exato;
- leitura/escrita do restore foi limitada para preservar o SLO do host compartilhado.

## Cutover E Rollback De Código

- após o cutover, eventos reais do agente avançaram de `282037` para `282064`;
- deploy blue/green da release `7f601046e65b7e7103c86994eabafb4e205c0134`
  passou no workflow `29963425375` e preservou 172 eventos posteriores ao marco;
- rollback para a release PostgreSQL-compatible
  `833598654c4b3532b5e2e6b01a40f014fa4a6835` declarou
  `data_restored=false`;
- o maior evento passou de `282209` antes do rollback para `282228` depois dele;
- health, readiness, catálogo, versão, social e manifesto permaneceram disponíveis.

## Contração Do Runtime

- o perfil cloud exige URL PostgreSQL e não importa o driver/adapters locais;
- unit, preflight, backup, restore e deploy cloud apontam somente para PostgreSQL;
- scripts, flags, outbox, canário e cutover transitórios foram retirados do release
  final, com gate bloqueante em `check.sh`;
- o modo local continua usando e testando seu adapter SQLite independente;
- o arquivo e os backups antigos do servidor foram preservados, pois a exclusão
  depende de confirmação humana explícita.

## Segurança Operacional

- nenhum comando foi enviado à impressora, Moonraker, Klipper, MCU ou Raspberry Pi;
- a impressão física em andamento não foi reiniciada nem interrompida;
- tarefas pesadas de sombra/restore foram pausadas ou limitadas quando afetaram a
  latência do processo web;
- segredos, URLs com senha e payloads sensíveis não foram registrados nesta evidência.
