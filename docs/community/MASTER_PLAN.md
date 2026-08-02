# Plano Diretor Enxuto Do Printora

## Objetivo

Evoluir o Printora como ferramenta de projetos, fatiamento, operação,
diagnóstico e manutenção de impressoras 3D. Conhecimento comunitário existe
para tornar resultados técnicos reproduzíveis, não para criar uma rede social
genérica.

## Problemas Prioritários

1. configurar impressora e agente com menos erro;
2. organizar projeto, arquivos, variantes, material e perfil;
3. reproduzir o fatiamento;
4. executar preflight e entrega segura;
5. acompanhar o trabalho e a impressora corretos;
6. registrar resultado, consumo e falha;
7. diagnosticar recorrência e planejar manutenção;
8. operar várias impressoras e ferramentas externas sem perder contexto.

## Capacidades Já Existentes

O produto já possui bases que devem ser caracterizadas e evoluídas:

- autenticação, conta, autorização, step-up e rate limit;
- cadastro de impressoras, agentes e integração Moonraker;
- health check, snapshots, auditoria, backup e relatórios;
- manutenção, calibração, Z-offset, CAN, firmware e updates;
- projetos de impressão, upload, quarentena, versão e biblioteca;
- perfis técnicos, slicing, preflight, entrega e histórico;
- arquivos G-code, preview e operação;
- busca, publicação técnica, moderação e notificações básicas;
- múltiplas impressoras e integração externa controlada.

Pacote novo não pode duplicar essas bases.

## Portfólio Ativo

O backlog executável está em `DEMANDAS.md`. O estado de todos os IDs
`PKG-101` a `PKG-155` está em `PACKAGE_PORTFOLIO.csv`.

Frentes ativas:

1. proteção essencial;
2. onboarding operacional;
3. materiais, spools e qualidade;
4. conhecimento e evidência;
5. projetos, biblioteca e inspeção;
6. fatiamento reproduzível;
7. fluxo ponta a ponta de impressão;
8. manutenção e confiabilidade;
9. frota e filas;
10. captura guiada de objeto por fotos;
11. integrações e descoberta técnica;
12. reconstrução 3D multiview;
13. qualificação e entrega de modelo imprimível.

## Inventário Histórico

`COMMUNITY_BACKLOG.*`, `COMMUNITY_SCREENS.*`, `PRIORITIES.md` e
`SUMMARY.json` preservam o levantamento amplo de julho de 2026:

- 55 frentes;
- 440 capacidades;
- 3.080 requisitos;
- 440 famílias de tela.

Esses números representam possibilidades geradas, não necessidade validada,
dependência, prioridade ou cobertura obrigatória. Rotas e telas desse
inventário são hipóteses arquivadas.

## Funcionalidades Fora Do Núcleo

Permanecem fora do backlog ativo:

- feed pessoal, grafo social, chat e eventos;
- educação formal, escolas e certificados;
- marketplace, pagamentos, assinaturas, CRM e logística;
- crowdfunding, concursos e reputação gamificada;
- tecnologia assistiva clínica e resposta humanitária;
- realidade aumentada, wearables e interfaces imersivas;
- recomendação algorítmica e analytics social;
- contas infantis.

Funcionalidade já existente não é apagada por esta decisão. Expansão futura
depende de problema comprovado e nova decisão.

## Ideias Adiadas

Internacionalização, customização paramétrica, coautoria e API pública
permanecem registradas, mas sem autorização de implementação. Visão
computacional e assistência por IA também permanecem adiadas fora do fluxo
delimitado de captura/reconstrução aprovado em `PKG-141`, `PKG-153` e `PKG-154`.
Para reativar outra ideia é obrigatório:

1. identificar usuário e problema;
2. medir baseline;
3. definir hipótese e critério de parada;
4. estimar custo operacional e risco;
5. provar que o núcleo não resolve o problema;
6. atualizar portfólio, arquitetura, backlog e testes.

## Princípios

- benefício operacional antes de volume de funcionalidades;
- segurança física antes de automação;
- fonte canônica e estado real antes de cache;
- projeto e revisão imutáveis para reprodução;
- relação social nunca concede comando físico;
- integração externa com timeout, quota e rollback;
- privacidade e acessibilidade como gates transversais;
- nenhuma tela criada apenas para satisfazer inventário.

## Medidas De Sucesso

- tempo até impressora conectada;
- taxa de preflight concluído sem bypass;
- impressão concluída e falha evitada;
- reimpressão reproduzível;
- tempo até diagnóstico acionável;
- recorrência de falha;
- disponibilidade da impressora;
- divergência entre estado exibido e estado real;
- consumo previsto versus realizado;
- incidentes de autorização, perda ou duplicidade.

Métrica sem decisão associada não justifica coleta.

## Rollout

Cada pacote ativo:

- começa por caracterização;
- entrega lotes pequenos;
- mantém N/N-1 quando necessário;
- usa SQL idempotente, nunca migration;
- valida a superfície real;
- possui rollback sem apagar dados;
- fecha com `./check.sh` e commit exclusivo.
