# Evidência de escala, resiliência e recuperação - 2026-07-23

## Escopo

- release exercitada: `aa80148cb300832f46066ffd893ffb2581a13342`;
- workflow aprovado: `29979938622`;
- host: servidor Cloud atual;
- fora do escopo: impressora, agente, Moonraker, Klipper, MCU e Raspberry Pi.

## Instâncias e deploy

- active slot: `blue`;
- `blue` e `replica` apontaram para a mesma release;
- `green` permaneceu em `25084bf` como rollback N-1 fora do upstream;
- Nginx carregou `8069` e `8071` como membros ativos equivalentes;
- preflight aprovou Nginx, slots, PostgreSQL, Redis, objetos, workers, backup,
  certificado, relógio e orçamento de recurso;
- workflow aprovou suíte completa, dependências, SBOM, bundle, cutover,
  drenagem e smoke público.

O primeiro ciclo atualizou o executor antigo e preservou o comportamento
blue/green. O ciclo seguinte inicializou a réplica e fez o cutover. Essa transição
confirmou que uma versão do executor não altera o upstream antes da readiness.

## Caos, backpressure e jobs

- parada controlada: somente `printora-cloud@blue.service`;
- durante a parada: 300 requests, zero erro, p95 1.287 ms;
- recuperação: `blue` e `replica` voltaram `active`, `/ready` permaneceu válido;
- sobrecarga: 1.000 requests produziram 600 sucessos e 400 respostas `429`,
  demonstrando backpressure sem indisponibilidade;
- carga durável: 500 jobs, 500 conclusões, zero duplicidade, 9,9 jobs/s;
- falha de lease: segunda tentativa concluiu e a conclusão antiga foi rejeitada;
- auditoria: zero job de agente sem evento e zero lease expirado.

## Soak e capacidade

- duração: 120 s;
- carga: 600 requests a 5 requests/s;
- erros: zero;
- maior p95 entre os lotes: 1.470 ms, abaixo do gate de 1.500 ms;
- CPU: 48 vCPU;
- memória disponível após o ensaio: 24.989.932 KiB;
- disco disponível após o ensaio: 115.883.248 KiB;
- utilização instantânea de disco no final: 0%.

O ensaio curto valida o gate do pacote no host atual. Tendência de longo prazo
continua dependente das métricas e alertas operacionais.

## Backup, retenção e restore

- snapshot externo criptografado: `38cb0d0f`;
- backup: 3,091 GiB processados em 88 s, 130,735 MiB armazenados;
- conteúdo: base física, dump lógico, WAL, objetos versionados, manifesto e
  configuração;
- configuração: 12 arquivos restaurados e validados por SHA-256;
- objetos: 8 versões validadas; 6 objetos canônicos reconciliados;
- banco: 146 tabelas, 86 revisões e zero FK inválida;
- busca: 364 documentos reconstruídos;
- restore isolado: 203 s, sem iniciar a aplicação restaurada;
- retenção: preview 14 diários, 8 semanais e 12 mensais;
- exclusão/prune: não executados.

Dois locks Restic obsoletos foram removidos somente após confirmar que o serviço
e processos de backup estavam inativos. Nenhum snapshot ou bloco foi removido.

## Perda simulada do host

A senha e a chave SSH mantidas no bundle privado externo foram comparadas com a
custódia configurada e acessaram o snapshot diretamente de uma máquina diferente
do servidor. A partir dessa cópia foram restaurados localmente o manifesto e os
12 arquivos de configuração, todos com checksum válido; o diretório temporário
foi eliminado após a validação.

- RPO observado no exercício manual: inferior a 1 minuto;
- RTO observado do início ao fim do restore integral: 203 s;
- alvo operacional de RTO: até 15 minutos no volume atual;
- pior caso de RPO físico pelo timer atual: até 24 h 15 min;
- RPO de deploy/cutover: zero para escritas confirmadas.

Não existe promessa de alta disponibilidade contra perda física do host. Outro
host ou réplica síncrona seria necessário para reduzir o pior caso físico.

## Rollback e integridade

- rollback de código permanece em `green` e reutiliza PostgreSQL/objetos atuais;
- restore nunca é usado para rollback de release;
- dados antigos, snapshots, WAL, versões de objeto e releases N-1 foram
  preservados;
- nenhuma tabela, linha, objeto, snapshot ou arquivo de produção foi apagado;
- owner operacional: administração da plataforma Printora.
