# Printora - Escopo

## Visão

Printora é uma ferramenta externa para o ecossistema Klipper/Moonraker/Mainsail, inspirada no modelo do Spoolman: aplicação web própria, API própria, banco local, serviço systemd, integração com Moonraker e entrada no Mainsail via navegação customizada.

O objetivo é resolver uma lacuna comum em impressoras Klipper avançadas: operação, manutenção, auditoria, firmware e confiabilidade ficam espalhados entre logs, configs, SSH, macros, plugins, Update Manager e memória do usuário.

O projeto deve ajudar o usuário a manter a impressora saudável sem precisar ser especialista em Linux, systemd, CAN, Git, Klipper, Moonraker e firmware ao mesmo tempo.

## Conhecimento técnico e comunidade

Comunidade existe para melhorar diagnóstico, reprodução de resultados,
projetos e evidência técnica. Ela não transforma o Printora em rede social,
marketplace, plataforma educacional ou sistema financeiro.

O norte é aumentar:

- impressão bem-sucedida e reproduzível;
- resolução confirmada de problemas;
- manutenção e disponibilidade da impressora;
- organização de projetos, arquivos, materiais e perfis;
- segurança, privacidade, acessibilidade e confiança.

O inventário amplo em `docs/community/` é histórico de ideias. Somente
`DEMANDAS.md` e `PACKAGE_PORTFOLIO.csv` autorizam execução.

## Arquitetura real do projeto

- Monorepo com backend Python/FastAPI em `backend/`.
- Frontend Vite/React/TypeScript em `frontend/`.
- Banco local SQLite gerenciado pelo backend.
- Scripts operacionais e validadores na raiz em `scripts/`.
- A raiz e a fonte de verdade para governanca, backlog, testes, decisoes, telas e runbook.

## Nomenclatura oficial do projeto

| Conceito | Nome usado | Onde fica | Observacao |
|---|---|---|---|
| Entrada HTTP | route/endpoint | `backend/app` | Manter fina, sem regra pesada |
| Regra de aplicacao | service/function coesa | `backend/app` | Separar regra de transporte |
| Persistencia | store/repository/sql helper | `backend/app`, `backend/sql` | Sem migrations |
| Integracao externa | client/adapter | `backend/app/moonraker.py` e similares | Isolar Moonraker/Klipper/systemd |
| Payload publico | request/response/schema | backend/frontend | Nao vazar entidade interna |
| Tela | page/view/component | `frontend/src` | Sem regra de negocio pesada |
| Estado de tela | state/view model/hook | `frontend/src` | Coordenar UI e API |
| Teste | unit/contract/flow | `backend/tests`, `frontend/tests` | Fixtures controladas |

## Modelo de Integração

Printora não deve tentar modificar o Mainsail como um plugin nativo. O Mainsail não possui um sistema completo de plugins para telas internas complexas.

O modelo correto é:

```text
Printora
├── backend Python/FastAPI ou Node
├── banco SQLite local
├── frontend web
├── systemd service
├── integração com Moonraker
├── entrada no Update Manager
└── link no Mainsail custom navigation
```

Exemplo de URL local:

```text
http://voron.local:8069
```

Exemplo de banco local:

```text
/home/pi/.local/share/printora/printora.db
```

Exemplo de Update Manager:

```ini
[update_manager printora]
type: git_repo
path: /home/pi/Printora
origin: https://github.com/mayder/printora.git
primary_branch: main
managed_services: printora
```

## Ideias Fortes Para A Comunidade

### 1. Checklist Pós-Update Guiado

- Verificar se Klipper está `ready`.
- Verificar Moonraker conectado.
- Verificar Update Manager sem warnings.
- Verificar serviços systemd falhando.
- Verificar erros recentes em `klippy.log`.
- Verificar erros recentes em `moonraker.log`.
- Verificar saúde CAN.
- Verificar compatibilidade de firmware das MCUs.
- Exibir resultado claro: "seguro imprimir" ou "não imprima ainda".

### 2. Auditoria De Configuração

