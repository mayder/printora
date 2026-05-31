import React from "react";
import * as authApi from "../../services/authApi";
import { getStoredAuthToken, storeAuthToken } from "../../services/http";
import type {
  AgentCredentialRecord,
  AgentCredentialResponse,
  AuthOrganizationDetail,
  AuthOrganizationInvite,
  AuthOrganizationRole,
  AuthUser,
  MfaSetupResponse,
  StepUpResponse,
} from "../../types";

interface UseAuthOptions {
  setError: (value: string | null) => void;
  setLoading: (value: boolean) => void;
}

export function useAuth({ setError, setLoading }: UseAuthOptions) {
  const [authUser, setAuthUser] = React.useState<AuthUser | null>(null);
  const [authMode, setAuthMode] = React.useState<"login" | "register">("login");
  const [authEmail, setAuthEmail] = React.useState("");
  const [authPassword, setAuthPassword] = React.useState("");
  const [authDisplayName, setAuthDisplayName] = React.useState("");
  const [authWhatsapp, setAuthWhatsapp] = React.useState("");
  const [authTelegram, setAuthTelegram] = React.useState("");
  const [authMfaChallengeToken, setAuthMfaChallengeToken] = React.useState<string | null>(null);
  const [authMfaCode, setAuthMfaCode] = React.useState("");
  const [mfaSetup, setMfaSetup] = React.useState<MfaSetupResponse | null>(null);
  const [organizationName, setOrganizationName] = React.useState("");
  const [memberEmail, setMemberEmail] = React.useState("");
  const [memberRole, setMemberRole] = React.useState<"admin" | "operator">("operator");
  const [selectedOrganizationId, setSelectedOrganizationId] = React.useState<number | null>(null);
  const [organizationCreateOpen, setOrganizationCreateOpen] = React.useState(false);
  const [organizationDetail, setOrganizationDetail] = React.useState<AuthOrganizationDetail | null>(null);
  const [createdOrganizationInvite, setCreatedOrganizationInvite] = React.useState<AuthOrganizationInvite | null>(null);
  const [organizationPrinterId, setOrganizationPrinterId] = React.useState<number | "">("");
  const [stepUpPassword, setStepUpPassword] = React.useState("");
  const [stepUpCode, setStepUpCode] = React.useState("");
  const [stepUpResult, setStepUpResult] = React.useState<StepUpResponse | null>(null);
  const [agentCredentialLabel, setAgentCredentialLabel] = React.useState("");
  const [agentCredentials, setAgentCredentials] = React.useState<AgentCredentialRecord[]>([]);
  const [createdAgentCredential, setCreatedAgentCredential] = React.useState<AgentCredentialResponse | null>(null);

  async function loadAuth() {
    if (!getStoredAuthToken()) {
      return null;
    }
    let user = await authApi.loadAuthUser();
    if (user) {
      user = await acceptPendingInvite(user);
    }
    setAuthUser(user);
    if (!user) {
      storeAuthToken(null);
    }
    return user;
  }

  async function submitAuth() {
    setLoading(true);
    setError(null);
    try {
      const normalizedEmail = authEmail.trim().toLowerCase();
      if (!isValidEmail(normalizedEmail)) {
        setError("Informe um email válido.");
        return;
      }
      if (authMode === "register") {
        const response = await authApi.registerUser({
          email: normalizedEmail,
          password: authPassword,
          display_name: authDisplayName || null,
          whatsapp: null,
          telegram: null,
        });
        setAuthUser(await acceptPendingInvite(response.user));
        setAuthMfaChallengeToken(null);
      } else {
        const response = await authApi.loginUser(normalizedEmail, authPassword);
        if (response.mfa_required && response.challenge_token) {
          setAuthMfaChallengeToken(response.challenge_token);
        } else if (response.user) {
          setAuthUser(await acceptPendingInvite(response.user));
          setAuthMfaChallengeToken(null);
        }
      }
      setAuthPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na autenticação");
    } finally {
      setLoading(false);
    }
  }

  async function submitMfaLogin() {
    if (!authMfaChallengeToken) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await authApi.completeMfaLogin(authMfaChallengeToken, authMfaCode);
      setAuthUser(await acceptPendingInvite(response.user));
      setAuthMfaChallengeToken(null);
      setAuthMfaCode("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no 2FA");
    } finally {
      setLoading(false);
    }
  }

  async function acceptPendingInvite(user: AuthUser): Promise<AuthUser> {
    const token = new URLSearchParams(window.location.search).get("org_invite");
    if (!token) {
      return user;
    }
    try {
      const organization = await authApi.acceptOrganizationInvite(token);
      const organizations = user.organizations.some((item) => item.id === organization.id)
        ? user.organizations.map((item) => (item.id === organization.id ? organization : item))
        : [...user.organizations, organization];
      window.history.replaceState({}, "", `${window.location.pathname}?section=account`);
      setSelectedOrganizationId(organization.id);
      await loadOrganizationDetail(organization.id);
      return { ...user, organizations };
    } catch {
      return user;
    }
  }

  async function logoutAuth() {
    setLoading(true);
    setError(null);
    try {
      await authApi.logoutUser();
      setAuthUser(null);
      setMfaSetup(null);
      setAgentCredentials([]);
      setCreatedAgentCredential(null);
    } catch {
      storeAuthToken(null);
      setAuthUser(null);
    } finally {
      setLoading(false);
    }
  }

  async function startMfaSetup() {
    setLoading(true);
    setError(null);
    try {
      setMfaSetup(await authApi.setupMfa());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao preparar 2FA");
    } finally {
      setLoading(false);
    }
  }

  async function confirmMfaSetup() {
    setLoading(true);
    setError(null);
    try {
      setAuthUser(await authApi.enableMfa(authMfaCode));
      setAuthMfaCode("");
      setMfaSetup(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao ativar 2FA");
    } finally {
      setLoading(false);
    }
  }

  async function disableMfa() {
    setLoading(true);
    setError(null);
    try {
      setAuthUser(await authApi.disableMfa(authMfaCode));
      setAuthMfaCode("");
      setMfaSetup(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao desativar 2FA");
    } finally {
      setLoading(false);
    }
  }

  async function createAuthOrganization() {
    setLoading(true);
    setError(null);
    try {
      const organization = await authApi.createOrganization(organizationName);
      setAuthUser((current) => current ? { ...current, organizations: [...current.organizations, organization] } : current);
      setSelectedOrganizationId(organization.id);
      setOrganizationName("");
      setOrganizationCreateOpen(false);
      await loadOrganizationDetail(organization.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar organização");
    } finally {
      setLoading(false);
    }
  }

  async function updateAuthOrganization(organizationId: number, name: string) {
    setLoading(true);
    setError(null);
    try {
      const organization = await authApi.updateOrganization(organizationId, name);
      setAuthUser((current) => current ? {
        ...current,
        organizations: current.organizations.map((item) => (item.id === organization.id ? organization : item)),
      } : current);
      if (selectedOrganizationId === organization.id) {
        await loadOrganizationDetail(organization.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao editar organização");
      throw err;
    } finally {
      setLoading(false);
    }
  }

  async function deleteAuthOrganization(organizationId: number) {
    setLoading(true);
    setError(null);
    try {
      await authApi.deleteOrganization(organizationId);
      setAuthUser((current) => current ? {
        ...current,
        organizations: current.organizations.filter((item) => item.id !== organizationId),
      } : current);
      if (selectedOrganizationId === organizationId) {
        setSelectedOrganizationId(null);
        setOrganizationDetail(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir organização");
      throw err;
    } finally {
      setLoading(false);
    }
  }

  async function addAuthOrganizationMember() {
    if (!selectedOrganizationId) {
      setError("Selecione uma organização");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await authApi.addOrganizationMember(selectedOrganizationId, memberEmail, memberRole);
      setMemberEmail("");
      await loadOrganizationDetail(selectedOrganizationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao vincular usuário");
    } finally {
      setLoading(false);
    }
  }

  async function loadOrganizationDetail(organizationId = selectedOrganizationId) {
    if (!organizationId) {
      setOrganizationDetail(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setSelectedOrganizationId(organizationId);
      setOrganizationDetail(await authApi.loadOrganizationDetail(organizationId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar organização");
    } finally {
      setLoading(false);
    }
  }

  async function createAuthOrganizationInvite(role: AuthOrganizationRole = memberRole) {
    if (!selectedOrganizationId) {
      setError("Selecione uma organização");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const invite = await authApi.createOrganizationInvite(selectedOrganizationId, role);
      setCreatedOrganizationInvite(invite);
      await loadOrganizationDetail(selectedOrganizationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao gerar convite");
    } finally {
      setLoading(false);
    }
  }

  async function removeAuthOrganizationMember(userId: number) {
    if (!selectedOrganizationId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await authApi.removeOrganizationMember(selectedOrganizationId, userId);
      await loadOrganizationDetail(selectedOrganizationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao remover usuário");
    } finally {
      setLoading(false);
    }
  }

  async function linkAuthOrganizationPrinter() {
    if (!selectedOrganizationId || organizationPrinterId === "") {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await authApi.linkOrganizationPrinter(selectedOrganizationId, organizationPrinterId);
      setOrganizationPrinterId("");
      await loadOrganizationDetail(selectedOrganizationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao vincular impressora");
    } finally {
      setLoading(false);
    }
  }

  async function unlinkAuthOrganizationPrinter(printerId: number) {
    if (!selectedOrganizationId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await authApi.unlinkOrganizationPrinter(selectedOrganizationId, printerId);
      await loadOrganizationDetail(selectedOrganizationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao remover impressora");
    } finally {
      setLoading(false);
    }
  }

  async function requestStepUp() {
    setLoading(true);
    setError(null);
    try {
      setStepUpResult(await authApi.createStepUpToken({
        purpose: "destructive_action",
        password: stepUpPassword || undefined,
        code: stepUpCode || undefined,
      }));
      setStepUpPassword("");
      setStepUpCode("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha na autenticação reforçada");
    } finally {
      setLoading(false);
    }
  }

  async function loadAgentCredentials() {
    if (!authUser) {
      return;
    }
    setAgentCredentials(await authApi.listAgentCredentials());
  }

  async function createAuthAgentCredential() {
    setLoading(true);
    setError(null);
    try {
      const credential = await authApi.createAgentCredential(agentCredentialLabel, selectedOrganizationId);
      setCreatedAgentCredential(credential);
      setAgentCredentialLabel("");
      await loadAgentCredentials();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar credencial do agente");
    } finally {
      setLoading(false);
    }
  }

  return {
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
    mfaSetup,
    memberEmail,
    memberRole,
    createdOrganizationInvite,
    organizationCreateOpen,
    organizationDetail,
    organizationName,
    organizationPrinterId,
    selectedOrganizationId,
    stepUpCode,
    stepUpPassword,
    stepUpResult,
    addAuthOrganizationMember,
    confirmMfaSetup,
    createAuthAgentCredential,
    createAuthOrganization,
    createAuthOrganizationInvite,
    deleteAuthOrganization,
    disableMfa,
    loadAgentCredentials,
    loadAuth,
    logoutAuth,
    requestStepUp,
    linkAuthOrganizationPrinter,
    loadOrganizationDetail,
    removeAuthOrganizationMember,
    setCreatedOrganizationInvite,
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
    setOrganizationCreateOpen,
    setOrganizationName,
    setOrganizationPrinterId,
    setSelectedOrganizationId,
    setStepUpCode,
    setStepUpPassword,
    startMfaSetup,
    submitAuth,
    submitMfaLogin,
    unlinkAuthOrganizationPrinter,
    updateAuthOrganization,
  };
}

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value);
}
