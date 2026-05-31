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
  "timeout_seconds": 5
}
```

O arquivo de credencial deve conter apenas a credencial operacional `ptr_agent_*`
e deve ficar com permissão `0600`.

## Segurança

- O agente só faz chamadas de saída para a API.
- O agente só lê endpoints read-only do Moonraker.
- O agente não envia G-code, não reinicia serviços, não aplica update, não faz
  build e não faz flash.
- Logs passam por redaction de tokens `ptr_agent_*`, `ptr_pair_*` e `ptr_sess_*`.
- A fila local é JSONL limitada e guarda payload compacto quando a API está
  indisponível.
