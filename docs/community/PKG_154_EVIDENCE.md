# Evidência atual — qualificação e revisão de malha

Data: 2026-08-02
Estado: lotes de software concluídos; benchmark real do processador e piloto
físico continuam bloqueantes para o fechamento integral.

## Entregue

- qualificação determinística limitada para OBJ, STL, PLY ASCII, GLB e 3MF;
- dimensões, manifold, watertight, bordas, buracos, normais, componentes,
  degenerados, auto-interseção limitada e espessura conservadora;
- limpeza, orientação, fechamento controlado, remoção de fragmentos, redução e
  conversão OBJ/STL/3MF com manifesto e checksum;
- revisão assíncrona e encadeada por job durável, idempotência, owner, cota,
  cancelamento, requalificação e download privado;
- escala uniforme explícita a partir de um eixo e uma medida conhecida em
  milímetros, registrada no manifesto e aplicada em nova revisão;
- interface simples que recomenda uma correção por vez, preserva a origem e
  bloqueia arquivo final quando escala ou topologia ainda não são seguras.
- aprovação/rejeição humana idempotente presa ao checksum, com finalidade,
  aceite de limitações e comparação métrica de até 3% de desvio;
- uso mecânico bloqueado sem CAD, dimensões críticas e validação física;
- promoção do STL/3MF aprovado para arquivo validado do projeto, referência ao
  mesmo objeto privado, snapshot imutável e cota sem contagem dupla;
- atualização imediata do projeto e continuidade explícita para o fluxo normal
  de fatiamento, que ainda exige impressora, material, perfil, prévia e preflight;
- alternativa textual para partes observadas/inferidas e histórico de cada
  reparo com versão e checksum.

## Evidência automatizada

- `backend/tests/test_mesh_qualification.py`;
- `backend/tests/test_mesh_repair.py`;
- `backend/tests/test_mesh_revisions.py`;
- `frontend/tests/unit/ReconstructionPanel.test.ts`;
- `frontend/tests/unit/meshRevisionApi.test.ts`.

## Limites declarados

- correção não significa aprovação para impressão;
- defeito complexo não recebe preenchimento ou reparo inventado;
- STL/3MF final não é oferecido na interface sem unidade conhecida e superfície
  fechada, sem cruzamentos ou junções complexas detectadas;
- o artefato bruto e todas as revisões anteriores permanecem privados e
  imutáveis durante correção, falha, cancelamento e rollback.

## Pendências para fechamento

- piloto físico com objeto autorizado, paquímetro, material e perfil registrados;
- benchmark real e fechamento dos bloqueios externos do processador 3D.

## Evidência focal de entrega no projeto

- `37` testes backend em qualificação, revisão, projetos e fatiamento;
- `8` testes frontend focais de reconstrução e API de revisão;
- build de produção e orçamento de bundle aprovados;
- aprovação idempotente comprovou snapshot atual, checksum idêntico entre
  revisão e arquivo, autorização por owner e armazenamento sem dupla contagem.
