import React from "react";
import { ExternalLink, Globe2, Lock, MapPin, RadioTower, Shield, Link as LinkIcon } from "lucide-react";
import type { ScreenPropsFor } from "./ScreenProps";
import { socialApi } from "../services/socialApi";
import { formatDateTime } from "../utils/formatters";
import type { CatalogSummary, CatalogVariant, FollowersVisibility, ProfileVisibility, PublicPrinter, PublicProfile, SocialMessagesFrom, SocialSafetySettings } from "../types";

type AccountTab = "profile" | "organizations";
const accountTabKeys: AccountTab[] = ["organizations", "profile"];
type ProfileSection = "account" | "social" | "contacts" | "password" | "security";
const commonTimezones = [
  "America/Sao_Paulo",
  "America/Manaus",
  "America/Cuiaba",
  "America/Rio_Branco",
  "America/New_York",
  "America/Los_Angeles",
  "Europe/Lisbon",
  "UTC",
];

type AuthScreenProps = ScreenPropsFor<
  | "KeyRound"
  | "LogOut"
  | "Plus"
  | "Printer"
  | "ArrowLeft"
  | "Building2"
  | "Pencil"
  | "ShieldCheck"
  | "Trash2"
  | "UserRound"
  | "Users"
  | "X"
  | "ClipboardCheck"
  | "authDisplayName"
  | "authEmail"
  | "authMfaChallengeToken"
  | "authMfaCode"
  | "authMode"
  | "authPassword"
  | "authTimezone"
  | "authUser"
  | "createdOrganizationInvite"
  | "loading"
  | "loadPrinters"
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
  | "setAuthTimezone"
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
  | "confirmAction"
  | "confirmMfaSetup"
  | "createAuthOrganization"
  | "createAuthOrganizationInvite"
  | "deleteAuthOrganization"
  | "disableMfa"
  | "linkAuthOrganizationPrinter"
  | "loadOrganizationDetail"
  | "logoutAuth"
  | "removeAuthOrganizationMember"
  | "requestStepUp"
  | "revokeAuthOrganizationInvite"
  | "startMfaSetup"
  | "submitAuth"
  | "submitMfaLogin"
  | "unlinkAuthOrganizationPrinter"
  | "updateAuthPassword"
  | "updateAuthProfile"
  | "updateAuthOrganization"
>;

