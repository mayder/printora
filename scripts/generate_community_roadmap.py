#!/usr/bin/env python3
"""Generate the long-term Printora community roadmap from a reviewed capability map."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "community"


DOMAINS = [
    {
        "key": "assistive",
        "name": "Tecnologia assistiva e autonomia",
        "priority": "P0",
        "impact": "Saúde, autonomia, inclusão e participação de pessoas com deficiência ou mobilidade reduzida.",
        "features": [
            "catálogo validado de dispositivos assistivos imprimíveis",
            "coautoria obrigatória com usuários finais e especialistas",
            "fluxo de medidas corporais com consentimento e minimização",
            "níveis de evidência clínica e limites de uso",
            "rede local de fabricação, ajuste e acompanhamento",
            "alertas de contraindicação, material e carga mecânica",
            "programa de subsídio e doação rastreável",
            "registro longitudinal de conforto, segurança e resultado",
        ],
    },
    {
        "key": "safety_models",
        "name": "Segurança de modelos e uso responsável",
        "priority": "P0",
        "impact": "Redução de lesões, incêndios, falhas mecânicas e uso indevido de peças críticas.",
        "features": [
            "classificação de risco por finalidade do modelo",
            "bloqueio de promessas médicas ou estruturais sem evidência",
            "checklist obrigatório para peças em contato com alimentos",
            "checklist obrigatório para peças infantis e brinquedos",
            "validação de temperatura, chama e isolamento elétrico",
            "alerta de fadiga, carga, orientação e anisotropia",
            "recall comunitário de arquivo ou versão perigosa",
            "trilha de incidentes e aprendizado sem exposição da vítima",
        ],
    },
    {
        "key": "humanitarian",
        "name": "Resposta humanitária e resiliência local",
        "priority": "P0",
        "impact": "Capacidade local de responder a emergências com peças apropriadas, seguras e coordenadas.",
        "features": [
            "modo de emergência ativado por autoridade ou parceiro verificado",
            "catálogo offline de itens humanitários pré-validados",
            "mapa de demanda, capacidade, materiais e energia disponíveis",
            "coordenação de lotes entre oficinas e voluntários",
            "controle de qualidade por amostragem e cadeia de custódia",
            "instruções multilíngues de fabricação e uso em campo",
            "priorização ética sem leilão ou exploração de escassez",
            "encerramento de missão com prestação de contas e lições",
        ],
    },
    {
        "key": "child_safety",
        "name": "Proteção de crianças e adolescentes",
        "priority": "P0",
        "impact": "Ambiente seguro para aprendizagem maker, sem exploração, assédio ou exposição indevida.",
        "features": [
            "contas juvenis com supervisão e consentimento apropriados",
            "experiência por faixa etária e conteúdo adequado",
            "mensagens privadas desativadas ou protegidas por padrão",
            "detecção e escalonamento de aliciamento e exploração",
            "ocultação de localização, escola e rotina pessoal",
            "moderação especializada e canal de ajuda acessível",
            "projetos escolares com identidade coletiva opcional",
            "painel de responsáveis com controles proporcionais",
        ],
    },
    {
        "key": "trust_integrity",
        "name": "Integridade, confiança e combate a fraude",
        "priority": "P0",
        "impact": "Proteção da comunidade contra golpes, manipulação, falsificação e conteúdo artificial enganoso.",
        "features": [
            "verificação progressiva de identidade e papel técnico",
            "proveniência de arquivo, imagem, vídeo e resultado de impressão",
            "rotulagem de conteúdo gerado ou alterado por IA",
            "detecção de avaliações, downloads e impressões coordenadas",
            "selo de teste físico com evidência reproduzível",
            "contestação de autoria e titularidade com prazo",
            "histórico público de sanções relevantes e recursos",
            "transparência de recomendação, promoção e patrocínio",
        ],
    },
    {
        "key": "privacy",
        "name": "Privacidade e soberania de dados",
        "priority": "P0",
        "impact": "Autonomia do usuário e prevenção de exposição doméstica, biométrica, operacional ou comercial.",
        "features": [
            "painel unificado de visibilidade por campo e contexto",
            "consentimento granular para telemetria e personalização",
            "exportação completa e portável da conta",
            "exclusão segura com retenções legais explicadas",
            "modo pseudônimo separado da identidade comercial",
            "proteção de localização de impressoras e oficinas",
            "cofre de medidas corporais e arquivos sensíveis",
            "registro legível de acessos, decisões e compartilhamentos",
        ],
    },
    {
        "key": "security",
        "name": "Segurança da plataforma e das impressoras",
        "priority": "P0",
        "impact": "Prevenção de tomada de conta, vazamento e comando físico indevido sobre equipamentos.",
        "features": [
            "autenticação multifator e chaves de acesso",
            "sessões por dispositivo com revogação e risco",
            "step-up para compra, publicação e operação crítica",
            "isolamento estrito entre social e controle operacional",
            "assinatura e verificação de artefatos distribuídos",
            "programa de divulgação responsável e resposta a incidentes",
            "detecção de bots, scraping e abuso de API",
            "backup, continuidade e recuperação testada do domínio social",
        ],
    },
    {
        "key": "moderation",
        "name": "Moderação e segurança comunitária",
        "priority": "P0",
        "impact": "Redução de assédio, ódio, violência, exploração e circulação de conteúdo ilegal ou perigoso.",
        "features": [
            "regras comunitárias locais subordinadas à política global",
            "fila priorizada por gravidade, alcance e vulnerabilidade",
            "moderação de texto, imagem, vídeo, áudio e arquivo 3D",
            "equipes por idioma, região e conhecimento técnico",
            "ações temporárias, graduais e reversíveis quando cabível",
            "recurso independente com prazo e explicação",
            "proteção contra brigading, raids e perseguição coordenada",
            "relatório periódico de transparência e qualidade decisória",
        ],
    },
    {
        "key": "accessibility",
        "name": "Acessibilidade universal",
        "priority": "P1",
        "impact": "Participação equivalente de pessoas com diferentes capacidades visuais, auditivas, motoras e cognitivas.",
        "features": [
            "conformidade contínua com WCAG e testes com usuários",
            "navegação integral por teclado, switch e voz",
            "leitor de tela com semântica e anúncios de estado",
            "contraste, zoom, redução de movimento e temas adaptativos",
            "legendas, transcrições e audiodescrição para mídia",
            "linguagem simples e modo de baixa carga cognitiva",
            "visualização 3D com alternativa textual e tátil exportável",
            "central de preferências acessíveis sincronizada",
        ],
    },
    {
        "key": "mobile",
        "name": "Mobilidade, PWA e uso em campo",
        "priority": "P1",
        "impact": "Acesso confiável em celular, oficina, escola e regiões com conectividade limitada.",
        "features": [
            "navegação mobile nativa com barra inferior contextual",
            "PWA instalável com cache seguro e atualização controlada",
            "fila offline de rascunhos, fotos e medições",
            "sincronização resiliente com conflito explícito",
            "captura por câmera, QR code, NFC e scanner 3D",
            "notificações push agrupadas e acionáveis",
            "modo economia de dados, bateria e processamento",
            "experiência para luvas, mãos ocupadas e telas externas",
        ],
    },
    {
        "key": "education",
        "name": "Educação maker e aprendizagem ao longo da vida",
        "priority": "P1",
        "impact": "Formação técnica acessível, pensamento crítico e ampliação de oportunidades educacionais.",
        "features": [
            "trilhas do primeiro modelo à fabricação avançada",
            "aulas passo a passo com arquivos e checkpoints",
            "laboratórios virtuais de CAD, slicing e diagnóstico",
            "avaliação prática por evidência de projeto",
            "mentoria entre pares com salvaguardas",
            "formação de educadores e planos de aula abertos",
            "certificados verificáveis baseados em competência",
            "biblioteca de erros reais e recuperação guiada",
        ],
    },
    {
        "key": "schools",
        "name": "Escolas, bibliotecas e makerspaces",
        "priority": "P1",
        "impact": "Democratização de infraestrutura de fabricação e fortalecimento de centros comunitários de aprendizagem.",
        "features": [
            "perfil institucional com turmas, oficinas e equipamentos",
            "reserva de máquina, espaço e instrutor",
            "fila pedagógica com aprovação e limites de material",
            "contas de turma sem coleta excessiva de dados",
            "inventário compartilhado e manutenção preventiva",
            "currículo, projetos e resultados públicos opcionais",
            "rede de empréstimo de ferramentas e componentes",
            "painel de inclusão, alcance territorial e aprendizagem",
        ],
    },
    {
        "key": "repair",
        "name": "Reparo, peças de reposição e economia circular",
        "priority": "P1",
        "impact": "Extensão da vida útil de produtos, redução de resíduos e acesso local a reparos.",
        "features": [
            "catálogo por produto, peça, revisão e compatibilidade",
            "busca por foto, medidas, código e sintoma",
            "manual de desmontagem, risco e remontagem",
            "rede de reparadores e oficinas verificadas",
            "passaporte de reparo e histórico do objeto",
            "comparação entre imprimir, comprar, usinar ou reutilizar",
            "incentivo a design reparável e peças abertas",
            "indicadores de resíduos evitados e vida útil ampliada",
        ],
    },
    {
        "key": "sustainability",
        "name": "Sustentabilidade e uso responsável de materiais",
        "priority": "P1",
        "impact": "Menos desperdício, energia e emissões, com decisões ambientais verificáveis.",
        "features": [
            "estimativa de material, energia, suporte e falha evitável",
            "comparação ambiental entre variantes de impressão",
            "passaporte de material e origem do filamento",
            "rede de coleta, reciclagem e reaproveitamento local",
            "biblioteca de perfis para material reciclado",
            "metas pessoais e institucionais de redução de desperdício",
            "alertas contra greenwashing e métricas não comparáveis",
            "relatório de impacto ambiental por projeto e comunidade",
        ],
    },
    {
        "key": "local_manufacturing",
        "name": "Fabricação local e capacidade produtiva",
        "priority": "P1",
        "impact": "Geração de renda, resiliência de cadeias e produção distribuída próxima da demanda.",
        "features": [
            "mapa de capacidade por processo, material e tolerância",
            "pedido de fabricação com especificação verificável",
            "cotação transparente sem corrida predatória por preço",
            "roteamento por distância, capacidade e impacto",
            "controle de lote, amostra, inspeção e não conformidade",
            "cadeia de custódia de arquivo e propriedade intelectual",
            "pagamento por marco com proteção a ambas as partes",
            "painel de renda local, prazo, qualidade e inclusão",
        ],
    },
    {
        "key": "quality",
        "name": "Qualidade, metrologia e rastreabilidade",
        "priority": "P1",
        "impact": "Resultados físicos mais previsíveis, seguros e reproduzíveis.",
        "features": [
            "plano de inspeção por tipo de peça e risco",
            "registro de medidas nominais, reais e tolerâncias",
            "fotos padronizadas e evidência de acabamento",
            "amostras de calibração vinculadas ao perfil usado",
            "rastreabilidade de máquina, material, lote e operador",
            "controle estatístico de processo acessível",
            "não conformidade, contenção e ação corretiva",
            "certificado de fabricação verificável e exportável",
        ],
    },
    {
        "key": "onboarding",
        "name": "Onboarding e ativação progressiva",
        "priority": "P1",
        "impact": "Entrada simples para iniciantes sem sacrificar profundidade para especialistas.",
        "features": [
            "escolha inicial de objetivos, experiência e equipamentos",
            "tour adaptativo baseado no primeiro resultado desejado",
            "checklist de perfil, impressora e primeiro projeto",
            "modo iniciante com termos explicados no contexto",
            "modo especialista com atalhos e densidade maior",
            "dados de exemplo removíveis e ambiente de treino",
            "retomada exata de fluxo interrompido em outro dispositivo",
            "medição de tempo até primeiro valor sem dark patterns",
        ],
    },
    {
        "key": "design_system",
        "name": "Layout, design system e coerência visual",
        "priority": "P1",
        "impact": "Uso mais fácil, previsível e inclusivo em toda a plataforma.",
        "features": [
            "design system documentado com tokens semânticos",
            "hierarquia visual consistente entre social e operação",
            "componentes responsivos para cards, tabelas e galerias",
            "densidade ajustável para oficina, leitura e administração",
            "padrões de formulário longo com salvamento e revisão",
            "estados loading, vazio, erro, parcial e offline coerentes",
            "microinterações com feedback e redução de movimento",
            "laboratório visual com regressão desktop e mobile",
        ],
    },
    {
        "key": "i18n",
        "name": "Internacionalização e inclusão linguística",
        "priority": "P1",
        "impact": "Acesso global e preservação de conhecimento técnico local.",
        "features": [
            "interface traduzida com fallback e cobertura visível",
            "conteúdo multilíngue por versão e autor",
            "tradução assistida com revisão comunitária",
            "glossário técnico por região e processo",
            "busca cruzada entre idiomas e sinônimos",
            "unidades, datas, moedas e normas locais",
            "suporte a escrita bidirecional e fontes apropriadas",
            "preservação de idioma original e atribuição da tradução",
        ],
    },
    {
        "key": "communities",
        "name": "Comunidades avançadas e governança local",
        "priority": "P2",
        "impact": "Pertencimento, cooperação e autonomia comunitária com responsabilidade.",
        "features": [
            "comunidades criadas por tema, território e finalidade",
            "canais de fórum, chat, anúncios, recursos e projetos",
            "papéis e permissões comunitárias configuráveis",
            "onboarding por interesses, regras e canais",
            "wiki, FAQ e base de conhecimento mantida pela comunidade",
            "propostas, enquetes e decisões com histórico",
            "saúde da comunidade, retenção e carga de moderação",
            "fusão, arquivamento e sucessão de administradores",
        ],
    },
    {
        "key": "messaging",
        "name": "Mensagens, chat e presença em tempo real",
        "priority": "P2",
        "impact": "Colaboração rápida, suporte e vínculos entre makers com controles de segurança.",
        "features": [
            "mensagens diretas com solicitações e filtros",
            "conversas em grupo com papéis e convite",
            "chat por projeto, comunidade, evento e trabalho",
            "threads, respostas, reações e mensagens fixadas",
            "presença opcional e status de disponibilidade",
            "compartilhamento seguro de arquivos e previews",
            "busca, exportação e retenção controlada da conversa",
            "voz, áudio curto e chamada com consentimento",
        ],
    },
    {
        "key": "events",
        "name": "Eventos, encontros e fabricação coletiva",
        "priority": "P2",
        "impact": "Mobilização comunitária, aprendizagem prática e conexão territorial.",
        "features": [
            "calendário de eventos online, presenciais e híbridos",
            "inscrição, capacidade, lista de espera e check-in",
            "mapa com privacidade de localização e acessibilidade",
            "agenda, palestrantes, oficinas e materiais necessários",
            "transmissão, chat, perguntas e gravação",
            "hackathons, repair cafés e print farms coletivas",
            "certificado, fotos e resultados pós-evento",
            "ferramentas contra no-show, assédio e evento fraudulento",
        ],
    },
    {
        "key": "collaboration",
        "name": "Coautoria, equipes e colaboração de projeto",
        "priority": "P2",
        "impact": "Projetos melhores por contribuição distribuída e autoria reconhecida.",
        "features": [
            "equipe de projeto com papéis e permissões granulares",
            "convite, solicitação de entrada e saída segura",
            "tarefas, marcos, dependências e responsáveis",
            "comentários ancorados em arquivo, peça e versão",
            "revisão por pares com aprovação e pedido de alteração",
            "branch, merge e resolução visual de conflito de modelo",
            "créditos proporcionais e histórico de contribuição",
            "handoff, arquivamento e continuidade do projeto",
        ],
    },
    {
        "key": "knowledge",
        "name": "Conhecimento técnico e suporte estruturado",
        "priority": "P2",
        "impact": "Redução de retrabalho e democratização de conhecimento confiável.",
        "features": [
            "perguntas e respostas com solução e versões afetadas",
            "árvore de diagnóstico guiada por sintoma",
            "artigos versionados com revisão técnica",
            "runbooks comunitários por hardware e software",
            "duplicidade sugerida antes de publicar dúvida",
            "resumo de discussão com fontes e incertezas",
            "escalonamento para especialista ou fabricante",
            "qualidade da resposta medida por resolução confirmada",
        ],
    },
    {
        "key": "feed",
        "name": "Feed pessoal e consumo saudável",
        "priority": "P2",
        "impact": "Descoberta relevante sem vício, manipulação ou perda de controle do usuário.",
        "features": [
            "feed cronológico de contas e comunidades seguidas",
            "feed recomendado com explicação e controles",
            "listas personalizadas e feeds por interesse técnico",
            "modo foco sem contadores ou rolagem infinita",
            "continuar de onde parou com limite diário opcional",
            "não recomendar conteúdo bloqueado, repetido ou já resolvido",
            "feedback explícito de menos, mais e não tenho interesse",
            "auditoria pessoal de por que cada item apareceu",
        ],
    },
    {
        "key": "search",
        "name": "Busca multimodal e descoberta avançada",
        "priority": "P2",
        "impact": "Encontrar rapidamente conhecimento, pessoas, peças e modelos compatíveis.",
        "features": [
            "busca unificada por texto, categoria e entidade",
            "busca geométrica por malha ou desenho semelhante",
            "busca por foto, objeto, peça quebrada ou QR code",
            "busca semântica por problema e intenção",
            "facetas técnicas combináveis e comparação de resultados",
            "consultas salvas e alertas de novos resultados",
            "histórico local e controles de personalização",
            "resultados explicados com qualidade e compatibilidade",
        ],
    },
    {
        "key": "recommendations",
        "name": "Recomendação e personalização responsável",
        "priority": "P2",
        "impact": "Conteúdo útil e compatível, com diversidade e transparência.",
        "features": [
            "recomendação por impressora, material, habilidade e objetivo",
            "mistura controlada de novidade, relevância e diversidade",
            "proteção contra bolhas, popularidade e concentração",
            "preferências editáveis e perfil de interesse visível",
            "recomendação local sem enviar dados sensíveis quando possível",
            "testes de viés por idioma, região e tamanho do criador",
            "modo descoberta aleatória e curadoria humana",
            "desativação total sem degradar funções básicas",
        ],
    },
    {
        "key": "identity",
        "name": "Identidade, perfil e presença avançada",
        "priority": "P2",
        "impact": "Representação autêntica de makers, organizações e especialidades.",
        "features": [
            "perfil modular com portfólio, habilidades e disponibilidade",
            "identidades pessoal, profissional, educativa e pseudônima",
            "pronomes, nome social e campos culturais opcionais",
            "destaques, posts fixados e coleção de apresentação",
            "currículo maker verificável por projetos e contribuições",
            "status de contratação, mentoria, colaboração e encomenda",
            "QR code e cartão público compartilhável",
            "memorialização, herança e encerramento de conta",
        ],
    },
    {
        "key": "social_graph",
        "name": "Grafo social e relações contextuais",
        "priority": "P2",
        "impact": "Conexões úteis baseadas em confiança, interesse e colaboração real.",
        "features": [
            "seguir tema, tag, impressora, projeto e organização",
            "círculos privados para organizar relações",
            "conexão por colaboração, mentoria e fabricação",
            "contatos próximos com compartilhamento específico",
            "sugestões explicadas por contexto comum",
            "remoção silenciosa, restrição e silenciamento granular",
            "importação de contatos com consentimento bilateral",
            "visualização privada do próprio grafo e lacunas de rede",
        ],
    },
    {
        "key": "publishing",
        "name": "Publicação rica e narrativa de fabricação",
        "priority": "P2",
        "impact": "Conhecimento reproduzível em vez de posts superficiais.",
        "features": [
            "editor em blocos para texto, foto, vídeo, arquivo e etapa",
            "rascunho automático, revisão e publicação agendada",
            "templates para dúvida, tutorial, make, falha e estudo",
            "passo a passo com materiais, ferramentas e tempo",
            "anotação de imagem, vídeo e visualização 3D",
            "coautoria, tradução e republicação autorizada",
            "histórico de edição e comparação de versões",
            "exportação aberta e preservação de links",
        ],
    },
    {
        "key": "media",
        "name": "Fotos, vídeo, live e mídia técnica",
        "priority": "P2",
        "impact": "Demonstração visual de processo, falha, aprendizado e resultado físico.",
        "features": [
            "upload e processamento resiliente de imagem e vídeo",
            "álbuns de progresso, before/after e timelapse",
            "vídeo curto técnico com capítulos e arquivos relacionados",
            "live de impressão, oficina e aula com baixa latência",
            "marcadores temporais para falha, ajuste e resultado",
            "legendas, transcrição, tradução e audiodescrição",
            "proteção de rosto, endereço, tela e metadados sensíveis",
            "download original ou otimizado conforme licença",
        ],
    },
    {
        "key": "models",
        "name": "Biblioteca 3D profissional e gestão de ativos",
        "priority": "P2",
        "impact": "Arquivos confiáveis, organizados, compatíveis e reutilizáveis ao longo do tempo.",
        "features": [
            "estrutura de projeto com peças, conjuntos e variantes",
            "suporte ampliado a STEP, CAD nativo, SVG e documentação",
            "dependências entre arquivos, hardware e consumíveis",
            "metadados técnicos obrigatórios por finalidade",
            "diff geométrico e de metadados entre versões",
            "artefatos derivados reproduzíveis e assinados",
            "espelhamento e preservação de projetos abandonados",
            "download seletivo, bundle e manifesto verificável",
        ],
    },
    {
        "key": "viewer",
        "name": "Visualização 3D e inspeção técnica",
        "priority": "P2",
        "impact": "Compreensão do objeto antes de baixar, fabricar ou comprar.",
        "features": [
            "viewer WebGL progressivo com fallback acessível",
            "explosão de conjunto e árvore de peças",
            "medição, corte, seção, espessura e escala",
            "mapa de overhang, suporte, ilhas e fragilidade",
            "comparação lado a lado e sobreposição de versões",
            "anotações espaciais e comentários por região",
            "visualização de material, cor e acabamento",
            "orçamento de desempenho para modelos grandes no mobile",
        ],
    },
    {
        "key": "parametric",
        "name": "Customização paramétrica e geração",
        "priority": "P2",
        "impact": "Adaptação local de peças sem exigir domínio completo de CAD.",
        "features": [
            "parâmetros declarados com unidade, limite e ajuda",
            "preview instantâneo e validação de geometria",
            "presets compartilháveis por uso e hardware",
            "geração isolada de OpenSCAD e engines compatíveis",
            "fila de geração com cota e cancelamento",
            "versão do gerador vinculada ao arquivo resultante",
            "teste automático de combinações limites",
            "publicação de variação sem quebrar autoria e licença",
        ],
    },
    {
        "key": "slicing",
        "name": "Fatiamento avançado e perfis reproduzíveis",
        "priority": "P2",
        "impact": "Impressões mais confiáveis com parâmetros compreensíveis e comparáveis.",
        "features": [
            "editor completo de perfil com níveis básico e avançado",
            "herança e diff entre perfil base e ajustes",
            "compatibilidade entre slicers com perdas explícitas",
            "orientação, suporte e arranjo assistidos",
            "estimativa comparativa de tempo, custo e resistência",
            "preview por recurso, velocidade, fluxo e ferramenta",
            "experimentos A/B de perfil com resultado físico",
            "reprodução exata por versão de engine e configuração",
        ],
    },
    {
        "key": "print_workflow",
        "name": "Fluxo ponta a ponta de impressão",
        "priority": "P2",
        "impact": "Menos etapas soltas entre descoberta, preparo, fabricação e aprendizado.",
        "features": [
            "checkout técnico do projeto para uma impressora",
            "seleção guiada de variante, peças e quantidades",
            "preflight de arquivo, perfil, material e máquina",
            "aprovação visual do G-code e riscos detectados",
            "fila pessoal com prioridade e janela desejada",
            "monitoramento com checkpoints e intervenção segura",
            "registro de resultado, falha, consumo e fotos",
            "reimpressão reproduzível ou melhoria derivada",
        ],
    },
    {
        "key": "farm",
        "name": "Fazendas de impressão e filas compartilhadas",
        "priority": "P2",
        "impact": "Uso eficiente e seguro de várias máquinas por equipes, escolas e pequenos negócios.",
        "features": [
            "painel de frota com agrupamento por local e capacidade",
            "fila multi-impressora com roteamento e prioridades",
            "calendário de disponibilidade, manutenção e operador",
            "kits de produção com lotes e quantidades",
            "troca de material e preparação de mesa como tarefas",
            "balanceamento por prazo, custo, energia e desgaste",
            "controle de qualidade e rastreabilidade por unidade",
            "handoff de turno, incidentes e produtividade saudável",
        ],
    },
    {
        "key": "vision_ai",
        "name": "Câmeras, visão computacional e assistência por IA",
        "priority": "P2",
        "impact": "Detecção antecipada de falhas com controle humano e redução de desperdício.",
        "features": [
            "configuração guiada de câmera, enquadramento e iluminação",
            "detecção de spaghetti, descolamento e deslocamento",
            "detecção de fumaça ou evento crítico com redundância",
            "score de confiança e política de alerta, pausa ou bloqueio",
            "feedback do usuário sobre falso positivo e falso negativo",
            "processamento local opcional e retenção mínima de imagem",
            "comparação da peça real com referência esperada",
            "painel de desempenho, viés e segurança do modelo",
        ],
    },
    {
        "key": "materials",
        "name": "Materiais, spools e ciência de processo",
        "priority": "P2",
        "impact": "Uso seguro e eficiente de materiais com conhecimento compartilhado.",
        "features": [
            "catálogo de materiais, marcas, lotes e propriedades",
            "inventário de spools com peso, cor, umidade e localização",
            "identificação por QR, NFC e balança",
            "compatibilidade de material com peça, máquina e ambiente",
            "secagem, armazenamento e validade guiados",
            "curvas de temperatura, fluxo e retração versionadas",
            "alertas de emissão, ventilação e descarte",
            "troca, doação e reaproveitamento de sobras locais",
        ],
    },
    {
        "key": "maintenance_network",
        "name": "Manutenção colaborativa e confiabilidade",
        "priority": "P2",
        "impact": "Equipamentos disponíveis por mais tempo e menor risco de falha recorrente.",
        "features": [
            "planos de manutenção por modelo, mod e ambiente",
            "procedimentos ilustrados revisados pela comunidade",
            "diagnóstico por sintomas, logs e histórico",
            "campanhas de inspeção por falha emergente",
            "peças e ferramentas necessárias por procedimento",
            "rede de técnicos e mentores por região",
            "benchmark anônimo de confiabilidade por componente",
            "lições pós-incidente incorporadas ao catálogo",
        ],
    },
    {
        "key": "integrations",
        "name": "Integrações e portabilidade do ecossistema 3D",
        "priority": "P2",
        "impact": "Menos aprisionamento e fluxo contínuo entre ferramentas que makers já usam.",
        "features": [
            "conectores oficiais para repositórios de modelos",
            "importação assistida com licença e autoria preservadas",
            "sincronização opt-in de favoritos, coleções e versões",
            "envio por um clique a slicers e hosts compatíveis",
            "integração com CAD, Git, storage e notas",
            "webhooks de projeto, versão, impressão e incidente",
            "painel de permissões, falhas e última sincronização",
            "exportação em formato aberto para migração completa",
        ],
    },
    {
        "key": "developer",
        "name": "Plataforma de desenvolvedores e extensões",
        "priority": "P2",
        "impact": "Inovação aberta sem comprometer segurança, privacidade ou estabilidade.",
        "features": [
            "API pública versionada com escopos mínimos",
            "portal de documentação, exemplos e changelog",
            "OAuth para aplicações de terceiros",
            "sandbox com dados sintéticos e impressora simulada",
            "SDKs e componentes incorporáveis",
            "marketplace de extensões revisadas",
            "limites, auditoria e revogação por integração",
            "programa de compatibilidade e depreciação previsível",
        ],
    },
    {
        "key": "analytics",
        "name": "Analytics de produto e impacto social",
        "priority": "P2",
        "impact": "Decisões orientadas a resultados humanos, não apenas tempo de tela ou volume.",
        "features": [
            "métricas de sucesso de impressão e falha evitada",
            "métricas de aprendizagem, resolução e autonomia",
            "métricas de reparo, resíduo, energia e vida útil",
            "métricas de inclusão por território sem reidentificação",
            "funis de ativação com privacidade e consentimento",
            "experimentos com hipótese, risco e critério de parada",
            "painel público de impacto com metodologia",
            "alertas contra métrica de vaidade e incentivo perverso",
        ],
    },
    {
        "key": "creator",
        "name": "Ferramentas profissionais para criadores",
        "priority": "P3",
        "impact": "Sustentabilidade econômica e melhor relacionamento entre criadores e comunidade.",
        "features": [
            "studio de conteúdo, modelos, posts e agenda",
            "painel de audiência, retenção e origem de descoberta",
            "CRM leve de apoiadores e clientes com consentimento",
            "respostas salvas, automações e caixa de entrada unificada",
            "kits de mídia, links e vitrine personalizável",
            "metas públicas e roadmap do criador",
            "colaboração e divisão transparente de receita",
            "exportação de dados financeiros e fiscais",
        ],
    },
    {
        "key": "memberships",
        "name": "Clubes, assinaturas e apoio recorrente",
        "priority": "P3",
        "impact": "Financiamento continuado para quem cria conhecimento e modelos úteis.",
        "features": [
            "níveis gratuitos e pagos com benefícios claros",
            "conteúdo, chat e arquivos por nível",
            "acesso antecipado com liberação pública programada",
            "licença comercial por nível e modelo",
            "trial, presente, bolsa e preço regional",
            "gestão de inadimplência, pausa e cancelamento simples",
            "reconhecimento de apoiador sem pressão pública",
            "painel de receita recorrente, churn e entrega de benefício",
        ],
    },
    {
        "key": "marketplace",
        "name": "Marketplace de modelos, serviços e impressões",
        "priority": "P3",
        "impact": "Renda para criadores e acesso seguro a bens digitais e físicos.",
        "features": [
            "venda avulsa de arquivo digital com licença",
            "venda de peça impressa por criador ou parceiro",
            "contratação de design, ajuste e consultoria",
            "carrinho, cupom, imposto, moeda e comprovante",
            "entrega digital segura e limite de download",
            "disputa, reembolso e proteção contra fraude",
            "avaliação separada de arquivo, vendedor e fabricação",
            "transparência de taxa, promoção e ranqueamento comercial",
        ],
    },
    {
        "key": "logistics",
        "name": "Pedidos, logística e pós-venda",
        "priority": "P3",
        "impact": "Entrega previsível de peças físicas e suporte após a compra.",
        "features": [
            "configurador de peça, material, cor e acabamento",
            "prazo calculado por fila e capacidade real",
            "etapas de produção com evidência e aprovação",
            "embalagem, envio, retirada local e rastreamento",
            "inspeção de recebimento e aceite do cliente",
            "reposição por dano, defeito ou incompatibilidade",
            "suporte pós-venda ligado à versão fabricada",
            "logística reversa, reciclagem e descarte responsável",
        ],
    },
    {
        "key": "reputation",
        "name": "Reputação, reconhecimento e credenciais",
        "priority": "P3",
        "impact": "Confiança baseada em contribuição verificável, não apenas popularidade.",
        "features": [
            "reputação multidimensional por competência",
            "credenciais emitidas por escola, comunidade e parceiro",
            "badges por contribuição, manutenção e mentoria",
            "níveis que não bloqueiam funções essenciais",
            "endorsement com contexto e expiração",
            "portfólio de impacto, não só contagem de likes",
            "detecção de troca de favores e fazenda de reputação",
            "contestação e correção de credencial incorreta",
        ],
    },
    {
        "key": "contests",
        "name": "Desafios, concursos e missões coletivas",
        "priority": "P3",
        "impact": "Mobilização criativa para problemas reais e aprendizado por projeto.",
        "features": [
            "desafios temáticos com problema e critérios claros",
            "categorias por idade, recurso e experiência",
            "submissão de equipe, versão e evidência física",
            "jurados, votação comunitária e conflito de interesse",
            "feedback estruturado para todos os participantes",
            "prêmios financeiros, materiais, bolsas e reconhecimento",
            "missões sociais com adoção e acompanhamento do resultado",
            "arquivo permanente de regras, decisões e projetos",
        ],
    },
    {
        "key": "crowdfunding",
        "name": "Financiamento coletivo e pré-venda",
        "priority": "P3",
        "impact": "Viabilização transparente de hardware, conteúdo e iniciativas comunitárias.",
        "features": [
            "campanha com meta, orçamento, risco e cronograma",
            "recompensas digitais, físicas e comunitárias",
            "protótipo e evidência técnica antes da captação",
            "marcos de liberação e prestação de contas",
            "atualizações, perguntas e votação de apoiadores",
            "gestão de atraso, mudança de escopo e reembolso",
            "verificação do responsável e prevenção a fraude",
            "relatório final de entrega, impacto e continuidade",
        ],
    },
    {
        "key": "organizations",
        "name": "Organizações, equipes e presença institucional",
        "priority": "P3",
        "impact": "Coordenação entre empresas, escolas, laboratórios, ONGs e coletivos.",
        "features": [
            "página institucional com unidades e finalidade",
            "membros, equipes, papéis e delegação",
            "portfólio de projetos, equipamentos e capacidade",
            "vagas, voluntariado, estágio e mentoria",
            "políticas públicas de segurança, licença e sustentabilidade",
            "relatórios e comunicados oficiais",
            "verificação por domínio e documentação",
            "transferência de propriedade e continuidade institucional",
        ],
    },
    {
        "key": "open_science",
        "name": "Pesquisa aberta e ciência cidadã",
        "priority": "P3",
        "impact": "Experimentos reproduzíveis e colaboração entre comunidade, academia e indústria.",
        "features": [
            "protocolo experimental com hipótese e método",
            "dataset versionado com licença e dicionário",
            "registro de máquina, perfil e condições ambientais",
            "pré-registro e plano de análise opcional",
            "revisão aberta e réplica independente",
            "DOI ou identificador persistente por resultado",
            "consentimento e ética para dados humanos",
            "painel de replicações, divergências e conhecimento acumulado",
        ],
    },
    {
        "key": "ar_scan",
        "name": "Escaneamento, realidade aumentada e espacial",
        "priority": "P4",
        "impact": "Conexão entre objeto físico, espaço e modelo digital quando houver valor comprovado.",
        "features": [
            "captura fotogramétrica guiada pelo celular",
            "limpeza, escala e reparo assistidos de malha",
            "preview em realidade aumentada no ambiente",
            "comparação do impresso com o modelo por sobreposição",
            "instrução espacial de montagem e manutenção",
            "medição de espaço e teste de encaixe",
            "tour virtual de oficina, laboratório e projeto",
            "controles de privacidade para imagem do ambiente",
        ],
    },
    {
        "key": "automation_ai",
        "name": "Copilotos e automação assistida",
        "priority": "P4",
        "impact": "Redução de barreiras técnicas mantendo explicação, revisão humana e limites seguros.",
        "features": [
            "copiloto de busca e diagnóstico com fontes",
            "assistente de publicação que não inventa evidência",
            "sugestão de tags, licença e compatibilidade",
            "análise preliminar de modelo e printabilidade",
            "geração assistida de suporte e orientação",
            "resumo de comunidade com incerteza e contestação",
            "automação configurável com preview e desfazer",
            "central de decisões de IA, dados usados e opt-out",
        ],
    },
    {
        "key": "future_interfaces",
        "name": "Interfaces futuras e experiências experimentais",
        "priority": "P4",
        "impact": "Exploração responsável de novos meios sem desviar recursos de necessidades sociais urgentes.",
        "features": [
            "painéis ambientais para oficina e parede",
            "controle por voz com confirmação de ações críticas",
            "interfaces vestíveis para monitoramento passivo",
            "visualização espacial colaborativa de montagem",
            "telepresença de mentor em bancada",
            "simulação física imersiva para treinamento",
            "interação háptica com modelos e superfícies",
            "programa de experimentos com gate de valor e segurança",
        ],
    },
]


LENSES = [
    (
        "produto",
        "Implementar {feature} como capacidade de domínio para {impact}",
        "Contrato, regra, permissão, persistência e rollback documentados; não duplicar capacidades existentes.",
    ),
    (
        "tela",
        "Criar fluxo de interface para {feature}, com entrada, detalhe, criação/edição e ação principal inequívocos.",
        "Tela separa lista, detalhe e formulário; possui loading, vazio, erro, sucesso, parcial e conflito quando aplicável.",
    ),
    (
        "mobile",
        "Adaptar {feature} para celular, tablet, PWA e uso em campo com conectividade instável.",
        "Funciona a 320 px, toque, orientação retrato/paisagem e retomada após perda de rede sem ação duplicada.",
    ),
    (
        "acessibilidade",
        "Garantir acesso equivalente a {feature} por teclado, leitor de tela, zoom, contraste e redução de movimento.",
        "Sem bloqueio por gesto, cor, hover, áudio ou visualização 3D; teste automatizado e manual documentado.",
    ),
    (
        "confiança",
        "Aplicar privacidade, segurança, moderação e prevenção de abuso a {feature} desde o desenho.",
        "Threat model, minimização de dados, rate limit, auditoria segura, denúncia/bloqueio e retenção definidos.",
    ),
    (
        "impacto",
        "Medir resultado humano e operacional de {feature}, evitando métricas de vaidade e incentivos perversos.",
        "Define baseline, indicador de sucesso, recortes de equidade, alertas de dano e revisão periódica.",
    ),
    (
        "qualidade",
        "Validar {feature} com testes proporcionais ao risco, fixtures controladas e prova do fluxo real.",
        "Cobre regra, API, permissão, falha, mobile e regressão; itens P0 exigem revisão independente e piloto controlado.",
    ),
]


STATUS_BY_DOMAIN = {
    "communities": "parcial",
    "identity": "parcial",
    "social_graph": "parcial",
    "publishing": "parcial",
    "models": "parcial",
    "viewer": "parcial",
    "slicing": "parcial",
    "print_workflow": "parcial",
    "search": "parcial",
    "recommendations": "parcial",
    "materials": "parcial",
    "maintenance_network": "parcial",
    "integrations": "parcial",
    "moderation": "parcial",
    "privacy": "parcial",
    "security": "parcial",
    "creator": "parcial",
    "marketplace": "parcial",
}


def slug(value: str) -> str:
    table = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüç", "aaaaaeeeeiiiiooooouuuuc")
    return "-".join("".join(ch if ch.isalnum() else " " for ch in value.lower().translate(table)).split())


def work_items() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    sequence = 1
    for domain_index, domain in enumerate(DOMAINS, start=1):
        for feature_index, feature in enumerate(domain["features"], start=1):
            capability_id = f"CAP-{domain_index:02d}-{feature_index:02d}"
            for lens_index, (lens, template, acceptance) in enumerate(LENSES, start=1):
                rows.append(
                    {
                        "id": f"COM-{sequence:04d}",
                        "capability_id": capability_id,
                        "priority": domain["priority"],
                        "status_2026_07": STATUS_BY_DOMAIN.get(domain["key"], "ausente"),
                        "domain": domain["name"],
                        "domain_key": domain["key"],
                        "lens": lens,
                        "feature": feature,
                        "requirement": template.format(feature=feature, impact=domain["impact"]),
                        "acceptance": acceptance,
                        "impact": domain["impact"],
                        "dependency": "produto" if lens_index > 1 else "auditoria de contrato existente",
                    }
                )
                sequence += 1
    return rows


def screen_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    sequence = 1
    for domain_index, domain in enumerate(DOMAINS, start=1):
        for feature_index, feature in enumerate(domain["features"], start=1):
            capability_id = f"CAP-{domain_index:02d}-{feature_index:02d}"
            path = f"/community/{domain['key']}/{slug(feature)}"
            rows.append(
                {
                    "id": f"SCR-{sequence:04d}",
                    "capability_id": capability_id,
                    "priority": domain["priority"],
                    "status_2026_07": STATUS_BY_DOMAIN.get(domain["key"], "ausente"),
                    "domain": domain["name"],
                    "screen": feature.capitalize(),
                    "entry": path,
                    "list_state": f"Lista, busca, filtros e ordenação de {feature}",
                    "detail_state": f"Detalhe, histórico, evidências, relações e permissões de {feature}",
                    "create_state": f"Cadastro/edição guiada de {feature}, fora da tela de listagem",
                    "mobile": "Navegação curta, ação principal alcançável, sem tabela obrigatória e com retomada offline quando aplicável.",
                    "accessibility": "Foco previsível, nomes acessíveis, alternativa a mídia/3D, zoom 400% e contraste AA no mínimo.",
                    "states": "loading; empty; error; success; partial; offline; forbidden; conflict",
                }
            )
            sequence += 1
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_backlog_markdown(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "# Inventário Atômico Da Comunidade Printora",
        "",
        "> Arquivo gerado por `scripts/generate_community_roadmap.py`. Não editar manualmente.",
        "",
        f"Total: **{len(rows)} melhorias verificáveis**, derivadas de {len(DOMAINS)} frentes, "
        f"{sum(len(item['features']) for item in DOMAINS)} capacidades e {len(LENSES)} lentes de entrega.",
        "",
        "Status `parcial` significa que há base relacionada no produto, mas o requisito descrito ainda não está integralmente atendido.",
        "Status `ausente` significa que a auditoria de julho de 2026 não encontrou contrato equivalente no produto.",
        "",
        "| ID | Prioridade | Estado | Frente | Lente | Requisito | Aceite mínimo |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {priority} | {status_2026_07} | {domain} | {lens} | {requirement} | {acceptance} |".format(
                **row
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_screens_markdown(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "# Catálogo De Telas E Fluxos Futuros",
        "",
        "> Arquivo gerado por `scripts/generate_community_roadmap.py`. Rotas são contratos de planejamento, não rotas já implementadas.",
        "",
        f"Total: **{len(rows)} famílias de tela**, cada uma cobrindo lista, detalhe e cadastro/edição separados.",
        "",
        "| ID | Prioridade | Estado | Frente | Tela/fluxo | Entrada planejada | Lista | Detalhe | Cadastro/edição |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {id} | {priority} | {status_2026_07} | {domain} | {screen} | `{entry}` | {list_state} | {detail_state} | {create_state} |".format(
                **row
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_priorities(path: Path, rows: list[dict[str, str]]) -> None:
    lines = [
        "# Prioridade Por Impacto Social",
        "",
        "A ordem abaixo usa impacto humano, urgência, alcance, equidade, redução de dano, dependência estrutural e reversibilidade. Receita e engajamento não elevam prioridade sozinhos.",
        "",
    ]
    for priority in ("P0", "P1", "P2", "P3", "P4"):
        domains = [domain for domain in DOMAINS if domain["priority"] == priority]
        count = sum(1 for row in rows if row["priority"] == priority)
        lines.extend([f"## {priority}", "", f"{count} itens atômicos em {len(domains)} frentes.", ""])
        for domain in domains:
            lines.append(f"- **{domain['name']}** — {domain['impact']}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    items = work_items()
    screens = screen_rows()
    write_csv(OUTPUT / "COMMUNITY_BACKLOG.csv", items)
    write_csv(OUTPUT / "COMMUNITY_SCREENS.csv", screens)
    write_backlog_markdown(OUTPUT / "COMMUNITY_BACKLOG.md", items)
    write_screens_markdown(OUTPUT / "COMMUNITY_SCREENS.md", screens)
    write_priorities(OUTPUT / "PRIORITIES.md", items)
    summary = {
        "domains": len(DOMAINS),
        "capabilities": sum(len(domain["features"]) for domain in DOMAINS),
        "atomic_items": len(items),
        "screen_families": len(screens),
        "screen_states": len(screens) * 3,
        "priorities": {
            priority: sum(1 for row in items if row["priority"] == priority)
            for priority in ("P0", "P1", "P2", "P3", "P4")
        },
    }
    (OUTPUT / "SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
