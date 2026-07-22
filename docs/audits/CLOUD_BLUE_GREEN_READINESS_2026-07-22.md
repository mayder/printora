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

## Evidência Local

```text
RUN_PYTHON_TESTS=1 RUN_FRONTEND_CHECKS=1 ./check.sh
478 testes backend passaram
go test ./... passou
build frontend e testes direcionados passaram
```

O build em Node 18.20.8 emitiu aviso de versão mínima do Vite, mas concluiu com
sucesso. O workflow usa o runner GitHub atual e deve registrar a versão Node no
primeiro ciclo de validação.

## Evidência Remota Obrigatória Pendente

- instalar bootstrap com administrador e confirmar sudoers via `visudo`;
- registrar CPU, RAM, disco, I/O, rede, file descriptors, processos e pico;
- aprovar orçamento para duas releases e dependências futuras;
- configurar destino restic fora do host, provar custódia externa da chave e restore;
- executar primeiro deploy para green e segundo para blue;
- medir requests falhos, p95, reconnect, duplicidade e tempo de drenagem sob carga;
- matar candidato antes da troca e ativo depois da troca;
- executar rollback e provar preservação de escrita posterior;
- observar logs/métricas pelo período definido e executar smoke público P0/P1;
- somente depois remover unit, venv e procedimento legados.

Até essa evidência existir, a publicação sem indisponibilidade não está aceita e
o pacote arquitetural inicial permanece aberto.
