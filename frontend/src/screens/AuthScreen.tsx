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
  | "createdOrganizationInvite"
  | "loading"
  | "memberEmail"
  | "memberRole"
  | "mfaSetup"
  | "organizationCreateOpen"
  | "organizationDetail"
  | "organizationName"
  | "organizationPrinterId"
  | "printers"
  | "selectedOrganizationId"
  | "setCreatedOrganizationInvite"
  | "setAuthDisplayName"
  | "setAuthEmail"
  | "setAuthMfaCode"
  | "setAuthMode"
  | "setAuthPassword"
  | "setMemberEmail"
  | "setMemberRole"
  | "setOrganizationCreateOpen"
  | "setOrganizationName"
  | "setOrganizationPrinterId"
  | "setSelectedOrganizationId"
  | "setStepUpCode"
  | "setStepUpPassword"
  | "showToast"
  | "stepUpCode"
  | "stepUpPassword"
  | "stepUpResult"
  | "addAuthOrganizationMember"
  | "confirmMfaSetup"
  | "createAuthOrganization"
  | "createAuthOrganizationInvite"
  | "disableMfa"
  | "linkAuthOrganizationPrinter"
  | "loadOrganizationDetail"
  | "logoutAuth"
  | "removeAuthOrganizationMember"
  | "requestStepUp"
  | "startMfaSetup"
  | "submitAuth"
  | "submitMfaLogin"
  | "unlinkAuthOrganizationPrinter"
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
    createdOrganizationInvite,
    loading,
    memberEmail,
    memberRole,
    mfaSetup,
    organizationCreateOpen,
    organizationDetail,
    organizationName,
    organizationPrinterId,
    printers,
    selectedOrganizationId,
    setCreatedOrganizationInvite,
    setAuthDisplayName,
    setAuthEmail,
    setAuthMfaCode,
    setAuthMode,
    setAuthPassword,
    setMemberEmail,
    setMemberRole,
    setOrganizationCreateOpen,
    setOrganizationName,
    setOrganizationPrinterId,
    setSelectedOrganizationId,
    setStepUpCode,
    setStepUpPassword,
    showToast,
    stepUpCode,
    stepUpPassword,
    stepUpResult,
    addAuthOrganizationMember,
    confirmMfaSetup,
    createAuthOrganization,
    createAuthOrganizationInvite,
    disableMfa,
    linkAuthOrganizationPrinter,
    loadOrganizationDetail,
    logoutAuth,
    removeAuthOrganizationMember,
    requestStepUp,
    startMfaSetup,
    submitAuth,
    submitMfaLogin,
    unlinkAuthOrganizationPrinter,
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
  React.useEffect(() => {
    if (accountTab === "organizations" && selectedOrganizationId && !organizationDetail) {
      void loadOrganizationDetail(selectedOrganizationId);
    }
  }, [accountTab, selectedOrganizationId, organizationDetail]);

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
                <p>Abra uma organização para ver membros, convites e impressoras vinculadas.</p>
              </div>
              <button type="button" className="secondary-button" onClick={() => setOrganizationCreateOpen(true)}>
                <Plus size={16} />
                Nova
              </button>
            </div>
            <div className="organization-list">
              <div className="organization-card active">
                <strong>Uso individual</strong>
                <span>Conta própria</span>
                <small>As impressoras ficam visíveis somente para você.</small>
              </div>
              {authUser.organizations.map((organization) => (
                <button
                  key={organization.id}
                  type="button"
                  className={`organization-card ${selectedOrganizationId === organization.id ? "active" : ""}`}
                  onClick={() => void loadOrganizationDetail(organization.id)}
                >
                  <strong>{organization.name}</strong>
                  <span>{organization.role}</span>
                  <small>Organização #{organization.id}</small>
                </button>
              ))}
            </div>
          </article>

          <article className="panel auth-panel">
            <div className="panel-header-row">
              <div>
                <h2>{organizationDetail ? organizationDetail.name : "Detalhe da organização"}</h2>
                <p>{organizationDetail ? `Organização #${organizationDetail.id} · ${organizationDetail.role}` : "Selecione uma organização para gerenciar acessos e impressoras."}</p>
              </div>
              <ShieldCheck size={20} />
            </div>
            {organizationDetail ? (
              <div className="auth-stack">
                <section className="organization-detail-section">
                  <div className="panel-header-row compact">
                    <h3>Membros</h3>
                    <button type="button" className="secondary-button" onClick={() => void createAuthOrganizationInvite()}>
                      Gerar link
                    </button>
                  </div>
                  <div className="auth-list">
                    {organizationDetail.members.map((member) => (
                      <div key={member.user_id}>
                        <strong>{member.display_name || member.email}</strong>
                        <span>{member.email} · {member.role}</span>
                        {member.role !== "owner" ? (
                          <button type="button" className="secondary-button" onClick={() => void removeAuthOrganizationMember(member.user_id)} disabled={loading}>
                            Remover
                          </button>
                        ) : null}
                      </div>
                    ))}
                  </div>
                </section>

                {createdOrganizationInvite ? (
                  <section className="auth-step">
                    <div>
                      <strong>Link de convite</strong>
                      <p className="muted">Válido até {createdOrganizationInvite.expires_at}.</p>
                      <code>{createdOrganizationInvite.invite_url}</code>
                    </div>
                    <button type="button" className="secondary-button" onClick={() => void copyInviteLink(createdOrganizationInvite.invite_url, showToast)}>
                      Copiar
                    </button>
                    <button type="button" className="secondary-button" onClick={() => setCreatedOrganizationInvite(null)}>
                      Ocultar
                    </button>
                  </section>
                ) : null}

                <section className="organization-detail-section">
                  <div className="panel-header-row compact">
                    <h3>Impressoras vinculadas</h3>
                    <div className="printer-card-actions">
                      <select value={organizationPrinterId} onChange={(event) => setOrganizationPrinterId(event.target.value ? Number(event.target.value) : "")}>
                        <option value="">Selecionar impressora</option>
                        {printers.map((printer) => (
                          <option key={printer.id} value={printer.id}>{printer.name}</option>
                        ))}
                      </select>
                      <button type="button" className="secondary-button" onClick={() => void linkAuthOrganizationPrinter()} disabled={loading || organizationPrinterId === ""}>
                        Vincular
                      </button>
                    </div>
                  </div>
                  <div className="auth-list">
                    {organizationDetail.printers.length === 0 ? <span className="muted">Nenhuma impressora vinculada.</span> : null}
                    {organizationDetail.printers.map((printer) => (
                      <div key={printer.printer_id}>
                        <strong>{printer.name}</strong>
                        <span>{printer.moonraker_url}</span>
                        <button type="button" className="secondary-button" onClick={() => void unlinkAuthOrganizationPrinter(printer.printer_id)} disabled={loading}>
                          Remover
                        </button>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="organization-detail-section">
                  <h3>Convites recentes</h3>
                  <div className="auth-list">
                    {organizationDetail.invites.length === 0 ? <span className="muted">Nenhum convite gerado.</span> : null}
                    {organizationDetail.invites.map((invite) => (
                      <div key={invite.id}>
                        <strong>{invite.token_prefix}</strong>
                        <span>{invite.role} · expira {invite.expires_at} · {invite.accepted_at ? "aceito" : "pendente"}</span>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            ) : null}
          </article>

          {organizationCreateOpen ? (
            <div className="modal-backdrop" role="presentation">
              <article className="modal-card auth-create-modal" aria-label="Criar organização">
                <div className="modal-header">
                  <div>
                    <h2>Criar organização</h2>
                    <p>Use apenas quando for compartilhar impressoras com outras pessoas.</p>
                  </div>
                  <button type="button" className="icon-button" onClick={() => setOrganizationCreateOpen(false)} aria-label="Fechar">
                    ×
                  </button>
                </div>
                <label>
                  <span>Nome da organização</span>
                  <input value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} />
                </label>
                <button type="button" className="primary-button" onClick={() => void createAuthOrganization()} disabled={loading || !organizationName.trim()}>
                  Criar organização
                </button>
              </article>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function readRequestedAccountTab(): AccountTab {
  const requested = (window as Window & { printoraAccountTab?: AccountTab }).printoraAccountTab;
  return requested && accountTabKeys.includes(requested) ? requested : "access";
}

async function copyInviteLink(inviteUrl: string, showToast: (options: { tone?: "success" | "danger"; title: string; detail?: string }) => void) {
  try {
    await navigator.clipboard.writeText(inviteUrl);
    showToast({ tone: "success", title: "Link copiado" });
  } catch {
    showToast({ tone: "danger", title: "Falha ao copiar link", detail: inviteUrl });
  }
}
