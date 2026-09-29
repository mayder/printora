# PKG-104 — Evidência de fechamento

Data: 2026-07-28.

## Entrega

- sessões opacas, revogação individual/coletiva e revogação total após senha;
- MFA com segredo pendente e prova atual antes de reconfiguração;
- step-up por finalidade, curto e de uso único;
- exportação determinística com digest e exclusão lógica idempotente;
- proteção de localização e contatos, retenção de auditoria por 180 dias;
- setup físico restrito a administrador com step-up;
- jobs genéricos limitados a `ping` e `remote_operation_status`;
- checksum e assinatura vinculada a plataforma, versão e protocolo para binários
  novos do agente; releases legadas ficam sem auto-update;
- bloqueio social bidirecional em perfil, feed, discussão, comentário e reação,
  remoção lógica e recurso com restauração;
- rate limit de autenticação incluindo MFA e step-up, com falha fechada;
- flag de rollback `PRINTORA_PLATFORM_PROTECTION_WRITES_ENABLED`.

## Auditoria e remediação

- scan inicial completo: `673a7010-f266-4497-abb7-db8c73482778`;
- cobertura: `1.018/1.018` arquivos, em três lotes independentes;
- triagem: 35 candidatos, 26 reportáveis e nove suprimidos;
- severidade inicial: sete médios, 19 baixos, zero alto ou crítico;
- os 26 achados foram corrigidos em autenticação fail-closed, isolamento de
  recursos, busca/bloqueio social, projeção pública, limites de arquivos e
  metadados, confirmação física, papéis de fabricação e cadeia de atualização;
- os workflows agora exigem host SSH previamente conhecido e instaladores não
  executam resposta remota;
- a interface do Codex Security abriu workspaces vazios repetidamente; por
  decisão do usuário, não foi aberta nova solicitação;
- o estado corrigido foi verificado por testes regressivos, revisão local das
  26 classes de achado, buscas estáticas focadas e pelo gate oficial completo.

## SQL

Ordem:

1. SQLite: `backend/sql/087_platform_protection.sql`;
2. PostgreSQL: `backend/sql/postgresql/019_platform_protection.sql`.

Os scripts são aditivos. Não contêm `DROP`, `DELETE`, cascade ou prune. Criam
solicitações de conta e recursos de moderação com `ON DELETE RESTRICT` e
retenção padrão de 180 dias.

## Validação

- testes focados de proteção, autenticação, operação, entrega, updates,
  backup, fabricação, projetos, moderação, bloqueio e sanitização: aprovados;
- testes Python completos: `673 passed`;
- testes Go: `go test ./...` aprovado;
- frontend Node `22.22.0`: build aprovado em `3.439.719` bytes e `848.958`
  bytes gzip, dentro do orçamento;
- E2E desktop/mobile: `32 passed`;
- property/fuzz: `20 passed`;
- mutação: `70,34%` (`306` mortos, `129` sobreviventes), acima do mínimo
  de `60%`;
- cobertura: Python global `79,2593%`, Python crítica `85,3101%`, Go global
  `56,6000%`, Go crítica `58,1000%`, frontend global `8,6548%` e frontend
  crítica `91,3669%`;
- inventário modular: `187` módulos, `390` rotas, `405` contratos e zero ciclo;
- contrato HTTP: `353` paths, `392` schemas e um websocket;
- `PATH=/Users/brenomayder/.nvm/versions/node/v22.22.0/bin:$PATH
  RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`: aprovado;
- a validação foi exclusivamente local, sem SSH, deploy ou reinício de
  servidor/serviço existente;
- revisão local final de segurança: aprovada, sem achado reportável conhecido;
- revisão final do diff: aprovada, com staging seletivo para excluir alterações
  comunitárias preexistentes;
- commit exclusivo do pacote: preparado após o gate completo.

## Rollback

Desativar somente novas exportações, exclusões e recursos com
`PRINTORA_PLATFORM_PROTECTION_WRITES_ENABLED=false`. Owner: operações.
Expiração máxima da flag: 24 horas; antes disso, corrigir ou restaurar a release
N-1. A flag não revoga sessões, não apaga auditoria e não altera dados
canônicos. Não executar `DROP`, `DELETE`, prune ou restauração de snapshot.
