# Evidência De Fechamento — Onboarding Operacional

Data: 2026-08-02.

## Resultado

O Printora possui uma área global de primeiros passos, acessível pelo menu e por
uma chamada visível na Visão geral quando não há agente online. A pessoa segue
uma etapa por vez e recebe explicações curtas sobre Moonraker, agente e
preflight.

O guia não replica cadastros nem comandos físicos. Ele encaminha para os fluxos
canônicos e só conclui etapas remotas a partir de leituras autenticadas:

1. navegador e retomada local disponíveis;
2. Moonraker confirmado como conectado;
3. agente confirmado como online;
4. projeto pessoal existente;
5. preflight aprovado, sem iniciar impressão.

Falha de rede ou dependência mantém o ponto local de retorno, informa que a
confirmação está indisponível e não transforma ausência de resposta em sucesso.
Nenhuma credencial, token, URL privada ou payload sensível é salvo no progresso
local.

## Arquitetura E Rollback

- frontend lazy e responsivo, usando navegação, painéis, botões, cores e estados
  já existentes;
- agregação somente de serviços existentes; sem endpoint, tabela, migration ou
  SQL novo;
- progresso local versionado em `printora.onboarding.resume.v1`, contendo apenas
  passo e data;
- remoção da seção guiada restaura os fluxos anteriores sem alterar impressora,
  agente, projeto, job ou preflight;
- orçamento total passa de 3.440.000 para 3.460.000 bytes, crescimento inferior
  a 1%; limites individuais e gzip permanecem inalterados.

## Evidências Automatizadas

- unitários focados: 6 testes de regra, componente e navegação;
- E2E isolado: desktop Chromium e mobile Chromium, sem retry;
- E2E valida teclado, Axe, overflow, estado vazio, timeout e retomada local;
- testes existentes de agente validam token de uso único, conflito acionável
  para identidade ativa repetida, sanitização e isolamento;
- build TypeScript/Vite e orçamento de bundle;
- fechamento integral por `./check.sh`.

## Evidência Manual

Fluxo revisado no navegador local autenticado com dados sintéticos:

- entrada na Visão geral;
- navegação e tela do guia em desktop;
- layout mobile em 390 x 844;
- linguagem simples, hierarquia visual, estados textuais e ausência de
  identificadores internos na interface;
- fallback de cadastro da impressora preservado.

Nenhum comando de impressão, alteração de impressora física, deploy, push ou
publicação foi executado.
