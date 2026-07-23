import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");

async function readJson(path) {
  return JSON.parse(await readFile(join(root, path), "utf8"));
}

function formatReleaseUpdateStatus(releases, loading = false, fetchError = null) {
  if (loading) return "carregando";
  if (fetchError) return "erro de rede";
  if (!releases) return "não carregado";
  if (releases.status !== "ok") return formatReleaseSourceStatus(releases.status);
  return {
    up_to_date: "já atualizado",
    outdated: "update disponível",
    unknown: "desconhecido",
  }[releases.update_status];
}

function formatReleaseSourceStatus(status) {
  return {
    ok: "online",
    offline: "GitHub offline",
    rate_limited: "limite do GitHub",
    disabled: "desabilitado",
    error: "erro de rede",
  }[status];
}

function releasePanelClass(releases) {
  if (!releases) return "";
  if (releases.status !== "ok") return "warn";
  return releases.update_status === "up_to_date" ? "ok" : "warn";
}

function canShowPlanAction(releases) {
  return Boolean(releases?.latest_release_available && releases?.latest_release?.tag);
}

function canShowApplyAction(plan) {
  return Boolean(plan?.update_supported && plan?.run?.status === "planned");
}

const outdated = await readJson("tests/fixtures/system_releases_outdated.json");
const upToDate = await readJson("tests/fixtures/system_releases_up_to_date.json");
const offline = await readJson("tests/fixtures/system_releases_offline.json");
const rateLimited = await readJson("tests/fixtures/system_releases_rate_limited.json");

assert.equal(formatReleaseUpdateStatus(null, true), "carregando");
assert.equal(formatReleaseUpdateStatus(null, false, "failed to fetch"), "erro de rede");
assert.equal(formatReleaseUpdateStatus(outdated), "update disponível");
assert.equal(formatReleaseUpdateStatus(upToDate), "já atualizado");
assert.equal(formatReleaseUpdateStatus(offline), "GitHub offline");
assert.equal(formatReleaseUpdateStatus(rateLimited), "limite do GitHub");

assert.equal(outdated.safe_mode, "read_only");
assert.equal(outdated.update_supported, false);
assert.equal(outdated.latest_release_available, true);
assert.equal(canShowPlanAction(outdated), true);
assert.equal(outdated.latest_release.changelog_summary, "Correcoes de manutencao e configuracao.");
assert.equal(upToDate.latest_release_available, false);
assert.equal(canShowPlanAction(upToDate), false);
assert.equal(offline.update_supported, false);
assert.equal(rateLimited.update_supported, false);
assert.equal(releasePanelClass(outdated), "warn");
assert.equal(releasePanelClass(upToDate), "ok");
assert.equal(releasePanelClass(offline), "warn");
assert.equal(
  canShowApplyAction({ update_supported: true, run: { status: "planned" } }),
  true,
);
assert.equal(
  canShowApplyAction({ update_supported: false, run: { status: "planned" } }),
  false,
);

const appSource = await readFile(join(root, "src/main.tsx"), "utf8");
const appHookSource = await readFile(join(root, "src/hooks/usePrintoraApp.ts"), "utf8");
const alertCenterSource = await readFile(join(root, "src/alertCenter.ts"), "utf8");
const updatesHookSource = await readFile(join(root, "src/hooks/domains/useUpdates.ts"), "utf8");
const feedbackTypesSource = await readFile(join(root, "src/types/feedback.ts"), "utf8");
const navigationSource = await readFile(join(root, "src/app/navigation.ts"), "utf8");
const overviewScreenSource = await readFile(join(root, "src/screens/OverviewScreen.tsx"), "utf8");
const selfUpdateHookSource = await readFile(join(root, "src/hooks/domains/useSelfUpdate.ts"), "utf8");
const systemApiSource = await readFile(join(root, "src/services/systemApi.ts"), "utf8");
const settingsScreenSource = await readFile(join(root, "src/screens/SettingsScreen.tsx"), "utf8");
const reportsScreenSource = await readFile(join(root, "src/screens/ReportsScreen.tsx"), "utf8");
const agentDetailScreenSource = await readFile(join(root, "src/screens/AgentDetailScreen.tsx"), "utf8");
const selfUpdateModalSource = await readFile(join(root, "src/components/modals/SelfUpdateModal.tsx"), "utf8");
const updatesScreenSource = await readFile(join(root, "src/screens/UpdatesScreen.tsx"), "utf8");
const socialStylesSource = await readFile(join(root, "src/styles/social.css"), "utf8");

