# GOVERNANCA.md

## Objetivo

Definir regras de segurança, prioridade, riscos e rollback para o Printora.

## Princípios

- Segurança da impressora vem antes de conveniência.
- O usuário deve entender o que será alterado antes de ações perigosas.
- Backup deve ser automático antes de qualquer mutação relevante.
- Flash de firmware deve ser tratado como operação crítica.
- Diagnóstico deve ser preferido a tentativa cega de correção.

## Escopo Seguro

Operações consideradas seguras:

- leitura de logs;
- leitura de status Moonraker/Klipper;
- leitura de status CAN;
- leitura de Update Manager;
- leitura de systemd;
- geração de relatório sanitizado;
- criação de backup;
- dry-run de comandos.

Operações que exigem confirmação:

- editar configs Klipper/Moonraker/Mainsail;
- reiniciar Klipper;
- reiniciar Moonraker;
- reiniciar serviços systemd;
- aplicar update;
- compilar firmware;
- fazer flash de MCU;
- restaurar backup.

Operações proibidas sem fluxo explícito:

- apagar configs sem backup;
- apagar histórico;
- sobrescrever `.config` de firmware;
- fazer flash se impressora estiver imprimindo;
- rodar comandos destrutivos sem rollback.

## Gates De Release

Uma versão só pode ser considerada publicável se:

- `./check.sh` passar;
- documentação principal estiver atualizada;
- riscos conhecidos estiverem em `BUGS.md`;
- fluxos perigosos tiverem confirmação e dry-run;
- dados sensíveis não estiverem versionados;
- o rollback mínimo estiver documentado.
- a tag da versao estiver publicada no remoto;
- a GitHub Release correspondente estiver criada, pois o verificador de releases do app usa GitHub Releases como fonte publica.

Migrations são proibidas. Toda alteração de banco deve ser entregue como script `.sql` idempotente em `backend/sql/`, com rollback e impacto documentados.

Em branch `main` ou `hml`, a IA deve perguntar antes de editar quando o usuário não tiver autorizado explicitamente o uso da branch.

## Riscos Principais

### Firmware

Risco: flash incorreto pode deixar MCU offline.

Mitigações:

- preservar `.config`;
- preservar binário anterior;
- validar UUID antes e depois;
- registrar comando usado;
- exigir checklist antes do flash;
- fornecer rollback manual.

### Configuração Klipper

Risco: alteração incorreta pode impedir Klipper de iniciar.

Mitigações:

- backup antes da edição;
- validação de includes;
- reinício controlado;
- confirmação de `printer/info ready`.

### Banco Local

Risco: corromper histórico ou inventário.

Mitigações:

- SQLite com backup;
- migrações idempotentes ou versionamento interno;
- exportação de dados;
- nunca armazenar segredo em texto puro.

### Relatórios

Risco: vazar senhas, tokens, IPs ou dados privados.

Mitigações:

- sanitização obrigatória;
- preview antes de exportar;
- lista de campos removidos.

### Observabilidade Do Agente

Risco: dados de suporte exporem credenciais, tokens, chaves ou payload sensível.

Mitigações:

- pacote de suporte sanitizado por padrão;
- nunca retornar credencial completa do agente;
- redigir tokens `ptr_agent_*`, `ptr_pair_*` e `ptr_sess_*`;
- limitar log tail e eventos recentes;
- retenção operacional de eventos/jobs de agente em 180 dias;
- limpeza somente por rotina supervisionada enquanto não houver job dedicado de retenção.

## Priorização

Ordem recomendada:

1. Auditoria somente leitura.
2. Checklist pós-update.
3. Health check.
4. Backups.
5. Relatórios.
6. Diário/manutenção.
7. Z-offset e primeira camada.
8. Monitor CAN histórico.
9. Gestão de plugins.
10. Firmware Manager com dry-run.
11. Firmware Manager com flash real.

## Rollback

Todo módulo que altera algo deve registrar:

- arquivo afetado;
- backup criado;
- comando executado;
- resultado;
- instrução de rollback.

Rollback mínimo para configs:

```bash
cp /path/do/backup.cfg /home/pi/printer_data/config/arquivo.cfg
sudo systemctl restart klipper
curl -s http://127.0.0.1:7125/printer/info
```

Rollback mínimo para firmware:

```text
1. localizar binário anterior;
2. colocar placa em bootloader;
3. executar comando de flash anterior;
4. validar UUID;
5. reiniciar Klipper;
6. confirmar printer/info ready.
```
