import { createRoot } from "react-dom/client";
import { useEffect, useState } from "react";
import { Bell, ChevronDown, Info, LogOut, Menu, UserRound, Users, X } from "lucide-react";
import { appSections } from "./app/navigation";
import type { AppSection } from "./app/navigation";
import { AppModals } from "./components/modals";
import { ToastViewport } from "./components/ToastViewport";
import { OverviewScreen } from "./screens/OverviewScreen";
import { PrintersScreen } from "./screens/PrintersScreen";
import { AgentsScreen } from "./screens/AgentsScreen";
import { AgentDetailScreen } from "./screens/AgentDetailScreen";
import { PrintProjectsScreen } from "./screens/PrintProjectsScreen";
import { SocialScreen } from "./screens/SocialScreen";
import { CatalogAdminScreen } from "./screens/CatalogAdminScreen";
import { SetupScreen } from "./screens/SetupScreen";
import { PrinterDetailScreen } from "./screens/PrinterDetailScreen";
import { MonitoringScreen } from "./screens/MonitoringScreen";
import { UpdatesScreen } from "./screens/UpdatesScreen";
import { TestsScreen } from "./screens/TestsScreen";
import { FirmwareScreen } from "./screens/FirmwareScreen";
import { MaintenanceScreen } from "./screens/MaintenanceScreen";
import { ReportsScreen } from "./screens/ReportsScreen";
import { SettingsScreen } from "./screens/SettingsScreen";
import { FinanceAdminScreen } from "./screens/FinanceAdminScreen";
import { ManufacturingAdminScreen } from "./screens/ManufacturingAdminScreen";
import { DataIntelligenceScreen } from "./screens/DataIntelligenceScreen";
import { AuthScreen } from "./screens/AuthScreen";
import { AboutScreen } from "./screens/AboutScreen";
import { LicenseScreen } from "./screens/LicenseScreen";
import { PublicProfileScreen } from "./screens/PublicProfileScreen";
import { PublicPrinterScreen } from "./screens/PublicPrinterScreen";
import { PublicCommunityScreen } from "./screens/PublicCommunityScreen";
import { usePrintoraApp } from "./hooks/usePrintoraApp";
import "./styles.css";
import "./styles/overview.css";
import "./styles/monitoring.css";
import "./styles/gcode-files.css";
import "./styles/operation.css";
import "./styles/printers.css";
import "./styles/modals.css";
import "./styles/backups.css";
import "./styles/maintenance.css";
import "./styles/settings.css";
import "./styles/finance.css";
import "./styles/manufacturing.css";
import "./styles/auth.css";
import "./styles/setup.css";
import "./styles/firmware.css";
import "./styles/calibration.css";
import "./styles/tests.css";
import "./styles/reports.css";
import "./styles/about.css";
import "./styles/print-projects.css";
import "./styles/social.css";
import "./styles/catalog-admin.css";
import "./styles/data-intelligence.css";
import { readDocumentTheme } from "./services/localPreferences";

type AccountTab = "profile" | "organizations";

function openAccountTab(tab: AccountTab, setActiveSection: (section: AppSection) => void) {
  (window as Window & { printoraAccountTab?: AccountTab }).printoraAccountTab = tab;
  setActiveSection("account");
  window.setTimeout(() => {
    window.dispatchEvent(new CustomEvent("printora:account-tab", { detail: tab }));
  }, 0);
}

function useStoredDocumentTheme() {
  useEffect(() => {
    document.documentElement.dataset.theme = readDocumentTheme();
  }, []);
}

