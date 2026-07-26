# Programa Plurianual Da Comunidade Printora

Este diretório é a fonte complementar do backlog para a evolução do Printora como comunidade e ecossistema de fabricação digital.

## Escopo e números

- 55 frentes estratégicas;
- 440 capacidades de produto;
- 3.080 melhorias atômicas rastreáveis;
- 440 famílias de tela;
- 1.320 estados principais de lista, detalhe e cadastro/edição;
- prioridades P0 a P4 ordenadas por impacto social;
- comparação com redes sociais, comunidades de criadores, repositórios 3D, slicers e interfaces de impressão.

## Arquivos

- `../../DEMANDAS.md`: pacotes executáveis `PKG-101` a `PKG-155`, com
  ordem topológica, dependências somente anteriores e rastreabilidade exata
  para todos os IDs `COM`, `CAP` e `SCR`.
- `../../DEMANDAS_CONSOLIDADAS_PKG_01_100.md`: histórico integral dos pacotes
  consolidados anteriores ao programa comunitário.
- `MASTER_PLAN.md`: visão, diagnóstico atual, método, arquitetura e fases.
- `PLATFORM_BENCHMARK.md`: comparação de plataformas e padrões a absorver ou evitar.
- `COMMUNITY_BACKLOG.md`: lista humana de todos os itens atômicos.
- `COMMUNITY_BACKLOG.csv`: versão filtrável e importável do inventário.
- `COMMUNITY_SCREENS.md`: catálogo completo de telas e fluxos planejados.
- `COMMUNITY_SCREENS.csv`: versão filtrável das telas.
- `PRIORITIES.md`: ordenação por impacto social.
- `SUMMARY.json`: contagem verificável do inventário.

## Regra de uso

O inventário é um mapa de possibilidades, não autorização para implementar tudo sem descoberta. Antes de iniciar uma frente:

1. validar o problema com pessoas afetadas;
2. auditar novamente o que já existe no Printora;
3. localizar o pacote e os IDs `COM`, `CAP` e `SCR` atribuídos em
   `DEMANDAS.md`, sem criar pacote paralelo ou sobreposto;
4. definir telas em `TELAS.md`, testes em `TESTES.md` e decisões relevantes em `DECISOES.md`;
5. pilotar com métricas de benefício e dano;
6. expandir somente quando o resultado justificar o custo e o risco.

Os arquivos gerados são reproduzíveis com:

```bash
python3 scripts/generate_community_roadmap.py
```
