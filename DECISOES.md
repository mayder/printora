# DECISOES.md

Registro de decisoes arquiteturais, tecnicas e operacionais relevantes do monorepo Printora.

## Regras

- Registrar escolhas que afetam arquitetura, stack, operacao, testes, seguranca, rollback ou manutencao.
- Nao registrar decisao trivial.
- Se uma decisao substituir outra, marcar a anterior como `substituida`.
- Se uma decisao for revertida, registrar motivo e plano de reversao.
- Decisoes aceitas valem como fonte de verdade ate serem substituidas.

## Modelo

```txt
### DEC-YYYYMMDD-01 - Titulo

Status: proposta | aceita | substituida | revertida
Data:
Contexto:
Decisao:
Alternativas consideradas:
Consequencias:
Impacto em testes:
Impacto em rollback:
Como reverter:
Referencias:
```

## Decisoes

### DEC-20260618-01 - Projeto de impressão é a entidade raiz de conteúdo imprimível

Status: aceita
Data: 2026-06-18
Contexto: a modelagem anterior nasceu em torno de biblioteca social, arquivos por comunidade e fluxo de fatiamento/envio em Administração. Esse desenho deixa comunidade parecendo dona do conteúdo, dificulta projetos com múltiplos arquivos STL/3MF/ZIP e mistura descoberta social com operação diária de impressão.
Decisao: adotar `Projeto de impressão` como entidade raiz para conteúdo imprimível. Arquivos do projeto, versões/snapshots, compartilhamentos em comunidade, publicação, jobs de fatiamento, entrega/G-code e histórico de impressão são relações ou derivados do projeto. Comunidade é apenas canal de compartilhamento/descoberta em relação N:N; Administração é apenas configuração, diagnóstico, política e fallback operacional. Jobs, G-code e histórico devem apontar para snapshot imutável do projeto e dos arquivos selecionados.
Alternativas consideradas: manter modelo/arquivo como item da comunidade; criar cópias por comunidade; manter fatiamento diário em Administração; tratar cada STL como projeto independente.
Consequencias: o mesmo projeto pode servir para todo o sistema, aparecer em zero, uma ou várias comunidades sem duplicação e conter múltiplos arquivos/peças. Fluxos legados de comunidade/Administração devem ser migrados, rebaixados ou removidos somente após a área nova estar validada. Decisões anteriores sobre biblioteca social passam a ser interpretadas como base legada a ser reaproveitada/migrada, não como raiz final do domínio.
Impacto em testes: testes dos PKG-77 a PKG-81 devem cobrir projeto multi-arquivo, snapshot imutável, relação N:N com comunidades, privacidade, publicação independente, fatiamento por seleção de arquivos, histórico sanitizado e regressão dos atalhos legados.
Impacto em rollback: médio; a implementação deve manter compatibilidade ou redirects enquanto dados legados existirem. Remoção de telas/rotas antigas só ocorre depois de validação do fluxo novo.
Como reverter: reativar entradas legadas de biblioteca/comunidade/Administração como fluxo principal e tratar projetos como camada de apresentação, mantendo dados criados como legado; reversão física de dados só com backup SQLite e confirmação explícita.
Referencias: `DEMANDAS.md` PKG-77 a PKG-81, `TELAS.md` Distribuição de conteúdo, `backend/sql/068_print_projects_core.sql`, `backend/sql/069_print_project_experience.sql`, `/api/print-projects`.

### DEC-20260617-01 - Impressão real alimenta ranking sem expor telemetria privada

Status: aceita
Data: 2026-06-17
Vigência: válida como regra de privacidade/ranking, mas subordinada à DEC-20260618-01; sinais públicos novos apontam para projeto central e snapshot, não para cópia por comunidade.
Contexto: resultados reais de impressão precisam melhorar recomendações e troubleshooting, mas impressora, Moonraker e telemetria detalhada são dados privados.
Decisao: criar histórico de impressão ligado ao fluxo de entrega de G-code, com feedback público ou privado e telemetria mínima segura. Feedback de sucesso/falha atualiza `social_quality_signals` com sinais explicáveis, sem publicar identificador privado de impressora.
Alternativas consideradas: usar apenas downloads/favoritos; expor telemetria completa; criar ranking separado para impressão.
Consequencias: recomendações passam a considerar resultado real de impressão mantendo privacidade e rollback simples por domínio.
Impacto em testes: testes focados devem cobrir privacidade do payload, feedback, atualização de ranking e validação de foto HTTPS.
Impacto em rollback: médio; há novo script SQLite `065_print_job_history.sql`.
Como reverter: remover endpoints/UI de histórico e restaurar backup SQLite anterior ao script `065_print_job_history.sql` se os dados não puderem permanecer como legado.
Referencias: `backend/sql/065_print_job_history.sql`, `backend/app/print_history.py`, `backend/app/routes/slicing.py`, `frontend/src/screens/SettingsScreen.tsx`.

### DEC-20260617-02 - Premium e patrocinado exigem revisão e transparência

Status: aceita
Data: 2026-06-17
Vigência: válida como regra comercial, mas subordinada à DEC-20260618-01; classificação comercial nova pertence ao projeto central, não à comunidade.
Contexto: o marketplace precisa preparar conteúdo premium/curado/patrocinado sem cobrar de fato e sem confundir promoção com recomendação técnica neutra.
Decisao: adicionar classificação comercial no item da biblioteca, revisão administrativa separada e aviso de transparência no payload/UI. Conteúdo premium ou patrocinado só pode ficar público com revisão aprovada.
Alternativas consideradas: criar marketplace separado; permitir premium sem revisão; misturar promoção no ranking técnico.
Consequencias: a biblioteca comunitária segue livre, promoção fica auditável e cobrança real permanece fora do escopo.
Impacto em testes: testes devem cobrir bloqueio de publicação sem revisão, aprovação administrativa e aviso de patrocinado.
Impacto em rollback: médio; há novo script SQLite `066_social_library_commercial_curation.sql`.
Como reverter: remover campos/rota/UI comerciais e restaurar backup SQLite anterior ao script `066_social_library_commercial_curation.sql` se necessário.
Referencias: `backend/sql/066_social_library_commercial_curation.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`.

### DEC-20260617-03 - Integração externa começa como bookmark controlado

Status: aceita
Data: 2026-06-17
Vigência: válida como mecanismo legado/base, mas subordinada à DEC-20260618-01; referências externas novas pertencem a projetos de impressão.
Contexto: importar bibliotecas externas pode gerar risco legal, dependência instável e cópia indevida de arquivo.
Decisao: implementar fonte externa, preview determinístico e referência/bookmark por URL como primeira etapa. O sistema registra metadados, licença, atribuição e checksum opcional, mas não copia arquivo externo sem fluxo futuro específico.
Alternativas consideradas: baixar arquivo externo automaticamente; integrar API de repositórios externos já no primeiro lote; guardar apenas URL livre em descrição.
Consequencias: integração externa fica segura, auditável e sem dependência de serviço externo no teste local.
Impacto em testes: testes devem cobrir atribuição obrigatória, bookmark sem cópia, preview por URL e deduplicação por checksum.
Impacto em rollback: médio; há novo script SQLite `067_external_library_imports.sql`.
Como reverter: remover endpoints/UI de fontes externas e restaurar backup SQLite anterior ao script `067_external_library_imports.sql` se necessário.
Referencias: `backend/sql/067_external_library_imports.sql`, `backend/app/external_library.py`, `backend/app/routes/external_library.py`, `frontend/src/screens/PublicCommunityScreen.tsx`.

### DEC-20260616-14 - Notificacoes sociais ficam separadas de alertas operacionais

Status: aceita
Data: 2026-06-16
Contexto: interacoes sociais, comunidades e conteudo acompanhado precisam notificar o usuario sem competir com alertas de impressora, agente, firmware, Moonraker ou manutencao. Misturar esses fluxos criaria ruido operacional e risco de tratar like/resposta como incidente tecnico.
Decisao: criar o dominio `social_notifications`, com SQL proprio em `058_social_notifications.sql`, central in-app, preferencias por tipo, acompanhamento de conteudo e digest opcional. Eventos sociais principais emitem notificacoes por rota/dominio, respeitando bloqueio social, preferencias e auto-notificacao. A UI fica como aba `Notificacoes` dentro de `Social`, enquanto alertas operacionais continuam nas telas de frota, impressora, agente e administracao.
Alternativas consideradas: reutilizar alertas operacionais existentes; enviar apenas email; criar notificacoes no frontend; misturar notificacoes na topbar global.
Consequencias: o produto preserva a separacao entre operacao tecnica e vida social do conteudo. A primeira versao entrega digest como agrupamento in-app pendente, sem agendamento externo ou envio por email.
Impacto em testes: `backend/tests/test_social_catalog.py` cobre preferencias, follows, bloqueio, emissao por comentarios/relacoes e leitura; build frontend valida a central social.
Impacto em rollback: medio; remover rotas/UI desativa emissao nova, mas notificacoes/follows ja persistidos podem permanecer como legado sem afetar operacao.
Como reverter: reverter `backend/app/social_notifications.py`, `backend/app/routes/social_notifications.py`, integracoes em `backend/app/routes/social_catalog.py`, `backend/sql/058_social_notifications.sql`, aba de notificacoes em `SocialScreen.tsx` e documentacao relacionada.
Referencias: `backend/app/social_notifications.py`, `backend/app/routes/social_notifications.py`, `backend/sql/058_social_notifications.sql`, `frontend/src/screens/SocialScreen.tsx`, `TELAS.md`, `RUNBOOK.md`.

### DEC-20260616-13 - Moderacao social usa fila auditavel e remocao logica

Status: aceita
Data: 2026-06-16
Contexto: conteudo social, arquivos 3D, tags e catalogo precisam de denuncia, revisao e bloqueio rapido sem apagar historico, sem misturar curadoria publica com tela Social e sem criar operacao irreversivel em SQLite/cloud.
Decisao: criar o dominio `social_moderation`, com SQL proprio em `057_social_moderation.sql`, tabelas de denuncias e acoes, rota autenticada para denuncia publica e rotas administrativas para fila/acao. Acoes de ocultar, remover, bloquear, restaurar, descartar e revisar registram motivo, estado anterior, estado novo e auditoria via `catalog_audit_events`. Conteudo moderado muda estado logico em tabelas existentes; exclusao fisica fica fora do fluxo. A UI administrativa fica na tela `Catalogo`, separada da tela `Social`.
Alternativas consideradas: apagar linhas denunciadas; criar moderacao dentro da tela Social; reutilizar apenas `catalog_audit_events` sem fila dedicada; criar tabela de auditoria nova para cada entidade.
Consequencias: moderacao fica reversivel, rastreavel e compativel com rollback por acao restauradora. A fila dedicada facilita triagem e preserva privacidade do usuario comum. Retencao de denuncias e acoes deve seguir politica operacional de auditoria social antes de qualquer limpeza.
Impacto em testes: `backend/tests/test_social_catalog.py` cobre denuncia, permissao administrativa, acao, auditoria, restauracao e curadoria de tag; build frontend valida o painel administrativo.
Impacto em rollback: medio; reverter o dominio remove a fila nova, mas estados logicos aplicados em conteudo permanecem e devem ser restaurados por acao administrativa ou SQL supervisionado antes de desativar o fluxo.
Como reverter: reverter `backend/app/social_moderation.py`, `backend/app/routes/social_moderation.py`, inclusao no `main.py`, `backend/sql/057_social_moderation.sql`, painel de moderacao no Catalogo e documentacao relacionada.
Referencias: `backend/app/social_moderation.py`, `backend/app/routes/social_moderation.py`, `backend/sql/057_social_moderation.sql`, `frontend/src/screens/CatalogAdminScreen.tsx`, `TELAS.md`, `RUNBOOK.md`.

### DEC-20260616-12 - Ranking social usa sinais publicos e explicaveis

Status: aceita
Data: 2026-06-16
Contexto: a descoberta social precisa priorizar conteúdo técnico útil sem usar dados privados, sem depender de algoritmo opaco e sem premiar auto-voto.
Decisao: criar o domínio `social_ranking`, com SQL próprio em `055_social_ranking_reputation.sql` e estado de materialização em `056_social_materialization_state.sql`. O score é determinístico e deriva sinais públicos: downloads, favoritos de outros usuários, soluções marcadas e reações úteis. Auto-voto é ignorado no score; sinais negativos de denúncia/moderação ficam modelados como `report` para reduzir exposição quando o domínio de moderação registrar eventos. A reputação técnica é snapshot derivado desses sinais e a UI mostra motivos curtos por recomendação. Índice social e sinais usam assinatura persistida da fonte para evitar rebuild síncrono em toda consulta pública.
Alternativas consideradas: usar somente ordenação recente; usar ranking por dados privados de impressão; bloquear favoritos próprios no produto; criar serviço externo de recomendação.
Consequencias: recomendações são auditáveis, reversíveis e coerentes com SQLite/cloud atual. O score inicial ainda é simples e deve evoluir quando existirem sinais reais de impressão e moderação completa.
Impacto em testes: `backend/tests/test_social_catalog.py` cobre score, explicação, reputação e ignorar auto-voto.
Impacto em rollback: médio; há novos scripts SQLite `055_social_ranking_reputation.sql` e `056_social_materialization_state.sql`.
Como reverter: remover rotas/UI de recomendações/reputação e restaurar backup SQLite anterior aos scripts `055_social_ranking_reputation.sql` e `056_social_materialization_state.sql` se as tabelas não puderem permanecer como legado.
Referencias: `backend/sql/055_social_ranking_reputation.sql`, `backend/sql/056_social_materialization_state.sql`, `backend/app/social_ranking.py`, `backend/app/routes/social_ranking.py`, `frontend/src/screens/SocialScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-11 - Busca social usa indice publico derivado

Status: aceita
Data: 2026-06-16
Contexto: a descoberta social precisa pesquisar comunidades, discussões, arquivos, configurações técnicas, perfis de material e catálogo sem vazar conteúdo privado nem transformar a UI em regra de negócio.
Decisao: criar o domínio `search_discovery`, com SQL próprio em `054_social_search_discovery.sql`, índice derivado reconstruído pela API de busca e tags normalizadas em tabelas dedicadas. A rota `/api/social/search` retorna somente conteúdo público ou comunitário elegível, com facetas e filtros técnicos; `/api/social/tags` expõe tags públicas e a curadoria administrativa usa `catalog_audit_events` existente. A UI fica como aba `Descoberta` da tela Social, consumindo contrato público sem acesso direto a persistência.
Alternativas consideradas: buscar diretamente em cada tabela no frontend; criar engine externa de busca; indexar conteúdo privado e filtrar depois.
Consequencias: a entrega fica simples para SQLite/cloud atual, com rollback claro e privacidade aplicada antes da resposta. O índice pode evoluir para atualização incremental real quando volume exigir.
Impacto em testes: `backend/tests/test_social_catalog.py` cobre privacidade, filtros técnicos e tags; build frontend valida a aba de descoberta.
Impacto em rollback: médio; há novo script SQLite `054_social_search_discovery.sql`.
Como reverter: remover rotas/UI de busca social e restaurar backup SQLite anterior ao script `054_social_search_discovery.sql` se as tabelas não puderem permanecer como legado.
Referencias: `backend/sql/054_social_search_discovery.sql`, `backend/app/search_discovery.py`, `backend/app/routes/search_discovery.py`, `frontend/src/screens/SocialScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-10 - Perfis de material e fatiamento são compartilháveis, não executáveis

