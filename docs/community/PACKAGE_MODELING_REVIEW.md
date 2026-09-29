# Reavaliação Do Portfólio Pós-PKG-100

Data: 2026-07-27.

## Problema

O programa anterior transformava 55 frentes de brainstorming em 55 pacotes
obrigatórios, 440 capacidades, 3.080 requisitos genéricos e 440 famílias de
tela. A regra numérica fazia funcionalidades operacionais úteis dependerem de
rede social, marketplace, educação, finanças e experimentos sem demanda
comprovada.

O baseline `ausente` também divergia do código real: autenticação, moderação,
busca, projetos, upload, slicing, preflight, entrega, histórico, manutenção,
múltiplas impressoras e integrações já possuíam implementações parciais.

## Critérios

Cada pacote pendente foi avaliado por:

1. problema real do usuário;
2. aderência ao núcleo operacional do Printora;
3. sobreposição com código existente;
4. custo permanente de operação, segurança e suporte;
5. risco físico, jurídico ou financeiro;
6. possibilidade de entrega e rollback independentes;
7. existência de demanda ou hipótese mensurável.

## Resultado

- 5 pacotes concluídos e preservados;
- 10 pacotes ativos;
- 10 IDs fundidos nos ativos;
- 4 ideias adiadas sem autorização de implementação;
- 26 pacotes cancelados.

O estado e a justificativa de cada ID estão em `PACKAGE_PORTFOLIO.csv`.

## Portfólio Preservado E Ativo

| Ordem | Pacote | Resultado |
|---|---|---|
| 1 | PKG-104 | proteção essencial, consolidando segurança, privacidade, integridade e moderação mínima |
| 2 | PKG-110 | onboarding até impressora conectada e primeiro fluxo seguro |
| 3 | PKG-114 | materiais, spools, consumo e qualidade básica |
| 4 | PKG-126 | conhecimento e evidência técnica reproduzível |
| 5 | PKG-128 | projetos, arquivos, versões e inspeção 3D básica |
| 6 | PKG-131 | perfis executáveis e fatiamento reproduzível |
| 7 | PKG-132 | fluxo projeto até resultado de impressão |
| 8 | PKG-133 | manutenção, diagnóstico e confiabilidade |
| 9 | PKG-134 | frota e filas de impressão |
| 10 | PKG-141 | captura guiada, cobertura, escala e privacidade das fotos |
| 11 | PKG-142 | integrações reais e descoberta técnica |
| 12 | PKG-153 | reconstrução 3D multiview rastreável e substituível |
| 13 | PKG-154 | qualificação, reparo assistido e entrega do modelo imprimível |

## Regras De Modelagem

- número é identidade histórica, não dependência;
- dependência técnica fica na matriz arquitetural;
- pacote cancelado, fundido ou adiado não pode ser dependência;
- inventário `COM/CAP/SCR` é histórico de ideias;
- cada pacote começa por testes de caracterização do comportamento existente;
- escopo útil fundido é implementado no owner ativo, sem criar módulo por ID;
- funcionalidade existente de pacote cancelado não é removida automaticamente;
- qualquer reativação exige decisão de produto e atualização do portfólio.

## Ownership E Risco

`PACKAGE_ARCHITECTURE.csv` cobre somente pacotes ativos e fixa:

- owner backend;
- colaboradores permitidos;
- área frontend;
- perfil de risco;
- dependências explícitas.

Colaboração ocorre por contrato, port, evento ou application service. Número de
pacote não autoriza importação interna.

## Riscos Residuais

- os pacotes ativos ainda precisam de auditoria de lacunas antes do código;
  onboarding e materiais já foram concluídos com evidência própria;
- parte da documentação histórica continua descrevendo ideias canceladas;
- funcionalidades parciais existentes podem exigir consolidação ou remoção em
  demanda futura própria;
- IA e visão computacional genéricas, internacionalização, coautoria e API
  pública permanecem adiadas; captura/reconstrução por fotos está autorizada
  somente nos limites de `PKG-141`, `PKG-153` e `PKG-154`;
- validação física continua dependendo de impressora segura e autorização.

## Veredito

O backlog ativo está apto para execução na ordem topológica explícita de
`DEMANDAS.md`. O inventário histórico não deve voltar a ser interpretado como
Definition of Done ou obrigação de implementação.
