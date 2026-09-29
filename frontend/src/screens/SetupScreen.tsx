import { useEffect, useMemo, useState } from "react";
import { X } from "lucide-react";
import { Metric } from "../components/common";
import { readSetupRecipe, writeSetupRecipe } from "../services/localPreferences";
import { formatDateTime } from "../utils/formatters";
import type { SetupCanPlanStep, SetupFinalValidationStatus, SetupFirmwarePlanStep, SetupFlashPlanStep, SetupPlanStep, SetupRunStatus } from "../types";
import type { ScreenPropsFor } from "./ScreenProps";

const manualRecipeKeys = ["os_image", "network", "ssh_enabled", "physical_ready", "printer_registered"] as const;
type ManualRecipeKey = typeof manualRecipeKeys[number];
type SetupGuide = {
  title: string;
  summary: string;
  options?: string[];
  steps: string[];
  success: string[];
  pitfalls?: string[];
  links?: Array<{ label: string; href: string }>;
};
const manualGuides: Record<ManualRecipeKey, SetupGuide> = {
  os_image: {
    title: "Gravar o sistema na Pi",
    summary: "Esta parte acontece antes do SSH. O Printora ainda não consegue entrar em uma placa virgem.",
    options: [
      "Raspberry Pi oficial: use Raspberry Pi OS Lite 64-bit pelo Raspberry Pi Imager.",
      "BTT Pi 1.2 ou CB1: use a imagem oficial da BIGTREETECH para CB1/BTT Pi.",
      "Evite imagens genéricas se a placa for BTT Pi/CB1, porque boot, Wi-Fi, overlays e drivers podem não bater.",
    ],
    steps: [
      "Identifique a placa: Raspberry Pi oficial, BTT Pi 1.2, CB1 ou outro SBC compatível.",
      "Baixe a imagem no site oficial: Raspberry Pi Imager para Raspberry Pi; releases da BIGTREETECH para BTT Pi/CB1.",
      "Use um cartão microSD confiável ou EMMC. Apague e grave a imagem pelo Raspberry Pi Imager, Balena Etcher ou ferramenta indicada pelo fabricante.",
      "Antes de gravar, configure hostname, usuário, senha ou chave SSH quando a ferramenta permitir.",
      "Depois da gravação, ejete a mídia com segurança, coloque na Pi, conecte rede e ligue a placa.",
      "Aguarde a primeira inicialização. Ela pode demorar alguns minutos porque o sistema expande partição e prepara serviços.",
    ],
    success: [
      "A placa liga sem erro visível.",
      "O sistema inicializa até ficar acessível pela rede.",
      "Você sabe qual usuário será usado no SSH.",
    ],
    pitfalls: [
      "Imagem errada pode ligar LEDs, mas não subir rede nem SSH.",
      "Cartão ruim causa boot intermitente; troque o cartão antes de culpar firmware.",
      "BTT Pi/CB1 normalmente precisa da imagem do fabricante, não da imagem padrão de Raspberry Pi.",
    ],
    links: [
      { label: "Raspberry Pi Imager", href: "https://www.raspberrypi.com/software/" },
      { label: "Raspberry Pi OS", href: "https://www.raspberrypi.com/downloads/" },
      { label: "BIGTREETECH CB1 releases", href: "https://github.com/bigtreetech/CB1/releases" },
      { label: "BIGTREETECH BTT Pi", href: "https://github.com/bigtreetech/BTT-Pi" },
    ],
  },
  network: {
    title: "Conectar na rede",
    summary: "Sem rede local estável, o Printora não consegue validar nem instalar nada por SSH.",
    options: [
      "Cabo Ethernet é a opção mais previsível para primeira instalação.",
      "Wi-Fi funciona, mas depende de SSID, senha, país/região e sinal no local da impressora.",
      "Hostname ajuda o usuário leigo, mas IP direto é melhor para diagnosticar falhas.",
    ],
    steps: [
      "Prefira cabo de rede na primeira instalação.",
      "Se usar Wi-Fi, configure SSID e senha antes do primeiro boot.",
      "Espere o roteador listar a placa ou teste o hostname definido.",
      "Anote IP ou hostname para preencher no próximo passo.",
    ],
    success: [
      "A Pi responde pelo IP ou hostname.",
      "O computador que roda o Printora está na mesma rede.",
      "A porta SSH prevista está liberada.",
    ],
    pitfalls: [
      "Rede de convidados costuma bloquear acesso entre dispositivos.",
      "Hostname pode falhar por DNS/mDNS; nesse caso use o IP.",
      "Wi-Fi fraco pode passar no primeiro teste e cair durante build ou flash.",
    ],
  },
  ssh_enabled: {
    title: "Ativar SSH e criar usuário",
    summary: "O acesso remoto só começa depois que o SSH está ativo no sistema operacional da Pi.",
    options: [
      "SSH com chave ou agente é o caminho preferido.",
      "Caminho de chave local pode ser usado quando a chave não está no agente.",
      "Senha não deve ser digitada no Printora; deixe senha apenas para teste manual fora do app.",
    ],
    steps: [
      "Habilite SSH na imagem, no painel do sistema ou via terminal local.",
      "Use chave SSH sempre que possível; senha não deve ser informada ao Printora.",
      "Confirme o usuário que terá permissão de sudo quando a etapa exigir alteração.",
      "Teste um login SSH fora do Printora se tiver terminal disponível.",
    ],
    success: [
      "O host aceita conexão SSH.",
      "O usuário informado existe.",
      "A autenticação por chave ou agente está pronta.",
    ],
    pitfalls: [
      "Usuário incorreto parece falha de rede, mas é autenticação negada.",
      "Chave privada com senha pode exigir agente SSH carregado.",
      "Sudo sem permissão vai bloquear etapas que aplicam configuração remota.",
    ],
  },
  physical_ready: {
    title: "Conferir placa e cabeamento",
    summary: "Antes de flash real, confirme a parte física. Esta etapa reduz risco de gravar firmware na placa errada.",
    options: [
      "CAN/Katapult é o caminho suportado para flash remoto supervisionado.",
      "USB/DFU e manual permanecem bloqueados até fluxo próprio e validação operacional.",
      "Se existir dúvida sobre UUID, pare e volte para diagnóstico CAN antes do flash.",
    ],
    steps: [
      "Confirme modelo da placa, MCU e método de flash.",
      "Confira alimentação, USB/CAN, U2C, terminação CAN e jumpers de bootloader.",
      "Compare o UUID esperado com o UUID detectado.",
      "Garanta que a impressora esteja parada e acompanhada por uma pessoa.",
    ],
    success: [
      "A placa correta está energizada e visível.",
      "O cabo ou barramento CAN está estável.",
      "Você consegue identificar o UUID antes de executar flash.",
    ],
    pitfalls: [
      "Duas placas iguais no barramento podem confundir UUID.",
      "Terminação CAN errada gera falhas intermitentes.",
      "Flash sem acompanhamento físico dificulta recuperação se a placa entrar em bootloader.",
    ],
  },
  printer_registered: {
    title: "Cadastrar a impressora",
    summary: "Depois da base Klipper aprovada, a impressora deve aparecer em Impressoras para operação normal.",
    options: [
      "Use a URL do Moonraker da Pi instalada, geralmente porta 7125.",
      "Cadastre por hostname se o DNS local for confiável; use IP se precisar estabilidade imediata.",
      "Selecione a impressora como ativa para liberar operação, firmware e manutenção.",
    ],
    steps: [
      "Abra o menu Impressoras.",
      "Cadastre a URL do Moonraker da máquina instalada.",
      "Teste a conexão e selecione a impressora como ativa.",
      "Volte ao Setup e marque esta etapa como concluída.",
    ],
    success: [
      "A impressora aparece no menu Impressoras.",
      "O teste de conexão com Moonraker passa.",
      "As telas de operação passam a usar esta impressora como contexto.",
    ],
    pitfalls: [
      "Klipper pode estar OK e Moonraker ainda estar offline; cadastre só depois de validar ambos.",
      "URL errada costuma passar despercebida quando há mais de uma impressora na rede.",
      "Sem selecionar como ativa, os menus operacionais continuam usando outro contexto.",
    ],
  },
};
const technicalGuides: Record<string, SetupGuide> = {
  ssh_access: {
    title: "Como preencher o acesso SSH",
    summary: "Esta etapa só informa ao Printora onde está a Pi. Nenhuma instalação acontece ao preencher os campos.",
    options: [
      "Host/IP: use hostname como btt-pi.local se sua rede resolver nomes; use IP quando quiser evitar dúvida.",
      "Porta: normalmente 22. Só altere se você configurou SSH em outra porta.",
      "Autenticação: SSH agent/chave padrão é a opção mais simples; caminho de chave serve para uma chave específica.",
    ],
    steps: [
      "Preencha Host/IP, porta, usuário e timeout.",
      "Escolha o método de autenticação.",
      "Clique em Preflight SSH para validar conexão e ambiente sem alterar a Pi.",
      "Se o preflight passar, clique em Gerar plano para ver o que seria necessário instalar/configurar.",
    ],
    success: [
      "Preflight mostra SSH, sistema e ferramentas lidas com sucesso.",
      "Plano dry-run aparece com comandos apenas planejados.",
      "Nenhuma senha ou chave privada é gravada no histórico.",
    ],
    pitfalls: [
      "Timeout muito baixo pode falhar em Pi lenta no primeiro boot.",
      "Host errado pode apontar para outra máquina da rede.",
      "Preflight não instala nada; ele só confirma se já dá para automatizar os próximos passos.",
    ],
  },
  ssh_preflight: {
    title: "Validar ambiente da Pi",
    summary: "O preflight é uma leitura segura para saber se a Pi está pronta para provisionamento.",
    steps: [
      "Execute Preflight SSH.",
      "Leia os checks de sistema, Klipper, Moonraker, printer_data e can0.",
      "Corrija bloqueios básicos antes de avançar para CAN, firmware ou flash.",
      "Gere o plano dry-run para revisar a ordem das próximas ações.",
    ],
    success: [
      "Checks principais aparecem como OK ou com ação clara.",
      "Plano mostra apenas comandos prefixados como planejamento.",
      "Você entende o que ainda será manual e o que pode ser automatizado.",
    ],
  },
  can: {
    title: "Configurar CAN/U2C",
    summary: "Aqui o Printora diagnostica barramento CAN, U2C, interface can0 e UUIDs antes de qualquer aplicação.",
    options: [
      "Interface: use can0 salvo se seu sistema usa outro nome.",
      "Bitrate: 1000000 é comum em setups Klipper CAN modernos; mantenha igual entre U2C, mainboard e toolhead.",
      "Aplicar CAN só fica disponível quando a instalação permite configuração remota e você digita a confirmação.",
    ],
    steps: [
      "Confira interface e bitrate.",
      "Clique em Diagnosticar CAN para ler módulos, links, U2C e UUIDs.",
      "Clique em Plano CAN para revisar mudanças necessárias sem aplicar.",
      "Só use Aplicar CAN quando o plano estiver correto, a impressora estiver parada e a frase de confirmação estiver exata.",
    ],
    success: [
      "U2C aparece detectado quando aplicável.",
      "can0 existe ou o plano explica como criar.",
      "UUIDs esperados aparecem de forma coerente.",
    ],
    pitfalls: [
      "Bitrate diferente entre placas impede comunicação.",
      "Aplicar CAN pode reiniciar interface de rede CAN; faça com a máquina parada.",
      "Sem configuração remota habilitada, a aplicação fica bloqueada por segurança.",
    ],
  },
  firmware: {
    title: "Gerar e compilar firmware",
    summary: "O firmware é gerado por preset e compilado remotamente sem fazer flash automático.",
    options: [
      "Preset deve bater com placa, MCU e método de comunicação reais.",
      "Nome físico é o rótulo humano para evitar confundir placas parecidas.",
      "Variante física conferida deve ser marcada somente depois de olhar a placa real.",
    ],
    steps: [
      "Escolha o preset da placa.",
      "Informe nome físico, papel da placa, caminho do Klipper e pasta de artefatos.",
      "Marque variante física conferida.",
      "Gere o plano e revise .config, hash e binário esperado.",
      "Execute build remoto somente com confirmação literal; ele não faz flash.",
    ],
    success: [
      ".config tem hash e diretório de artefato.",
      "Build gera binário esperado e log copiável.",
      "Nenhum flash é executado nesta etapa.",
    ],
  },
  flash: {
    title: "Flash supervisionado",
    summary: "Esta é uma etapa crítica. O Printora exige preflight, plano e frase específica antes de gravar firmware.",
    options: [
      "CAN/Katapult é o método remoto suportado neste fluxo.",
      "USB/DFU e manual aparecem bloqueados por segurança.",
      "Binário anterior é opcional, mas ajuda rollback manual.",
    ],
    steps: [
      "Informe método, artefato remoto, UUID esperado e binário anterior se existir.",
      "Marque checklist físico somente depois de conferir placa, cabos e UUID.",
      "Execute preflight de flash.",
      "Gere plano, leia rollback e frase de confirmação.",
      "Execute flash apenas com operador presente e confirmação exata.",
    ],
    success: [
      "Preflight confirma placa, artefato e estado seguro.",
      "Plano mostra rollback manual e frase específica.",
      "Execução registra resultado sem editar printer.cfg.",
    ],
    pitfalls: [
      "UUID errado pode gravar na placa errada.",
      "Perda de energia durante flash pode exigir recuperação manual.",
      "Flash não substitui validação final da base Klipper.",
    ],
  },
  final: {
    title: "Validar base Klipper",
    summary: "Esta etapa faz leitura final da base: serviços, CAN, configs, UUIDs, temperaturas, update manager e logs.",
    options: [
      "UUIDs esperados podem ser separados por vírgula.",
      "Configs Klipper normalmente ficam em ~/printer_data/config.",
      "Logs Klipper/Moonraker normalmente ficam em ~/printer_data/logs.",
    ],
    steps: [
      "Preencha UUIDs esperados quando souber quais placas devem aparecer.",
      "Confirme os caminhos de configs e logs.",
      "Clique em Validar base.",
      "Leia o status final: aprovado para calibração, aprovado com observação, intervenção manual ou bloqueado.",
      "Copie o relatório de aceite quando precisar compartilhar evidência.",
    ],
    success: [
      "Klipper e Moonraker respondem.",
      "CAN e UUIDs batem com o esperado.",
      "Relatório sanitizado fica disponível para aceite.",
    ],
  },
};

type SetupScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "CheckCircle2"
  | "ClipboardCheck"
  | "History"
  | "Radio"
  | "RefreshCw"
  | "Server"
  | "ShieldCheck"
  | "Zap"
  | "setupAuthMethod"
  | "setupBusy"
  | "setupCanApplyResult"
  | "setupCanBitrate"
  | "setupCanConfirmation"
  | "setupCanHistory"
  | "setupCanInterfaceName"
  | "setupCanPlan"
  | "setupCanPreflight"
  | "setupFirmwareBoardName"
  | "setupFirmwareBoardRole"
  | "setupFirmwareBuildResult"
  | "setupFirmwareConfirmation"
  | "setupFirmwareHistory"
  | "setupFirmwareKlipperPath"
  | "setupFirmwareOutputRoot"
  | "setupFirmwarePlan"
  | "setupFirmwarePresetId"
  | "setupFirmwareVariantConfirmed"
  | "setupFlashArtifactPath"
  | "setupFlashChecklistConfirmed"
  | "setupFlashConfirmation"
  | "setupFlashExecuteResult"
  | "setupFlashExpectedUuid"
  | "setupFlashHistory"
  | "setupFlashMethod"
  | "setupFlashPlan"
  | "setupFlashPreflight"
  | "setupFlashPreviousBinaryPath"
  | "setupFinalConfigRoot"
  | "setupFinalExpectedUuids"
  | "setupFinalHistory"
  | "setupFinalLogRoot"
  | "setupFinalValidation"
  | "setupHistory"
  | "setupHost"
  | "setupKeyPath"
  | "setupPlan"
  | "setupPort"
  | "setupPreflight"
  | "setupTimeoutSeconds"
  | "setupUsername"
  | "runSetupPlan"
  | "runSetupCanApply"
  | "runSetupCanPlan"
  | "runSetupCanPreflight"
  | "runSetupFirmwareBuild"
  | "runSetupFirmwarePlan"
  | "runSetupFlashExecute"
  | "runSetupFlashPlan"
  | "runSetupFlashPreflight"
  | "runSetupFinalValidation"
  | "runSetupPreflight"
  | "setSetupAuthMethod"
  | "setSetupCanBitrate"
  | "setSetupCanConfirmation"
  | "setSetupCanInterfaceName"
  | "setSetupFirmwareBoardName"
  | "setSetupFirmwareBoardRole"
  | "setSetupFirmwareConfirmation"
  | "setSetupFirmwareKlipperPath"
  | "setSetupFirmwareOutputRoot"
  | "setSetupFirmwarePresetId"
  | "setSetupFirmwareVariantConfirmed"
  | "setSetupFlashArtifactPath"
  | "setSetupFlashChecklistConfirmed"
  | "setSetupFlashConfirmation"
  | "setSetupFlashExpectedUuid"
  | "setSetupFlashMethod"
  | "setSetupFlashPreviousBinaryPath"
  | "setSetupFinalConfigRoot"
  | "setSetupFinalExpectedUuids"
  | "setSetupFinalLogRoot"
  | "setSetupHost"
  | "setSetupKeyPath"
  | "setSetupPort"
  | "setSetupTimeoutSeconds"
  | "setSetupUsername"
