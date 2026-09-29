# Evidência de fechamento — Materiais, spools e qualidade básica

Data: 2026-08-02.

## Resultado entregue

- inventário local owner-scoped com cadastro, edição por revisão e arquivamento
  lógico;
- Spoolman consultado pelo agente pareado e proxy read-only do Moonraker,
  permanecendo autoridade do inventário externo;
- consumo planejado e confirmado em ledger imutável, com chave idempotente e
  redução atômica única do peso local;
- compatibilidade conservadora por perfil, material, impressora, peso e
  ventilação;
- amostra dimensional/calibração com tolerância e resultado determinístico;
- alertas acionáveis de peso, armazenamento, secagem, ventilação, validade e
  descarte;
- tela global de materiais com lista, detalhe, criação/edição separadas,
  histórico e linguagem orientada a pessoas sem conhecimento técnico.

## Fronteiras verificadas

- o cloud não conecta diretamente a endereço privado do Spoolman;
- spool importado não é editável no Printora;
- ausência de evidência não vira compatibilidade positiva;
- falha do Spoolman não impede inventário local;
- nenhum fluxo inicia impressão, aquece, movimenta ou altera configuração;
- UI não expõe nomes internos de pacote/lote.

## Persistência e rollback

- SQLite: `backend/sql/088_material_inventory.sql`;
- PostgreSQL: `backend/sql/postgresql/020_material_inventory.sql`;
- ordem: aplicar o script do banco alvo antes da release que consome as tabelas;
- scripts são aditivos e reexecutáveis;
- rollback restaura a release N-1 e preserva tabelas, IDs externos, ledger,
  pesos e medidas; não existe rollback destrutivo de dados.

## Evidências de teste

- schema novo inicializado em banco SQLite vazio;
- suíte backend focada cobre CRUD, isolamento, consumo idempotente, peso
  insuficiente, Spoolman e compatibilidade;
- testes Go cobrem status e inventário read-only do Spoolman;
- build TypeScript/Vite aprovado com tela lazy e orçamento mensurado;
- testes unitários cobrem estado vazio e degradação do Spoolman;
- E2E autenticado aprovado em desktop e celular, com Axe e sem overflow;
- inspeção manual aprovada em 1440x900 e 390x844, incluindo lista e detalhe;
- fechamento final exige `./check.sh` integral verde no mesmo snapshot do
  commit.

## Riscos residuais

- sincronização real depende de Spoolman, Moonraker e agente compatíveis na
  impressora escolhida;
- peso sem balança é informado ou derivado pelo sistema canônico e pode divergir
  do físico;
- alertas são orientações e não substituem ficha técnica, ventilação adequada
  ou validação física do material.
