# Agente 0.1.34 - Evidência De Release E Canário

Data: 2026-07-23
Pacote: PKG-96
Estado: candidato local validado; publicação, canário, rollback físico e promoção pendentes

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
- `RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh`: 567 testes Python,
  testes Go, build frontend e testes de release/preview passaram.

O build frontend ainda emitiu os warnings de Node 18 incompatível e chunks acima
de 500 kB. O comando terminou com sucesso porque esses limites pertencem ao
PKG-97 e ainda não são gates bloqueantes.

## Observação Real Somente Leitura

Em produção, antes de qualquer mutação:

- `/health` e `/ready` responderam saudáveis;
- os três slots cloud e os workers estavam ativos;
- o manifesto público ainda recomendava `0.1.33`;
- o agente real `linux/arm64` reportava `0.1.33`, protocolo 1, WebSocket ativo e
  heartbeat atual;
- um job auditado `remote_operation_status` terminou com `safe_mode=read_only`,
  `kind=operation_status` e estado físico `standby`.

Nenhum update, restart, comando G-code, alteração de Klipper/Moonraker, flash ou
mudança de firmware foi executado nesta etapa.

## Gates Pendentes

1. commit/push e publicar o candidato sem alterar a recomendação;
2. validar download público, checksum, assinatura, SBOM e smoke;
3. com a impressora ainda ociosa, instalar somente `printora-agent` como canário;
4. exercer heartbeat, snapshot, job, WebSocket, reconnect, polling e fencing;
5. comprovar que Klipper, Moonraker, MCU, host e fila não reiniciaram;
6. executar rollback real para o N-1, validar saúde e reaplicar `0.1.34`;
7. observar o canário e somente então promover `recommended_version`;
8. repetir gate completo, smoke público, auditoria de resíduo e fechar o pacote.

## Risco Residual

O artefato candidato está validado localmente, mas não existe evidência suficiente
para chamá-lo de publicado, instalado ou homologado em hardware. A ausência de
mutação nesta etapa preserva a impressão e o rollback, mas impede o fechamento
do PKG-96 até os gates operacionais acima.
