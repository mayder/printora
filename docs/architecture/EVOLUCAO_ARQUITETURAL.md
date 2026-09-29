# Evolução Arquitetural Do Printora

## Objetivo

Evoluir o Printora em quatro etapas sem interromper os fluxos publicados, sem
perder dados e sem manter caminhos legados depois de cada transição. A solução
alvo deve executar integralmente no servidor atual, atrás do Nginx existente,
sem depender de Kubernetes, segundo runtime ou infraestrutura gerenciada. Cópia
externa de backup e integrações de negócio inevitáveis, como pagamento e frete,
não executam o Printora e precisam de adapter, timeout, idempotência e fallback.

Este documento detalha os pacotes executáveis `PKG-86` a `PKG-95`. O programa
comunitário define o que o produto poderá fazer; estes pacotes criam a base
técnica para isso sem transformar o monólito atual em um conjunto prematuro de
microsserviços.

## Estado De Partida Comprovado

- backend FastAPI em um processo Uvicorn, na porta interna `8069`;
- frontend React/Vite entregue pelo mesmo release;
- persistência principal SQLite e arquivos no diretório compartilhado;
- sessões de agentes e entrega imediata de jobs mantidas em memória do processo;
- Nginx, systemd, Python 3.12 e virtualenv no servidor atual;
- deploy troca o symlink `current` e reinicia o único processo;
- Docker e Node não estão disponíveis para o usuário de deploy;
- módulos e telas centrais já concentram responsabilidades e arquivos grandes;
- testes existentes são amplos, mas cobertura mínima ainda não é gate obrigatório.

## Invariantes Obrigatórios

1. Nenhum lote troca tecnologia antes de inventariar produtores, consumidores,
   dados, configurações, jobs, arquivos, testes, documentação e rollback.
2. Toda alteração de banco é entregue como SQL idempotente em `backend/sql/`;
   migrations de framework continuam proibidas.
3. Um banco ou caminho antigo só é aposentado após reconciliação integral,
   período de observação e autorização explícita para a limpeza destrutiva.
4. A compatibilidade temporária tem data, owner e teste de remoção. Ela é
   eliminada no mesmo pacote; não vira arquitetura permanente.
5. O fechamento de cada pacote exige busca automatizada por referências antigas
   em runtime, configuração, dependências, workflow, docs e testes.
6. Um cutover não pode perder nem duplicar operação confirmada. Escritas usam
   idempotency key, transação, outbox e reconciliação quando aplicável.
7. Deploy e cutover usam instâncias azul/verde, health/readiness, drenagem e
   troca atômica do upstream Nginx. Reiniciar primeiro e testar depois deixa de
   ser fluxo aceitável.
8. Todo rollback preserva as escritas feitas após o cutover. Restaurar snapshot
   antigo sobre produção não é rollback válido.
9. Dados sensíveis não aparecem em logs, métricas, traces, filas ou relatórios.
10. Toda retenção de log, evento, auditoria, cache, artefato e backup possui
    rotina de limpeza testada.
11. Todos os serviços cabem no orçamento medido de CPU, RAM, disco, I/O e file
    descriptors do servidor atual. O pacote bloqueia antes do cutover quando
    não houver folga comprovada.
12. O agente, Moonraker e impressões em andamento não dependem da continuidade
    do processo cloud. Uma publicação nunca reinicia Klipper ou Moonraker.
13. Release é imutável: código, frontend, virtualenv, lockfile e unit apontam
    para o mesmo diretório versionado. Blue e green nunca compartilham venv
    mutável nem dependem do symlink `current` durante a execução.
14. Alterações de schema seguem expandir/migrar/contrair. O release anterior e
    o candidato precisam operar simultaneamente durante a drenagem; mudança
    incompatível só é contraída depois que nenhum processo antigo permanece.
15. Eventos, webhooks e jobs possuem schema versionado, idempotency key,
    deduplicação, ordenação quando necessária e consumidor compatível com N/N-1.
16. Segredos ficam fora do release, com usuário/role mínimo, rotação e teste de
    revogação. PostgreSQL, Redis e storage não ficam expostos à Internet.