- Detectar includes quebrados.
- Detectar macros que chamam arquivos ou comandos inexistentes.
- Detectar plugins instalados mas não usados.
- Detectar configs duplicadas ou conflitantes.
- Detectar `SAVE_CONFIG` perdido em `printer.cfg`.
- Classificar itens como necessário, opcional, lixo técnico, perigoso remover.
- Sugerir ações seguras com backup.

### 3. Gerenciador De Backups

- Backup automático antes de updates.
- Backup antes de editar configs.
- Snapshot de `printer_data/config`.
- Comparação visual entre backups.
- Restauração segura por arquivo.
- Histórico: "o que mudou desde a última impressão boa".

### 4. Health Check Da Impressora

- Temperaturas ociosas.
- Temperatura da Raspberry Pi.
- Temperatura das MCUs.
- Uso de CPU, RAM e disco.
- Espaço livre.
- Serviços ativos e falhando.
- Latência Moonraker/Klipper.
- Alertas antes de imprimir.

### 5. Monitor CAN

- Ler `rx_error`, `tx_error` e `tx_retries`.
- Manter histórico por impressão.
- Alertar quando contador cresce.
- Sugerir diagnóstico mínimo: cabo, terminação, alimentação, aterramento, conectores e bitrate.
- Comparar antes e depois de zerar contadores.

### 6. Assistente De Primeira Camada

- Registrar Z-offset por chapa e material.
- Manter histórico de ajustes.
- Wizard para `PROBE_CALIBRATE`.
- Comparar offset atual com offset anterior.
- Alertar quando offset mudou muito.
- Permitir fotos ou notas opcionais da primeira camada.

### 7. Manutenção Preventiva

- Controlar horas de impressão.
- Controlar metros ou gramas de filamento.
- Criar checklists por intervalo:
  - limpar mesa;
  - lubrificar trilhos;
  - verificar correias;
  - apertar parafusos;
  - limpar fans;
  - revisar conectores CAN;
  - revisar hotend/nozzle.
- Gerar alertas por tempo, horas de uso ou número de impressões.

### 8. Gestão De Mods E Plugins

- Listar KAMP, KTC, `led_effect`, Crowsnest, Sonar, Timelapse e outros.
- Mostrar versão, repositório e status Git.
- Mostrar se está ativo na configuração.
- Mostrar se está instalado mas sem uso.
- Sugerir ação segura: manter, atualizar, remover depois de backup.

### 9. Firmware Manager Documentado

- Registrar UUIDs CAN.
- Registrar `.config` usado por MCU.
- Registrar binários gerados.
- Registrar comandos de flash usados.
- Manter histórico de firmware por placa.
- Exigir checklist antes de flash.
- Documentar rollback.

### 10. Diário Da Impressora

- Registrar cada manutenção feita.
- Registrar cada falha encontrada.
- Registrar cada ajuste de offset.
- Registrar cada troca de nozzle.
- Registrar cada atualização de firmware.
- Registrar cada limpeza e lubrificação.
- Manter histórico pesquisável.

### 11. Validador De Print Start

Antes de imprimir, validar:

- Klipper ready.
- QGL recente.
- Mesh recente.
- Spool selecionado.
- Filamento suficiente.
- Temperatura ambiente/chamber aceitável.
- CAN sem erro recente.

Resultado esperado:

```text
OK para imprimir
```

ou:

```text
Não imprima ainda
```

### 12. Relatórios Compartilháveis

- Exportar diagnóstico para Discord, fórum ou issue.
- Gerar relatório sanitizado sem senhas, tokens ou chaves.
- Incluir logs relevantes, versões, configs e erros recentes.
- Facilitar pedido de ajuda na comunidade sem expor dados sensíveis.

## Diferencial

A maioria das ferramentas atuais resolve uma área isolada: câmera, spool, update, timelapse. O Printora deve resolver operação e confiabilidade.

Resumo do produto:

```text
Printora
- Saúde
- Updates
- Backups
- CAN
- Z-offset
- Manutenção
- Plugins
- Firmware
- Relatórios
```

## Klipper Firmware Manager

Um dos módulos principais será o Klipper Firmware Manager, pensado para transformar atualização de firmware em um fluxo seguro, repetível e documentado.

