# Perfis OrcaSlicer da Voron 2.4 350

Perfis versionados usados na Voron 2.4 350 com bico de 0,6 mm.

## Qualidade fina

- Processo: `V24 0.6 - 0.18 Qualidade Fina`
- Filamento: `Generic PLA @System - 20072023`

O processo preserva a primeira camada validada em 0,24 mm, largura inicial de
0,66 mm, demais larguras de 0,60 mm, compensação de pé de elefante desativada,
travessia de paredes reduzida e malha de velocidades de qualidade fina.

## Peça articulada

- Processo: `V24 0.6 - 0.18 Peça Articulada`
- Filamento: `Generic PLA - Peça Articulada`

Os dois presets devem ser selecionados juntos. O OrcaSlicer guarda temperatura
e overrides de retração no perfil de filamento, não no perfil de processo.

O conjunto articulado deriva do perfil de qualidade fina e altera somente:

- temperatura: 205 °C na primeira camada e 195 °C nas demais;
- retração: 0,7 mm a 35 mm/s, retorno a 30 mm/s;
- wipe: 1,5 mm;
- Z-hop: 0,20 mm;
- travel: 250 mm/s;
- `Avoid crossing walls` habilitado com desvio máximo de 50%.
