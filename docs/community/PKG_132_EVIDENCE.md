# Fluxo ponta a ponta de impressão — evidências

## Resultado

O fluxo diário em `Projetos de impressão > Meus projetos` agora conduz uma
pessoa da seleção até a reimpressão. A seleção congela projeto, versão, arquivos,
quantidades, impressora, material e revisão executável do perfil. Alterações
posteriores não mudam o preparo já criado.

O G-code concluído pode ser aberto no visualizador existente. A aprovação humana
grava data e checksum; o preflight de projeto bloqueia quando não há aprovação ou
quando o artefato mudou. O preflight local/remoto, confirmação para iniciar,
entrega pelo agente, rollback seguro, histórico sanitizado e feedback continuam
usando os contratos canônicos já existentes.

`Reimprimir igual` cria um novo preparo a partir do snapshot imutável original,
incluindo peças, quantidades, impressora, material, perfil e checksum do perfil.
O novo G-code sempre precisa ser gerado, revisto e aprovado novamente.

## Segurança e compatibilidade

- G-code só é lido pelo dono do job e com `Cache-Control: private, no-store`.
- O caminho do artefato permanece confinado ao diretório de dados.
- Preflight revalida vínculo de impressora, checksum e estado/revisão do spool.
- Rotas anteriores permanecem compatíveis; campos novos são opcionais para N-1.
- Retry HTTP continua sob a camada idempotente e a entrega mantém unicidade por
  preflight ativo, evitando duplicação de arquivo/comando.
- Administração permanece como fallback técnico; rollback não apaga histórico.

## Banco e rollback

Aplicação em ordem:

1. SQLite: `backend/sql/091_print_journey.sql`;
2. PostgreSQL: `backend/sql/postgresql/023_print_journey.sql`;
3. validar colunas de aprovação e origem de reimpressão;
4. habilitar a superfície somente após aplicação e smoke.

Os scripts são aditivos. A release N-1 ignora os campos. Para rollback lógico,
retire as novas ações da UI e preserve jobs, G-code, entregas e histórico. Não
execute `DROP`, `DELETE` ou reversão física sem backup e confirmação.

## Validação exigida

- testes de pipeline, preflight, entrega, histórico e versionamento do schema;
- contrato OpenAPI e inventário de módulos sem divergência;
- build e orçamento de bundle;
- desktop e mobile sem overflow, com teclado e linguagem simples;
- smoke seguro até `save_only`; impressão física somente com operador presente,
  material conhecido, confirmação explícita e observação da primeira camada;
- `./check.sh` integral antes do commit.
