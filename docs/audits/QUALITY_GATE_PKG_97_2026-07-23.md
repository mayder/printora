# Evidência Do Gate De Qualidade

Data de início: 2026-07-23
Pacote: PKG-97
Estado: em implementação

## Toolchain

- Node fixado em `22.22.x`, com `.node-version`, `.nvmrc`, `engines` e CI
  convergindo para `22.22.0`;
- npm fixado em `11.7.x`, com `packageManager`, `engine-strict` e CI convergindo
  para `11.7.0`;
- o gate roda no início de `check.sh`, no `preinstall` e no `prebuild`;
- Node `18.20.8`, `20.20.0`, `22.21.9`, `22.23.0` e `23.0.0` foram rejeitados;
- Node `22.22.0` e `22.22.9` foram aceitos;
- o Dockerfile usa imagem Node `22.22.0` e instalação limpa por `npm ci`.

## Build Reproduzível E Bundle

- instalação limpa usa `npm ci` no CI e no Docker;
- dois builds consecutivos produziram o mesmo manifesto SHA-256;
- dependências frontend passaram em `npm audit` sem vulnerabilidade conhecida;
- React e ícones foram separados do entrypoint por chunks estáveis;
- baseline bloqueante: asset individual 1.850.000 bytes, entrada 710.000 bytes,
  stylesheet 260.000 bytes, total 3.400.000 bytes e total gzip 830.000 bytes;
- medição atual: 3.362.437 bytes totais e 824.627 bytes gzip; entrada principal
  697.320 bytes e viewer G-code sob demanda 1.825.250 bytes;
- o build falha quando qualquer orçamento é excedido; o warning genérico de
  500 kB foi substituído por limites explícitos, testados e adequados aos chunks.

## Baseline Real De Cobertura

O baseline inclui código não exercitado e não exclui telas, hooks, serviços ou
regras para elevar artificialmente o percentual. Arquivos apenas de tipos e
declarações sem runtime são as únicas exclusões frontend.

| Módulo | Cobertura global | Cobertura crítica |
| --- | ---: | ---: |
| Backend Python | 79,25% de linhas | 84,58% de linhas |
| Agente Go | 53,3% de statements | 54,8% no pacote operacional |
| Frontend | 1,74% de linhas | 89,20% nas fronteiras P0 selecionadas |

- backend: 569 testes, medidos por `pytest-cov`;
- agente: `go test -coverprofile` sobre todos os pacotes;
- frontend: nove testes Vitest em três arquivos, com Istanbul sobre todos os
  `.ts`/`.tsx`, inclusive arquivos nunca importados;
- fronteiras frontend P0 medidas: cliente HTTP/autorização, cálculo de preview
  G-code e polling sequencial;
- a cobertura frontend global baixa é dívida real visível; não foi ocultada por
  filtro de diretórios.

## Evidência Pendente

- limiares e não regressão bloqueantes;
- E2E, acessibilidade e falhas de rede;
- property/fuzz e mutation;
- pentest independente e reteste;
- gate completo, CI, publicação e auditoria final.