export function AuthScreen(props: AuthScreenProps) {
  const {
    KeyRound,
    LogOut,
    Plus,
    Printer,
    ArrowLeft,
    Building2,
    Pencil,
    ShieldCheck,
    Trash2,
    UserRound,
    Users,
    X,
    ClipboardCheck,
    authDisplayName,
    authEmail,
    authMfaChallengeToken,
    authMfaCode,
    authMode,
    authPassword,
    authTimezone,
    authUser,
    createdOrganizationInvite,
    loading,
    loadPrinters,
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
    setAuthTimezone,
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
    confirmAction,
    confirmMfaSetup,
    createAuthOrganization,
    createAuthOrganizationInvite,
    deleteAuthOrganization,
    disableMfa,
    linkAuthOrganizationPrinter,
    loadOrganizationDetail,
    logoutAuth,
    removeAuthOrganizationMember,
    requestStepUp,
    revokeAuthOrganizationInvite,
    startMfaSetup,
    submitAuth,
    submitMfaLogin,
    unlinkAuthOrganizationPrinter,
    updateAuthPassword,
    updateAuthProfile,
    updateAuthOrganization,
  } = props;
  const [accountTab, setAccountTab] = React.useState<AccountTab>(() => readRequestedAccountTab());
  const [organizationPage, setOrganizationPage] = React.useState<"list" | "detail">("list");
  const [organizationEditOpen, setOrganizationEditOpen] = React.useState(false);
  const [editingOrganizationName, setEditingOrganizationName] = React.useState("");
  const [profileDisplayName, setProfileDisplayName] = React.useState("");
  const [profileWhatsapp, setProfileWhatsapp] = React.useState("");
  const [profileTelegram, setProfileTelegram] = React.useState("");
  const [profileInstagram, setProfileInstagram] = React.useState("");
  const [profileX, setProfileX] = React.useState("");
  const [profileFacebook, setProfileFacebook] = React.useState("");
  const [profileWebsite, setProfileWebsite] = React.useState("");
  const [profileTimezone, setProfileTimezone] = React.useState(authTimezone);
  const [profileSection, setProfileSection] = React.useState<ProfileSection>("account");
  const [socialProfile, setSocialProfile] = React.useState<PublicProfile | null>(null);
  const [socialPrinters, setSocialPrinters] = React.useState<PublicPrinter[]>([]);
  const [socialCatalog, setSocialCatalog] = React.useState<CatalogSummary | null>(null);
  const [selectedPublicPrinterId, setSelectedPublicPrinterId] = React.useState<number | "">("");
  const [selectedPublicVariantId, setSelectedPublicVariantId] = React.useState<number | "">("");
  const [publicPrinterDescription, setPublicPrinterDescription] = React.useState("");
  const [publicPrinterMods, setPublicPrinterMods] = React.useState("");
  const [socialDisplayName, setSocialDisplayName] = React.useState("");
  const [socialSlug, setSocialSlug] = React.useState("");
  const [socialBio, setSocialBio] = React.useState("");
  const [socialLocation, setSocialLocation] = React.useState("");
  const [socialAvatarUrl, setSocialAvatarUrl] = React.useState("");
  const [socialVisibility, setSocialVisibility] = React.useState<ProfileVisibility>("public");
  const [socialGithub, setSocialGithub] = React.useState("");
  const [socialInstagram, setSocialInstagram] = React.useState("");
  const [socialYoutube, setSocialYoutube] = React.useState("");
  const [socialX, setSocialX] = React.useState("");
  const [socialPrintables, setSocialPrintables] = React.useState("");
  const [socialMakerworld, setSocialMakerworld] = React.useState("");
  const [socialWebsite, setSocialWebsite] = React.useState("");
  const [socialSafety, setSocialSafety] = React.useState<SocialSafetySettings | null>(null);
  const [safetyProfileDiscoverable, setSafetyProfileDiscoverable] = React.useState(true);
  const [safetyFollowersVisibility, setSafetyFollowersVisibility] = React.useState<FollowersVisibility>("public");
  const [safetyMessagesFrom, setSafetyMessagesFrom] = React.useState<SocialMessagesFrom>("friends");
  const [safetyAllowMentions, setSafetyAllowMentions] = React.useState(true);
  const [safetyAllowDownloadTracking, setSafetyAllowDownloadTracking] = React.useState(true);
  const [safetyRecentDenials, setSafetyRecentDenials] = React.useState(0);
  const [safetyActiveSignals, setSafetyActiveSignals] = React.useState(0);
  const [socialLoading, setSocialLoading] = React.useState(false);
  const [currentPassword, setCurrentPassword] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");
  const [confirmNewPassword, setConfirmNewPassword] = React.useState("");
  const hydratedProfileUserId = React.useRef<number | null>(null);
  React.useEffect(() => {
    function handleAccountTab(event: Event) {
      const tab = (event as CustomEvent<AccountTab | "security">).detail;
      if (tab === "security") {
        setAccountTab("profile");
        return;
      }
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
  React.useEffect(() => {
    if (!authUser || hydratedProfileUserId.current === authUser.id) {
      return;
    }
    hydratedProfileUserId.current = authUser.id;
    setProfileDisplayName(authUser?.display_name ?? "");
    setProfileWhatsapp(authUser?.whatsapp ?? "");
    setProfileTelegram(authUser?.telegram ?? "");
    setProfileInstagram(authUser?.social_links.instagram ?? "");
    setProfileX(authUser?.social_links.x ?? "");
    setProfileFacebook(authUser?.social_links.facebook ?? "");
    setProfileWebsite(authUser?.social_links.website ?? "");
    setProfileTimezone(authUser?.timezone ?? authTimezone);
    setAuthTimezone(authUser?.timezone ?? authTimezone);
  }, [authUser?.id]);
  React.useEffect(() => {
    if (!authUser) {
      return;
    }
    void loadSocialProfile();
  }, [authUser?.id]);
  const organizationByDetail = organizationDetail
    ? authUser?.organizations.find((organization) => organization.id === organizationDetail.id)
    : null;
  const canManageSelectedOrganization = organizationByDetail?.role === "owner" || organizationByDetail?.role === "admin";
  const canOwnSelectedOrganization = organizationByDetail?.role === "owner";
  const publicProfileUrl = socialProfile ? `${window.location.origin}/u/${socialProfile.slug}` : "";
  const socialVariants = React.useMemo(() => flattenVariants(socialCatalog), [socialCatalog]);
  const selectedPublicPrinter = printers.find((printer) => printer.id === selectedPublicPrinterId);
  const selectedPublicVariant = socialVariants.find((variant) => variant.id === selectedPublicVariantId);

  async function openOrganizationDetail(organizationId: number) {
    await loadOrganizationDetail(organizationId);
    setOrganizationPage("detail");
    setCreatedOrganizationInvite(null);
  }

  function openOrganizationEdit(organizationId: number, name: string) {
    setSelectedOrganizationId(organizationId);
    setEditingOrganizationName(name);
    setOrganizationEditOpen(true);
  }

  async function saveOrganizationEdit() {
    if (!selectedOrganizationId || !editingOrganizationName.trim()) {
      return;
    }
    await updateAuthOrganization(selectedOrganizationId, editingOrganizationName);
    setOrganizationEditOpen(false);
  }

  async function confirmOrganizationDelete(organizationId: number, name: string) {
    const confirmed = await confirmAction({
      tone: "danger",
      title: "Excluir organização",
      detail: `A organização "${name}" será removida. Membros perdem acesso compartilhado e convites pendentes são revogados.`,
      evidence: name,
      confirmLabel: "Excluir",
      cancelLabel: "Cancelar",
    });
    if (!confirmed) {
      return;
    }
    await deleteAuthOrganization(organizationId);
    setOrganizationPage("list");
    setCreatedOrganizationInvite(null);
  }

  async function confirmInviteRevoke(inviteId: number, tokenPrefix: string) {
    const confirmed = await confirmAction({
      tone: "warning",
      title: "Cancelar convite",
      detail: `O convite ${tokenPrefix} não poderá mais ser usado para entrar na organização.`,
      confirmLabel: "Cancelar convite",
      cancelLabel: "Voltar",
    });
    if (confirmed) {
      await revokeAuthOrganizationInvite(inviteId);
    }
  }

  async function saveProfile() {
    await updateAuthProfile({
      display_name: profileDisplayName || null,
      whatsapp: profileWhatsapp || null,
      telegram: profileTelegram || null,
      timezone: profileTimezone,
      social_links: {
        instagram: profileInstagram || null,
        x: profileX || null,
        facebook: profileFacebook || null,
        website: profileWebsite || null,
      },
    });
    showToast({ tone: "success", title: "Perfil atualizado" });
  }

  async function savePassword() {
    if (newPassword !== confirmNewPassword) {
      showToast({ tone: "danger", title: "Senhas diferentes", detail: "Confirme a nova senha corretamente." });
      return;
    }
    await updateAuthPassword(currentPassword, newPassword);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmNewPassword("");
    showToast({ tone: "success", title: "Senha alterada" });
  }

  async function loadSocialProfile() {
    setSocialLoading(true);
    try {
      const [profilePayload, catalogPayload, safetyPayload] = await Promise.all([socialApi.myProfile(), socialApi.catalog(), socialApi.socialSafety()]);
      const printerPayload = await socialApi.profilePrinters(profilePayload.slug);
      setSocialProfile(profilePayload);
      setSocialPrinters(printerPayload);
      setSocialCatalog(catalogPayload);
      setSocialSafety(safetyPayload.settings);
      setSafetyProfileDiscoverable(safetyPayload.settings.profile_discoverable);
      setSafetyFollowersVisibility(safetyPayload.settings.followers_visibility);
      setSafetyMessagesFrom(safetyPayload.settings.messages_from);
      setSafetyAllowMentions(safetyPayload.settings.allow_content_mentions);
      setSafetyAllowDownloadTracking(safetyPayload.settings.allow_download_tracking);
      setSafetyRecentDenials(safetyPayload.recent_denials);
      setSafetyActiveSignals(safetyPayload.active_signals.length);
      setSocialDisplayName(profilePayload.display_name);
      setSocialSlug(profilePayload.slug);
      setSocialBio(profilePayload.bio ?? "");
      setSocialLocation(profilePayload.location ?? "");
      setSocialAvatarUrl(profilePayload.avatar_url ?? "");
      setSocialVisibility(profilePayload.visibility);
      setSocialGithub(profilePayload.social_links.github ?? "");
      setSocialInstagram(profilePayload.social_links.instagram ?? "");
      setSocialYoutube(profilePayload.social_links.youtube ?? "");
      setSocialX(profilePayload.social_links.x ?? "");
      setSocialPrintables(profilePayload.social_links.printables ?? "");
      setSocialMakerworld(profilePayload.social_links.makerworld ?? "");
      setSocialWebsite(profilePayload.social_links.website ?? "");
    } catch (err) {
      showToast({ tone: "danger", title: "Falha ao carregar perfil social", detail: err instanceof Error ? err.message : undefined });
    } finally {
      setSocialLoading(false);
    }
  }

  async function saveSocialProfile() {
    if (!authUser) {
      return;
    }
    setSocialLoading(true);
    try {
      const updated = await socialApi.updateProfile({
        slug: socialSlug,
        display_name: socialDisplayName || profileDisplayName || authUser.email,
        bio: socialBio || null,
        location: socialLocation || null,
        avatar_url: socialAvatarUrl || null,
        visibility: socialVisibility,
        social_links: {
          website: socialWebsite || null,
          github: socialGithub || null,
          instagram: socialInstagram || null,
          youtube: socialYoutube || null,
          x: socialX || null,
          printables: socialPrintables || null,
          makerworld: socialMakerworld || null,
        },
      });
      setSocialProfile(updated);
      setSocialPrinters(await socialApi.profilePrinters(updated.slug));
      showToast({ tone: "success", title: "Perfil público atualizado" });
    } catch (err) {
      showToast({ tone: "danger", title: "Falha ao salvar perfil público", detail: err instanceof Error ? err.message : undefined });
    } finally {
      setSocialLoading(false);
    }
  }

  async function saveSocialSafety() {
    setSocialLoading(true);
    try {
      const updated = await socialApi.updateSocialSafety({
        profile_discoverable: safetyProfileDiscoverable,
        followers_visibility: safetyFollowersVisibility,
        messages_from: safetyMessagesFrom,
        allow_content_mentions: safetyAllowMentions,
        allow_download_tracking: safetyAllowDownloadTracking,
      });
      setSocialSafety(updated);
      showToast({ tone: "success", title: "Segurança social atualizada" });
    } catch (err) {
      showToast({ tone: "danger", title: "Falha ao salvar segurança social", detail: err instanceof Error ? err.message : undefined });
    } finally {
      setSocialLoading(false);
    }
  }

  async function publishProfilePrinter(publicEnabled: boolean) {
    if (!selectedPublicPrinterId || !selectedPublicPrinter || (!selectedPublicVariantId && publicEnabled)) {
      showToast({ tone: "danger", title: "Seleção incompleta", detail: "Selecione uma impressora e uma variante do catálogo." });
      return;
    }
    setSocialLoading(true);
    try {
      await socialApi.updatePrinterPublic(Number(selectedPublicPrinterId), {
        public_profile_enabled: publicEnabled,
        catalog_variant_id: publicEnabled ? Number(selectedPublicVariantId) : null,
        public_name: selectedPublicPrinter.name,
        public_description: publicPrinterDescription || null,
        public_mods: publicPrinterMods.split(",").map((item) => item.trim()).filter(Boolean),
      });
      await loadPrinters();
      if (socialProfile) {
        setSocialPrinters(await socialApi.profilePrinters(socialProfile.slug));
      }
      showToast({ tone: "success", title: publicEnabled ? "Impressora publicada" : "Impressora privada" });
    } catch (err) {
      showToast({ tone: "danger", title: "Falha ao atualizar impressora pública", detail: err instanceof Error ? err.message : undefined });
    } finally {
      setSocialLoading(false);
    }
  }

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
            <LogOut size={16} />
            Sair
          </button>
        </div>
      </article>

      {accountTab === "profile" ? (
        <div className="profile-workspace">
          <div className="segmented-control profile-tabs" role="tablist" aria-label="Perfil">
            <button type="button" className={profileSection === "account" ? "active" : ""} onClick={() => setProfileSection("account")}>
              <UserRound size={16} />
              Conta
            </button>
            <button type="button" className={profileSection === "social" ? "active" : ""} onClick={() => setProfileSection("social")}>
              <Globe2 size={16} />
              Público
            </button>
            <button type="button" className={profileSection === "contacts" ? "active" : ""} onClick={() => setProfileSection("contacts")}>
              <Users size={16} />
              Contatos
            </button>
            <button type="button" className={profileSection === "password" ? "active" : ""} onClick={() => setProfileSection("password")}>
              <KeyRound size={16} />
              Senha
            </button>
            <button type="button" className={profileSection === "security" ? "active" : ""} onClick={() => setProfileSection("security")}>
              <ShieldCheck size={16} />
              Segurança
            </button>
          </div>
          {profileSection === "account" ? (
          <article className="panel auth-panel profile-card">
            <div className="profile-section-title">
              <span className="organization-card-icon"><UserRound size={17} /></span>
              <div>
                <span className="account-eyebrow">Perfil</span>
                <h2>Dados da conta</h2>
                <p>Email é usado para login; demais dados podem ser alterados quando quiser.</p>
              </div>
            </div>
            <div className="profile-form-grid">
              <label>
                <span>Email</span>
                <input value={authUser.email} disabled />
              </label>
              <label>
                <span>Nome</span>
                <input value={profileDisplayName} onChange={(event) => setProfileDisplayName(event.target.value)} placeholder="Nome exibido" />
              </label>
              <label>
                <span>Timezone</span>
                <select value={profileTimezone} onChange={(event) => setProfileTimezone(event.target.value)}>
                  {timezoneOptions(profileTimezone).map((timezone) => (
                    <option key={timezone} value={timezone}>{timezone}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="profile-card-actions">
              <button type="button" className="primary-button" onClick={() => void saveProfile()} disabled={loading}>
                <ClipboardCheck size={16} />
                Salvar perfil
              </button>
            </div>
          </article>
          ) : null}

          {profileSection === "social" ? (
          <div className="social-profile-workspace">
            <article className="panel auth-panel profile-card social-profile-editor">
              <div className="profile-section-title">
                <span className="organization-card-icon"><Globe2 size={17} /></span>
                <div>
                  <span className="account-eyebrow">Perfil público/social</span>
                  <h2>Identidade pública</h2>
                  <p>Estes dados aparecem na página pública. Email, WhatsApp, organizações, permissões, agente, Moonraker, SSH e tokens ficam fora do perfil público.</p>
                </div>
              </div>
              <div className="profile-form-grid">
                <label>
                  <span>Nome público</span>
                  <input value={socialDisplayName} onChange={(event) => setSocialDisplayName(event.target.value)} maxLength={120} placeholder="Nome visível para outros makers" />
                </label>
                <label>
                  <span>Slug público</span>
                  <input value={socialSlug} onChange={(event) => setSocialSlug(event.target.value)} maxLength={80} placeholder="meu-perfil" />
                  <small>Trocar o slug muda a URL pública. Slugs antigos ficam reservados para evitar abuso.</small>
                </label>
                <label>
                  <span>Visibilidade</span>
                  <select value={socialVisibility} onChange={(event) => setSocialVisibility(event.target.value as ProfileVisibility)}>
                    <option value="public">Público</option>
                    <option value="unlisted">Não listado, acessível por URL direta</option>
                    <option value="private">Privado</option>
                  </select>
                  <small>{visibilityHelp(socialVisibility)}</small>
                </label>
                <label>
                  <span>Avatar HTTPS</span>
                  <input value={socialAvatarUrl} onChange={(event) => setSocialAvatarUrl(event.target.value)} placeholder="https://..." />
                  <small>Apenas URL HTTPS pública; hosts locais ou privados são rejeitados.</small>
                </label>
                <label>
                  <span>Localização opcional</span>
                  <input value={socialLocation} onChange={(event) => setSocialLocation(event.target.value)} maxLength={120} placeholder="Cidade/UF" />
                </label>
                <label>
                  <span>Bio curta</span>
                  <textarea value={socialBio} onChange={(event) => setSocialBio(event.target.value)} maxLength={280} placeholder="Tipo de impressora, materiais e foco do perfil" />
                </label>
              </div>

              <div className="profile-section-title compact">
                <span className="organization-card-icon"><LinkIcon size={17} /></span>
                <div>
                  <span className="account-eyebrow">Links permitidos</span>
                  <h2>Avatar e redes</h2>
                  <p>Links sociais aceitam somente HTTPS e hosts públicos esperados para cada rede.</p>
                </div>
              </div>
              <div className="profile-form-grid">
                <label><span>Website</span><input value={socialWebsite} onChange={(event) => setSocialWebsite(event.target.value)} placeholder="https://..." /></label>
                <label><span>GitHub</span><input value={socialGithub} onChange={(event) => setSocialGithub(event.target.value)} placeholder="https://github.com/usuario" /></label>
                <label><span>Instagram</span><input value={socialInstagram} onChange={(event) => setSocialInstagram(event.target.value)} placeholder="https://instagram.com/usuario" /></label>
                <label><span>YouTube</span><input value={socialYoutube} onChange={(event) => setSocialYoutube(event.target.value)} placeholder="https://youtube.com/@canal" /></label>
                <label><span>X/Twitter</span><input value={socialX} onChange={(event) => setSocialX(event.target.value)} placeholder="https://x.com/usuario" /></label>
                <label><span>Printables</span><input value={socialPrintables} onChange={(event) => setSocialPrintables(event.target.value)} placeholder="https://printables.com/@usuario" /></label>
                <label><span>MakerWorld</span><input value={socialMakerworld} onChange={(event) => setSocialMakerworld(event.target.value)} placeholder="https://makerworld.com/..." /></label>
              </div>

              <div className="social-profile-url">
                <div>
                  <span>URL pública</span>
                  <strong>{publicProfileUrl || "Salve o perfil para gerar a URL"}</strong>
                  {socialProfile?.reserved_slugs?.length ? <small>Slugs reservados: {socialProfile.reserved_slugs.join(", ")}</small> : <small>Nenhum slug antigo reservado para sua conta.</small>}
                </div>
                {publicProfileUrl ? <a className="secondary-button" href={publicProfileUrl} target="_blank" rel="noreferrer"><ExternalLink size={16} />Abrir</a> : null}
              </div>

              <div className="profile-card-actions">
                <button type="button" className="primary-button" onClick={() => void saveSocialProfile()} disabled={socialLoading || !socialDisplayName.trim()}>
                  <ClipboardCheck size={16} />
                  Salvar perfil público
                </button>
              </div>
            </article>

            <article className="panel auth-panel profile-card social-profile-preview">
              <div className="profile-section-title">
                <span className="organization-card-icon"><Shield size={17} /></span>
                <div>
                  <span className="account-eyebrow">Prévia pública</span>
                  <h2>{socialDisplayName || "Nome público"}</h2>
                  <p>{socialBio || "Bio curta opcional do perfil social."}</p>
                </div>
              </div>
              <div className="public-preview-card">
                <div className="public-preview-avatar">
                  {socialAvatarUrl ? <img src={socialAvatarUrl} alt="" /> : <UserRound size={28} />}
                </div>
                <div>
                  <strong>{socialDisplayName || "Nome público"}</strong>
                  <span>@{socialSlug || "slug"}</span>
                  {socialLocation ? <small><MapPin size={13} />{socialLocation}</small> : null}
                </div>
              </div>
              <div className="social-privacy-state">
                <strong>Privacidade: {visibilityLabel(socialVisibility)}</strong>
                <span>{visibilityHelp(socialVisibility)}</span>
              </div>
              <div className="social-safe-list">
                <strong>Não exposto publicamente</strong>
                <span>Email, WhatsApp, organizações, papéis, permissões, URLs Moonraker, SSH, agente e tokens.</span>
              </div>
              <div className="public-printer-list compact">
                <strong>Impressoras públicas em contexto</strong>
                {socialPrinters.map((printer) => (
                  <section key={printer.id} className="public-printer-card">
                    <div>
                      <Printer size={16} />
                      <strong>{printer.public_name}</strong>
                    </div>
                    <span>{printer.manufacturer_name} / {printer.model_name} / {printer.variant_name}</span>
                  </section>
                ))}
                {socialPrinters.length === 0 ? <p>Nenhuma impressora pública vinculada ao perfil.</p> : null}
              </div>
            </article>

            <article className="panel auth-panel profile-card social-safety-controls">
              <div className="profile-section-title">
                <span className="organization-card-icon"><ShieldCheck size={17} /></span>
                <div>
                  <span className="account-eyebrow">Segurança social</span>
                  <h2>Privacidade e antiabuso</h2>
                  <p>Controle descoberta, seguidores e contato social sem alterar permissões operacionais da conta.</p>
                </div>
              </div>
              <div className="social-safety-status">
                <section>
                  <strong>{safetyRecentDenials}</strong>
                  <span>limites acionados em 24h</span>
                </section>
                <section>
                  <strong>{safetyActiveSignals}</strong>
                  <span>sinais ativos para revisão</span>
                </section>
                <section>
                  <strong>{socialSafety ? formatDateTime(socialSafety.updated_at) : "-"}</strong>
                  <span>última atualização</span>
                </section>
              </div>
              <div className="profile-form-grid">
                <label className="social-toggle-row">
                  <input type="checkbox" checked={safetyProfileDiscoverable} onChange={(event) => setSafetyProfileDiscoverable(event.target.checked)} />
                  <span>
                    <strong>Aparecer na descoberta</strong>
                    <small>Desligado remove o perfil de listagens e busca por nome; a URL direta continua respeitando a visibilidade pública.</small>
                  </span>
                </label>
                <label>
                  <span>Quem vê seguidores</span>
                  <select value={safetyFollowersVisibility} onChange={(event) => setSafetyFollowersVisibility(event.target.value as FollowersVisibility)}>
                    <option value="public">Qualquer pessoa</option>
                    <option value="followers">Seguidores</option>
                    <option value="friends">Amigos</option>
                    <option value="private">Somente eu</option>
                  </select>
                </label>
                <label>
                  <span>Mensagens sociais</span>
                  <select value={safetyMessagesFrom} onChange={(event) => setSafetyMessagesFrom(event.target.value as SocialMessagesFrom)}>
                    <option value="public">Qualquer perfil</option>
                    <option value="followers">Seguidores</option>
                    <option value="friends">Amigos</option>
                    <option value="none">Ninguém</option>
                  </select>
                </label>
                <label className="social-toggle-row">
                  <input type="checkbox" checked={safetyAllowMentions} onChange={(event) => setSafetyAllowMentions(event.target.checked)} />
                  <span>
                    <strong>Permitir menções em conteúdo</strong>
                    <small>Usado por discussões, comentários e futuras mensagens sociais.</small>
                  </span>
                </label>
                <label className="social-toggle-row">
                  <input type="checkbox" checked={safetyAllowDownloadTracking} onChange={(event) => setSafetyAllowDownloadTracking(event.target.checked)} />
                  <span>
                    <strong>Registrar histórico de downloads sociais</strong>
                    <small>Afeta métricas sociais de arquivos sem expor dados operacionais de impressora.</small>
                  </span>
                </label>
              </div>
              <div className="profile-card-actions">
                <button type="button" className="primary-button" onClick={() => void saveSocialSafety()} disabled={socialLoading}>
                  <ShieldCheck size={16} />
                  Salvar segurança
                </button>
              </div>
            </article>

            <article className="panel auth-panel profile-card social-printer-public-manager">
              <div className="profile-section-title">
                <span className="organization-card-icon"><RadioTower size={17} /></span>
                <div>
                  <span className="account-eyebrow">Impressoras públicas</span>
                  <h2>Publicação no perfil</h2>
                  <p>Escolha quais impressoras aparecem na página pública. A publicação mostra apenas dados sociais e catálogo canônico.</p>
                </div>
              </div>
              <div className="profile-form-grid">
                <label>
                  <span>Inventário real</span>
                  <select value={selectedPublicPrinterId} onChange={(event) => setSelectedPublicPrinterId(event.target.value ? Number(event.target.value) : "")}>
                    <option value="">Selecione</option>
                    {printers.map((printer) => (
                      <option key={printer.id} value={printer.id}>{printer.name}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Variante canônica</span>
                  <select value={selectedPublicVariantId} onChange={(event) => setSelectedPublicVariantId(event.target.value ? Number(event.target.value) : "")}>
                    <option value="">Selecione</option>
                    {socialVariants.map((variant) => (
                      <option key={variant.id} value={variant.id}>{variant.label}</option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>Descrição pública</span>
                  <textarea value={publicPrinterDescription} onChange={(event) => setPublicPrinterDescription(event.target.value)} maxLength={500} />
                </label>
                <label>
                  <span>Mods públicos</span>
                  <input value={publicPrinterMods} onChange={(event) => setPublicPrinterMods(event.target.value)} placeholder="Tap, Nevermore, ERCF" />
                </label>
              </div>
              <div className="profile-card-actions">
                <button type="button" className="primary-button" disabled={socialLoading || !selectedPublicVariant} onClick={() => void publishProfilePrinter(true)}>
                  <Globe2 size={16} />
                  Publicar
                </button>
                <button type="button" className="secondary-button" disabled={socialLoading || !selectedPublicPrinterId} onClick={() => void publishProfilePrinter(false)}>
                  <Lock size={16} />
                  Tornar privada
                </button>
              </div>
            </article>
          </div>
          ) : null}

          {profileSection === "contacts" ? (
          <article className="panel auth-panel profile-card">
            <div className="profile-section-title">
              <span className="organization-card-icon"><Users size={17} /></span>
              <div>
                <span className="account-eyebrow">Contatos</span>
                <h2>WhatsApp, Telegram e redes</h2>
                <p>Informações opcionais para suporte, convites e identificação da conta.</p>
              </div>
            </div>
            <div className="profile-form-grid">
              <label>
                <span>WhatsApp</span>
                <input value={profileWhatsapp} onChange={(event) => setProfileWhatsapp(event.target.value)} placeholder="+55..." />
              </label>
              <label>
                <span>Telegram</span>
                <input value={profileTelegram} onChange={(event) => setProfileTelegram(event.target.value)} placeholder="@usuario" />
              </label>
              <label>
                <span>Instagram</span>
                <input value={profileInstagram} onChange={(event) => setProfileInstagram(event.target.value)} placeholder="@usuario" />
              </label>
              <label>
                <span>X/Twitter</span>
                <input value={profileX} onChange={(event) => setProfileX(event.target.value)} placeholder="@usuario" />
              </label>
              <label>
                <span>Facebook</span>
                <input value={profileFacebook} onChange={(event) => setProfileFacebook(event.target.value)} placeholder="perfil ou página" />
              </label>
              <label>
                <span>Website</span>
                <input value={profileWebsite} onChange={(event) => setProfileWebsite(event.target.value)} placeholder="https://..." />
              </label>
            </div>
            <div className="profile-card-actions">
              <button type="button" className="primary-button" onClick={() => void saveProfile()} disabled={loading}>
                <ClipboardCheck size={16} />
                Salvar perfil
              </button>
            </div>
          </article>
          ) : null}

          {profileSection === "password" ? (
          <article className="panel auth-panel profile-card">
            <div className="profile-section-title">
              <span className="organization-card-icon"><KeyRound size={17} /></span>
              <div>
                <span className="account-eyebrow">Senha</span>
                <h2>Alterar senha</h2>
                <p>Informe a senha atual antes de definir uma nova senha.</p>
              </div>
            </div>
            <div className="profile-form-grid">
              <label>
                <span>Senha atual</span>
                <input value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} type="password" autoComplete="current-password" />
              </label>
              <label>
                <span>Nova senha</span>
                <input value={newPassword} onChange={(event) => setNewPassword(event.target.value)} type="password" autoComplete="new-password" />
              </label>
              <label>
                <span>Confirmar nova senha</span>
                <input value={confirmNewPassword} onChange={(event) => setConfirmNewPassword(event.target.value)} type="password" autoComplete="new-password" />
              </label>
            </div>
            <div className="profile-card-actions">
              <button type="button" className="secondary-button" onClick={() => void savePassword()} disabled={loading || !currentPassword || !newPassword || !confirmNewPassword}>
                <KeyRound size={16} />
                Alterar senha
              </button>
            </div>
          </article>
          ) : null}

          {profileSection === "security" ? (
          <article className="panel auth-panel profile-card">
            <div className="profile-section-title">
              <span className="organization-card-icon"><ShieldCheck size={17} /></span>
              <div>
                <span className="account-eyebrow">Segurança</span>
                <h2>2FA e autenticação reforçada</h2>
                <p>Controles usados para proteger login e ações críticas na impressora.</p>
              </div>
            </div>
            <div className="profile-security-grid">
              <section className="profile-security-block">
                <div className="panel-header-row compact">
                  <div>
                    <h3>2FA</h3>
                    <p>Opcional por usuário e usado como reforço em ações críticas.</p>
                  </div>
                  <span className={`status-pill ${authUser.mfa_enabled ? "active" : ""}`}>{authUser.mfa_enabled ? "ativo" : "inativo"}</span>
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
                      <ShieldCheck size={16} />
                      Ativar 2FA
                    </button>
                  </div>
                ) : (
                  <div className="auth-stack">
                    <button type="button" className="primary-button" onClick={() => void startMfaSetup()} disabled={loading}>
                      <ShieldCheck size={16} />
                      Preparar 2FA
                    </button>
                    {authUser.mfa_enabled ? (
                      <>
                        <label>
                          <span>Código atual</span>
                          <input value={authMfaCode} onChange={(event) => setAuthMfaCode(event.target.value)} inputMode="numeric" />
                        </label>
                        <button type="button" className="secondary-button" onClick={() => void disableMfa()} disabled={loading || !authMfaCode.trim()}>
                          <X size={16} />
                          Desativar
                        </button>
                      </>
                    ) : null}
                  </div>
                )}
              </section>

              <section className="profile-security-block">
                <div className="panel-header-row compact">
                  <div>
                    <h3>Autenticação reforçada</h3>
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
                      <span>Senha atual da conta</span>
                      <input
                        value={stepUpPassword}
                        onChange={(event) => setStepUpPassword(event.target.value)}
                        type="password"
                        autoComplete="current-password"
                        placeholder="Confirme sua senha de login"
                      />
                    </label>
                  )}
                  <button type="button" className="primary-button" onClick={() => void requestStepUp()} disabled={loading || (!stepUpCode.trim() && !stepUpPassword.trim())}>
                    <KeyRound size={16} />
                    Gerar autorização
                  </button>
                  {stepUpResult ? <small>Autorização válida até {formatDateTime(stepUpResult.expires_at)}.</small> : null}
                </div>
              </section>
            </div>
          </article>
          ) : null}
        </div>
      ) : null}

      {accountTab === "organizations" ? (
        <div className={organizationPage === "detail" ? "organization-workspace organization-workspace-detail" : "organization-workspace"}>
          {organizationPage === "list" ? (
          <article className="panel auth-panel organization-directory">
            <div className="panel-header-row">
              <div>
                <span className="account-eyebrow">Organizações</span>
                <h2>Minhas organizações</h2>
                <p>Use a conta individual por padrão. Crie organizações só quando quiser compartilhar impressoras.</p>
              </div>
              <button type="button" className="secondary-button" onClick={() => setOrganizationCreateOpen(true)}>
                <Plus size={16} />
                Nova organização
              </button>
            </div>
            <div className="organization-summary-grid">
              <div>
                <span>Organizações</span>
                <strong>{authUser.organizations.length}</strong>
              </div>
              <div>
                <span>Uso individual</span>
                <strong>ativo</strong>
              </div>
              <div>
                <span>Compartilhamento</span>
                <strong>{authUser.organizations.length ? "disponível" : "opcional"}</strong>
              </div>
            </div>
            <div className="organization-table" role="table" aria-label="Organizações">
              <div className="organization-table-header" role="row">
                <span>Organização</span>
                <span>Membros</span>
                <span>Papel</span>
                <span>Ações</span>
              </div>
              <div className="organization-table-row individual" role="row">
                <div className="organization-card-main">
                  <span className="organization-card-icon">
                    <UserRound size={16} />
                  </span>
                  <div>
                    <strong>Uso individual</strong>
                    <small>Conta própria</small>
                  </div>
                </div>
                <span>1</span>
                <span className="status-pill active">ativo</span>
                <span className="organization-row-actions">
                  <button type="button" className="secondary-button" disabled>
                    <ShieldCheck size={15} />
                    Padrão
                  </button>
                </span>
              </div>
              {authUser.organizations.map((organization) => (
                <div key={organization.id} className={`organization-table-row ${selectedOrganizationId === organization.id ? "active" : ""}`} role="row">
                  <div className="organization-card-main">
                    <span className="organization-card-icon">
                      <Building2 size={16} />
                    </span>
                    <div>
                      <strong>{organization.name}</strong>
                      <small>Organização #{organization.id}</small>
                    </div>
                  </div>
                  <span>-</span>
                  <span className="status-pill">{organization.role}</span>
                  <span className="organization-row-actions">
                    <button type="button" className="secondary-button" onClick={() => void openOrganizationDetail(organization.id)} disabled={loading}>
                      <Users size={15} />
                      Detalhar
                    </button>
                    <button type="button" className="secondary-button" onClick={() => openOrganizationEdit(organization.id, organization.name)} disabled={loading || organization.role !== "owner"}>
                      <Pencil size={15} />
                      Editar
                    </button>
                    <button type="button" className="secondary-button danger-action" onClick={() => void confirmOrganizationDelete(organization.id, organization.name)} disabled={loading || organization.role !== "owner"}>
                      <Trash2 size={15} />
                      Excluir
                    </button>
                  </span>
                </div>
              ))}
            </div>
          </article>
          ) : null}

          {organizationPage === "detail" ? (
          <article className="panel auth-panel organization-detail-panel organization-detail-page">
            <div className="panel-header-row">
              <div className="organization-detail-heading">
                <button type="button" className="icon-button" onClick={() => setOrganizationPage("list")} aria-label="Voltar para organizações">
                  <ArrowLeft size={16} />
                </button>
                <div>
                  <span className="account-eyebrow">Detalhe da organização</span>
                  <h2>{organizationDetail ? organizationDetail.name : "Organização"}</h2>
                  <p>{organizationDetail ? `Organização #${organizationDetail.id} · ${organizationDetail.role}` : "Carregando organização."}</p>
                </div>
              </div>
              {organizationDetail ? (
                <div className="organization-detail-actions">
                  <button type="button" className="secondary-button" onClick={() => openOrganizationEdit(organizationDetail.id, organizationDetail.name)} disabled={loading || !canOwnSelectedOrganization}>
                    <Pencil size={15} />
                    Editar
                  </button>
                  <button type="button" className="secondary-button danger-action" onClick={() => void confirmOrganizationDelete(organizationDetail.id, organizationDetail.name)} disabled={loading || !canOwnSelectedOrganization}>
                    <Trash2 size={15} />
                    Excluir
                  </button>
                </div>
              ) : null}
            </div>
            {organizationDetail ? (
              <div className="auth-stack">
                <div className="organization-summary-grid detail">
                  <div>
                    <span>Membros</span>
                    <strong>{organizationDetail.members.length}</strong>
                  </div>
                  <div>
                    <span>Impressoras</span>
                    <strong>{organizationDetail.printers.length}</strong>
                  </div>
                  <div>
                    <span>Convites</span>
                    <strong>{organizationDetail.invites.length}</strong>
                  </div>
                </div>
                <section className="organization-detail-section organization-data-card">
                  <div className="panel-header-row compact">
                    <div className="organization-section-title">
                      <Users size={17} />
                      <h3>Membros</h3>
                      <span>{organizationDetail.members.length}</span>
                    </div>
                    <button type="button" className="secondary-button" onClick={() => void createAuthOrganizationInvite()} disabled={!canManageSelectedOrganization}>
                      <KeyRound size={15} />
                      Gerar link
                    </button>
                  </div>
                  <div className="organization-data-table members" role="table" aria-label="Membros da organização">
                    <div className="organization-data-header" role="row">
                      <span>Usuário</span>
                      <span>Email</span>
                      <span>Papel</span>
                      <span>Ações</span>
                    </div>
                    {organizationDetail.members.map((member) => (
                      <div key={member.user_id} className="organization-data-row" role="row">
                        <strong>{member.display_name || member.email}</strong>
                        <span>{member.email}</span>
                        <span className="status-pill">{member.role}</span>
                        <span className="organization-row-actions">
                        {member.role !== "owner" && canManageSelectedOrganization ? (
                          <button type="button" className="secondary-button" onClick={() => void removeAuthOrganizationMember(member.user_id)} disabled={loading}>
                            <Trash2 size={15} />
                            Remover
                          </button>
                        ) : null}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>

                {createdOrganizationInvite ? (
                  <section className="auth-step">
                    <div>
                      <strong>Link de convite</strong>
                      <p className="muted">Válido até {formatDateTime(createdOrganizationInvite.expires_at)}.</p>
                      <code>{createdOrganizationInvite.invite_url}</code>
                    </div>
                    <button type="button" className="secondary-button" onClick={() => void copyInviteLink(createdOrganizationInvite.invite_url, showToast)}>
                      <ClipboardCheck size={15} />
                      Copiar
                    </button>
                    <button type="button" className="secondary-button" onClick={() => setCreatedOrganizationInvite(null)}>
                      <X size={15} />
                      Ocultar
                    </button>
                  </section>
                ) : null}

                <section className="organization-detail-section organization-data-card">
                  <div className="panel-header-row compact">
                    <div className="organization-section-title">
                      <Printer size={17} />
                      <h3>Impressoras vinculadas</h3>
                      <span>{organizationDetail.printers.length}</span>
                    </div>
                    {canManageSelectedOrganization ? (
                    <div className="printer-card-actions">
                      <select value={organizationPrinterId} onChange={(event) => setOrganizationPrinterId(event.target.value ? Number(event.target.value) : "")}>
                        <option value="">Selecionar impressora</option>
                        {printers.map((printer) => (
                          <option key={printer.id} value={printer.id}>{printer.name}</option>
                        ))}
                      </select>
                      <button type="button" className="secondary-button" onClick={() => void linkAuthOrganizationPrinter()} disabled={loading || organizationPrinterId === ""}>
                        <Plus size={15} />
                        Vincular
                      </button>
                    </div>
                    ) : null}
                  </div>
                  <div className="organization-data-table printers" role="table" aria-label="Impressoras vinculadas">
                    <div className="organization-data-header" role="row">
                      <span>Impressora</span>
                      <span>Moonraker</span>
                      <span>Vinculada em</span>
                      <span>Ações</span>
                    </div>
                    {organizationDetail.printers.length === 0 ? <span className="organization-empty-row muted">Nenhuma impressora vinculada.</span> : null}
                    {organizationDetail.printers.map((printer) => (
                      <div key={printer.printer_id} className="organization-data-row" role="row">
                        <strong>{printer.name}</strong>
                        <span>{printer.moonraker_url}</span>
                        <span>{formatDateTime(printer.linked_at)}</span>
                        <span className="organization-row-actions">
                        {canManageSelectedOrganization ? (
                        <button type="button" className="secondary-button" onClick={() => void unlinkAuthOrganizationPrinter(printer.printer_id)} disabled={loading}>
                          <Trash2 size={15} />
                          Remover
                        </button>
                        ) : null}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>

                <section className="organization-detail-section organization-data-card">
                  <div className="panel-header-row compact">
                    <div className="organization-section-title">
                      <KeyRound size={17} />
                      <h3>Convites</h3>
                      <span>{organizationDetail.invites.length}</span>
                    </div>
                  </div>
                  <div className="organization-data-table invites" role="table" aria-label="Convites da organização">
                    <div className="organization-data-header" role="row">
                      <span>Token</span>
                      <span>Papel</span>
                      <span>Expiração</span>
                      <span>Status</span>
                      <span>Ações</span>
                    </div>
                    {organizationDetail.invites.length === 0 ? <span className="organization-empty-row muted">Nenhum convite gerado.</span> : null}
                    {organizationDetail.invites.map((invite) => (
                      <div key={invite.id} className="organization-data-row" role="row">
                        <strong>{invite.token_prefix}</strong>
                        <span>{invite.role}</span>
                        <span>{formatDateTime(invite.expires_at)}</span>
                        <span className={`status-pill ${invite.revoked_at ? "danger" : invite.accepted_at ? "active" : ""}`}>{organizationInviteStatus(invite)}</span>
                        <span className="organization-row-actions">
                          {!invite.accepted_at && !invite.revoked_at && canManageSelectedOrganization ? (
                            <button type="button" className="secondary-button danger-action" onClick={() => void confirmInviteRevoke(invite.id, invite.token_prefix)} disabled={loading}>
                              <X size={15} />
                              Cancelar
                            </button>
                          ) : null}
                        </span>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
            ) : null}
          </article>
          ) : null}

          {organizationCreateOpen ? (
            <div className="modal-backdrop" role="presentation">
              <article className="modal-card auth-create-modal" aria-label="Criar organização">
                <div className="modal-header">
                  <div>
                    <h2>Criar organização</h2>
                    <p>Use apenas quando for compartilhar impressoras com outras pessoas.</p>
                  </div>
                  <button type="button" className="icon-button" onClick={() => setOrganizationCreateOpen(false)} aria-label="Fechar">
                    <X size={16} />
                  </button>
                </div>
                <label>
                  <span>Nome da organização</span>
                  <input value={organizationName} onChange={(event) => setOrganizationName(event.target.value)} />
                </label>
                <button type="button" className="primary-button" onClick={() => void createAuthOrganization()} disabled={loading || !organizationName.trim()}>
                  <Plus size={16} />
                  Criar organização
                </button>
              </article>
            </div>
          ) : null}
          {organizationEditOpen ? (
            <div className="modal-backdrop" role="presentation">
              <article className="modal-card auth-create-modal" aria-label="Editar organização">
                <div className="modal-header">
                  <div>
                    <h2>Editar organização</h2>
                    <p>Atualize o nome exibido para membros e convites.</p>
                  </div>
                  <button type="button" className="icon-button" onClick={() => setOrganizationEditOpen(false)} aria-label="Fechar">
                    <X size={16} />
                  </button>
                </div>
                <label>
                  <span>Nome da organização</span>
                  <input value={editingOrganizationName} onChange={(event) => setEditingOrganizationName(event.target.value)} />
                </label>
                <button type="button" className="primary-button" onClick={() => void saveOrganizationEdit()} disabled={loading || !editingOrganizationName.trim()}>
                  <Pencil size={16} />
                  Salvar alterações
                </button>
              </article>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function timezoneOptions(current: string) {
  return Array.from(new Set([current, ...commonTimezones].filter(Boolean)));
}

function readRequestedAccountTab(): AccountTab {
  const requested = (window as Window & { printoraAccountTab?: AccountTab | "security" }).printoraAccountTab;
  if (requested === "security") {
    return "profile";
  }
  return requested && accountTabKeys.includes(requested) ? requested : "organizations";
}

function visibilityLabel(value: ProfileVisibility) {
  if (value === "private") return "privado";
  if (value === "unlisted") return "não listado";
  return "público";
}

function visibilityHelp(value: ProfileVisibility) {
  if (value === "private") return "Perfil não abre publicamente e impressoras não aparecem por URL.";
  if (value === "unlisted") return "Perfil abre por URL direta, mas não deve aparecer em listagens.";
  return "Perfil pode aparecer publicamente e abre pela URL do slug.";
}

function flattenVariants(catalog: CatalogSummary | null): Array<CatalogVariant & { label: string }> {
  if (!catalog) {
    return [];
  }
  return catalog.manufacturers.flatMap((manufacturer) =>
    manufacturer.models.flatMap((model) =>
      model.variants.map((variant) => ({
        ...variant,
        label: `${manufacturer.name} · ${model.name} · ${variant.name}`,
      })),
    ),
  );
}

async function copyInviteLink(inviteUrl: string, showToast: (options: { tone?: "success" | "danger"; title: string; detail?: string }) => void) {
  try {
    await navigator.clipboard.writeText(inviteUrl);
    showToast({ tone: "success", title: "Link copiado" });
  } catch {
    showToast({ tone: "danger", title: "Falha ao copiar link", detail: inviteUrl });
  }
}

function organizationInviteStatus(invite: { accepted_at?: string | null; revoked_at?: string | null }): string {
  if (invite.revoked_at) {
    return "cancelado";
  }
  if (invite.accepted_at) {
    return "aceito";
  }
  return "pendente";
}
