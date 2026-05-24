import { createRoot } from "react-dom/client";
import { Bell, Menu, X } from "lucide-react";
import { appSections } from "./app/navigation";
import { AppModals } from "./components/modals";
import { OverviewScreen } from "./screens/OverviewScreen";
import { PrintersScreen } from "./screens/PrintersScreen";
import { OperationScreen } from "./screens/OperationScreen";
import { MonitoringScreen } from "./screens/MonitoringScreen";
import { UpdatesScreen } from "./screens/UpdatesScreen";
import { CalibrationScreen } from "./screens/CalibrationScreen";
import { TestsScreen } from "./screens/TestsScreen";
import { FirmwareScreen } from "./screens/FirmwareScreen";
import { MaintenanceScreen } from "./screens/MaintenanceScreen";
import { ReportsScreen } from "./screens/ReportsScreen";
import { SettingsScreen } from "./screens/SettingsScreen";
import { usePrintoraApp } from "./hooks/usePrintoraApp";
import "./styles.css";

function App() {
  const {
    ActiveIcon,
    ThemeIcon,
    TopbarPrimaryIcon,
    activeSection,
    activeSectionMeta,
    alertCount,
    error,
    mobileNavOpen,
    printers,
    screenProps,
    selectPrinter,
    selectedPrinter,
    selectedPrinterId,
    setActiveSection,
    setAlertCenterOpen,
    setMobileNavOpen,
    setTheme,
    theme,
    topbarAlertTone,
    topbarPrimaryAction,
    visibleNavGroups,
  } = usePrintoraApp();

  return (
    <main className="app-shell">
      <aside className={`sidebar ${mobileNavOpen ? "open" : ""}`} aria-label="Navegação principal">
        <div className="brand">
          <div className="brand-mark">
            <img src="/brand/printora-icon-app-color.png" alt="" />
          </div>
          <div>
            <strong>Printora</strong>
            <span>Klipper Ops</span>
          </div>
          <button type="button" className="icon-button sidebar-close" onClick={() => setMobileNavOpen(false)} aria-label="Fechar menu">
            <X size={18} />
          </button>
        </div>
        <nav className="sidebar-nav">
          {visibleNavGroups.map((group) => (
            <div key={group.title} className="nav-group">
              <span className="nav-group-title">{group.title}</span>
              {group.sections.map((sectionKey) => {
                const section = appSections.find((candidate) => candidate.key === sectionKey);
                if (!section) {
                  return null;
                }
                const Icon = section.icon;
                return (
                  <button
                    key={section.key}
                    type="button"
                    className={`nav-button ${activeSection === section.key ? "active" : ""}`}
                    onClick={() => {
                      setActiveSection(section.key);
                      setMobileNavOpen(false);
                    }}
                  >
                    <span className="nav-icon">
                      <Icon size={17} strokeWidth={2.2} />
                    </span>
                    <span>{section.label}</span>
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span>Impressora ativa</span>
          <strong>{selectedPrinter?.name ?? "não selecionada"}</strong>
          <small>{selectedPrinter?.moonraker_url ?? "Cadastre ou selecione uma impressora."}</small>
        </div>
      </aside>
      {mobileNavOpen ? <button type="button" className="sidebar-backdrop" onClick={() => setMobileNavOpen(false)} aria-label="Fechar menu" /> : null}

      <div className={`workspace section-${activeSection}`}>
        <header className="topbar">
          <div className="topbar-title">
            <button type="button" className="icon-button mobile-menu-button" onClick={() => setMobileNavOpen(true)} aria-label="Abrir menu">
              <Menu size={18} />
            </button>
            <span className="section-icon">
              <ActiveIcon size={18} strokeWidth={2.2} />
            </span>
            <div>
              <h1>{activeSectionMeta.label}</h1>
            </div>
          </div>
          <div className="topbar-actions">
            <label className="topbar-printer context-select" aria-label="Impressora ativa">
              <select
                value={selectedPrinterId ?? ""}
                onChange={(event) => selectPrinter(Number(event.target.value))}
              >
                <option value="" disabled>
                  Selecione uma impressora
                </option>
                {printers.map((printer) => (
                  <option key={printer.id} value={printer.id}>
                    {printer.name}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className={`icon-button topbar-alert ${topbarAlertTone}`}
              title="Alertas"
              aria-label={alertCount > 0 ? `${alertCount} alerta(s)` : "Sem alertas"}
              onClick={() => setAlertCenterOpen(true)}
            >
              <Bell size={16} />
              {alertCount > 0 ? <strong>{alertCount}</strong> : null}
            </button>
            <button
              type="button"
              className="icon-button"
              title={theme === "dark" ? "Usar tema claro" : "Usar tema escuro"}
              aria-label={theme === "dark" ? "Usar tema claro" : "Usar tema escuro"}
              onClick={() => setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"))}
            >
              <ThemeIcon size={18} />
            </button>
            <button
              type="button"
              className="icon-button topbar-primary"
              title={topbarPrimaryAction.label}
              aria-label={topbarPrimaryAction.label}
              onClick={() => void topbarPrimaryAction.run()}
              disabled={topbarPrimaryAction.disabled}
            >
              <TopbarPrimaryIcon size={16} />
            </button>
          </div>
        </header>

        <section className="page-helper">
          <strong>{activeSectionMeta.purpose}</strong>
          <span>
            {activeSection === "settings"
              ? "Configuração global do Printora"
              : selectedPrinter
                ? `Contexto atual: ${selectedPrinter.name}`
                : "Selecione uma impressora para carregar os dados por contexto."}
          </span>
        </section>
        <button type="button" className="primary-button mobile-section-action" onClick={() => void topbarPrimaryAction.run()} disabled={topbarPrimaryAction.disabled}>
          <TopbarPrimaryIcon size={16} />
          {topbarPrimaryAction.label}
        </button>

        {error ? <section className="alert danger">{error}</section> : null}

        <AppModals {...screenProps} />

        <section className="grid">
          <OverviewScreen {...screenProps} />
          <PrintersScreen {...screenProps} />
          <OperationScreen {...screenProps} />
          <MonitoringScreen {...screenProps} />
          <ReportsScreen {...screenProps} />
          <UpdatesScreen {...screenProps} />
          <SettingsScreen {...screenProps} />
          <FirmwareScreen {...screenProps} />
          <TestsScreen {...screenProps} />
          <CalibrationScreen {...screenProps} />
          <MaintenanceScreen {...screenProps} />
        </section>
      </div>
    </main>
  );
}


createRoot(document.getElementById("root")!).render(<App />);
