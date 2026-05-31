# Printora Agent

Agente local read-only do Printora para hosts Klipper/Moonraker.

## Comandos

```bash
printora-agent -config ~/.config/printora-agent/config.json config-sample
printora-agent -config ~/.config/printora-agent/config.json doctor
printora-agent -config ~/.config/printora-agent/config.json once
printora-agent -config ~/.config/printora-agent/config.json run
```

## Config

O config é JSON e deve ficar com permissão `0600`.

```json
{
  "api_base_url": "https://printora.example.com",
  "moonraker_url": "http://127.0.0.1:7125",
  "credential_file": "/etc/printora-agent/credential",
  "queue_file": "/var/lib/printora-agent/queue.jsonl",
  "log_file": "/var/log/printora-agent/agent.log",
  "interval_seconds": 10,
  "timeout_seconds": 5,
  "websocket_enabled": true,
  "polling_enabled": true,
  "max_payload_bytes": 65536,
  "update_enabled": true,
  "update_check_interval_seconds": 3600,
  "update_manifest_url": "https://printora.example.com/api/agent/update/manifest",
  "update_state_file": "/var/lib/printora-agent/update-state.json",
  "update_staging_dir": "/var/lib/printora-agent/updates",
  "agent_binary_path": "/usr/local/bin/printora-agent",
  "agent_service_name": "printora-agent",
  "allow_service_restart": true
}
```

O arquivo de credencial deve conter apenas a credencial operacional `ptr_agent_*`
e deve ficar com permissão `0600`.

## Segurança

- O agente só faz chamadas de saída para a API.
- O agente lê endpoints read-only do Moonraker por padrão.
- O agente só envia G-code em jobs `remote_mutation_execute` criados após
  preflight remoto, confirmação textual e expiração controlada pela API.
- O agente não executa shell genérico, não reinicia serviços, não faz build e
  não faz flash.
- Logs passam por redaction de tokens `ptr_agent_*`, `ptr_pair_*` e `ptr_sess_*`.
- A fila local é JSONL limitada e guarda payload compacto quando a API está
  indisponível.

## Canal remoto

O comando `run` tenta manter WebSocket outbound com `/api/agent/ws`. Se o canal
falhar e `polling_enabled` estiver ativo, o agente usa polling HTTPS para buscar
jobs e enviar `ack`, `result` ou `error`.

Jobs suportados nesta etapa:

- `ping`: responde com `pong`.
- `snapshot`: coleta snapshot read-only compacto do Moonraker.

## Instalação assistida

A tela Impressoras gera comandos com token curto por impressora. O script online
fica em `/api/agent/install/linux.sh` e suporta:

```bash
--preflight
--apply --yes
--uninstall
```

O script troca o token por credencial operacional no próprio host, grava config
com permissão restrita e instala serviço systemd. O uninstall remove serviço e
binário, preservando configuração, fila e logs para rollback/diagnóstico.

## Atualização

```bash
printora-agent -config /etc/printora-agent/config.json update-check
```

O agente consulta `/api/agent/update/manifest`, valida plataforma, versão,
protocolo e SHA-256 antes de trocar o binário. O restart automático reinicia
somente o serviço `printora-agent` quando `allow_service_restart=true`. Falha de
health/restart tenta restaurar o binário anterior.

## Paridade remota

O agente executa jobs read-only e dry-run enviados pela API:

- `remote_audit`
- `remote_snapshot`
- `remote_health`
- `remote_temperatures`
- `remote_update_status`
- `remote_can_status`
- `remote_final_validation`
- `remote_report_sanitized`
- `remote_backup_preview`
- `remote_operation_preview`
- `remote_firmware_preview`

Antes de enviar resultados, o agente sanitiza campos sensíveis como `password`,
`token`, `secret`, `credential` e `private_key`.

## Operação remota segura

Jobs mutáveis suportados:

- `remote_mutation_preflight`: coleta estado Moonraker/Klipper, detecta impressão
  em andamento e retorna `can_execute`.
- `remote_mutation_execute`: reexecuta preflight no agente e envia somente o
  `command_preview` aprovado para `/printer/gcode/script`.

O agente bloqueia execução quando Moonraker está indisponível, Klipper/Klippy
não estão `ready` ou há impressão em andamento. O rollback vem no payload do job
e volta no resultado para auditoria.

## Suporte remoto

Job de suporte:

- `remote_doctor`: retorna versão, plataforma, protocolo, checks de config,
  credencial, Moonraker, API, fila local e log tail sanitizado.

O doctor remoto não executa shell genérico e não retorna credencial completa. O
log tail passa pela mesma redaction de `ptr_agent_*`, `ptr_pair_*` e
`ptr_sess_*` usada nos logs locais.
