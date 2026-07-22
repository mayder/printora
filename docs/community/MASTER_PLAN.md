# Plano Diretor Da Comunidade E Fabricação 3D

## Objetivo

Transformar o Printora, ao longo de vários anos, em uma infraestrutura comunitária aberta que conecte pessoas, conhecimento, modelos, materiais, impressoras, escolas, oficinas, criadores e necessidades sociais. A comunidade não deve ser uma cópia genérica de rede social: deve converter interação em aprendizado, fabricação segura, reparo, autonomia, renda local, inclusão e redução de desperdício.

O plano preserva o diferencial já existente do produto: operação segura de impressoras Klipper/Moonraker, histórico técnico, projetos, biblioteca 3D e uma camada social isolada das permissões operacionais.

## Resultado da auditoria de julho de 2026

### Já existe e deve ser evoluído, não duplicado

- autenticação, conta, perfil público e slug;
- impressoras públicas vinculadas ao inventário e catálogo canônico;
- comunidades automáticas por fabricante, modelo e variante;
- follow, amizade, bloqueio e visibilidade básica;
- feed técnico por comunidade;
- posts, comentários, respostas, reações e solução marcada;
- biblioteca STL/3MF, upload em quarentena, análise e thumbnail;
- autoria, licença, versão, remix, favoritos, coleções e listas de impressão;
- perfis técnicos, material e fatiamento compartilháveis;
- busca, tags, recomendações e reputação iniciais;
- denúncias, fila de moderação, notificações e antiabuso básico;
- cotas, retenção, importação externa e armazenamento local;
- projetos de impressão, publicação, conteúdo premium, slicing, preflight, entrega e histórico;
- arquivos G-code, preview e ponte entre projeto e operação.

### Existe parcialmente

- comunidade: hoje é majoritariamente derivada do catálogo; faltam grupos por finalidade, território, instituição e iniciativa;
- perfil: existe identidade pública, mas falta portfólio completo, papéis contextuais, credenciais e presença profissional;
- feed: existe dentro de comunidade, mas falta feed pessoal controlável, listas, modo foco e explicação item a item;
- publicação: existe discussão técnica, mas falta editor rico, tutorial passo a passo, vídeo, live e coautoria;
- biblioteca: existe base funcional, mas faltam conjuntos, CAD nativo, dependências, diff geométrico e preservação;
- visualização: existe análise inicial, mas falta inspeção técnica avançada, corte, medição, anotações e comparação;
- slicing e impressão: existem pipelines, mas faltam experiência avançada, experimentos, fazendas, filas coletivas e QA por lote;
- creator economy: há publicação comercial inicial, mas faltam assinaturas, studio, CRM, pedidos, logística e proteção econômica madura;
- segurança social: existe base, mas faltam proteção infantil, proveniência multimídia, recursos de decisão e operação global multilíngue;
- mobile e acessibilidade: há responsividade pontual, mas ainda não existe produto mobile/offline nem programa contínuo de acessibilidade.

### Ausências estruturais mais relevantes

- tecnologia assistiva com validação, consentimento, acompanhamento e especialistas;
- resposta humanitária e coordenação de capacidade local;
- escolas, bibliotecas, makerspaces, turmas e aprendizagem estruturada;
- reparo, peças de reposição, passaporte de produto e economia circular;
- coautoria, equipes, tarefas, revisão e merge de projetos;
- mensagens, chats, eventos, lives e presença;
- fabricação local, cotação, qualidade, cadeia de custódia e pagamento por marco;
- ciência aberta, datasets, replicação e ética;
- PWA offline, captura em campo e sincronização resiliente;
- métricas públicas de impacto social e ambiental.

## Cobertura do inventário

O catálogo gerado contém 440 capacidades em 55 frentes. Cada capacidade foi decomposta em sete entregas independentes:

1. regra e contrato de produto;
2. tela e fluxo;
3. mobile, PWA e conectividade limitada;
4. acessibilidade;
5. confiança, privacidade, segurança e moderação;
6. métrica de impacto;
7. teste, piloto e evidência de qualidade.

Isso resulta em 3.080 itens atômicos. O catálogo de telas contém 440 famílias e exige pelo menos três estados separados por família: lista/descoberta, detalhe e cadastro/edição, totalizando 1.320 estados principais antes de modais e estados excepcionais.

## Princípios de produto

### Benefício humano antes de engajamento

- não otimizar rolagem infinita, notificações ou recompensa apenas para aumentar tempo de tela;
- priorizar resolução confirmada, aprendizado, impressão bem-sucedida, reparo, autonomia, renda justa e desperdício evitado;
- permitir feed cronológico, desligamento de recomendação e modo foco;
- tornar promoção, patrocínio e recomendação explicáveis.

### Segurança física e digital integrada

