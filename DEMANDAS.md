# DEMANDAS.md

## Índice De Pacotes

- PKG-01: Base do projeto e documentação operacional
- PKG-02: Auditoria somente leitura do ambiente Klipper
- PKG-03: Checklist pós-update guiado
- PKG-04: Health check da impressora
- PKG-05: Gerenciador de backups
- PKG-06: Relatórios sanitizados
- PKG-07: Diário da impressora e manutenção preventiva
- PKG-08: Assistente de primeira camada e Z-offset
- PKG-09: Monitor CAN
- PKG-10: Gestão de mods e plugins
- PKG-11: Firmware Manager - cadastro de placas e presets
- PKG-12: Firmware Manager - build e dry-run
- PKG-13: Firmware Manager - flash controlado
- PKG-14: Integração Mainsail e Update Manager

## PKG-01: Base Do Projeto E Documentação Operacional

Objetivo:

Criar estrutura mínima do projeto, escopo, governança, backlog, testes, bugs e check script.

Entregáveis:

- `ESCOPO.md`
- `CODEX_PATHS.toml`
- `QUALITY_ROADMAP.md`
- `GOVERNANCA.md`
- `DEMANDAS.md`
- `TESTS.md`
- `BUGS.md`
- `check.sh`
- `.gitignore`

Critério de aceite:

- `./check.sh` passa.
- Documentos principais existem.

## PKG-02: Auditoria Somente Leitura Do Ambiente Klipper

Objetivo:

Criar diagnóstico inicial sem alterar nada.

Verificar:

- `printer_data/config`;
- includes quebrados;
- macros suspeitas;
- symlinks quebrados;
- logs recentes;
- plugins externos;
- repos Git;
- systemd;
- Moonraker Update Manager.

Critério de aceite:

- relatório classifica achados em corrigir agora, monitorar, ignorar e precisa confirmação.

Estado atual:

- MVP parcial implementado via `GET /api/audit/read-only`.
- Classificação inicial cobre Klipper, Moonraker, Update Manager e sinais básicos do host.
- Próximo incremento: incluir leitura segura de logs, systemd, includes e symlinks.

## PKG-03: Checklist Pós-Update Guiado

Objetivo:

Criar fluxo orientado para validar impressora após updates.

Critério de aceite:

- resultado final simples: "seguro imprimir" ou "não imprima ainda".

## PKG-04: Health Check Da Impressora

Objetivo:

Exibir saúde operacional.

Itens:

- CPU/RAM/disco;
- temperatura Raspberry Pi;
- temperatura MCUs;
- serviços falhando;
- Klipper/Moonraker ready;
- latência API;
- alertas.

## PKG-05: Gerenciador De Backups

Objetivo:

Criar snapshots seguros de configs e dados relevantes.

Regras:

- backup antes de alterar;
- comparação visual;
- restauração por arquivo;
- histórico.

## PKG-06: Relatórios Sanitizados

Objetivo:

Exportar diagnóstico para comunidade/suporte sem segredos.

Remover:

- senhas;
- tokens;
- chaves;
- URLs privadas;
- dados pessoais.

## PKG-07: Diário Da Impressora E Manutenção Preventiva

Objetivo:

Registrar manutenção, falhas, ajustes e alertas por intervalo.

Itens:

- lubrificação;
- correias;
- parafusos;
- fans;
- conectores CAN;
- hotend/nozzle;
- limpeza de mesa.

## PKG-08: Assistente De Primeira Camada E Z-Offset

Objetivo:

Guiar ajuste de primeira camada.

Itens:

- wizard para `PROBE_CALIBRATE`;
- histórico de Z-offset por chapa/material;
- comparação com valor anterior;
- alerta se mudança for grande;
- notas e fotos opcionais.

## PKG-09: Monitor CAN

Objetivo:

Monitorar saúde CAN e histórico por impressão.

Itens:

- `rx_error`;
- `tx_error`;
- `tx_retries`;
- `ip -details -statistics link show can0`;
- comparação antes/depois;
- diagnóstico físico sugerido.

## PKG-10: Gestão De Mods E Plugins

Objetivo:

Mostrar plugins instalados, ativos, legados e arriscados.

Itens:

- KAMP;
- KTC/StealthChanger;
- `led_effect`;
- Crowsnest;
- Sonar;
- Timelapse;
- Auto Speed;
- TMC Autotune.

Critério de aceite:

- usuário vê o que manter, remover, atualizar ou investigar.

## PKG-11: Firmware Manager - Cadastro De Placas E Presets

Objetivo:

Cadastrar placas e presets.

Itens:

- Octopus;
- EBB;
- SB2209/SB2240;
- Mellow;
- Fysetc;
- presets com MCU, bootloader, pins, build output e flash methods.

## PKG-12: Firmware Manager - Build E Dry-Run

Objetivo:

Compilar firmware sem fazer flash.

Fluxo:

1. validar Klipper;
2. backup de `.config`;
3. aplicar preset;
4. `make clean`;
5. `make`;
6. salvar binário;
7. salvar log.

Critério de aceite:

- dry-run mostra exatamente o que seria feito.

## PKG-13: Firmware Manager - Flash Controlado

Objetivo:

Executar flash com segurança.

Regras:

- bloquear se impressão em andamento;
- validar UUID;
- exigir confirmação;
- salvar backup;
- salvar log;
- validar retorno da MCU;
- reiniciar Klipper;
- confirmar `printer/info ready`.

## PKG-14: Integração Mainsail E Update Manager

Objetivo:

Integrar app ao ecossistema.

Itens:

- link no Mainsail custom navigation;
- serviço systemd;
- entrada no Moonraker Update Manager;
- documentação de instalação;
- documentação de rollback.
