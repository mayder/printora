# Evidência parcial — reconstrução 3D por múltiplas fotos

Data: 2026-08-02
Estado: base operacional implementada; pacote permanece ativo.

## Entregue nesta alteração lógica

- job assíncrono vinculado a captura pronta, projeto e proprietário;
- idempotência, limite de jobs ativos, fila `bulk`, retry e correlação;
- tentativas cercadas por identificador ativo para impedir promoção atrasada;
- cancelamento cooperativo do wrapper e estado terminal sem nova tentativa;
- adapters desabilitado, fixture sintética e comando local/provider sob o mesmo
  contrato versionado;
- gateway COLMAP concreto, com denso/Poisson em CUDA e fallback
  esparso/Delaunay explicitamente não qualificado sem CUDA;
- gateway Tripo com quatro vistas médias equidistantes, segredo isolado,
  polling, download HTTPS público e checkpoint privado para não recriar tarefa
  paga em retry;
- checkpoint versionado marca somente conclusões validadas e possui revisão de
  retenção em modo preview por padrão; aplicação supervisionada remove apenas
  checkpoints concluídos e expirados, preservando estados ativos, ambíguos,
  legados, inválidos e bloqueados;
- diretório temporário, executável fixo, shell desativado, ambiente restrito,
  timeout e validação de caminho, symlink, formato, tamanho e proporções;
- circuito após falhas repetidas e falha isolada da reconstrução;
- provenance com engine, adapter, modelo, parâmetros e checksums das fotos;
- artefato privado, com cota, ownership, streaming `no-store` e sem storage key
  no contrato público;
- interface simples no fim da captura, com escolha automática recomendada,
  estágios verdadeiros, saída da tela, cancelamento, retomada e aviso explícito
  de que a malha bruta ainda não está pronta para impressão.

## Proteções de produto

O padrão é `disabled`. A fixture gera geometria sintética marcada como teste e
não informa cobertura observada ou inferida. Nenhum provider é chamado pelo
frontend, nenhuma credencial integra payload ou argumento e o agente da
impressora não recebe fotos ou trabalho pesado. Falha do registro auxiliar de
saúde não transforma reconstrução concluída em retry pago.

## Validação executável

- backend: domínio, worker, adapter, cancelamento, fencing, circuito, ownership,
  rota, artefato privado e retenção segura do checkpoint;
- frontend: criação em linguagem humana, ausência de identificadores internos e
  ausência de percentual quando o engine só informa estágio;
- contrato OpenAPI, inventário modular, build e orçamento de bundle;
- SQL aditivo: `backend/sql/093_photo_reconstruction.sql` e
  `backend/sql/postgresql/025_photo_reconstruction.sql`.

## Smoke real do motor local

COLMAP 4.1.1 foi executado no Apple M4 Pro sem CUDA sobre 24 imagens reduzidas
para 1600 px do dataset oficial South Building. O gateway registrou 24/24
imagens, 3.908 pontos esparsos, erro médio de reprojeção de 0,381595 px e gerou
PLY esparso com 3.126 vértices e 6.223 faces em 15,003 s. O contrato completo do
adapter também produziu PLY privado com provenance.

Essa execução prova instalação, isolamento, contrato, SfM, meshing CPU e
provenance. Não prova reconstrução de objeto, cobertura de superfície, escala,
qualidade densa ou imprimibilidade. Resultado e checksums estão em
`docs/community/benchmarks/photo-reconstruction/2026-08-02-colmap-south-building.json`.

## Contrato do provider

O gateway Tripo segue os endpoints oficiais de upload, criação multiview e
consulta de tarefa. Testes simulados validam seleção e ordem das quatro vistas,
uma única criação paga por correlação, retomada pelo `task_id`, divergência de
fingerprint, custo em créditos e ausência de cobertura inventada. A credencial
entra somente no ambiente restrito do subprocesso e a URL de saída precisa ser
HTTPS com resolução pública.

Falhas do provider não são repetidas automaticamente: sem idempotência forte
documentada na criação remota, um retry cego poderia cobrar outra tarefa. O
checkpoint reconcilia tarefas conhecidas; estado ambíguo exige revisão humana.

Não foi feita chamada real ou cobrança. Portanto essa evidência valida o
contrato e as proteções do gateway, não a disponibilidade, qualidade ou custo
observado do provider.

## Pendências para fechamento

O gateway local e o COLMAP estão validados neste ambiente, mas não há CUDA,
captura de objeto físico nem credencial/chamada real de provider. Portanto, ainda não
existe evidência honesta de reconstrução densa de objeto. O pacote só pode ser
fechado após:

1. conjunto de fotos autorizado e objeto de referência mensurável;
2. execução do mesmo benchmark no pipeline local e provider elegível;
3. medição de conclusão, cobertura, erro por eixo/escala, duração, recurso e
   custo, sem avaliação apenas visual;
4. webhook ou polling autenticado/reconciliado quando o provider escolhido
   exigir operação assíncrona;
5. teste de carga e canário em ambiente do provider; a política e o executor
   supervisionado de retenção/cleanup local já estão implementados;
6. validação manual desktop/mobile do estado de processamento real.

Referências oficiais consultadas: [geração multiview](https://platform.tripo3d.ai/docs/generation),
[upload](https://platform.tripo3d.ai/docs/upload),
[consulta de tarefa](https://platform.tripo3d.ai/docs/task) e
[preços em créditos](https://platform.tripo3d.ai/docs/billing).

## Rollback

Definir `PRINTORA_RECONSTRUCTION_MODE=disabled`, bloquear novos jobs e manter
capturas, tentativas e artefatos privados em leitura. A release anterior ignora
as tabelas aditivas. Não executar `DROP`, `DELETE` nem remoção de objetos.
