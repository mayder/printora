import type { PrinterRecord } from "../../types";

export function validatePrinterConnectionInput(moonrakerUrl: string, sshHost: string) {
  try {
    const parsedUrl = new URL(moonrakerUrl.trim());
    if (!["http:", "https:"].includes(parsedUrl.protocol)) {
      return "A URL do Moonraker precisa começar com http:// ou https://.";
    }
    if (parsedUrl.hostname.endsWith(".loca")) {
      return `Host Moonraker inválido: use ${parsedUrl.hostname}l ou um IP.`;
    }
  } catch {
    return "URL Moonraker inválida. Exemplo: http://voron.local:7125.";
  }

  const cleanSshHost = sshHost.trim();
  if (cleanSshHost.endsWith(".loca")) {
    return `Host SSH inválido: use ${cleanSshHost}l ou um IP.`;
  }
  return null;
}

export function extractHost(url: string) {
  try {
    return new URL(url).hostname;
  } catch {
    return "";
  }
}

export function formatSshStatus(printer: PrinterRecord) {
  if (!printer.ssh_host || !printer.ssh_username) {
    return "pendente";
  }
  return printer.ssh_credential_configured ? "configurado" : "sem credencial";
}