assert.doesNotMatch(appSource, /fetch\(/);
assert.match(appHookSource, /await Promise\.allSettled\(\[firmware\.loadBoardPresets\(\), printers\.loadPrinters\(\)\]\);[\s\S]*void selfUpdate\.loadSystemReleases\(\);/);
assert.match(appHookSource, /function getPrinterAvailability\([\s\S]*return health\.connected \? "online" : "offline";/);
assert.match(appHookSource, /if \(!health\.connected\) \{[\s\S]*return "offline";[\s\S]*\}/);
assert.match(appHookSource, /printerAvailability !== "offline"/);
assert.match(appHookSource, /window\.setInterval\(\(\) => \{[\s\S]*settings\.loadPrinterHealth\(contextPrinterId!\);[\s\S]*\}, 60000\);/);
assert.match(appHookSource, /setDetailPrinterId\(printerId\);[\s\S]*shell\.setActiveSection\("printer-detail"\);/);
assert.doesNotMatch(appHookSource, /function openPrinterDetail[\s\S]*printers\.selectPrinter\(printerId\);/);
assert.match(alertCenterSource, /const printerOffline = Boolean\(health && !health\.connected\);/);
assert.match(alertCenterSource, /if \(printerOffline\) \{[\s\S]*return dedupeAlertCenterItems\(items\);[\s\S]*\}/);
assert.doesNotMatch(updatesHookSource, /window\.confirm|window\.alert/);
assert.match(updatesHookSource, /confirmAction\(\{[\s\S]*title: "Silenciar versão"/);
assert.match(updatesHookSource, /showToast\(\{[\s\S]*title: "Versão silenciada"/);
assert.match(feedbackTypesSource, /export type ConfirmActionOptions/);
assert.match(updatesScreenSource, /ArrowUpCircle/);
assert.match(updatesScreenSource, /className="update-run-button"/);
assert.match(updatesScreenSource, /Silenciando\.\.\./);
assert.match(updatesScreenSource, /update-row-busy/);
assert.match(overviewScreenSource, /alertBlockerCount/);
assert.doesNotMatch(overviewScreenSource, /health\?\.counts\.blocker/);
assert.match(navigationSource, /export type PrinterAvailability = "none" \| "unknown" \| "online" \| "offline";/);
assert.match(navigationSource, /\{ title: "Principal", sections: \["overview", "printers", "agents", "projects", "social", "catalog", "setup"\] \}/);
assert.match(navigationSource, /\{ title: "Sistema", sections: \["finance", "manufacturing", "data-intelligence", "settings"\] \}/);
assert.doesNotMatch(navigationSource, /title: "Impressora ativa"/);
assert.match(navigationSource, /sectionKey === "printer-detail" \|\| sectionKey === "agent-detail"/);
assert.match(navigationSource, /onlinePrinterSections\.has\(sectionKey\) \|\| selectedPrinterLocalSections\.has\(sectionKey\)/);
assert.match(navigationSource, /function canUsePrinterTab\([\s\S]*return printerAvailability === "online";/);
assert.doesNotMatch(appSource, /topbar-printer|context-select|topbar-primary|mobile-section-action/);
assert.match(appSource, /className=\{\`icon-button topbar-alert/);
assert.match(appSource, /className=\{\`account-menu-button/);
assert.match(appHookSource, /function buildFleetAlertCenterItems/);
assert.match(appHookSource, /actionKind: "open_printer"/);
assert.match(selfUpdateHookSource, /async function loadSystemReleases\(\)/);
assert.match(selfUpdateHookSource, /async function startSelfUpdateFlow\(\)/);
assert.match(selfUpdateHookSource, /async function startSelfUpdateRecovery\(/);
assert.match(selfUpdateHookSource, /continuar[aá] verificando automaticamente/);
assert.match(selfUpdateHookSource, /Update concluído após reinício/);
assert.match(systemApiSource, /\/api\/system\/update\/plan/);
assert.match(systemApiSource, /\/api\/system\/update\/apply/);
assert.match(systemApiSource, /\/api\/system\/update\/history/);
assert.match(systemApiSource, /\/api\/system\/install-diagnostics/);
assert.match(selfUpdateModalSource, /ATUALIZAR PRINTORA/);
assert.match(appHookSource, /user\.email\.toLowerCase\(\) === "breno@mayder\.com\.br"/);
assert.match(appHookSource, /isPlatformAdmin && !selfUpdate\.systemReleases/);
assert.match(settingsScreenSource, /authUser\?\.email\?\.toLowerCase\(\) === "breno@mayder\.com\.br"/);
assert.match(settingsScreenSource, /Releases da plataforma não fazem parte da operação do cliente/);
assert.match(settingsScreenSource, /Plataforma Printora \(interno\)/);
assert.match(settingsScreenSource, /Histórico da plataforma/);
assert.doesNotMatch(settingsScreenSource, /Administração do sistema/);
assert.doesNotMatch(settingsScreenSource, /Atualizar agora/);
assert.doesNotMatch(settingsScreenSource, /Diagnóstico da instalação/);
assert.doesNotMatch(settingsScreenSource, /Copiar diagnóstico/);
assert.match(reportsScreenSource, /Registro técnico CAN da impressora/);
assert.match(agentDetailScreenSource, /Dispositivo do agente/);
assert.match(agentDetailScreenSource, /raspberry_throttling/);
assert.match(selfUpdateModalSource, /visibleSelfUpdateSteps/);
assert.match(socialStylesSource, /\.social-screen\s*\{[\s\S]*grid-column: 1 \/ -1;/);
assert.match(socialStylesSource, /\.social-screen\s*\{[\s\S]*min-width: 0;/);

console.log("Frontend release states passed.");
