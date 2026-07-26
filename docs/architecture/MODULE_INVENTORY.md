# Inventário De Módulos E Contratos

> Gerado por `scripts/audit_module_boundaries.py`; não editar manualmente.

## Resumo

- módulos Python: 186;
- endpoints HTTP/WebSocket: 381;
- contratos tipados: 396;
- tabelas declaradas em SQL: 157;
- ciclos de import detectados: 0.

## Fronteiras E Owners

| Fronteira | Owner | Responsabilidade | Módulos | Tabelas |
|---|---|---|---:|---:|
| `accessibility` | Acessibilidade | Preferências acessíveis, semântica, alternativas e contrato compartilhado. | 7 | 1 |
| `design_system` | Design system | Tokens, componentes, estados e contratos visuais compartilhados. | 5 | 0 |
| `identity` | Identidade e permissões | Autenticação, sessão, organizações, autorização e auditoria de acesso. | 13 | 8 |
| `community` | Comunidade e projetos | Catálogo social, projetos, biblioteca, descoberta, moderação e perfis públicos. | 29 | 45 |
| `finance` | Finanças e pedidos | Ledger, pedidos, pagamentos, reconciliação, risco e repasses. | 13 | 20 |
| `operations` | Operação e agentes | Impressoras, agentes, impressão, calibração, manutenção, setup e firmware. | 59 | 44 |
| `administration` | Administração | Saúde, configuração, backup, relatórios, releases, suporte e operação do produto. | 31 | 39 |
| `integrations` | Integrações | Adapters de Moonraker, descoberta, plugins e dependências externas. | 7 | 0 |
| `shared` | Plataforma | Bootstrap e persistência transversal durante a extração. | 22 | 0 |

## Arquivos Críticos

| Módulo | Owner | Linhas | Rotas | Contratos |
|---|---|---:|---:|---:|
| `social_catalog` | `community` | 3402 | 0 | 0 |
| `operation` | `operations` | 1158 | 0 | 0 |
| `routes.operation` | `operations` | 1153 | 16 | 0 |
| `maintenance` | `operations` | 1147 | 0 | 8 |
| `routes.social_catalog` | `community` | 1120 | 59 | 0 |
| `print_projects` | `community` | 1064 | 0 | 14 |
| `self_update` | `administration` | 1007 | 0 | 10 |
| `agent_pairing` | `operations` | 997 | 0 | 0 |
| `auth` | `identity` | 913 | 0 | 0 |
| `calibration` | `operations` | 910 | 0 | 12 |
| `routes.agents` | `operations` | 776 | 38 | 0 |
| `modules.platform.durable_execution` | `shared` | 763 | 0 | 1 |
| `setup_flash` | `operations` | 753 | 0 | 7 |
| `search_discovery` | `community` | 733 | 0 | 5 |
| `setup_can` | `operations` | 699 | 0 | 7 |
| `slicing_pipeline` | `operations` | 680 | 0 | 5 |
| `routes.calibration` | `operations` | 674 | 15 | 0 |
| `modules.administration.intelligence` | `administration` | 673 | 0 | 0 |
| `agent_support` | `operations` | 655 | 0 | 5 |
| `setup_wizard` | `operations` | 643 | 0 | 7 |
| `printers` | `operations` | 635 | 0 | 3 |
| `database` | `shared` | 591 | 0 | 0 |
| `gcode_files` | `operations` | 574 | 0 | 11 |
| `health` | `administration` | 513 | 0 | 0 |
| `setup_firmware` | `operations` | 513 | 0 | 5 |
| `setup_final_validation` | `operations` | 509 | 0 | 4 |
| `firmware.repository` | `operations` | 489 | 0 | 0 |
| `firmware_catalog` | `operations` | 478 | 0 | 14 |
| `updates` | `administration` | 465 | 0 | 8 |
| `backups` | `administration` | 431 | 0 | 0 |
| `install_diagnostics` | `administration` | 403 | 0 | 2 |
| `print_profiles` | `community` | 400 | 0 | 5 |

## Ciclos De Import

Nenhum ciclo entre módulos Python foi detectado.

## Contrato De Evolução

- cada módulo possui um único owner;
- API importa application/contract, nunca infrastructure interna de outro módulo;
- domínio e contratos não importam FastAPI, SQLite, PostgreSQL, Redis, storage ou UI;
- adapters cloud e local implementam ports compartilhadas, sem fallback cruzado;
- toda alteração pública preserva compatibilidade N/N-1 ou versiona o contrato;
- arquivos críticos acima do limite devem ser divididos ao serem alterados.
