# Evidência atual — qualificação e revisão de malha

Data: 2026-08-02
Estado: implementação parcial; aprovação humana, snapshot, preflight e piloto
físico continuam bloqueantes para o fechamento.

## Entregue

- qualificação determinística limitada para OBJ, STL, PLY ASCII, GLB e 3MF;
- dimensões, manifold, watertight, bordas, buracos, normais, componentes,
  degenerados, auto-interseção limitada e espessura conservadora;
- limpeza, orientação, fechamento controlado, remoção de fragmentos, redução e
  conversão OBJ/STL/3MF com manifesto e checksum;
- revisão assíncrona e encadeada por job durável, idempotência, owner, cota,
  cancelamento, requalificação e download privado;
- interface simples que recomenda uma correção por vez, preserva a origem e
  bloqueia arquivo final quando escala ou topologia ainda não são seguras.

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

- confirmação métrica e revisão humana vinculadas ao checksum;
- snapshot aprovado no projeto e integração com fatiamento/preflight;
- comparação visual/textual bruto versus revisado;
- piloto físico com objeto autorizado, paquímetro, material e perfil registrados;
- benchmark real e fechamento dos bloqueios externos do processador 3D.
