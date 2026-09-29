# Revisão De Fechamento Dos Pacotes Arquiteturais

Data da revisão: 2026-07-22.

Escopo: `PKG-86` a `PKG-95`, quatro etapas arquiteturais, perfil cloud no
servidor atual e preservação do produto local/offline.

## Resultado

A primeira versão tinha cinco pacotes grandes e deixava riscos implícitos. A
revisão dividiu o programa em dez pacotes fecháveis e transformou os riscos em
dependências, critérios de aceite e testes bloqueantes.

Planejamento revisado não é prova de implementação sem defeito. A garantia
possível nesta fase é: nenhum risco conhecido abaixo ficou sem owner, pacote,
gate e evidência exigida. Capacidade real, integrações externas e comportamento
em produção só podem ser aprovados quando os respectivos testes forem executados.

## Matriz De Cobertura

| Área de risco | Cobertura obrigatória | Pacote |
|---|---|---|
| Capacidade do host | CPU, RAM, disco, I/O, FD, portas, quotas, folga e soak | PKG-86 |
| Privilégios | Nginx/systemd, usuários, ownership, firewall e instalação sem Docker | PKG-86 |
| Release | código, frontend, venv, lockfile e unit imutáveis por release | PKG-86 |
| Deploy | readiness, smoke privado, `nginx -t`, troca atômica, drain e rollback | PKG-86 |
| Compatibilidade | contratos, schema, eventos e consumers N/N-1 | PKG-86/87 |
| WebSocket/agente | reconnect com jitter, ack, deduplicação e retomada durável | PKG-86/89 |
| Acoplamento | domínio/aplicação/API/infra/UI separados e sem ciclos | PKG-87 |
| Arquivos grandes | caracterização, divisão por responsabilidade e gate automático | PKG-87/95 |
| Perfis cloud/local | PostgreSQL cloud e SQLite local isolados, sem fallback cruzado | PKG-87/88/95 |
| Migração de banco | snapshot, outbox SQLite, import, sombra, canário e watermark | PKG-88 |
| Integridade | contagem, checksum, sequences, FKs, órfãos e semântica de tipos | PKG-88 |
| Rollback pós-cutover | release anterior PostgreSQL-compatible; nunca snapshot velho | PKG-88 |
| Jobs/eventos | outbox/inbox, lease, idempotência, retry, DLQ, replay e retenção | PKG-89 |
| Redis | somente cache/presença/pub-sub recomponíveis; falha segura | PKG-89 |
| Objetos | streaming, checksum, quarentena, promoção, quota, backup e restore | PKG-90 |
| Busca | permissão no query, atualização por evento e rebuild total | PKG-90 |
| Financeiro | ledger, inteiro/moeda, PCI reduzido, webhook e reconciliação | PKG-91 |
| Fraude e acesso | segregação, step-up, explicação, revisão humana e recurso | PKG-91 |
| Produção | snapshots, capacidade, estados, qualidade e idempotência | PKG-92 |
| Segurança física | peça reprovada, incidente, recall e cadeia de custódia | PKG-92 |
| Resiliência | múltiplas instâncias, backpressure, bulkhead e circuit breaker | PKG-93 |
| Backup/desastre | WAL/backup externo criptografado, restore e RPO/RTO medidos | PKG-93 |
| Analytics | role read-only, lineage, replay, consentimento e remoção derivada | PKG-94 |
| Moderação/ML | revisão humana, bias, canário, drift, rollback e kill switch | PKG-94 |
| Segurança | least privilege, segredo, rede privada, auditoria e revisão independente | Todos/95 |
| Retenção | logs, WAL, backup, objetos, DLQ, auditoria, datasets e modelos | Todos/95 |
| Supply chain | lockfiles, SBOM, dependências, artefatos e atualização/rollback | PKG-86/95 |
| Legado | scanner por perfil em código, banco, filesystem, units e docs | Cada pacote/95 |
| Operação/UI | telas separadas, permissões, estados, confirmação e acessibilidade | Pacote dono/95 |

