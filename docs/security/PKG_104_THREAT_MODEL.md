# PKG-104 — Threat model

Data: 2026-07-27.

## Ativos e fronteiras

- credenciais, MFA, sessões e autorizações reforçadas;
- dados pessoais, localização, organizações e perfil social;
- comandos físicos enviados ao agente;
- binários do agente e manifesto de atualização;
- denúncias, bloqueios, remoções lógicas e recursos;
- logs, bundles de suporte e trilhas de auditoria.

A interface não é fronteira de confiança. Toda decisão de owner, organização,
recurso, papel e finalidade do step-up é revalidada no backend. Agente,
Moonraker, host remoto, Redis e URLs externas são fronteiras não confiáveis.

## Ameaças e controles

| Ameaça | Controle verificável |
| --- | --- |
| tomada de conta e reutilização de sessão | MFA com segredo pendente, revogação de sessões e senha revogando todas as sessões |
| replay de ação crítica | step-up curto, vinculado à finalidade e consumido atomicamente uma vez |
| escalada de papel | admin não cria, convida ou aceita owner; owner e recurso são revalidados |
| comando físico indevido | setup físico exige administrador e step-up; endpoint genérico aceita apenas jobs inofensivos |
| injeção em shell | valores derivados de requisição são citados com regra de shell e cobertos por teste |
| vazamento de dados | exportação minimizada exclui hashes, tokens e segredos; logs e bundles aplicam redação recursiva |
| abuso social | bloqueio bidirecional também no feed/discussão, rate limit, remoção lógica, recurso restrito ao autor e fila administrativa |
| duplicidade ou corrida | chave idempotente, constraints e consumo atômico concorrente |
| artefato adulterado ou replayado | manifesto com identidade de chave e assinatura Ed25519 sobre plataforma, versão, checksum SHA-256 e limites de protocolo antes da troca |
| falha de dependência antiabuso | autenticação falha fechada quando Redis configurado degrada |
| IDOR por identificador global | backup, manutenção, snapshot e firmware revalidam o recurso pai no escopo do usuário antes de retornar ou alterar |
| origem de update controlada pelo cliente | aplicação usa somente o repositório configurado; agente limita release e redirecionamentos à origem do manifesto |
| execução de instalador remoto | bootstrap falha fechado quando Homebrew ou nvm não existem e não executa resposta HTTP |
| MITM no primeiro SSH | workflows exigem `PRINTORA_SSH_KNOWN_HOSTS` previamente validado e não fazem descoberta durante o deploy |
| exposição de armazenamento social | respostas públicas removem `storage_key`, quarentena e motivo interno; owner mantém diagnóstico autenticado |
| bypass comunitário ou de bloqueio | busca SQLite exige associação ativa para conteúdo comunitário e exclui bloqueios em ambos os sentidos |
| arquivo comprimido ou metadado abusivo | leitura de ZIP tem teto por entrada, total e razão; metadados têm profundidade, contagem e tamanho máximos |
| mutação física sem prova humana | toda ação exige preview, frase enviada pelo cliente, step-up e bloqueio durante impressão |

## Riscos residuais

- a recuperação dentro da retenção de 180 dias é procedimento operacional, não
  autoatendimento;
- a chave privada de release permanece fora do repositório e sua rotação exige
  release coordenada do backend e do agente;
- releases legadas assinadas somente pelo digest ficam com auto-update
  desativado; uma nova publicação exige a carga canônica vinculada aos metadados;
- moderação multimídia, fraude comportamental e identidade comercial estão fora
  do pacote.
