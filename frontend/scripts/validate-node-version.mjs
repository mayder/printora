import process from "node:process";

const SUPPORTED_MAJOR = 22;
const MINIMUM_MINOR = 22;

export function parseNodeVersion(value) {
  const match = /^v?(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$/.exec(value.trim());
  if (!match) {
    throw new Error(`versão Node inválida: ${value}`);
  }
  return match.slice(1).map(Number);
}

export function isSupportedNodeVersion(value) {
  const [major, minor] = parseNodeVersion(value);
  return major === SUPPORTED_MAJOR && minor === MINIMUM_MINOR;
}

const version =
  process.env.PRINTORA_NODE_GATE_TEST === "1"
    ? process.env.PRINTORA_NODE_VERSION_OVERRIDE ?? ""
    : process.versions.node;

if (!isSupportedNodeVersion(version)) {
  console.error(
    `Node ${version || "desconhecido"} incompatível. ` +
      `Use Node ${SUPPORTED_MAJOR}.${MINIMUM_MINOR}.x conforme .node-version.`,
  );
  process.exit(1);
}
