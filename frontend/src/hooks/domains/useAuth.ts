import React from "react";
import * as authApi from "../../services/authApi";
import { getStoredAuthToken, storeAuthToken } from "../../services/http";
import type { AgentCredentialRecord, AgentCredentialResponse, AuthOrganization, AuthUser, MfaSetupResponse, StepUpResponse } from "../../types";

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
    const user = await authApi.loadAuthUser();
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
      if (authMode === "register") {
        const response = await authApi.registerUser({
          email: authEmail,
          password: authPassword,
          display_name: authDisplayName || null,
          whatsapp: authWhatsapp || null,
          telegram: authTelegram || null,
        });
        setAuthUser(response.user);
        setAuthMfaChallengeToken(null);
      } else {
        const response = await authApi.loginUser(authEmail, authPassword);
        if (response.mfa_required && response.challenge_token) {
          setAuthMfaChallengeToken(response.challenge_token);
        } else if (response.user) {
          setAuthUser(response.user);
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
      setAuthUser(response.user);
      setAuthMfaChallengeToken(null);
      setAuthMfaCode("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha no 2FA");
    } finally {
      setLoading(false);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar organização");
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao vincular usuário");
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
    organizationName,
    selectedOrganizationId,
    stepUpCode,
    stepUpPassword,
    stepUpResult,
    addAuthOrganizationMember,
    confirmMfaSetup,
    createAuthAgentCredential,
    createAuthOrganization,
    disableMfa,
    loadAgentCredentials,
    loadAuth,
    logoutAuth,
    requestStepUp,
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
    startMfaSetup,
    submitAuth,
    submitMfaLogin,
  };
}
