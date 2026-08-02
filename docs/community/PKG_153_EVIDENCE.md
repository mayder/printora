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
  rota e artefato privado;
- frontend: criação em linguagem humana, ausência de identificadores internos e
  ausência de percentual quando o engine só informa estágio;
- contrato OpenAPI, inventário modular, build e orçamento de bundle;
- SQL aditivo: `backend/sql/093_photo_reconstruction.sql` e
  `backend/sql/postgresql/025_photo_reconstruction.sql`.

## Pendências para fechamento

Não há COLMAP/Meshroom nem gateway de provider instalado/configurado neste
ambiente. Portanto, ainda não existe evidência honesta de reconstrução real. O
pacote só pode ser fechado após:

1. conjunto de fotos autorizado e objeto de referência mensurável;
2. execução do mesmo benchmark no pipeline local e provider elegível;
3. medição de conclusão, cobertura, erro por eixo/escala, duração, recurso e
   custo, sem avaliação apenas visual;
4. webhook ou polling autenticado/reconciliado quando o provider escolhido
   exigir operação assíncrona;
5. teste de carga, egress/segredo, canário e política de retenção/cleanup;
6. validação manual desktop/mobile do estado de processamento real.

## Rollback

Definir `PRINTORA_RECONSTRUCTION_MODE=disabled`, bloquear novos jobs e manter
capturas, tentativas e artefatos privados em leitura. A release anterior ignora
as tabelas aditivas. Não executar `DROP`, `DELETE` nem remoção de objetos.
