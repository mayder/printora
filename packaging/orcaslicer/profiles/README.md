# Perfis OrcaSlicer das Voron

Perfis versionados usados nas impressoras:

- Voron 2.4 350 com bico de 0,6 mm, prefixo `V24 0.6`;
- Voron 0.2 120 com bico de 0,4 mm, prefixo `V02 0.4`.

O OrcaSlicer identifica o modelo de sistema da Voron 0.2 como `Voron 0.1`.
O perfil de usuário corrige o nome visível e preserva o volume útil de
120 x 120 x 120 mm.

## Perfis de processo

As duas impressoras têm as mesmas 14 finalidades:

- 0,18 Peça Articulada;
- 0,18 Qualidade Fina;
- 0,20 Detalhe;
- 0,24 Qualidade Padrão;
- 0,24 Resistência;
- 0,24 Sem Suporte;
- 0,24 Superfície Lisa;
- 0,24 Suporte Orgânico Fácil;
- 0,24 Suporte Preciso;
- 0,24 Vase Mode;
- 0,28 Resistência Rápida;
- 0,30 Peças Grandes;
- 0,30 Rápido Limpo;
- 0,32 Rápido Forte.

Os perfis `V02 0.4` preservam a finalidade e os ajustes dos equivalentes
`V24 0.6`, mas usam herança compatível com bico de 0,4 mm e larguras de
extrusão proporcionais, nunca menores que o diâmetro do bico.

## Qualidade fina da Voron 2.4

- Processo: `V24 0.6 - 0.18 Qualidade Fina`
- Filamento: `Generic PLA @System - 20072023`

O processo preserva a primeira camada validada em 0,24 mm, largura inicial de
0,66 mm, compensação de pé de elefante de 0,01 mm, travessia de paredes
reduzida e malha de velocidades de qualidade fina.

## Peça articulada da Voron 2.4

- Processo: `V24 0.6 - 0.18 Peça Articulada`
- Filamento: `Generic PLA - Peça Articulada`

Os dois presets devem ser selecionados juntos. O OrcaSlicer guarda temperatura
e overrides de retração no perfil de filamento, não no perfil de processo.

O processo articulado é mais conservador: parede externa a 30 mm/s, interna a
50 mm/s, travel a 160 mm/s e aceleração de travel em 1.500 mm/s². O filamento
usa 205 °C na primeira camada, 200 °C nas demais, retração de 0,7 mm,
wipe de 1,5 mm e Z-hop de 0,60 mm.

## Instalação local da Voron 0.2

Com o OrcaSlicer fechado:

```bash
python3 scripts/orcaslicer/install-voron-02-profiles.py
```

Esse primeiro comando somente valida os 28 perfis e não altera o OrcaSlicer.
Se a validação terminar sem erro, instale com:

```bash
python3 scripts/orcaslicer/install-voron-02-profiles.py --apply
```

O instalador:

- cria backup dos perfis e da configuração atuais;
- usa como fonte os 14 perfis `V24 0.6` versionados;
- valida e instala os 14 equivalentes `V02 0.4` versionados;
- restaura a impressora `Voron 0.2 120 0.4 nozzle - 290126`;
- mantém a impressora selecionada e os demais modelos configurados.