Hoje atualizar firmware exige uma sequência manual, arriscada e fácil de esquecer. O Printora deve permitir cadastrar as placas uma vez e depois atualizar por botão, com validação e rollback.

### Cadastro De Placas

Exemplo:

```text
Octopus
- tipo: BTT Octopus Pro
- conexão: USB-CAN bridge
- MCU: STM32F446
- bootloader: Katapult ou DFU
- CAN UUID: 862bb5a4c690
- interface: can0
- firmware config: octopus_usb_can.config

EBB T0
- tipo: BTT EBB36 / EBB42
- conexão: CAN
- MCU: STM32G0B1
- CAN UUID: fd7bbba1e6aa
- interface: can0
- firmware config: ebb_can.config
```

### Fluxo De Atualização

Ao clicar em "Atualizar firmware", o app deve:

1. Verificar a versão atual do Klipper.
2. Fazer backup das configs `.config`.
3. Validar UUID CAN.
4. Rodar `make clean`.
5. Aplicar a `.config` correta.
6. Rodar `make`.
7. Gerar binário.
8. Colocar placa em modo bootloader, quando necessário.
9. Executar flash.
10. Reiniciar Klipper.
11. Confirmar `printer/info ready`.
12. Registrar tudo no histórico.

### Arquivo De Configuração

Formato conceitual em INI:

```ini
# pcb_config.cfg

[board octopus]
name: Octopus USB-CAN bridge
type: btt_octopus_pro_v1.1
connection: usb_can_bridge
mcu: stm32f446
can_uuid: 862bb5a4c690
can_interface: can0
config_file: firmware/octopus_usb_can.config
flash_method: katapult_usb_can

[board ebb_t0]
name: EBB T0
type: btt_ebb36_g0b1
connection: can
mcu: stm32g0b1
can_uuid: fd7bbba1e6aa
can_interface: can0
config_file: firmware/ebb_g0b1_can.config
flash_method: katapult_can
```

Formato preferido para a aplicação:

```yaml
boards:
  - id: octopus
    name: Octopus USB-CAN Bridge
    preset: btt_octopus_pro_v1_1_usb_can
    can_uuid: 862bb5a4c690
    can_interface: can0
    config_file: octopus_usb_can.config
    flash_method: katapult_usb_can

  - id: ebb_t0
    name: EBB T0
    preset: btt_ebb36_g0b1_can
    can_uuid: fd7bbba1e6aa
    can_interface: can0
    config_file: ebb_g0b1_can.config
    flash_method: katapult_can
```

### Presets De Placas

O app deve ter um catálogo de placas comuns:

```text
BTT Octopus v1.1
BTT Octopus Pro STM32F446
BTT Octopus Pro H723
BTT EBB36 STM32G0B1
BTT EBB42 STM32G0B1
BTT SB2209
BTT SB2240
Mellow Fly SB2040
Mellow Fly SHT36
Fysetc Spider
Fysetc SB CAN Toolhead
```

Cada preset deve conter:

- arquitetura do MCU;
- modelo do processador;
- clock;
- bootloader offset;
- interface de comunicação;
- CAN bus pins;
- USB pins;
- caminho esperado do binário;
- método de flash recomendado;
- comandos seguros.

Exemplo:

```yaml
presets:
  btt_ebb36_g0b1_can:
    mcu: stm32g0b1
    architecture: stm32
    communication: canbus
    canbus_pins: PB0/PB1
    bootloader_offset: 8KiB
    build_output: out/klipper.bin
    flash_methods:
      - katapult_can
      - canboot_can
```

### Tela Do Firmware Manager

Fluxo esperado:

```text
Firmware Manager

Placas cadastradas
[Octopus USB-CAN]  Klipper v0.13.0-656  UUID 862bb5a4c690  Atualizar
[EBB T0]           Klipper v0.13.0-656  UUID fd7bbba1e6aa  Atualizar

Botões:
- Validar
- Compilar
- Flash
- Atualizar tudo
- Ver histórico
- Baixar backup
```

Antes de atualizar, exigir checklist:

```text
[ ] Impressora parada
[ ] Hotend frio ou seguro
[ ] Nenhuma impressão em andamento
[ ] Backup criado
[ ] UUID detectado
[ ] Firmware atual documentado
```