17. Logs, WAL, backups, objetos, dead-letter e temporários possuem quota,
    monitoramento de disco cheio, retenção e limpeza que não apaga dado vigente.
18. O perfil cloud e o perfil local são produtos suportados distintos. A
    migração cloud remove SQLite de todo caminho cloud; SQLite local só pode
    permanecer em módulo/empacotamento explicitamente local, sem fallback cloud,
    import cruzado ou configuração ambígua.

## Limite Da Garantia No Servidor Atual

Duas instâncias do app, processos workers e redundância de serviços no mesmo
host protegem contra falha de processo e permitem deploy sem indisponibilidade
observável. Eles não protegem contra perda de energia, kernel, disco, rede ou
falha física do host. O programa entrega backup verificável, restauração e
recuperação; alta disponibilidade contra perda total do servidor exigiria outro
host e fica fora da restrição atual. Para sobreviver à perda do host, pelo menos
uma cópia criptografada e restaurável do backup/WAL precisa ficar fora dele. Isso
não move a execução da aplicação: todos os serviços continuam no servidor atual.

Há duas garantias diferentes:

- migração/deploy: nenhuma escrita confirmada pode ser perdida; alvo RPO zero;
- desastre físico do host: RPO/RTO são medidos e limitados pelo envio de WAL e
  backup externo; RPO zero físico exigiria réplica síncrona em outro host.

## Arquitetura Alvo No Mesmo Servidor

```text
Cloudflare
   |
Nginx -> app blue :8069 / app green :8070
             |          |
             +----------+
                 |
       monólito modular FastAPI
          |       |       |
     PostgreSQL  Redis   storage S3-compatible
          |
   fila transacional + workers systemd
          |
  busca/indexação e processamento assíncrono
```

- PostgreSQL é a única fonte relacional autoritativa do perfil cloud após a transição.
- Redis guarda apenas dados recomponíveis: cache, limites, presença, pub/sub e
  coordenação curta; nunca é a única fonte de dado de negócio.
- A fila durável usa PostgreSQL com lock concorrente e outbox transacional,
  evitando adicionar um broker separado ao host antes de necessidade medida.
- Armazenamento de objetos usa contrato S3 compatível em serviço no host, com
  checksum, quarentena, versionamento e backup; paths locais antigos deixam de
  ser contrato público ou fonte autoritativa.
- Busca textual inicial usa PostgreSQL. Índices especializados só entram quando
  carga, relevância ou busca geométrica justificarem processo separado.
- Serviços são units systemd com usuário restrito, limites, health check,
  restart controlado, logs estruturados e retenção.
- A implementação S3-compatible só é escolhida no PKG-90 após prova de licença,
  suporte systemd sem Docker, consumo de recursos, upgrade, backup, restore,
  checksum, versionamento, segurança e rollback. O contrato não autoriza criar
  um serviço caseiro de armazenamento.

## Pré-condições Do Servidor Atual

Antes do primeiro lote remoto, `PKG-86` deve comprovar:

- acesso controlado a Nginx/systemd, criação de usuários/units e portas locais;
- capacidade de instalar PostgreSQL, Redis e o storage escolhido sem Docker;
- duas portas de app, socket/porta de métricas e diretórios com ownership correto;
- espaço para duas releases, snapshot, import, WAL, objetos e rollback simultâneos;
- backup externo criptografado e credencial de restore disponível;
- firewall permitindo apenas Nginx público; bancos/cache/storage em loopback ou socket;
- relógio/NTP, certificados, DNS, limites, logrotate/journald e alertas de disco;
- uma janela de rollback e um responsável humano alcançável durante cada cutover.

Se qualquer item falhar, o programa fica bloqueado antes de instalar ou migrar.

## Estratégia Universal De Transição

Cada migração de tecnologia segue a mesma máquina de estados:

