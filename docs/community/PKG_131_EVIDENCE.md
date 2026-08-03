# Evidência de fechamento — fatiamento avançado e perfis reproduzíveis

## Resultado

O Printora passa a manter um perfil executável privado como um conjunto nativo
do OrcaSlicer: impressora, processo e filamento. Cada importação válida gera uma
revisão imutável com representação canônica e SHA-256. Um trabalho de fatiamento
grava a revisão, a versão da engine, o checksum e o snapshot canônico usados,
portanto uma atualização posterior do perfil não altera trabalhos antigos.

Na área **Meus projetos**, a pessoa pode:

- importar um JSON com os três perfis sem precisar conhecer o schema interno;
- criar um perfil novo ou adicionar uma versão a um perfil existente;
- comparar as duas versões mais recentes por quantidade de campos adicionados,
  alterados e removidos;
- baixar uma cópia nativa;
- escolher um perfil reproduzível ao criar o trabalho de fatiamento.

A interface usa nomes humanos e mantém checksum e número da versão apenas como
evidência secundária. O perfil social resumido continua informativo e não vira
autoridade executável.

## Persistência e ordem SQL

1. SQLite: `backend/sql/090_slicing_profile_bundles.sql`.
2. PostgreSQL: `backend/sql/postgresql/022_slicing_profile_bundles.sql`.

Os scripts adicionam bundles, revisões e vínculos opcionais em `slicing_jobs`.
Não removem nem reescrevem jobs, perfis sociais ou artefatos existentes. O
versionador registra cada script uma única vez; PostgreSQL usa adições
idempotentes.

## Segurança, privacidade e observabilidade

- bundles pertencem ao usuário autenticado e não podem ser enumerados por outro
  usuário;
- importação limita payload a 2 MiB, profundidade, quantidade e tamanho de
  campos;
- chaves operacionais e valores com credenciais, host privado, URL local ou path
  pessoal são rejeitados;
- campos desconhecidos permitidos são preservados, evitando perda silenciosa;
- o job persiste somente conteúdo sanitizado, versão e checksum;
- não há nova tabela de logs; diagnóstico usa os registros existentes do job.

## Validação

- round-trip N/N-1, preservação de campo desconhecido e importação idempotente;
- fixture controlada no formato nativo do OrcaSlicer;
- revisão, herança, override, diff e isolamento por owner;
- rejeição de conteúdo operacional sensível sem falso positivo em termos
  comuns do fatiador;
- trabalho de fatiamento preso à revisão original após nova versão;
- teste de UI para linguagem simples e comparação;
- build TypeScript/Vite e orçamento do bundle;
- contrato OpenAPI, inventários e gate completo do repositório no fechamento.

Os perfis locais homologados incluem 14 finalidades para a Voron 2.4 com bico
de 0,6 mm e os 14 equivalentes para a Voron 0.2 com bico de 0,4 mm. O teste
compara cada perfil V02 com sua derivação V24, garante largura mínima de 0,4 mm
e compatibilidade explícita com a impressora correta. O instalador valida por
padrão sem alterar arquivos; `--apply` exige configuração Orca válida, rejeita
endereço com credencial e cria backup antes de instalar.

## Rollback

Reverter as rotas e consumidores de perfis executáveis e manter as tabelas e
colunas em leitura somente. Novos trabalhos podem continuar sem revisão
executável ou ser bloqueados por configuração, sem apagar bundles ou revisões.
Se for indispensável remover o schema após aplicação, restaurar backup validado;
não executar `DROP` ou `DELETE` manual.
