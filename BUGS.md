# BUGS.md

## Bugs Conhecidos

Nenhum bug aberto de implementação registrado.

## Bugs Corrigidos

### Alerta Vermelho Sem Causa Acionavel Na Home

Sintoma:

- a Home mostrava `Nao imprimir`, mas o operador precisava abrir a Central de alertas e interpretar listas tecnicas para saber qual bloqueio estava ativo e como agir.

Causa:

- a tela resumia apenas contadores de bloqueios/alertas e a Central exibia detalhe e acao como texto livre, sem separar causa, evidencia, orientacao e acao do sistema.

Correção:

- a Home passou a destacar o bloqueio ou alerta principal;
- a Central de alertas passou a exibir `Por que aparece`, `Evidencia`, `Como resolver` e botoes de acao por item;
- itens de health/checklist podem ser revalidados, updates podem abrir o fluxo do Update Manager e itens manuais abrem o diagnostico.

Validação:

- `npm run build` no frontend.

### Timeout No Envio De G-code De Calibração

Sintoma:

- a UI marcava falha ao enviar G-code mesmo quando a impressora recebia e executava o comando.

Causa provável:

- timeout/erro de transporte do POST para `/printer/gcode/script` era tratado como falha definitiva sem consultar o estado final do Moonraker/Klipper.

Correção:

- após cada envio, o backend monitora o estado final da impressora e registra o retorno final; se a impressora fica `ready`, o comando é tratado como confirmado.

Validação:

- teste automatizado cobre timeout após aceitação do comando e confirmação posterior por estado final.

## Riscos Técnicos Acompanhar

### Cache De Navegadores Embutidos

Apps abertos pelo OrcaSlicer podem manter cache agressivo e service worker antigo.

Impacto:

- mudanças de UI podem demorar a aparecer;
- links externos podem prender o usuário fora do Mainsail.

Mitigação:

- versionar assets;
- evitar dependência de hack em frontend de terceiros;
- preferir app próprio com rota de retorno clara.

### Firmware Flash

Flash incorreto pode deixar MCU fora do CAN.

Mitigação:

- dry-run;
- backup;
- UUID antes/depois;
- rollback documentado;
- confirmação explícita.

### Detecção De Plugins

Plugins podem estar instalados, mas não ativos.

Mitigação:

- diferenciar repo instalado, include ativo, módulo Python ativo e serviço systemd ativo.

### Relatórios Sanitizados

Logs podem conter dados sensíveis.

Mitigação:

- sanitização obrigatória;
- preview antes de exportar.

### Updater Do Próprio Printora

Atualizar backend, frontend e schema a partir da própria aplicação pode deixar o ambiente parcialmente atualizado se houver falha no meio do processo.

Durante o update real no Android/Termux, a conexão HTTP que disparou `POST /api/system/update/apply` pode cair quando as sessões `tmux` forem reiniciadas, mesmo que o script finalize com sucesso.

Validação real em 2026-05-23 encontrou e corrigiu um caso pior: quando o script era executado como filho direto do backend dentro do `tmux printora`, o `tmux kill-session -t printora` podia encerrar também o processo do update antes de marcar o run como `succeeded`.

Rollback é operação destrutiva sobre a pasta atual do projeto e pode restaurar um binário/código que ainda não contém os endpoints novos de histórico. O histórico SQLite não deve ser apagado e a UI deve tolerar queda de conexão durante restart.

Mitigação:

- plano read-only antes de aplicar;
- backup obrigatório do `printora.db`;
- execução Android destacada do processo web antes do restart;
- progresso persistido por etapa;
- rollback explícito;
- rollback exige `ROLLBACK PRINTORA`, paths absolutos seguros e backup gerado pelo updater;
- logs sanitizados.
- UI deve orientar recarregar e consultar `/api/system/update/history` após queda de conexão durante restart.

### GitHub Releases Rate Limit E Cache

Consulta pública ao GitHub Releases pode sofrer rate limit, ficar offline ou retornar dados defasados por cache intermediário.

Impacto:

- tela Configurações pode mostrar `limite do GitHub`, `GitHub offline` ou uma release antiga temporariamente;
- operador pode achar que não há update quando a resposta pública ainda não propagou.

Mitigação:

- consulta é read-only e não bloqueia o restante da tela;
- não há token obrigatório para repositório público;
- UI mantém botão manual `Verificar releases`;
- payload expõe `status`, `update_status` e erro resumido para diagnóstico;
- update real permanece fora do PKG-21.

### Versionamento De Schema SQLite

Aplicar scripts SQL novos em um banco local real pode falhar por corrupção prévia, arquivo bloqueado ou SQL inválido.

Mitigação:

- backup automático de `printora.db` antes de scripts pendentes;
- restauração automática do banco original em falha de aplicação;
- `PRAGMA integrity_check` obrigatório após schema;
- histórico em `schema_versions`, `app_version` e `schema_integrity_checks`.

Rollback:

- parar o app;
- restaurar o backup `printora.<timestamp>.before-schema.db` para `printora.db`;
- reiniciar o app e validar `GET /api/system/version`.
