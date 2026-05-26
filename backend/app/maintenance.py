from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.database import connect_database


MaintenanceEventType = Literal["maintenance", "failure", "adjustment", "note"]
MaintenanceIntervalKind = Literal["days", "print_hours"]
TaskDueStatus = Literal["due", "soon", "ok", "unknown", "not_validated", "needs_review"]


def _help(how_to: list[str], why: str, prevents: list[str], recommendation: str) -> dict[str, Any]:
    return {
        "how_to": how_to,
        "why": why,
        "prevents": prevents,
        "recommendation": recommendation,
    }


DEFAULT_PREVENTIVE_TASKS = [
    {"name": "Limpar superfície da mesa", "component": "mesa", "interval_days": 7},
    {"name": "Inspecionar adesão da mesa", "component": "mesa", "interval_days": 14},
    {"name": "Verificar nivelamento mecânico da mesa", "component": "mesa", "interval_days": 30},
    {"name": "Revisar Z-offset aprovado", "component": "calibração", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Refazer malha da mesa", "component": "calibração", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 200},
    {"name": "Limpar poeira da estrutura", "component": "estrutura", "interval_days": 30},
    {"name": "Conferir parafusos estruturais", "component": "estrutura", "interval_days": 60},
    {"name": "Conferir esquadro da estrutura", "component": "estrutura", "interval_days": 90},
    {"name": "Verificar tensão das correias", "component": "movimento", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Inspecionar desgaste das correias", "component": "movimento", "interval_days": 60, "recommended_interval_kind": "print_hours", "recommended_interval_value": 250},
    {"name": "Lubrificar trilhos lineares", "component": "movimento", "interval_days": 45, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Limpar trilhos e guias", "component": "movimento", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Inspecionar roldanas, polias e idlers", "component": "movimento", "interval_days": 60, "recommended_interval_kind": "print_hours", "recommended_interval_value": 250},
    {"name": "Conferir aperto de polias nos motores", "component": "movimento", "interval_days": 60, "recommended_interval_kind": "print_hours", "recommended_interval_value": 250},
    {"name": "Limpar bico externamente", "component": "hotend", "interval_days": 14, "recommended_interval_kind": "print_hours", "recommended_interval_value": 50},
    {"name": "Inspecionar bico por desgaste ou entupimento", "component": "hotend", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Conferir aperto do hotend em temperatura segura", "component": "hotend", "interval_days": 90, "recommended_interval_kind": "print_hours", "recommended_interval_value": 300},
    {"name": "Inspecionar vazamento de filamento no hotend", "component": "hotend", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Limpar engrenagens do extrusor", "component": "extrusor", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Verificar pressão/tensão do extrusor", "component": "extrusor", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Inspecionar tubo PTFE ou guia de filamento", "component": "filamento", "interval_days": 45, "recommended_interval_kind": "print_hours", "recommended_interval_value": 250},
    {"name": "Limpar caminho do filamento", "component": "filamento", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Inspecionar sensor de filamento", "component": "filamento", "interval_days": 45, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Limpar fans e dutos", "component": "refrigeração", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Verificar ruído ou folga dos fans", "component": "refrigeração", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Limpar filtro de ar ou carvão ativado", "component": "refrigeração", "interval_days": 30, "recommended_interval_kind": "print_hours", "recommended_interval_value": 100},
    {"name": "Inspecionar cabos do toolhead", "component": "elétrica", "interval_days": 30},
    {"name": "Inspecionar conectores CAN/USB", "component": "elétrica", "interval_days": 30},
    {"name": "Conferir fixação e alívio de tensão dos cabos", "component": "elétrica", "interval_days": 45},
    {"name": "Inspecionar fonte, borne e aterramento visualmente", "component": "elétrica", "interval_days": 90},
    {"name": "Conferir câmera e iluminação", "component": "acessórios", "interval_days": 60},
    {"name": "Conferir spool holder e caminho até a impressora", "component": "acessórios", "interval_days": 30},
    {"name": "Revisar macros e perfil do slicer após mudanças", "component": "software", "interval_days": 90},
]


MAINTENANCE_HELP_BY_TASK = {
    "limpar superfície da mesa": _help(
        [
            "Remova a chapa quando o material permitir e espere a superfície chegar a uma temperatura segura.",
            "Retire restos de plástico com espátula adequada, sem riscar a superfície.",
            "Limpe gordura e poeira com o método compatível com a chapa usada.",
            "Reinstale a chapa bem assentada e valide a primeira camada em uma área pequena.",
        ],
        "A superfície da mesa define a aderência inicial. Gordura, poeira e resíduo de filamento mudam o Z real e prejudicam a primeira camada.",
        ["Peça soltando no meio da impressão.", "Warping por baixa aderência.", "Ajuste errado de Z-offset para compensar sujeira."],
        "Faça antes de peças longas, troca de material ou sempre que tocar na mesa com a mão.",
    ),
    "inspecionar adesão da mesa": _help(
        [
            "Observe marcas de desgaste, zonas brilhantes, bolhas, riscos profundos ou pontos onde a peça costuma soltar.",
            "Faça uma linha ou quadrado curto de teste nas áreas mais usadas da chapa.",
            "Compare centro e cantos para saber se o problema é sujeira, chapa ou nivelamento.",
        ],
        "A aderência pode cair mesmo com a mesa limpa, principalmente em chapas gastas ou materiais exigentes.",
        ["Falha repetida no mesmo ponto da chapa.", "Perda de peças grandes depois de várias horas.", "Diagnóstico errado de fluxo ou temperatura."],
        "Se uma região falhar duas vezes, limpe novamente, gire a chapa se possível ou troque a superfície.",
    ),
    "verificar nivelamento mecânico da mesa": _help(
        [
            "Aqueça a impressora nas condições normais de uso.",
            "Confirme se chapa e base estão bem assentadas e sem sujeira entre elas.",
            "Execute a rotina de nivelamento aplicável ao modelo e observe se algum canto fica fora do padrão.",
            "Após ajuste mecânico, refaça a malha ou a validação de primeira camada.",
        ],
        "Nivelamento mecânico ruim força o firmware a compensar demais e reduz a margem da primeira camada.",
        ["Primeira camada boa em um canto e ruim em outro.", "Mesh muito inclinada.", "Bico raspando ou imprimindo alto em regiões diferentes."],
        "Mexa mecanicamente só quando houver desvio claro; pequenas variações podem ser tratadas pela malha.",
    ),
    "revisar z-offset aprovado": _help(
        [
            "Limpe bico e mesa antes de medir.",
            "Aqueça mesa e hotend como em uma impressão real.",
            "Rode a rotina de Z-offset e compare com o último valor aprovado.",
            "Faça uma primeira camada curta para validar se as linhas aderem sem raspar.",
        ],
        "Z-offset muda com bico, chapa, temperatura e manutenção mecânica. Valor antigo pode deixar de representar a distância real.",
        ["Bico riscando a chapa.", "Primeira camada solta.", "Compensação errada depois de troca de bico ou chapa."],
        "Revalide após trocar bico, chapa, hotend, probe ou depois de colisão.",
    ),
    "refazer malha da mesa": _help(
        [
            "Aqueça a mesa e aguarde estabilizar.",
            "Garanta que a chapa esteja limpa e travada na posição correta.",
            "Execute a geração de malha com a configuração usada normalmente.",
            "Salve ou aplique conforme o fluxo da impressora e valide com primeira camada.",
        ],
        "A malha representa a geometria atual da superfície. Mudanças térmicas ou mecânicas tornam a malha antiga menos confiável.",
        ["Primeira camada irregular em regiões específicas.", "Compensação antiga após manutenção.", "Problemas de aderência sem causa aparente."],
        "Refaça após troca de chapa, ajuste de mesa, colisão ou mudanças relevantes de temperatura de trabalho.",
    ),
    "limpar poeira da estrutura": _help(
        [
            "Desligue a impressora se for limpar perto de eletrônica ou fans.",
            "Use pincel macio, ar controlado ou pano seco para tirar poeira de perfis, cantos e painéis.",
            "Não empurre sujeira para trilhos, rolamentos, fonte ou placas.",
        ],
        "Poeira acumulada entra em fans, trilhos e conectores, aumentando ruído, desgaste e aquecimento.",
        ["Fan perdendo fluxo.", "Sujeira em trilhos.", "Aquecimento e mau contato por acúmulo em eletrônica."],
        "Faça com mais frequência em ambiente aberto, oficina ou quando imprimir materiais que soltam pó.",
    ),
    "conferir parafusos estruturais": _help(
        [
            "Com a impressora parada, pressione levemente pontos da estrutura e procure folga.",
            "Verifique parafusos de perfis, painéis, suportes e peças impressas críticas.",
            "Reaperte apenas parafusos frouxos; não force roscas em alumínio ou plástico.",
        ],
        "Parafuso frouxo vira vibração e perda de repetibilidade, especialmente em impressoras rápidas.",
        ["Ringing por vibração.", "Peça impressa trincando por esforço.", "Desalinhamento progressivo da estrutura."],
        "Se vários parafusos estavam frouxos, faça uma validação curta de movimento depois.",
    ),
    "conferir esquadro da estrutura": _help(
        [
            "Meça diagonais ou use referência mecânica compatível com o modelo.",
            "Procure diferença entre lados, torção em painéis e desalinhamento de eixos.",
            "Corrija em pequenos passos e valide movimento livre depois de cada ajuste.",
        ],
        "Esquadro ruim afeta geometria, movimento e acabamento mesmo quando firmware e slicer parecem corretos.",
        ["Peças fora de medida.", "Movimento com esforço desigual.", "Correções artificiais no slicer para problema mecânico."],
        "Faça depois de transporte, desmontagem, colisão ou troca de partes estruturais.",
    ),
    "verificar tensão das correias": _help(
        [
            "Com a máquina parada, compare a tensão entre lados equivalentes.",
            "Procure correia frouxa, muito esticada ou com som/deflexão diferente entre eixos.",
            "Ajuste em pequenos passos e mova o eixo para confirmar que não ficou pesado.",
        ],
        "Tensão incorreta altera resposta do movimento e qualidade das paredes.",
        ["Layer shift.", "Ringing excessivo.", "Desgaste de rolamentos, idlers e motores por tensão alta."],
        "Depois de ajustar, rode uma peça de teste curta antes de imprimir algo longo.",
    ),
    "inspecionar desgaste das correias": _help(
        [
            "Examine dentes, laterais e regiões próximas a polias/idlers.",
            "Procure fios soltos, rachaduras, marcas brilhantes ou desgaste lateral.",
            "Verifique se a correia está alinhada e não raspa em flange ou peça impressa.",
        ],
        "Correia desgastada pode falhar sem aviso e costuma dar sinais antes de romper.",
        ["Perda de passo por dente danificado.", "Rompimento durante impressão.", "Desgaste acelerado por desalinhamento."],
        "Troque a correia se houver fibra exposta, dente danificado ou desgaste lateral consistente.",
    ),
    "lubrificar trilhos lineares": _help(
        [
            "Limpe sujeira superficial antes de aplicar lubrificante.",
            "Use lubrificante compatível com o trilho e aplique pouca quantidade.",
            "Movimente o eixo algumas vezes para distribuir.",
            "Remova excesso para não capturar poeira.",
        ],
        "Lubrificação correta reduz atrito e desgaste nos carros lineares.",
        ["Movimento áspero.", "Ruído em trilhos.", "Desgaste prematuro de guia e patins."],
        "Não misture lubrificantes sem limpar antes; excesso também prejudica.",
    ),
    "limpar trilhos e guias": _help(
        [
            "Passe pano sem fiapos na região exposta dos trilhos.",
            "Remova poeira e resíduos antes que entrem no carro linear.",
            "Movimente o eixo para acessar outras regiões e repita a limpeza.",
        ],
        "Trilho sujo transforma poeira em abrasivo e aumenta esforço de movimento.",
        ["Risco no trilho.", "Ponto duro no movimento.", "Falha de qualidade por atrito variável."],
        "Limpe antes de lubrificar; lubrificante sobre sujeira piora o desgaste.",
    ),
    "inspecionar roldanas, polias e idlers": _help(
        [
            "Gire idlers e polias com cuidado e procure ruído, folga ou resistência.",
            "Verifique se parafusos e espaçadores estão firmes.",
            "Observe se a correia corre centralizada e sem raspar.",
        ],
        "Polias e idlers guiam a correia; qualquer folga vira erro de movimento.",
        ["Correia comendo lateral.", "Ruído e vibração.", "Layer shift ou irregularidade em paredes."],
        "Substitua rolamento/idler se houver ruído áspero ou folga perceptível.",
    ),
    "conferir aperto de polias nos motores": _help(
        [
            "Desligue motores e acesse as polias com segurança.",
            "Confira se o grub screw está apertado no plano correto do eixo quando aplicável.",
            "Procure marca de polia escorregando no eixo.",
        ],
        "Polia frouxa causa deslocamento intermitente difícil de diferenciar de perda de passo.",
        ["Layer shift aleatório.", "Dimensão inconsistente.", "Diagnóstico errado de corrente de motor."],
        "Use trava rosca adequada se o modelo recomendar e houver recorrência.",
    ),
    "limpar bico externamente": _help(
        [
            "Aqueça o hotend a temperatura segura para amolecer resíduo, se necessário.",
            "Use escova adequada e evite curto em termistor/aquecedor.",
            "Remova plástico carbonizado em volta do bico e do bloco.",
        ],
        "Resíduo no bico pode cair na peça, grudar na primeira camada ou virar blob.",
        ["Marcas queimadas na peça.", "Filamento acumulando no bico.", "Falha de primeira camada por material preso."],
        "Nunca force cabo de termistor ou heater durante a limpeza.",
    ),
    "inspecionar bico por desgaste ou entupimento": _help(
        [
            "Observe se o filamento extrudado sai reto e com diâmetro consistente.",
            "Procure ponta ovalizada, arranhada ou com resíduo interno.",
            "Compare qualidade de parede/topo com uma impressão curta conhecida.",
        ],
        "Bico gasto ou parcialmente entupido altera fluxo e precisão.",
        ["Subextrusão.", "Linhas largas ou irregulares.", "Peças frágeis por fluxo inconsistente."],
        "Troque o bico se o problema persistir após limpeza e calibração de fluxo.",
    ),
    "conferir aperto do hotend em temperatura segura": _help(
        [
            "Aqueça conforme recomendação do hotend e use ferramenta correta.",
            "Segure o bloco de forma adequada para não torcer heatbreak.",
            "Confira bico/heatbreak sem aplicar força excessiva.",
        ],
        "Hotend mal apertado pode vazar filamento entre bico, bloco e heatbreak.",
        ["Blob envolvendo o hotend.", "Vazamento lento de filamento.", "Dano ao heatbreak por aperto frio/incorreto."],
        "Faça só quando souber o procedimento do hotend; se houver dúvida, não force.",
    ),
    "inspecionar vazamento de filamento no hotend": _help(
        [
            "Remova o silicone sock se existir e estiver frio o suficiente.",
            "Procure filamento acima do bloco, em volta do bico e na rosca.",
            "Se houver vazamento, pare e planeje limpeza/reaperto antes de imprimir.",
        ],
        "Vazamento pequeno cresce rápido e pode cobrir heater, termistor e cabos.",
        ["Blob grande no hotend.", "Falha térmica por termistor deslocado.", "Dano em cabos do aquecedor."],
        "Não marque como feita se houver filamento subindo pela rosca.",
    ),
    "limpar engrenagens do extrusor": _help(
        [
            "Retire o filamento e abra o acesso ao conjunto tracionador.",
            "Remova pó de filamento dos dentes com escova pequena.",
            "Confira se as engrenagens estão alinhadas com o caminho do filamento.",
        ],
        "Pó nos dentes reduz tração e faz o extrusor moer filamento.",
        ["Subextrusão intermitente.", "Filamento moído.", "Falha em retrações e velocidades altas."],
        "Depois da limpeza, faça extrusão manual curta para confirmar avanço uniforme.",
    ),
    "verificar pressão/tensão do extrusor": _help(
        [
            "Carregue filamento comum e observe a marca deixada pela engrenagem.",
            "Ajuste a pressão em pequenos passos conforme o extrusor.",
            "Teste extrusão e retração curta sem esmagar o filamento.",
        ],
        "Pressão baixa escorrega; pressão alta deforma o filamento e aumenta atrito.",
        ["Cliques no extrusor.", "Filamento ovalizado.", "Subextrusão em velocidade maior."],
        "Ajuste por material se necessário, principalmente flexíveis.",
    ),
    "inspecionar tubo ptfe ou guia de filamento": _help(
        [
            "Remova o filamento e confira se o tubo/guia está preso e alinhado.",
            "Procure ponta ovalizada, corte torto, desgaste interno ou curva fechada.",
            "Substitua o trecho se houver atrito, marca profunda ou folga.",
        ],
        "Guia gasto ou mal alinhado aumenta esforço do extrusor e pode raspar o filamento.",
        ["Subextrusão por atrito.", "Filamento quebrando.", "Sensor ou extrusor recebendo filamento desalinhado."],
        "Cortes de PTFE devem ser retos e bem assentados.",
    ),
    "limpar caminho do filamento": _help(
        [
            "Siga o caminho do spool até o extrusor.",
            "Remova poeira, pedaços de filamento e pontos de atrito.",
            "Confirme que guias, tubos e entradas estão alinhados.",
        ],
        "Caminho sujo ou com atrito cria falhas que parecem problema de hotend.",
        ["Tranco no extrusor.", "Subextrusão em peças longas.", "Desgaste de filamento antes do extrusor."],
        "Puxe o filamento manualmente; a resistência deve ser baixa e constante.",
    ),
    "inspecionar sensor de filamento": _help(
        [
            "Acione o sensor com e sem filamento e confira a mudança de estado.",
            "Veja se o filamento passa centralizado e sem raspar.",
            "Limpe poeira ou fragmentos que possam prender a chave/encoder.",
        ],
        "Sensor sujo ou desalinhado pode falhar quando o filamento realmente acaba ou pausar sem motivo.",
        ["Pausa falsa.", "Fim de filamento não detectado.", "Atrito extra antes do extrusor."],
        "Valide no software se o estado muda antes de confiar em impressão longa.",
    ),
    "limpar fans e dutos": _help(
        [
            "Desligue a impressora antes de encostar em fans.",
            "Remova poeira das pás, grades e dutos sem forçar o eixo.",
            "Confira se nenhum cabo encosta nas pás.",
            "Ligue os fans e observe ruído e fluxo.",
        ],
        "Fans sujos perdem fluxo e podem travar, afetando hotend, peça e eletrônica.",
        ["Heat creep.", "Pontes e overhangs ruins.", "Superaquecimento de eletrônica."],
        "Se houver ruído áspero ou fan demorando a partir, planeje troca.",
    ),
    "verificar ruído ou folga dos fans": _help(
        [
            "Acione cada fan separadamente quando possível.",
            "Escute vibração, raspagem, partida lenta ou variação de rotação.",
            "Confira fixação, duto trincado e cabo próximo às pás.",
        ],
        "Ruído é um aviso comum antes de fan travar ou perder eficiência.",
        ["Falha de refrigeração no meio da impressão.", "Vibração passando para a peça.", "Dano por cabo encostando na hélice."],
        "Troque fan com folga no eixo, partida irregular ou ruído persistente.",
    ),
    "limpar filtro de ar ou carvão ativado": _help(
        [
            "Desligue o sistema de exaustão/filtragem.",
            "Remova poeira externa e confira se o fluxo de ar não está bloqueado.",
            "Troque ou regenere o elemento filtrante conforme o material usado e o tipo do filtro.",
        ],
        "Filtro saturado reduz fluxo e deixa odores/partículas circulando mais tempo.",
        ["Câmara com fluxo ruim.", "Cheiro forte em ABS/ASA.", "Fan trabalhando forçado."],
        "Para ABS/ASA frequente, encurte o intervalo e registre a troca do elemento.",
    ),
    "inspecionar cabos do toolhead": _help(
        [
            "Mova o toolhead por todo o curso com a impressora parada.",
            "Observe dobra, tensão, ponto pegando, malha rompida ou conector mexendo.",
            "Confira alívio de tensão e folga suficiente nos extremos do movimento.",
        ],
        "Cabos do toolhead sofrem movimento constante e falham de forma intermitente antes de romper.",
        ["Perda de comunicação CAN/USB.", "Falha de heater, termistor ou fan em posição específica.", "Cabo rompendo durante impressão."],
        "Se a falha aparece só em uma posição, suspeite de cabo antes de firmware.",
    ),
    "inspecionar conectores can/usb": _help(
        [
            "Desligue a impressora antes de tocar nos conectores.",
            "Confira encaixe, trava, folga, oxidação e esforço no cabo.",
            "Verifique se o cabo não puxa o conector quando o eixo se move.",
        ],
        "Conector frouxo causa quedas intermitentes difíceis de reproduzir.",
        ["Lost communication to MCU.", "Falha CAN aleatória.", "Reset de placa durante movimento."],
        "Não use conector com folga mecânica perceptível em produção.",
    ),
    "conferir fixação e alívio de tensão dos cabos": _help(
        [
            "Veja todos os pontos onde cabo dobra, passa por corrente ou prende em suporte.",
            "Confirme que a fixação segura a capa do cabo, não o fio individual.",
            "Garanta raio de curva confortável nos extremos dos eixos.",
        ],
        "Alívio de tensão correto evita que movimento repetido force solda, borne ou conector.",
        ["Cabo rompido internamente.", "Mau contato em movimento.", "Conector arrancado ou aquecendo por contato ruim."],
        "Depois de reposicionar cabo, mova os eixos no curso completo.",
    ),
    "inspecionar fonte, borne e aterramento visualmente": _help(
        [
            "Desligue da tomada e aguarde antes de abrir compartimento elétrico.",
            "Faça inspeção visual sem tocar em partes energizadas.",
            "Procure borne escurecido, fio solto, isolamento derretido, cheiro de queimado ou aterramento ausente.",
        ],
        "Fonte e bornes são pontos críticos de segurança. Sinal visual pequeno pode indicar aquecimento sério.",
        ["Aquecimento perigoso.", "Queda de tensão sob carga.", "Risco elétrico por aterramento ou borne inadequado."],
        "Se houver marca de aquecimento, não imprima até revisar com segurança.",
    ),
    "conferir câmera e iluminação": _help(
        [
            "Abra a imagem da câmera e confirme que mesa, bico e peça ficam visíveis.",
            "Limpe a lente sem forçar o suporte.",
            "Ajuste iluminação para evitar sombra forte ou imagem estourada.",
            "Mova o toolhead devagar e confirme que câmera/LEDs não interferem no movimento.",
        ],
        "Boa visão remota permite detectar cedo primeira camada soltando, spaghetti, colisão e acúmulo no bico.",
        ["Perder horas de impressão por falha visível.", "Diagnóstico ruim por imagem escura ou fora de quadro.", "Suporte de câmera/LED encostando no movimento."],
        "Marque como feita quando a imagem estiver limpa, iluminada e enquadrando a área útil.",
    ),
    "conferir spool holder e caminho até a impressora": _help(
        [
            "Gire o spool manualmente e confirme que roda livre.",
            "Siga o filamento até o extrusor e procure curva fechada, atrito, nó ou poeira.",
            "Confira alinhamento de tubo, guia e sensor de filamento.",
            "Puxe um trecho curto; a resistência deve ser baixa e constante.",
        ],
        "Alimentação irregular do spool vira subextrusão, tranco no extrusor e falhas que parecem problema de hotend.",
        ["Subextrusão em peças longas.", "Filamento enrolando ou quebrando.", "Pausa falsa de sensor ou desgaste da engrenagem."],
        "Marque como feita quando spool e caminho alimentarem sem travar.",
    ),
    "revisar macros e perfil do slicer após mudanças": _help(
        [
            "Liste o que mudou: firmware, macro, slicer, material, bico ou geometria.",
            "Revise temperaturas, retração, flow, pressure advance, aceleração e limites.",
            "Execute uma impressão curta ou simulação segura antes de peça longa.",
            "Registre o que mudou para permitir rollback.",
        ],
        "Mudanças de software alteram comportamento mesmo quando a mecânica está perfeita.",
        ["Macro antiga executando sequência errada.", "Perfil de material aplicado na peça errada.", "Dificuldade de voltar ao estado anterior."],
        "Sempre valide após update de slicer, firmware, macro ou perfil de material.",
    ),
}


class MaintenanceEventCreate(BaseModel):
    event_type: MaintenanceEventType = "maintenance"
    component: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=1, max_length=120)
    notes: str = Field(default="", max_length=1000)
    performed_at: str | None = Field(default=None, max_length=40)
    print_hours_at: float | None = Field(default=None, ge=0)
    print_hours_read_at: str | None = Field(default=None, max_length=40)


class MaintenanceEventRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    performed_at: str
    event_type: MaintenanceEventType
    component: str | None
    title: str
    notes: str
    created_at: str
    print_hours_at: float | None = None
    print_hours_read_at: str | None = None


class MaintenanceTaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    component: str = Field(min_length=1, max_length=80)
    interval_days: int = Field(default=30, ge=1, le=3650)
    interval_kind: MaintenanceIntervalKind = "days"
    interval_value: float | None = Field(default=None, gt=0, le=100000)
    last_done_at: str | None = Field(default=None, max_length=40)
    last_done_print_hours: float | None = Field(default=None, ge=0)
    last_print_hours_read_at: str | None = Field(default=None, max_length=40)


class MaintenanceTaskComplete(BaseModel):
    notes: str = Field(default="", max_length=1000)
    performed_at: str | None = Field(default=None, max_length=40)
    next_interval_days: int | None = Field(default=None, ge=1, le=3650)
    next_interval_kind: MaintenanceIntervalKind | None = None
    next_interval_value: float | None = Field(default=None, gt=0, le=100000)
    print_hours_at: float | None = Field(default=None, ge=0)
    print_hours_read_at: str | None = Field(default=None, max_length=40)
    disable_reminder: bool = False


class MaintenanceTaskHelp(BaseModel):
    how_to: list[str]
    why: str
    prevents: list[str]
    recommendation: str


class MaintenanceTaskRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    name: str
    component: str
    interval_days: int
    interval_kind: MaintenanceIntervalKind
    interval_value: float
    last_done_at: str | None
    last_done_print_hours: float | None
    last_print_hours_read_at: str | None
    current_print_hours: float | None
    current_print_hours_read_at: str | None
    current_print_hours_source: str | None
    is_active: bool
    created_at: str
    updated_at: str
    due_status: TaskDueStatus
    days_until_due: int | None
    print_hours_delta: float | None = None
    print_hours_until_due: float | None = None
    due_detail: str | None = None
    recommended_interval_kind: MaintenanceIntervalKind | None = None
    recommended_interval_value: float | None = None
    maintenance_help: MaintenanceTaskHelp | None = None


class MaintenanceSummary(BaseModel):
    printer_id: int
    safe_mode: str
    counts: dict[str, int]
    due_components: list[str]
    next_due_task: MaintenanceTaskRecord | None
    recommended_tasks: list[dict[str, Any]]
    print_hours_source: str | None = None
    print_hours_read_at: str | None = None


@dataclass(frozen=True)
class MaintenanceRepository:
    database_path: Path

    def create_event(self, printer_id: int, payload: MaintenanceEventCreate) -> MaintenanceEventRecord:
        performed_at = _clean_timestamp(payload.performed_at)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO maintenance_events (printer_id, performed_at, event_type, component, title, notes)
                VALUES (?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    performed_at,
                    payload.event_type,
                    _clean_optional(payload.component),
                    payload.title.strip(),
                    payload.notes.strip(),
                ),
            )
            event_id = int(cursor.lastrowid)
            if payload.print_hours_at is not None or payload.print_hours_read_at is not None:
                connection.execute(
                    """
                    UPDATE maintenance_events
                    SET print_hours_at = ?, print_hours_read_at = ?
                    WHERE id = ?
                    """,
                    (payload.print_hours_at, _clean_timestamp(payload.print_hours_read_at), event_id),
                )
        event = self.get_event(event_id)
        if event is None:
            raise RuntimeError("maintenance event was not persisted")
        return event

    def list_events(self, printer_id: int, limit: int = 50) -> list[MaintenanceEventRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, performed_at, event_type, component, title, notes, created_at,
                       print_hours_at, print_hours_read_at
                FROM maintenance_events
                WHERE printer_id = ?
                ORDER BY performed_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, limit),
            ).fetchall()
        return [_event_from_row(row) for row in rows]

    def get_event(self, event_id: int) -> MaintenanceEventRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, performed_at, event_type, component, title, notes, created_at,
                       print_hours_at, print_hours_read_at
                FROM maintenance_events
                WHERE id = ?
                """,
                (event_id,),
            ).fetchone()
        return _event_from_row(row) if row else None

    def delete_event(self, event_id: int) -> MaintenanceEventRecord | None:
        event = self.get_event(event_id)
        if event is None:
            return None
        with connect_database(self.database_path) as connection:
            connection.execute("DELETE FROM maintenance_events WHERE id = ?", (event.id,))
            self._sync_tasks_for_event(connection, event)
        return event

    def create_task(self, printer_id: int, payload: MaintenanceTaskCreate) -> MaintenanceTaskRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO maintenance_tasks (
                    printer_id, name, component, interval_days, interval_kind, interval_value,
                    last_done_at, last_done_print_hours, last_print_hours_read_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    payload.name.strip(),
                    payload.component.strip(),
                    payload.interval_days,
                    payload.interval_kind,
                    _interval_value(payload.interval_kind, payload.interval_value, payload.interval_days),
                    _clean_timestamp(payload.last_done_at),
                    payload.last_done_print_hours,
                    _clean_timestamp(payload.last_print_hours_read_at),
                ),
            )
            task_id = int(cursor.lastrowid)
        task = self.get_task(task_id)
        if task is None:
            raise RuntimeError("maintenance task was not persisted")
        return task

    def list_tasks(self, printer_id: int) -> list[MaintenanceTaskRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, name, component, interval_days, interval_kind, interval_value,
                       last_done_at, last_done_print_hours, last_print_hours_read_at,
                       current_print_hours, current_print_hours_read_at, current_print_hours_source,
                       is_active, created_at, updated_at
                FROM maintenance_tasks
                WHERE printer_id = ?
                ORDER BY is_active DESC, component ASC, name ASC
                """,
                (printer_id,),
            ).fetchall()
        return [_task_from_row(row) for row in rows]

    def summary(self, printer_id: int) -> MaintenanceSummary:
        tasks = self.list_tasks(printer_id)
        counts = {"due": 0, "soon": 0, "ok": 0, "unknown": 0, "not_validated": 0, "needs_review": 0, "inactive": 0}
        for task in tasks:
            if not task.is_active:
                counts["inactive"] += 1
                continue
            counts[task.due_status] += 1
        due_components = sorted(
            {task.component for task in tasks if task.is_active and task.due_status in {"due", "soon"}}
        )
        active_known_tasks = [task for task in tasks if task.is_active and task.due_status not in {"unknown", "not_validated", "needs_review"}]
        next_due_task = min(active_known_tasks, key=_task_due_sort_value) if active_known_tasks else None
        existing = {(task.name.lower(), task.component.lower()) for task in tasks}
        recommended_tasks = [
            task
            for task in DEFAULT_PREVENTIVE_TASKS
            if (str(task["name"]).lower(), str(task["component"]).lower()) not in existing
        ]
        return MaintenanceSummary(
            printer_id=printer_id,
            safe_mode="local_only",
            counts=counts,
            due_components=due_components,
            next_due_task=next_due_task,
            recommended_tasks=recommended_tasks,
        )

    def create_default_tasks(self, printer_id: int) -> list[MaintenanceTaskRecord]:
        created: list[MaintenanceTaskRecord] = []
        existing = {
            (task.name.lower(), task.component.lower())
            for task in self.list_tasks(printer_id)
        }
        for task in DEFAULT_PREVENTIVE_TASKS:
            key = (str(task["name"]).lower(), str(task["component"]).lower())
            if key in existing:
                continue
            created.append(
                self.create_task(
                    printer_id,
                    MaintenanceTaskCreate(
                        name=str(task["name"]),
                        component=str(task["component"]),
                        interval_days=int(task["interval_days"]),
                    ),
                )
            )
            existing.add(key)
        return created

    def ensure_default_tasks(self, printer_id: int) -> None:
        if not self.list_tasks(printer_id):
            self.create_default_tasks(printer_id)

    def get_task(self, task_id: int) -> MaintenanceTaskRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, name, component, interval_days, interval_kind, interval_value,
                       last_done_at, last_done_print_hours, last_print_hours_read_at,
                       current_print_hours, current_print_hours_read_at, current_print_hours_source,
                       is_active, created_at, updated_at
                FROM maintenance_tasks
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()
        return _task_from_row(row) if row else None

    def complete_task(self, task_id: int, payload: MaintenanceTaskComplete) -> MaintenanceEventRecord | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        performed_at = _clean_timestamp(payload.performed_at) or _now_text()
        interval_kind = payload.next_interval_kind or task.interval_kind
        interval_value = _complete_interval_value(task, payload)
        print_hours_read_at = _clean_timestamp(payload.print_hours_read_at)
        event = self.create_event(
            task.printer_id,
            MaintenanceEventCreate(
                event_type="maintenance",
                component=task.component,
                title=task.name,
                notes=payload.notes,
                performed_at=performed_at,
                print_hours_at=payload.print_hours_at,
                print_hours_read_at=print_hours_read_at,
            ),
        )
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE maintenance_tasks
                SET last_done_at = ?,
                    interval_days = COALESCE(?, interval_days),
                    interval_kind = ?,
                    interval_value = ?,
                    last_done_print_hours = ?,
                    last_print_hours_read_at = ?,
                    is_active = CASE WHEN ? THEN 0 ELSE 1 END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    performed_at,
                    int(interval_value) if interval_kind == "days" else payload.next_interval_days,
                    interval_kind,
                    interval_value,
                    payload.print_hours_at if interval_kind == "print_hours" else None,
                    print_hours_read_at if interval_kind == "print_hours" else None,
                    1 if payload.disable_reminder else 0,
                    task.id,
                ),
            )
        return event

    def update_current_print_hours(
        self,
        printer_id: int,
        print_hours: float | None,
        *,
        read_at: str | None,
        source: str,
    ) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE maintenance_tasks
                SET current_print_hours = COALESCE(?, current_print_hours),
                    current_print_hours_read_at = COALESCE(?, current_print_hours_read_at),
                    current_print_hours_source = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE printer_id = ?
                """,
                (print_hours, _clean_timestamp(read_at), source, printer_id),
            )

    def delete_latest_task_event(self, task_id: int) -> MaintenanceEventRecord | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, performed_at, event_type, component, title, notes, created_at,
                       print_hours_at, print_hours_read_at
                FROM maintenance_events
                WHERE printer_id = ?
                  AND event_type = 'maintenance'
                  AND lower(title) = lower(?)
                  AND lower(COALESCE(component, '')) = lower(?)
                ORDER BY performed_at DESC, id DESC
                LIMIT 1
                """,
                (task.printer_id, task.name, task.component),
            ).fetchone()
            if row is None:
                return None
            event = _event_from_row(row)
            connection.execute("DELETE FROM maintenance_events WHERE id = ?", (event.id,))
            self._sync_task_last_done(connection, task)
        return event

    def _sync_tasks_for_event(self, connection, event: MaintenanceEventRecord) -> None:
        rows = connection.execute(
            """
            SELECT id, printer_id, name, component, interval_days, interval_kind, interval_value,
                   last_done_at, last_done_print_hours, last_print_hours_read_at,
                   current_print_hours, current_print_hours_read_at, current_print_hours_source,
                   is_active, created_at, updated_at
            FROM maintenance_tasks
            WHERE printer_id = ?
              AND lower(name) = lower(?)
              AND lower(COALESCE(component, '')) = lower(COALESCE(?, ''))
            """,
            (event.printer_id, event.title, event.component),
        ).fetchall()
        for row in rows:
            self._sync_task_last_done(connection, _task_from_row(row))

    def _sync_task_last_done(self, connection, task: MaintenanceTaskRecord) -> None:
        latest = connection.execute(
            """
            SELECT performed_at, print_hours_at, print_hours_read_at
            FROM maintenance_events
            WHERE printer_id = ?
              AND event_type = 'maintenance'
              AND lower(title) = lower(?)
              AND lower(COALESCE(component, '')) = lower(?)
            ORDER BY performed_at DESC, id DESC
            LIMIT 1
            """,
            (task.printer_id, task.name, task.component),
        ).fetchone()
        connection.execute(
            """
            UPDATE maintenance_tasks
            SET last_done_at = ?,
                last_done_print_hours = ?,
                last_print_hours_read_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                latest["performed_at"] if latest else None,
                latest["print_hours_at"] if latest else None,
                latest["print_hours_read_at"] if latest else None,
                task.id,
            ),
        )


def _event_from_row(row) -> MaintenanceEventRecord:
    return MaintenanceEventRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        performed_at=str(row["performed_at"]),
        event_type=row["event_type"],
        component=row["component"],
        title=str(row["title"]),
        notes=str(row["notes"]),
        created_at=str(row["created_at"]),
        print_hours_at=row["print_hours_at"],
        print_hours_read_at=row["print_hours_read_at"],
    )


def _task_from_row(row) -> MaintenanceTaskRecord:
    stored_interval_kind: MaintenanceIntervalKind = row["interval_kind"] if row["interval_kind"] in {"days", "print_hours"} else "days"
    stored_interval_value = float(row["interval_value"] if row["interval_value"] is not None else row["interval_days"])
    recommendation = _recommended_interval_for_task(str(row["name"]), str(row["component"]))
    help_content = _maintenance_help_for_task(str(row["name"]), str(row["component"]))
    current_print_hours_source = row["current_print_hours_source"]
    current_print_hours = row["current_print_hours"]
    interval_kind, interval_value = _effective_interval(
        stored_interval_kind=stored_interval_kind,
        stored_interval_value=stored_interval_value,
        recommended_interval_kind=recommendation[0],
        recommended_interval_value=recommendation[1],
        current_print_hours=current_print_hours,
        current_print_hours_source=current_print_hours_source,
    )
    due_status, days_until_due, print_hours_delta, print_hours_until_due, due_detail = _calculate_due_status(
        interval_kind=interval_kind,
        interval_value=interval_value,
        last_done_at=row["last_done_at"],
        interval_days=int(row["interval_days"]),
        last_done_print_hours=row["last_done_print_hours"],
        current_print_hours=current_print_hours,
        current_print_hours_source=current_print_hours_source,
    )
    return MaintenanceTaskRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        name=str(row["name"]),
        component=str(row["component"]),
        interval_days=int(row["interval_days"]),
        interval_kind=interval_kind,
        interval_value=interval_value,
        last_done_at=row["last_done_at"],
        last_done_print_hours=row["last_done_print_hours"],
        last_print_hours_read_at=row["last_print_hours_read_at"],
        current_print_hours=current_print_hours,
        current_print_hours_read_at=row["current_print_hours_read_at"],
        current_print_hours_source=current_print_hours_source,
        is_active=bool(row["is_active"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        due_status=due_status,
        days_until_due=days_until_due,
        print_hours_delta=print_hours_delta,
        print_hours_until_due=print_hours_until_due,
        due_detail=due_detail,
        recommended_interval_kind=recommendation[0],
        recommended_interval_value=recommendation[1],
        maintenance_help=MaintenanceTaskHelp(**help_content) if help_content else None,
    )


def _recommended_interval_for_task(
    name: str,
    component: str,
) -> tuple[MaintenanceIntervalKind | None, float | None]:
    key = (name.lower(), component.lower())
    for task in DEFAULT_PREVENTIVE_TASKS:
        if key != (str(task["name"]).lower(), str(task["component"]).lower()):
            continue
        kind = task.get("recommended_interval_kind")
        value = task.get("recommended_interval_value")
        if kind in {"days", "print_hours"} and value is not None:
            return kind, float(value)
        return None, None
    return None, None


def _maintenance_help_for_task(name: str, component: str) -> dict[str, Any] | None:
    direct = MAINTENANCE_HELP_BY_TASK.get(name.lower())
    if direct:
        return direct
    key = (name.lower(), component.lower())
    for task in DEFAULT_PREVENTIVE_TASKS:
        if key == (str(task["name"]).lower(), str(task["component"]).lower()):
            help_content = MAINTENANCE_HELP_BY_TASK.get(str(task["name"]).lower())
            return help_content
    return None


def _effective_interval(
    *,
    stored_interval_kind: MaintenanceIntervalKind,
    stored_interval_value: float,
    recommended_interval_kind: MaintenanceIntervalKind | None,
    recommended_interval_value: float | None,
    current_print_hours: float | None,
    current_print_hours_source: str | None,
) -> tuple[MaintenanceIntervalKind, float]:
    if (
        recommended_interval_kind == "print_hours"
        and recommended_interval_value is not None
        and current_print_hours is not None
        and current_print_hours_source == "live"
    ):
        return "print_hours", recommended_interval_value
    return stored_interval_kind, stored_interval_value


def _calculate_due_status(
    *,
    interval_kind: MaintenanceIntervalKind,
    interval_value: float,
    last_done_at: str | None,
    interval_days: int,
    last_done_print_hours: float | None,
    current_print_hours: float | None,
    current_print_hours_source: str | None,
) -> tuple[TaskDueStatus, int | None, float | None, float | None, str | None]:
    if interval_kind == "print_hours":
        if not last_done_at and current_print_hours is not None and current_print_hours_source == "live":
            return "due", None, None, None, "Primeira execução pendente."
        return _calculate_print_hours_due_status(
            interval_value, last_done_print_hours, current_print_hours, current_print_hours_source
        )
    if not last_done_at:
        return "due", 0, None, None, None
    parsed = _parse_datetime(last_done_at)
    if parsed is None:
        return "unknown", None, None, None, "Data da última execução inválida."
    elapsed_days = (datetime.now(timezone.utc) - parsed).days
    days_until_due = interval_days - elapsed_days
    if days_until_due <= 0:
        return "due", 0, None, None, None
    if days_until_due <= max(1, min(7, interval_days // 5)):
        return "soon", days_until_due, None, None, None
    return "ok", days_until_due, None, None, None


def _calculate_print_hours_due_status(
    interval_value: float,
    last_done_print_hours: float | None,
    current_print_hours: float | None,
    current_print_hours_source: str | None,
) -> tuple[TaskDueStatus, int | None, float | None, float | None, str | None]:
    if last_done_print_hours is None:
        return "not_validated", None, None, None, "Aguardando leitura de horas para validar a base."
    if current_print_hours is None:
        return "not_validated", None, None, None, "Moonraker sem leitura de horas disponível."
    delta = current_print_hours - last_done_print_hours
    if delta < 0:
        return "needs_review", None, delta, None, "Total atual menor que a base salva; histórico pode ter sido resetado."
    hours_until_due = interval_value - delta
    detail = "Leitura de horas ao vivo." if current_print_hours_source == "live" else "Leitura de horas desatualizada."
    if hours_until_due <= 0:
        return "due", None, delta, 0, detail
    if hours_until_due <= max(1.0, min(10.0, interval_value * 0.2)):
        return "soon", None, delta, hours_until_due, detail
    return "ok", None, delta, hours_until_due, detail


def _interval_value(interval_kind: MaintenanceIntervalKind, interval_value: float | None, interval_days: int) -> float:
    if interval_kind == "days":
        return float(interval_value if interval_value is not None else interval_days)
    if interval_value is None:
        raise ValueError("interval_value é obrigatório para lembrete por horas de impressão")
    return float(interval_value)


def _complete_interval_value(task: MaintenanceTaskRecord, payload: MaintenanceTaskComplete) -> float:
    interval_kind = payload.next_interval_kind or task.interval_kind
    if interval_kind == "days":
        return float(payload.next_interval_value or payload.next_interval_days or task.interval_days)
    if payload.next_interval_value is not None:
        return float(payload.next_interval_value)
    if payload.next_interval_days is not None:
        return float(payload.next_interval_days)
    return float(task.interval_value)


def _task_due_sort_value(task: MaintenanceTaskRecord) -> float:
    if task.interval_kind == "print_hours":
        return task.print_hours_until_due if task.print_hours_until_due is not None else float("inf")
    return float(task.days_until_due if task.days_until_due is not None else 999999)


def _parse_datetime(value: str) -> datetime | None:
    for candidate in (value, value.replace(" ", "T")):
        try:
            parsed = datetime.fromisoformat(candidate)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _clean_timestamp(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None


def _clean_optional(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None


def _now_text() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
