# TESTS.md

## Objetivo

Definir validações mínimas para o MayderPrintLab.

## Check Local

Comando obrigatório antes de commit:

```bash
./check.sh
```

O check inicial valida:

- existência dos documentos principais;
- ausência de marcadores básicos de segredo;
- formato básico do `CODEX_PATHS.toml`;
- permissão executável do `check.sh`.

## Testes Manuais Futuros

### Auditoria

- Rodar auditoria em ambiente Klipper real.
- Confirmar que não altera arquivos.
- Confirmar classificação dos achados.

### Backups

- Criar backup.
- Confirmar arquivos incluídos.
- Confirmar que segredos não vazam.
- Testar restauração por arquivo em ambiente controlado.

### Firmware Dry-Run

- Cadastrar placa.
- Selecionar preset.
- Rodar dry-run.
- Confirmar que nenhum flash foi feito.
- Confirmar log completo.

### Firmware Flash

Executar somente em ambiente autorizado.

Critérios:

- impressora parada;
- backup criado;
- UUID validado;
- binário gerado;
- flash concluído;
- MCU voltou;
- Klipper ready.

### UI

- Abrir app em navegador normal.
- Abrir app pelo Mainsail.
- Validar layout desktop.
- Validar layout no navegador embutido do OrcaSlicer.

## Critérios Para Não Avançar

Não avançar se:

- `./check.sh` falhar;
- houver risco de flash sem confirmação;
- houver alteração de config sem backup;
- relatório expuser segredo;
- app não conseguir distinguir leitura de mutação.
