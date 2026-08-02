# Evidência — captura guiada de objeto por fotos

Data: 2026-08-02

## Resultado

A área `Meus projetos` permite ao proprietário iniciar e retomar uma captura
privada sem escolher impressora. A tela explica preparação, consentimento,
voltas e alturas em linguagem simples; mostra cobertura, fotos para refazer,
escala e próximas ações antes de liberar a conclusão.

## Contrato e persistência

- sessão vinculada ao projeto e ao owner, com estados `draft`, `review`,
  `ready`, `cancelled` e `expired`;
- alvo de 12 a 80 fotos, três alturas e posição determinística;
- foto original não é exposta: JPEG/PNG é decodificado, orientação é
  normalizada e metadados são removidos antes da promoção;
- reenvio idempotente não duplica; foto repetida em outro ângulo é recusada;
- refazer uma posição preserva a revisão anterior como não corrente;
- escala registra método, milímetros, incerteza e confirmação explícita;
- exportação privada gera ZIP temporário com manifesto e checksums;
- SQL aditivo: `backend/sql/092_photo_capture.sql` e
  `backend/sql/postgresql/024_photo_capture.sql`.

## Qualidade e privacidade

- assinatura real, decoder, formato estático, limite de 15 MB e 40 milhões de
  pixels protegem o pipeline de arquivo disfarçado e imagem desproporcional;
- resolução, brilho e foco são avaliados em amostra limitada e produzem ação
  legível; nenhuma aprovação é inferida quando a foto falha;
- JPEG/PNG são recodificados sem EXIF, GPS, comentários ou textos incorporados;
- endpoints retornam 404 para outro owner e respostas públicas não contêm foto,
  storage key ou metadado privado;
- cota considera o armazenamento já usado pelas capturas;
- rascunhos vencem após 30 dias para estado lógico `expired`; não existe rotina
  automática de exclusão física. Qualquer limpeza exige política e ação
  autorizadas, preservando exportação e evidência.

## Validação

- backend focado: assinatura, metadados, qualidade acionável, idempotência,
  substituição, escala, cobertura, conclusão, isolamento de owner, rota e ZIP;
- frontend focado: preparação, consentimento, início e retomada sem linguagem
  interna;
- build TypeScript/Vite e orçamento de bundle;
- navegador local: fluxo real da criação do projeto ao início da captura;
- responsividade verificada em 1440x900, 390x844 e 320x720, sem overflow
  horizontal; botões, bloqueios e instruções permaneceram legíveis.

## Rollback

Ocultar `Digitalizar este objeto` e bloquear criação de novas sessões. Manter
sessões, fotos e exportação privadas em leitura. A release anterior ignora as
tabelas aditivas. Não executar `DROP`, `DELETE` ou remoção de objetos durante o
rollback.
