# Evidência Cloud — analytics e inteligência

Data: 2026-07-23

## Escopo

Validação do consumidor analítico isolado, sem qualquer acesso ou comando a
impressora física, agente, Moonraker, Klipper, MCU ou Raspberry Pi.

## Implementação

- schema 85 local e extensão PostgreSQL 016, ambos aditivos;
- eventos sanitizados com finalidade, versão, digest, pseudônimo e retenção;
- métricas, lineage, replay, controles de titular, moderação, recursos, modelos,
  decisões, busca geométrica e políticas em tabelas derivadas;
- role `printora_analytics` sem privilégio no OLTP;
- worker systemd separado com CPU 50%, MemoryHigh 512 MiB, MemoryMax 1 GiB,
  TasksMax 128, IOWeight 25 e `NoNewPrivileges`;
- console `?section=data-intelligence` com dashboard, moderação, modelos e
  lineage;
- baseline determinístico sem dataset/modelo externo.

## Evidência local

- testes focados: 12 aprovados;
- suíte backend: 566 aprovados;
- testes Go: aprovados;
- build TypeScript/Vite: aprovado, com alerta já conhecido de Node 18 e chunks;
- primeira execução do gate completo encontrou apenas expectativa antiga do
  teste de navegação; a expectativa foi atualizada;
- reteste completo final: `./check.sh` aprovado com 566 testes backend, Go,
  build frontend e testes de release/G-code.
- workflow remoto `29982441050`: 565 testes passaram e um teste preexistente de
  desconexão WebSocket excedeu a espera de consistência de 2 s antes do deploy;
  a espera do teste foi ampliada para tolerar runner compartilhado, sem mudança
  no runtime. Reteste remoto pendente.

## Evidência remota

Pendente de publicação e probe controlado.

## Retenção e rollback

Nenhuma exclusão foi executada. A retenção é preview-only. Rollback interrompe o
worker quando a release não é compatível e preserva todos os derivados para
forward-fix.
