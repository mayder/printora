# PKG-128 — Evidência de fechamento

## Resultado

O projeto de impressão permanece a raiz do conteúdo. Cada upload hospedado pode
ser nomeado como peça, associado a uma montagem e a uma variação, inspecionado
sem executar o conteúdo e congelado em um manifesto canônico com SHA-256.

## Invariantes

- somente o dono altera a estrutura de arquivos de um projeto;
- projeto público aprovado pode ser baixado por usuário autenticado, sem expor
  chave de storage;
- arquivo rejeitado ou em quarentena nunca entra no bundle;
- upload repetido pela mesma chave ou pela mesma assinatura
  projeto/nome/função/checksum retorna o estado existente e não cria versão;
- snapshot anterior, arquivo canônico e checksum permanecem imutáveis;
- inspeção é informativa e nunca envia, fatia, publica ou altera a malha;
- ZIP recebe fallback limitado; STL e 3MF são analisados com limites explícitos;
- cota considera em conjunto biblioteca social e arquivos de projeto ativos.

## Fluxo de estados

`upload -> quarantined -> validated -> inspection ready|limited|failed`.

Falha de inspeção não muda um arquivo validado para aprovado geometricamente.
Ela bloqueia somente a prévia/análise e mantém os demais arquivos navegáveis.
Referência externa fica `metadata_only/not_applicable` e não é fatiável.

## Segurança e capacidade

- upload individual: 25 MB;
- inspeção: até 500.000 triângulos;
- preview: amostra determinística de até 600 triângulos;
- 3MF: até 100 entradas e 50 MB descompactados durante inspeção;
- bundle: até 250 MB de arquivos validados, gerado em arquivo temporário e
  removido após a resposta;
- download individual continua usando token curto, de uso único e autorização
  no backend;
- nomes do ZIP são sanitizados e colisões recebem sufixo determinístico;
- nenhum token, path, bucket ou payload bruto entra no manifesto público.

## Banco e compatibilidade

Aplicar, na ordem:

1. SQLite: `backend/sql/089_project_assets.sql` pelo versionador normal;
2. PostgreSQL: `backend/sql/postgresql/021_project_assets.sql` pelo fluxo
   privilegiado documentado, antes de habilitar a versão cloud.

Os scripts são aditivos. A aplicação N-1 ignora as novas colunas e continua
lendo projetos, arquivos e versões existentes. O rollback desativa a nova UI e
restaura a release N-1, preservando schema e objetos. Para reversão física do
SQLite, usar o backup automático anterior ao script; não executar `DROP`,
`DELETE` ou limpeza de objetos.

## Superfície humana

No detalhe do projeto, `Peças e inspeção` mostra nome, grupo, variação, medidas,
triângulos e avisos em texto. `Ver forma em 3D` é progressivo, permite girar,
simular corte e tamanho e declara que a simulação não altera o arquivo. Sem a
prévia, as mesmas informações essenciais permanecem disponíveis. Em `Meus
projetos`, `Organizar peças` usa rótulos cotidianos e formulário separado do
upload e da persistência.

## Validação

Validação executada:

```bash
backend/.venv/bin/python -m pytest -q backend/tests/test_project_assets.py backend/tests/test_print_projects.py backend/tests/test_schema_versioning.py
PATH=/Users/brenomayder/.nvm/versions/node/v22.22.0/bin:$PATH npm --prefix frontend run build
PATH=/Users/brenomayder/.nvm/versions/node/v22.22.0/bin:$PATH npm --prefix frontend run test:unit -- tests/unit/ProjectAssetsPanel.test.ts
./check.sh
```

Os testes focados do backend passaram com 39 casos e o painel passou com três
casos, incluindo compatibilidade com resposta N-1 sem inspeção. O build respeitou
o orçamento de bundle. O `./check.sh` completo passou com E2E desktop/mobile,
property/fuzz, mutação, cobertura, contratos, arquitetura e dependências do
portfólio.

Na validação manual foi criado um projeto privado, enviado um STL sintético de
10 × 10 × 10 mm, conferidas medidas, aviso, malha progressiva, giro, corte,
simulação de escala e organização em peça/montagem/variação. O mesmo fluxo foi
revisto em viewport móvel de 390 × 844, sem perda de informação essencial ou
ação crítica.