1. **Inventário**: mapear schema, volumes, checksums, referências e SLO atual.
2. **Base paralela**: instalar o destino no host sem receber tráfego produtivo.
3. **Carga inicial**: snapshot consistente, import idempotente e validação.
4. **Captura incremental**: outbox/watermark cobre alterações após o snapshot.
5. **Leitura sombra**: comparar origem e destino sem responder pelo destino.
6. **Canário**: pequena parcela ou domínio não crítico lê o destino.
7. **Cutover**: drenar operações, reconciliar watermark e trocar atomicamente.
8. **Observação**: medir erro, latência, fila, divergência e recursos.
9. **Remoção da ponte**: apagar dual-read/dual-write, flags e adapters temporários.
10. **Erradicação legada**: remover código, pacote, env, unit, arquivo, tabela,
    path, workflow, teste e documentação antigos após autorização destrutiva.
11. **Prova final**: busca por referência, testes, carga, restauração e smoke real.

Dual-write não pode ser feito por duas gravações independentes no request. A
escrita autoritativa e o evento de replicação devem confirmar na mesma transação;
o consumidor é idempotente e reconciliável.

Para SQLite -> PostgreSQL, a ponte segura é explícita:

1. release A introduz ports de persistência e outbox SQLite, continuando em SQLite;
2. replicador idempotente preenche PostgreSQL e leitura sombra mede divergência;
3. release B, já compatível com PostgreSQL, é colocado em green e validado;
4. o watermark é reconciliado e o tráfego troca para B/PostgreSQL;
5. rollback de código volta para um release PostgreSQL-compatible, nunca para
   binário que só entenda SQLite e nunca para snapshot anterior;
6. release C remove adapter, replicador e configuração cloud SQLite dentro do
   mesmo pacote, após observação e aprovação da limpeza física.

No deploy blue/green, cada release possui venv e frontend próprios. Nginx testa
a configuração antes do reload; o candidato passa readiness e smoke privado;
o upstream troca atomicamente; a instância antiga entra em drain, deixa de
aceitar conexão nova e só encerra após requests/jobs protegidos concluírem.
WebSockets longos recebem sinal de reconnect com jitter e retomam por sessão/job
durável. Entrega ao agente exige ack/deduplicação para não perder nem repetir job.

Workers seguem o mesmo protocolo: candidato inicia pausado, valida dependências,
assume leases somente após o cutover, e workers antigos drenam antes da contração
de schema/evento. Um worker morto não pode manter lease infinito.

## Prova De Integridade De Dados

O cutover exige relatório assinado pelo release contendo:

- contagem por tabela, estado e tenant/owner;
- menor/maior ID, sequences e chaves naturais;
- checksum por lotes ordenados e checksum de objetos;
- quantidade e lista explicada de nulos, órfãos e violações de chave;
- amostras semânticas dos fluxos P0/P1;
- watermark final da captura incremental e fila zerada;
- reconciliação de jobs, pagamentos, arquivos, permissões e auditoria;
- teste de escrita/leitura após cutover;
- backup restaurado em ambiente isolado e comparado;
- nenhum registro perdido ou duplicado sem justificativa formal.

## Prova De Erradicação Legada

Cada pacote mantém um manifesto de termos e artefatos aposentados. O gate final
falha se `rg`, análise de imports, configuração efetiva, dependências, units ou
rotas encontrarem referência não autorizada. Exceções só podem existir em
histórico Git e em um registro de decisão que descreva a transição concluída.

Para a troca do banco cloud, a meta final é não haver SQLite no runtime cloud,
deploy, env, units, dependências cloud, SQL cloud ativo, testes cloud, scripts,
workflows ou docs operacionais cloud. O modo local/offline continua suportado
somente em módulo e empacotamento próprios; não é fallback do cloud e deve ter
teste de arquitetura impedindo import cruzado. Documentos cloud descrevem apenas
PostgreSQL. O arquivo SQLite cloud e seus backups só serão removidos do servidor
após aceite humano explícito do relatório e da janela de observação.

## Definition Of Ready De Cada Pacote

Um pacote só inicia quando possui:

- owner técnico e operacional, escopo incluído/excluído e dependências fechadas;
- inventário real e baseline; ADRs de tecnologia ainda não decidida;
- SLO, RPO/RTO quando aplicável, orçamento de recurso e plano de capacidade;
- ameaça/privacidade, classificação de dados, retenção e segregação de acesso;
- contrato/API/evento/schema e matriz N/N-1;
- plano de rollout, observação, rollback e limpeza legada;
- testes proporcionais, fixtures, ambiente de restore e evidência manual;
- autorização prévia para qualquer serviço externo inevitável, como pagamento
  ou destino de backup, sem transferir a aplicação do host atual.

