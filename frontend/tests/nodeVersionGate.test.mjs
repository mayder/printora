import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const gate = fileURLToPath(
  new URL("../scripts/validate-node-version.mjs", import.meta.url),
);

function run(version) {
  return spawnSync(process.execPath, [gate], {
    encoding: "utf8",
    env: {
      ...process.env,
      PRINTORA_NODE_GATE_TEST: "1",
      PRINTORA_NODE_VERSION_OVERRIDE: version,
    },
  });
}

assert.equal(run("18.20.8").status, 1);
assert.equal(run("20.20.0").status, 1);
assert.equal(run("22.21.9").status, 1);
assert.equal(run("22.22.0").status, 0);
assert.equal(run("22.22.9").status, 0);
assert.equal(run("22.23.0").status, 1);
assert.equal(run("23.0.0").status, 1);

console.log("node version gate tests passed");
