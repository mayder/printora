# BUGS.md

## Bugs Conhecidos

Nenhum bug de implementação registrado ainda. O projeto está em fase de escopo.

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