Status: aceita
Data: 2026-06-16
Contexto: o PKG-63 precisa permitir compartilhamento de material e fatiamento por impressora, nozzle, material e objetivo antes de qualquer integração com engine de slicer.
Decisao: criar o domínio `print_profiles`, com SQL próprio em `053_social_material_slicing_profiles.sql`, rotas dedicadas, CRUD no detalhe da impressora e leitura pública na aba `Perfis` da comunidade. O perfil material contém marca, tipo, temperatura, cama, fluxo, compatibilidade e versão; o perfil de fatiamento ligado contém layer height, velocidade, suporte, infill, objetivo e configurações livres. Export/import usa JSON neutro e importação entra privada.
Alternativas consideradas: colocar campos de material dentro da configuração técnica do PKG-62; acoplar perfil diretamente a arquivo de slicer; executar/aplicar perfil automaticamente.
Consequencias: o produto ganha comparação e compartilhamento técnico sem risco operacional. Aplicação automática, engine de fatiamento e formatos específicos ficam para pacotes posteriores.
Impacto em testes: testes focados cobrem criação, compatibilidade, export/import, sanitização e visibilidade comunitária.
Impacto em rollback: médio; há novo script SQLite `053_social_material_slicing_profiles.sql`.
Como reverter: remover rotas/UI de perfis de material e restaurar backup SQLite anterior ao script `053_social_material_slicing_profiles.sql` se a tabela não puder permanecer.
Referencias: `backend/sql/053_social_material_slicing_profiles.sql`, `backend/app/print_profiles.py`, `backend/app/routes/print_profiles.py`, `frontend/src/screens/PrinterDetailScreen.tsx`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-09 - Configuração técnica pública é perfil social separado da operação

