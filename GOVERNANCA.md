# GOVERNANCA.md

## Objetivo

Definir regras de segurança, prioridade, riscos e rollback para o Printora.

## Princípios

- Segurança da impressora vem antes de conveniência.
- O usuário deve entender o que será alterado antes de ações perigosas.
- Backup deve ser automático antes de qualquer mutação relevante.
- Flash de firmware deve ser tratado como operação crítica.
- Diagnóstico deve ser preferido a tentativa cega de correção.

## Escopo Seguro

Operações consideradas seguras:

- leitura de logs;
- leitura de status Moonraker/Klipper;
- leitura de status CAN;
- leitura de Update Manager;
- leitura de systemd;
- geração de relatório sanitizado;
- criação de backup;
- dry-run de comandos.

Operações que exigem confirmação:

- editar configs Klipper/Moonraker/Mainsail;
- reiniciar Klipper;
- reiniciar Moonraker;
- reiniciar serviços systemd;
- aplicar update;
- compilar firmware;
- fazer flash de MCU;
- restaurar backup.

Operações proibidas sem fluxo explícito:

- apagar configs sem backup;
- apagar histórico;
- sobrescrever `.config` de firmware;
- fazer flash se impressora estiver imprimindo;
- rodar comandos destrutivos sem rollback.

## Gates De Release

Uma versão só pode ser considerada publicável se:

- `./check.sh` passar;
- documentação principal estiver atualizada;
- riscos conhecidos estiverem em `BUGS.md`;
- fluxos perigosos tiverem confirmação e dry-run;
- dados sensíveis não estiverem versionados;
- o rollback mínimo estiver documentado.
- a tag da versao estiver publicada no remoto;
- a GitHub Release correspondente estiver criada, pois o verificador de releases do app usa GitHub Releases como fonte publica.

Migrations são proibidas. Toda alteração de banco deve ser entregue como script `.sql` idempotente em `backend/sql/`, com rollback e impacto documentados.

### Gates De Evolução Arquitetural

Os pacotes `PKG-86` a `PKG-95` seguem
`docs/architecture/EVOLUCAO_ARQUITETURAL.md` e só podem avançar quando:

- a capacidade de CPU, RAM, disco, I/O e file descriptors do servidor atual foi medida;
- o destino roda em paralelo sem receber tráfego produtivo prematuramente;
- backup foi restaurado e validado em ambiente isolado;
- dados foram reconciliados por contagem, checksum, chaves, sequences e consultas semânticas;
- deploy/cutover possui health, readiness, canário, drenagem e rollback sem restaurar snapshot velho sobre escritas novas;
- toda escrita mutável possui idempotência e outbox quando cruza processo/tecnologia;
- a observação pós-cutover não registra erro, perda, duplicidade ou regressão de SLO atribuível à troca;
- bridges, dual-read, dual-write e flags temporárias são removidos no mesmo pacote;
- referências à tecnologia aposentada são zeradas em runtime, configuração, dependências, SQL ativo, scripts, workflow, tests e docs;
- limpeza de banco, tabela, arquivo, backup ou objeto antigo recebe confirmação humana explícita.
- release blue/green não compartilha virtualenv, frontend ou dependência mutável;
- retenção de release preserva obrigatoriamente todos os alvos de `current`,
  `blue`, `green` e `replica`; somente diretório imutável sem vínculo pode ser
  removido automaticamente;
- capacidade de disco gera aviso abaixo de 15% livre e bloqueia deploy abaixo
  de 10%; o bloqueio não pode ser retirado para acelerar publicação;
- schema, evento e contrato preservam compatibilidade N/N-1 durante a drenagem;
- o perfil cloud não carrega SQLite; o adapter SQLite local fica isolado e testado;
- backup/WAL criptografado possui cópia fora do host e restore independente;
- serviço novo possui role mínima, segredo rotacionável, quota, retenção, alerta,
  owner, atualização e procedimento de remoção.

O servidor atual pode oferecer redundância de processo e deploy sem
indisponibilidade observável. Não é permitido classificar isso como alta
disponibilidade contra perda física do host; esse nível exige outro host.

O fechamento de cada transição deve anexar relatório de integridade, relatório
de referências legadas, teste de restauração, capacidade residual, período de
observação, responsável e rollback ainda disponível.

Nenhum pacote pode prometer simultaneamente execução em um único host e RPO zero
contra destruição física desse host. RPO zero é obrigatório para deploy/cutover;
desastre físico usa RPO/RTO medidos pela cópia externa até existir réplica
síncrona autorizada em outro host.

Todos os pacotes arquiteturais exigem threat model, autorização backend
deny-by-default, isolamento owner/tenant, rate limit, idempotência, validação de
entrada, proteção SSRF/upload, SQL parametrizado, secrets fora do release,
dependências fixadas/SBOM, scans de segredo/dependência, artefatos verificáveis,
logs sanitizados e plano de incidente. Tela desabilitada nunca substitui
controle de permissão no backend.

### Gates De Confiança Pós-Arquitetura

Os pacotes `PKG-96` a `PKG-99` só podem fechar quando:

