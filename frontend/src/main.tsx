import { createRoot } from "react-dom/client";
import { useState } from "react";
import { Bell, ChevronDown, Info, LogOut, Menu, ShieldCheck, UserRound, Users, X } from "lucide-react";
import { appSections } from "./app/navigation";
import { AppModals } from "./components/modals";
import { ToastViewport } from "./components/ToastViewport";
import { OverviewScreen } from "./screens/OverviewScreen";
import { PrintersScreen } from "./screens/PrintersScreen";
import { AgentsScreen } from "./screens/AgentsScreen";
import { SetupScreen } from "./screens/SetupScreen";
import { MonitoringScreen } from "./screens/MonitoringScreen";
import { UpdatesScreen } from "./screens/UpdatesScreen";
import { TestsScreen } from "./screens/TestsScreen";
import { FirmwareScreen } from "./screens/FirmwareScreen";
import { MaintenanceScreen } from "./screens/MaintenanceScreen";
import { ReportsScreen } from "./screens/ReportsScreen";
import { SettingsScreen } from "./screens/SettingsScreen";
import { AuthScreen } from "./screens/AuthScreen";
import { AboutScreen } from "./screens/AboutScreen";
import { LicenseScreen } from "./screens/LicenseScreen";
import { usePrintoraApp } from "./hooks/usePrintoraApp";
import "./styles.css";
import "./styles/overview.css";
import "./styles/monitoring.css";
import "./styles/operation.css";
import "./styles/printers.css";
import "./styles/modals.css";
import "./styles/backups.css";
import "./styles/maintenance.css";
import "./styles/settings.css";
import "./styles/auth.css";
import "./styles/setup.css";
import "./styles/firmware.css";
import "./styles/calibration.css";
import "./styles/tests.css";
import "./styles/reports.css";
import "./styles/about.css";

function App() {
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
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
    toasts,
    dismissToast,
    visibleNavGroups,
  } = usePrintoraApp();
  const userLabel = screenProps.authUser?.display_name || screenProps.authUser?.email || "Conta";
  const accountMenuItems = [
    { label: "Acessos da conta", icon: UserRound, tab: "access" },
    { label: "Segurança", icon: ShieldCheck, tab: "security" },
    { label: "Organizações", icon: Users, tab: "organizations" },
  ];

  const activeScreen = (() => {
    switch (activeSection) {
      case "overview":
        return <OverviewScreen {...screenProps} />;
      case "printers":
        return <PrintersScreen {...screenProps} />;
      case "agents":
        return <AgentsScreen {...screenProps} />;
      case "setup":
        return <SetupScreen {...screenProps} />;
      case "monitoring":
        return <MonitoringScreen {...screenProps} />;
      case "updates":
        return <UpdatesScreen {...screenProps} />;
      case "tests":
        return <TestsScreen {...screenProps} />;
      case "firmware":
        return <FirmwareScreen {...screenProps} />;
      case "maintenance":
        return <MaintenanceScreen {...screenProps} />;
      case "reports":
        return <ReportsScreen {...screenProps} />;
      case "settings":
        return <SettingsScreen {...screenProps} />;
      case "account":
        return <AuthScreen {...screenProps} />;
      case "about":
        return <AboutScreen {...screenProps} />;
      case "license":
        return <LicenseScreen {...screenProps} />;
      default:
        return <OverviewScreen {...screenProps} />;
    }
  })();

  if (!screenProps.authUser) {
    return (
      <main className="auth-only-shell">
        {error ? <section className="alert danger">{error}</section> : null}
        <AuthScreen {...screenProps} />
        <ToastViewport toasts={toasts} dismissToast={dismissToast} />
      </main>
    );
  }

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
            <button
              type="button"
              className={`icon-button topbar-info ${activeSection === "about" || activeSection === "license" ? "active" : ""}`}
              title="Sobre o Printora"
              aria-label="Sobre o Printora"
              onClick={() => setActiveSection("about")}
            >
              <Info size={17} />
            </button>
            <div className="topbar-account">
              <button
                type="button"
                className={`account-menu-button ${accountMenuOpen ? "active" : ""}`}
                aria-expanded={accountMenuOpen}
                aria-haspopup="menu"
                onClick={() => setAccountMenuOpen((current) => !current)}
              >
                <span className="account-avatar">
                  <UserRound size={16} />
                </span>
                <span className="account-menu-label">
                  <strong>{userLabel}</strong>
                  <small>{screenProps.authUser?.mfa_enabled ? "2FA ativo" : "2FA inativo"}</small>
                </span>
                <ChevronDown size={15} />
              </button>
              {accountMenuOpen ? (
                <div className="account-dropdown" role="menu">
                  {accountMenuItems.map((item) => {
                    const ItemIcon = item.icon;
                    return (
                      <button
                        key={item.label}
                        type="button"
                        role="menuitem"
                        onClick={() => {
                          setActiveSection("account");
                          window.dispatchEvent(new CustomEvent("printora:account-tab", { detail: item.tab }));
                          setAccountMenuOpen(false);
                        }}
                      >
                        <ItemIcon size={16} />
                        <span>{item.label}</span>
                      </button>
                    );
                  })}
                  <button
                    type="button"
                    role="menuitem"
                    className="danger"
                    onClick={() => {
                      setAccountMenuOpen(false);
                      void screenProps.logoutAuth();
                    }}
                  >
                    <LogOut size={16} />
                    <span>Sair</span>
                  </button>
                </div>
              ) : null}
            </div>
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
            {activeSection !== "account" ? (
              <button
                type="button"
                className="icon-button topbar-primary"
                title={topbarPrimaryAction.label}
                aria-label={topbarPrimaryAction.label}
                onClick={() => void topbarPrimaryAction.run()}
                disabled={topbarPrimaryAction.disabled}
              >
                <TopbarPrimaryIcon className={topbarPrimaryAction.busy ? "button-busy-icon" : undefined} size={16} />
              </button>
            ) : null}
          </div>
        </header>

        <section className="page-helper">
          <strong>{activeSectionMeta.purpose}</strong>
          <span>
            {activeSection === "settings"
              ? "Configuração global do Printora"
              : activeSection === "account"
                ? "Identidade, segurança e organizações"
              : activeSection === "setup"
                ? "Provisionamento começa somente depois que Linux e SSH estão ativos"
              : activeSection === "about"
                ? "Autoria, roadmap público e identidade do projeto"
                : activeSection === "license"
                  ? "Uso open source com limites de responsabilidade"
              : selectedPrinter
                ? `Contexto atual: ${selectedPrinter.name}`
                : "Selecione uma impressora para carregar os dados por contexto."}
          </span>
        </section>
        {activeSection !== "account" ? (
          <button type="button" className="primary-button mobile-section-action" onClick={() => void topbarPrimaryAction.run()} disabled={topbarPrimaryAction.disabled}>
            <TopbarPrimaryIcon size={16} />
            {topbarPrimaryAction.label}
          </button>
        ) : null}

        {error ? <section className="alert danger">{error}</section> : null}

        <AppModals {...screenProps} />
        <ToastViewport toasts={toasts} dismissToast={dismissToast} />

        <section className="grid">
          {activeScreen}
        </section>
      </div>
    </main>
  );
}


createRoot(document.getElementById("root")!).render(<App />);
