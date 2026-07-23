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
  o workflow `29982767486` confirmou que o runner cancela o fechamento implícito
  do client sem entregar a desconexão ao servidor. O teste passou a fechar o
  WebSocket explicitamente, como faz o agente real, sem mudança no runtime.
  Reteste remoto pendente.

## Evidência remota

- workflow `29983090499`: release `1636411` publicada com gate, dependências,
  SBOM, preflight, blue/green e endpoint público aprovados;
- três processos web ready no schema 86; role comprovada com update em derivados
  e sem select/update em `auth_users`;
- unit isolada instalada e ativa com CPU 50%, MemoryHigh 512 MiB, MemoryMax
  1 GiB, TasksMax 128 e IOWeight 25;
- 600 leituras simultâneas de readiness: zero erro, máximo 83 ms;
- a primeira carga real encontrou conversão de `CURRENT_TIMESTAMP` para texto no
  adapter PostgreSQL. A transação reverteu sem dado parcial; todos os timestamps
  do serviço passaram a usar parâmetros ISO;
- workflow `29983809937`: release `8457aac` publicada com sucesso;
- carga de 1.004 eventos processada; 600 readiness simultâneas tiveram zero erro
  e máximo 75 ms. O replay global revelou que a minimização de moderação removia
  features necessárias à reprodução. O evento agora preserva somente idioma,
  rótulos, confiança, flag humana e digests, sem texto, e o digest original
  continua imutável para deduplicação;
- workflow `29984464479`: release `734de42` publicada com gate completo,
  auditorias de dependência, SBOM, preflight, blue/green e smoke público;
- probe final: 1.004 eventos em 54,4 s (18,456 eventos/s), replay de 2.000
  eventos com 2.000 resultados invariantes, anonimização somente em derivados,
  PT/EN/ES com revisão humana e fallback determinístico exercitado;
- role final: acesso de atualização em derivados, sem leitura ou escrita em
  `auth_users`; nenhum registro temporário e nenhuma exclusão de retenção;
- worker ativo com cerca de 34 MiB, CPU 50%, MemoryHigh 512 MiB, MemoryMax
  1 GiB, TasksMax 128 e IOWeight 25;
- 600 leituras concorrentes nas duas instâncias: zero erro e máximo 77 ms;
- navegador real abriu `?section=data-intelligence` sem erro de console, mas a
  sessão disponível estava desautenticada e exibiu o login. A inspeção visual
  interna não foi alegada; contrato, testes e probe autenticado são a evidência
  funcional do painel.

## Retenção e rollback

Nenhuma exclusão foi executada. A retenção é preview-only. Rollback interrompe o
worker quando a release não é compatível e preserva todos os derivados para
forward-fix.
