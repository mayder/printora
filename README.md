<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="identidade/printora-logo-horizontal-dark-bg.png">
    <img src="identidade/printora-logo-horizontal-color.png" alt="Printora" width="620">
  </picture>
</p>

Printora é uma aplicação local para acompanhar, diagnosticar e manter impressoras 3D com Klipper/Moonraker.

O foco é segurança operacional: ler o estado real da impressora, registrar histórico, gerar evidências e reduzir risco antes de updates, manutenção, ajustes ou planejamento de firmware.

## Para Que Serve

- cadastrar e selecionar múltiplas impressoras Klipper/Moonraker;
- acompanhar visão geral, health check e alertas;
- visualizar operação ao vivo da impressora ativa;
- consultar Update Manager e checklist pós-update;
- registrar manutenção preventiva, diário técnico e horas de impressão;
- capturar snapshots read-only e comparar mudanças;
- gerar relatórios sanitizados para compartilhar sem expor dados sensíveis;
- acompanhar histórico CAN, Z-offset e calibração;
- planejar build e flash de firmware com fluxo conservador.

## Estado Atual

Esta versão é local, gratuita e ainda está em teste.

Por padrão, o Printora é conservador:

- não envia G-code pelo launcher rápido;
- não reinicia Klipper, Moonraker ou systemd pelo launcher rápido;
- não faz flash de firmware pelo launcher rápido;
- salva os dados em SQLite no computador ou dispositivo onde a aplicação está rodando.

## Instalação

A porta padrão é:

```text
http://127.0.0.1:8069
```

Escolha o guia do seu sistema:

- [macOS](docs/INSTALL_MACOS.md)
- [Windows](docs/INSTALL_WINDOWS.md)
- [Android com Termux](docs/INSTALL_ANDROID_TERMUX.md)
- [Linux/Raspberry/CB1/Manta](docs/INSTALL_LINUX_RASPBERRY.md)
- [Docker](docs/INSTALL_DOCKER.md)

Para instalação local, prefira clonar com Git em vez de baixar o ZIP do GitHub. Isso preserva o fluxo de update.

Os guias usam instaladores assistidos que verificam o ambiente, mostram o que já está OK e perguntam antes de instalar dependências ausentes.

## Configurar Impressora

Depois de abrir o Printora, cadastre a URL Moonraker da impressora pela interface.

Exemplo:

```text
http://voron.local:7125
```

Também é possível iniciar o app com uma URL padrão:

```bash
PRINTORA_MOONRAKER_URL=http://sua-impressora.local:7125 ./scripts/run_app.sh
```

## Dados Locais

O banco local é `printora.db`.

- macOS: `~/Library/Application Support/Printora`
- Windows: `%LOCALAPPDATA%\Printora`
- Linux/Raspberry: `~/.local/share/printora`
- Android/Termux: `~/.local/share/printora`
- Docker: volume `printora-data`

## Diagnóstico

Se a instalação não abrir:

```bash
PRINTORA_PORT=8069 ./scripts/doctor_install.sh
```

Se um update local ficar travado em `em execução`, use a ação `Atualizar status` no histórico de updates. Em instalações antigas, antes dessa ação existir, use:

```bash
./scripts/unlock_update.sh
```

## Documentação Pública

- [Escopo do projeto](ESCOPO.md)
- [Backlog de funcionalidades](DEMANDAS.md)
- [Recursos e endpoints](docs/FEATURES.md)
- [Plano diretor da comunidade](docs/community/MASTER_PLAN.md)
- [Benchmark de redes e impressão 3D](docs/community/PLATFORM_BENCHMARK.md)
- [Inventário completo de melhorias](docs/community/COMMUNITY_BACKLOG.md)
- [Catálogo futuro de telas](docs/community/COMMUNITY_SCREENS.md)
- [Evolução arquitetural em quatro etapas](docs/architecture/EVOLUCAO_ARQUITETURAL.md)
- [Revisão e matriz de cobertura arquitetural](docs/architecture/REVISAO_PACOTES.md)
- [Instalação por plataforma](docs/INSTALL_MULTIPLATFORM.md)

## Licença

Printora é open source sob a licença MIT. Veja [LICENSE](LICENSE).

O software é fornecido sem garantia. Operações em impressoras, firmware, Moonraker, Klipper, systemd ou arquivos de configuração devem ser revisadas pelo usuário antes de execução real.

## Links

- Projeto: <https://github.com/mayder/printora>
- Autor: <https://www.linkedin.com/in/brenomayder/>
- Instagram: <https://www.instagram.com/brenomayder>
