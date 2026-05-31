import React from "react";
import type { ScreenPropsFor } from "./ScreenProps";

type AccountTab = "access" | "security" | "organizations";
const accountTabKeys: AccountTab[] = ["access", "security", "organizations"];

type AuthScreenProps = ScreenPropsFor<
  | "KeyRound"
  | "Plus"
  | "ShieldCheck"
  | "UserRound"
  | "authDisplayName"
  | "authEmail"
  | "authMfaChallengeToken"
  | "authMfaCode"
  | "authMode"
  | "authPassword"
  | "authUser"
  | "loading"
  | "memberEmail"
  | "memberRole"
  | "mfaSetup"
  | "organizationName"
  | "selectedOrganizationId"
  | "setAuthDisplayName"
  | "setAuthEmail"
  | "setAuthMfaCode"
  | "setAuthMode"
  | "setAuthPassword"
  | "setMemberEmail"
  | "setMemberRole"
  | "setOrganizationName"
  | "setSelectedOrganizationId"
  | "setStepUpCode"
  | "setStepUpPassword"
  | "stepUpCode"
  | "stepUpPassword"
  | "stepUpResult"
  | "addAuthOrganizationMember"
  | "confirmMfaSetup"
  | "createAuthOrganization"
  | "disableMfa"
  | "logoutAuth"
  | "requestStepUp"
  | "startMfaSetup"
  | "submitAuth"
  | "submitMfaLogin"
>;