## Pontas Soltas Corrigidas

### Venv compartilhado

O deploy atual instala dependências em virtualenv compartilhado. Isso poderia
alterar a instância azul antes do cutover e tornar rollback falso. O PKG-86 agora
exige virtualenv e artefato completos por release.

### Schema incompatível durante blue/green

Dois releases coexistem durante drenagem. O programa agora exige
expandir/migrar/contrair e compatibilidade N/N-1 para banco, evento e API.

### Rollback depois de abandonar SQLite

Voltar a um binário SQLite-only perderia escritas feitas no PostgreSQL. O PKG-88
agora exige um release intermediário que entende PostgreSQL; todo rollback após
o cutover continua no PostgreSQL.

### SQLite local confundido com legado cloud

Remover SQLite do repositório inteiro quebraria instalações macOS, Windows,
Linux/Raspberry e Android. A decisão revisada remove SQLite integralmente do
perfil cloud e mantém o adapter local como produto suportado e isolado. Scanner
e testes impedem fallback/import cruzado.

### WebSockets que nunca drenam

Conexões de agentes são longas. PKG-86/89 agora exigem modo draining, reconnect
com jitter, sessão/job durável, ack e deduplicação antes de encerrar o blue.

### Backup somente no mesmo host

Backup local não protege contra perda do servidor. PKG-93 exige cópia externa
criptografada e restore independente. A aplicação continua executando apenas no
host atual; a cópia externa é condição de recuperação, não segundo runtime.

### Pacotes grandes demais

Banco, Redis, jobs, realtime, objetos e busca estavam no mesmo pacote; financeiro
e fabricação também. Foram separados para permitir rollback e encerramento sem
bridge permanente.

### Dependência S3 não decidida

Não foi imposto um produto sem medir licença, suporte systemd, recursos, upgrade
e restore. PKG-90 possui ADR e prova obrigatórias; sem decisão aprovada o pacote
fica bloqueado antes de persistir objeto produtivo.

### Dinheiro em float e exposição PCI

PKG-91 exige unidade monetária mínima + moeda, checkout/tokenização do provedor,
ausência de PAN/CVV, ledger balanceado, reconciliação e segregação de função.

### Analytics/ML afetando produção

PKG-94 exige role sem escrita no OLTP, quotas, fallback, kill switch, lineage,
consentimento, remoção derivada, revisão humana e capacidade residual.

## Bloqueios Externos Formalizados

Estes itens não podem ser inventados no planejamento. Eles bloqueiam o pacote
correspondente até existir evidência:

1. capacidade e privilégios reais do servidor: PKG-86;
2. destino externo criptografado de backup/WAL: PKG-86/93;
3. implementação S3-compatible após ADR/prova: PKG-90;
4. provedor de pagamento, sandbox, jurídico, fiscal e PCI: PKG-91;
5. transportadoras, responsabilidade, segurança e recall: PKG-92;
6. datasets, licenças, revisão especializada e capacidade de ML: PKG-94.

O acesso privado específico do Printora não está cadastrado em
`DEPLOY_ACCESS.md`; portanto a capacidade atual do host não foi alegada como
validada nesta revisão. Credenciais de outro projeto no mesmo IP não devem ser
reutilizadas por inferência.

## Gates Que Impedem Falso Fechamento

- pacote sem Definition of Ready não inicia;
- bridge/flag/adaptação temporária precisa de owner e remoção no mesmo pacote;
- resultado sem relatório de integridade/restore/carga não conta como entregue;
- teste verde local não substitui smoke publicado e observação;
- limpeza destrutiva sem confirmação explícita não executa;
- bloqueio externo não pode ser reclassificado como concluído;
- pacote fechado exige commit próprio, sem misturar outro pacote;
- PKG-95 repete scanner, restore, deploy, carga, soak, segurança e revisão final.