>;

export function SetupScreen(props: SetupScreenProps) {
  const {
    AlertTriangle,
    CheckCircle2,
    ClipboardCheck,
    History,
    Radio,
    RefreshCw,
    Server,
    ShieldCheck,
    Zap,
    runSetupPlan,
    runSetupCanApply,
    runSetupCanPlan,
    runSetupCanPreflight,
    runSetupFirmwareBuild,
    runSetupFirmwarePlan,
    runSetupFlashExecute,
    runSetupFlashPlan,
    runSetupFlashPreflight,
    runSetupFinalValidation,
    runSetupPreflight,
    setSetupAuthMethod,
    setSetupCanBitrate,
    setSetupCanConfirmation,
    setSetupCanInterfaceName,
    setSetupFirmwareBoardName,
    setSetupFirmwareBoardRole,
    setSetupFirmwareConfirmation,
    setSetupFirmwareKlipperPath,
    setSetupFirmwareOutputRoot,
    setSetupFirmwarePresetId,
    setSetupFirmwareVariantConfirmed,
    setSetupFlashArtifactPath,
    setSetupFlashChecklistConfirmed,
    setSetupFlashConfirmation,
    setSetupFlashExpectedUuid,
    setSetupFlashMethod,
    setSetupFlashPreviousBinaryPath,
    setSetupFinalConfigRoot,
    setSetupFinalExpectedUuids,
    setSetupFinalLogRoot,
    setSetupHost,
    setSetupKeyPath,
    setSetupPort,
    setSetupTimeoutSeconds,
    setSetupUsername,
    setupAuthMethod,
    setupBusy,
    setupCanApplyResult,
    setupCanBitrate,
    setupCanConfirmation,
    setupCanHistory,
    setupCanInterfaceName,
    setupCanPlan,
    setupCanPreflight,
    setupFirmwareBoardName,
    setupFirmwareBoardRole,
    setupFirmwareBuildResult,
    setupFirmwareConfirmation,
    setupFirmwareHistory,
    setupFirmwareKlipperPath,
    setupFirmwareOutputRoot,
    setupFirmwarePlan,
    setupFirmwarePresetId,
    setupFirmwareVariantConfirmed,
    setupFlashArtifactPath,
    setupFlashChecklistConfirmed,
    setupFlashConfirmation,
    setupFlashExecuteResult,
    setupFlashExpectedUuid,
    setupFlashHistory,
    setupFlashMethod,
    setupFlashPlan,
    setupFlashPreflight,
    setupFlashPreviousBinaryPath,
    setupFinalConfigRoot,
    setupFinalExpectedUuids,
    setupFinalHistory,
    setupFinalLogRoot,
    setupFinalValidation,
    setupHistory,
    setupHost,
    setupKeyPath,
    setupPlan,
    setupPort,
    setupPreflight,
    setupTimeoutSeconds,
    setupUsername,
  } = props;

  const canRun = Boolean(setupHost.trim() && setupUsername.trim() && setupPort > 0);
  const [activeSetupStepKey, setActiveSetupStepKey] = useState<string | null>(null);
  const [manualRecipeDone, setManualRecipeDone] = useState<Record<ManualRecipeKey, boolean>>({
    os_image: false,
    network: false,
    ssh_enabled: false,
    physical_ready: false,
    printer_registered: false,
  });

  useEffect(() => {
    const parsed = readSetupRecipe<Record<ManualRecipeKey, boolean>>();
    if (parsed) {
      setManualRecipeDone((current) => ({ ...current, ...parsed }));
    }
  }, []);

  useEffect(() => {
    writeSetupRecipe(manualRecipeDone);
  }, [manualRecipeDone]);

  const recipeSteps = useMemo(
    () => [
      {
        key: "os_image",
        title: "Gravar o sistema na Pi",
        detail: "Instale Raspberry Pi OS, CB1/BTT Pi OS ou imagem compatível no cartão/EMMC e ligue a placa.",
        status: manualRecipeDone.os_image ? "done" : "todo",
        action: "Orientação",
        href: "#setup-manual-prep",
      },
      {
        key: "network",
        title: "Conectar na rede",
        detail: "A Pi precisa aparecer na rede por cabo ou Wi-Fi antes de qualquer automação.",
        status: manualRecipeDone.network ? "done" : "todo",
        action: "Orientação",
        href: "#setup-manual-prep",
      },
      {
        key: "ssh_enabled",
        title: "Ativar SSH e criar usuário",
        detail: "Habilite SSH no sistema operacional e deixe uma chave ou usuário pronto para acesso.",
        status: manualRecipeDone.ssh_enabled ? "done" : "todo",
        action: "Orientação",
        href: "#setup-manual-prep",
      },
      {
        key: "ssh_access",
        title: "Informar acesso SSH",
        detail: "Preencha host, porta, usuário e método de autenticação. O Printora não armazena senha nem chave privada.",
        status: canRun ? "done" : "todo",
        action: "Preencher",
        href: "#setup-ssh",
      },
      {
        key: "ssh_preflight",
        title: "Validar ambiente da Pi",
        detail: "Execute o preflight e depois gere o plano. Nesta fase nada é instalado sem revisão.",
        status: setupPreflight || setupPlan ? "done" : canRun ? "ready" : "locked",
        action: "Executar",
        href: "#setup-ssh",
      },
      {
        key: "can",
        title: "Configurar CAN/U2C",
        detail: "Diagnostique U2C, can0, bitrate e UUIDs. Aplicações reais exigem frase de confirmação e modo remoto.",
        status: setupCanApplyResult?.status === "ok" || setupCanPreflight || setupCanPlan ? "done" : canRun ? "ready" : "locked",
        action: "Diagnosticar",
        href: "#setup-can",
      },
      {
        key: "firmware",
        title: "Gerar e compilar firmware",
        detail: "Escolha a placa física, gere .config e faça build remoto sem flash automático.",
        status: setupFirmwareBuildResult?.status === "ok" || setupFirmwarePlan ? "done" : canRun ? "ready" : "locked",
        action: "Preparar",
        href: "#setup-firmware",
      },
      {
        key: "physical_ready",
        title: "Conferir placa e cabeamento",
        detail: "Antes de flash e aceite, confirme energia, cabo USB/CAN, bootloader, UUID e placa correta.",
        status: manualRecipeDone.physical_ready || setupFlashChecklistConfirmed ? "done" : "todo",
        action: "Orientação",
        href: "#setup-flash",
      },
      {
        key: "flash",
        title: "Flash supervisionado",
        detail: "Faça preflight de flash, revise rollback e só execute com confirmação explícita.",
        status: setupFlashExecuteResult?.status === "ok" || setupFlashPreflight || setupFlashPlan ? "done" : canRun ? "ready" : "locked",
        action: "Executar",
        href: "#setup-flash",
      },
      {
        key: "final",
        title: "Validar base Klipper",
        detail: "Leia serviços, CAN, configs, UUIDs e logs. O resultado diferencia base pronta de calibração mecânica pendente.",
        status: setupFinalValidation ? "done" : canRun ? "ready" : "locked",
        action: "Validar",
        href: "#setup-final",
      },
      {
        key: "printer_registered",
        title: "Cadastrar a impressora",
        detail: "Depois do aceite, cadastre Moonraker em Impressoras para operar e manter a máquina pelo Printora.",
        status: manualRecipeDone.printer_registered ? "done" : setupFinalValidation?.status === "approved_for_calibration" ? "ready" : "locked",
        action: "Abrir Impressoras",
        href: "?section=printers",
      },
    ],
    [
      canRun,
      manualRecipeDone,
      setupCanApplyResult,
      setupCanPlan,
      setupCanPreflight,
      setupFinalValidation,
      setupFirmwareBuildResult,
      setupFirmwarePlan,
      setupFlashChecklistConfirmed,
      setupFlashExecuteResult,
      setupFlashPlan,
      setupFlashPreflight,
      setupPlan,
      setupPreflight,
    ],
  );
  const recipeDoneCount = recipeSteps.filter((step) => step.status === "done").length;
  const recipeProgress = Math.round((recipeDoneCount / recipeSteps.length) * 100);
  const setupCompleted = recipeDoneCount === recipeSteps.length;
  const activeRecipeStep = recipeSteps.find((step) => step.key === activeSetupStepKey);
  const activeManualStepKey = manualRecipeKeys.includes(activeSetupStepKey as ManualRecipeKey) ? (activeSetupStepKey as ManualRecipeKey) : null;
  const activeTechnicalGuide = activeSetupStepKey ? technicalGuides[activeSetupStepKey] : undefined;

  function toggleManualStep(key: ManualRecipeKey, checked: boolean) {
    setManualRecipeDone((current) => ({ ...current, [key]: checked }));
  }

  return (
    <>
      <article className="panel wide setup-hero-panel">
        <div className="panel-header-row">
          <div>
            <h2>Setup</h2>
            <p>Siga a receita em ordem. Você prepara o que é físico, informa SSH, revisa cada plano e autoriza somente as etapas que realmente podem alterar algo.</p>
          </div>
          <span className="setup-status setup-status-info">Assistido</span>
        </div>
        <div className="setup-boundary-grid">
          <Metric label="Progresso" value={`${recipeProgress}%`} />
          <Metric label="Próxima etapa" value={recipeSteps.find((step) => step.status !== "done")?.title ?? "Cadastrar impressora"} />
          <Metric label="Segurança" value="Confirmação por etapa" />
        </div>
      </article>

      {setupCompleted ? (
        <article className="panel wide setup-complete-panel">
          <div className="panel-header-row">
            <div>
              <h2>Impressora pronta no Printora</h2>
              <p>O checklist foi concluído. A área de preparação fica recolhida para não manter dados e formulários técnicos na frente do operador.</p>
            </div>
            <CheckCircle2 size={22} />
          </div>
          <div className="button-row">
            <a className="primary-button setup-recipe-link" href="?section=printers">Abrir Impressoras</a>
            <button type="button" className="secondary-button" onClick={() => toggleManualStep("printer_registered", false)}>
              Reabrir receita
            </button>
          </div>
        </article>
      ) : (
        <>
      <article className="panel wide setup-recipe-panel" id="setup-manual-prep">
        <div className="panel-header-row">
          <div>
            <h2>Receita de instalação</h2>
            <p>Marque o que já foi feito. O Printora libera os próximos passos conforme você completa a preparação e valida o acesso.</p>
          </div>
          <span className="setup-status setup-status-info">{recipeDoneCount}/{recipeSteps.length}</span>
        </div>
        <div className="setup-progress-bar" aria-label={`Progresso ${recipeProgress}%`}>
          <span style={{ width: `${recipeProgress}%` }} />
        </div>
        <div className="setup-recipe-grid">
          {recipeSteps.map((step, index) => (
            <section key={step.key} className={`setup-recipe-step setup-recipe-${step.status}`}>
              <div className="setup-recipe-index">{index + 1}</div>
              <div>
                <div className="setup-recipe-title-row">
                  <strong>{step.title}</strong>
                  <span>{formatRecipeStatus(step.status)}</span>
                </div>
                <p>{step.detail}</p>
                <div className="setup-recipe-actions">
                  {manualRecipeKeys.includes(step.key as ManualRecipeKey) ? (
                    <label className="setup-inline-check">
                      <input
                        type="checkbox"
                        checked={manualRecipeDone[step.key as ManualRecipeKey]}
                        onChange={(event) => toggleManualStep(step.key as ManualRecipeKey, event.target.checked)}
                      />
                      Já foi feito
                    </label>
                  ) : null}
                  <button type="button" className="secondary-button setup-recipe-link" onClick={() => setActiveSetupStepKey(step.key)}>
                    <ClipboardCheck size={14} />
                    {step.action}
                  </button>
                </div>
              </div>
            </section>
          ))}
        </div>
      </article>

      <article className="panel wide setup-help-panel">
        <div>
          <strong>Antes do SSH</strong>
          <span>O Printora ainda não consegue acessar placa virgem. Primeiro grave o sistema operacional, ligue a Pi na rede e habilite SSH.</span>
        </div>
        <div>
          <strong>Depois do SSH</strong>
          <span>O Printora executa leituras, monta planos e só aplica ações críticas quando você digita a confirmação pedida.</span>
        </div>
        <div>
          <strong>Resultado final</strong>
          <span>Ao aprovar a base Klipper, cadastre a impressora em Impressoras para operação, manutenção e relatórios.</span>
        </div>
      </article>

        </>
      )}

      {!setupCompleted && activeSetupStepKey ? (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={activeRecipeStep?.title ?? "Etapa do setup"}>
          <div className="modal-card setup-modal-card">
            <div className="modal-header">
              <div>
                <h2>{activeRecipeStep?.title ?? "Etapa do setup"}</h2>
                <p>{activeRecipeStep?.detail ?? "Siga a etapa e feche quando terminar."}</p>
              </div>
              <button type="button" className="icon-button" onClick={() => setActiveSetupStepKey(null)} aria-label="Fechar etapa">
                <X size={18} />
              </button>
            </div>
            <div className="setup-modal-body">
              {activeManualStepKey ? (
                <SetupManualStep
                  stepKey={activeManualStepKey}
                  done={manualRecipeDone[activeManualStepKey]}
                  onToggle={(checked) => toggleManualStep(activeManualStepKey, checked)}
                />
              ) : null}
              {!activeManualStepKey && activeTechnicalGuide ? <SetupGuidePanel guide={activeTechnicalGuide} /> : null}

      <article className="panel setup-connection-panel" id="setup-ssh" hidden={!["ssh_access", "ssh_preflight"].includes(activeSetupStepKey)}>
        <div className="panel-header-row">
          <div>
            <h2>1. Acesso SSH</h2>
            <p>Preencha os dados da Pi quando ela já estiver ligada, com Linux instalado, rede funcionando e SSH ativo.</p>
          </div>
          <Server size={20} />
        </div>
        <div className="form-grid setup-form-grid">
          <label>
            Host/IP
            <input value={setupHost} onChange={(event) => setSetupHost(event.target.value)} placeholder="btt-pi.local" />
          </label>
          <label>
            Porta
            <input type="number" min={1} max={65535} value={setupPort} onChange={(event) => setSetupPort(Number(event.target.value))} />
          </label>
          <label>
            Usuário
            <input value={setupUsername} onChange={(event) => setSetupUsername(event.target.value)} placeholder="pi" />
          </label>
          <label>
            Timeout
            <input type="number" min={2} max={60} value={setupTimeoutSeconds} onChange={(event) => setSetupTimeoutSeconds(Number(event.target.value))} />
          </label>
          <label>
            Autenticação
            <select value={setupAuthMethod} onChange={(event) => setSetupAuthMethod(event.target.value as "agent" | "key_path")}>
              <option value="agent">SSH agent / chave padrão</option>
              <option value="key_path">Caminho de chave no host local</option>
            </select>
          </label>
          {setupAuthMethod === "key_path" ? (
            <label>
              Caminho da chave
              <input value={setupKeyPath} onChange={(event) => setSetupKeyPath(event.target.value)} placeholder="~/.ssh/id_ed25519" />
            </label>
          ) : null}
        </div>
        <div className="button-row">
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupPreflight()}>
            <ShieldCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Preflight SSH
          </button>
          <button type="button" className="primary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupPlan()}>
            <ClipboardCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Gerar plano
          </button>
        </div>
      </article>

      <article className="panel setup-result-panel" hidden={!["ssh_access", "ssh_preflight"].includes(activeSetupStepKey)}>
        <div className="panel-header-row">
          <div>
            <h2>Preflight</h2>
            <p>{setupPreflight?.summary ?? "Nenhum preflight executado."}</p>
          </div>
          {setupPreflight ? <StatusBadge status={setupPreflight.status} /> : null}
        </div>
        {setupPreflight ? (
          <div className="setup-check-list">
            {setupPreflight.checks.map((check) => (
              <div key={check.key} className={`setup-check setup-${check.status}`}>
                {check.status === "ok" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                <div>
                  <strong>{check.label}</strong>
                  <span>{check.detail}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">Informe o SSH da Pi e execute o preflight.</div>
        )}
      </article>

      <article className="panel wide setup-plan-panel" hidden={!["ssh_access", "ssh_preflight"].includes(activeSetupStepKey)}>
        <div className="panel-header-row">
          <div>
            <h2>Plano dry-run</h2>
            <p>{setupPlan?.summary ?? "O plano aparece depois do preflight completo."}</p>
          </div>
          {setupPlan ? <StatusBadge status={setupPlan.status} /> : <RefreshCw size={18} />}
        </div>
        {setupPlan?.blocked_reasons.length ? (
          <div className="action-result warning">
            <strong>Bloqueios</strong>
            <span>{setupPlan.blocked_reasons.join(" ")}</span>
          </div>
        ) : null}
        {setupPlan ? (
          <div className="setup-step-list">
            {setupPlan.steps.map((step) => (
              <SetupStepCard key={step.key} step={step} />
            ))}
          </div>
        ) : (
          <div className="empty-state">Nenhum comando será executado nesta tela. O fluxo gera plano revisável.</div>
        )}
      </article>

      <article className="panel wide setup-can-panel" id="setup-can" hidden={activeSetupStepKey !== "can"}>
        <div className="panel-header-row">
          <div>
            <h2>2. CAN/U2C</h2>
            <p>Diagnóstico remoto de U2C, módulos CAN, interface can0, bitrate, UUIDs e plano de configuração.</p>
          </div>
          <Radio size={20} />
        </div>
        <div className="form-grid setup-form-grid">
          <label>
            Interface
            <input value={setupCanInterfaceName} onChange={(event) => setSetupCanInterfaceName(event.target.value)} placeholder="can0" />
          </label>
          <label>
            Bitrate
            <input type="number" min={10000} max={5000000} step={10000} value={setupCanBitrate} onChange={(event) => setSetupCanBitrate(Number(event.target.value))} />
          </label>
        </div>
        <div className="button-row">
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupCanPreflight()}>
            <ShieldCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Diagnosticar CAN
          </button>
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupCanPlan()}>
            <ClipboardCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Plano CAN
          </button>
        </div>
        {setupCanPreflight ? (
          <div className="setup-check-list setup-can-findings">
            {setupCanPreflight.findings.map((finding) => (
              <div key={finding.key} className={`setup-check setup-${finding.status === "blocked" ? "error" : finding.status}`}>
                {finding.status === "ok" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                <div>
                  <strong>{finding.title}</strong>
                  <span>{finding.detail}</span>
                  <small>{finding.action}</small>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">Execute o diagnóstico CAN depois de informar o SSH.</div>
        )}
        {setupCanPlan ? (
          <div className="setup-step-list">
            {setupCanPlan.blocked_reasons.length ? (
              <div className="action-result warning">
                <strong>Bloqueios CAN</strong>
                <span>{setupCanPlan.blocked_reasons.join(" ")}</span>
              </div>
            ) : null}
            {setupCanPlan.steps.map((step) => (
              <SetupStepCard key={step.key} step={step} />
            ))}
          </div>
        ) : null}
        <div className="setup-apply-box">
          <label>
            Confirmação para apply CAN
            <input value={setupCanConfirmation} onChange={(event) => setSetupCanConfirmation(event.target.value)} placeholder="CONFIGURAR CAN0" />
          </label>
          <button type="button" className="danger-button" disabled={!canRun || setupBusy || setupCanConfirmation !== "CONFIGURAR CAN0"} onClick={() => void runSetupCanApply()}>
            <AlertTriangle className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Aplicar CAN
          </button>
          <p>A configuração remota precisa estar habilitada; caso contrário, a tentativa permanece bloqueada e registrada.</p>
        </div>
        {setupCanApplyResult ? (
          <div className={`action-result ${setupCanApplyResult.status === "ok" ? "success" : "warning"}`}>
            <strong>{setupCanApplyResult.summary}</strong>
            <span>{setupCanApplyResult.blocked_reasons.length ? setupCanApplyResult.blocked_reasons.join(" ") : "Resultado registrado no histórico."}</span>
          </div>
        ) : null}
      </article>

      <article className="panel wide setup-firmware-panel" id="setup-firmware" hidden={activeSetupStepKey !== "firmware"}>
        <div className="panel-header-row">
          <div>
            <h2>3. Firmware remoto</h2>
            <p>Selecione a placa física, gere .config, planeje build remoto e compile sem flash.</p>
          </div>
          <Zap size={20} />
        </div>
        <div className="form-grid setup-form-grid">
          <label>
            Preset
            <select value={setupFirmwarePresetId} onChange={(event) => setSetupFirmwarePresetId(event.target.value)}>
              <option value="btt_octopus_pro_h723_usb_can">BTT Octopus Pro H723</option>
              <option value="btt_ebb36_g0b1_can">BTT EBB36 v1.2/G0B1</option>
              <option value="btt_kraken_h723_usb_can">BTT Kraken H723</option>
              <option value="btt_manta_m8p_v2_h723_usb_can">BTT Manta M8P v2 H723</option>
              <option value="mellow_fly_sht36_v3_rp2040_can">Mellow Fly SHT36 v3</option>
            </select>
          </label>
          <label>
            Nome físico
            <input value={setupFirmwareBoardName} onChange={(event) => setSetupFirmwareBoardName(event.target.value)} placeholder="Octopus Pro H723" />
          </label>
          <label>
            Papel
            <select value={setupFirmwareBoardRole} onChange={(event) => setSetupFirmwareBoardRole(event.target.value as "mainboard" | "toolhead" | "can_adapter" | "unknown")}>
              <option value="mainboard">MCU principal</option>
              <option value="toolhead">Toolhead</option>
              <option value="can_adapter">Adaptador CAN</option>
              <option value="unknown">Outro</option>
            </select>
          </label>
          <label>
            Klipper remoto
            <input value={setupFirmwareKlipperPath} onChange={(event) => setSetupFirmwareKlipperPath(event.target.value)} placeholder="~/klipper" />
          </label>
          <label>
            Artefatos
            <input value={setupFirmwareOutputRoot} onChange={(event) => setSetupFirmwareOutputRoot(event.target.value)} placeholder="~/.local/share/printora/firmware-setup" />
          </label>
          <label className="setup-checkbox-label">
            <input type="checkbox" checked={setupFirmwareVariantConfirmed} onChange={(event) => setSetupFirmwareVariantConfirmed(event.target.checked)} />
            Variante física conferida
          </label>
        </div>
        <div className="button-row">
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupFirmwarePlan()}>
            <ClipboardCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Plano firmware
          </button>
        </div>
        {setupFirmwarePlan ? (
          <div className="setup-step-list">
            {setupFirmwarePlan.blocked_reasons.length ? (
              <div className="action-result warning">
                <strong>Bloqueios firmware</strong>
                <span>{setupFirmwarePlan.blocked_reasons.join(" ")}</span>
              </div>
            ) : null}
            <div className="setup-artifact-summary">
              <Metric label="Config SHA" value={setupFirmwarePlan.config_sha256.slice(0, 12)} />
              <Metric label="Artefatos" value={setupFirmwarePlan.artifact_dir} />
              <Metric label="Binário" value={setupFirmwarePlan.expected_binary_path} />
            </div>
            {setupFirmwarePlan.steps.map((step) => (
              <SetupStepCard key={step.key} step={step} />
            ))}
          </div>
        ) : (
          <div className="empty-state">Confirme a variante física e gere o plano de firmware.</div>
        )}
        <div className="setup-apply-box">
          <label>
            Confirmação para build sem flash
            <input value={setupFirmwareConfirmation} onChange={(event) => setSetupFirmwareConfirmation(event.target.value)} placeholder="BUILD_FIRMWARE_NO_FLASH" />
          </label>
          <button type="button" className="danger-button" disabled={!canRun || setupBusy || setupFirmwareConfirmation !== "BUILD_FIRMWARE_NO_FLASH"} onClick={() => void runSetupFirmwareBuild()}>
            <AlertTriangle className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Build remoto
          </button>
          <p>A compilação remota precisa estar habilitada e nunca executa flash automaticamente.</p>
        </div>
        {setupFirmwareBuildResult ? (
          <div className={`action-result ${setupFirmwareBuildResult.status === "ok" ? "success" : "warning"}`}>
            <strong>{setupFirmwareBuildResult.summary}</strong>
            <span>{setupFirmwareBuildResult.blocked_reasons.length ? setupFirmwareBuildResult.blocked_reasons.join(" ") : setupFirmwareBuildResult.binary_path ?? "Artefato registrado."}</span>
          </div>
        ) : null}
      </article>

      <article className="panel wide setup-flash-panel" id="setup-flash" hidden={activeSetupStepKey !== "flash"}>
        <div className="panel-header-row">
          <div>
            <h2>4. Flash supervisionado</h2>
            <p>Preflight crítico, plano revisável e execução CAN/Katapult com trava operacional.</p>
          </div>
          <AlertTriangle size={20} />
        </div>
        <div className="form-grid setup-form-grid">
          <label>
            Método
            <select value={setupFlashMethod} onChange={(event) => setSetupFlashMethod(event.target.value as "can_katapult" | "usb_dfu" | "manual")}>
              <option value="can_katapult">CAN/Katapult</option>
              <option value="usb_dfu">USB/DFU (bloqueado)</option>
              <option value="manual">Manual (bloqueado)</option>
            </select>
          </label>
          <label>
            Artefato remoto
            <input value={setupFlashArtifactPath} onChange={(event) => setSetupFlashArtifactPath(event.target.value)} placeholder={setupFirmwareBuildResult?.binary_path ?? setupFirmwarePlan?.expected_binary_path ?? "~/.local/share/printora/firmware-setup/ebb36/klipper.bin"} />
          </label>
          <label>
            UUID esperado
            <input value={setupFlashExpectedUuid} onChange={(event) => setSetupFlashExpectedUuid(event.target.value)} placeholder="0123456789ab" />
          </label>
          <label>
            Binário anterior
            <input value={setupFlashPreviousBinaryPath} onChange={(event) => setSetupFlashPreviousBinaryPath(event.target.value)} placeholder="opcional: caminho do firmware anterior" />
          </label>
          <label className="setup-checkbox-label">
            <input type="checkbox" checked={setupFlashChecklistConfirmed} onChange={(event) => setSetupFlashChecklistConfirmed(event.target.checked)} />
            Checklist físico conferido
          </label>
        </div>
        <div className="button-row">
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupFlashPreflight()}>
            <ShieldCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Preflight flash
          </button>
          <button type="button" className="secondary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupFlashPlan()}>
            <ClipboardCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Plano flash
          </button>
        </div>
        {setupFlashPreflight ? (
          <div className="setup-check-list setup-can-findings">
            {setupFlashPreflight.findings.map((finding) => (
              <div key={finding.key} className={`setup-check setup-${finding.status === "blocked" || finding.status === "requires_recovery" ? "error" : finding.status}`}>
                {finding.status === "ok" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                <div>
                  <strong>{finding.title}</strong>
                  <span>{finding.detail}</span>
                  <small>{finding.action}</small>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">Use o artefato do build remoto e execute o preflight antes do flash.</div>
        )}
        {setupFlashPlan ? (
          <div className="setup-step-list">
            {setupFlashPlan.blocked_reasons.length ? (
              <div className="action-result warning">
                <strong>Bloqueios flash</strong>
                <span>{setupFlashPlan.blocked_reasons.join(" ")}</span>
              </div>
            ) : null}
            <div className="setup-artifact-summary">
              <Metric label="Confirmação" value={setupFlashPlan.confirmation_phrase} />
              <Metric label="Artefato SHA" value={setupFlashPlan.artifact_sha256?.slice(0, 12) ?? "pendente"} />
              <Metric label="UUID" value={setupFlashPlan.expected_uuid ?? "pendente"} />
            </div>
            {setupFlashPlan.steps.map((step) => (
              <SetupStepCard key={step.key} step={step} />
            ))}
            <div className="action-result warning">
              <strong>Rollback manual</strong>
              <span>{setupFlashPlan.rollback.join(" ")}</span>
            </div>
          </div>
        ) : null}
        <div className="setup-apply-box">
          <label>
            Confirmação para flash real
            <input value={setupFlashConfirmation} onChange={(event) => setSetupFlashConfirmation(event.target.value)} placeholder={setupFlashPlan?.confirmation_phrase ?? "gere o plano primeiro"} />
          </label>
          <button type="button" className="danger-button" disabled={!canRun || setupBusy || !setupFlashPlan || setupFlashConfirmation !== setupFlashPlan.confirmation_phrase} onClick={() => void runSetupFlashExecute()}>
            <AlertTriangle className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Executar flash
          </button>
          <p>O flash remoto precisa estar habilitado; caso contrário, a tentativa permanece bloqueada e registrada.</p>
        </div>
        {setupFlashExecuteResult ? (
          <div className={`action-result ${setupFlashExecuteResult.status === "ok" ? "success" : "warning"}`}>
            <strong>{setupFlashExecuteResult.summary}</strong>
            <span>{setupFlashExecuteResult.blocked_reasons.length ? setupFlashExecuteResult.blocked_reasons.join(" ") : setupFlashExecuteResult.artifact_sha256?.slice(0, 12) ?? "Resultado registrado."}</span>
          </div>
        ) : null}
      </article>

      <article className="panel wide setup-final-panel" id="setup-final" hidden={activeSetupStepKey !== "final"}>
        <div className="panel-header-row">
          <div>
            <h2>5. Validação final</h2>
            <p>Fecha a base Klipper com coleta read-only, checklist técnico e relatório de aceite sanitizado.</p>
          </div>
          <CheckCircle2 size={20} />
        </div>
        <div className="form-grid setup-form-grid">
          <label>
            UUIDs esperados
            <input value={setupFinalExpectedUuids} onChange={(event) => setSetupFinalExpectedUuids(event.target.value)} placeholder="0123456789ab, abcdef123456" />
          </label>
          <label>
            Configs Klipper
            <input value={setupFinalConfigRoot} onChange={(event) => setSetupFinalConfigRoot(event.target.value)} placeholder="~/printer_data/config" />
          </label>
          <label>
            Logs Klipper/Moonraker
            <input value={setupFinalLogRoot} onChange={(event) => setSetupFinalLogRoot(event.target.value)} placeholder="~/printer_data/logs" />
          </label>
        </div>
        <div className="button-row">
          <button type="button" className="primary-button" disabled={!canRun || setupBusy} onClick={() => void runSetupFinalValidation()}>
            <ShieldCheck className={setupBusy ? "button-busy-icon" : undefined} size={16} />
            Validar base
          </button>
        </div>
        {setupFinalValidation ? (
          <div className="setup-step-list">
            <div className={`action-result ${setupFinalValidation.status === "approved_for_calibration" ? "success" : setupFinalValidation.status === "blocked" ? "danger" : "warning"}`}>
              <strong>{setupFinalValidation.summary}</strong>
              <span>{setupFinalValidation.status === "approved_for_calibration" ? "Pronta para calibração mecânica." : "Revise os itens abaixo antes de continuar."}</span>
            </div>
            <div className="setup-artifact-summary">
              <Metric label="Status" value={formatFinalStatus(setupFinalValidation.status)} />
              <Metric label="Interface" value={setupFinalValidation.interface_name} />
              <Metric label="UUIDs" value={setupFinalValidation.expected_uuids.length ? String(setupFinalValidation.expected_uuids.length) : "manual"} />
            </div>
            <div className="setup-check-list">
              {setupFinalValidation.checks.map((check) => (
                <div key={check.key} className={`setup-check setup-${check.status === "blocked" ? "error" : check.status === "manual" ? "warning" : check.status}`}>
                  {check.status === "ok" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
                  <div>
                    <strong>{check.title}</strong>
                    <span>{check.detail}</span>
                    <small>{check.action}</small>
                  </div>
                </div>
              ))}
            </div>
            <div className="setup-report-box">
              <div className="panel-header-row">
                <strong>Relatório de aceite</strong>
                <button type="button" className="secondary-button" onClick={() => void navigator.clipboard?.writeText(setupFinalValidation.report_markdown)}>
                  Copiar relatório
                </button>
              </div>
              <pre>{setupFinalValidation.report_markdown}</pre>
            </div>
          </div>
        ) : (
          <div className="empty-state">Informe os UUIDs esperados e execute a validação final quando a base estiver montada.</div>
        )}
      </article>

      <article className="panel wide setup-history-panel" hidden={Boolean(activeManualStepKey)}>
        <div className="panel-header-row">
          <div>
            <h2>Histórico</h2>
            <p>Registros locais sem senha, token ou chave privada.</p>
          </div>
          <History size={18} />
        </div>
        {setupHistory.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Tipo</th>
                  <th>Alvo</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {setupHistory.slice(0, 8).map((run) => (
                  <tr key={run.id}>
                    <td>{formatDateTime(run.created_at)}</td>
                    <td>{run.run_type === "plan" ? "Plano" : "Preflight"}</td>
                    <td>{run.target_user}@{run.target_host}:{run.target_port}</td>
                    <td><StatusBadge status={run.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">Sem histórico de setup.</div>
        )}
        {setupCanHistory.length ? (
          <div className="table-wrap setup-can-history">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>CAN</th>
                  <th>Alvo</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {setupCanHistory.slice(0, 8).map((run) => (
                  <tr key={run.id}>
                    <td>{formatDateTime(run.created_at)}</td>
                    <td>{run.run_type} · {run.interface_name} · {run.bitrate}</td>
                    <td>{run.target_user}@{run.target_host}:{run.target_port}</td>
                    <td><StatusBadge status={run.status === "blocked" ? "error" : run.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        {setupFirmwareHistory.length ? (
          <div className="table-wrap setup-can-history">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Firmware</th>
                  <th>Alvo</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {setupFirmwareHistory.slice(0, 8).map((run) => (
                  <tr key={run.id}>
                    <td>{formatDateTime(run.created_at)}</td>
                    <td>{run.run_type} · {run.board_name} · {run.preset_id}</td>
                    <td>{run.target_user}@{run.target_host}:{run.target_port}</td>
                    <td><StatusBadge status={run.status === "blocked" ? "error" : run.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        {setupFlashHistory.length ? (
          <div className="table-wrap setup-can-history">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Flash</th>
                  <th>Alvo</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {setupFlashHistory.slice(0, 8).map((run) => (
                  <tr key={run.id}>
                    <td>{formatDateTime(run.created_at)}</td>
                    <td>{run.run_type} · {run.board_name} · {run.flash_method}</td>
                    <td>{run.target_user}@{run.target_host}:{run.target_port}</td>
                    <td><StatusBadge status={run.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        {setupFinalHistory.length ? (
          <div className="table-wrap setup-can-history">
            <table>
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Validação</th>
                  <th>Alvo</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {setupFinalHistory.slice(0, 8).map((run) => (
                  <tr key={run.id}>
                    <td>{formatDateTime(run.created_at)}</td>
                    <td>{run.interface_name} · {run.summary}</td>
                    <td>{run.target_user}@{run.target_host}:{run.target_port}</td>
                    <td><FinalStatusBadge status={run.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </article>
            </div>
            <div className="modal-footer">
              <button type="button" className="secondary-button" onClick={() => setActiveSetupStepKey(null)}>
                Fechar
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}

function StatusBadge({ status }: { status: SetupRunStatus | "blocked" | "requires_recovery" }) {
  const tone = status === "ok" ? "success" : status === "warning" ? "warning" : "danger";
  const label = status === "ok" ? "OK" : status === "warning" ? "Atenção" : status === "requires_recovery" ? "Recuperação" : "Erro";
  return <span className={`setup-status setup-status-${tone}`}>{label}</span>;
}

function FinalStatusBadge({ status }: { status: SetupFinalValidationStatus }) {
  const tone = status === "approved_for_calibration" ? "success" : status === "blocked" ? "danger" : "warning";
  return <span className={`setup-status setup-status-${tone}`}>{formatFinalStatus(status)}</span>;
}

function formatFinalStatus(status: SetupFinalValidationStatus) {
  if (status === "approved_for_calibration") return "Aprovado";
  if (status === "approved_with_notes") return "Com observação";
  if (status === "needs_manual_intervention") return "Conferir";
  return "Bloqueado";
}

function formatRecipeStatus(status: string) {
  if (status === "done") return "feito";
  if (status === "ready") return "pronto";
  if (status === "locked") return "aguardando";
  return "a fazer";
}

function SetupManualStep({ done, onToggle, stepKey }: { done: boolean; onToggle: (checked: boolean) => void; stepKey: ManualRecipeKey }) {
  const guide = manualGuides[stepKey];
  return (
    <article className="panel setup-manual-modal-panel">
      <div className="panel-header-row">
        <div>
          <h2>{guide.title}</h2>
          <p>{guide.summary}</p>
        </div>
        <StatusBadge status={done ? "ok" : "warning"} />
      </div>
      <SetupGuideContent guide={guide} />
      <label className="setup-modal-check">
        <input type="checkbox" checked={done} onChange={(event) => onToggle(event.target.checked)} />
        Já concluí esta etapa
      </label>
      {stepKey === "printer_registered" ? (
        <div className="button-row">
          <a className="primary-button setup-recipe-link" href="?section=printers">Abrir Impressoras</a>
        </div>
      ) : null}
    </article>
  );
}

function SetupGuidePanel({ guide }: { guide: SetupGuide }) {
  return (
    <article className="panel setup-guide-panel">
      <div className="panel-header-row">
        <div>
          <h2>{guide.title}</h2>
          <p>{guide.summary}</p>
        </div>
        <StatusBadge status="warning" />
      </div>
      <SetupGuideContent guide={guide} />
    </article>
  );
}

function SetupGuideContent({ guide }: { guide: SetupGuide }) {
  return (
    <div className="setup-manual-grid">
      {guide.options?.length ? (
        <section>
          <strong>Opções e escolhas</strong>
          <ol>
            {guide.options.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </section>
      ) : null}
      <section>
        <strong>Faça nesta ordem</strong>
        <ol>
          {guide.steps.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>
      <section>
        <strong>Como saber que terminou</strong>
        <ol>
          {guide.success.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </section>
      {guide.pitfalls?.length ? (
        <section>
          <strong>Erros comuns</strong>
          <ol>
            {guide.pitfalls.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
        </section>
      ) : null}
      {guide.links?.length ? (
        <section className="setup-guide-links">
          <strong>Fontes oficiais</strong>
          <div>
            {guide.links.map((link) => (
              <a key={link.href} className="secondary-button setup-recipe-link" href={link.href} target="_blank" rel="noreferrer">
                {link.label}
              </a>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function SetupStepCard({ step }: { step: SetupPlanStep | SetupCanPlanStep | SetupFirmwarePlanStep | SetupFlashPlanStep }) {
  return (
    <section className={`setup-step setup-step-${step.status}`}>
      <div className="setup-step-header">
        <div>
          <strong>{step.title}</strong>
          <span>{step.detail}</span>
        </div>
        <span className={`setup-status setup-status-${step.status === "ready" ? "success" : step.status === "blocked" ? "danger" : "warning"}`}>{step.status}</span>
      </div>
      {step.commands.length ? (
        <div className="setup-command-list">
          {step.commands.map((command) => (
            <div key={`${step.key}-${command.command}`} className={`setup-command setup-command-${command.risk}`}>
              <code>{command.command}</code>
              <span>{command.reason}</span>
            </div>
          ))}
        </div>
      ) : null}
      {step.rollback ? <p className="setup-rollback">Rollback: {step.rollback}</p> : null}
    </section>
  );
}
