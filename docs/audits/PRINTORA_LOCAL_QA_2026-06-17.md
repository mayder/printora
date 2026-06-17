# QA local do Printora - 2026-06-17

## Escopo validado

- Branch local: `cloud`.
- App local: `http://127.0.0.1:8069`.
- Ambiente: backend/frontend locais com dados controlados, usuario autenticado, impressoras, agentes, comunidades, perfil publico, catalogo, biblioteca social e rotas publicas.
- Temas: claro e escuro.
- Viewports: desktop e mobile.
- Rotas internas cobertas na matriz visual: `overview`, `printers`, `agents`, `social`, `catalog`, `setup`, `settings`, detalhe da impressora, detalhe do agente, relatorios e comunidade.
- Rotas publicas reais cobertas: `/p/6`, `/c/maker-voron-design`, `/u/maker-social`.

## Evidencias locais

- Matriz visual mobile final:
  - `/tmp/printora-full-qa-visual-20260617-r6/report-mobile-final-light-a.json`
  - `/tmp/printora-full-qa-visual-20260617-r6/report-mobile-final-light-b.json`
  - `/tmp/printora-full-qa-visual-20260617-r6/report-mobile-final-dark-a.json`
  - `/tmp/printora-full-qa-visual-20260617-r6/report-mobile-final-dark-b.json`
- Matriz visual desktop final:
  - `/tmp/printora-full-qa-visual-20260617-r6/report-desktop-final-light.json`
  - `/tmp/printora-full-qa-visual-20260617-r6/report-desktop-final-dark-a.json`
  - `/tmp/printora-full-qa-visual-20260617-r6/report-desktop-final-dark-b.json`
- Contact sheets finais:
  - `/tmp/printora-mobile-final-light-contact.png`
  - `/tmp/printora-mobile-final-dark-contact.png`
  - `/tmp/printora-desktop-final-light-contact.png`
  - `/tmp/printora-desktop-final-dark-contact.png`
- Acoes seguras: `/tmp/printora-qa-safe-actions-final3.json` e `/tmp/printora-qa-printer-detail-actions-final.json`.
- Screenshot da UI final: `/tmp/printora-qa-ui-final-clean.png`.
- Screenshot de rota publica: `/tmp/printora-qa-public-printer.png`.
- Screenshot de acoes seguras: `/tmp/printora-qa-safe-actions-final3.png`.

## Problemas corrigidos

- Endpoint publico de versao expunha caminho/local interno de banco e detalhes operacionais.
- Releases e status de update mostravam identificadores internos de pacote/lote.
- Telas de agentes exibiam prefixos de credencial/token operacional.
- Suporte/paridade de agente retornavam credenciais e identificadores internos em payloads de suporte.
- Detalhe do agente podia quebrar com `Cannot read properties of null (reading 'agent')`.
- Detalhe de impressora e detalhe de agente tinham acao de voltar pouco explicita.
- Tabela do catalogo quebrava em mobile; agora vira cards rotulados.
- Relatorios/diagnostico dentro do detalhe da impressora tinham risco de overflow em mobile.
- Cards/listas de impressora e paineis gerais tinham estouro horizontal em mobile.
- Aba `Resumo` do detalhe da impressora abria formularios de publicacao, configuracao tecnica e material/fatiamento por padrao; agora esses blocos abrem em leitura e os formularios aparecem apenas por acao explicita.
- Resumo da impressora, dashboard da frota, operacao e manutencao tinham grids desktop forçando colunas estreitas no mobile; foram ajustados para empilhamento responsivo sem texto vertical.
- Paginas publicas standalone `/p/{id}` e `/u/{slug}` nao aplicavam o tema persistido; agora respeitam tema claro/escuro.
- A validacao de comunidade publica usava slug inexistente; a cobertura final usa `maker-voron-design`, com fixture local valida.
- Conteudo publico de comunidade mencionava termos tecnicos sensiveis fora do necessario.

## Simulado

- Agente conectado/offline/degradado e impressora conectada/sem agente foram validados por fixtures/dados locais e APIs locais.
- Upload, biblioteca, comunidade, filtros, abas, publicacao e superficies sociais foram exercitados em UI/API local sem enviar arquivo real externo.
- Slicing, preflight, telemetria, jobs e suporte foram verificados por contratos locais, estados de tela e endpoints simulados/controlados.

## Pendente de ambiente real

- Deploy, push, SSH real, restart remoto, flash, G-code real e acao destrutiva nao foram executados por regra de seguranca.
- Impressao fisica, telemetria real de impressora e envio real de G-code dependem de autorizacao explicita e ambiente conectado.

## Validacao tecnica

- Testes focados de backend para versao, releases, suporte de agente e paridade de agente.
- Build frontend.
- Check oficial completo deve ser executado no fechamento: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
