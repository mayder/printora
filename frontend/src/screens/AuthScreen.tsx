import type { ScreenPropsFor } from "./ScreenProps";

type AuthScreenProps = ScreenPropsFor<
  | "KeyRound"
  | "Plus"
  | "ShieldCheck"
  | "UserRound"
  | "agentCredentialLabel"
  | "agentCredentials"
  | "authDisplayName"
  | "authEmail"
  | "authMfaChallengeToken"
  | "authMfaCode"
  | "authMode"
  | "authPassword"
  | "authTelegram"
  | "authUser"
  | "authWhatsapp"
  | "createdAgentCredential"
  | "loading"
  | "memberEmail"
  | "memberRole"
  | "mfaSetup"
  | "organizationName"
  | "selectedOrganizationId"
  | "setAgentCredentialLabel"
  | "setAuthDisplayName"
  | "setAuthEmail"
  | "setAuthMfaCode"
  | "setAuthMode"
  | "setAuthPassword"
  | "setAuthTelegram"
  | "setAuthWhatsapp"
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
  | "createAuthAgentCredential"
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
    agentCredentialLabel,
    agentCredentials,
    authDisplayName,
    authEmail,
    authMfaChallengeToken,
    authMfaCode,
    authMode,
    authPassword,
    authTelegram,
    authUser,
    authWhatsapp,
    createdAgentCredential,
    loading,
    memberEmail,
    memberRole,
    mfaSetup,
    organizationName,
    selectedOrganizationId,
    setAgentCredentialLabel,
    setAuthDisplayName,
    setAuthEmail,
    setAuthMfaCode,
    setAuthMode,
    setAuthPassword,
    setAuthTelegram,
    setAuthWhatsapp,
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
    createAuthAgentCredential,
    createAuthOrganization,
    disableMfa,
    logoutAuth,
    requestStepUp,
    startMfaSetup,
    submitAuth,
    submitMfaLogin,
  } = props;

  if (!authUser) {
    return (
      <article className="panel wide auth-panel">
        <div className="panel-header-row">
          <div>
            <h2>{authMode === "login" ? "Entrar" : "Criar conta"}</h2>
            <p>Email e senha são obrigatórios. Contatos são opcionais.</p>
          </div>
          <span className="status-pill info">{authMode === "login" ? "Sessão" : "Cadastro"}</span>
        </div>
        <div className="segmented-control">
          <button type="button" className={authMode === "login" ? "active" : ""} onClick={() => setAuthMode("login")}>Login</button>
          <button type="button" className={authMode === "register" ? "active" : ""} onClick={() => setAuthMode("register")}>Cadastro</button>
        </div>
        <div className="auth-grid">
          <label>
            <span>Email</span>
            <input value={authEmail} onChange={(event) => setAuthEmail(event.target.value)} type="email" autoComplete="email" />
          </label>
          <label>
            <span>Senha</span>
            <input value={authPassword} onChange={(event) => setAuthPassword(event.target.value)} type="password" autoComplete={authMode === "login" ? "current-password" : "new-password"} />
          </label>
          {authMode === "register" ? (
            <>
              <label>
                <span>Nome</span>
                <input value={authDisplayName} onChange={(event) => setAuthDisplayName(event.target.value)} />
              </label>
              <label>
                <span>WhatsApp</span>
                <input value={authWhatsapp} onChange={(event) => setAuthWhatsapp(event.target.value)} />
              </label>
              <label>
                <span>Telegram</span>
                <input value={authTelegram} onChange={(event) => setAuthTelegram(event.target.value)} />
              </label>
            </>
          ) : null}
        </div>
        {authMfaChallengeToken ? (
          <div className="auth-step">
            <label>
              <span>Código 2FA</span>
              <input value={authMfaCode} onChange={(event) => setAuthMfaCode(event.target.value)} inputMode="numeric" />
            </label>
            <button type="button" className="primary-button" onClick={() => void submitMfaLogin()} disabled={loading || !authMfaCode.trim()}>
              <ShieldCheck size={16} />
              Validar
            </button>
          </div>
        ) : (
          <button type="button" className="primary-button" onClick={() => void submitAuth()} disabled={loading || !authEmail.trim() || !authPassword.trim()}>
            <UserRound size={16} />
            {authMode === "login" ? "Entrar" : "Criar conta"}
          </button>
        )}
      </article>
    );
  }

  return (
    <>
      <article className="panel wide auth-panel">
        <div className="panel-header-row">
          <div>
            <h2>Conta autenticada</h2>
            <p>{authUser.email}</p>
          </div>
          <button type="button" className="secondary-button" onClick={() => void logoutAuth()}>
            Sair
          </button>
        </div>
        <div className="auth-summary">
          <span>2FA: <strong>{authUser.mfa_enabled ? "ativo" : "inativo"}</strong></span>
          <span>Organizações: <strong>{authUser.organizations.length}</strong></span>
          <span>WhatsApp: <strong>{authUser.whatsapp || "-"}</strong></span>
          <span>Telegram: <strong>{authUser.telegram || "-"}</strong></span>
        </div>
      </article>

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
            <h2>Organização opcional</h2>
            <p>Use apenas quando quiser compartilhar impressoras com outros usuários.</p>
          </div>
          <Plus size={20} />
        </div>
        <div className="auth-stack">
          <label>
            <span>Nova organização</span>
            <input value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} />
          </label>
          <button type="button" className="primary-button" onClick={() => void createAuthOrganization()} disabled={loading || !organizationName.trim()}>
            Criar
          </button>
          <label>
            <span>Organização</span>
            <select value={selectedOrganizationId ?? ""} onChange={(event) => setSelectedOrganizationId(Number(event.target.value) || null)}>
              <option value="">Uso individual</option>
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

      <article className="panel wide auth-panel">
        <div className="panel-header-row">
          <div>
            <h2>Credenciais de agente</h2>
            <p>A credencial completa aparece uma única vez e pode ser revogada em pacote posterior.</p>
          </div>
          <KeyRound size={20} />
        </div>
        <div className="auth-stack">
          <label>
            <span>Identificação do agente</span>
            <input value={agentCredentialLabel} onChange={(event) => setAgentCredentialLabel(event.target.value)} />
          </label>
          <button type="button" className="primary-button" onClick={() => void createAuthAgentCredential()} disabled={loading || !agentCredentialLabel.trim()}>
            Criar credencial
          </button>
          {createdAgentCredential ? (
            <code>{createdAgentCredential.credential}</code>
          ) : null}
          <div className="auth-list">
            {agentCredentials.map((credential) => (
              <div key={credential.id}>
                <strong>{credential.label}</strong>
                <span>{credential.credential_prefix} · {credential.revoked ? "revogada" : "ativa"}</span>
              </div>
            ))}
          </div>
        </div>
      </article>
    </>
  );
}
