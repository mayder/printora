import type { CalibrationExecutionRecord, CalibrationResultFormConfig, CalibrationRunRecord, CalibrationSequencePlan, CalibrationTestRecord } from "../../types";

export function formatCalibrationCategory(category: string) {
  const labels: Record<string, string> = {
    extrusao_base: "extrusão base",
    validacao_mecanica: "validação mecânica",
    nivelamento: "nivelamento",
    probe: "probe",
    primeira_camada: "primeira camada",
    material: "material",
    extrusao: "extrusão",
    movimento: "movimento",
    qualidade: "qualidade",
    temperatura: "temperatura",
    perifericos: "periféricos",
    dimensional: "dimensional",
  };
  return labels[category] ?? category;
}

export function formatExecutionMode(mode: CalibrationTestRecord["execution_mode"]) {
  const labels: Record<CalibrationTestRecord["execution_mode"], string> = {
    read_only: "somente leitura",
    manual: "manual",
    gcode_review_required: "G-code exige revisão",
    blocked_while_printing: "bloqueado imprimindo",
  };
  return labels[mode];
}

export function formatRiskLevel(riskLevel: CalibrationTestRecord["risk_level"]) {
  const labels: Record<CalibrationTestRecord["risk_level"], string> = {
    low: "baixo",
    medium: "médio",
    high: "alto",
  };
  return labels[riskLevel];
}

export function formatCalibrationResult(resultStatus: CalibrationRunRecord["result_status"]) {
  const labels: Record<CalibrationRunRecord["result_status"], string> = {
    passed: "aprovado",
    warning: "atenção",
    failed: "falhou",
    skipped: "ignorado",
  };
  return labels[resultStatus];
}

export function formatCalibrationExecutionStatus(status: string) {
  const labels: Record<string, string> = {
    executed: "executado",
    dispatched_unconfirmed: "despachado sem confirmação",
    blocked: "bloqueado",
    failed: "falhou",
    failed_partial: "falhou parcialmente",
  };
  return labels[status] ?? status;
}

export function calibrationExecutionRowClass(status: string) {
  if (status === "executed") {
    return "passed";
  }
  if (status === "dispatched_unconfirmed") {
    return "warning";
  }
  if (status === "failed" || status === "failed_partial") {
    return "failed";
  }
  return "warning";
}

export function summarizeCalibrationExecutionFinalState(execution: CalibrationExecutionRecord) {
  const finalState = latestCalibrationExecutionFinalState(execution);
  if (!finalState) {
    return `${execution.sent_commands.length}/${execution.commands.length} comando(s) confirmado(s)`;
  }
  const klipper = typeof finalState.klipper_state === "string" ? finalState.klipper_state : "-";
  const klippy = typeof finalState.klippy_state === "string" ? finalState.klippy_state : "-";
  const printState = typeof finalState.print_state === "string" && finalState.print_state ? finalState.print_state : "-";
  const homedAxes = typeof finalState.homed_axes === "string" && finalState.homed_axes ? ` · homed ${finalState.homed_axes}` : "";
  return `Final: Klipper ${klipper} · Klippy ${klippy} · print ${printState}${homedAxes}`;
}

export function formatCalibrationExecutionResult(execution: CalibrationExecutionRecord) {
  return JSON.stringify(execution.result, null, 2);
}

export function buildCalibrationExecutionNotes(execution: CalibrationExecutionRecord) {
  const commandText = execution.sent_commands.length ? execution.sent_commands.join(", ") : "-";
  const consoleExcerpt = calibrationExecutionConsoleExcerpt(execution);
  const saveConfigNote = calibrationExecutionRequiresSaveConfig(execution)
    ? "Atenção: o Klipper pediu SAVE_CONFIG. Os valores só entram no printer.cfg depois de salvar a configuração; isso reinicia o firmware."
    : "";
  return [
    execution.message,
    summarizeCalibrationExecutionFinalState(execution),
    `Comandos confirmados: ${commandText}`,
    saveConfigNote,
    consoleExcerpt.length ? "Console Moonraker:" : "",
    consoleExcerpt.length ? consoleExcerpt.join("\n") : "",
    "Retorno final Moonraker:",
    formatCalibrationExecutionResult(execution),
  ].filter(Boolean).join("\n");
}

export function calibrationExecutionConsoleExcerpt(execution: CalibrationExecutionRecord) {
  const consoleRecord = calibrationExecutionConsoleRecord(execution);
  const excerpt = consoleRecord?.console_excerpt;
  if (!Array.isArray(excerpt)) {
    return [];
  }
  return excerpt.map((item) => String(item).trim()).filter(Boolean);
}

export function calibrationExecutionRequiresSaveConfig(execution: CalibrationExecutionRecord) {
  const consoleRecord = calibrationExecutionConsoleRecord(execution);
  if (consoleRecord?.save_config_required === true) {
    return true;
  }
  return calibrationExecutionConsoleExcerpt(execution).join("\n").toUpperCase().includes("SAVE_CONFIG");
}

export function calibrationExecutionPidParameters(execution: CalibrationExecutionRecord) {
  const params = calibrationExecutionConsoleRecord(execution)?.pid_parameters;
  if (!params || typeof params !== "object" || Array.isArray(params)) {
    return null;
  }
  const mapped = params as Record<string, unknown>;
  const kp = Number(mapped.pid_Kp);
  const ki = Number(mapped.pid_Ki);
  const kd = Number(mapped.pid_Kd);
  if (![kp, ki, kd].every(Number.isFinite)) {
    return null;
  }
  return { kp, ki, kd };
}

export function latestCalibrationExecutionFinalState(execution: CalibrationExecutionRecord) {
  for (let index = execution.result.length - 1; index >= 0; index -= 1) {
    const item = execution.result[index];
    const finalState = item.final_state;
    if (finalState && typeof finalState === "object" && !Array.isArray(finalState)) {
      return finalState as Record<string, unknown>;
    }
  }
  return null;
}

