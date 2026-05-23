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

const source = await readFile(join(root, "src/main.tsx"), "utf8");
assert.match(source, /void loadSystemReleases\(\);[\s\S]*await loadPrinters\(\);/);
assert.doesNotMatch(source, /fetch\(["']\/api\/system\/releases["'],\s*\{/);
assert.match(source, /\/api\/system\/update\/plan/);
assert.match(source, /\/api\/system\/update\/apply/);
assert.match(source, /\/api\/system\/update\/history/);
assert.match(source, /ATUALIZAR PRINTORA/);
assert.match(source, /Planejar update/);
assert.match(source, /Atualizar agora/);

console.log("Frontend release states passed.");
