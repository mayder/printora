# Agente 0.1.34 - Evidência De Release E Canário

Data: 2026-07-23
Pacote: PKG-96
Estado: publicado, homologado nas Voron 2.4 e 0.2 e promovido como recomendado

## Escopo Exercitado

- inventário do binário público `0.1.33` e das mudanças posteriores no agente;
- suporte declarado restrito a `linux/arm64`;
- versão `0.1.34` no código e artefato candidato;
- build duplo reproduzível com Go `1.25.12`, `CGO_ENABLED=0`, `-trimpath`,
  VCS/build ID removidos e dependências bloqueadas;
- SBOM CycloneDX, SHA-256 e assinaturas Ed25519 verificadas;
- chave pública e fingerprint fixadas no agente; chave privada mantida fora do
  repositório;
- manifesto com N-1 recomendado e candidato separado;
- endpoint candidato autenticado, sem adoção automática pela frota;
- ações web explícitas de candidato e rollback, com alvo exato, preflight
  Moonraker, backup, SHA-256, Ed25519 e restart apenas do `printora-agent`;
- verificação de checksum e assinatura no instalador e no auto-update;
- preflight fail-closed de `print_stats.state`, bloqueando update quando a
  impressora está imprimindo/pausada ou quando não é possível provar que está
  ociosa;
- journal local `0600`, limitado a 200 entradas, com recebimento persistido
  antes do ACK, início antes do efeito e resultado antes da resposta; escrita e
  diretório são sincronizados em disco para impedir repetição após queda,
  redelivery ou restart;
- compatibilidade do protocolo 1 e seleção exclusiva da versão recomendada;
- reconnect com jitter, fallback por polling, fencing de sessão e deduplicação
  concorrente/durável cobertos por teste.

## Artefatos

| Item | Evidência |
| --- | --- |
| Binário candidato | `backend/app/data/agent_releases/printora-agent-linux-arm64-0.1.34` |
| SHA-256 | `c430f3b16f0785808b09ecacce63fb734c434864262dc22a50dcc3642a6ff9dc` |
| SBOM | `printora-agent-linux-arm64-0.1.34.sbom.cdx.json` |
| Checksums assinados | `printora-agent-linux-arm64-0.1.34.SHA256SUMS` e `.sig` |
| Metadados | `printora-agent-linux-arm64-0.1.34.metadata.json` |
| N-1 retido | `printora-agent-linux-arm64-0.1.33`, SHA-256 `1373f97adaf22cb76bf6c9f69c9deedeeb1984659b8e01fea4d261eafd805811` |
| Chave pública | `packaging/agent/agent-release-ed25519.pub` |
| Fingerprint | `sha256:e241d16ebb469da7436ff050a36212635557eab1322495a2c62e2ca6caf24cdc` |

O nome genérico mutável do binário foi removido depois de confirmar igualdade
byte a byte com o N-1 versionado. O conteúdo continua recuperável pelo artefato
`0.1.33` e pelo histórico Git.

## Validação Automatizada

- duas execuções consecutivas de `scripts/build-agent-release.sh` produziram o
  mesmo SHA-256 e validaram as assinaturas;
- `go test ./...`: passou;
- `go test -race ./...`: passou depois de corrigir uma corrida no teste de
  timeout e cobriu a persistência anterior ao ACK;
- `govulncheck ./...`: nenhuma vulnerabilidade alcançável;
- testes focados de agente/update/instalador/backend passaram, incluindo canal
  candidato, rollback N-1, bloqueio prematuro e rejeição de canal inválido;
- `CHECK_STRICT_SECRETS=1 CHECK_STRICT_RUNTIME_NAMES=1 RUN_PYTHON_TESTS=1
  RUN_FRONTEND_CHECKS=1 ./check.sh`: 569 testes Python, testes Go, build frontend
  e testes de release, preview e polling sequencial passaram.

O build frontend ainda emitiu os warnings de Node 18 incompatível e chunks acima
de 500 kB. O comando terminou com sucesso porque esses limites pertencem ao
PKG-97 e ainda não são gates bloqueantes.

Na primeira publicação do candidato, o gate completo passou, mas o deploy foi
bloqueado antes do empacotamento porque o npm 10 do runner chamou o endpoint
legado de auditoria e recebeu HTTP 400 `Invalid package tree`. O workflow passou
a fixar npm `11.7.0`, que usa o endpoint atual; a auditoria continuou bloqueante
e foi validada localmente com zero vulnerabilidade de produção.