export function AuthScreen(props: AuthScreenProps) {
  const {
    KeyRound,
    Plus,
    ShieldCheck,
    UserRound,
    authDisplayName,
    authEmail,
    authMfaChallengeToken,
    authMfaCode,
    authMode,
    authPassword,
    authUser,
    loading,
    memberEmail,
    memberRole,
    mfaSetup,
    organizationName,
    selectedOrganizationId,
    setAuthDisplayName,
    setAuthEmail,
    setAuthMfaCode,
    setAuthMode,
    setAuthPassword,
    setMemberEmail,
    setMemberRole,
    setOrganizationName,
    setSelectedOrganizationId,
    setStepUpCode,
    setStepUpPassword,
    stepUpCode,
    stepUpPassword,
    stepUpResult,
    addAuthOrganizationMember,
    confirmMfaSetup,
    createAuthOrganization,
    disableMfa,
    logoutAuth,
    requestStepUp,
    startMfaSetup,
    submitAuth,
    submitMfaLogin,
  } = props;
  const [accountTab, setAccountTab] = React.useState<AccountTab>(() => readRequestedAccountTab());
  const accountTabs: Array<{ key: AccountTab; label: string }> = [
    { key: "access", label: "Acessos" },
    { key: "security", label: "Segurança" },
    { key: "organizations", label: "Organizações" },
  ];
  React.useEffect(() => {
    function handleAccountTab(event: Event) {
      const tab = (event as CustomEvent<AccountTab>).detail;
      if (accountTabKeys.includes(tab)) {
        setAccountTab(tab);
      }
    }
    window.addEventListener("printora:account-tab", handleAccountTab);
    return () => window.removeEventListener("printora:account-tab", handleAccountTab);
  }, []);

  if (!authUser) {
    return (
      <section className="auth-entry">
        <aside className="auth-showcase" aria-label="Printora">
          <div className="auth-showcase-inner">
            <div className="auth-logo-panel">
              <img className="auth-showcase-logo" src="/brand/printora-logo-horizontal-color.png" alt="Printora" />
            </div>
            <div className="auth-showcase-copy">
              <span>Klipper Ops</span>
              <h1>Acesso seguro para operação remota.</h1>
              <p>Conta individual, organização opcional e agente pareado por token curto.</p>
            </div>
            <div className="auth-device-panel" aria-hidden="true">
              <div className="auth-device-top">
                <span />
                <span />
                <span />
              </div>
              <div className="auth-device-grid">
                <div>
                  <strong>Multi-modelo</strong>
                  <small>Klipper/Moonraker</small>
                </div>
                <div>
                  <strong>2FA</strong>
                  <small>opcional</small>
                </div>
                <div>
                  <strong>Jobs</strong>
                  <small>auditados</small>
                </div>
                <div>
                  <strong>Cloud</strong>
                  <small>isolado</small>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <article className="auth-card" aria-label={authMode === "login" ? "Entrar" : "Criar conta"}>
          <div className="auth-card-brand">
            <img src="/brand/printora-icon-app-color.png" alt="" />
          </div>
          <div className="auth-card-heading">
            <span>{authMode === "login" ? "Sessão" : "Cadastro"}</span>
            <h2>{authMode === "login" ? "Entrar no Printora" : "Criar conta"}</h2>
          </div>
          <div className="segmented-control auth-mode-tabs">
            <button type="button" className={authMode === "login" ? "active" : ""} onClick={() => setAuthMode("login")}>Login</button>
            <button type="button" className={authMode === "register" ? "active" : ""} onClick={() => setAuthMode("register")}>Cadastro</button>
          </div>
          <div className="auth-grid">
            <label>
              <span>Email</span>
              <input value={authEmail} onChange={(event) => setAuthEmail(event.target.value)} type="email" autoComplete="email" inputMode="email" pattern="^[^\\s@]+@[^\\s@]+\\.[^\\s@]{2,}$" placeholder="voce@empresa.com" />
            </label>
            <label>
              <span>Senha</span>
              <input value={authPassword} onChange={(event) => setAuthPassword(event.target.value)} type="password" autoComplete={authMode === "login" ? "current-password" : "new-password"} placeholder="Sua senha" />
            </label>
            {authMode === "register" ? (
              <>
                <label>
                  <span>Nome</span>
                  <input value={authDisplayName} onChange={(event) => setAuthDisplayName(event.target.value)} placeholder="Opcional" />
                </label>
              </>
            ) : null}
          </div>
          {authMfaChallengeToken ? (
            <div className="auth-step">
              <label>
                <span>Código 2FA</span>
                <input value={authMfaCode} onChange={(event) => setAuthMfaCode(event.target.value)} inputMode="numeric" placeholder="000000" />
              </label>
              <button type="button" className="primary-button" onClick={() => void submitMfaLogin()} disabled={loading || !authMfaCode.trim()}>
                <ShieldCheck size={16} />
                Validar
              </button>
            </div>
          ) : (
            <button type="button" className="primary-button auth-submit" onClick={() => void submitAuth()} disabled={loading || !authEmail.trim() || !authPassword.trim()}>
              <UserRound size={16} />
              {authMode === "login" ? "Entrar" : "Criar conta"}
            </button>
          )}
        </article>
      </section>
    );
  }

  return (
    <section className="account-workspace">
      <article className="panel wide account-hero">
        <div>
          <span className="account-eyebrow">Conta autenticada</span>
          <h2>{authUser.display_name || authUser.email}</h2>
          <p>{authUser.email}</p>
        </div>
        <div className="account-hero-actions">
          <button type="button" className="secondary-button" onClick={() => void logoutAuth()}>
            Sair
          </button>
        </div>
      </article>

      <div className="segmented-control account-tabs" role="tablist" aria-label="Áreas da conta">
        {accountTabs.map((tab) => (
          <button key={tab.key} type="button" className={accountTab === tab.key ? "active" : ""} onClick={() => setAccountTab(tab.key)}>
            {tab.label}
          </button>
        ))}
      </div>

      {accountTab === "access" ? (
        <div className="account-grid">
          <article className="panel auth-panel">
            <div className="panel-header-row">
              <div>
                <h2>Acessos da conta</h2>
                <p>O uso individual continua disponível; organizações entram só quando você quiser compartilhar impressoras.</p>
              </div>
              <UserRound size={20} />
            </div>
            <div className="auth-summary">
              <span>2FA: <strong>{authUser.mfa_enabled ? "ativo" : "inativo"}</strong></span>
              <span>Organizações: <strong>{authUser.organizations.length}</strong></span>
              <span>WhatsApp: <strong>{authUser.whatsapp || "não informado"}</strong></span>
              <span>Telegram: <strong>{authUser.telegram || "não informado"}</strong></span>
            </div>
          </article>
          <article className="panel auth-panel">
            <div className="panel-header-row">
              <div>
                <h2>Permissões disponíveis</h2>
                <p>Recursos liberados para esta conta no momento.</p>
              </div>
              <ShieldCheck size={20} />
            </div>
            <div className="auth-list">
              <div><strong>Conta individual</strong><span>ativa</span></div>
              <div><strong>Compartilhamento por organização</strong><span>{authUser.organizations.length ? "disponível" : "opcional"}</span></div>
              <div><strong>Ações críticas</strong><span>{authUser.mfa_enabled ? "2FA" : "senha"}</span></div>
              <div><strong>Agentes</strong><span>gerenciados na tela Agentes</span></div>
            </div>
          </article>
        </div>
      ) : null}

      {accountTab === "security" ? (
        <div className="account-grid">
          <article className="panel auth-panel">
            <div className="panel-header-row">
              <div>
                <h2>2FA</h2>
                <p>Opcional por usuário e usado como reforço em ações críticas.</p>
              </div>
              <ShieldCheck size={20} />
            </div>
            {mfaSetup ? (
              <div className="auth-stack">
                <code>{mfaSetup.secret}</code>
                <small>{mfaSetup.otpauth_uri}</small>
                <label>
                  <span>Código do app autenticador</span>
                  <input value={authMfaCode} onChange={(event) => setAuthMfaCode(event.target.value)} inputMode="numeric" />
                </label>
                <button type="button" className="primary-button" onClick={() => void confirmMfaSetup()} disabled={loading || !authMfaCode.trim()}>
                  Ativar 2FA
                </button>
              </div>
            ) : (
              <div className="auth-stack">
                <button type="button" className="primary-button" onClick={() => void startMfaSetup()} disabled={loading}>
                  Preparar 2FA
                </button>
                {authUser.mfa_enabled ? (
                  <>
                    <label>
                      <span>Código atual</span>
                      <input value={authMfaCode} onChange={(event) => setAuthMfaCode(event.target.value)} inputMode="numeric" />
                    </label>
                    <button type="button" className="secondary-button" onClick={() => void disableMfa()} disabled={loading || !authMfaCode.trim()}>
                      Desativar
                    </button>
                  </>
                ) : null}
              </div>
            )}
          </article>

          <article className="panel auth-panel">
            <div className="panel-header-row">
              <div>
                <h2>Autenticação reforçada</h2>
                <p>Pré-validação curta para ações destrutivas na impressora.</p>
              </div>
              <KeyRound size={20} />
            </div>
            <div className="auth-stack">
              {authUser.mfa_enabled ? (
                <label>
                  <span>Código 2FA</span>
                  <input value={stepUpCode} onChange={(event) => setStepUpCode(event.target.value)} inputMode="numeric" />
                </label>
              ) : (
                <label>
                  <span>Senha</span>
                  <input value={stepUpPassword} onChange={(event) => setStepUpPassword(event.target.value)} type="password" />
                </label>
              )}
              <button type="button" className="primary-button" onClick={() => void requestStepUp()} disabled={loading || (!stepUpCode.trim() && !stepUpPassword.trim())}>
                Gerar autorização
              </button>
              {stepUpResult ? <small>Autorização válida até {stepUpResult.expires_at}.</small> : null}
            </div>
          </article>
        </div>
      ) : null}

      {accountTab === "organizations" ? (
        <div className="account-grid">
          <article className="panel auth-panel">
            <div className="panel-header-row">
              <div>
                <h2>Minhas organizações</h2>
                <p>Você pode participar de mais de uma organização e manter uso individual ao mesmo tempo.</p>
              </div>
              <Plus size={20} />
            </div>
            <div className="organization-list">
              <div className="organization-card active">
                <strong>Uso individual</strong>
                <span>Conta própria</span>
                <small>As impressoras ficam visíveis somente para você.</small>
              </div>
              {authUser.organizations.map((organization) => (
                <div key={organization.id} className="organization-card">
                  <strong>{organization.name}</strong>
                  <span>{organization.role}</span>
                  <small>Organização #{organization.id}</small>
                </div>
              ))}
            </div>
          </article>

          <article className="panel auth-panel">
            <div className="panel-header-row">
              <div>
                <h2>Organização opcional</h2>
                <p>Crie organizações apenas quando quiser compartilhar impressoras com outros usuários.</p>
              </div>
              <Plus size={20} />
            </div>
            <div className="auth-stack">
              <label>
                <span>Nova organização</span>
                <input value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} />
              </label>
              <button type="button" className="primary-button" onClick={() => void createAuthOrganization()} disabled={loading || !organizationName.trim()}>
                Criar organização
              </button>
              <label>
                <span>Organização para convite</span>
                <select value={selectedOrganizationId ?? ""} onChange={(event) => setSelectedOrganizationId(Number(event.target.value) || null)}>
                  <option value="">Selecione</option>
                  {authUser.organizations.map((organization) => (
                    <option key={organization.id} value={organization.id}>{organization.name} · {organization.role}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Email do usuário</span>
                <input value={memberEmail} onChange={(event) => setMemberEmail(event.target.value)} type="email" />
              </label>
              <label>
                <span>Papel</span>
                <select value={memberRole} onChange={(event) => setMemberRole(event.target.value as "admin" | "operator")}>
                  <option value="operator">Operador</option>
                  <option value="admin">Admin</option>
                </select>
              </label>
              <button type="button" className="secondary-button" onClick={() => void addAuthOrganizationMember()} disabled={loading || !selectedOrganizationId || !memberEmail.trim()}>
                Vincular usuário
              </button>
            </div>
          </article>
        </div>
      ) : null}
    </section>
  );
}

function readRequestedAccountTab(): AccountTab {
  const requested = (window as Window & { printoraAccountTab?: AccountTab }).printoraAccountTab;
  return requested && accountTabKeys.includes(requested) ? requested : "access";
}
