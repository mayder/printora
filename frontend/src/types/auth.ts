export type AuthOrganizationRole = "owner" | "admin" | "operator";

export interface AuthOrganization {
  id: number;
  name: string;
  role: AuthOrganizationRole;
  owner_user_id: number;
}

export interface AuthOrganizationMember {
  user_id: number;
  email: string;
  display_name?: string | null;
  role: AuthOrganizationRole;
  created_at: string;
}

export interface AuthOrganizationPrinter {
  printer_id: number;
  name: string;
  moonraker_url: string;
  linked_at: string;
}

export interface AuthOrganizationInvite {
  id: number;
  token_prefix: string;
  role: AuthOrganizationRole;
  invite_url: string;
  expires_at: string;
  accepted_at?: string | null;
  revoked_at?: string | null;
  created_at: string;
}

export interface AuthOrganizationDetail extends AuthOrganization {
  members: AuthOrganizationMember[];
  printers: AuthOrganizationPrinter[];
  invites: AuthOrganizationInvite[];
}

export interface AuthUser {
  id: number;
  email: string;
  display_name?: string | null;
  whatsapp?: string | null;
  telegram?: string | null;
  social_links: Record<string, string | null>;
  timezone: string;
  mfa_enabled: boolean;
  is_active: boolean;
  platform_admin: boolean;
  created_at: string;
  organizations: AuthOrganization[];
}

export interface AuthSessionResponse {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  user: AuthUser;
}

export interface LoginResponse {
  access_token?: string | null;
  token_type: "bearer";
  expires_at?: string | null;
  user?: AuthUser | null;
  mfa_required: boolean;
  challenge_token?: string | null;
}

export interface MfaSetupResponse {
  secret: string;
  otpauth_uri: string;
}

export interface StepUpResponse {
  step_up_token: string;
  expires_at: string;
}

export interface AgentCredentialResponse {
  id: number;
  label: string;
  credential: string;
  credential_prefix: string;
  organization_id?: number | null;
  created_at: string;
}

export interface AgentCredentialRecord {
  id: number;
  label: string;
  credential_prefix: string;
  organization_id?: number | null;
  revoked: boolean;
  created_at: string;
  last_used_at?: string | null;
}