function calibrationExecutionConsoleRecord(execution: CalibrationExecutionRecord) {
  return execution.result.find((item) => item.kind === "moonraker_console") ?? null;
}

export function formatCalibrationTestTitle(testKey: string, tests: CalibrationTestRecord[]) {
  return tests.find((test) => test.test_key === testKey)?.title ?? testKey;
}

export function formatCalibrationSequenceStatus(status: CalibrationSequencePlan["steps"][number]["status"]) {
  if (status === "completed") {
    return "concluído";
  }
  if (status === "skipped") {
    return "pulado";
  }
  return "pendente";
}

export function groupCalibrationSteps(steps: CalibrationSequencePlan["steps"]) {
  const groups = new Map<string, CalibrationSequencePlan["steps"]>();
  steps.forEach((step) => {
    const current = groups.get(step.phase) ?? [];
    current.push(step);
    groups.set(step.phase, current);
  });
  return Array.from(groups.entries()).map(([phase, phaseSteps]) => ({
    phase,
    steps: phaseSteps,
    completed: phaseSteps.filter((step) => step.status === "completed").length,
  }));
}

export function formatCalibrationPhase(phase: string) {
  const labels: Record<string, string> = {
    "01_base_mecanica": "1. Base mecânica",
    "02_temperatura": "2. Temperatura",
    "03_extrusao_base": "3. Extrusão base",
    "04_probe_mesa": "4. Probe e mesa",
    "05_primeira_camada": "5. Primeira camada",
    "06_material": "6. Material e fluxo",
    "07_movimento": "7. Movimento e vibração",
    "08_acabamento": "8. Acabamento",
    "09_dimensional": "9. Dimensional",
    "10_perifericos": "10. Periféricos",
  };
  return labels[phase] ?? phase.replace(/^[0-9]+_/, "").replaceAll("_", " ");
}

export function getCalibrationResultFormConfig(test: CalibrationTestRecord): CalibrationResultFormConfig {
  const base: CalibrationResultFormConfig = {
    summary: "Registre o que foi verificado neste item. O histórico serve para liberar a próxima revisão com evidência local.",
    observedLabel: "Resultado objetivo",
    observedPlaceholder: "Ex.: aprovado sem folgas, range 0.012 mm, temperatura estável",
    notesLabel: "Evidência e observações",
    notesPlaceholder: "O que foi visto, corrigido, medido ou precisa ser revisado depois",
    showMaterial: false,
    showPlate: false,
    showNozzle: false,
  };
  if (test.test_key === "mechanical_preflight" || test.category === "validacao_mecanica") {
    return {
      ...base,
      summary: "Use este registro para confirmar a inspeção física antes de ajustes por software.",
      observedLabel: "Resumo da inspeção",
      observedPlaceholder: "Ex.: correias firmes, toolhead sem folga, cabos livres",
      notesLabel: "Problemas encontrados ou correções feitas",
      notesPlaceholder: "Ex.: reapertado parafuso X, cabo do toolhead reposicionado, sem ação necessária",
    };
  }
  if (test.category === "temperatura") {
    return {
      ...base,
      observedLabel: "Temperatura e estabilidade",
      observedPlaceholder: "Ex.: 220 °C estável, overshoot baixo, mesa estabilizou em 60 °C",
      notesLabel: "Condição do teste",
      notesPlaceholder: "Material usado, tempo de estabilização, oscilação observada ou erro do Klipper",
      showMaterial: true,
    };
  }
  if (test.category === "primeira_camada") {
    return {
      ...base,
      summary: "Este resultado deve refletir o teste real de primeira camada. Use o perfil aprovado abaixo só quando este teste estiver bom.",
      observedLabel: "Z-offset/resultado visual",
      observedPlaceholder: "Ex.: -0.295, linhas aderidas sem raspar",
      notesLabel: "Aderência e aparência",
      notesPlaceholder: "Uniformidade, cantos, excesso de esmagamento, limpeza da mesa e ajuste usado",
      showMaterial: true,
      showPlate: true,
      showNozzle: true,
    };
  }
  if (test.category === "material" || test.category === "extrusao" || test.category === "extrusao_base") {
    return {
      ...base,
      observedLabel: "Valor medido ou escolhido",
      observedPlaceholder: "Ex.: flow 0.96, PA 0.035, 18 mm3/s, extrusão real 49.6 mm",
      notesLabel: "Material, perfil e evidência",
      notesPlaceholder: "Marca/cor do filamento, perfil do slicer, peça usada, falhas ou aprovação visual",
      showMaterial: true,
      showPlate: test.category === "material",
      showNozzle: true,
    };
  }
  if (test.category === "probe" || test.category === "nivelamento") {
    return {
      ...base,
      observedLabel: "Medição ou conclusão",
      observedPlaceholder: "Ex.: probe repetível, QGL dentro da tolerância, offset XY conferido",
      notesLabel: "Condição da mesa/probe",
      notesPlaceholder: "Estado da chapa, bico limpo, range, retries, ajuste manual ou bloqueio encontrado",
      showPlate: true,
      showNozzle: true,
    };
  }
  if (test.category === "movimento" || test.category === "qualidade" || test.category === "dimensional") {
    return {
      ...base,
      observedLabel: "Medição ou artefato observado",
      observedPlaceholder: "Ex.: sem ringing visível, X 20.02 mm, sem layer shift",
      notesLabel: "Peça de teste e interpretação",
      notesPlaceholder: "Velocidade, aceleração, medidas, foto/referência e próximos ajustes",
      showMaterial: true,
      showNozzle: true,
    };
  }
  return base;
}