- versão de agente identifica exatamente um conjunto de fontes/binários;
- plataforma anunciada possui artefato, checksum, assinatura e teste real;
- Node incompatível bloqueia antes do build;
- cobertura mínima global/crítica e não regressão estão ativas;
- E2E executa fluxos P0/P1 com isolamento entre usuários/organizações;
- fuzzing/property testing e mutation testing produzem evidência reproduzível;
- pentest independente não deixa achado crítico/alto aberto ou sua dispensa
  explícita pelo owner registra escopo não testado, risco residual e revisão
  futura sem apresentar os demais testes como equivalentes;
- validação física respeita estado da impressora e nunca usa impressão ativa
  para mutação não autorizada;
- soak final é contínuo; falha reinicia a janela afetada;
- RPO/RTO são medidos e alertados, não apenas descritos;
- relatório final lista explicitamente escopo testado, não testado e risco residual.

Pentest, fuzz, carga e E2E em produção precisam de autorização e escopo
específicos. Teste destrutivo, prune, flash, restart de Klipper/Moonraker,
alteração de firmware ou comando físico perigoso não é autorizado por esses
pacotes.

Em branch `main` ou `hml`, a IA deve perguntar antes de editar quando o usuário não tiver autorizado explicitamente o uso da branch.

## Riscos Principais

### Firmware

Risco: flash incorreto pode deixar MCU offline.

Mitigações:

- preservar `.config`;
- preservar binário anterior;
- validar UUID antes e depois;
- registrar comando usado;
- exigir checklist antes do flash;
- fornecer rollback manual.

### Configuração Klipper

Risco: alteração incorreta pode impedir Klipper de iniciar.

Mitigações:

- backup antes da edição;
- validação de includes;
- reinício controlado;
- confirmação de `printer/info ready`.

### Banco Local

Risco: corromper histórico ou inventário.

Mitigações:

- SQLite com backup;
- scripts SQL idempotentes e versionamento interno, sem migration de framework;
- exportação de dados;
- nunca armazenar segredo em texto puro.

### Transição De Banco E Storage

Risco: perda, duplicidade, divergência silenciosa ou permanência indefinida de
dois caminhos autoritativos.

Mitigações:

- snapshot consistente e captura incremental por watermark/outbox;
- import idempotente e leitura sombra antes do canário;
- reconciliação antes e depois do cutover;
- uma única fonte autoritativa em cada instante;
- ponte temporária removida antes do fechamento do pacote;
- banco/storage antigo preservado somente durante a janela de rollback;
- exclusão física apenas após aceite explícito do relatório de integridade;
- restore validado antes de qualquer exclusão.

### Relatórios

Risco: vazar senhas, tokens, IPs ou dados privados.

Mitigações:

- sanitização obrigatória;
- preview antes de exportar;
- lista de campos removidos.

### Observabilidade Do Agente

Risco: dados de suporte exporem credenciais, tokens, chaves ou payload sensível.

Mitigações:

- pacote de suporte sanitizado por padrão;
- nunca retornar credencial completa do agente;
- redigir tokens `ptr_agent_*`, `ptr_pair_*` e `ptr_sess_*`;
- limitar log tail e eventos recentes;
- retenção operacional de eventos/jobs de agente em 180 dias;
- limpeza somente por rotina supervisionada enquanto não houver job dedicado de retenção.

## Priorização

Ordem recomendada:

1. Auditoria somente leitura.
2. Checklist pós-update.
3. Health check.
4. Backups.
5. Relatórios.
6. Diário/manutenção.
7. Z-offset e primeira camada.
8. Monitor CAN histórico.
9. Gestão de plugins.
10. Firmware Manager com dry-run.
11. Firmware Manager com flash real.

### Programa comunitário plurianual

Para itens de `docs/community/`, a prioridade é definida por impacto social, não por potencial de engajamento ou receita:

1. `P0`: vida, autonomia, proteção infantil, segurança física/digital, privacidade, integridade e moderação;
2. `P1`: acessibilidade, mobile/offline, educação, escolas, reparo, sustentabilidade, fabricação local e qualidade;
3. `P2`: núcleo comunitário, conhecimento, colaboração, modelos, slicing, impressão em rede e integrações;
4. `P3`: creator economy, marketplace, logística, reputação, concursos e financiamento;
5. `P4`: AR, IA generativa e interfaces experimentais.

Critérios de desempate: alcance, urgência, equidade, redução de dano, dependência estrutural, evidência, custo de oportunidade e reversibilidade.

Itens `P0` exigem especialista da área quando aplicável, revisão independente, piloto controlado, métrica de dano, canal de incidente e rollback antes de escala. Funcionalidades comerciais não podem bloquear acesso a alertas de segurança, atribuição, denúncia, exportação de dados ou conhecimento essencial de reparo e uso responsável.

## Rollback

Todo módulo que altera algo deve registrar:

- arquivo afetado;
- backup criado;
- comando executado;
- resultado;
- instrução de rollback.

Rollback mínimo para configs:

```bash
cp /path/do/backup.cfg /home/pi/printer_data/config/arquivo.cfg
sudo systemctl restart klipper
curl -s http://127.0.0.1:7125/printer/info
```

Rollback mínimo para firmware:

```text
1. localizar binário anterior;
2. colocar placa em bootloader;
3. executar comando de flash anterior;
4. validar UUID;
5. reiniciar Klipper;
6. confirmar printer/info ready.
```
