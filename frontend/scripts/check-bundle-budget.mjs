import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { gzipSync } from "node:zlib";
import { fileURLToPath } from "node:url";

export function validateBundle(files, budget) {
  const errors = [];
  let totalBytes = 0;
  let totalGzipBytes = 0;

  for (const file of files) {
    totalBytes += file.bytes;
    totalGzipBytes += file.gzipBytes;
    if (file.bytes > budget.maxAssetBytes) {
      errors.push(`${file.name}: ${file.bytes} > ${budget.maxAssetBytes} bytes`);
    }
    if (/^index-[^.]+\.js$/.test(file.name) && file.bytes > budget.maxEntryBytes) {
      errors.push(`${file.name}: entrada ${file.bytes} > ${budget.maxEntryBytes} bytes`);
    }
    if (file.name.endsWith(".css") && file.bytes > budget.maxStylesheetBytes) {
      errors.push(
        `${file.name}: stylesheet ${file.bytes} > ${budget.maxStylesheetBytes} bytes`,
      );
    }
  }

  if (totalBytes > budget.maxTotalBytes) {
    errors.push(`total: ${totalBytes} > ${budget.maxTotalBytes} bytes`);
  }
  if (totalGzipBytes > budget.maxTotalGzipBytes) {
    errors.push(`total gzip: ${totalGzipBytes} > ${budget.maxTotalGzipBytes} bytes`);
  }
  return { errors, totalBytes, totalGzipBytes };
}

function readFiles(assetsDirectory) {
  return fs.readdirSync(assetsDirectory).map((name) => {
    const content = fs.readFileSync(path.join(assetsDirectory, name));
    return {
      name,
      bytes: content.length,
      gzipBytes: gzipSync(content).length,
    };
  });
}

function main() {
  const frontendDirectory = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
  );
  const budget = JSON.parse(
    fs.readFileSync(path.join(frontendDirectory, "bundle-budget.json"), "utf8"),
  );
  const result = validateBundle(
    readFiles(path.join(frontendDirectory, "dist", "assets")),
    budget,
  );
  if (result.errors.length > 0) {
    console.error(`Bundle fora do orçamento:\n- ${result.errors.join("\n- ")}`);
    process.exit(1);
  }
  console.log(
    `bundle budget passed: ${result.totalBytes} bytes, ` +
      `${result.totalGzipBytes} bytes gzip`,
  );
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  main();
}
