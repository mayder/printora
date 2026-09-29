# Inventário Histórico E Portfólio Ativo

Este diretório preserva o inventário de ideias comunitárias e governa o
portfólio ativo enxuto. Inventário não é backlog nem autorização de
implementação.

## Escopo histórico e números

- 55 frentes inventariadas;
- 440 capacidades hipotéticas;
- 3.080 melhorias atômicas rastreáveis;
- 440 famílias de tela;
- 1.320 estados principais de lista, detalhe e cadastro/edição;
- prioridades históricas P0 a P4 por impacto social;
- comparação com redes sociais, comunidades de criadores, repositórios 3D, slicers e interfaces de impressão.

## Arquivos

- `../../DEMANDAS.md`: somente pacotes executáveis ativos, com dependências
  técnicas explícitas.
- `../../DEMANDAS_CONSOLIDADAS_PKG_01_100.md`: histórico integral dos pacotes
  consolidados anteriores ao programa comunitário.
- `MASTER_PLAN.md`: visão, diagnóstico atual, método, arquitetura e fases.
- `PLATFORM_BENCHMARK.md`: comparação de plataformas e padrões a absorver ou evitar.
- `COMMUNITY_BACKLOG.md`: inventário histórico de possibilidades, não backlog.
- `COMMUNITY_BACKLOG.csv`: versão filtrável e importável do inventário.
- `COMMUNITY_SCREENS.md`: catálogo histórico de telas hipotéticas.
- `COMMUNITY_SCREENS.csv`: versão filtrável das telas.
- `PRIORITIES.md`: priorização histórica do inventário de ideias.
- `SUMMARY.json`: contagem verificável do inventário.
- `PACKAGE_PORTFOLIO.csv`: estado e decisão dos IDs `PKG-101` a `PKG-155`.
- `PACKAGE_ARCHITECTURE.csv`: owner, colaboradores, área, risco e dependências
  dos pacotes ativos.
- `PACKAGE_EXECUTION_STANDARD.md`: padrão bloqueante de modelagem,
  implementação, testes, rollout e fechamento.
- `PACKAGE_MODELING_REVIEW.md`: revisão transversal, brechas tratadas e riscos
  residuais que não podem ser eliminados por documentação.

## Regra de uso

O inventário é um mapa de possibilidades, não autorização para implementar tudo sem descoberta. Antes de iniciar uma frente:

1. validar o problema com pessoas afetadas;
2. auditar novamente o que já existe no Printora;
3. confirmar status `active` em `PACKAGE_PORTFOLIO.csv`;
4. consultar owner, colaboradores, risco e dependências em
   `PACKAGE_ARCHITECTURE.csv`;
5. cumprir a Definition of Ready de `PACKAGE_EXECUTION_STANDARD.md`;
6. definir telas em `TELAS.md`, testes em `TESTES.md` e decisões relevantes em `DECISOES.md`;
7. pilotar com métricas de benefício e dano;
8. expandir somente quando o resultado justificar o custo e o risco.

Itens cancelados, fundidos ou adiados não podem voltar por referência ao
inventário gerado. Precisam de nova decisão de produto e atualização explícita
do portfólio.

Os arquivos gerados são reproduzíveis com:

```bash
python3 scripts/generate_community_roadmap.py
```
