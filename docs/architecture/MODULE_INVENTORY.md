# Inventário De Módulos E Contratos

> Gerado por `scripts/audit_module_boundaries.py`; não editar manualmente.

## Resumo

- módulos Python: 158;
- endpoints HTTP/WebSocket: 341;
- contratos tipados: 358;
- tabelas declaradas em SQL: 127;
- ciclos de import detectados: 0.

## Fronteiras E Owners

| Fronteira | Owner | Responsabilidade | Módulos | Tabelas |
|---|---|---|---:|---:|
| `identity` | Identidade e permissões | Autenticação, sessão, organizações, autorização e auditoria de acesso. | 10 | 8 |
| `community` | Comunidade e projetos | Catálogo social, projetos, biblioteca, descoberta, moderação e perfis públicos. | 29 | 45 |
| `finance` | Finanças e pedidos | Ledger, pedidos, pagamentos, reconciliação, risco e repasses. | 10 | 14 |
| `operations` | Operação e agentes | Impressoras, agentes, impressão, calibração, manutenção, setup e firmware. | 55 | 32 |
| `administration` | Administração | Saúde, configuração, backup, relatórios, releases, suporte e operação do produto. | 26 | 28 |
| `integrations` | Integrações | Adapters de Moonraker, descoberta, plugins e dependências externas. | 7 | 0 |
| `shared` | Plataforma | Bootstrap e persistência transversal durante a extração. | 21 | 0 |

## Arquivos Críticos

| Módulo | Owner | Linhas | Rotas | Contratos |
|---|---|---:|---:|---:|
| `social_catalog` | `community` | 3377 | 0 | 0 |
| `operation` | `operations` | 1153 | 0 | 0 |
| `maintenance` | `operations` | 1147 | 0 | 8 |
| `routes.social_catalog` | `community` | 1119 | 59 | 0 |
| `print_projects` | `community` | 1059 | 0 | 14 |
| `self_update` | `administration` | 1001 | 0 | 10 |
| `agent_pairing` | `operations` | 917 | 0 | 0 |
| `auth` | `identity` | 911 | 0 | 0 |
| `calibration` | `operations` | 910 | 0 | 12 |
| `routes.operation` | `operations` | 776 | 13 | 0 |
| `modules.platform.durable_execution` | `shared` | 763 | 0 | 1 |
| `setup_flash` | `operations` | 753 | 0 | 7 |
| `search_discovery` | `community` | 733 | 0 | 5 |
| `setup_can` | `operations` | 699 | 0 | 7 |
| `routes.agents` | `operations` | 693 | 35 | 0 |
| `slicing_pipeline` | `operations` | 680 | 0 | 5 |
| `routes.calibration` | `operations` | 674 | 15 | 0 |
| `setup_wizard` | `operations` | 643 | 0 | 7 |
| `printers` | `operations` | 635 | 0 | 3 |
| `database` | `shared` | 561 | 0 | 0 |
| `gcode_files` | `operations` | 543 | 0 | 10 |
| `health` | `administration` | 513 | 0 | 0 |
| `setup_firmware` | `operations` | 513 | 0 | 5 |
| `setup_final_validation` | `operations` | 509 | 0 | 4 |
| `firmware.repository` | `operations` | 489 | 0 | 0 |
| `agent_support` | `operations` | 486 | 0 | 5 |
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
