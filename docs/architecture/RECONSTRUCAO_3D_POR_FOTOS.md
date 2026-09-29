# Reconstrução 3D Por Fotos

## Objetivo

Definir a arquitetura, os limites de produto e a validação necessários para o
Printora transformar múltiplas fotos de um objeto em um artefato 3D revisado,
baixável em STL/3MF e opcionalmente encaminhado ao fatiamento.

Este documento governa `PKG-141`, `PKG-153` e `PKG-154`. Ele não autoriza
implementação fora dos lotes, não escolhe fornecedor antes do benchmark e não
promete réplica dimensional apenas por qualidade visual.

## Problema E Hipótese

Problema: criar um modelo imprimível a partir de um objeto físico exige captura,
fotogrametria, ferramentas de malha e conhecimento que a maioria dos usuários
do Printora não possui.

Hipótese: um fluxo guiado que rejeite captura ruim antes do processamento,
preserve escala/provenance e exija revisão humana pode gerar modelos úteis para
objetos decorativos e orgânicos, com custo e taxa de conclusão mensuráveis.

Não é hipótese aprovada que fotos comuns substituam metrologia ou CAD para
roscas, encaixes, superfícies de vedação, tolerâncias ou peças de segurança.

## Resultado Mensurável

O piloto deve medir, por classe de objeto:

- sessões iniciadas, concluídas, rejeitadas e abandonadas;
- reconstruções concluídas, falhas e retomadas;
- cobertura observada e proporção inferida/reparada;
- erro dimensional por eixo quando houver referência confiável;
- validade de malha, watertight, componentes, faces e espessura mínima;
- tempo de fila, processamento e revisão;
- consumo de CPU/GPU/storage, egress e custo externo por resultado aprovado;
- download, fatiamento, impressão física e resultado informado pelo usuário;
- incidentes de privacidade, isolamento, abuso ou cobrança duplicada.

Metas numéricas só serão fixadas após o benchmark inicial. Avaliação visual
isolada não fecha pacote nem homologa engine.

## Fluxo Canônico

```text
Projeto privado
  -> sessão de captura
  -> fotos em quarentena
  -> qualidade e cobertura
  -> escala e aprovação da captura
  -> job assíncrono de reconstrução
  -> malha bruta + provenance
  -> qualificação geométrica
  -> reparos versionados
  -> revisão humana
  -> snapshot aprovado
  -> STL/3MF ou job de fatiamento
```

Cada seta representa estado persistido e idempotente. Nenhuma etapa publica,
cobra novamente, fatia ou envia à impressora por inferência implícita.

## Arquitetura

### Fronteiras

- `community/project_assets`: owner, projeto, sessão, fotos, snapshots,
  manifestos, arquivos e permissões.
- `operations`: job, tentativa, worker, cancelamento, quota, custo, artefatos e
  integração com fatiamento.
- `integrations`: adapters de engine próprio ou provedor externo, autenticação,
  timeout, circuit breaker, webhook/polling e normalização de resposta.
- `frontend/projects`: captura guiada, progresso, preview, relatório, revisão,
  download e encaminhamento explícito ao fatiamento.
- agente da impressora: fora do processamento; não recebe fotos nem executa
  GPU, fotogrametria ou reparo de malha.

### Contratos Principais

- `CaptureSession`: owner, projeto, estado, protocolo, escala, retenção e fotos.
- `CapturePhoto`: checksum, formato, dimensões, orientação, qualidade,
  quarentena e storage key privada.
- `ReconstructionJob`: captura aprovada, idempotency key, engine policy, estado,
  tentativas, custo, cancelamento e correlação.
- `ReconstructionArtifact`: tipo, checksum, unidade, engine/modelo/versão,
  parâmetros, fontes e mapa de observação/inferência.
- `MeshQualification`: invariantes, medidas, bloqueios, avisos e resultado.
- `MeshRevision`: operação reversível, parent, parâmetros, checksum e autor.
- `HumanReview`: aceite/rejeição, limitações reconhecidas e dimensões críticas.

Payload público não expõe storage key, URL assinada expirada, credencial,
parâmetro sensível do provedor ou foto de outro owner.

## Estratégia De Reconstrução

Fotogrametria multiview é a fonte geométrica preferida para objetos reais. O
pipeline recupera poses, nuvem esparsa/densa e superfície a partir das imagens.
IA pode auxiliar segmentação, avaliação de captura, seleção de parâmetros ou
preenchimento marcado, mas não transforma região não observada em fato.

Os primeiros candidatos técnicos são:

- COLMAP para Structure-from-Motion, Multi-View Stereo, nuvem densa e superfície;
- AliceVision/Meshroom como pipeline aberto alternativo;
- provedor externo multiview apenas atrás de adapter, após avaliação de termos,
  privacidade, região de dados, custo, retenção, disponibilidade e exportação;
