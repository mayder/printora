# Evidência Do Monólito Modular

Data: 2026-07-22.

## Fronteiras Entregues

- identidade e permissões;
- comunidade e projetos;
- operação e agentes;
- administração;
- integrações.

O bootstrap HTTP registra os routers por módulo, com owner, versão de contrato e
ordem única. `main.py` não conhece mais cada route individualmente.

## Contratos E Ports

- contratos de identidade, comunidade, operação e administração foram extraídos
  dos repositories e adapters;
- contratos comunitários foram separados por catálogo, comunidade, biblioteca e
  validação para evitar um novo arquivo monolítico;
- ports explícitas cobrem identidade, comunidade, jobs/agentes, backup e
  Moonraker;
- o despacho de jobs do agente virou application service sem FastAPI, banco ou
  UI; o adapter HTTP somente traduz erros de aplicação para status HTTP;
- preferências locais do frontend passaram por um service boundary e o gate de
  layering React ficou bloqueante por padrão.

## Contratos Congelados

- OpenAPI v1: 287 paths e 326 schemas;
- realtime v1: um endpoint WebSocket e schemas de protocolo/agente;
- compatibilidade declarada: `1.x`;
- snapshots determinísticos são verificados em todo `./check.sh`.

## Inventário Executável

`scripts/audit_module_boundaries.py` encontrou:

- 133 módulos Python;
- 322 endpoints HTTP/WebSocket declarados;
- 337 contratos tipados;
- 100 tabelas declaradas em SQL;
- zero ciclo de import.

Cada arquivo e tabela possui owner. O inventário JSON/Markdown é regenerável e o
check falha quando código, rota, contrato ou dependência diverge.

## Compatibilidade E Regressão

- snapshots HTTP/realtime permaneceram idênticos durante as extrações;
- testes direcionados de autenticação, comunidade, backup, agentes e adapters
  passaram;
- o frontend compilou e o scanner estrito confirmou ausência de HTTP/storage
  direto em pages/components;
- nenhum schema, dado, endpoint, payload ou comportamento público foi removido.

## Dívida Controlada

Repositories SQLite locais ainda são arquivos grandes porque serão separados por
adapter durante o cutover do PKG-88. A data limite é 2026-08-31 e o gate final é
o PKG-95, o que ocorrer primeiro. Não há bridge de runtime: contratos e ports são
canônicos, e os repositories atuais são adapters concretos do perfil local/cloud
vigente até a troca de persistência.