## Definition Of Done De Cada Pacote

Um pacote só fecha quando:

- todos os lotes e critérios passaram no release publicado;
- integridade, carga, segurança, restore, smoke e observação foram anexados;
- métricas/alertas/runbook/on-call e retenção estão operacionais;
- código temporário, flags, adapters, units, dados e docs foram removidos;
- scanner de legado e dependências não encontra resíduo fora das exceções locais;
- rollback restante foi executado ou comprovado, não apenas descrito;
- diff completo foi revisado, `./check.sh` passou e o pacote recebeu commit próprio.

## Gates Transversais De Segurança E Privacidade

Todos os pacotes, não apenas o financeiro, exigem:

- threat model atualizado para assets, atores, trust boundaries e abuso;
- autenticação e autorização deny-by-default no backend; UI nunca é controle;
- isolamento de owner/organização/tenant testado em leitura, mutação, busca,
  objeto, evento, cache, exportação, backup e suporte;
- proteção de sessão/token, rotação, revogação, expiração, CSRF quando aplicável,
  CORS estrito, headers seguros e step-up em ação sensível;
- validação de entrada/saída, limites de payload, paginação, rate limit e
  proteção contra enumeração, replay, injeção e mass assignment;
- URL externa protegida contra SSRF/DNS rebinding e arquivo protegido contra
  traversal, archive bomb, malware, parser bomb e content-type enganoso;
- SQL parametrizado, role mínima e nenhum segredo em código, log, trace, evento,
  backup, screenshot ou bundle de suporte;
- criptografia em trânsito, backup externo criptografado e chaves separadas do
  conteúdo protegido;
- dependências fixadas, SBOM, scan de segredo/dependência, artefato com checksum/
  assinatura e procedimento de atualização/rollback;
- logs de segurança sanitizados, alerta acionável, retenção, canal de incidente
  e teste de abuso/negação de serviço;
- revisão independente e teste de segurança mais forte antes de pagamento,
  fabricação, dado sensível, moderação automatizada ou escala pública.

## Etapa 1 - Fundação Modular E Operação Sem Parada

Pacotes: `PKG-86` e `PKG-87`.

Resultados:

- mapa de domínios, contratos e dependências do monólito;
- extração incremental de módulos por responsabilidade, sem alterar API pública;
- application services sem dependência de FastAPI e repositories sem regra de UI;
- componentes frontend divididos em page, state/hook, form e API client;
- contratos tipados e testes de arquitetura impedindo dependências proibidas;
- observabilidade com request/correlation/job ID, métricas, readiness e logs;
- deploy blue/green em duas portas, Nginx upstream e drenagem de conexões;
- inventário e orçamento real do servidor, com limites por unit systemd;
- baseline de carga, capacidade, latência, erros e uso de recursos;
- cobertura obrigatória crescente nos fluxos críticos, sem meta cosmética global.

Esta etapa não cria microsserviços. Ela torna fronteiras explícitas para que
dados e processos sejam trocados sem reescrever toda a aplicação.

## Etapa 2 - Dados, Realtime, Jobs, Arquivos E Busca

Pacotes: `PKG-88`, `PKG-89` e `PKG-90`.

Resultados:

- PostgreSQL como única base relacional cloud;
- SQL idempotente e versionador compatível com PostgreSQL;
- Redis para cache recomponível, rate limit, presença e pub/sub;
- sessões WebSocket distribuídas, sem registry autoritativo em memória;
- outbox e fila transacional PostgreSQL com workers systemd concorrentes;
- retries com backoff, timeout, idempotência, dead-letter e reprocessamento seguro;
- storage S3-compatible local com checksum, quarentena e URLs autorizadas;
- índice textual PostgreSQL, atualização assíncrona e rebuild total reproduzível;
- cutovers por sombra/canário sem indisponibilidade observável;
- remoção total de SQLite no perfil cloud, paths de storage e filas in-memory aposentados.

