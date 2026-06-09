import { createRoot } from "react-dom/client";
import { useState } from "react";
import { Bell, ChevronDown, Info, LogOut, Menu, UserRound, Users, X } from "lucide-react";
import { appSections } from "./app/navigation";
import type { AppSection } from "./app/navigation";
import { AppModals } from "./components/modals";
import { ToastViewport } from "./components/ToastViewport";
import { OverviewScreen } from "./screens/OverviewScreen";
import { PrintersScreen } from "./screens/PrintersScreen";
import { AgentsScreen } from "./screens/AgentsScreen";
import { AgentDetailScreen } from "./screens/AgentDetailScreen";
import { SetupScreen } from "./screens/SetupScreen";
import { PrinterDetailScreen } from "./screens/PrinterDetailScreen";
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

type AccountTab = "profile" | "organizations";

function openAccountTab(tab: AccountTab, setActiveSection: (section: AppSection) => void) {
  (window as Window & { printoraAccountTab?: AccountTab }).printoraAccountTab = tab;
  setActiveSection("account");
  window.setTimeout(() => {
    window.dispatchEvent(new CustomEvent("printora:account-tab", { detail: tab }));
  }, 0);
}

function App() {
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const {
    ActiveIcon,
    ThemeIcon,
    activeSection,
    activeSectionMeta,
    alertCount,
    mobileNavOpen,
    screenProps,
    selectedPrinter,
    setActiveSection,
    setAlertCenterOpen,
    setMobileNavOpen,
    setTheme,
    theme,
    topbarAlertTone,
    toasts,
    dismissToast,
    visibleNavGroups,
  } = usePrintoraApp();
  const userLabel = screenProps.authUser?.display_name || screenProps.authUser?.email || "Conta";
  const accountMenuItems = [
    { label: "Organizações", icon: Users, tab: "organizations" as const },
    { label: "Perfil", icon: UserRound, tab: "profile" as const },
  ];

  const activeScreen = (() => {
    switch (activeSection) {
      case "overview":
        return <OverviewScreen {...screenProps} />;
      case "printers":
        return <PrintersScreen {...screenProps} />;
      case "printer-detail":
        return <PrinterDetailScreen {...screenProps} />;
      case "agents":
        return <AgentsScreen {...screenProps} />;
      case "agent-detail":
        return <AgentDetailScreen {...screenProps} />;
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
          <span>Contexto rápido</span>
          <strong>{selectedPrinter?.name ?? "nenhuma impressora"}</strong>
          <small>{selectedPrinter?.moonraker_url ?? "Abra uma impressora pela lista."}</small>
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
              className={`icon-button topbar-alert ${topbarAlertTone}`}
              title="Alertas da frota"
              aria-label={alertCount > 0 ? `${alertCount} alerta(s) da frota` : "Sem alertas da frota"}
              onClick={() => setAlertCenterOpen(true)}
            >
              <Bell size={16} />
              {alertCount > 0 ? <strong>{alertCount}</strong> : null}
            </button>
            <button
              type="button"
              className={`icon-button topbar-info ${activeSection === "about" || activeSection === "license" ? "active" : ""}`}
              title="Sobre o Printora"
              aria-label="Sobre o Printora"
              onClick={() => setActiveSection("about")}
            >
              <Info size={17} />
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
                          openAccountTab(item.tab, setActiveSection);
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
          </div>
        </header>

        <section className="page-helper">
          <strong>{activeSectionMeta.purpose}</strong>
          <span>
            {activeSection === "settings"
              ? "Configuração global do Printora"
              : activeSection === "printer-detail"
                ? selectedPrinter
                  ? `Registro aberto: ${selectedPrinter.name}`
                  : "Abra uma impressora pela lista"
              : activeSection === "agent-detail"
                ? "Registro do agente selecionado"
              : activeSection === "account"
                ? "Identidade, segurança e organizações"
              : activeSection === "setup"
                ? "Provisionamento começa somente depois que Linux e SSH estão ativos"
              : activeSection === "overview"
                ? "Resumo global da frota"
              : activeSection === "printers"
                ? "Lista de impressoras e acesso ao detalhe"
              : activeSection === "agents"
                ? "Lista global de agentes da frota"
              : activeSection === "reports"
                ? "Relatórios globais; diagnóstico de impressora fica no detalhe"
              : activeSection === "about"
                ? "Autoria, roadmap público e identidade do projeto"
                : activeSection === "license"
                  ? "Uso open source com limites de responsabilidade"
              : selectedPrinter
                ? `Contexto atual: ${selectedPrinter.name}`
                : "Selecione uma impressora para carregar os dados por contexto."}
          </span>
        </section>
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