- Open3D ou biblioteca equivalente para checagens determinísticas de malha,
  incluindo watertight, sem torná-la regra de domínio acoplada à biblioteca.

Nenhum candidato é obrigatório antes do lote de benchmark. Versão, licença,
SBOM, GPU suportada e qualidade N/N-1 devem ser fixadas quando houver escolha.

## Build Versus Buy

O benchmark deve executar o mesmo conjunto controlado em pelo menos um pipeline
próprio e um provider externo elegível, comparando:

| Critério | Pipeline próprio | Provedor externo |
|---|---|---|
| Qualidade e repetibilidade | Medir | Medir |
| Latência e fila | Medir com GPU alvo | Medir API e egress |
| Custo por aprovado | Infra, energia e operação | Chamada, storage e egress |
| Privacidade e retenção | Controle interno | Contrato e região do fornecedor |
| Lock-in e exportação | Baixo se formato aberto | Validar contrato e saída |
| Manutenção | Dependências, drivers e worker | Versões, quota e mudanças de API |
| Degradação | Fila própria limitada | Circuit breaker e modo indisponível |

A escolha pode ser híbrida. O domínio não conhece nome de fornecedor e a troca
de adapter não altera projeto, captura, review ou artefato já aprovado.

## Qualificação Para Impressão

A malha bruta nunca recebe automaticamente o estado `imprimível`. A
qualificação deve verificar, dentro de limites de recurso:

- unidade, escala, bounding box e dimensão conhecida;
- manifold, watertight, normais e componentes desconectados;
- faces degeneradas, auto-interseções, buracos e regiões ausentes;
- espessura mínima e detalhes menores que a capacidade informada;
- alterações de reparo, áreas inferidas e perdas por simplificação;
- compatibilidade básica com volume da impressora e fluxo de preflight.

Classe decorativa pode aceitar avisos após revisão. Classe mecânica exige
dimensões críticas, incerteza explícita e validação física; o Printora não
garante tolerância funcional.

## Segurança, Privacidade E Abuso

- privado por padrão e deny-by-default em todos os recursos filhos;
- upload com assinatura, limites, quarentena, checksum e proteção contra ZIP ou
  parser bomb quando houver pacote;
- EXIF desnecessário removido; localização não integra o contrato canônico;
- URL de entrada/saída do provider não é aceita livremente do cliente; egress
  usa allowlist e proteção SSRF;
- webhook autenticado, replay negado, corpo limitado e reconciliação pela fonte;
- credenciais em secret store, rotacionáveis e fora de release/log;
- quota por owner/organização, limite de concorrência e proteção contra custo;
- fotos não alimentam treinamento sem consentimento específico e revogável;
- retenção distinta para rascunho, fonte, intermediário, resultado e auditoria;
- nenhuma exclusão física automática antes da política, janela e autorização
  definidas; rollback preserva objetos canônicos.

## Observabilidade E Custo

Usar correlação de captura, job e tentativa sem nomes de arquivo, fotos ou
payloads sensíveis. Medir fila, estágio, duração, erro normalizado, engine,
versão, consumo, custo estimado e resultado. Auditoria registra mutações e
revisão humana. Retenção segue os padrões do projeto e requer cleanup testado.

Alertas mínimos: fila parada, taxa de falha, custo anômalo, webhook inválido,
quota, storage, worker sem heartbeat e divergência entre estado local/provider.

## Rollback E Degradação

- flags separadas para captura, cada adapter, reparo assistido, exportação e
  entrada no fatiamento;
- provider indisponível não afeta projeto, upload, viewer ou fatiamento comum;
- N-1 lê sessões, jobs, artefatos e snapshots criados por N;
- job iniciado termina, cancela ou entra em reconciliação; não é abandonado em
  estado ambíguo durante deploy;
- rollback nunca remove foto, malha, snapshot, manifesto ou review;
- troca de engine cria nova tentativa/artefato, sem sobrescrever o anterior.

## Evidência De Fechamento

- benchmark versionado e reproduzível, sem dados reais de produção;
- testes unitários, domínio, SQL, adapter, worker, API, permissão, segurança,
  frontend, acessibilidade, carga e compatibilidade N/N-1;
- revisão visual em desktop/mobile e fluxo retomado após falha de rede;
- impressão física controlada e medidas com instrumento identificado;
- custos e classes suportadas/não suportadas publicados sem promessa indevida;
- threat model, retenção, incidente, canário e rollback ensaiado;
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh` verde.

## Fontes Técnicas Primárias

- COLMAP tutorial: <https://colmap.github.io/tutorial.html>
- AliceVision: <https://alicevision.org/>
- Meshroom documentation: <https://meshroom.readthedocs.io/en/stable/>
- Open3D mesh checks: <https://www.open3d.org/docs/latest/tutorial/Basic/mesh.html>
- Tripo multiview API, apenas como candidato de benchmark:
  <https://developers.tripo3d.ai/en/docs/generation-multiview-to-model/standard>