A ordem interna é banco, fila/outbox, realtime/cache, objetos e busca. Cada
subtransição termina a própria limpeza antes de habilitar a próxima.

## Etapa 3 - Transações Comerciais E Cadeia De Produção

Pacotes: `PKG-91` e `PKG-92`.

Resultados:

- domínio financeiro isolado dentro do monólito modular;
- ledger de partidas dobradas, imutável e reconciliável;
- adapters de provedores, webhooks autenticados, idempotência e replay seguro;
- pedidos, itens, licenças, impostos preparados, reembolso e disputa;
- saldo, repasse e fechamento sem derivar dinheiro de campos mutáveis;
- fraude e risco com regras explicáveis, revisão humana e trilha de decisão;
- ordem de fabricação ligada a projeto, versão, arquivo, material e produtor;
- cotação, aceite, produção, qualidade, expedição, entrega e incidente;
- cadeia de custódia e evidência sem expor endereço ou documento indevido;
- suporte e operação financeira separados de moderação e conteúdo público;
- nenhum checkout, saldo ou pedido legado em paralelo ao domínio canônico.

Nenhuma função financeira entra em produção apenas por teste unitário. São
obrigatórios sandbox do provedor, reconciliação, cenários de duplicidade, timeout,
chargeback, permissionamento, auditoria, retenção e revisão de segurança.

## Etapa 4 - Escala, Recuperação, Dados E Inteligência

Pacotes: `PKG-93` e `PKG-94`.

Resultados:

- múltiplas instâncias stateless no host, balanceadas pelo Nginx;
- workers separados por classe de carga e limites de concorrência;
- backpressure, quotas, circuit breakers e degradação graciosa;
- backup automatizado de PostgreSQL, objetos e configuração, com restore testado;
- objetivos RPO/RTO medidos e simulações periódicas de desastre;
- warehouse analítico derivado, sem consulta pesada no banco transacional;
- moderação multilíngue, filas especializadas e revisão humana;
- serviço isolado para ML, recomendação e busca geométrica quando justificado;
- modelos versionados, avaliação offline, canário, rollback e monitoramento de drift;
- testes de carga, soak, caos de processo, segurança e recuperação;
- capacidade documentada para crescer verticalmente no host atual.

Analytics e ML consomem eventos sanitizados e não escrevem diretamente nas
tabelas transacionais. A falha desses componentes degrada recomendação, busca ou
relatório, mas não bloqueia login, segurança, projeto, impressão ou pedido.

## Consolidação Final

Pacote: `PKG-95`.

O programa só termina depois de:

- todos os pacotes anteriores estarem fechados e publicados;
- referências antigas zeradas ou justificadas como história arquitetural;
- flags temporárias, adapters, bridges, jobs, units e dashboards removidos;
- arquivos grandes restantes divididos ou aceitos por decisão explícita;
- contratos públicos inventariados e consumidores validados;
- restore completo ensaiado a partir de backup;
- carga de pico e soak passarem no servidor atual com folga definida;
- cutover/redeploy comprovarem zero falha atribuível à troca;
- runbook, topologia, ownership, retenção, riscos e rollback refletirem somente
  a arquitetura final.

## Ordem Obrigatória

1. `PKG-86`: qualificação do servidor, releases imutáveis e blue/green.
2. `PKG-87`: monólito modular, contratos e redução dos arquivos críticos.
3. `PKG-88`: transição cloud SQLite -> PostgreSQL.
4. `PKG-89`: outbox, workers, Redis e realtime distribuído.
5. `PKG-90`: armazenamento de objetos e busca reconstruível.
6. `PKG-91`: ledger, pagamentos, pedidos e reconciliação.
7. `PKG-92`: fabricação, qualidade, logística e cadeia de custódia.
8. `PKG-93`: múltiplas instâncias, resiliência, backup e recuperação.
9. `PKG-94`: analytics, moderação multilíngue e ML isolado.
10. `PKG-95`: auditoria final e erradicação residual.

Não é permitido iniciar uma etapa quando o gate de capacidade, integridade ou
limpeza da anterior estiver aberto.