function App() {
  useStoredDocumentTheme();
  const publicProfileSlug = readPublicProfilePathSlug();
  const embeddedProfileSlug = readEmbeddedProfileSlug();
  const publicPrinterId = readPublicPrinterId();
  const publicCommunitySlug = readPublicCommunitySlug();
  if (publicProfileSlug) {
    return <PublicProfileScreen slug={publicProfileSlug} />;
  }
  if (publicPrinterId) {
    return <PublicPrinterScreen printerId={publicPrinterId} />;
  }

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
  useEffect(() => {
    if (publicCommunitySlug || embeddedProfileSlug) {
      setActiveSection("social");
    }
  }, [publicCommunitySlug, embeddedProfileSlug, setActiveSection]);
  const userLabel = screenProps.authUser?.display_name || screenProps.authUser?.email || "Conta";
  const accountMenuItems = [
    { label: "Organizações", icon: Users, tab: "organizations" as const },
    { label: "Perfil", icon: UserRound, tab: "profile" as const },
  ];
  const shellSection = publicCommunitySlug || embeddedProfileSlug ? "social" : activeSection;
  const shellSectionMeta = appSections.find((section) => section.key === shellSection) ?? activeSectionMeta;
  const ShellIcon = publicCommunitySlug || embeddedProfileSlug ? Users : ActiveIcon;

  const activeScreen = (() => {
    if (publicCommunitySlug) {
      return <PublicCommunityScreen slug={publicCommunitySlug} embedded />;
    }
    if (embeddedProfileSlug) {
      return <PublicProfileScreen slug={embeddedProfileSlug} embedded />;
    }
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
      case "projects":
        return <PrintProjectsScreen {...screenProps} />;
      case "social":
        return <SocialScreen {...screenProps} />;
      case "catalog":
        return <CatalogAdminScreen {...screenProps} />;
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
      case "finance":
        return <FinanceAdminScreen {...screenProps} />;
      case "manufacturing":
        return <ManufacturingAdminScreen {...screenProps} />;
      case "data-intelligence":
        return <DataIntelligenceScreen {...screenProps} />;
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

  if (!screenProps.authUser && !screenProps.authReady) {
    return (
      <main className="auth-only-shell">
        <section className="auth-card" aria-label="Validando sessão">
          <span className="auth-eyebrow">Sessão</span>
          <h2>Validando acesso</h2>
          <p>Carregando sua sessão do Printora.</p>
        </section>
        <ToastViewport toasts={toasts} dismissToast={dismissToast} />
      </main>
    );
  }

  if (!screenProps.authUser) {
    if (publicCommunitySlug) {
      return <PublicCommunityScreen slug={publicCommunitySlug} />;
    }
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
                    className={`nav-button ${shellSection === section.key ? "active" : ""}`}
                    onClick={() => {
                      setActiveSection(section.key);
                      if (publicCommunitySlug || embeddedProfileSlug) {
                        window.history.pushState(null, "", `/?section=${section.key}`);
                      }
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
          <small>{selectedPrinter ? "Impressora selecionada" : "Abra uma impressora pela lista."}</small>
        </div>
      </aside>
      {mobileNavOpen ? <button type="button" className="sidebar-backdrop" onClick={() => setMobileNavOpen(false)} aria-label="Fechar menu" /> : null}

      <div className={`workspace section-${shellSection}`}>
        <header className="topbar">
          <div className="topbar-title">
            <button type="button" className="icon-button mobile-menu-button" onClick={() => setMobileNavOpen(true)} aria-label="Abrir menu">
              <Menu size={18} />
            </button>
            <span className="section-icon">
              <ShellIcon size={18} strokeWidth={2.2} />
            </span>
            <div>
              <h1>{shellSectionMeta.label}</h1>
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
              className={`icon-button topbar-info ${shellSection === "about" || shellSection === "license" ? "active" : ""}`}
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
          <strong>{shellSectionMeta.purpose}</strong>
          <span>
            {publicCommunitySlug
              ? "Comunidade pública com conteúdo técnico e dados autorizados"
              : embeddedProfileSlug
                ? "Perfil público com ações sociais e dados autorizados"
              : shellSection === "settings"
              ? "Configuração global do Printora"
              : shellSection === "printer-detail"
                ? selectedPrinter
                  ? `Registro aberto: ${selectedPrinter.name}`
                  : "Abra uma impressora pela lista"
              : shellSection === "agent-detail"
                ? "Registro do agente selecionado"
              : shellSection === "account"
                ? "Identidade, segurança e organizações"
              : shellSection === "setup"
                ? "Provisionamento começa somente depois que Linux e SSH estão ativos"
              : shellSection === "overview"
                ? "Resumo global da frota"
              : shellSection === "printers"
                ? "Lista de impressoras e acesso ao detalhe"
              : shellSection === "agents"
                ? "Lista global de agentes da frota"
              : shellSection === "social"
                ? "Descoberta pública e comunidade"
              : shellSection === "reports"
                ? "Relatórios globais; diagnóstico de impressora fica no detalhe"
              : shellSection === "about"
                ? "Autoria, roadmap público e identidade do projeto"
                : shellSection === "license"
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

function readPublicProfilePathSlug() {
  const pathMatch = window.location.pathname.match(/^\/u\/([a-z0-9-]+)\/?$/i);
  if (pathMatch) {
    return pathMatch[1];
  }
  return null;
}

function readEmbeddedProfileSlug() {
  const params = new URLSearchParams(window.location.search);
  return params.get("profile") || params.get("u");
}

function readPublicPrinterId() {
  const pathMatch = window.location.pathname.match(/^\/p\/([0-9]+)\/?$/i);
  if (pathMatch) {
    return pathMatch[1];
  }
  const params = new URLSearchParams(window.location.search);
  return params.get("printer");
}

function readPublicCommunitySlug() {
  const pathMatch = window.location.pathname.match(/^\/c\/([a-z0-9-]+)\/?$/i);
  if (pathMatch) {
    return pathMatch[1];
  }
  const params = new URLSearchParams(window.location.search);
  return params.get("community") || params.get("c");
}


createRoot(document.getElementById("root")!).render(<App />);