## Observação Real Somente Leitura

Em produção, antes de qualquer mutação:

- `/health` e `/ready` responderam saudáveis;
- os três slots cloud e os workers estavam ativos;
- o manifesto público ainda recomendava `0.1.33`;
- o agente real `linux/arm64` reportava `0.1.33`, protocolo 1, WebSocket ativo e
  heartbeat atual;
- um job auditado `remote_operation_status` terminou com `safe_mode=read_only`,
  `kind=operation_status` e estado físico `standby`.

Nenhum comando G-code, alteração de Klipper/Moonraker, flash ou mudança de
firmware foi executado.

## Canário, Rollback E Paridade Real

- Voron 0.2 e Voron 2.4 foram confirmadas com Moonraker online, Klipper `ready`
  e `print_stats.state=standby` antes de cada ação mutável;
- a primeira tentativa na Voron 0.2 falhou antes da instalação porque o OpenSSL
  1.1.1 local não suportava a verificação Ed25519 usada; o binário não foi
  substituído;
- o verificador foi trocado por uma implementação Ed25519 portátil em Python
  padrão, validada contra a assinatura real e contra adulteração;
- as duas impressoras instalaram `0.1.34`, voltaram para `0.1.33` e reaplicaram
  `0.1.34` exclusivamente pelas ações web do Printora;
- cada operação reiniciou somente `printora-agent`; Klipper, Moonraker, MCU e
  host permaneceram ativos;
- doctor remoto final confirmou API, Moonraker, fila local e logs; a Voron 2.4
  também confirmou ausência de throttling/undervoltage;
- conexões WebSocket `101`, reconnect, heartbeat a cada 10 segundos, entrega de
  jobs e fallback por `/api/agent/jobs/next` foram observados em produção;
- retransmissões de resultado foram idempotentes e o journal durável impediu
  repetição do efeito físico;
- depois da janela de observação, ambos os agentes continuaram online em
  `linux/arm64`, protocolo 1 e versão `0.1.34`.

## Defeitos Encontrados E Corrigidos

- timestamps PostgreSQL com offset curto impediam a UI de reconhecer agentes
  online; backend e frontend passaram a normalizar o formato;
- `printer_snapshots.id` não possuía identidade no baseline PostgreSQL legado;
  `017_printer_snapshots_identity.sql` adicionou sequência/default de forma
  aditiva, idempotente e transacional, alinhando a propriedade da sequência à
  tabela;
- a desconexão WebSocket era removida da memória antes da persistência e podia
  ser perdida no shutdown; a ordem foi invertida e o teste passou 30 vezes
  consecutivas;
- a aba Operação sobrepunha leituras a cada cinco segundos quando o agente estava
  lento; o polling agora espera a rodada atual terminar antes de agendar outra.

Em produção, o banco registrou um snapshot por impressora:

| Impressora | `printer_id` | Snapshot real |
| --- | ---: | --- |
| Voron 0.2 | 1 | `2026-07-23 11:31:49-03` |
| Voron 2.4 | 3 | `2026-07-23 11:30:44-03` |

A janela estabilizada do polling registrou Operação às 11:51:46, saúde às
11:52:01 e nova Operação às 11:52:12, sem sobreposição.

## Publicação E Promoção

| Marco | Evidência |
| --- | --- |
| Candidato publicado | workflow `30009192554` |
| Schema/snapshot corrigidos | workflow `30015189640` |
| Polling sequencial publicado | workflow `30016684483` |
| Promoção pública | workflow `30018307622`, commit `7acb26f` |

O manifesto público final recomenda `0.1.34`, não anuncia candidato e mantém os
artefatos `0.1.33` e `0.1.34`. Downloads públicos produziram exatamente os
SHA-256 documentados. `/health` respondeu `ok`; `/ready` respondeu `ready`,
PostgreSQL `ok` e schema revision 86. A UI exibiu dois agentes online, ambos em
`0.1.34`, versão esperada `0.1.34` e canário ausente.

## Risco Residual

- o alerta histórico de falhas em 24 horas permanece visível até a janela de
  retenção expirar, mas a causa de tempestade foi corrigida e a nova janela
  mostrou leituras sequenciais;
- Node 18 e chunks acima de 500 kB continuam warnings não bloqueantes e pertencem
  explicitamente ao PKG-97;
- o rollback permanece disponível para `0.1.33`; não envolve restauração de
  PostgreSQL, Redis, objetos ou release web.