Status: aceita
Data: 2026-06-16
Contexto: o PKG-62 precisa permitir que makers compartilhem configurações de impressora, mods, componentes e calibrações sem transformar comunidade em permissão operacional nem expor dados sensíveis da frota.
Decisao: criar o domínio `technical_profiles`, com SQL próprio em `052_social_technical_printer_configs.sql`, rotas dedicadas e leitura na aba `Perfis` da comunidade. O registro referencia usuário, impressora, variante do catálogo, comunidade e item de biblioteca quando existir, mas o payload público contém somente dados técnicos sanitizados. Arquivamento é lógico.
Alternativas consideradas: adicionar tudo em `social_catalog.py`; guardar configurações em JSON dentro de impressoras públicas; expor campos operacionais sanitizados no frontend.
Consequencias: o domínio social ganha comparação técnica por comunidade sem aumentar o módulo social principal e sem risco de virar acesso operacional. A leitura/comparação fica na comunidade; cadastro, edição e arquivamento ficam no detalhe da impressora.
Impacto em testes: testes focados cobrem criação, edição, arquivamento lógico, sanitização de dados sensíveis, visibilidade comunitária e comparação normalizada.
Impacto em rollback: médio; há novo script SQLite `052_social_technical_printer_configs.sql`.
Como reverter: remover rotas/UI de perfis técnicos e restaurar backup SQLite anterior ao script `052_social_technical_printer_configs.sql` se a tabela não puder permanecer.
Referencias: `backend/sql/052_social_technical_printer_configs.sql`, `backend/app/technical_profiles.py`, `backend/app/routes/technical_profiles.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-08 - Organizador da biblioteca separa favoritos, coleções e listas de impressão

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: dados e endpoints existentes podem ser reaproveitados/migrados, mas projetos de impressão são a raiz final.
Contexto: o PKG-61 precisa organizar modelos sem executar fatiamento e sem vazar coleções privadas ou histórico pessoal.
Decisao: criar um organizador social com favoritos por usuário, coleções com visibilidade `private`, `community` ou `public`, listas de impressão por usuário/impressora e itens de lista sempre ligados a uma versão específica de modelo. O histórico de download autenticado entra apenas no resumo do usuário.
Alternativas consideradas: guardar favoritos em JSON no usuário; transformar coleção em feed; permitir lista de impressão sem versão.
Consequencias: a UI consegue organizar modelos sem misturar CRUD de modelo com organização pessoal, e listas permanecem reprodutíveis porque apontam para uma versão imutável.
Impacto em testes: testes cobrem isolamento de coleção privada, bloqueio de impressora de outro usuário, favorito, download histórico e lista por versão.
Impacto em rollback: médio; há novo script SQLite `051_social_library_organizer.sql`.
Como reverter: remover endpoints/UI do organizador e restaurar backup SQLite anterior ao script `051_social_library_organizer.sql` se necessário.
Referencias: `backend/sql/051_social_library_organizer.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-07 - Versionamento de biblioteca por snapshot imutável

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: snapshots de biblioteca viram base legada para snapshots imutáveis de projeto.
Contexto: o PKG-60 precisa permitir evolução de modelos sem sobrescrever artefatos já baixados, citados ou usados como origem de remix.
Decisao: persistir versões em `social_library_versions` com snapshot JSON dos arquivos, metadados do item, changelog, autor da versão e marcador `is_current`. O item mantém os arquivos correntes para listagem simples, mas cada versão preserva seu snapshot; downloads podem apontar para versão específica.
Alternativas consideradas: duplicar item por versão; criar tabela normalizada para cada arquivo de versão; manter apenas `version_label` no item.
Consequencias: rollback lógico fica barato e auditável, downloads por versão ficam mensuráveis e a UI pode mostrar histórico sem misturar rascunho, arquivo corrente e snapshot histórico.
Impacto em testes: testes cobrem imutabilidade do snapshot, download de versão, permissão de criação e promoção de versão anterior.
Impacto em rollback: médio; há novo script SQLite `050_social_library_versions.sql`.
Como reverter: remover endpoints/UI de versão, voltar downloads ao item corrente e restaurar backup SQLite anterior ao script `050_social_library_versions.sql` se necessário.
Referencias: `backend/sql/050_social_library_versions.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-06 - Publicação pública exige autoria, licença e termos

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: regras de autoria/licença continuam válidas, mas aplicadas ao projeto central.
Contexto: o PKG-59 precisa reduzir risco legal da biblioteca e deixar direitos de uso claros antes de downloads e remixes.
Decisao: itens `public` e `community` exigem `original_author_name`, `license` e aceite de termos antes da publicação. Fonte pública, atribuição e origem de remix ficam no item; itens privados podem existir como rascunho sem exposição pública. Remix referencia item ativo e não pode apontar para si mesmo.
Alternativas consideradas: permitir publicação pública com licença padrão implícita; deixar autoria apenas como dono do perfil; postergar remix para versionamento.
Consequencias: downloads e listagens passam a exibir crédito/licença claramente, e pacotes posteriores podem versionar/remixar sem perder cadeia de atribuição.
Impacto em testes: testes cobrem bloqueio sem autoria/termos, persistência de créditos e referência de remix.
Impacto em rollback: médio; há novo script SQLite `049_social_library_license_attribution.sql`.
Como reverter: remover validação de publicação, campos de UI/contrato de autoria/licença avançada e restaurar backup SQLite anterior ao script `049_social_library_license_attribution.sql` se necessário.
Referencias: `backend/sql/049_social_library_license_attribution.sql`, `backend/app/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `frontend/src/screens/PublicProfileScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-05 - Análise 3D usa parser controlado e preview derivado

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: análise por arquivo continua válida, mas arquivo passa a pertencer ao projeto.
Contexto: o PKG-58 precisa entregar dimensões, alertas e preview de modelos sem executar código nem depender de ferramenta externa pesada.
Decisao: analisar STL/3MF/ZIP com parsers controlados em Python/stdlib, lendo vértices e triângulos para derivar bounding box, dimensões, volume aproximado, contagens e alertas. O preview é SVG gerado a partir do bounding box, salvo em `thumbnail_svg`; falha fica restrita ao arquivo como `analysis_failed`.
Alternativas consideradas: usar biblioteca nativa de malha; renderizar WebGL real no servidor; bloquear item inteiro em falha de análise.
Consequencias: análise fica determinística, auditável e segura para arquivos pequenos/médios, com preview útil sem custo de renderização 3D pesada.
Impacto em testes: testes cobrem STL binário determinístico, dimensões, thumbnail, suporte provável e falha isolada por arquivo.
Impacto em rollback: médio; há novo script SQLite `048_social_library_analysis.sql`.
Como reverter: remover endpoint `/api/social/library/files/{file_id}/analysis`, métodos de análise, UI de preview/análise e restaurar backup SQLite anterior ao script `048_social_library_analysis.sql` se necessário.
Referencias: `backend/sql/048_social_library_analysis.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-04 - Upload 3D usa corpo bruto e quarentena local controlada

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: upload bruto/quarentena continua válido, mas entrada principal passa a ser arquivo de projeto, não item de comunidade.
Contexto: o PKG-57 precisa aceitar arquivo 3D real com segurança, mas o ambiente não possui `python-multipart` e o upload deve ficar separado da validação técnica profunda do pacote seguinte.
Decisao: expor upload por corpo `application/octet-stream` em item existente da biblioteca, usando `file_name` na query apenas como metadado validado. O arquivo é salvo em `<data_dir>/library_uploads/quarantine` com nome derivado de SHA-256, nunca por path do usuário. O backend valida extensão, tamanho, assinatura básica, ZIP seguro, checksum e deduplicação; resultado fica como `quarantined` ou `rejected`.
Alternativas consideradas: adicionar dependência multipart; aceitar upload direto para storage público; validar e liberar download imediatamente.
Consequencias: reduz dependência nova, evita path traversal no destino e garante que arquivo real não saia da quarentena antes da análise técnica posterior.
Impacto em testes: testes cobrem upload bruto, limite, ZIP inseguro, rejeição, quarentena, checksum e deduplicação.
Impacto em rollback: médio; há novo script SQLite `047_social_library_uploads.sql` e diretório local de quarentena.
Como reverter: remover endpoint `/api/social/library/{item_id}/files/upload`, método de upload, UI de seleção de arquivo e restaurar backup SQLite anterior ao script `047_social_library_uploads.sql`; limpar diretório de quarentena somente após confirmação explícita.
Referencias: `backend/sql/047_social_library_uploads.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-03 - Biblioteca base separa metadados de upload e quarentena

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: tabelas `social_library_*` permanecem como legado/base de migração.
Contexto: o PKG-56 precisa criar a biblioteca de modelos 3D por comunidade/perfil antes do pacote de upload seguro, validação pesada e quarentena.
Decisao: persistir itens em `social_library_items`, arquivos declarados em `social_library_files` e downloads em `social_library_downloads`. O pacote aceita STL, 3MF e ZIP apenas como metadados `metadata_only`, com dono obrigatório, licença, visibilidade explícita, vínculo opcional com comunidade/variante de catálogo e arquivamento lógico. Upload binário, armazenamento, quarentena, extração técnica e antivírus ficam no pacote dedicado seguinte.
Alternativas consideradas: aceitar upload binário já no cadastro; guardar arquivos em JSON dentro do item; não registrar downloads até haver arquivo real.
Consequencias: a UI já entrega biblioteca navegável sem assumir segurança de arquivo ainda inexistente. A separação reduz risco de aceitar binário sem validação e mantém rollback simples via script SQL.
Impacto em testes: testes cobrem visibilidade, vínculo com catálogo, criação, edição, arquivamento, histórico de download, contrato HTTP e rejeição de nomes de arquivo inseguros.
Impacto em rollback: médio; há novo script SQLite `046_social_library_items.sql`. Rollback funcional remove endpoints/UI de biblioteca e mantém dados como legado; rollback estrutural exige backup SQLite anterior ao script.
Como reverter: remover endpoints `/api/social/library*`, métodos de biblioteca em `social_catalog`, UI de `Arquivos`/perfil, tipos/serviços frontend e restaurar backup SQLite anterior ao script `046_social_library_items.sql` se as tabelas não puderem permanecer.
Referencias: `backend/sql/046_social_library_items.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `frontend/src/screens/PublicProfileScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-02 - Discussões técnicas evoluem o feed sem virar permissão operacional

Status: aceita
Data: 2026-06-16
Contexto: o PKG-55 precisa permitir posts, comentários, reações e soluções técnicas em comunidades públicas, sem transformar comunidade em organização operacional nem apagar histórico quando houver moderação.
Decisao: usar `social_feed_items` como post raiz e adicionar `social_discussion_comments`, `social_discussion_reactions` e `social_discussion_edit_history`. Posts e comentários usam remoção lógica por `deleted_at`; comentários aceitam árvore curta de um nível; solução é marcada no post de tipo dúvida por `solution_comment_id`; permissões distinguem autor, moderador de comunidade e administrador. HTML/script é rejeitado e anexos leves aceitam somente URL HTTPS pública.
Alternativas consideradas: criar um domínio paralelo de fórum; permitir árvore ilimitada; apagar linhas removidas; aceitar HTML sanitizado; usar organização como permissão de moderação.
Consequencias: discussão pública fica auditável, reversível e independente de acesso operacional. Pacotes futuros podem adicionar antiabuso completo, biblioteca e moderação avançada sem quebrar o contrato atual.
Impacto em testes: testes cobrem criação/edição/remoção lógica, comentários/respostas, reação, solução, permissões, sanitização e payload sem dados operacionais.
Impacto em rollback: médio; há novo script SQLite `045_social_discussions.sql`. Rollback funcional remove endpoints/UI de discussão e mantém dados como legado; rollback estrutural exige backup SQLite anterior ao script.
Como reverter: remover endpoints `/api/social/posts/*` e `/api/social/comments/*`, métodos de discussão em `social_catalog`, UI de discussão em `PublicCommunityScreen`, tipos/serviço frontend e restaurar backup SQLite anterior ao script `045_social_discussions.sql` se as tabelas não puderem permanecer.
Referencias: `backend/sql/045_social_discussions.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-01 - Feed técnico é público por comunidade e separado das discussões

Status: aceita
Data: 2026-06-16
Contexto: o PKG-54 precisa transformar a aba `Feed` das comunidades em conteúdo real sem antecipar toda a escrita social do PKG-55 e sem misturar organizações operacionais com comunidades públicas.
Decisao: persistir itens de feed em `social_feed_items`, sempre vinculados a `social_communities`, com tipos técnicos, visibilidade explícita, filtros por componente/material/firmware/problema e ordenações `recent`, `recommended` e `pinned`. O PKG-54 expõe leitura pública paginada e avisos de curadoria derivados do catálogo; criação/edição interativa de posts, comentários e reações fica para o PKG-55.
Alternativas consideradas: manter placeholder até posts completos; criar timeline global; usar organizações como comunidade; guardar feed apenas no frontend.
Consequencias: comunidades ganham leitura útil e segura agora, sem conceder permissão operacional e sem expor conteúdo privado. A tabela permite evoluir para posts/discussões sem quebrar o contrato público.
Impacto em testes: testes cobrem paginação, filtros, ordenação, exclusão de item privado, payload sanitizado e contrato HTTP do feed.
Impacto em rollback: médio; há novo script SQLite idempotente `044_social_community_feed.sql`. Rollback funcional remove endpoint/UI e mantém dados como legado; rollback estrutural restaura backup SQLite anterior ao script.
Como reverter: remover `/api/social/communities/{slug}/feed`, métodos de feed em `social_catalog`, integração da aba `Feed`, tipos/serviço frontend e restaurar backup SQLite anterior ao script `044_social_community_feed.sql` se a tabela não puder permanecer.
Referencias: `backend/sql/044_social_community_feed.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260615-05 - Social e descoberta publica, nao gestao proprietaria

Status: aceita
Data: 2026-06-15
Contexto: os pacotes PKG-49 a PKG-53 foram implementados com contratos separados, mas a tela Social acumulava edição de perfil, publicação de impressora, catálogo, comunidades e relações, criando uma experiência confusa e com risco de misturar descoberta pública com gestão operacional.
Decisao: a seção `Social` passa a ser somente descoberta pública e comunidade. Ela possui abas para `Comunidades`, `Impressoras`, `Makers` e `Relações`, consumindo catálogo canônico, perfis públicos, impressoras publicadas e resumo relacional. Gestão de perfil fica em `Conta > Perfil > Público`; publicar/despublicar impressora fica no detalhe da impressora; curadoria do catálogo fica na seção `Catálogo`/admin; ações sociais completas ficam em `/u/{slug}` ou `Conta > Perfil`.
Alternativas consideradas: manter formulários de gestão dentro de Social; criar uma tela social fake para recursos futuros; transformar Social em administração de catálogo; deixar publicação de impressora fora do inventário real.
Consequencias: a primeira tela Social fica navegável, sem formulário bruto, e reforça que relações sociais não concedem acesso operacional. Recursos futuros devem entrar como conteúdo real ou permanecer ocultos até terem entrega útil.
Impacto em testes: validação cobre ausência de formulário principal de perfil e de ação principal de publicar impressora em Social, filtros canônicos, comunidades reais, impressoras públicas, makers públicos, resumo de relações e ausência de dados sensíveis.
Impacto em rollback: baixo; rollback funcional reverte `frontend/src/screens/SocialScreen.tsx`, estilos sociais e a listagem sem termo de `/api/social/profiles`. Nenhum schema novo foi criado.
Como reverter: restaurar a tela Social anterior e voltar `GET /api/social/profiles` a exigir `q`, mantendo perfil, publicação, catálogo e comunidades nos contextos proprietários já existentes.
Referencias: `frontend/src/screens/SocialScreen.tsx`, `frontend/src/styles/social.css`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `backend/tests/test_social_catalog.py`.

### DEC-20260614-01 - Social usa catálogo canônico e não permissões operacionais

Status: aceita
Data: 2026-06-14
Contexto: os pacotes PKG-49 a PKG-53 introduzem perfil público, impressoras públicas, comunidades automáticas e grafo social. Esses recursos precisam usar inventário real e modelo canônico sem vazar endpoints, agentes, credenciais ou permissões de operação.
Decisao: criar o domínio `social_catalog` com SQL idempotente próprio. O catálogo mestre versiona fabricante, modelo, variante e componentes. Impressoras públicas exigem `catalog_variant_id`; comunidades são derivadas automaticamente do catálogo e da publicação consentida da impressora; relações sociais ficam isoladas em `social_relationships` e não alteram organizações, ownership ou acesso operacional.
Alternativas consideradas: usar texto livre `cloud_model`; transformar comunidade em organização operacional; misturar perfil público nos campos de conta; criar comunidades manuais antes do catálogo.
Consequencias: recursos sociais ficam consistentes e auditáveis, com menor risco de vazamento operacional. A primeira UI é enxuta e pode evoluir para curadoria avançada sem mudar o contrato base.
Impacto em testes: testes focados cobrem seed do catálogo, privacidade do perfil, vínculo obrigatório de impressora pública, sincronização de comunidade e bloqueio social.
Impacto em rollback: médio; o schema adiciona tabelas sociais e colunas públicas em `printers`. O inicializador cria backup do SQLite antes de aplicar script pendente.
Como reverter: restaurar backup do SQLite anterior ao `035_social_catalog.sql`, remover `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, tela `Social`, serviço `socialApi` e a inclusão da rota no `main.py`.
Referencias: `backend/sql/035_social_catalog.sql`, `backend/app/social_catalog.py`, `frontend/src/screens/SocialScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260615-03 - Publicação de impressora pertence ao detalhe do inventário

Status: aceita
Data: 2026-06-15
Contexto: o PKG-51 precisava deixar de tratar publicação de impressora como ação escondida na tela Social. A decisão de expor uma impressora pública deve acontecer onde o usuário reconhece o inventário operacional real, sem vazar campos de operação.
Decisao: manter a API de escrita em `/api/printers/{printer_id}/public-profile`, criar a página pública `/p/{printer_id}` via `GET /api/public/printers/{printer_id}` e concentrar a UI de publicar/despublicar no detalhe da impressora. Busca pública usa `/api/social/printers` e comunidades usam somente impressoras públicas de perfis públicos.
Alternativas consideradas: continuar publicando pela tela Social; criar slug público editável por impressora; expor a página pública apenas dentro de `/u/{slug}`.
Consequencias: a ação fica ligada ao inventário real, a URL pública fica simples e reversível por ID interno não sensível, e a tela Social permanece focada em descoberta/perfis/comunidades.
Impacto em testes: testes cobrem ownership, variante obrigatória/bloqueada, imagem inválida, busca pública, página direta, perfil privado, despublicação e sanitização de payload.
Como reverter: remover a rota pública `/p/{printer_id}`, ocultar a seção de publicação no detalhe da impressora e despublicar registros via endpoint antes de restaurar backup de banco quando necessário.

### DEC-20260615-04 - Comunidades são catálogo público, não organização operacional

Status: aceita
Data: 2026-06-15
Contexto: o PKG-52 precisa transformar comunidades automáticas em produto navegável sem misturar descoberta social com autorização operacional, e sem prometer feed/arquivos/mods completos antes dos pacotes dedicados.
Decisao: comunidades são derivadas de fabricante, modelo e variante do catálogo canônico. Vínculos são criados somente por impressoras públicas de perfis públicos. `active` e `uncurated` aceitam associação automática; `obsolete` fica como histórico sem membros/impressoras ativas; `merged` preserva a origem e aponta `merged_into_id` quando houver destino. A página `/c/{slug}` expõe contexto técnico, contagens e abas esperadas. Feed e arquivos começam como placeholders operacionais seguros; mods usam os mods públicos declarados na publicação da impressora até existir biblioteca dedicada.
Alternativas consideradas: criar grupos manuais genéricos; transformar comunidade em organização/permissão; esconder estados iniciais; apagar comunidades obsoletas; implementar feed/arquivos completos dentro do pacote de comunidade.
Consequencias: a navegação social fica útil e reversível, contagens não incluem impressoras privadas, merge/obsolescência não geram acesso novo e pacotes futuros podem ligar feed/arquivos sem alterar o contrato base.
Impacto em testes: testes cobrem associação por fabricante/modelo/variante, troca de variante, despublicação, filtros canônicos, contagens sem privados, estados `obsolete`/`merged`, contrato por slug e ausência de dados operacionais no payload.
Impacto em rollback: baixo a médio; rollback funcional usa despublicação, estado `obsolete`/`blocked` ou ajuste controlado de `merged_into_id`. Rollback estrutural exige backup SQLite anterior ao `035_social_catalog.sql`.
Como reverter: remover `/c/{slug}` e filtros da tela Social, manter as tabelas como legado, despublicar impressoras afetadas e restaurar backup SQLite apenas se for necessário desfazer o domínio social inteiro.
Referencias: `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/SocialScreen.tsx`, `frontend/src/screens/PublicCommunityScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260615-01 - Curadoria do catálogo mestre fica em superfície administrativa própria

Status: aceita
Data: 2026-06-15
Contexto: o catálogo mestre precisa sustentar comunidades, publicação de impressoras, biblioteca de modelos e fatiamento seguro. Misturar curadoria canônica na tela Social deixaria regras administrativas pouco auditáveis e permitiria confundir identidade pública com administração de dados técnicos.
Decisao: manter o domínio `social_catalog`, mas separar a superfície de curadoria na seção `Catálogo`. Usuário autenticado comum pode navegar no catálogo detalhado em modo leitura; criação, edição e promoção de curadoria ficam restritas ao administrador. A API de leitura detalhada expõe busca filtrável agrupada por fabricante/modelo, com variações técnicas dentro do detalhe do modelo, e as rotas mutáveis continuam protegidas por administrador. O contrato inclui metadados enriquecidos de fabricante/modelo: logo, resumo, site, repositório, documentação, BOM, Discord, Reddit, imagem e notas de curadoria quando confirmados. A UI não exibe campo de origem técnica nem identificador interno de pacote. Os estados válidos são `official`, `community`, `draft`, `obsolete` e `blocked`; `community` exige revisão de fonte antes de virar `official`; `draft` é usado quando volume/componentes ainda têm incerteza; `obsolete` preserva vínculos existentes e bloqueia nova publicação; `blocked` remove o item da consulta pública e fica oculto da curadoria padrão, mas continua acessível por filtro para auditoria/rollback. Merge/rename deve criar nova entrada ou atualizar metadados sem apagar a variante antiga enquanto houver impressora vinculada.
Alternativas consideradas: manter tudo na tela Social; aceitar edição por usuários comuns; apagar variantes bloqueadas; alterar `035_social_catalog.sql` já versionado.
Consequencias: a curadoria fica auditável e reversível, usuário comum não edita catálogo canônico e dados incertos entram como `community`/`draft` sem promessa técnica falsa. O detalhe administrativo expõe `detail_json` e `source_links_json` por modelo para registrar ficha técnica e fontes usadas sem misturar isso com campos internos. Logos só são exibidos quando vierem de fonte oficial, GitHub org/usuário confiável ou imagem confirmada; caso contrário a UI usa monograma.
Impacto em testes: testes cobrem seed amplo DIY, metadados enriquecidos, ficha/fonte de curadoria, política de logo confiável, contrato agrupado por modelo, filtros administrativos, ausência de identificador interno de pacote nas fontes, leitura detalhada para usuário comum, permissão 403 para mutação por usuário comum, duplicidade, obsolescência/bloqueio e vínculo de impressora com variante canônica.
Impacto em rollback: médio; seeds `036_expand_printer_catalog_seed.sql`/`037_expand_diy_catalog_breadth.sql`, metadados `038_catalog_manufacturer_model_metadata.sql`, bloqueio `039_catalog_block_toolchanger_entries.sql`, complemento `040_catalog_add_voron_phoenix_draft.sql`, sanitização `041_catalog_sanitize_internal_sources.sql`, enriquecimentos `042_catalog_enriched_metadata.sql`/`043_catalog_deeper_model_detail.sql` e tela `CatalogAdminScreen` podem ser revertidos sem apagar dados de impressoras existentes.
Como reverter: reverter scripts SQL 036 a 043, endpoints administrativos novos, `frontend/src/screens/CatalogAdminScreen.tsx`, estilos/rota `catalog` e restaurar docs; em banco já aplicado, manter linhas como legado auditável ou restaurar backup SQLite anterior ao script 036.
Referencias: `backend/sql/036_expand_printer_catalog_seed.sql`, `backend/sql/037_expand_diy_catalog_breadth.sql`, `backend/sql/038_catalog_manufacturer_model_metadata.sql`, `backend/sql/039_catalog_block_toolchanger_entries.sql`, `backend/sql/040_catalog_add_voron_phoenix_draft.sql`, `backend/sql/041_catalog_sanitize_internal_sources.sql`, `backend/sql/042_catalog_enriched_metadata.sql`, `backend/sql/043_catalog_deeper_model_detail.sql`, `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/CatalogAdminScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260615-02 - Perfil social e gerido na Conta, com pagina publica sanitizada

Status: aceita
Data: 2026-06-15
Contexto: a primeira UI do PKG-50 colocou a edição do perfil social dentro da tela `Social`, mas o fluxo correto do produto é o usuário abrir o menu do topo e gerenciar dados pessoais em `Conta > Perfil`. A página pública por slug também precisa existir como superfície separada e não pode vazar dados operacionais.
Decisao: mover a edição principal do perfil social para `Conta > Perfil > Público`, mantendo a tela `Social` como referência para comunidades e publicação social. A rota pública frontend passa a ser `/u/{slug}` e consome somente os endpoints públicos `/api/social/profiles/{slug}` e `/api/social/profiles/{slug}/printers`. A API valida avatar e links por HTTPS público, bloqueia hosts locais/privados, restringe hosts de redes sociais conhecidas, reserva slugs antigos e trata `private`, `unlisted` e bloqueio social no acesso público.
Alternativas consideradas: manter edição na tela `Social`; expor perfil público só via JSON; aceitar links livres com sanitização posterior.
Consequencias: a gestão de identidade fica no lugar esperado da conta, o contrato público permanece pequeno e auditável, e a página pública não precisa conhecer conta operacional, organizações, permissões, agente, Moonraker, SSH ou tokens.
Impacto em testes: testes focados cobrem slug duplicado, slug histórico reservado, privacidade, unlisted, bloqueio social, sanitização de avatar/link e ausência de dados sensíveis no contrato público.
Impacto em rollback: baixo a médio; rollback remove a aba `Público` da Conta, a tela `/u/{slug}` e os validadores novos, mantendo a tabela `social_profiles` existente.
Como reverter: restaurar os arquivos `frontend/src/screens/AuthScreen.tsx`, `frontend/src/screens/PublicProfileScreen.tsx`, `frontend/src/screens/SocialScreen.tsx`, `frontend/src/services/socialApi.ts`, `frontend/src/types/social.ts`, `backend/app/social_catalog.py` e `backend/app/routes/social_catalog.py` ao estado anterior e manter os dados de perfil como legado.
Referencias: `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/AuthScreen.tsx`, `frontend/src/screens/PublicProfileScreen.tsx`, `frontend/src/screens/SocialScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260615-03 - Relações sociais não concedem acesso operacional

Status: aceita
Data: 2026-06-15
Contexto: o PKG-53 completa follow, amizade e bloqueio. Essas relações precisam melhorar descoberta social e moderação sem alterar organizações, ownership, permissões de impressora, Moonraker, agente, SSH ou tokens.
Decisao: manter `social_relationships` como grafo social isolado. A API aceita follow/unfollow, solicitação/aceite/recusa/cancelamento de amizade, unfriend e block/unblock; bloqueio encerra follows/amizades existentes e impede novas interações sociais, mas desbloqueio não recria vínculos. Busca de perfis lista `public`, permite `unlisted` por slug direto, nunca lista `private` e filtra bloqueados para viewer autenticado. O histórico mínimo de abuso usa `catalog_audit_events` com `entity_type='social_relationship'`, ação, IDs e `retention_days=180`, sem email, telefone, token, credencial ou payload operacional.
Alternativas consideradas: criar tabela dedicada de moderação; esconder relações na tela Social; fazer amizade conceder acesso a impressoras públicas restritas.
Consequencias: relações ficam auditáveis e reversíveis sem misturar o domínio social com controle operacional. Conteúdo público/restrito respeita privacidade e bloqueio, mas acesso a impressora continua governado por owner/organização/permissões existentes.
Impacto em testes: `backend/tests/test_social_catalog.py` cobre ciclo completo de follow/friend/block, idempotência, payload sanitizado, busca/visibilidade, bloqueio e isolamento operacional.
Impacto em rollback: baixo a médio; relações podem ser encerradas por API sem apagar histórico. Se necessário, restaurar backup SQLite anterior ao script social, sem executar `DELETE` manual sem confirmação explícita.
Como reverter: reverter endpoints e UI de relacionamento em `backend/app/routes/social_catalog.py`, regras em `backend/app/social_catalog.py`, contratos de `frontend/src/services/socialApi.ts`, `frontend/src/types/social.ts`, `frontend/src/screens/PublicProfileScreen.tsx` e `frontend/src/screens/SocialScreen.tsx`.
Referencias: `backend/app/social_catalog.py`, `backend/app/routes/social_catalog.py`, `frontend/src/screens/PublicProfileScreen.tsx`, `frontend/src/screens/SocialScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260616-15 - Segurança social fica em camada dedicada

Status: aceita
Data: 2026-06-16
Contexto: a camada social já possui perfil público, relações, biblioteca, moderação e notificações. O endurecimento contra spam, scraping, assédio, enumeração e vazamento não deve ser espalhado na UI nem misturado com permissões operacionais de impressora.
Decisao: criar `social_safety` como camada dedicada com preferências de privacidade social, eventos de rate limit e sinais de abuso. A busca de perfis respeita `profile_discoverable` sem quebrar URL direta autorizada. Endpoints públicos sensíveis aplicam rate limit por ação e registram somente hashes/metadados seguros. Sinais de abuso ficam em endpoint administrativo separado de moderação, enquanto controles do usuário ficam em `Conta > Perfil > Público`.
Alternativas consideradas: aplicar limites apenas em memória; reutilizar denúncias como rate limit; colocar controles na tela `Social`.
Consequencias: regras antiabuso ficam auditáveis, testáveis e sem dependência de UI. Relações sociais continuam isoladas de organizações, agentes, Moonraker, SSH, tokens e permissões operacionais. Eventos persistidos exigem retenção/limpeza operacional.
Impacto em testes: testes focados cobrem preferências, descoberta, rate limit, sinais de abuso, endpoint administrativo e payload sanitizado.
Impacto em rollback: baixo a médio; rollback remove rotas e integração de rate limit, preservando tabelas como histórico inerte até limpeza supervisionada.
Como reverter: reverter `backend/app/social_safety.py`, `backend/app/routes/social_safety.py`, integrações em rotas sociais, SQL `059_social_safety_antiabuse.sql`, UI de segurança social em `AuthScreen.tsx` e contratos em `socialApi.ts`/`types/social.ts`.
Referencias: `backend/app/social_safety.py`, `backend/app/routes/social_safety.py`, `backend/app/routes/social_catalog.py`, `backend/app/routes/social_moderation.py`, `frontend/src/screens/AuthScreen.tsx`, `backend/tests/test_social_catalog.py`.

### DEC-20260530-01 - Setup do Zero começa após Linux e SSH ativo

Status: aceita
Data: 2026-05-30
Contexto: o Printora precisa ajudar no provisionamento de uma Raspberry/BTT Pi para impressoras Klipper, mas uma placa realmente virgem nao possui sistema operacional, rede ou serviço SSH. Prometer instalacao completa via SSH nesse estado seria tecnicamente incorreto.
Decisao: o fluxo `Setup do Zero` fica dividido em fase de preparo de mídia/boot, tratada como etapa manual ou futura, e fase SSH. O PKG-34 implementa apenas a fase SSH com preflight read-only, plano dry-run e historico sem segredos. Instalacao real, CAN, build remoto, flash e validacao final ficam em pacotes posteriores.
Alternativas consideradas: tentar instalar SO via SSH; incluir gravacao de SD/eMMC no mesmo pacote; criar um botao unico que executa KIAUH/instaladores direto.
Consequencias: o produto evita uma promessa impossivel para placa sem OS e cria uma base segura para automatizar instalacao em etapas futuras.
Impacto em testes: testes cobrem boundary de placa virgem, parser read-only, plano dry-run e ausencia de persistencia de `key_path`.
Impacto em rollback: baixo; remover a secao `setup` e as rotas `/api/setup/ssh/*` volta o produto ao estado anterior.
Como reverter: remover tela `SetupScreen`, hook/service/tipos de setup, rota `setup`, modulo `setup_wizard` e script SQL `021_setup_ssh_runs.sql`.
Referencias: `DEMANDAS.md`, `TESTES.md`, `TELAS.md`, `RUNBOOK.md`, `backend/app/setup_wizard.py`, `frontend/src/screens/SetupScreen.tsx`.

### DEC-20260530-02 - Setup CAN remoto exige modo operacional e confirmação

Status: aceita
Data: 2026-05-30
Contexto: configurar `can0` em uma Raspberry/BTT Pi altera rede e systemd, podendo derrubar comunicação com MCUs CAN se executado no momento errado. O fluxo precisa ser útil para setup do zero sem virar ação perigosa por clique acidental.
Decisao: o PKG-35 implementa diagnóstico read-only e plano dry-run por padrão. O apply real só executa com confirmação textual `CONFIGURAR CAN0`, variável de ambiente `PRINTORA_CAN_SETUP_MODE=remote`, preflight aprovado, sem impressão em andamento detectada e `sudo -n` disponível. Antes de escrever `/etc/systemd/system/can0.service`, o fluxo cria backup remoto em `~/.local/share/printora/can-setup/backups/<timestamp>/`.
Alternativas consideradas: manter CAN apenas como plano sem apply; executar apply sempre que o usuário clicar; editar arquivos de rede tradicionais como `/etc/network/interfaces` diretamente.
Consequencias: o produto entrega automação real controlada, mas continua bloqueado por padrão em ambientes comuns. O serviço systemd isolado reduz acoplamento com distribuições diferentes.
Impacto em testes: testes cobrem parsing de CAN/U2C/UUID, bloqueio por impressão, comandos `PLAN`, confirmação explícita e histórico sem `key_path`.
Impacto em rollback: médio; o rollback depende de restaurar o backup do serviço ou remover/desabilitar `can0.service` criado pelo Printora.
Como reverter: remover endpoints `/api/setup/can/*`, modulo `setup_can`, tela CAN em `SetupScreen`, SQL `022_setup_can_runs.sql` e documentação do PKG-35.
Referencias: `backend/app/setup_can.py`, `backend/sql/022_setup_can_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`.

### DEC-20260530-03 - Build remoto de firmware nunca faz flash

Status: aceita
Data: 2026-05-30
Contexto: depois de preparar SSH e CAN, o Printora precisa compilar firmware para placas reais no host da impressora. Misturar build e flash no mesmo passo aumentaria o risco de deixar MCU offline sem validação de artefatos.
Decisao: o PKG-36 implementa seleção de hardware real, geração remota de `.config`, build remoto e captura de artefatos/UUIDs, mas flash permanece fora do pacote. O build real exige `BUILD_FIRMWARE_NO_FLASH`, `PRINTORA_REMOTE_FIRMWARE_BUILD_MODE=remote`, variante física confirmada e restauração automática da `.config` por `trap`.
Alternativas consideradas: manter build apenas local; executar flash logo após build; editar `printer.cfg` automaticamente com UUID capturado.
Consequencias: o usuário ganha artefato rastreável e UUID sugerido sem mutação crítica de MCU ou config da impressora. O próximo pacote pode tratar flash com checklist próprio.
Impacto em testes: testes cobrem bloqueio sem variante confirmada, plano com comandos `PLAN`, ausência de comando de flash, confirmação textual e histórico sem `key_path`.
Impacto em rollback: médio; rollback do build é restaurar `.config.before-build` e apagar artefatos do build remoto.
Como reverter: remover endpoints `/api/setup/firmware/*`, modulo `setup_firmware`, SQL `023_setup_firmware_runs.sql`, UI Firmware remoto em `SetupScreen` e documentação do PKG-36.
Referencias: `backend/app/setup_firmware.py`, `backend/sql/023_setup_firmware_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`.

### DEC-20260522-01 - Governanca do monorepo fica na raiz

Status: aceita
Data: 2026-05-22
Contexto: `backend` e `frontend` estavam com copias completas dos documentos do modelo, criando redundancia e risco de divergencia.
Decisao: a raiz do monorepo e a fonte de verdade para `DEMANDAS.md`, `GOVERNANCA.md`, `QUALITY_ROADMAP.md`, `TESTES.md`, `BUGS.md`, `TELAS.md`, `DECISOES.md`, `RUNBOOK.md`, mapas e `check.sh`.
Alternativas consideradas: manter documentacao completa em cada modulo; duplicar apenas alguns arquivos.
Consequencias: a IA le menos arquivos, reduz conflito de regras e executa validacao por um ponto unico.
Impacto em testes: `./check.sh` da raiz passa a validar modelo, backend e frontend.
Impacto em rollback: baixo; restaurar documentos por modulo se algum fluxo exigir.
Como reverter: recriar documentacao especifica no modulo e apontar `PATHS.toml` do modulo para ela.
Referencias: `PATHS.toml`, `QUALITY_ROADMAP.md`, `check.sh`.

### DEC-20260525-01 - Instalacao usa porta 8069 e runtime local isolado

Status: aceita
Data: 2026-05-25
Contexto: instalacoes reais em Android/Termux e macOS falharam por divergencia de porta, Python global antigo, venv criada com Python incompatível e update orfao bloqueando novas versoes.
Decisao: a porta padrao do Printora e `8069`; scripts devem procurar Python `3.11+` sem remover Python antigo do usuario; a venv local deve ser recriada quando incompatível; recuperacao de update travado deve existir por UI e script oficial com backup do SQLite.
Alternativas consideradas: exigir que o usuario troque o Python global; manter comandos SQL manuais para destravar updates; manter `8085` como padrao em desktop.
Consequencias: instalacao fica mais previsivel, preserva sistemas legados do usuario e reduz suporte manual.
Impacto em testes: validar scripts de instalacao, endpoint de reconciliacao e build frontend com a nova acao.
Impacto em rollback: baixo; voltar para `8085` exigiria alterar scripts, docs e testes. Backups do banco sao criados antes do script de destravamento.
Como reverter: restaurar defaults anteriores e remover endpoint/botao/script de reconciliacao.
Referencias: `scripts/mpl_platform.sh`, `scripts/doctor_install.sh`, `scripts/unlock_update.sh`, `frontend/src/screens/SettingsScreen.tsx`, `backend/app/routes/system.py`.

### DEC-20260526-01 - Updates criticos da impressora exigem revisao e rollback visivel

Status: aceita
Data: 2026-05-26
Contexto: update de Klipper junto de plugin de toolchanger pode quebrar compatibilidade de API interna e impedir o Klipper de iniciar, sem aviso suficiente no Mainsail ou no proprio Update Manager.
Decisao: o Printora classifica `klipper` e componentes de toolchanger como risco alto quando ha update pendente, exige confirmacao literal antes de executar pelo backend/UI e exibe rollback por componente quando o Moonraker informa `rollback_version`.
Alternativas consideradas: deixar o fluxo igual ao Mainsail; apenas mostrar um aviso visual sem bloqueio backend; bloquear todos os updates globais.
Consequencias: update critico deixa de ser um clique acidental, mas continua disponivel para usuario tecnico que assumir o risco. Rollback fica operacional na mesma tela quando suportado pelo Moonraker.
Impacto em testes: adicionar testes de classificacao de risco, selecao de componentes de risco em `all` e exposicao de rollback.
Impacto em rollback: baixo; remover o guard e os campos novos restaura o comportamento anterior.
Como reverter: retirar a confirmacao de risco em `backend/app/routes/printer_updates.py`, remover metadados de risco em `backend/app/updates.py` e ocultar botoes/avisos da tela Atualizacoes.
Referencias: `backend/app/updates.py`, `backend/app/routes/printer_updates.py`, `frontend/src/screens/UpdatesScreen.tsx`.

### DEC-20260526-02 - Silencio de update vale por versao concreta do componente

Status: aceita
Data: 2026-05-26
Contexto: uma versao especifica de Klipper, plugin ou outro componente do Update Manager pode estar disponivel, mas ser indesejada no momento por quebrar o ambiente ou exigir rollback manual. O alerta recorrente passa a poluir Home, topbar, Central de alertas, Health, Checklist e Auditoria mesmo quando o usuario decidiu aguardar a proxima versao.
Decisao: permitir silenciar qualquer componente por impressora e por identidade concreta da leitura atual (`component_name` + versoes + atraso/pacotes + warnings/anomalias). Silenciar remove o item dos alertas e contadores ativos, mas mantem o card e as acoes `Reanalisar`, `Atualizar`, `Rollback` e `Reativar alerta`.
Alternativas consideradas: silenciar componente para sempre; esconder o card; transformar silencio em autorizacao de update; manter alerta sempre ativo.
Consequencias: reduz ruido operacional sem esconder a capacidade de atualizar manualmente. Quando a leitura do Update Manager muda, o silencio deixa de combinar e o alerta volta automaticamente.
Impacto em testes: cobrir persistencia SQLite, expiracao por nova versao, agregadores de Health/Checklist/Auditoria e UI da tela Atualizacoes.
Impacto em rollback: baixo; remover a tabela `update_alert_silences`, os endpoints de silencio e os filtros de agregacao restaura o comportamento anterior.
Como reverter: remover `backend/sql/019_update_alert_silences.sql`, `UpdateAlertSilenceRepository`, endpoints `/updates/silences`, filtros `printora_alert_silenced` e controles da tela Atualizacoes.
Referencias: `backend/app/updates.py`, `backend/app/routes/printer_updates.py`, `backend/app/health.py`, `backend/app/checklists.py`, `backend/app/audit.py`, `frontend/src/screens/UpdatesScreen.tsx`.

### DEC-20260526-03 - Feedback operacional usa modal e toast proprios

Status: aceita
Data: 2026-05-26
Contexto: dialogos nativos do navegador quebram a identidade visual do Printora e deixam confirmacoes operacionais importantes fora do padrao da aplicacao.
Decisao: confirmacoes de decisao devem usar modal proprio do shell React; feedback temporario de sucesso/falha deve usar toast. Erros persistentes e diagnosticos continuam inline ou na Central de alertas quando exigem acao ou leitura posterior.
Alternativas consideradas: continuar com `window.confirm`; trocar tudo por toast; usar modal para qualquer mensagem temporaria.
Consequencias: melhora consistencia visual sem esconder falhas que precisam ficar persistentes na tela.
Impacto em testes: validar build frontend e contrato de tela sem `window.confirm` no fluxo de silencio de versao.
Impacto em rollback: baixo; remover `ConfirmDialogModal`, `ToastViewport` e voltar chamadas para feedback inline/nativo.
Como reverter: retirar helpers `confirmAction`/`showToast` do shell e restaurar o fluxo anterior nos hooks.
Referencias: `frontend/src/hooks/usePrintoraApp.ts`, `frontend/src/components/modals/ConfirmDialogModal.tsx`, `frontend/src/components/ToastViewport.tsx`, `frontend/src/hooks/domains/useUpdates.ts`.

### DEC-20260526-04 - Consulta Moonraker nao pode travar a API local

Status: aceita
Data: 2026-05-26
Contexto: chamadas para hosts `.local` podem ficar presas em resolucao mDNS e bloquear o processo local do Printora, fazendo ate `/health` e acoes locais deixarem de responder.
Decisao: a gravacao de silencio de update usa a versao ja exibida no card, sem consultar Moonraker. O cliente Moonraker resolve `.local` fora do loop principal e falha com timeout curto quando a resolucao nao responde.
Alternativas consideradas: pedir reinicio manual sempre que a rota travar; manter consulta live do Moonraker antes de silenciar; trocar a porta/processo sem corrigir DNS.
Consequencias: acoes locais continuam responsivas mesmo com Moonraker lento ou DNS `.local` instavel. O silencio continua expirando quando uma nova leitura do Update Manager muda a identidade da versao.
Impacto em testes: cobrir endpoint de silencio com host Moonraker propositalmente irresolvivel e validar `./check.sh` com testes backend e frontend.
Impacto em rollback: medio; voltar a consulta live no silencio reintroduz risco de travar a UI durante falha de DNS.
Como reverter: remover campos de versao do payload de silencio, voltar a buscar `_current_update_component_payload` na rota e restaurar resolucao `.local` direta no cliente Moonraker.
Referencias: `backend/app/moonraker.py`, `backend/app/routes/printer_updates.py`, `frontend/src/hooks/domains/useUpdates.ts`.

### DEC-20260526-05 - Operacao envia G-code operacional com preflight

Status: aceita
Data: 2026-05-26
Contexto: a tela Operacao estava visualmente parecida com painel de controle, mas ainda funcionava como preview bloqueado. Isso confundia o usuario porque Mainsail permite operar movimento, temperatura, fan e fatores percentuais diretamente.
Decisao: liberar execucao operacional controlada por Moonraker para acoes de operacao da impressora, mantendo preflight live, capacidade confirmada, bloqueio quando ha impressao em andamento, historico local e monitoramento apos envio. Updates, restart, flash e alteracao de config continuam fora da tela Operacao.
Alternativas consideradas: manter apenas preview dry-run; liberar comandos sem preflight; exigir frase manual para cada clique operacional.
Consequencias: a tela passa a operar a impressora de verdade, com risco operacional proporcional a Mainsail. O backend continua bloqueando offline, Klipper/Klippy nao ready, impressao em andamento e capacidade desconhecida.
Impacto em testes: testes backend de operacao foram atualizados para `operation_ready`, preflight executavel e historico de execucao; validacao completa roda com `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
Impacto em rollback: medio; para voltar ao modelo dry-run, restaurar `build_operation_action_preflight` para `would_send_gcode=false`, remover `execute-direct` e voltar botoes da UI para preview.
Como reverter: remover endpoint `/operation/actions/execute-direct`, remover envio via `_send_and_monitor_gcode`, restaurar `can_send_commands=false` e voltar a UI para `Prévia`/`Preflight`.
Referencias: `backend/app/operation.py`, `backend/app/routes/operation.py`, `backend/app/operation_history.py`, `frontend/src/components/monitoring/OperationActions.tsx`.

### DEC-20260527-01 - Catalogo Esoterical CANBus tem schema Pydantic versionado

Status: aceita
Data: 2026-05-27
Contexto: o PKG-30 precisa transformar o guia Esoterical CANBus em catalogo local verificavel, sem depender do site em runtime e sem misturar dados manuais com cobertura nao comprovada.
Decisao: o catalogo local de firmware passa a ter contrato oficial em `FirmwareCatalog`, validado por Pydantic, com `schema_version`, `source`, `manifest`, `workflows`, `hardware`, `troubleshooting`, `update_flows`, `katapult`, `can_speed`, `known_hardware_without_local_preset` e `generation_metadata`. Cada hardware aceita `modelo`, role, conexao, guia, MCUs, metodo de flash, bootloader/Katapult, comandos de validacao, notas de seguranca, presets locais e status de catalogacao.
Alternativas consideradas: manter JSON livre sem contrato; criar tabela SQLite para catalogo; validar apenas no frontend.
Consequencias: a normalizacao, o cruzamento com presets locais, o endpoint read-only e a tela Firmware usam o mesmo contrato validado. O runtime continua lendo arquivo local e nao consulta o site externo.
Impacto em testes: testes backend validam o schema do catalogo, campos obrigatorios do contrato, vinculacao ao manifesto, cobertura do menu publico, dry-run dos scripts, exclusao de comandos mutaveis e runtime sem dependencia externa.
Impacto em rollback: baixo; remover os modelos novos e voltar ao loader JSON livre restaura o comportamento anterior, mas perde validacao de cobertura.
Como reverter: remover `FirmwareCatalog` e campos associados em `backend/app/firmware_catalog.py`, retirar o teste de schema e voltar `firmware_hardware_catalog.json` ao formato minimo anterior.
Referencias: `backend/app/firmware_catalog.py`, `backend/app/routes/firmware.py`, `backend/app/data/firmware_hardware_catalog.json`, `backend/app/data/firmware_canbus_manifest.json`, `backend/tests/test_canbus_manifest.py`, `backend/tests/test_firmware.py`, `scripts/build_canbus_manifest.py`, `scripts/build_firmware_catalog.py`, `frontend/src/screens/FirmwareScreen.tsx`.

### DEC-20260527-02 - Preset de firmware expõe build config versionado

Status: aceita
Data: 2026-05-27
Contexto: o PKG-33 precisa transformar presets locais em entrada segura para geracao futura de `.config`, sem depender de `make menuconfig`, host Klipper real ou estado de impressora.
Decisao: cada `BoardPreset` passa a expor `FirmwareBuildConfig` versionado, com arquitetura, MCU, modelo de processador, bootloader, clock, interface de comunicacao, conexao CAN/USB/serial, arquivo `.config` e output esperado. O backend calcula `build_config_status` e `build_config_validation` para classificar preset completo, faltando dados ou invalido.
Alternativas consideradas: inferir tudo apenas no gerador de `.config`; deixar validacao na UI; persistir configuracao em SQLite antes de existir edicao pelo usuario.
Consequencias: o contrato fica testavel e deterministico no endpoint de presets, sem banco novo e sem executar comandos mutaveis. A UI pode consumir o status sem duplicar regra de suficiencia.
Impacto em testes: testes backend cobrem preset completo, dados faltantes, schema invalido e compatibilidade do endpoint `/api/firmware/board-presets`.
Impacto em rollback: baixo; remover `FirmwareBuildConfig` e os campos calculados volta o preset ao contrato anterior, mas remove a garantia previa para geracao deterministica de `.config`.
Como reverter: remover `FirmwareBuildConfig`, `FirmwareBuildConfigValidation`, `build_config`, `build_config_status` e `build_config_validation` de `backend/app/firmware/models.py`, ajustar tipos frontend e remover testes do Lote 2.
Referencias: `backend/app/firmware/models.py`, `backend/app/firmware/presets.py`, `backend/tests/test_firmware.py`, `frontend/src/types/firmware.ts`.

### DEC-20260527-03 - Build local de firmware é controlado e nunca faz flash

Status: aceita
Data: 2026-05-27
Contexto: o PKG-33 precisa permitir build local real de firmware sem transformar o Printora em ferramenta de flash automático ou mutação remota de impressora.
Decisao: o build local só executa quando `PRINTORA_FIRMWARE_BUILD_MODE=local` e a confirmação textual `EXECUTE_LOCAL_BUILD_NO_FLASH` é enviada. O executor gera `.config` determinístico a partir do preset, faz backup da `.config` atual, executa apenas `make clean` e `make` no `klipper_path` local informado, restaura a `.config` em sucesso ou falha e salva preview, log e binário em `output_root/local-build/<placa>/`. Flash, SSH, restart e update ficam fora do fluxo.
Alternativas consideradas: manter apenas dry-run; aceitar `.config` manual cadastrado; expor flash na mesma UI; executar build sem confirmação textual.
Consequencias: o usuário pode validar build em ambiente local controlado com histórico e rollback, sem risco de flash automático. A UI permanece guiada pela impressora ativa e consome status do backend sem duplicar regra de build.
Impacto em testes: testes backend cobrem bloqueio por modo, bloqueio por confirmação, build fake em tmpdir, restauração de `.config` em sucesso e falha, log/binário salvos e ausência de flash/SSH/restart/update. Fechamento roda `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.
Impacto em rollback: médio; remover execução local volta o fluxo para dry-run e preview de `.config`, preservando cadastro de presets.
Como reverter: remover `execute_build_local`, ocultar o bloco de build local da tela Firmware e manter apenas `/build-runs/dry-run`, `/build-runs/preflight` e `/config-preview`.
Referencias: `backend/app/firmware/build_service.py`, `backend/app/firmware/repository.py`, `backend/app/routes/firmware.py`, `frontend/src/screens/FirmwareScreen.tsx`, `RUNBOOK.md`, `TESTES.md`.

### DEC-20260530-04 - Flash supervisionado começa por CAN/Katapult com gate remoto

Status: aceita
Data: 2026-05-30
Contexto: o PKG-37 precisa permitir flash real sem transformar o Printora em executor perigoso por padrão. Flash incorreto pode deixar MCU offline e exige prova de artefato, placa, UUID e rollback.
Decisao: o backend implementa preflight/plan/execute/historico de flash em `Setup do Zero`, mas execução real inicial fica restrita a `can_katapult`. O flash exige checklist físico, UUID visível, artefato remoto existente, impressora parada, frase específica por placa/método e `PRINTORA_REMOTE_FLASH_MODE=remote`. Métodos `usb_dfu` e `manual` ficam bloqueados até política própria.
Alternativas consideradas: liberar qualquer comando manual; manter somente plano sem execução; implementar USB/DFU junto do CAN.
Consequencias: o fluxo entrega uma primeira execução real supervisionada com risco menor e rastreabilidade, sem editar `printer.cfg`, reiniciar serviços, rodar update ou enviar G-code. Hardware real ainda precisa validação acompanhada.
Impacto em testes: testes backend cobrem bloqueios, frase/env, histórico sem `key_path` e ausência de restart/config; frontend build valida contrato da UI.
Impacto em rollback: medio; remover endpoints `/api/setup/flash/*`, modulo `setup_flash`, SQL `024_setup_flash_runs.sql` e seção Flash supervisionado da UI volta o setup ao estado PKG-36.
Como reverter: reverter o commit do PKG-37 e restaurar banco a partir do backup de schema se o script `024_setup_flash_runs.sql` ainda não puder permanecer.
Referencias: `backend/app/setup_flash.py`, `backend/app/routes/setup.py`, `backend/sql/024_setup_flash_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`, `TESTES.md`.

### DEC-20260530-05 - Aceite final do setup é read-only e sanitizado

Status: aceita
Data: 2026-05-30
Contexto: após setup, CAN, firmware e flash, o Printora precisa diferenciar base eletrônica/software pronta de calibração mecânica ainda pendente sem executar comandos perigosos.
Decisao: a validação final executa somente leitura via SSH e Moonraker local, gera checks acionáveis e relatório Markdown sanitizado. O fluxo não envia G-code, não aquece, não move eixo, não reinicia serviços, não edita configs e não executa update.
Alternativas consideradas: usar health check genérico da impressora cadastrada; executar testes de movimento/temperatura; exigir cadastro prévio da impressora.
Consequencias: o setup pode ser fechado antes do cadastro final da impressora, com relatório técnico copiável e risco operacional baixo. Homologação em campo ainda depende de hardware real acompanhado.
Impacto em testes: testes backend cobrem aprovação, bloqueio por UUID ausente, intervenção manual sem UUID e histórico sem `key_path`; frontend build valida o contrato da tela.
Impacto em rollback: baixo; remover endpoints `/api/setup/final-validation/*`, módulo `setup_final_validation`, SQL `025_setup_final_validation_runs.sql` e seção Validação final da UI.
Como reverter: reverter o commit do PKG-38 e restaurar banco a partir do backup de schema se o script `025_setup_final_validation_runs.sql` ainda não puder permanecer.
Referencias: `backend/app/setup_final_validation.py`, `backend/app/routes/setup.py`, `backend/sql/025_setup_final_validation_runs.sql`, `frontend/src/screens/SetupScreen.tsx`, `RUNBOOK.md`, `TESTES.md`.

### DEC-20260530-06 - Autenticação cloud começa em SQLite com organização opcional

Status: aceita
Data: 2026-05-30
Contexto: o Printora local não exige login, mas a evolução cloud precisa de usuário, sessão, permissões, compartilhamento opcional e base segura para agente remoto. A migração imediata para Postgres aumentaria o custo antes da validação do fluxo.
Decisao: implementar o PKG-39 primeiro em SQLite, com repositório concentrado e SQL simples, evitando dependências desnecessárias de SQLite para facilitar migração futura para Postgres. O modelo é usuário-first: email e senha obrigatórios, contatos opcionais, organização opcional para compartilhamento e papéis mínimos `owner`, `admin` e `operator`.
Alternativas consideradas: migrar já para Postgres; tornar organização obrigatória; manter somente usuário individual sem compartilhamento; deixar 2FA para pacote futuro.
Consequencias: o app local continua funcionando sem login obrigatório, enquanto a área `Conta` entrega cadastro/login, organizações, 2FA, step-up auth e credenciais de agente para o caminho cloud. Rotas operacionais passam a validar sessão quando há usuários cadastrados, rotas por impressora usam o escopo usuário/organização e históricos de setup/update passam a ter owner. A migração futura para Postgres ainda exigirá trabalho de adaptação e validação, mas fica menos arriscada.
Impacto em testes: `backend/tests/test_auth.py` cobre schema, cadastro/login, organização opcional, 2FA, step-up, credencial de agente, bloqueio anônimo de `/api/auth/me`, isolamento por impressora e isolamento de histórico operacional.
Impacto em rollback: médio; remover a camada exige reverter rotas, UI, SQL `026_auth_identity.sql`, `027_printer_ownership.sql`, `028_operational_ownership.sql` e restaurar backup do banco se o schema aplicado não puder permanecer.
Como reverter: reverter arquivos do PKG-39 e restaurar `printora.<timestamp>.before-schema.db` quando for necessário desfazer o schema aplicado.
Referencias: `backend/app/auth.py`, `backend/app/routes/auth.py`, `backend/sql/026_auth_identity.sql`, `backend/sql/027_printer_ownership.sql`, `backend/sql/028_operational_ownership.sql`, `frontend/src/screens/AuthScreen.tsx`, `frontend/src/hooks/domains/useAuth.ts`.

### DEC-20260531-08 - Impressora cloud é cadastro operacional com status derivado do agente

Status: aceita
Data: 2026-05-31
Contexto: o cadastro local de impressoras dependia de Moonraker acessível pela mesma rede, mas o uso cloud precisa permitir cadastrar a impressora antes do agente existir e compartilhar acesso por organização opcional.
Decisao: manter `printers` como entidade canônica, com owner e organização opcional do PKG-39, metadados cloud (`cloud_model`, `cloud_tags`, localização e observações) e status calculado a partir de tokens/agentes/snapshots existentes. O cadastro não tenta conectar no Moonraker automaticamente; descoberta, teste e leitura de status continuam como ações explícitas.
Consequencias: o usuário consegue preparar as duas impressoras na aplicação local por IP da API, instalar/parear agentes depois e ver estados `sem_agente`, `aguardando_pareamento`, `online`, `offline` ou `revogado` sem criar tabela nova de inventário.
Impacto em testes: `backend/tests/test_auth.py` cobre metadados cloud, detalhe escopado, status por token/agente e isolamento para usuário sem acesso.
Como reverter: reverter alterações do PKG-40 em backend/UI/docs; dados existentes de impressoras permanecem preservados e podem ser mantidos até nova decisão.
Referencias: `backend/app/printers.py`, `backend/app/routes/printers.py`, `frontend/src/screens/PrintersScreen.tsx`, `frontend/src/components/modals/PrinterModal.tsx`.

### DEC-20260530-07 - Pareamento do agente usa token curto e credencial operacional por hash

Status: aceita
Data: 2026-05-30
Contexto: o agente precisa parear a partir da rede da impressora, sem o servidor acessar a rede local e sem transformar o token de instalação em credencial permanente.
Decisao: usar token curto de pareamento por impressora, persistido por hash, com expiração, uso único e revogação. A troca pública gera uma credencial operacional `ptr_agent_*`, também persistida por hash, ligada a uma identidade estável do agente. Rotação substitui a credencial ativa e revogação bloqueia heartbeat, snapshot e jobs.
Alternativas consideradas: reutilizar credenciais genéricas do PKG-39; usar token de pareamento como credencial permanente; deixar revogação para pacote futuro.
Consequencias: o usuário consegue instalar/copiar um segredo curto uma vez e o agente passa a autenticar sem expor token permanente. A etapa ainda não instala o agente nem executa comandos remotos; isso fica para pacotes posteriores.
Impacto em testes: `backend/tests/test_agent_pairing.py` cobre uso único, expiração, revogação, ownership, rotação e bloqueio de endpoints do agente revogado.
Impacto em rollback: médio; remover exige reverter rotas, UI, `backend/app/agent_pairing.py` e SQL `029_agent_pairing.sql`, ou restaurar backup do banco anterior ao schema.
Como reverter: reverter arquivos do PKG-41 e restaurar `printora.<timestamp>.before-schema.db` se o schema aplicado não puder permanecer.
Referencias: `backend/app/agent_pairing.py`, `backend/app/routes/agents.py`, `backend/sql/029_agent_pairing.sql`, `frontend/src/screens/PrintersScreen.tsx`, `frontend/src/hooks/domains/usePrinters.ts`.

### DEC-20260531-01 - Agente remoto base em Go

Status: aceita
Data: 2026-05-31
Contexto: o agente precisa rodar em hosts Klipper variados, normalmente Raspberry/BTT Pi, com baixo uso de memória, instalação simples, atualização previsível e sem depender de Python/Node locais.
Decisao: implementar o agente em Go, sem dependências externas, como binário único com CLI `printora-agent`. A base usa config JSON, credencial separada `0600`, HTTP keep-alive, cliente Moonraker read-only, fila JSONL local, logs com redaction e serviço systemd.
Alternativas consideradas: Python para ficar próximo do ecossistema Klipper; Node por reaproveitar stack web; shell scripts para instalação mínima.
Consequencias: distribuição e atualização ficam simples por arquitetura Linux (`arm64`, `armv7`, `amd64`), com menor risco de quebrar venvs Python da impressora. Em troca, integrações futuras precisarão manter contratos Go e testes próprios.
Impacto em testes: `agent/internal/agent/agent_test.go` cobre redaction, permissões, coleta read-only, autenticação Bearer e fila local; `check.sh` passa a executar `go test ./...` em `agent/`.
Impacto em rollback: baixo; remover o agente exige reverter `agent/`, entradas em `PATHS.toml`, `check.sh` e docs. No host real, parar/remover o serviço systemd e o binário.
Como reverter: `sudo systemctl disable --now printora-agent`, remover `/usr/local/bin/printora-agent` e restaurar commit anterior ao PKG-42.
Referencias: `agent/cmd/printora-agent/main.go`, `agent/internal/agent`, `agent/systemd/printora-agent.service`, `agent/docs/README.md`.

### DEC-20260531-02 - Canal remoto usa WebSocket primario e polling de fallback

Status: aceita
Data: 2026-05-31
Contexto: o agente precisa receber comandos rápidos da aplicação web sem abrir portas no host Klipper e sem depender de conectividade WebSocket perfeita em todas as redes.
Decisao: implementar protocolo v1 sobre WebSocket outbound autenticado por credencial operacional do agente, com fallback HTTPS por polling. Jobs ficam persistidos em `agent_jobs`, sempre vinculados a `printer_id` e opcionalmente a `agent_id`, com `correlation_id` único, ack/nack/result/error, limite de payload de 64 KB e resultado idempotente. O agente deve continuar reconectando sozinho com backoff limitado e manter heartbeat/polling HTTPS durante perda de WebSocket para reduzir necessidade de reiniciar a impressora.
Alternativas consideradas: manter apenas polling; abrir socket raw; abrir porta inbound no agente; executar jobs sem persistência.
Consequencias: a latência normal fica baixa por WebSocket e ambientes restritos continuam funcionando por HTTPS. O servidor preserva isolamento por impressora e o agente continua outbound/read-only nesta etapa, aceitando apenas jobs seguros `ping` e `snapshot`. Quedas intermitentes de internet ou proxy nao devem deixar o agente parado esperando reinicio manual.
Impacto em testes: `backend/tests/test_agent_channel.py` cobre isolamento, WebSocket, versão incompatível e idempotência; `agent/internal/agent/agent_test.go` cobre polling, ack/result, URL WebSocket segura, fallback repetido e limite de backoff.
Impacto em rollback: médio; remover exige reverter rotas, serviço de jobs, agente e SQL `030_agent_channel.sql`, ou restaurar backup do banco anterior ao schema se a tabela não puder permanecer.
Como reverter: reverter arquivos do PKG-43, desativar WebSocket no config do agente com `"websocket_enabled": false` durante transição e restaurar `printora.<timestamp>.before-schema.db` se necessário.
Referencias: `backend/app/agent_pairing.py`, `backend/app/routes/agents.py`, `backend/sql/030_agent_channel.sql`, `backend/tests/test_agent_channel.py`, `agent/internal/agent/channel.go`, `agent/internal/agent/api.go`.

### DEC-20260531-03 - Instalador do agente troca token curto no host e preserva dados no uninstall

Status: aceita
Data: 2026-05-31
Contexto: o usuário precisa instalar o agente no host Klipper com o menor erro manual possível, sem transformar o token de pareamento em segredo permanente e sem esconder riscos de systemd, Moonraker, rede ou permissão.
Decisao: gerar um plano de instalação por impressora com token curto, servir um script Linux público sem segredo embutido e fazer a troca do token por credencial operacional no próprio host. O instalador tem `--preflight`, `--apply --yes` e `--uninstall`, exige systemd para serviço, grava config/credencial com permissão restrita e preserva dados locais no uninstall.
Alternativas consideradas: embutir credencial operacional no comando; instalar sem preflight; apagar diretórios no uninstall; deixar a instalação somente documentada.
Consequencias: a instalação fica copiável pela UI e auditável por status de heartbeat, mantendo uso único do token. O pacote ainda não faz auto-update nem resolve distribuição final de binários por release; isso fica para o PKG-45.
Impacto em testes: `backend/tests/test_agent_install.py` cobre isolamento do plano, consumo único do token, status por heartbeat e preflight sem vazamento de token.
Impacto em rollback: baixo; remover exige reverter endpoints/UI/script e, no host real, rodar `--uninstall`. Dados locais do agente permanecem até remoção manual explícita.
Como reverter: revogar tokens/agentes pela tela Impressoras, rodar `curl -fsSL <api>/api/agent/install/linux.sh | sudo bash -s -- --uninstall` no host e reverter arquivos do PKG-44.
Referencias: `backend/scripts/install_agent_linux.sh`, `backend/app/routes/agents.py`, `backend/app/agent_pairing.py`, `backend/tests/test_agent_install.py`, `frontend/src/screens/PrintersScreen.tsx`.

### DEC-20260531-04 - Update do agente troca apenas o binário e exige SHA-256

Status: aceita
Data: 2026-05-31
Contexto: o agente precisa evoluir junto com o servidor cloud, mas roda no host Klipper. Um update quebrado não pode reiniciar Klipper, Moonraker, firmware ou a impressora, e precisa ter rollback local.
Decisao: o agente consulta manifesto público versionado, escolhe release por plataforma, bloqueia versão/protocolo incompatível, exige SHA-256, baixa para staging, preserva backup do binário/config e troca somente o binário do `printora-agent`. Restart automático só é permitido para o serviço `printora-agent` quando `allow_service_restart=true`. Falha em health command ou restart restaura o binário anterior quando possível. A UI cria um job direcionado `remote_agent_update_check` para antecipar a verificação periódica sem acessar a rede local diretamente.
Alternativas consideradas: delegar update ao Moonraker Update Manager; baixar sem hash em ambiente de desenvolvimento; reiniciar todos os serviços do host; deixar update apenas manual.
Consequencias: o update fica automatizável e auditável sem tocar na impressora. A publicação real de binários e assinatura forte ainda depende do fluxo de release do agente, mas o contrato já bloqueia aplicação sem hash.
Impacto em testes: `backend/tests/test_agent_updates.py` cobre manifesto, relatório autenticado e histórico isolado; `backend/tests/test_agent_support.py` cobre job remoto de update direcionado; `agent/internal/agent/agent_test.go` cobre sucesso, hash inválido, rollback por health, versão bloqueada e execução do job remoto.
Impacto em rollback: médio; no host real, restaurar backup local do binário em `/var/lib/printora-agent/updates` e reiniciar apenas `printora-agent`.
Como reverter: desativar `"update_enabled": false` no config, reverter arquivos do PKG-45 e restaurar o binário anterior se necessário.
Referencias: `backend/app/agent_updates.py`, `backend/app/data/agent_update_manifest.json`, `agent/internal/agent/update.go`, `agent/cmd/printora-agent/main.go`, `RUNBOOK.md`.

### DEC-20260531-05 - Paridade remota usa matriz explícita e bloqueia mutações até PKG-47

Status: aceita
Data: 2026-05-31
Contexto: o Printora cloud precisa reutilizar as leituras e previews existentes sem o servidor acessar a rede local da impressora. Ao mesmo tempo, operações mutáveis remotas exigem autorização, preflight e rollback próprios.
Decisao: criar matriz de paridade por impressora com estados explícitos e jobs remotos executados pelo agente. Jobs read-only e dry-run são permitidos; backup real com payload grande, build/flash remoto e operação mutável ficam bloqueados até a camada de segurança do PKG-47.
Alternativas consideradas: tentar chamar Moonraker diretamente do servidor; liberar mutações junto com a paridade; esconder funcionalidades ainda não suportadas da matriz.
Consequencias: a UI/API consegue diferenciar implementado, cached, offline, bloqueado e não suportado, evitando falsa paridade. A execução remota continua outbound pelo agente e payloads são sanitizados antes de sair do host.
Impacto em testes: `backend/tests/test_agent_parity.py` cobre matriz, isolamento, criação de job, estado cached e bloqueio; `agent/internal/agent/agent_test.go` cobre job remoto read-only com sanitização.
Impacto em rollback: baixo; remover rotas e jobs de paridade volta o cloud ao pareamento/canal remoto sem alterar schema.
Como reverter: reverter arquivos do PKG-46; jobs já concluídos permanecem em `agent_jobs` como histórico seguro.
Referencias: `backend/app/agent_parity.py`, `backend/app/routes/agents.py`, `backend/tests/test_agent_parity.py`, `agent/internal/agent/moonraker.go`, `agent/internal/agent/channel.go`.

### DEC-20260531-06 - Operação remota mutável exige preflight e execução em jobs separados

Status: aceita
Data: 2026-05-31
Contexto: operações mutáveis pelo agente podem mover, aquecer ou alterar estado da impressora fora da rede local. A execução não pode depender só de clique na UI nem de confiança implícita no agente.
Decisao: separar toda operação remota mutável em dois jobs persistidos: `remote_mutation_preflight` e `remote_mutation_execute`. O servidor cria execução somente para usuário com acesso à impressora, com preflight concluído, confirmação textual única, job não expirado e resultado `can_execute=true`. O agente reexecuta preflight imediatamente antes de enviar G-code e usa apenas `/printer/gcode/script`, sem shell genérico.
Alternativas consideradas: executar direto depois da confirmação na UI; reaproveitar jobs de paridade; permitir comando arbitrário no agente; criar tabela nova de auditoria.
Consequencias: aumenta a latência operacional, mas reduz risco de ação remota fora de estado seguro. `agent_jobs` e `printer_agent_events` viram a trilha de auditoria principal sem aumentar schema.
Impacto em testes: `backend/tests/test_remote_operations.py` cobre escopo, preflight, confirmação, bloqueio por impressão e cancelamento; `agent/internal/agent/agent_test.go` cobre preflight/execução remota sem shell.
Impacto em rollback: baixo; remover rotas, módulo remoto, UI e handlers do agente volta as mutações remotas ao bloqueio do PKG-46. Jobs históricos permanecem como auditoria.
Como reverter: reverter arquivos do PKG-47 e manter agentes instalados; eles passarão a responder `unsupported job type` se algum job antigo for reenviado.
Referencias: `backend/app/remote_operations.py`, `backend/app/routes/agents.py`, `backend/tests/test_remote_operations.py`, `agent/internal/agent/moonraker.go`, `agent/internal/agent/channel.go`, `frontend/src/screens/PrintersScreen.tsx`.

### DEC-20260531-07 - Suporte do agente usa eventos/jobs existentes e pacote sanitizado

Status: aceita
Data: 2026-05-31
Contexto: suporte precisa diagnosticar agente remoto sem acessar a rede local do cliente e sem criar um novo repositório de logs sensíveis.
Decisao: usar `printer_agents`, `agent_jobs` e `printer_agent_events` como fonte de observabilidade. O painel calcula saúde, fila, falhas e alertas em leitura; `remote_doctor` coleta diagnóstico local pelo agente; o pacote de suporte é exportado sanitizado e não cria tabela nova.
Alternativas consideradas: criar tabela dedicada de logs; enviar logs completos do host; diagnosticar somente por heartbeat; apagar eventos automaticamente no endpoint.
Consequencias: a solução fica simples e auditável, sem duplicar persistência. A limpeza fica definida como retenção operacional de 180 dias e deve ser executada por rotina supervisionada futura, não pelo endpoint de suporte.
Impacto em testes: `backend/tests/test_agent_support.py` cobre escopo, alertas, doctor e sanitização do pacote; `agent/internal/agent/agent_test.go` cobre doctor remoto com log tail sanitizado.
Impacto em rollback: baixo; remover rotas/UI/handler `remote_doctor` preserva os eventos e jobs já existentes.
Como reverter: reverter arquivos do PKG-48; agentes antigos passam a rejeitar `remote_doctor` como job não suportado.
Referencias: `backend/app/agent_support.py`, `backend/app/routes/agents.py`, `backend/tests/test_agent_support.py`, `agent/internal/agent/doctor.go`, `frontend/src/screens/PrintersScreen.tsx`.

### DEC-20260531-08 - Rotas operacionais usam agente como caminho principal

Status: aceita
Data: 2026-05-31
Contexto: a aplicação precisa funcionar em cenário cloud/rede local sem depender de o servidor alcançar diretamente o Moonraker ou SSH da impressora. A impressora selecionada deve ser operada pelo agente pareado como caminho principal.
Decisao: centralizar criação, push e espera de jobs em um executor do agente e migrar status, operação, snapshots, auditoria, relatórios, checklist, calibração, update manager e inventário de firmware para jobs outbound pelo agente. Acesso direto ao Moonraker/SSH permanece apenas como legado/bootstrap de setup ou utilitário local explícito, não como caminho operacional das telas principais.
Alternativas consideradas: manter chamadas diretas com fallback para agente; duplicar lógica por rota; abrir conectividade inbound no host Klipper; permitir shell genérico no agente.
Consequencias: as telas principais passam a depender de agente online e exibem erro quando não há agente, reduzindo risco de isolamento e aproximando o ambiente local do futuro cloud. O agente precisa evoluir junto do servidor, por isso a versão esperada foi atualizada para `0.1.8`.
Impacto em testes: `./check.sh`, `go test ./...`, testes focados de backend e smoke real nas duas impressoras com status, operação, update refresh, calibração, snapshot, firmware inventory e execução segura `M106 S0`.
Impacto em rollback: médio; reverter exige restaurar handlers diretos das rotas e reinstalar agente anterior se necessário. Jobs históricos permanecem em `agent_jobs`.
Como reverter: reverter este commit, reinstalar binário do agente anterior em `/usr/local/bin/printora-agent` nos hosts e reiniciar apenas `printora-agent`.
Referencias: `backend/app/agent_executor.py`, `backend/app/agent_channel.py`, `backend/app/agent_moonraker.py`, `backend/app/routes/operation.py`, `backend/app/routes/calibration.py`, `agent/internal/agent/moonraker.go`, `agent/internal/agent/channel.go`.

### DEC-20260531-09 - Fluxos de impressora em cloud nao usam rede local pela API

Status: aceita
Data: 2026-05-31
Contexto: ao publicar a API em IP publico, ela nao tera acesso a Moonraker, SSH, CAN, arquivos ou rede local da impressora. Qualquer fluxo que ainda roda no servidor da API gera falso positivo local e falha em cloud.
Decisao: desativar descoberta/teste direto pela API, mover setup, CAN, firmware, flash, validacao final, auditoria de host, horas de impressao, backup e build de firmware para jobs do agente. O job `remote_host_script` executa scripts controlados gerados pelo backend no host pareado; os demais fluxos continuam usando jobs Moonraker especificos do agente.
Alternativas consideradas: manter fallback direto para ambiente local; exigir VPN/rede privada entre cloud e impressora; manter SSH via API para setup.
Consequencias: a API passa a bloquear quando nao existe agente pareado/online em vez de tentar rede local. Setup de uma placa sem agente exige primeiro instalar/parear um agente na impressora ou em um futuro agente de rede dedicado para descoberta.
Impacto em testes: backend completo, Go completo e busca por chamadas diretas de Moonraker/SSH nas rotas operacionais.
Impacto em rollback: medio; reverter recoloca caminhos diretos e deve ser evitado em ambiente cloud.
Como reverter: reverter esta decisao e os arquivos de agente/backend relacionados; reinstalar agente anterior se necessario.
Referencias: `backend/app/agent_host.py`, `backend/app/routes/printers.py`, `backend/app/routes/setup.py`, `backend/app/routes/backups.py`, `backend/app/routes/firmware.py`, `backend/app/routes/audit.py`, `agent/internal/agent/host.go`.

### DEC-20260531-10 - Navegacao cloud usa frota e detalhe de registro

Status: aceita
Data: 2026-05-31
Contexto: o Printora deixou de ser apenas uma UI local para uma impressora e passou a operar em ambiente web/cloud com varias impressoras e agentes. A navegacao antiga escondia ou expunha secoes com base em uma impressora ativa global, o que nao escala para frota, agentes remotos e usuarios/organizacoes.
Decisao: o menu principal passa a conter somente areas globais independentes de impressora. `Impressoras` e `Agentes` viram listas de frota; operacao, atualizacoes, calibracao, firmware, manutencao, diagnostico/backups e pareamento ficam dentro do detalhe da impressora. Saude, fila, doctor remoto, suporte e credencial ficam dentro do detalhe do agente. A topbar fica fixa e global, sem seletor de impressora e sem acoes especificas de tela; ela mostra titulo, alertas de frota, Sobre, tema e conta do usuario no extremo direito.
Alternativas consideradas: manter grupo `Impressora ativa` no menu; esconder secoes quando a impressora estiver offline; criar rotas separadas para cada tela operacional ainda dependentes de contexto global.
Consequencias: a UI fica coerente com cloud/frota e evita que telas globais desaparecam por falta de impressora. Acoes contextuais passam a ficar no corpo da tela ou aba especifica. A Central de alertas precisa agregar alertas de frota e permitir abrir a impressora afetada.
Impacto em testes: build frontend deve passar e `./check.sh` valida documentacao/governanca. Validacao visual deve abrir menu global, lista de impressoras, detalhe da impressora e detalhe do agente.
Impacto em rollback: baixo a medio; reverter restaura as secoes operacionais no menu lateral e remove `PrinterDetailScreen`/`AgentDetailScreen`.
Como reverter: reverter alteracoes em `frontend/src/app/navigation.ts`, `frontend/src/hooks/usePrintoraApp.ts`, `frontend/src/main.tsx`, telas novas de detalhe e atualizacoes de `TELAS.md`.
Referencias: `frontend/src/app/navigation.ts`, `frontend/src/screens/PrinterDetailScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `frontend/src/screens/PrintersScreen.tsx`, `frontend/src/screens/AgentsScreen.tsx`, `TELAS.md`.

### DEC-20260531-11 - Update de agente usa job remoto direto

Status: substitui a decisão original de fallback por SSH
Data: 2026-05-31
Atualizacao: 2026-06-01
Contexto: o fallback por SSH gerava falha de credencial e contradizia o objetivo cloud: se o agente já está instalado e online, ele deve receber a ação pelo canal do agente e se autoatualizar.
Decisao: a UI e o backend sempre criam `remote_agent_update_check` para o agente ativo, independentemente da versão reportada. O instalador systemd padrão roda o agente como `root` para que o próprio agente consiga trocar `/usr/local/bin/printora-agent` e reiniciar `printora-agent` sem SSH, senha ou ação manual do usuário.
Alternativas consideradas: manter SSH como ponte para agentes antigos; exigir comando manual; usar sudoers específico para o usuário `printora-agent`; criar shell genérico remoto.
Consequencias: o fluxo fica consistente com cloud e usuário leigo. O agente instalado tem privilégio maior no host, limitado pelo contrato de jobs explícitos e sem shell genérico. Hosts antigos instalados sem permissão suficiente podem precisar reinstalação única do serviço para ganhar o novo modelo.
Impacto em testes: `backend/tests/test_agent_support.py` cobre criação direta do job remoto para agente antigo e atual; build frontend valida remoção dos rótulos de SSH/manual.
Impacto em rollback: médio; voltar ao fallback SSH exige restaurar `_request_legacy_update_via_ssh` e rótulos da UI.
Como reverter: reverter alterações em `backend/app/agent_support.py`, instalador do agente, unit systemd e textos da UI/documentação.
Referencias: `backend/app/agent_support.py`, `backend/scripts/install_agent_linux.sh`, `agent/systemd/printora-agent.service`, `frontend/src/screens/AgentsScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `RUNBOOK.md`.

### DEC-20260601-01 - Administracao cloud separa plataforma, impressora e agente

Status: aceita
Data: 2026-06-01
Contexto: a tela antiga de configuracoes misturava update do Printora, diagnostico local do servidor, CAN da impressora e diagnostico do host onde o agente roda. Em cloud isso confunde operador e expõe informacoes que pertencem a outros contextos.
Decisao: manter `settings` como tela global de Administracao, sem releases da plataforma para usuarios comuns. Versao publicada, releases e historico administrativo da plataforma ficam restritos ao usuario de suporte `breno@mayder.com.br`; a operacao de update visivel ao cliente passa a ser por agente. Registro tecnico CAN passa para `Detalhe da impressora > Diagnostico`. Diagnostico de host/dispositivo passa para `Detalhe do agente`, abastecido por doctor remoto do agente, incluindo leitura Raspberry de energia/throttling quando disponivel.
Alternativas consideradas: manter os blocos colapsados em Configuracoes; criar uma tela global de Diagnostico tecnico; esconder os blocos apenas por permissao.
Consequencias: o operador leigo ve menos acoes perigosas no escopo global. Suporte passa a diagnosticar impressora e agente no registro correto. O doctor remoto precisa evoluir junto do agente para ampliar leituras de hardware.
Impacto em testes: build frontend, testes Go do agente e `./check.sh` devem validar a reorganizacao.
Impacto em rollback: baixo; reverter esta decisao devolve os blocos para Settings e remove a leitura Raspberry do doctor.
Como reverter: reverter alteracoes em `frontend/src/screens/SettingsScreen.tsx`, `frontend/src/screens/ReportsScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `agent/internal/agent/doctor.go` e documentacao.
Referencias: `frontend/src/screens/SettingsScreen.tsx`, `frontend/src/screens/ReportsScreen.tsx`, `frontend/src/screens/AgentDetailScreen.tsx`, `agent/internal/agent/doctor.go`, `TELAS.md`.

### DEC-20260609-01 - SAVE_CONFIG fica como acao supervisionada

Status: aceita
Data: 2026-06-09
Contexto: calibrações Klipper como `PID_CALIBRATE` retornam valores úteis no console e pedem `SAVE_CONFIG` para gravar no `printer.cfg` e reiniciar o firmware. O Printora precisa guardar o retorno técnico sem aplicar alterações permanentes automaticamente.
Decisao: o agente captura trecho do `/server/gcode_store` após execuções de calibração e o backend salva esse retorno no histórico. Quando o console indicar `SAVE_CONFIG`, a UI mostra os parâmetros e explica que a configuração ainda precisa ser salva. A aplicação oferece `Salvar config` como ação operacional supervisionada, com preflight e confirmação, mas não dispara esse comando automaticamente a partir do resultado de calibração.
Alternativas consideradas: salvar automaticamente após PID; deixar o usuário ir sempre ao Mainsail; armazenar só uma nota manual. 
Consequencias: o histórico passa a guardar evidência técnica do PID e o operador tem caminho explícito para aplicar valores pendentes, preservando controle humano sobre escrita em arquivo e restart do Klipper.
Impacto em testes: `backend/tests/test_calibration.py` cobre extração do console/PID; `backend/tests/test_operation.py` cobre preview `SAVE_CONFIG`; `go test ./...`, build frontend e `./check.sh` validam o fluxo.
Impacto em rollback: médio; remover a ação `save_config` volta a exigir Mainsail para salvar, mas os históricos já registrados permanecem legíveis como JSON.
Como reverter: reverter alterações em `backend/app/routes/calibration.py`, `backend/app/operation.py`, `agent/internal/agent/moonraker.go`, modais de calibração e manifesto/binário do agente.

### DEC-20260609-02 - Remediacao supervisionada de config incluida

Contexto: em instalacoes Klipper com `[include ...]`, `SAVE_CONFIG` pode falhar com conflito quando a secao/opcao gerenciada esta em arquivo incluido, por exemplo `[extruder] control`. Nesse caso o usuario precisa de um caminho seguro para aplicar os valores calculados sem editar arquivo manualmente.

Decisao: quando houver valores calculados em uma calibracao e o `SAVE_CONFIG` falhar por conflito de include, o Printora oferece uma remediacao supervisionada: o agente varre somente `~/printer_data/config`, considera arquivos `.cfg` e `.conf`, ignora comentarios/backups, lista todas as secoes ativas compatíveis, mostra diff por arquivo e aplica apenas os alvos selecionados pelo usuario. A aplicacao exige autenticacao reforcada, cria backup remoto antes de sobrescrever e reinicia o firmware apos aplicar.

Consequencias: o fluxo continua explicito e auditavel, sem alterar arquivos fora da pasta de configuracao da impressora. A primeira implementacao expõe a remediacao para PID do hotend; o backend aceita secao/opcoes genericas para evoluir para outras calibracoes.

Impacto em testes: `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`.

Como reverter: reverter `backend/app/config_remediation.py`, endpoints de remediacao em `backend/app/routes/calibration.py` e componentes/estado de remediacao no frontend.
Referencias: `backend/app/routes/calibration.py`, `backend/app/operation.py`, `agent/internal/agent/moonraker.go`, `frontend/src/components/modals/CalibrationExecuteModal.tsx`, `frontend/src/components/modals/CalibrationResultModal.tsx`.

### DEC-20260601-03 - Update de agente sem SSH e manifesto derivado do artefato publicado

Status: aceita
Data: 2026-06-01
Contexto: o update do agente deve ser simples para usuario leigo e nao pode depender de SSH salvo como ultimo recurso. O manifesto estatico tambem pode ficar divergente do binario realmente servido, causando falha de SHA-256.
Decisao: o endpoint de update do agente cria job `remote_agent_update_check`, tenta entregar imediatamente via WebSocket e mantém fallback por heartbeat/polling. O manifesto publico do agente recalcula URL e SHA-256 a partir do artefato local publicado em `.artifacts/agent` antes de responder.
Consequencias: a UI deixa de sugerir update por SSH. Se o agente estiver online e suportar o job de update, a acao chega imediatamente; se nao estiver, fica pendente para o proximo contato. Agentes legados que ainda nao suportam `remote_agent_update_check` precisam de uma atualizacao/reinstalacao manual unica para entrar no fluxo novo. Falha real passa a vir do resultado do job ou do relatorio do agente, nao do SSH da impressora.
Como reverter: voltar `backend/app/routes/agents.py`, `backend/app/agent_support.py`, `backend/app/agent_updates.py`, `frontend/src/hooks/domains/usePrinters.ts` e documentacao.

### DEC-20260609-02 - Datas usam timezone do usuario na UI

Status: aceita
Data: 2026-06-09
Contexto: dados persistidos em SQLite usam timestamps UTC/texto sem offset em vários módulos. Somar ou subtrair horas no banco corromperia histórico e criaria divergência entre usuários.
Decisao: adicionar `timezone` em `auth_users` e usar esse valor apenas na camada de formatação do frontend. A regra para datas novas e existentes é manter o valor bruto persistido e converter na UI por `formatDateTime`.
Consequencias: cada usuário vê horários no próprio fuso sem regravar históricos. Novas telas devem usar o formatter centralizado em vez de `new Date(...).toLocaleString(...)` local.
Impacto em testes: schema SQL, testes de auth, build frontend e `./check.sh`.
Impacto em rollback: baixo; remover a coluna volta ao fuso padrão do navegador/servidor, mas históricos permanecem intactos.
Como reverter: reverter `backend/sql/034_auth_user_timezone.sql`, campos de auth e formatter de datas do frontend.

### DEC-20260616-16 - Storage social usa cota antes da escrita e retenção supervisionada

Status: aceita
Data: 2026-06-16
Vigência: válida como política de storage/cota, mas subordinada à DEC-20260618-01; a superfície nova é `Projetos de impressão > Meus projetos`.
Contexto: a biblioteca social passou a aceitar arquivos reais em quarentena. Sem cota e retenção, o crescimento de arquivos ficaria sem controle e uma migração futura para object storage exigiria desfazer acoplamento ao filesystem local.
Decisao: criar uma camada dedicada de storage social com política de cota/custo/retenção, adapter local de caminho seguro e relatório autenticado de uso. O upload verifica cota antes de gravar o objeto local. Retenção gera revisão `dry_run` auditável e não apaga arquivo, linha ou versão automaticamente.
Alternativas consideradas: manter limite fixo de 25 MB por upload; apagar arquivos rejeitados imediatamente; implementar bucket externo já neste pacote.
Consequencias: o custo passa a ser mensurável, o usuário recebe feedback de cota e a operação de limpeza fica reversível/supervisionada. Object storage futuro troca adapter e backfill sem alterar contrato social principal.
Impacto em testes: testes de upload/cota, relatório de storage, revisão de retenção, schema versionado, build frontend e `./check.sh`.
Impacto em rollback: médio; reverter remove relatório e bloqueio de cota, mas arquivos já gravados permanecem no diretório local.
Como reverter: reverter `backend/app/social_storage.py`, `backend/app/routes/social_storage.py`, integração de upload em `social_catalog.py`, painel de biblioteca no frontend e documentação. Se `060_social_file_storage.sql` já tiver sido aplicado, restaurar backup SQLite anterior criado pelo versionador; não executar `DELETE` ou `DROP TABLE` sem confirmação explícita.

### DEC-20260616-17 - Fatiamento usa CLI externa controlada sem UI embutida

Status: aceita
Data: 2026-06-16
Vigência: válida como regra de engine controlada, mas subordinada à DEC-20260618-01; fatiamento real diário deve partir de projeto de impressão.
Contexto: o Printora precisa iniciar integração com engine de fatiamento sem transformar o produto em uma tela embutida do OrcaSlicer/PrusaSlicer nem executar comandos reais antes de perfil, impressora e material estarem compatíveis.
Decisao: a primeira ponte suporta OrcaSlicer/PrusaSlicer por CLI detectada no host ou agente, com configuração opcional por `PRINTORA_SLICER_ENGINE_PATH`. O backend expõe somente detecção, versão e dry-run de worker isolado; fatiamento real permanece bloqueado até o pipeline rastreável validar projeto/item legado, perfil, impressora e material.
Alternativas consideradas: embutir a UI do fatiador em iframe/webview; chamar qualquer binário configurado livremente; iniciar geração real de G-code no primeiro pacote.
Consequencias: a integração fica simples, auditável e reversível. O usuário recebe bloqueio claro quando a engine não está instalada, e os próximos pacotes podem acoplar jobs/artefatos sem refazer o contrato.
Impacto em testes: `backend/tests/test_slicing.py`, build frontend, schema versionado e `./check.sh`.
Impacto em rollback: baixo a médio; reverter remove endpoints e painel de engine, mas tabelas já aplicadas permanecem sem afetar impressoras, agentes ou arquivos.
Como reverter: reverter `backend/app/slicing.py`, `backend/app/routes/slicing.py`, integração em `backend/app/main.py`, painel de Administração e documentação. Se `061_slicing_engine_bridge.sql` já tiver sido aplicado e precisar desfazer schema, restaurar backup SQLite anterior criado pelo versionador; não executar `DROP TABLE` sem confirmação explícita.

### DEC-20260616-18 - Jobs de fatiamento persistem artefatos antes de qualquer envio

Status: substituida
Data: 2026-06-16
Substituida por: DEC-20260618-01. Vigência residual: tabelas de job/artefato podem ser reaproveitadas, mas novos jobs diários devem nascer do projeto de impressão com snapshot imutável.
Contexto: o fatiamento precisava ser rastreável por item/modelo legado, perfil, impressora e usuário antes de qualquer preflight ou envio para Moonraker. No desenho substituído, isso evolui para projeto de impressão com snapshot imutável. Sem job persistido, erro de engine, incompatibilidade de volume e artefatos gerados ficariam soltos.
Decisao: criar `slicing_jobs` e `slicing_job_artifacts` como trilha do pipeline. O job começa planejado, pode ser executado/cancelado e só conclui quando o worker registra artefatos. Se a engine não estiver configurada, o job falha com log acionável em vez de criar G-code simulado.
Alternativas consideradas: reaproveitar apenas logs de dry-run; gravar G-code direto no filesystem sem linha de job; acoplar fatiamento ao envio para a impressora.
Consequencias: preflight e envio seguro passam a ter uma origem rastreável. O banco recebe tabelas aditivas e rollback estrutural deve restaurar backup SQLite em vez de remover dados manualmente.
Impacto em testes: `backend/tests/test_slicing_pipeline.py`, schema versionado, build frontend e `./check.sh`.
Impacto em rollback: médio; reverter remove API/UI do pipeline, mas jobs já criados permanecem no SQLite se o SQL tiver sido aplicado.
Como reverter: reverter `backend/app/slicing_pipeline.py`, endpoints de jobs em `backend/app/routes/slicing.py`, painel de pipeline no frontend e documentação. Se `062_slicing_jobs.sql` já tiver sido aplicado e precisar desfazer schema, restaurar backup SQLite anterior criado pelo versionador; não executar `DROP TABLE` sem confirmação explícita.

### DEC-20260616-19 - Preflight de impressão separa análise local e estado remoto

Status: aceita
Data: 2026-06-16
Contexto: G-code gerado por fatiamento precisa ser validado antes de qualquer envio para impressora. A análise do arquivo é local e reproduzível, mas o estado real da impressora depende do agente/Moonraker no momento do envio.
Decisao: persistir `print_preflight_checks` com metadados locais do G-code e, quando houver agente ativo, vincular um job `remote_gcode_preflight`. O preflight só fica aprovado quando não há blockers locais e o agente confirma `can_execute=true`, sem impressão em andamento.
Alternativas consideradas: validar apenas o G-code local; delegar todo preflight ao agente; acoplar preflight diretamente ao envio seguro.
Consequencias: PKG-73 pode exigir preflight aprovado e recente antes de salvar ou iniciar impressão. Ambientes sem agente continuam bloqueados com diagnóstico claro e checklist preservado.
Impacto em testes: `backend/tests/test_print_preflight.py`, fixture G-code, schema versionado, build frontend e `./check.sh`.
Impacto em rollback: médio; reverter remove API/UI de preflight, mas registros aplicados permanecem no SQLite se o script já rodou.
Como reverter: reverter `backend/app/print_preflight.py`, endpoints de preflight em `backend/app/routes/slicing.py`, painel de preflight no frontend e documentação. Se `063_print_preflight_checks.sql` já tiver sido aplicado e precisar desfazer schema, restaurar backup SQLite anterior criado pelo versionador; não executar `DROP TABLE` sem confirmação explícita.

### DEC-20260617-20 - Envio de G-code usa entrega auditada e upload remoto pelo agente

Status: aceita
Data: 2026-06-17
Contexto: depois do preflight aprovado, o Printora precisa salvar ou iniciar impressão sem expor G-code bruto no frontend, sem enviar para impressora errada e com rollback operacional quando o arquivo ainda não foi impresso.
Decisao: persistir `print_gcode_deliveries` como trilha de entrega e usar jobs de agente `remote_gcode_upload` e `remote_gcode_delete`. A entrega exige preflight aprovado e recente; iniciar impressão exige confirmação textual ou step-up válido. O agente reexecuta preflight remoto antes do upload e envia o arquivo por multipart para Moonraker.
Alternativas consideradas: enviar cada linha por `/printer/gcode/script`; acoplar envio diretamente ao preflight; salvar arquivo remoto sem auditoria dedicada.
Consequencias: o envio fica rastreável por usuário, impressora, job, preflight e checksum. O rollback automático só remove arquivo salvo sem impressão iniciada; impressão iniciada continua dependendo de ação operacional no Moonraker/Klipper.
Impacto em testes: `backend/tests/test_print_delivery.py`, testes Go do agente, build frontend, schema versionado e `./check.sh`.
Impacto em rollback: médio; reverter remove API/UI/agent jobs de entrega, mas registros aplicados permanecem no SQLite se o script já rodou.
Como reverter: reverter `backend/app/print_delivery.py`, endpoints de entrega em `backend/app/routes/slicing.py`, jobs `remote_gcode_upload`/`remote_gcode_delete` no agente, painel de entrega no frontend e documentação. Se `064_print_gcode_deliveries.sql` já tiver sido aplicado e precisar desfazer schema, restaurar backup SQLite anterior criado pelo versionador; não executar `DROP TABLE` ou remoção manual de arquivos sem confirmação explícita.