### Regras De Segurança Do Firmware Manager

- Nunca fazer flash se Klipper estiver imprimindo.
- Nunca apagar `.config` antiga.
- Salvar binário antigo.
- Salvar log completo do flash.
- Detectar se a placa voltou no CAN.
- Abortar se UUID não bater.
- Ter botão de dry-run.
- Exigir confirmação clara antes de flash.
- Permitir rollback manual documentado.

### Histórico De Firmware

Cada atualização deve gerar registro:

```text
2026-05-17 22:14
Board: EBB T0
Preset: btt_ebb36_g0b1_can
Klipper commit: g4cc47cf5
Config: ebb_g0b1_can.config
Binary: firmware_builds/20260517-2214/ebb_t0/klipper.bin
Flash: success
CAN UUID after flash: fd7bbba1e6aa
Printer state after restart: ready
```

## Nome Do Projeto

Nome escolhido:

```text
Printora
```

Subtítulo:

```text
Klipper firmware, maintenance and diagnostics toolkit
```

Descrição curta:

```text
A Klipper toolkit for firmware, maintenance, diagnostics and printer operations.
```

## Princípios Do Produto

- Segurança antes de automação.
- Backup antes de qualquer ação mutável.
- Dry-run antes de operações perigosas.
- Histórico de tudo que mudou.
- Rollback documentado.
- Integração limpa com Moonraker e Mainsail.
- Zero dependência de edição manual de configs para tarefas repetitivas.
- Diagnósticos claros para usuários não especialistas.
- Relatórios úteis para comunidade e suporte.

## Arquitetura Alvo Plurianual

A evolução técnica oficial está em
`docs/architecture/EVOLUCAO_ARQUITETURAL.md` e nos pacotes `PKG-86` a `PKG-95`.

O produto evolui em quatro etapas:

1. qualificação do host, releases imutáveis, monólito modular, contratos,
   observabilidade e deploy blue/green;
2. PostgreSQL cloud, Redis recomponível, outbox/fila durável, workers, objetos
   S3-compatible, realtime distribuído e busca reconstruível;
3. múltiplas instâncias, resiliência e recuperação;
4. analytics operacional ou ML isolado somente com hipótese aprovada.

Todos os componentes devem executar no servidor cloud atual. Kubernetes,
segundo host e serviços gerenciados não são requisitos. A arquitetura no mesmo
host protege contra falha de processo e deploy, mas não promete sobrevivência à
perda física do servidor.

Após cada cutover, existe apenas um caminho canônico por perfil. O cloud não
mantém fallback SQLite; o SQLite local permanece somente como adapter local
suportado e isolado. Bridges, flags, bancos, arquivos, dependências,
configurações, testes e documentação aposentados são removidos antes do
fechamento, respeitando confirmação explícita e prova de integridade/restauração.

## Confiança Contínua Pós-Arquitetura

A arquitetura base encerrada nos pacotes `PKG-86` a `PKG-95` é seguida pelos
pacotes `PKG-96` a `PKG-99`:

1. agente versionado e distribuído de forma imutável;
2. toolchain, cobertura, E2E, fuzzing, mutation testing e pentest;
3. homologação com impressora/agente reais e soak de 72 horas;
4. RPO físico reduzido e recuperação de desastre continuamente comprovada.

Esses pacotes elevam a confiança sem bloquear a evolução funcional futura e sem
prometer ausência absoluta de defeitos.

## Gerenciador Completo De Arquivos G-code

O `PKG-100` consolida a aba `Arquivos G-code` como gerenciador operacional da
impressora, com listagem paginada, pastas, upload, metadados, preview 3D,
download, fila e ações protegidas. A cloud nunca acessa o Moonraker diretamente:
todo acesso passa pelo agente pareado e respeita permissão, estado real da
impressora, confirmação reforçada, limite de arquivo e auditoria sanitizada.

O fluxo deve permanecer leve na Raspberry. A listagem inicial não pode baixar
todos os G-codes, thumbnails ou metadados individualmente; enriquecimento e
conteúdo completo são carregados somente para a página ou arquivo solicitado.
