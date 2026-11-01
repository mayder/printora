-- Execução exclusiva no cluster dedicado 16/printora, porta 5433.
-- Autorização do owner em 2026-11-01: sem backup automático/PITR.
-- Pré-condições: nenhuma réplica/slot; timers de backup/WAL/restore parados.
-- ALTER SYSTEM não pode executar dentro de transação. Requer superuser.
-- Após executar: reiniciar SOMENTE postgresql@16-printora.service.
-- Validar: SHOW archive_mode = off; archive_timeout = 0; archive_command = (disabled);
-- fsync, full_page_writes e synchronous_commit permanecem on.
-- Não altera dados, tabelas, pg_wal ou a segurança transacional do banco.
ALTER SYSTEM SET archive_mode = 'off';
ALTER SYSTEM SET archive_timeout = '0';
ALTER SYSTEM SET archive_command = '';
-- Rollback (sem recuperar o intervalo não arquivado):
-- ALTER SYSTEM RESET archive_mode;
-- ALTER SYSTEM RESET archive_timeout;
-- ALTER SYSTEM RESET archive_command;
-- Reverter a política versionada (cujo padrão agora é off), configurar
-- archive_mode on, reiniciar somente Printora, reprovisionar timers mascarados,
-- criar nova base externa e validar restore antes de afirmar cobertura PITR.
