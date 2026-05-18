# Auditoria Read-Only Da Voron - 2026-05-18

## Escopo

Auditoria executada depois que a impressora ficou ociosa.

Operações realizadas:

- leitura de estado Klipper/Moonraker;
- leitura de `print_stats`;
- leitura de disco;
- leitura de `systemctl --failed`;
- leitura de serviços relevantes;
- leitura de CAN `can0`;
- leitura de includes e referências antigas;
- leitura de symlinks quebrados;
- leitura de repositórios Git;
- leitura recente de logs;
- commit local do `SAVE_CONFIG` já existente em `printer.cfg`.

Não foi feito:

- restart de Klipper/Moonraker;
- edição de config;
- update;
- flash;
- remoção de arquivo;
- alteração de firmware.

## Estado Geral

- Klipper: `ready`.
- Impressão: `standby`.
- Moonraker: conectado ao Klipper.
- `systemctl --failed`: `0 loaded units listed`.
- Disco: `/dev/root` com aproximadamente 18 GB livres, 38% usado.
- CAN `can0`: `ERROR-ACTIVE`, `rx_error=0`, `tx_error=0`, sem bus-off.

## Corrigir Agora

Nenhum item crítico encontrado.

## Monitorar

### Klipper `software_version` Com `-dirty`

O Klipper continua mostrando:

```text
v0.13.0-656-g4cc47cf5-dirty
```

O Update Manager reporta o repo Klipper como limpo. Isso é compatível com o uso de módulos externos ativos em `klippy/extras`, principalmente KTC-Easy e `led_effect`.

Ação recomendada:

- manter como item monitorado;
- não criar workaround cosmético;
- revisar novamente se o Update Manager passar a mostrar `is_dirty=True`.

### Diretório Antigo `/home/pi/timelapse`

Existe um diretório `/home/pi/timelapse`, mas ele não é repo Git e não aparece como serviço ativo.

Ação recomendada:

- pode ser removido depois de confirmação explícita;
- baixo risco, mas não é necessário para funcionamento atual.

### Symlinks Quebrados Em Backups

Há symlinks quebrados dentro de:

```text
/home/pi/printer_data/config/backups/cleanup_unused_20260516-223642/
```

Eles estão em arquivos arquivados, fora dos includes ativos.

Ação recomendada:

- ignorar no funcionamento diário;
- limpar apenas quando for revisar `cleanup_archives` e backups antigos.

## Ignorar

### Crowsnest E Sonar

Não há `crowsnest.service` nem `sonar.service` ativos.

Serviços relevantes encontrados:

```text
klipper.service
moonraker.service
nginx.service
Spoolman.service
```

### Referências Antigas Ativas

Não foram encontradas referências ativas a:

- `tapchanger`;
- `auto_speed`;
- `sonar`;
- `crowsnest`;
- `timelapse`;
- `tmc_autotune`.

As ocorrências restantes estão em backups, snapshots ou configs read-only arquivadas.

### CAN

CAN está saudável na coleta:

```text
can0 state ERROR-ACTIVE
rx_error=0
tx_error=0
tx_retries=0
```

Sem indício atual de problema físico/elétrico.

## Ação Executada

O `printer.cfg` estava sujo no git porque o Klipper gravou um `SAVE_CONFIG` com o `bed_mesh default`.

Foi feito commit local no repo de configuração da Raspberry:

```text
5cccfdb Record saved bed mesh
```

Validação após o commit:

```text
Klipper state: ready
Printer is ready
```

## Próximos Passos Seguros

1. Transformar esta auditoria SSH em coletor read-only dentro do MayderPrintLab.
2. Adicionar parser para logs recentes com resumo em vez de log bruto.
3. Adicionar seção de limpeza sugerida para diretórios legados, sempre com confirmação.
4. Adicionar monitor CAN histórico.
5. Criar módulo de knowledge base CAN com dados estruturados do guia Esoterical.
