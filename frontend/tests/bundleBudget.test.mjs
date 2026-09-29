import assert from "node:assert/strict";
import { validateBundle } from "../scripts/check-bundle-budget.mjs";

const budget = {
  maxAssetBytes: 100,
  maxEntryBytes: 80,
  maxStylesheetBytes: 50,
  maxTotalBytes: 150,
  maxTotalGzipBytes: 90,
};

assert.deepEqual(
  validateBundle(
    [
      { name: "index-ok.js", bytes: 70, gzipBytes: 30 },
      { name: "index-ok.css", bytes: 40, gzipBytes: 20 },
    ],
    budget,
  ).errors,
  [],
);

const failures = validateBundle(
  [
    { name: "index-big.js", bytes: 101, gzipBytes: 60 },
    { name: "index-big.css", bytes: 60, gzipBytes: 40 },
  ],
  budget,
).errors;

assert.equal(failures.length, 5);
assert.ok(failures.some((failure) => failure.includes("entrada")));
assert.ok(failures.some((failure) => failure.includes("stylesheet")));
assert.ok(failures.some((failure) => failure.startsWith("total gzip")));

console.log("bundle budget tests passed");
