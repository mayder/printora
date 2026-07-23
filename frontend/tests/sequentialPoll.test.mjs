import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, "..");
const source = await readFile(join(root, "src/utils/sequentialPoll.ts"), "utf8");
const transpiled = ts.transpileModule(source, {
  compilerOptions: {
    target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ES2022,
  },
});
const moduleUrl = `data:text/javascript;base64,${Buffer.from(transpiled.outputText).toString("base64")}`;
const { startSequentialPoll } = await import(moduleUrl);

let calls = 0;
let scheduled;
let resolveTask;
let canceled;
const task = () => {
  calls += 1;
  return new Promise((resolve) => {
    resolveTask = resolve;
  });
};
const schedule = (callback, delayMs) => {
  assert.equal(delayMs, 5000);
  scheduled = callback;
  return 7;
};
const cancel = (handle) => {
  canceled = handle;
};

const stop = startSequentialPoll(task, 5000, schedule, cancel);
await Promise.resolve();
assert.equal(calls, 1);
assert.equal(scheduled, undefined);

resolveTask();
await Promise.resolve();
await Promise.resolve();
assert.equal(typeof scheduled, "function");

const next = scheduled;
scheduled = undefined;
next();
await Promise.resolve();
assert.equal(calls, 2);
assert.equal(scheduled, undefined);

resolveTask();
await Promise.resolve();
await Promise.resolve();
assert.equal(typeof scheduled, "function");

stop();
assert.equal(canceled, 7);
console.log("Sequential polling tests passed.");
