# Evidência De Prontidão Blue/Green

Data: 2026-07-22.

## Implementado Localmente

- liveness em `/health` e readiness com banco/schema em `/ready`;
- request ID propagado, log HTTP estruturado e métricas Prometheus sem payload;
- duas units systemd com portas, venv e frontend separados por slot;
- upstream Nginx selecionável e `/metrics` restrito a loopback;
- deploy fail-closed, smoke privado, troca atômica, drenagem e rollback de código;
- preflight de privilégios, NTP, certificado, portas, logrotate, backup e limites;
- backup restic externo e teste de restore SQLite isolado;
- reconnect do agente com jitter, fallback polling e deduplicação concorrente;
- substituição segura de sessão WebSocket durante reconnect;
- carga HTTP reproduzível com erro zero e limite p95 configurável.
- threat model repository-wide persistido em `SECURITY.md`, cobrindo ativos,
  fronteiras, invariantes, supply chain, agente/impressora e severidade.
- SBOM CycloneDX reproduzível para backend, frontend e agente, com checksums e
  gate de vulnerabilidades antes de empacotar a release.
- probes e restarts não executam varredura integral do SQLite; `integrity_check`
  permanece no gate de schema e nos fluxos isolados de backup/restore.
- após a drenagem, N-1 reinicia sem WebSockets antigos e permanece aquecido como
  backup do upstream ativo.

## Evidência Local

```text
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
478 testes backend passaram
go test ./... passou
build frontend e testes direcionados passaram
CHECK_STRICT_SECRETS=1 CHECK_STRICT_RUNTIME_NAMES=1 ./check.sh passou
npm audit --omit=dev: 0 vulnerabilidades
pip-audit --local: 0 vulnerabilidades conhecidas
govulncheck ./... com Go 1.25.12: 0 vulnerabilidades alcançáveis
```

O build em Node 18.20.8 emitiu aviso de versão mínima do Vite, mas concluiu com
sucesso. O workflow usa o runner GitHub atual e deve registrar a versão Node no
primeiro ciclo de validação.

O agente fixa `toolchain go1.25.12`: a auditoria inicial com Go 1.25.4 encontrou
14 vulnerabilidades alcançáveis na biblioteca padrão; a reexecução com a versão
corrigida não encontrou vulnerabilidades.

## Evidência Remota Coletada

- host: 48 CPUs, 32 GB de RAM total e 25 GB disponíveis;
- disco: 906 GB totais e 130 GB disponíveis; 9 milhões de inodes disponíveis;
- banco SQLite: 4,04 GiB; diretório de dados: 28 GB;
- serviço legado permaneceu saudável durante o bootstrap;
- backup Restic criptografado externo: snapshot `a698d107`, 4,04 GiB lidos e
  413,8 MiB armazenados;
- restore isolado: 4,04 GiB restaurados, `integrity=ok`, 100 tabelas e 73 scripts
  de schema; nenhuma aplicação foi iniciada sobre a cópia restaurada.
- backup limitado por systemd a 8 GiB de memória, 200% de CPU e 128 tarefas; o
  timer persistente ficou habilitado e ativo, com destino fora do host primário;
- primeiro ciclo publicado no slot green pelo run `29944639803` e segundo ciclo
  no slot blue pelo run `29945127924`, ambos com checks completos;
- rollback de código reativou green sem restaurar snapshot: durante a prova, os
  jobs avançaram de 68.034 para 68.040 e o heartbeat do agente continuou;
- release inválido falhou readiness, reiniciou somente o candidato e nunca foi
  ligado ao upstream; 1.000 requests públicos passaram sem erro;
- morte controlada do processo cloud ativo recuperou em aproximadamente seis
  segundos pelo slot N-1 aquecido; 2.000 requests passaram sem erro;
- o agente realmente online permaneceu conectado; não foram observados ACKs ou
  correlation IDs duplicados (`duplicate_recent_acks=0` e
  `duplicate_correlations=0`);
- cargas de 1.000 requests durante deploy, rollback e candidato inválido tiveram
  zero erro; p95 medido entre 210,66 ms e 2.119 ms, abaixo do gate de 3 s;
- carga final de 1.000 requests teve zero erro e p95 de 234,42 ms;
- o deploy `ac44608c227c4aa9fc9ead9a51dce44d91649174` concluiu no run
  `29946500234`, mantendo green ativo e blue N-1 pronto;
- o fechamento `41f5a88e3d74b8308d7560a6c7ad6cf12de739b4` concluiu no run
  `29947381195`, com blue ativo, green N-1 pronto e timer de backup ativo;
- `/ready` retornou banco e schema 73 prontos; `/health` permaneceu saudável;
- nenhum warning ou erro da aplicação foi encontrado na observação final;
- a unit de instância única ficou `not-found` e o venv compartilhado foi
  removido somente após a prova dos dois slots; dados, backups e releases foram
  preservados;
- nenhum serviço da impressora, Moonraker, Klipper, MCU ou agente local foi
  reiniciado durante as provas.

## Resultado

O PKG-86 está aceito. O host atual possui folga para os dois slots e rollback,
o backup externo possui restore isolado comprovado e o caminho legado de
publicação foi eliminado. A solução remove indisponibilidade por publicação e
por falha isolada do processo; indisponibilidade física do host permanece risco
conhecido e será tratada no PKG-93.
