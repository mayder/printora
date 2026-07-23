# Evidência Do Gate De Qualidade

Data de início: 2026-07-23
Pacote: PKG-97
Estado: em implementação

## Toolchain

- Node fixado em `22.22.x`, com `.node-version`, `.nvmrc`, `engines` e CI
  convergindo para `22.22.0`;
- npm fixado em `11.7.x`, com `packageManager`, `engine-strict` e CI convergindo
  para `11.7.0`;
- o gate roda no início de `check.sh`, no `preinstall` e no `prebuild`;
- Node `18.20.8`, `20.20.0`, `22.21.9`, `22.23.0` e `23.0.0` foram rejeitados;
- Node `22.22.0` e `22.22.9` foram aceitos;
- o Dockerfile usa imagem Node `22.22.0` e instalação limpa por `npm ci`.

## Evidência Pendente

- orçamento de bundle e warnings bloqueantes;
- cobertura Python, Go e frontend;
- E2E, acessibilidade e falhas de rede;
- property/fuzz e mutation;
- pentest independente e reteste;
- gate completo, CI, publicação e auditoria final.
