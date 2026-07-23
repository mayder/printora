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
| Backend Python | 79,41% de linhas | 85,04% de linhas |
| Agente Go | 53,3% de statements | 54,8% no pacote operacional |
| Frontend | 1,80% de linhas | 91,36% nas fronteiras P0 selecionadas |

- backend: 596 testes, medidos por `pytest-cov`;
- agente: `go test -coverprofile` sobre todos os pacotes;
- frontend: 11 testes Vitest em três arquivos, com Istanbul sobre todos os
  `.ts`/`.tsx`, inclusive arquivos nunca importados;
- fronteiras frontend P0 medidas: cliente HTTP/autorização, cálculo de preview
  G-code e polling sequencial;
- a cobertura frontend global baixa é dívida real visível; não foi ocultada por
  filtro de diretórios.

## Gate De Cobertura

- `scripts/run-coverage-gate.sh` executa as três stacks e falha abaixo do mínimo
  ou do baseline versionado em `quality/coverage-baseline.json`;
- `PATHS.toml` habilita cobertura e registra os limiares por stack e criticidade;
- Python exige 79% global e 84% crítico;
- Go exige 53% global e 54% no pacote operacional crítico;
- frontend exige 1,7% global e 89% agregado crítico, além de limites por arquivo
  para HTTP, preview G-code e polling sequencial;
- o workflow publica JSON, LCOV e perfis Go em artefato com retenção de 30 dias,
  inclusive quando o gate falhar;
- queda abaixo do baseline exige decisão e aprovação explícita; reduzir apenas o
  limiar não contorna a comparação de não regressão.
- o novo gate encontrou uma rejeição intermitente da assinatura Ed25519 do
  instalador; a dependência de OpenSSL foi removida e o teste passou 100 vezes;
- o ambiente jsdom recebeu `localStorage` determinístico e a suíte frontend
  passou 30 repetições consecutivas antes do gate completo final.

## E2E Em Navegador Real

- Playwright `1.61.1` executa Chromium com workers serializados e sem retry;
- matriz: desktop Chrome em tema escuro e Pixel 7 em tema claro;
- 20 cenários passaram: anônimo, login/logout, teclado, acessibilidade,
  isolamento de duas organizações, negação de privilégios, comunidade, busca,
  projeto, upload rejeitado/quarentena/promoção, agente pareado com heartbeat,
  administração, financeiro sandbox, fabricação, offline, timeout, `429` e
  `5xx`;
- dados e banco são temporários; emails, organizações, projetos, impressoras,
  agentes e idempotency keys incluem projeto e índice de repetição;
- nenhuma rota P0 usa retry ou quarentena;
- flakiness: os 20 cenários passaram 10 vezes por projeto, totalizando 200
  execuções consecutivas em 3,7 minutos, sem retry;
- Axe não encontrou violação `critical` ou `serious` nas rotas P0 medidas;
- o gate revelou o fallback frontend antes das APIs e três telas administrativas
  comprimidas na primeira coluna. Ambos os defeitos foram corrigidos e
  ganharam regressão automatizada.
- o CI revelou uma corrida entre logout e `/api/auth/me`: a revogação retornava
  `200`, mas uma leitura anterior podia restaurar o usuário na interface. A
  geração local de autenticação agora descarta respostas antigas; 200 execuções
  desktop/mobile passaram depois da correção.

## Property-based E Fuzz

- Hypothesis `6.161.0`, perfil CI determinístico com 200 exemplos e perfil fuzz
  com 1.000 exemplos/seed `970099`;
- 8 properties e regressões determinísticas de porta inválida passaram em ambos
  os perfis sobre URL/SSRF, path G-code, parser de metadata, idempotência e
  assinatura de webhook;
- corpus versionado não contém dado real;
- achados corrigidos: porta URL inválida e path G-code absoluto, NUL,
  URL-encoded ou duplamente encoded com traversal.

## Mutation Testing

- mutmut `3.6.0` executa quatro domínios críticos;
- resultado: 723 mutantes totais, 312 mortos, 197 sobreviventes, 214 sem teste,
  zero timeout/suspicious/segfault;
- score testado: `312 / (312 + 197) = 61,30%`, acima do mínimo bloqueante de
  `60%` registrado em `PATHS.toml`;
- `stats.json` e `survivors.txt` são publicados no CI. A lista completa dos 197
  sobreviventes fica preservada, sem filtro;
- backlog explícito, cobrindo todos os sobreviventes: Plataforma/idempotência
  79, Pagamentos 54, Identidade 37 e Comunidade/validação 27; owners e prazo
  `PKG-100` estão definidos na `DEC-20260723-07`.

## Gate Integrado

- `scripts/run-pkg97-test-gates.sh` executa E2E, property/fuzz e mutation;
- `PATHS.toml` referencia esse comando como teste da stack;
- cobertura permanece executada separadamente no check para publicar seus
  relatórios e aplicar não regressão;
- CI instala Chromium e publica cobertura, E2E e mutation por 30 dias, inclusive
  em falha.
- a primeira execução remota `30027129656` foi bloqueada pelo scanner estrito
  antes dos testes porque a fixture E2E declarava um valor sintético literal;
  nenhum slot foi preparado ou trocado. A fixture passou a compor o valor em
  runtime, sem credencial real, e ausência de artefato antes do gate gera aviso
  em vez de uma segunda falha que esconda a causa primária;
- a execução corrigida `30027821712` publicou o commit runtime `07e2eb2` em
  `18m45s`: gate completo, build reproduzível, artefatos, auditoria de
  dependências, SBOM, release imutável, preflight, preparação do slot, troca
  com drain e validação pública passaram;
- smoke externo confirmou `/health`, `/ready`, `/api/system/version`, catálogo
  e feed comunitário. O navegador autenticado abriu a Visão geral publicada,
  sem erro visível, com as duas impressoras e os dois agentes online em
  `0.1.34`; nenhuma ação mutável foi enviada às impressoras;
- a execução `30032632953` do commit `d5b3744` foi bloqueada no gate E2E pela
  corrida de logout antes de empacotar, enviar ou trocar qualquer slot;
- a execução corrigida `30034513130` publicou o commit `9f2fcc1` em `24m11s`;
  gate completo, build reproduzível, evidência, auditoria, SBOM, release
  imutável, preflight, preparação independente, troca com drain e smoke público
  passaram;
- smoke externo posterior confirmou `/health`, `/ready`, catálogo e versão
  `0.1.41` com schema `86`. O navegador autenticado mostrou duas impressoras,
  dois agentes online em `0.1.34`, zero alertas e operação `2/2`; nenhuma ação
  mutável foi enviada às impressoras;
- `./check.sh` passou em 2026-07-23 com Node suportado, regras/arquitetura,
  20 E2E, 20 execuções property/fuzz, 723 mutantes, 596 testes Python, cobertura
  Python/Go/frontend, contratos, compileall e testes Go;
- validação visual local em navegador real confirmou Finanças, Fabricação e
  Dados e inteligência com 2.145 px úteis em viewport de 2.461 px, zero overflow
  horizontal e lista/detalhe de Fabricação sem sobreposição.

## Evidência Pendente

- contratação, identificação e assinatura independente do escopo preparado em
  `PENTEST_SCOPE_PKG_97_2026-07-23.md`;
- correção e reteste de achados críticos/altos e tratamento dos médios;
- gate completo final depois do pentest;
- publicação, auditoria e fechamento do pacote.