- arquivo publicável não é automaticamente seguro para qualquer uso;
- peça médica, infantil, estrutural, elétrica, alimentar ou de emergência precisa de classificação e gates próprios;
- relação social nunca concede controle sobre impressora;
- comando físico remoto continua exigindo preflight, confirmação e trilha operacional;
- conteúdo, modelos e artefatos distribuídos precisam de proveniência e versão.

### Comunidade como conhecimento reproduzível

- todo resultado técnico deve poder apontar para projeto, versão, perfil, material, impressora compatível e evidência física;
- perguntas devem preservar solução, contexto e versões afetadas;
- tutoriais devem ter materiais, ferramentas, etapas, riscos e resultado;
- edição e tradução preservam histórico e autoria.

### Local-first quando possível

- permitir uso local e cloud sem transformar telemetria doméstica em conteúdo social;
- processar mídia, visão computacional e dados sensíveis localmente quando possível;
- oferecer exportação aberta e evitar aprisionamento;
- suportar PWA e tarefas offline em oficinas e escolas.

## Arquitetura de informação alvo

### Navegação global desktop

- Início: visão pessoal, retomadas, impacto e alertas sociais relevantes.
- Descobrir: projetos, modelos, posts, pessoas, comunidades, eventos e oficinas.
- Comunidades: espaços seguidos, canais, fóruns, chat, wiki e decisões.
- Projetos: explorar, meus projetos, equipes, salvos, listas, slicing e trabalhos.
- Fabricar: filas, impressoras, fazendas, pedidos e controle de qualidade.
- Aprender: trilhas, aulas, mentores, escolas e certificados.
- Impacto: reparo, sustentabilidade, assistência, iniciativas e indicadores.
- Criar/Vender: studio, publicação, assinaturas, marketplace e pedidos.
- Caixa de entrada: mensagens, solicitações, comentários e notificações.
- Conta: perfil, privacidade, segurança, acessibilidade, integrações e dados.

### Navegação mobile

- barra inferior com `Início`, `Descobrir`, `Criar`, `Projetos` e `Conta`;
- comunidades, mensagens e alertas acessíveis em segundo nível curto;
- ação `Criar` abre seletor contextual: post, projeto, make, pergunta, evento, pedido ou medição;
- operação crítica da impressora não fica escondida dentro de conteúdo social;
- controles primários ficam no alcance do polegar e não dependem de hover;
- rascunho, upload e coleta de evidência suportam retomada e conectividade limitada.

### Estrutura de uma capacidade

Cada família do catálogo de telas deve separar:

- lista/descoberta: busca, filtros, ordenação, paginação, estado vazio e ação de entrada;
- detalhe: contexto, histórico, evidência, relações, permissão e ações próprias;
- cadastro/edição: formulário por etapas, validação, salvamento, revisão e cancelamento;
- administração, quando aplicável: fila, política, auditoria e rollback, separada do uso diário.

## Padrões obrigatórios de layout e usabilidade

### Hierarquia e densidade

- uma ação principal clara por estado;
- informação crítica antes de métricas de popularidade;
- cards para descoberta visual; tabelas apenas quando comparação densa justificar;
- modo compacto para operação/fazenda e modo confortável para leitura/aprendizagem;
- cabeçalhos sticky somente quando não roubarem espaço útil;
- breadcrumbs em fluxos profundos e retorno que preserve filtros e posição.

### Formulários

- dividir formulários longos por objetivo, não por estrutura do banco;
- salvar rascunho automaticamente e mostrar o que ainda falta;
- validar perto do campo e resumir erros no topo para leitor de tela;
- oferecer preview antes de publicar, vender, enviar ou comandar;
- preservar entrada após falha de rede;
- nunca depender de placeholder como rótulo.

### Estados

Toda tela aplicável deve definir:

- carregando com skeleton coerente;
- vazio com explicação e próxima ação;
- erro acionável com retry seguro;
- parcial quando uma fonte falhar;
- offline/cached com idade do dado;
- sem permissão com motivo não enumerável;
- conflito de edição/sincronização;
- sucesso persistente o bastante para confirmação;
- conteúdo removido, moderado, arquivado e mesclado.

### Acessibilidade

- WCAG como piso, não como substituto de teste com pessoas;
- teclado, leitor de tela, zoom 400%, contraste, foco visível e redução de movimento;
- alternativa a gráficos, mídia, cor, gesto e visualização 3D;
- legendas, transcrição, audiodescrição e linguagem simples;
- tamanho de alvo adequado e suporte a switch/voz;
- preferências acessíveis sincronizadas sem impedir uso anônimo.

## Priorização por impacto social

### P0 — proteção da vida, autonomia e confiança básica

Tecnologia assistiva; segurança de modelos; resposta humanitária; proteção infantil; integridade; privacidade; segurança da plataforma; moderação.

Nenhum P0 deve ser lançado amplamente sem especialista, revisão independente, piloto controlado, métrica de dano, rollback e canal de incidente.

### P1 — acesso, educação, sustentabilidade e infraestrutura social

Acessibilidade; mobile/offline; educação; escolas/makerspaces; reparo; sustentabilidade; fabricação local; qualidade; onboarding; design system; internacionalização.

### P2 — núcleo comunitário e fabricação conectada

Comunidades avançadas; mensagens; eventos; colaboração; conhecimento; feed; busca; recomendações; identidade; grafo; publicação; mídia; biblioteca; viewer; parametrização; slicing; impressão; fazendas; visão computacional; materiais; manutenção; integrações; plataforma de desenvolvedor; analytics.

### P3 — economia de criadores e crescimento sustentável

Studio; assinaturas; marketplace; logística; reputação; concursos; crowdfunding; organizações; ciência aberta.

### P4 — apostas experimentais

AR/scan; copilotos e automação; interfaces futuras. Só avançam depois que dependências P0/P1 estiverem maduras e houver hipótese de benefício comprovável.

## Fases plurianuais

### Fase 0 — fundação mensurável

- design system e acessibilidade contínua;
- arquitetura mobile/PWA;
- telemetria com consentimento e indicadores de impacto;
- proveniência, segurança, moderação e proteção infantil;
- decomposição dos arquivos grandes atuais antes de ampliar a UI social.

### Fase 1 — comunidade útil diariamente

- feed pessoal controlável;
- grupos por finalidade e território;
- chat, inbox, eventos e onboarding comunitário;
- publicação rica, tutorial, makes e colaboração;
- busca multimodal e conhecimento estruturado.

### Fase 2 — fabricação e aprendizagem em rede

- escolas/makerspaces, trilhas, mentoria e certificados;
- equipes de projeto e revisão;
- materiais, QA, fazendas e filas compartilhadas;
- reparo e passaporte de produto;
- integrações e API pública.

### Fase 3 — impacto social coordenado

- tecnologia assistiva com governança especializada;
- fabricação local e cadeia de custódia;
- resposta humanitária offline;
- sustentabilidade comparável;
- ciência aberta e indicadores públicos.

### Fase 4 — economia e escala

- clubes e assinaturas;
- marketplace digital/físico;
- pedidos, logística, disputa e pós-venda;
- crowdfunding e programas institucionais;
- expansão internacional e operação de confiança multilíngue.

### Fase 5 — experimentação responsável

- scanning, AR, assistência por IA e interfaces espaciais;
- gates de valor, segurança, acessibilidade, custo e privacidade antes de adoção.

## Métricas norteadoras

### Sociedade

- pessoas que ganharam autonomia com solução assistiva segura;
- reparos concluídos e vida útil ampliada;
- estudantes e educadores que concluíram competências práticas;
- demanda local atendida e renda distribuída;
- capacidade humanitária preparada e tempo de resposta;
- participação de grupos historicamente excluídos.

### Fabricação

- taxa de sucesso na primeira tentativa;
- falhas detectadas ou evitadas;
- material, energia e horas desperdiçadas;
- reprodutibilidade por versão/perfil;
- não conformidades e tempo até contenção;
- disponibilidade e confiabilidade da frota.

### Comunidade

- perguntas resolvidas e confirmadas;
- tempo até primeira contribuição útil;
- diversidade de criadores descobertos;
- retenção saudável sem aumento artificial de tempo de tela;
- carga e qualidade da moderação;
- recursos procedentes e decisões revertidas corretamente.

## Riscos e controles

- **Escopo infinito:** executar uma frente por problema validado e pacote pequeno, sem prometer o catálogo inteiro de uma vez.
- **Rede social viciante:** feed cronológico, modo foco, limites, explicação e ausência de dark patterns.
- **Dano físico:** classificação de risco, especialista, evidência, alerta e recall.
- **Vazamento doméstico:** separar social/operação, ocultar localização e processar localmente quando possível.
- **Monetização predatória:** taxas claras, cancelamento fácil, recurso, disputa e proteção a pequenos criadores.
- **IA opaca:** fontes, confiança, revisão humana, opt-out e medição de erro.
- **Moderação desigual:** operação por idioma/região, auditoria, recurso e relatório de transparência.
- **Arquitetura frágil:** contratos versionados, filas assíncronas, isolamento de mídia, busca e pagamentos, observabilidade e rollback.

## Critério de conclusão desta meta de planejamento

- estado atual auditado contra código e documentação;
- benchmark registrado com fontes oficiais;
- frentes, capacidades, telas e itens atômicos gerados;
- prioridade por impacto social definida;
- layout, usabilidade, mobile, acessibilidade, segurança e métricas incorporados a cada capacidade;
- fontes oficiais do repositório apontando para o programa;
- geração reproduzível e checks do repositório aprovados.
