--
-- PostgreSQL database dump
--

-- Dumped from database version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.14 (Ubuntu 16.14-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

-- *not* creating schema, since initdb creates it


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: agent_credentials; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agent_credentials (
    id bigint NOT NULL,
    organization_id bigint,
    owner_user_id bigint,
    label text,
    credential_hash text,
    credential_prefix text,
    revoked_at text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    last_used_at text
);


--
-- Name: agent_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.agent_jobs (
    id bigint NOT NULL,
    printer_id bigint,
    agent_id bigint,
    correlation_id text,
    job_type text,
    payload_json text DEFAULT '{}'::text,
    status text DEFAULT 'pending'::text,
    attempts bigint DEFAULT '0'::bigint,
    result_json text,
    error_message text,
    available_at text DEFAULT CURRENT_TIMESTAMP,
    expires_at text,
    acked_at text,
    finished_at text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: agent_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.agent_jobs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: agent_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.agent_jobs_id_seq OWNED BY public.agent_jobs.id;


--
-- Name: app_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_events (
    id bigint NOT NULL,
    printer_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    event_type text,
    payload_json text
);


--
-- Name: app_update_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_update_runs (
    id bigint NOT NULL,
    target_version text,
    target_tag text,
    source_url text,
    environment text,
    status text,
    started_at text,
    finished_at text,
    backup_db_path text,
    backup_project_path text,
    previous_project_path text,
    current_project_path text,
    error_message text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    owner_user_id bigint,
    organization_id bigint
);


--
-- Name: app_update_steps; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_update_steps (
    id bigint NOT NULL,
    run_id bigint,
    step_key text,
    title text,
    status text,
    log_excerpt text,
    started_at text,
    finished_at text
);


--
-- Name: app_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_version (
    id bigint NOT NULL,
    app_name text DEFAULT 'Printora'::text,
    version text,
    schema_revision bigint DEFAULT '0'::bigint,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: auth_mfa_challenges; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_mfa_challenges (
    id bigint NOT NULL,
    user_id bigint,
    challenge_hash text,
    expires_at text,
    consumed_at text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: auth_organization_invites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_organization_invites (
    id bigint NOT NULL,
    organization_id bigint,
    created_by_user_id bigint,
    token_hash text,
    token_prefix text,
    role text DEFAULT 'operator'::text,
    expires_at text,
    accepted_by_user_id bigint,
    accepted_at text,
    revoked_at text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: auth_organization_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_organization_members (
    id bigint NOT NULL,
    organization_id bigint,
    user_id bigint,
    role text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: auth_organization_printers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_organization_printers (
    organization_id bigint NOT NULL,
    printer_id bigint NOT NULL,
    linked_by_user_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: auth_organizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_organizations (
    id bigint NOT NULL,
    name text,
    owner_user_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: auth_sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_sessions (
    id bigint NOT NULL,
    user_id bigint,
    token_hash text,
    expires_at text,
    revoked_at text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    last_seen_at text
);


--
-- Name: auth_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auth_sessions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auth_sessions_id_seq OWNED BY public.auth_sessions.id;


--
-- Name: auth_step_up_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_step_up_tokens (
    id bigint NOT NULL,
    user_id bigint,
    token_hash text,
    purpose text,
    expires_at text,
    consumed_at text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: auth_step_up_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auth_step_up_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_step_up_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auth_step_up_tokens_id_seq OWNED BY public.auth_step_up_tokens.id;


--
-- Name: auth_users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.auth_users (
    id bigint NOT NULL,
    email text,
    password_hash text,
    display_name text,
    whatsapp text,
    telegram text,
    social_links_json text DEFAULT '{}'::text,
    mfa_enabled bigint DEFAULT '0'::bigint,
    mfa_secret_protected text,
    is_active bigint DEFAULT '1'::bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    timezone text DEFAULT 'America/Sao_Paulo'::text
);


--
-- Name: auth_users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.auth_users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auth_users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.auth_users_id_seq OWNED BY public.auth_users.id;


--
-- Name: backup_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.backup_policies (
    id bigint NOT NULL,
    printer_id bigint,
    name text,
    source_path text,
    destination_path text,
    include_patterns_json text,
    exclude_patterns_json text,
    dry_run_only bigint DEFAULT '1'::bigint,
    is_active bigint DEFAULT '1'::bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: backup_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.backup_runs (
    id bigint NOT NULL,
    printer_id bigint,
    policy_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    status text,
    dry_run bigint DEFAULT '1'::bigint,
    source_path text,
    destination_path text,
    include_patterns_json text,
    exclude_patterns_json text,
    total_files bigint DEFAULT '0'::bigint,
    total_bytes bigint DEFAULT '0'::bigint,
    message text
);


--
-- Name: calibration_execution_attempts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.calibration_execution_attempts (
    id bigint NOT NULL,
    printer_id bigint,
    test_key text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    status text,
    confirmation_matched bigint DEFAULT '0'::bigint,
    operator_present bigint DEFAULT '0'::bigint,
    gcode_reviewed bigint DEFAULT '0'::bigint,
    connected bigint DEFAULT '0'::bigint,
    printing bigint DEFAULT '0'::bigint,
    print_state text DEFAULT ''::text,
    klipper_state text,
    klippy_state text,
    commands_json text,
    sent_commands_json text,
    result_json text,
    block_reasons_json text,
    message text DEFAULT ''::text
);


--
-- Name: calibration_execution_attempts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.calibration_execution_attempts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: calibration_execution_attempts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.calibration_execution_attempts_id_seq OWNED BY public.calibration_execution_attempts.id;


--
-- Name: calibration_test_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.calibration_test_runs (
    id bigint NOT NULL,
    printer_id bigint,
    test_key text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    result_status text,
    material text DEFAULT ''::text,
    plate_name text DEFAULT ''::text,
    nozzle text DEFAULT ''::text,
    observed_value text DEFAULT ''::text,
    notes text DEFAULT ''::text,
    gcode_reviewed bigint DEFAULT '0'::bigint,
    photo_reference text
);


--
-- Name: calibration_test_runs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.calibration_test_runs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: calibration_test_runs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.calibration_test_runs_id_seq OWNED BY public.calibration_test_runs.id;


--
-- Name: calibration_tests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.calibration_tests (
    id bigint NOT NULL,
    test_key text,
    category text,
    title text,
    objective text,
    source text,
    execution_mode text,
    risk_level text,
    blocked_while_printing bigint DEFAULT '1'::bigint,
    prerequisites_json text,
    gcode_json text,
    success_criteria_json text,
    notes text DEFAULT ''::text,
    sort_order bigint DEFAULT '0'::bigint
);


--
-- Name: calibration_tests_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.calibration_tests_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: calibration_tests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.calibration_tests_id_seq OWNED BY public.calibration_tests.id;


--
-- Name: can_bus_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.can_bus_records (
    id bigint NOT NULL,
    printer_id bigint,
    recorded_at text DEFAULT CURRENT_TIMESTAMP,
    interface_name text DEFAULT 'can0'::text,
    rx_error bigint DEFAULT '0'::bigint,
    tx_error bigint DEFAULT '0'::bigint,
    tx_retries bigint DEFAULT '0'::bigint,
    bus_state text,
    bitrate bigint,
    previous_rx_error bigint,
    previous_tx_error bigint,
    previous_tx_retries bigint,
    delta_rx_error bigint,
    delta_tx_error bigint,
    delta_tx_retries bigint,
    alert_level text DEFAULT 'ok'::text,
    notes text DEFAULT ''::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: catalog_audit_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.catalog_audit_events (
    id bigint NOT NULL,
    entity_type text,
    entity_id bigint,
    action text,
    actor_user_id bigint,
    payload_json text DEFAULT '{}'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: catalog_audit_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.catalog_audit_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: catalog_audit_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.catalog_audit_events_id_seq OWNED BY public.catalog_audit_events.id;


--
-- Name: catalog_manufacturers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.catalog_manufacturers (
    id bigint NOT NULL,
    slug text,
    name text,
    trust_state text DEFAULT 'official'::text,
    source text DEFAULT 'printora_seed'::text,
    created_by_user_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    website_url text,
    repository_url text,
    documentation_url text,
    logo_url text,
    discord_url text,
    reddit_url text,
    summary text
);


--
-- Name: catalog_manufacturers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.catalog_manufacturers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: catalog_manufacturers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.catalog_manufacturers_id_seq OWNED BY public.catalog_manufacturers.id;


--
-- Name: catalog_printer_models; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.catalog_printer_models (
    id bigint NOT NULL,
    manufacturer_id bigint,
    slug text,
    name text,
    kinematics text,
    trust_state text DEFAULT 'official'::text,
    source text DEFAULT 'printora_seed'::text,
    created_by_user_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    website_url text,
    repository_url text,
    documentation_url text,
    bom_url text,
    description text,
    image_url text,
    discord_url text,
    reddit_url text,
    forum_url text,
    curation_notes text,
    detail_json text DEFAULT '{}'::text,
    source_links_json text DEFAULT '{}'::text
);


--
-- Name: catalog_printer_models_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.catalog_printer_models_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: catalog_printer_models_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.catalog_printer_models_id_seq OWNED BY public.catalog_printer_models.id;


--
-- Name: catalog_printer_variants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.catalog_printer_variants (
    id bigint NOT NULL,
    model_id bigint,
    slug text,
    name text,
    build_volume_json text DEFAULT '{}'::text,
    components_json text DEFAULT '{}'::text,
    firmware_family text,
    trust_state text DEFAULT 'official'::text,
    source text DEFAULT 'printora_seed'::text,
    created_by_user_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: catalog_printer_variants_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.catalog_printer_variants_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: catalog_printer_variants_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.catalog_printer_variants_id_seq OWNED BY public.catalog_printer_variants.id;


--
-- Name: external_content_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.external_content_sources (
    id bigint NOT NULL,
    owner_user_id bigint,
    name text,
    base_url text,
    license_policy text DEFAULT ''::text,
    attribution_required bigint DEFAULT '1'::bigint,
    status text DEFAULT 'active'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: external_library_references; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.external_library_references (
    id bigint NOT NULL,
    owner_user_id bigint,
    source_id bigint,
    library_item_id bigint,
    title text,
    external_url text,
    author_name text DEFAULT ''::text,
    license text DEFAULT ''::text,
    attribution_text text DEFAULT ''::text,
    checksum_sha256 text,
    import_mode text,
    duplicate_library_file_id bigint,
    status text DEFAULT 'active'::text,
    metadata_json text DEFAULT '{}'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: firmware_boards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.firmware_boards (
    id bigint NOT NULL,
    printer_id bigint,
    name text,
    preset_id text,
    can_uuid text,
    can_interface text DEFAULT 'can0'::text,
    connection_type text,
    mcu text,
    flash_method text,
    config_file text,
    notes text DEFAULT ''::text,
    is_active bigint DEFAULT '1'::bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: firmware_build_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.firmware_build_runs (
    id bigint NOT NULL,
    printer_id bigint,
    board_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    status text DEFAULT 'dry_run_planned'::text,
    klipper_path text DEFAULT '~/klipper'::text,
    output_dir text,
    config_backup_path text,
    binary_output_path text,
    commands_json text,
    checklist_json text,
    message text DEFAULT ''::text
);


--
-- Name: firmware_flash_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.firmware_flash_runs (
    id bigint NOT NULL,
    printer_id bigint,
    board_id bigint,
    build_run_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    status text DEFAULT 'flash_dry_run_planned'::text,
    flash_method text,
    can_uuid text,
    can_interface text DEFAULT 'can0'::text,
    binary_path text,
    commands_json text,
    checklist_json text,
    message text DEFAULT ''::text
);


--
-- Name: maintenance_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_events (
    id bigint NOT NULL,
    printer_id bigint,
    performed_at text DEFAULT CURRENT_TIMESTAMP,
    event_type text,
    component text,
    title text,
    notes text DEFAULT ''::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    print_hours_at double precision,
    print_hours_read_at text
);


--
-- Name: maintenance_tasks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.maintenance_tasks (
    id bigint NOT NULL,
    printer_id bigint,
    name text,
    component text,
    interval_days bigint DEFAULT '30'::bigint,
    last_done_at text,
    is_active bigint DEFAULT '1'::bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    interval_kind text DEFAULT 'days'::text,
    interval_value double precision,
    last_done_print_hours double precision,
    last_print_hours_read_at text,
    current_print_hours double precision,
    current_print_hours_read_at text,
    current_print_hours_source text,
    is_applicable bigint DEFAULT '1'::bigint,
    not_applicable_at text
);


--
-- Name: maintenance_tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.maintenance_tasks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: maintenance_tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.maintenance_tasks_id_seq OWNED BY public.maintenance_tasks.id;


--
-- Name: operation_action_execution_attempts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.operation_action_execution_attempts (
    id bigint NOT NULL,
    printer_id bigint,
    preview_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    action_id text,
    status text,
    confirmation_matched bigint DEFAULT '0'::bigint,
    executable bigint DEFAULT '0'::bigint,
    would_send_gcode bigint DEFAULT '0'::bigint,
    block_reason text,
    payload_json text
);


--
-- Name: operation_action_execution_attempts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.operation_action_execution_attempts_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: operation_action_execution_attempts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.operation_action_execution_attempts_id_seq OWNED BY public.operation_action_execution_attempts.id;


--
-- Name: operation_action_previews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.operation_action_previews (
    id bigint NOT NULL,
    printer_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    action_id text,
    action_label text,
    safe_mode text,
    executable bigint DEFAULT '0'::bigint,
    would_send_gcode bigint DEFAULT '0'::bigint,
    command_preview_json text,
    blockers_json text,
    payload_json text
);


--
-- Name: operation_action_previews_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.operation_action_previews_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: operation_action_previews_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.operation_action_previews_id_seq OWNED BY public.operation_action_previews.id;


--
-- Name: print_gcode_deliveries; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.print_gcode_deliveries (
    id bigint NOT NULL,
    owner_user_id bigint,
    printer_id bigint,
    slicing_job_id bigint,
    preflight_id bigint,
    remote_agent_job_id bigint,
    rollback_agent_job_id bigint,
    mode text,
    status text,
    remote_filename text,
    gcode_checksum_sha256 text,
    gcode_size_bytes bigint DEFAULT '0'::bigint,
    confirmation_phrase text DEFAULT ''::text,
    confirmation_matched bigint DEFAULT '0'::bigint,
    preflight_snapshot_json text DEFAULT '{}'::text,
    remote_result_json text DEFAULT '{}'::text,
    rollback_result_json text DEFAULT '{}'::text,
    blockers_json text DEFAULT '[]'::text,
    audit_json text DEFAULT '{}'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    completed_at text,
    canceled_at text,
    rolled_back_at text
);


--
-- Name: print_job_feedback; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.print_job_feedback (
    id bigint NOT NULL,
    history_id bigint,
    owner_user_id bigint,
    outcome text,
    visibility text DEFAULT 'private'::text,
    note text DEFAULT ''::text,
    photo_url text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: print_job_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.print_job_history (
    id bigint NOT NULL,
    owner_user_id bigint,
    printer_id bigint,
    slicing_job_id bigint,
    delivery_id bigint,
    library_item_id bigint,
    model_reference text,
    model_version_reference text DEFAULT ''::text,
    profile_reference text,
    quality_reference text DEFAULT ''::text,
    status text,
    visibility text DEFAULT 'private'::text,
    telemetry_json text DEFAULT '{}'::text,
    result_json text DEFAULT '{}'::text,
    retention_days bigint DEFAULT '180'::bigint,
    started_at text,
    completed_at text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: print_preflight_checks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.print_preflight_checks (
    id bigint NOT NULL,
    owner_user_id bigint,
    printer_id bigint,
    slicing_job_id bigint,
    remote_agent_job_id bigint,
    status text,
    local_metadata_json text DEFAULT '{}'::text,
    remote_preflight_json text DEFAULT '{}'::text,
    blockers_json text DEFAULT '[]'::text,
    warnings_json text DEFAULT '[]'::text,
    checklist_json text DEFAULT '[]'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    approved_at text
);


--
-- Name: print_project_community_shares; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.print_project_community_shares (
    id bigint NOT NULL,
    project_id bigint,
    community_id bigint,
    shared_by_user_id bigint,
    status text DEFAULT 'active'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: print_project_files; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.print_project_files (
    id bigint NOT NULL,
    project_id bigint,
    file_kind text,
    file_role text DEFAULT 'printable'::text,
    file_name text,
    external_url text,
    storage_path text,
    size_bytes bigint,
    sha256 text,
    validation_status text DEFAULT 'metadata_only'::text,
    can_slice bigint DEFAULT '0'::bigint,
    analysis_json text DEFAULT '{}'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    quarantine_key text,
    uploaded_size_bytes bigint,
    uploaded_at text,
    rejection_reason text,
    is_primary_preview bigint DEFAULT '0'::bigint
);


--
-- Name: print_project_publication_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.print_project_publication_reviews (
    id bigint NOT NULL,
    project_id bigint,
    reviewer_user_id bigint,
    status text,
    note text DEFAULT ''::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: print_project_saves; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.print_project_saves (
    id bigint NOT NULL,
    owner_user_id bigint,
    project_id bigint,
    save_kind text DEFAULT 'reference'::text,
    status text DEFAULT 'active'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: print_project_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.print_project_versions (
    id bigint NOT NULL,
    project_id bigint,
    version_label text,
    changelog text DEFAULT ''::text,
    project_snapshot_json text DEFAULT '{}'::text,
    files_snapshot_json text DEFAULT '[]'::text,
    created_by_user_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: print_projects; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.print_projects (
    id bigint NOT NULL,
    owner_user_id bigint,
    slug text,
    title text,
    description text DEFAULT ''::text,
    visibility text DEFAULT 'private'::text,
    lifecycle_status text DEFAULT 'draft'::text,
    publication_status text DEFAULT 'draft'::text,
    commercial_class text DEFAULT 'free'::text,
    license text DEFAULT ''::text,
    original_author_name text DEFAULT ''::text,
    attribution_text text DEFAULT ''::text,
    source_url text,
    primary_file_id bigint,
    current_version_id bigint,
    tags_json text DEFAULT '[]'::text,
    metadata_json text DEFAULT '{}'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    price_cents bigint DEFAULT '0'::bigint,
    currency text DEFAULT 'BRL'::text,
    commercial_terms text DEFAULT ''::text,
    promotion_disclosure text DEFAULT ''::text
);


--
-- Name: printer_agent_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.printer_agent_events (
    id bigint NOT NULL,
    printer_id bigint,
    agent_id bigint,
    event_type text,
    status text,
    detail text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: printer_agent_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.printer_agent_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: printer_agent_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.printer_agent_events_id_seq OWNED BY public.printer_agent_events.id;


--
-- Name: printer_agents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.printer_agents (
    id bigint NOT NULL,
    printer_id bigint,
    organization_id bigint,
    owner_user_id bigint,
    stable_id text,
    credential_hash text,
    credential_prefix text,
    agent_version text,
    platform text,
    capabilities_json text DEFAULT '{}'::text,
    status text DEFAULT 'active'::text,
    paired_at text DEFAULT CURRENT_TIMESTAMP,
    last_seen_at text,
    revoked_at text,
    rotated_at text,
    removed_at text
);


--
-- Name: printer_agents_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.printer_agents_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: printer_agents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.printer_agents_id_seq OWNED BY public.printer_agents.id;


--
-- Name: printer_pairing_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.printer_pairing_tokens (
    id bigint NOT NULL,
    printer_id bigint,
    organization_id bigint,
    owner_user_id bigint,
    created_by_user_id bigint,
    token_hash text,
    token_prefix text,
    expires_at text,
    consumed_at text,
    revoked_at text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    removed_at text
);


--
-- Name: printer_pairing_tokens_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.printer_pairing_tokens_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: printer_pairing_tokens_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.printer_pairing_tokens_id_seq OWNED BY public.printer_pairing_tokens.id;


--
-- Name: printer_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.printer_snapshots (
    id bigint NOT NULL,
    printer_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    snapshot_type text,
    payload_json text
);


--
-- Name: printer_ssh_access; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.printer_ssh_access (
    printer_id bigint NOT NULL,
    ssh_host text,
    ssh_port bigint DEFAULT '22'::bigint,
    ssh_username text,
    credential_blob text,
    credential_configured bigint DEFAULT '0'::bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: printers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.printers (
    id bigint NOT NULL,
    name text,
    moonraker_url text,
    host_audit_mode text DEFAULT 'disabled'::text,
    host_audit_ssh_target text,
    location text,
    notes text,
    is_active bigint DEFAULT '1'::bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    owner_user_id bigint,
    organization_id bigint,
    cloud_model text,
    cloud_tags_json text DEFAULT '[]'::text,
    catalog_variant_id bigint,
    public_profile_enabled bigint DEFAULT '0'::bigint,
    public_name text,
    public_description text,
    public_mods_json text DEFAULT '[]'::text,
    public_images_json text DEFAULT '[]'::text
);


--
-- Name: printers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.printers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: printers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.printers_id_seq OWNED BY public.printers.id;


--
-- Name: schema_integrity_checks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_integrity_checks (
    id bigint NOT NULL,
    checked_at text DEFAULT CURRENT_TIMESTAMP,
    schema_revision bigint,
    status text,
    result_json text
);


--
-- Name: schema_integrity_checks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.schema_integrity_checks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: schema_integrity_checks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.schema_integrity_checks_id_seq OWNED BY public.schema_integrity_checks.id;


--
-- Name: schema_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.schema_versions (
    script_name text NOT NULL,
    checksum_sha256 text,
    execution_order bigint,
    applied_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: setup_can_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.setup_can_runs (
    id bigint NOT NULL,
    run_type text,
    status text,
    safe_mode text,
    target_host text,
    target_port bigint,
    target_user text,
    interface_name text,
    bitrate bigint,
    summary_json text,
    plan_json text,
    command_log text,
    error_message text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    owner_user_id bigint,
    organization_id bigint
);


--
-- Name: setup_final_validation_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.setup_final_validation_runs (
    id bigint NOT NULL,
    status text,
    safe_mode text,
    target_host text,
    target_port bigint,
    target_user text,
    interface_name text,
    expected_uuids_json text,
    summary text,
    checks_json text,
    sections_json text,
    report_markdown text,
    error_message text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    owner_user_id bigint,
    organization_id bigint
);


--
-- Name: setup_firmware_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.setup_firmware_runs (
    id bigint NOT NULL,
    run_type text,
    status text,
    safe_mode text,
    target_host text,
    target_port bigint,
    target_user text,
    board_name text,
    board_role text,
    preset_id text,
    can_interface text,
    config_path text,
    artifact_dir text,
    binary_path text,
    config_sha256 text,
    binary_sha256 text,
    uuid_query_json text,
    summary_json text,
    plan_json text,
    command_log text,
    error_message text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    owner_user_id bigint,
    organization_id bigint
);


--
-- Name: setup_flash_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.setup_flash_runs (
    id bigint NOT NULL,
    run_type text,
    status text,
    safe_mode text,
    target_host text,
    target_port bigint,
    target_user text,
    board_name text,
    board_role text,
    flash_method text,
    can_interface text,
    expected_uuid text,
    artifact_path text,
    artifact_sha256 text,
    previous_binary_path text,
    confirmation_phrase text,
    duration_ms bigint,
    summary_json text,
    preflight_json text,
    plan_json text,
    command_log text,
    rollback_json text,
    error_message text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    owner_user_id bigint,
    organization_id bigint
);


--
-- Name: setup_ssh_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.setup_ssh_runs (
    id bigint NOT NULL,
    run_type text,
    status text,
    safe_mode text,
    target_host text,
    target_port bigint,
    target_user text,
    auth_method text,
    summary_json text,
    plan_json text,
    error_message text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    owner_user_id bigint,
    organization_id bigint
);


--
-- Name: slicing_dry_run_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.slicing_dry_run_logs (
    id bigint NOT NULL,
    engine text,
    model_reference text,
    printer_reference text,
    material_reference text,
    quality_reference text,
    status text,
    command_preview_json text DEFAULT '[]'::text,
    warnings_json text DEFAULT '[]'::text,
    sanitized_log text DEFAULT ''::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: slicing_engine_checks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.slicing_engine_checks (
    id bigint NOT NULL,
    engine text,
    configured_path text,
    detected_path text,
    version_text text,
    status text,
    warnings_json text DEFAULT '[]'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: slicing_engine_checks_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.slicing_engine_checks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: slicing_engine_checks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.slicing_engine_checks_id_seq OWNED BY public.slicing_engine_checks.id;


--
-- Name: slicing_job_artifacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.slicing_job_artifacts (
    id bigint NOT NULL,
    job_id bigint,
    artifact_kind text,
    storage_key text,
    checksum_sha256 text,
    size_bytes bigint DEFAULT '0'::bigint,
    payload_json text DEFAULT '{}'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: slicing_jobs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.slicing_jobs (
    id bigint NOT NULL,
    owner_user_id bigint,
    printer_id bigint,
    material_profile_id bigint,
    engine text,
    model_reference text,
    model_version_reference text DEFAULT ''::text,
    model_dimensions_json text DEFAULT '{}'::text,
    quality_reference text,
    status text DEFAULT 'planned'::text,
    compatibility_json text DEFAULT '{}'::text,
    input_json text DEFAULT '{}'::text,
    output_json text DEFAULT '{}'::text,
    error_message text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    completed_at text,
    canceled_at text,
    print_project_id bigint,
    print_project_version_id bigint,
    selected_project_files_json text DEFAULT '[]'::text,
    project_snapshot_json text DEFAULT '{}'::text
);


--
-- Name: social_abuse_signals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_abuse_signals (
    id bigint NOT NULL,
    subject_user_id bigint,
    target_user_id bigint,
    action text,
    reason text,
    severity bigint DEFAULT '1'::bigint,
    status text DEFAULT 'active'::text,
    metadata_json text DEFAULT '{}'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    resolved_at text
);


--
-- Name: social_communities; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_communities (
    id bigint NOT NULL,
    slug text,
    name text,
    scope text,
    manufacturer_id bigint,
    model_id bigint,
    variant_id bigint,
    status text DEFAULT 'active'::text,
    merged_into_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_communities_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.social_communities_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: social_communities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.social_communities_id_seq OWNED BY public.social_communities.id;


--
-- Name: social_community_members; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_community_members (
    id bigint NOT NULL,
    community_id bigint,
    user_id bigint,
    printer_id bigint,
    source text DEFAULT 'public_printer'::text,
    active bigint DEFAULT '1'::bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_content_follows; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_content_follows (
    id bigint NOT NULL,
    user_id bigint,
    entity_type text,
    entity_id bigint,
    muted bigint DEFAULT '0'::bigint,
    digest_enabled bigint DEFAULT '0'::bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_content_tag_links; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_content_tag_links (
    tag_id bigint NOT NULL,
    entity_type text NOT NULL,
    entity_id bigint NOT NULL,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_content_tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_content_tags (
    id bigint NOT NULL,
    slug text,
    label text,
    status text DEFAULT 'active'::text,
    source text DEFAULT 'user'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_content_tags_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.social_content_tags_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: social_content_tags_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.social_content_tags_id_seq OWNED BY public.social_content_tags.id;


--
-- Name: social_discussion_comments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_discussion_comments (
    id bigint NOT NULL,
    feed_item_id bigint,
    author_user_id bigint,
    parent_comment_id bigint,
    body text,
    attachments_json text DEFAULT '[]'::text,
    edit_count bigint DEFAULT '0'::bigint,
    deleted_at text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_discussion_edit_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_discussion_edit_history (
    id bigint NOT NULL,
    target_type text,
    target_id bigint,
    actor_user_id bigint,
    action text,
    previous_json text DEFAULT '{}'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_discussion_reactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_discussion_reactions (
    id bigint NOT NULL,
    target_type text,
    target_id bigint,
    user_id bigint,
    reaction_type text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_feed_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_feed_items (
    id bigint NOT NULL,
    community_id bigint,
    author_user_id bigint,
    content_type text,
    title text,
    body text DEFAULT ''::text,
    component text,
    material text,
    firmware_family text,
    problem_tag text,
    pinned bigint DEFAULT '0'::bigint,
    visibility text DEFAULT 'public'::text,
    source_type text DEFAULT 'community'::text,
    source_id text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    attachments_json text DEFAULT '[]'::text,
    solution_comment_id bigint,
    edit_count bigint DEFAULT '0'::bigint,
    deleted_at text
);


--
-- Name: social_feed_items_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.social_feed_items_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: social_feed_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.social_feed_items_id_seq OWNED BY public.social_feed_items.id;


--
-- Name: social_file_retention_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_file_retention_reviews (
    id bigint NOT NULL,
    owner_user_id bigint,
    requested_by_user_id bigint,
    mode text DEFAULT 'dry_run'::text,
    candidate_count bigint DEFAULT '0'::bigint,
    blocked_count bigint DEFAULT '0'::bigint,
    reclaimable_bytes bigint DEFAULT '0'::bigint,
    result_json text DEFAULT '{}'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_file_storage_policies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_file_storage_policies (
    id bigint NOT NULL,
    scope_type text,
    scope_id bigint,
    quota_bytes bigint,
    retention_days bigint,
    cost_per_gb_month_cents bigint DEFAULT '0'::bigint,
    status text DEFAULT 'active'::text,
    updated_by_user_id bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_file_storage_policies_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.social_file_storage_policies_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: social_file_storage_policies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.social_file_storage_policies_id_seq OWNED BY public.social_file_storage_policies.id;


--
-- Name: social_library_collection_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_library_collection_items (
    collection_id bigint NOT NULL,
    item_id bigint NOT NULL,
    version_id bigint NOT NULL,
    added_by_user_id bigint,
    notes text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_library_collections; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_library_collections (
    id bigint NOT NULL,
    owner_user_id bigint,
    community_id bigint,
    name text,
    description text DEFAULT ''::text,
    visibility text,
    status text DEFAULT 'active'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_library_commercial_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_library_commercial_reviews (
    id bigint NOT NULL,
    item_id bigint,
    reviewer_user_id bigint,
    status text,
    note text DEFAULT ''::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_library_downloads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_library_downloads (
    id bigint NOT NULL,
    item_id bigint,
    user_id bigint,
    anonymous_label text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    version_id bigint
);


--
-- Name: social_library_favorites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_library_favorites (
    user_id bigint NOT NULL,
    item_id bigint NOT NULL,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_library_files; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_library_files (
    id bigint NOT NULL,
    item_id bigint,
    file_kind text,
    file_name text,
    original_url text,
    size_bytes bigint,
    sha256 text,
    validation_status text DEFAULT 'metadata_only'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    storage_key text,
    quarantine_key text,
    uploaded_size_bytes bigint,
    uploaded_at text,
    rejection_reason text,
    deduplicated_from_file_id bigint,
    analysis_json text DEFAULT '{}'::text,
    thumbnail_svg text,
    analyzed_at text
);


--
-- Name: social_library_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_library_items (
    id bigint NOT NULL,
    owner_user_id bigint,
    community_id bigint,
    catalog_variant_id bigint,
    title text,
    description text DEFAULT ''::text,
    visibility text,
    component text,
    version_label text DEFAULT 'v1'::text,
    material_suggestion text,
    supports_required bigint DEFAULT '0'::bigint,
    orientation_notes text,
    license text,
    status text DEFAULT 'active'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    original_author_name text,
    source_url text,
    attribution_text text,
    remix_source_item_id bigint,
    publication_terms_accepted_at text,
    content_class text DEFAULT 'community'::text,
    commercial_status text DEFAULT 'none'::text,
    commercial_metadata_json text DEFAULT '{}'::text,
    promotion_disclosure text DEFAULT ''::text
);


--
-- Name: social_library_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_library_versions (
    id bigint NOT NULL,
    item_id bigint,
    version_label text,
    changelog text DEFAULT ''::text,
    files_snapshot_json text DEFAULT '[]'::text,
    metadata_snapshot_json text DEFAULT '{}'::text,
    created_by_user_id bigint,
    is_current bigint DEFAULT '0'::bigint,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_material_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_material_profiles (
    id bigint NOT NULL,
    owner_user_id bigint,
    printer_id bigint,
    catalog_variant_id bigint,
    community_id bigint,
    linked_library_item_id bigint,
    title text,
    visibility text,
    material_brand text DEFAULT ''::text,
    material_type text,
    nozzle_diameter_mm double precision,
    bed_temperature_c bigint,
    nozzle_temperature_c bigint,
    flow_percent double precision,
    notes text DEFAULT ''::text,
    version_label text DEFAULT 'v1'::text,
    compatibility_json text DEFAULT '{}'::text,
    status text DEFAULT 'active'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_materialization_state; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_materialization_state (
    name text NOT NULL,
    source_signature text,
    refreshed_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_moderation_actions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_moderation_actions (
    id bigint NOT NULL,
    report_id bigint,
    entity_type text,
    entity_id bigint,
    action text,
    previous_state_json text DEFAULT '{}'::text,
    new_state_json text DEFAULT '{}'::text,
    moderator_user_id bigint,
    reason text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_moderation_reports; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_moderation_reports (
    id bigint NOT NULL,
    entity_type text,
    entity_id bigint,
    reporter_user_id bigint,
    reason text,
    detail text DEFAULT ''::text,
    status text DEFAULT 'open'::text,
    assigned_moderator_user_id bigint,
    resolution_note text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    resolved_at text
);


--
-- Name: social_notification_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_notification_preferences (
    user_id bigint NOT NULL,
    notification_type text NOT NULL,
    in_app_enabled bigint DEFAULT '1'::bigint,
    digest_enabled bigint DEFAULT '0'::bigint,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_notifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_notifications (
    id bigint NOT NULL,
    recipient_user_id bigint,
    actor_user_id bigint,
    notification_type text,
    entity_type text,
    entity_id bigint,
    title text,
    body text DEFAULT ''::text,
    action_url text,
    status text DEFAULT 'unread'::text,
    metadata_json text DEFAULT '{}'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    read_at text
);


--
-- Name: social_print_list_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_print_list_items (
    id bigint NOT NULL,
    print_list_id bigint,
    item_id bigint,
    version_id bigint,
    status text DEFAULT 'want_to_print'::text,
    notes text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_print_lists; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_print_lists (
    id bigint NOT NULL,
    owner_user_id bigint,
    printer_id bigint,
    name text,
    status text DEFAULT 'active'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_profile_slug_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_profile_slug_history (
    id bigint NOT NULL,
    user_id bigint,
    slug text,
    replaced_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_profiles (
    user_id bigint NOT NULL,
    slug text,
    display_name text,
    bio text,
    avatar_url text,
    location text,
    social_links_json text DEFAULT '{}'::text,
    visibility text DEFAULT 'public'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_quality_signals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_quality_signals (
    id bigint NOT NULL,
    entity_type text,
    entity_id bigint,
    signal_type text,
    actor_user_id bigint,
    target_user_id bigint,
    source_table text,
    source_id text,
    weight bigint DEFAULT '0'::bigint,
    reason text DEFAULT ''::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_rate_limit_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_rate_limit_events (
    id bigint NOT NULL,
    actor_user_id bigint,
    action text,
    subject_hash text,
    allowed bigint,
    reason text DEFAULT ''::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_rate_limit_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.social_rate_limit_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: social_rate_limit_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.social_rate_limit_events_id_seq OWNED BY public.social_rate_limit_events.id;


--
-- Name: social_relationships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_relationships (
    id bigint NOT NULL,
    actor_user_id bigint,
    target_user_id bigint,
    relation_type text,
    status text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP,
    ended_at text
);


--
-- Name: social_relationships_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.social_relationships_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: social_relationships_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.social_relationships_id_seq OWNED BY public.social_relationships.id;


--
-- Name: social_search_index; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_search_index (
    entity_type text NOT NULL,
    entity_id bigint NOT NULL,
    title text,
    body text DEFAULT ''::text,
    tags_json text DEFAULT '[]'::text,
    community_id bigint,
    catalog_variant_id bigint,
    owner_user_id bigint,
    visibility text DEFAULT 'public'::text,
    popularity_score bigint DEFAULT '0'::bigint,
    source_updated_at text DEFAULT CURRENT_TIMESTAMP,
    indexed_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_slicing_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_slicing_profiles (
    id bigint NOT NULL,
    material_profile_id bigint,
    layer_height_mm double precision,
    speed_mm_s bigint,
    infill_percent bigint,
    supports_enabled bigint DEFAULT '0'::bigint,
    goal text DEFAULT 'quality'::text,
    settings_json text DEFAULT '{}'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_technical_printer_configs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_technical_printer_configs (
    id bigint NOT NULL,
    owner_user_id bigint,
    printer_id bigint,
    catalog_variant_id bigint,
    community_id bigint,
    linked_library_item_id bigint,
    title text,
    visibility text,
    mods_json text DEFAULT '[]'::text,
    components_json text DEFAULT '{}'::text,
    calibrations_json text DEFAULT '{}'::text,
    notes text DEFAULT ''::text,
    status text DEFAULT 'active'::text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_user_reputation_snapshots; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_user_reputation_snapshots (
    user_id bigint NOT NULL,
    contribution_count bigint DEFAULT '0'::bigint,
    reputation_score bigint DEFAULT '0'::bigint,
    breakdown_json text DEFAULT '{}'::text,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: social_user_safety_settings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.social_user_safety_settings (
    user_id bigint NOT NULL,
    profile_discoverable bigint DEFAULT '1'::bigint,
    followers_visibility text DEFAULT 'public'::text,
    messages_from text DEFAULT 'friends'::text,
    allow_content_mentions bigint DEFAULT '1'::bigint,
    allow_download_tracking bigint DEFAULT '1'::bigint,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: update_alert_silences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.update_alert_silences (
    id bigint NOT NULL,
    printer_id bigint,
    component_name text,
    version_key text,
    current_version text,
    remote_version text,
    full_version text,
    reason text,
    created_at text DEFAULT CURRENT_TIMESTAMP,
    updated_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: z_offset_records; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.z_offset_records (
    id bigint NOT NULL,
    printer_id bigint,
    recorded_at text DEFAULT CURRENT_TIMESTAMP,
    plate_name text,
    material text,
    nozzle text DEFAULT 'T0'::text,
    offset_value double precision,
    previous_offset_value double precision,
    delta_value double precision,
    alert_level text DEFAULT 'ok'::text,
    notes text DEFAULT ''::text,
    created_at text DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: agent_jobs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_jobs ALTER COLUMN id SET DEFAULT nextval('public.agent_jobs_id_seq'::regclass);


--
-- Name: auth_sessions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_sessions ALTER COLUMN id SET DEFAULT nextval('public.auth_sessions_id_seq'::regclass);


--
-- Name: auth_step_up_tokens id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_step_up_tokens ALTER COLUMN id SET DEFAULT nextval('public.auth_step_up_tokens_id_seq'::regclass);


--
-- Name: auth_users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_users ALTER COLUMN id SET DEFAULT nextval('public.auth_users_id_seq'::regclass);


--
-- Name: calibration_execution_attempts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_execution_attempts ALTER COLUMN id SET DEFAULT nextval('public.calibration_execution_attempts_id_seq'::regclass);


--
-- Name: calibration_test_runs id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_test_runs ALTER COLUMN id SET DEFAULT nextval('public.calibration_test_runs_id_seq'::regclass);


--
-- Name: calibration_tests id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_tests ALTER COLUMN id SET DEFAULT nextval('public.calibration_tests_id_seq'::regclass);


--
-- Name: catalog_audit_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_audit_events ALTER COLUMN id SET DEFAULT nextval('public.catalog_audit_events_id_seq'::regclass);


--
-- Name: catalog_manufacturers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_manufacturers ALTER COLUMN id SET DEFAULT nextval('public.catalog_manufacturers_id_seq'::regclass);


--
-- Name: catalog_printer_models id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_printer_models ALTER COLUMN id SET DEFAULT nextval('public.catalog_printer_models_id_seq'::regclass);


--
-- Name: catalog_printer_variants id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_printer_variants ALTER COLUMN id SET DEFAULT nextval('public.catalog_printer_variants_id_seq'::regclass);


--
-- Name: maintenance_tasks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_tasks ALTER COLUMN id SET DEFAULT nextval('public.maintenance_tasks_id_seq'::regclass);


--
-- Name: operation_action_execution_attempts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.operation_action_execution_attempts ALTER COLUMN id SET DEFAULT nextval('public.operation_action_execution_attempts_id_seq'::regclass);


--
-- Name: operation_action_previews id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.operation_action_previews ALTER COLUMN id SET DEFAULT nextval('public.operation_action_previews_id_seq'::regclass);


--
-- Name: printer_agent_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_agent_events ALTER COLUMN id SET DEFAULT nextval('public.printer_agent_events_id_seq'::regclass);


--
-- Name: printer_agents id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_agents ALTER COLUMN id SET DEFAULT nextval('public.printer_agents_id_seq'::regclass);


--
-- Name: printer_pairing_tokens id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_pairing_tokens ALTER COLUMN id SET DEFAULT nextval('public.printer_pairing_tokens_id_seq'::regclass);


--
-- Name: printers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printers ALTER COLUMN id SET DEFAULT nextval('public.printers_id_seq'::regclass);


--
-- Name: schema_integrity_checks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_integrity_checks ALTER COLUMN id SET DEFAULT nextval('public.schema_integrity_checks_id_seq'::regclass);


--
-- Name: slicing_engine_checks id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slicing_engine_checks ALTER COLUMN id SET DEFAULT nextval('public.slicing_engine_checks_id_seq'::regclass);


--
-- Name: social_communities id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_communities ALTER COLUMN id SET DEFAULT nextval('public.social_communities_id_seq'::regclass);


--
-- Name: social_content_tags id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_content_tags ALTER COLUMN id SET DEFAULT nextval('public.social_content_tags_id_seq'::regclass);


--
-- Name: social_feed_items id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_feed_items ALTER COLUMN id SET DEFAULT nextval('public.social_feed_items_id_seq'::regclass);


--
-- Name: social_file_storage_policies id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_file_storage_policies ALTER COLUMN id SET DEFAULT nextval('public.social_file_storage_policies_id_seq'::regclass);


--
-- Name: social_rate_limit_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_rate_limit_events ALTER COLUMN id SET DEFAULT nextval('public.social_rate_limit_events_id_seq'::regclass);


--
-- Name: social_relationships id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_relationships ALTER COLUMN id SET DEFAULT nextval('public.social_relationships_id_seq'::regclass);


--
-- Name: schema_versions idx_28422_sqlite_autoindex_schema_versions_1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_versions
    ADD CONSTRAINT idx_28422_sqlite_autoindex_schema_versions_1 PRIMARY KEY (script_name);


--
-- Name: app_version idx_28428_app_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_version
    ADD CONSTRAINT idx_28428_app_version_pkey PRIMARY KEY (id);


--
-- Name: printers idx_28437_printers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printers
    ADD CONSTRAINT idx_28437_printers_pkey PRIMARY KEY (id);


--
-- Name: app_events idx_28451_app_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_events
    ADD CONSTRAINT idx_28451_app_events_pkey PRIMARY KEY (id);


--
-- Name: printer_snapshots idx_28457_printer_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_snapshots
    ADD CONSTRAINT idx_28457_printer_snapshots_pkey PRIMARY KEY (id);


--
-- Name: backup_policies idx_28463_backup_policies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backup_policies
    ADD CONSTRAINT idx_28463_backup_policies_pkey PRIMARY KEY (id);


--
-- Name: backup_runs idx_28472_backup_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backup_runs
    ADD CONSTRAINT idx_28472_backup_runs_pkey PRIMARY KEY (id);


--
-- Name: maintenance_events idx_28481_maintenance_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_events
    ADD CONSTRAINT idx_28481_maintenance_events_pkey PRIMARY KEY (id);


--
-- Name: maintenance_tasks idx_28490_maintenance_tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_tasks
    ADD CONSTRAINT idx_28490_maintenance_tasks_pkey PRIMARY KEY (id);


--
-- Name: z_offset_records idx_28502_z_offset_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.z_offset_records
    ADD CONSTRAINT idx_28502_z_offset_records_pkey PRIMARY KEY (id);


--
-- Name: can_bus_records idx_28512_can_bus_records_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.can_bus_records
    ADD CONSTRAINT idx_28512_can_bus_records_pkey PRIMARY KEY (id);


--
-- Name: firmware_boards idx_28525_firmware_boards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firmware_boards
    ADD CONSTRAINT idx_28525_firmware_boards_pkey PRIMARY KEY (id);


--
-- Name: firmware_build_runs idx_28535_firmware_build_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firmware_build_runs
    ADD CONSTRAINT idx_28535_firmware_build_runs_pkey PRIMARY KEY (id);


--
-- Name: firmware_flash_runs idx_28544_firmware_flash_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firmware_flash_runs
    ADD CONSTRAINT idx_28544_firmware_flash_runs_pkey PRIMARY KEY (id);


--
-- Name: calibration_tests idx_28554_calibration_tests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_tests
    ADD CONSTRAINT idx_28554_calibration_tests_pkey PRIMARY KEY (id);


--
-- Name: calibration_test_runs idx_28564_calibration_test_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_test_runs
    ADD CONSTRAINT idx_28564_calibration_test_runs_pkey PRIMARY KEY (id);


--
-- Name: printer_ssh_access idx_28577_printer_ssh_access_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_ssh_access
    ADD CONSTRAINT idx_28577_printer_ssh_access_pkey PRIMARY KEY (printer_id);


--
-- Name: operation_action_previews idx_28587_operation_action_previews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.operation_action_previews
    ADD CONSTRAINT idx_28587_operation_action_previews_pkey PRIMARY KEY (id);


--
-- Name: operation_action_execution_attempts idx_28597_operation_action_execution_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.operation_action_execution_attempts
    ADD CONSTRAINT idx_28597_operation_action_execution_attempts_pkey PRIMARY KEY (id);


--
-- Name: calibration_execution_attempts idx_28608_calibration_execution_attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_execution_attempts
    ADD CONSTRAINT idx_28608_calibration_execution_attempts_pkey PRIMARY KEY (id);


--
-- Name: schema_integrity_checks idx_28623_schema_integrity_checks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.schema_integrity_checks
    ADD CONSTRAINT idx_28623_schema_integrity_checks_pkey PRIMARY KEY (id);


--
-- Name: app_update_runs idx_28630_app_update_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_update_runs
    ADD CONSTRAINT idx_28630_app_update_runs_pkey PRIMARY KEY (id);


--
-- Name: app_update_steps idx_28636_app_update_steps_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_update_steps
    ADD CONSTRAINT idx_28636_app_update_steps_pkey PRIMARY KEY (id);


--
-- Name: update_alert_silences idx_28641_update_alert_silences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.update_alert_silences
    ADD CONSTRAINT idx_28641_update_alert_silences_pkey PRIMARY KEY (id);


--
-- Name: setup_ssh_runs idx_28648_setup_ssh_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_ssh_runs
    ADD CONSTRAINT idx_28648_setup_ssh_runs_pkey PRIMARY KEY (id);


--
-- Name: setup_can_runs idx_28654_setup_can_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_can_runs
    ADD CONSTRAINT idx_28654_setup_can_runs_pkey PRIMARY KEY (id);


--
-- Name: setup_firmware_runs idx_28660_setup_firmware_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_firmware_runs
    ADD CONSTRAINT idx_28660_setup_firmware_runs_pkey PRIMARY KEY (id);


--
-- Name: setup_flash_runs idx_28666_setup_flash_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_flash_runs
    ADD CONSTRAINT idx_28666_setup_flash_runs_pkey PRIMARY KEY (id);


--
-- Name: setup_final_validation_runs idx_28672_setup_final_validation_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_final_validation_runs
    ADD CONSTRAINT idx_28672_setup_final_validation_runs_pkey PRIMARY KEY (id);


--
-- Name: auth_users idx_28679_auth_users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_users
    ADD CONSTRAINT idx_28679_auth_users_pkey PRIMARY KEY (id);


--
-- Name: auth_organizations idx_28691_auth_organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organizations
    ADD CONSTRAINT idx_28691_auth_organizations_pkey PRIMARY KEY (id);


--
-- Name: auth_organization_members idx_28698_auth_organization_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organization_members
    ADD CONSTRAINT idx_28698_auth_organization_members_pkey PRIMARY KEY (id);


--
-- Name: auth_sessions idx_28706_auth_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT idx_28706_auth_sessions_pkey PRIMARY KEY (id);


--
-- Name: auth_mfa_challenges idx_28713_auth_mfa_challenges_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_mfa_challenges
    ADD CONSTRAINT idx_28713_auth_mfa_challenges_pkey PRIMARY KEY (id);


--
-- Name: auth_step_up_tokens idx_28720_auth_step_up_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_step_up_tokens
    ADD CONSTRAINT idx_28720_auth_step_up_tokens_pkey PRIMARY KEY (id);


--
-- Name: agent_credentials idx_28727_agent_credentials_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_credentials
    ADD CONSTRAINT idx_28727_agent_credentials_pkey PRIMARY KEY (id);


--
-- Name: printer_pairing_tokens idx_28734_printer_pairing_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_pairing_tokens
    ADD CONSTRAINT idx_28734_printer_pairing_tokens_pkey PRIMARY KEY (id);


--
-- Name: printer_agents idx_28742_printer_agents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_agents
    ADD CONSTRAINT idx_28742_printer_agents_pkey PRIMARY KEY (id);


--
-- Name: printer_agent_events idx_28752_printer_agent_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_agent_events
    ADD CONSTRAINT idx_28752_printer_agent_events_pkey PRIMARY KEY (id);


--
-- Name: agent_jobs idx_28760_agent_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_jobs
    ADD CONSTRAINT idx_28760_agent_jobs_pkey PRIMARY KEY (id);


--
-- Name: auth_organization_invites idx_28772_auth_organization_invites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organization_invites
    ADD CONSTRAINT idx_28772_auth_organization_invites_pkey PRIMARY KEY (id);


--
-- Name: auth_organization_printers idx_28779_sqlite_autoindex_auth_organization_printers_1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organization_printers
    ADD CONSTRAINT idx_28779_sqlite_autoindex_auth_organization_printers_1 PRIMARY KEY (organization_id, printer_id);


--
-- Name: catalog_manufacturers idx_28786_catalog_manufacturers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_manufacturers
    ADD CONSTRAINT idx_28786_catalog_manufacturers_pkey PRIMARY KEY (id);


--
-- Name: catalog_printer_models idx_28797_catalog_printer_models_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_printer_models
    ADD CONSTRAINT idx_28797_catalog_printer_models_pkey PRIMARY KEY (id);


--
-- Name: catalog_printer_variants idx_28810_catalog_printer_variants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_printer_variants
    ADD CONSTRAINT idx_28810_catalog_printer_variants_pkey PRIMARY KEY (id);


--
-- Name: catalog_audit_events idx_28823_catalog_audit_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_audit_events
    ADD CONSTRAINT idx_28823_catalog_audit_events_pkey PRIMARY KEY (id);


--
-- Name: social_profiles idx_28831_social_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_profiles
    ADD CONSTRAINT idx_28831_social_profiles_pkey PRIMARY KEY (user_id);


--
-- Name: social_profile_slug_history idx_28840_social_profile_slug_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_profile_slug_history
    ADD CONSTRAINT idx_28840_social_profile_slug_history_pkey PRIMARY KEY (id);


--
-- Name: social_communities idx_28847_social_communities_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_communities
    ADD CONSTRAINT idx_28847_social_communities_pkey PRIMARY KEY (id);


--
-- Name: social_community_members idx_28856_social_community_members_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_community_members
    ADD CONSTRAINT idx_28856_social_community_members_pkey PRIMARY KEY (id);


--
-- Name: social_relationships idx_28866_social_relationships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_relationships
    ADD CONSTRAINT idx_28866_social_relationships_pkey PRIMARY KEY (id);


--
-- Name: social_feed_items idx_28875_social_feed_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_feed_items
    ADD CONSTRAINT idx_28875_social_feed_items_pkey PRIMARY KEY (id);


--
-- Name: social_discussion_comments idx_28889_social_discussion_comments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_discussion_comments
    ADD CONSTRAINT idx_28889_social_discussion_comments_pkey PRIMARY KEY (id);


--
-- Name: social_discussion_reactions idx_28898_social_discussion_reactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_discussion_reactions
    ADD CONSTRAINT idx_28898_social_discussion_reactions_pkey PRIMARY KEY (id);


--
-- Name: social_discussion_edit_history idx_28905_social_discussion_edit_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_discussion_edit_history
    ADD CONSTRAINT idx_28905_social_discussion_edit_history_pkey PRIMARY KEY (id);


--
-- Name: social_library_items idx_28912_social_library_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_items
    ADD CONSTRAINT idx_28912_social_library_items_pkey PRIMARY KEY (id);


--
-- Name: social_library_files idx_28927_social_library_files_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_files
    ADD CONSTRAINT idx_28927_social_library_files_pkey PRIMARY KEY (id);


--
-- Name: social_library_downloads idx_28935_social_library_downloads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_downloads
    ADD CONSTRAINT idx_28935_social_library_downloads_pkey PRIMARY KEY (id);


--
-- Name: social_library_versions idx_28941_social_library_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_versions
    ADD CONSTRAINT idx_28941_social_library_versions_pkey PRIMARY KEY (id);


--
-- Name: social_library_favorites idx_28951_sqlite_autoindex_social_library_favorites_1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_favorites
    ADD CONSTRAINT idx_28951_sqlite_autoindex_social_library_favorites_1 PRIMARY KEY (user_id, item_id);


--
-- Name: social_library_collections idx_28957_social_library_collections_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_collections
    ADD CONSTRAINT idx_28957_social_library_collections_pkey PRIMARY KEY (id);


--
-- Name: social_library_collection_items idx_28966_sqlite_autoindex_social_library_collection_items_1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_collection_items
    ADD CONSTRAINT idx_28966_sqlite_autoindex_social_library_collection_items_1 PRIMARY KEY (collection_id, item_id, version_id);


--
-- Name: social_print_lists idx_28972_social_print_lists_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_print_lists
    ADD CONSTRAINT idx_28972_social_print_lists_pkey PRIMARY KEY (id);


--
-- Name: social_print_list_items idx_28980_social_print_list_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_print_list_items
    ADD CONSTRAINT idx_28980_social_print_list_items_pkey PRIMARY KEY (id);


--
-- Name: social_technical_printer_configs idx_28988_social_technical_printer_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_technical_printer_configs
    ADD CONSTRAINT idx_28988_social_technical_printer_configs_pkey PRIMARY KEY (id);


--
-- Name: social_material_profiles idx_29000_social_material_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_material_profiles
    ADD CONSTRAINT idx_29000_social_material_profiles_pkey PRIMARY KEY (id);


--
-- Name: social_slicing_profiles idx_29012_social_slicing_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_slicing_profiles
    ADD CONSTRAINT idx_29012_social_slicing_profiles_pkey PRIMARY KEY (id);


--
-- Name: social_content_tags idx_29023_social_content_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_content_tags
    ADD CONSTRAINT idx_29023_social_content_tags_pkey PRIMARY KEY (id);


--
-- Name: social_content_tag_links idx_29033_sqlite_autoindex_social_content_tag_links_1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_content_tag_links
    ADD CONSTRAINT idx_29033_sqlite_autoindex_social_content_tag_links_1 PRIMARY KEY (tag_id, entity_type, entity_id);


--
-- Name: social_search_index idx_29039_sqlite_autoindex_social_search_index_1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_search_index
    ADD CONSTRAINT idx_29039_sqlite_autoindex_social_search_index_1 PRIMARY KEY (entity_type, entity_id);


--
-- Name: social_quality_signals idx_29050_social_quality_signals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_quality_signals
    ADD CONSTRAINT idx_29050_social_quality_signals_pkey PRIMARY KEY (id);


--
-- Name: social_user_reputation_snapshots idx_29058_social_user_reputation_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_user_reputation_snapshots
    ADD CONSTRAINT idx_29058_social_user_reputation_snapshots_pkey PRIMARY KEY (user_id);


--
-- Name: social_materialization_state idx_29067_sqlite_autoindex_social_materialization_state_1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_materialization_state
    ADD CONSTRAINT idx_29067_sqlite_autoindex_social_materialization_state_1 PRIMARY KEY (name);


--
-- Name: social_moderation_reports idx_29073_social_moderation_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_moderation_reports
    ADD CONSTRAINT idx_29073_social_moderation_reports_pkey PRIMARY KEY (id);


--
-- Name: social_moderation_actions idx_29082_social_moderation_actions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_moderation_actions
    ADD CONSTRAINT idx_29082_social_moderation_actions_pkey PRIMARY KEY (id);


--
-- Name: social_notifications idx_29090_social_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_notifications
    ADD CONSTRAINT idx_29090_social_notifications_pkey PRIMARY KEY (id);


--
-- Name: social_notification_preferences idx_29099_sqlite_autoindex_social_notification_preferences_1; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_notification_preferences
    ADD CONSTRAINT idx_29099_sqlite_autoindex_social_notification_preferences_1 PRIMARY KEY (user_id, notification_type);


--
-- Name: social_content_follows idx_29107_social_content_follows_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_content_follows
    ADD CONSTRAINT idx_29107_social_content_follows_pkey PRIMARY KEY (id);


--
-- Name: social_user_safety_settings idx_29116_social_user_safety_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_user_safety_settings
    ADD CONSTRAINT idx_29116_social_user_safety_settings_pkey PRIMARY KEY (user_id);


--
-- Name: social_rate_limit_events idx_29128_social_rate_limit_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_rate_limit_events
    ADD CONSTRAINT idx_29128_social_rate_limit_events_pkey PRIMARY KEY (id);


--
-- Name: social_abuse_signals idx_29136_social_abuse_signals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_abuse_signals
    ADD CONSTRAINT idx_29136_social_abuse_signals_pkey PRIMARY KEY (id);


--
-- Name: social_file_storage_policies idx_29147_social_file_storage_policies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_file_storage_policies
    ADD CONSTRAINT idx_29147_social_file_storage_policies_pkey PRIMARY KEY (id);


--
-- Name: social_file_retention_reviews idx_29157_social_file_retention_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_file_retention_reviews
    ADD CONSTRAINT idx_29157_social_file_retention_reviews_pkey PRIMARY KEY (id);


--
-- Name: slicing_engine_checks idx_29169_slicing_engine_checks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slicing_engine_checks
    ADD CONSTRAINT idx_29169_slicing_engine_checks_pkey PRIMARY KEY (id);


--
-- Name: slicing_dry_run_logs idx_29177_slicing_dry_run_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slicing_dry_run_logs
    ADD CONSTRAINT idx_29177_slicing_dry_run_logs_pkey PRIMARY KEY (id);


--
-- Name: slicing_jobs idx_29186_slicing_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slicing_jobs
    ADD CONSTRAINT idx_29186_slicing_jobs_pkey PRIMARY KEY (id);


--
-- Name: slicing_job_artifacts idx_29201_slicing_job_artifacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slicing_job_artifacts
    ADD CONSTRAINT idx_29201_slicing_job_artifacts_pkey PRIMARY KEY (id);


--
-- Name: print_preflight_checks idx_29209_print_preflight_checks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_preflight_checks
    ADD CONSTRAINT idx_29209_print_preflight_checks_pkey PRIMARY KEY (id);


--
-- Name: print_gcode_deliveries idx_29221_print_gcode_deliveries_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_gcode_deliveries
    ADD CONSTRAINT idx_29221_print_gcode_deliveries_pkey PRIMARY KEY (id);


--
-- Name: print_job_history idx_29236_print_job_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_job_history
    ADD CONSTRAINT idx_29236_print_job_history_pkey PRIMARY KEY (id);


--
-- Name: print_job_feedback idx_29249_print_job_feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_job_feedback
    ADD CONSTRAINT idx_29249_print_job_feedback_pkey PRIMARY KEY (id);


--
-- Name: social_library_commercial_reviews idx_29258_social_library_commercial_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_commercial_reviews
    ADD CONSTRAINT idx_29258_social_library_commercial_reviews_pkey PRIMARY KEY (id);


--
-- Name: external_content_sources idx_29265_external_content_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_content_sources
    ADD CONSTRAINT idx_29265_external_content_sources_pkey PRIMARY KEY (id);


--
-- Name: external_library_references idx_29275_external_library_references_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_library_references
    ADD CONSTRAINT idx_29275_external_library_references_pkey PRIMARY KEY (id);


--
-- Name: print_projects idx_29287_print_projects_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_projects
    ADD CONSTRAINT idx_29287_print_projects_pkey PRIMARY KEY (id);


--
-- Name: print_project_files idx_29308_print_project_files_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_files
    ADD CONSTRAINT idx_29308_print_project_files_pkey PRIMARY KEY (id);


--
-- Name: print_project_versions idx_29319_print_project_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_versions
    ADD CONSTRAINT idx_29319_print_project_versions_pkey PRIMARY KEY (id);


--
-- Name: print_project_community_shares idx_29328_print_project_community_shares_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_community_shares
    ADD CONSTRAINT idx_29328_print_project_community_shares_pkey PRIMARY KEY (id);


--
-- Name: print_project_saves idx_29336_print_project_saves_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_saves
    ADD CONSTRAINT idx_29336_print_project_saves_pkey PRIMARY KEY (id);


--
-- Name: print_project_publication_reviews idx_29345_print_project_publication_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_publication_reviews
    ADD CONSTRAINT idx_29345_print_project_publication_reviews_pkey PRIMARY KEY (id);


--
-- Name: idx_28422_idx_schema_versions_execution_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28422_idx_schema_versions_execution_order ON public.schema_versions USING btree (execution_order);


--
-- Name: idx_28437_idx_printers_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28437_idx_printers_active ON public.printers USING btree (is_active);


--
-- Name: idx_28437_idx_printers_catalog_variant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28437_idx_printers_catalog_variant ON public.printers USING btree (catalog_variant_id);


--
-- Name: idx_28437_idx_printers_organization; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28437_idx_printers_organization ON public.printers USING btree (organization_id);


--
-- Name: idx_28437_idx_printers_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28437_idx_printers_owner ON public.printers USING btree (owner_user_id);


--
-- Name: idx_28437_idx_printers_public; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28437_idx_printers_public ON public.printers USING btree (public_profile_enabled, catalog_variant_id);


--
-- Name: idx_28437_sqlite_autoindex_printers_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28437_sqlite_autoindex_printers_1 ON public.printers USING btree (name);


--
-- Name: idx_28451_idx_app_events_printer_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28451_idx_app_events_printer_created ON public.app_events USING btree (printer_id, created_at);


--
-- Name: idx_28457_idx_printer_snapshots_printer_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28457_idx_printer_snapshots_printer_created ON public.printer_snapshots USING btree (printer_id, created_at);


--
-- Name: idx_28463_idx_backup_policies_printer_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28463_idx_backup_policies_printer_active ON public.backup_policies USING btree (printer_id, is_active);


--
-- Name: idx_28463_sqlite_autoindex_backup_policies_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28463_sqlite_autoindex_backup_policies_1 ON public.backup_policies USING btree (printer_id, name);


--
-- Name: idx_28472_idx_backup_runs_printer_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28472_idx_backup_runs_printer_created ON public.backup_runs USING btree (printer_id, created_at);


--
-- Name: idx_28481_idx_maintenance_events_printer_performed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28481_idx_maintenance_events_printer_performed ON public.maintenance_events USING btree (printer_id, performed_at);


--
-- Name: idx_28490_idx_maintenance_tasks_interval_kind; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28490_idx_maintenance_tasks_interval_kind ON public.maintenance_tasks USING btree (printer_id, interval_kind, is_active);


--
-- Name: idx_28490_idx_maintenance_tasks_printer_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28490_idx_maintenance_tasks_printer_active ON public.maintenance_tasks USING btree (printer_id, is_active);


--
-- Name: idx_28490_idx_maintenance_tasks_printer_applicable; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28490_idx_maintenance_tasks_printer_applicable ON public.maintenance_tasks USING btree (printer_id, is_applicable);


--
-- Name: idx_28490_sqlite_autoindex_maintenance_tasks_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28490_sqlite_autoindex_maintenance_tasks_1 ON public.maintenance_tasks USING btree (printer_id, name);


--
-- Name: idx_28502_idx_z_offset_records_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28502_idx_z_offset_records_lookup ON public.z_offset_records USING btree (printer_id, plate_name, material, nozzle, recorded_at);


--
-- Name: idx_28502_idx_z_offset_records_printer_recorded; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28502_idx_z_offset_records_printer_recorded ON public.z_offset_records USING btree (printer_id, recorded_at);


--
-- Name: idx_28512_idx_can_bus_records_lookup; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28512_idx_can_bus_records_lookup ON public.can_bus_records USING btree (printer_id, interface_name, recorded_at);


--
-- Name: idx_28512_idx_can_bus_records_printer_recorded; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28512_idx_can_bus_records_printer_recorded ON public.can_bus_records USING btree (printer_id, recorded_at);


--
-- Name: idx_28525_idx_firmware_boards_preset; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28525_idx_firmware_boards_preset ON public.firmware_boards USING btree (preset_id);


--
-- Name: idx_28525_idx_firmware_boards_printer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28525_idx_firmware_boards_printer ON public.firmware_boards USING btree (printer_id, is_active, name);


--
-- Name: idx_28525_sqlite_autoindex_firmware_boards_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28525_sqlite_autoindex_firmware_boards_1 ON public.firmware_boards USING btree (printer_id, name);


--
-- Name: idx_28535_idx_firmware_build_runs_board_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28535_idx_firmware_build_runs_board_created ON public.firmware_build_runs USING btree (board_id, created_at);


--
-- Name: idx_28535_idx_firmware_build_runs_printer_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28535_idx_firmware_build_runs_printer_created ON public.firmware_build_runs USING btree (printer_id, created_at);


--
-- Name: idx_28544_idx_firmware_flash_runs_board_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28544_idx_firmware_flash_runs_board_created ON public.firmware_flash_runs USING btree (board_id, created_at);


--
-- Name: idx_28544_idx_firmware_flash_runs_printer_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28544_idx_firmware_flash_runs_printer_created ON public.firmware_flash_runs USING btree (printer_id, created_at);


--
-- Name: idx_28554_idx_calibration_tests_category_sort; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28554_idx_calibration_tests_category_sort ON public.calibration_tests USING btree (category, sort_order);


--
-- Name: idx_28554_sqlite_autoindex_calibration_tests_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28554_sqlite_autoindex_calibration_tests_1 ON public.calibration_tests USING btree (test_key);


--
-- Name: idx_28564_idx_calibration_test_runs_printer_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28564_idx_calibration_test_runs_printer_created ON public.calibration_test_runs USING btree (printer_id, created_at);


--
-- Name: idx_28564_idx_calibration_test_runs_test_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28564_idx_calibration_test_runs_test_created ON public.calibration_test_runs USING btree (test_key, created_at);


--
-- Name: idx_28587_idx_operation_action_previews_printer_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28587_idx_operation_action_previews_printer_created ON public.operation_action_previews USING btree (printer_id, created_at);


--
-- Name: idx_28597_idx_operation_action_execution_attempts_preview; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28597_idx_operation_action_execution_attempts_preview ON public.operation_action_execution_attempts USING btree (preview_id);


--
-- Name: idx_28597_idx_operation_action_execution_attempts_printer_creat; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28597_idx_operation_action_execution_attempts_printer_creat ON public.operation_action_execution_attempts USING btree (printer_id, created_at);


--
-- Name: idx_28608_idx_calibration_execution_attempts_printer_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28608_idx_calibration_execution_attempts_printer_created ON public.calibration_execution_attempts USING btree (printer_id, created_at);


--
-- Name: idx_28623_idx_schema_integrity_checks_checked; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28623_idx_schema_integrity_checks_checked ON public.schema_integrity_checks USING btree (checked_at);


--
-- Name: idx_28630_idx_app_update_runs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28630_idx_app_update_runs_created_at ON public.app_update_runs USING btree (created_at);


--
-- Name: idx_28630_idx_app_update_runs_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28630_idx_app_update_runs_owner ON public.app_update_runs USING btree (owner_user_id);


--
-- Name: idx_28630_idx_app_update_runs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28630_idx_app_update_runs_status ON public.app_update_runs USING btree (status);


--
-- Name: idx_28636_idx_app_update_steps_run_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28636_idx_app_update_steps_run_id ON public.app_update_steps USING btree (run_id);


--
-- Name: idx_28636_idx_app_update_steps_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28636_idx_app_update_steps_status ON public.app_update_steps USING btree (status);


--
-- Name: idx_28641_idx_update_alert_silences_printer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28641_idx_update_alert_silences_printer ON public.update_alert_silences USING btree (printer_id, component_name);


--
-- Name: idx_28641_sqlite_autoindex_update_alert_silences_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28641_sqlite_autoindex_update_alert_silences_1 ON public.update_alert_silences USING btree (printer_id, component_name, version_key);


--
-- Name: idx_28648_idx_setup_ssh_runs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28648_idx_setup_ssh_runs_created_at ON public.setup_ssh_runs USING btree (created_at);


--
-- Name: idx_28648_idx_setup_ssh_runs_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28648_idx_setup_ssh_runs_owner ON public.setup_ssh_runs USING btree (owner_user_id);


--
-- Name: idx_28648_idx_setup_ssh_runs_run_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28648_idx_setup_ssh_runs_run_type ON public.setup_ssh_runs USING btree (run_type);


--
-- Name: idx_28654_idx_setup_can_runs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28654_idx_setup_can_runs_created_at ON public.setup_can_runs USING btree (created_at);


--
-- Name: idx_28654_idx_setup_can_runs_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28654_idx_setup_can_runs_owner ON public.setup_can_runs USING btree (owner_user_id);


--
-- Name: idx_28654_idx_setup_can_runs_run_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28654_idx_setup_can_runs_run_type ON public.setup_can_runs USING btree (run_type);


--
-- Name: idx_28660_idx_setup_firmware_runs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28660_idx_setup_firmware_runs_created_at ON public.setup_firmware_runs USING btree (created_at);


--
-- Name: idx_28660_idx_setup_firmware_runs_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28660_idx_setup_firmware_runs_owner ON public.setup_firmware_runs USING btree (owner_user_id);


--
-- Name: idx_28660_idx_setup_firmware_runs_preset; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28660_idx_setup_firmware_runs_preset ON public.setup_firmware_runs USING btree (preset_id);


--
-- Name: idx_28666_idx_setup_flash_runs_board; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28666_idx_setup_flash_runs_board ON public.setup_flash_runs USING btree (board_name, flash_method);


--
-- Name: idx_28666_idx_setup_flash_runs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28666_idx_setup_flash_runs_created_at ON public.setup_flash_runs USING btree (created_at);


--
-- Name: idx_28666_idx_setup_flash_runs_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28666_idx_setup_flash_runs_owner ON public.setup_flash_runs USING btree (owner_user_id);


--
-- Name: idx_28672_idx_setup_final_validation_runs_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28672_idx_setup_final_validation_runs_created_at ON public.setup_final_validation_runs USING btree (created_at);


--
-- Name: idx_28672_idx_setup_final_validation_runs_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28672_idx_setup_final_validation_runs_owner ON public.setup_final_validation_runs USING btree (owner_user_id);


--
-- Name: idx_28679_idx_auth_users_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28679_idx_auth_users_email ON public.auth_users USING btree (email);


--
-- Name: idx_28679_sqlite_autoindex_auth_users_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28679_sqlite_autoindex_auth_users_1 ON public.auth_users USING btree (email);


--
-- Name: idx_28698_idx_auth_members_org; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28698_idx_auth_members_org ON public.auth_organization_members USING btree (organization_id);


--
-- Name: idx_28698_idx_auth_members_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28698_idx_auth_members_user ON public.auth_organization_members USING btree (user_id);


--
-- Name: idx_28698_sqlite_autoindex_auth_organization_members_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28698_sqlite_autoindex_auth_organization_members_1 ON public.auth_organization_members USING btree (organization_id, user_id);


--
-- Name: idx_28706_idx_auth_sessions_user_expires; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28706_idx_auth_sessions_user_expires ON public.auth_sessions USING btree (user_id, expires_at);


--
-- Name: idx_28706_sqlite_autoindex_auth_sessions_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28706_sqlite_autoindex_auth_sessions_1 ON public.auth_sessions USING btree (token_hash);


--
-- Name: idx_28713_sqlite_autoindex_auth_mfa_challenges_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28713_sqlite_autoindex_auth_mfa_challenges_1 ON public.auth_mfa_challenges USING btree (challenge_hash);


--
-- Name: idx_28720_sqlite_autoindex_auth_step_up_tokens_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28720_sqlite_autoindex_auth_step_up_tokens_1 ON public.auth_step_up_tokens USING btree (token_hash);


--
-- Name: idx_28727_idx_agent_credentials_org; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28727_idx_agent_credentials_org ON public.agent_credentials USING btree (organization_id);


--
-- Name: idx_28727_idx_agent_credentials_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28727_idx_agent_credentials_owner ON public.agent_credentials USING btree (owner_user_id);


--
-- Name: idx_28727_sqlite_autoindex_agent_credentials_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28727_sqlite_autoindex_agent_credentials_1 ON public.agent_credentials USING btree (credential_hash);


--
-- Name: idx_28734_idx_pairing_tokens_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28734_idx_pairing_tokens_hash ON public.printer_pairing_tokens USING btree (token_hash);


--
-- Name: idx_28734_idx_pairing_tokens_printer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28734_idx_pairing_tokens_printer ON public.printer_pairing_tokens USING btree (printer_id, created_at);


--
-- Name: idx_28734_sqlite_autoindex_printer_pairing_tokens_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28734_sqlite_autoindex_printer_pairing_tokens_1 ON public.printer_pairing_tokens USING btree (token_hash);


--
-- Name: idx_28742_idx_printer_agents_credential; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28742_idx_printer_agents_credential ON public.printer_agents USING btree (credential_hash);


--
-- Name: idx_28742_idx_printer_agents_printer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28742_idx_printer_agents_printer ON public.printer_agents USING btree (printer_id, status);


--
-- Name: idx_28742_sqlite_autoindex_printer_agents_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28742_sqlite_autoindex_printer_agents_1 ON public.printer_agents USING btree (stable_id);


--
-- Name: idx_28742_sqlite_autoindex_printer_agents_2; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28742_sqlite_autoindex_printer_agents_2 ON public.printer_agents USING btree (credential_hash);


--
-- Name: idx_28752_idx_printer_agent_events_printer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28752_idx_printer_agent_events_printer ON public.printer_agent_events USING btree (printer_id, created_at);


--
-- Name: idx_28760_idx_agent_jobs_agent_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28760_idx_agent_jobs_agent_status ON public.agent_jobs USING btree (agent_id, status, available_at);


--
-- Name: idx_28760_idx_agent_jobs_correlation; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28760_idx_agent_jobs_correlation ON public.agent_jobs USING btree (correlation_id);


--
-- Name: idx_28760_idx_agent_jobs_printer_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28760_idx_agent_jobs_printer_status ON public.agent_jobs USING btree (printer_id, status, available_at);


--
-- Name: idx_28760_sqlite_autoindex_agent_jobs_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28760_sqlite_autoindex_agent_jobs_1 ON public.agent_jobs USING btree (correlation_id);


--
-- Name: idx_28772_idx_auth_org_invites_hash; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28772_idx_auth_org_invites_hash ON public.auth_organization_invites USING btree (token_hash);


--
-- Name: idx_28772_idx_auth_org_invites_org; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28772_idx_auth_org_invites_org ON public.auth_organization_invites USING btree (organization_id, created_at);


--
-- Name: idx_28772_sqlite_autoindex_auth_organization_invites_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28772_sqlite_autoindex_auth_organization_invites_1 ON public.auth_organization_invites USING btree (token_hash);


--
-- Name: idx_28779_idx_auth_org_printers_printer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28779_idx_auth_org_printers_printer ON public.auth_organization_printers USING btree (printer_id);


--
-- Name: idx_28786_sqlite_autoindex_catalog_manufacturers_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28786_sqlite_autoindex_catalog_manufacturers_1 ON public.catalog_manufacturers USING btree (slug);


--
-- Name: idx_28797_idx_catalog_models_manufacturer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28797_idx_catalog_models_manufacturer ON public.catalog_printer_models USING btree (manufacturer_id);


--
-- Name: idx_28797_sqlite_autoindex_catalog_printer_models_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28797_sqlite_autoindex_catalog_printer_models_1 ON public.catalog_printer_models USING btree (manufacturer_id, slug);


--
-- Name: idx_28810_idx_catalog_variants_model; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28810_idx_catalog_variants_model ON public.catalog_printer_variants USING btree (model_id);


--
-- Name: idx_28810_sqlite_autoindex_catalog_printer_variants_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28810_sqlite_autoindex_catalog_printer_variants_1 ON public.catalog_printer_variants USING btree (model_id, slug);


--
-- Name: idx_28831_idx_social_profiles_visibility; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28831_idx_social_profiles_visibility ON public.social_profiles USING btree (visibility);


--
-- Name: idx_28831_sqlite_autoindex_social_profiles_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28831_sqlite_autoindex_social_profiles_1 ON public.social_profiles USING btree (slug);


--
-- Name: idx_28840_sqlite_autoindex_social_profile_slug_history_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28840_sqlite_autoindex_social_profile_slug_history_1 ON public.social_profile_slug_history USING btree (slug);


--
-- Name: idx_28847_sqlite_autoindex_social_communities_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28847_sqlite_autoindex_social_communities_1 ON public.social_communities USING btree (slug);


--
-- Name: idx_28856_idx_social_community_members_user; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28856_idx_social_community_members_user ON public.social_community_members USING btree (user_id, active);


--
-- Name: idx_28856_sqlite_autoindex_social_community_members_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28856_sqlite_autoindex_social_community_members_1 ON public.social_community_members USING btree (community_id, user_id, printer_id);


--
-- Name: idx_28866_idx_social_relationships_actor; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28866_idx_social_relationships_actor ON public.social_relationships USING btree (actor_user_id, relation_type, status);


--
-- Name: idx_28866_idx_social_relationships_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28866_idx_social_relationships_target ON public.social_relationships USING btree (target_user_id, relation_type, status);


--
-- Name: idx_28866_sqlite_autoindex_social_relationships_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28866_sqlite_autoindex_social_relationships_1 ON public.social_relationships USING btree (actor_user_id, target_user_id, relation_type);


--
-- Name: idx_28875_idx_social_feed_items_community_public; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28875_idx_social_feed_items_community_public ON public.social_feed_items USING btree (community_id, visibility, pinned, created_at);


--
-- Name: idx_28875_idx_social_feed_items_filters; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28875_idx_social_feed_items_filters ON public.social_feed_items USING btree (component, material, firmware_family, problem_tag);


--
-- Name: idx_28875_idx_social_feed_items_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28875_idx_social_feed_items_type ON public.social_feed_items USING btree (content_type);


--
-- Name: idx_28875_sqlite_autoindex_social_feed_items_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28875_sqlite_autoindex_social_feed_items_1 ON public.social_feed_items USING btree (source_type, source_id);


--
-- Name: idx_28889_idx_social_comments_feed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28889_idx_social_comments_feed ON public.social_discussion_comments USING btree (feed_item_id, parent_comment_id, deleted_at, created_at);


--
-- Name: idx_28898_idx_social_reactions_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28898_idx_social_reactions_target ON public.social_discussion_reactions USING btree (target_type, target_id, reaction_type);


--
-- Name: idx_28898_sqlite_autoindex_social_discussion_reactions_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28898_sqlite_autoindex_social_discussion_reactions_1 ON public.social_discussion_reactions USING btree (target_type, target_id, user_id, reaction_type);


--
-- Name: idx_28905_idx_social_edit_history_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28905_idx_social_edit_history_target ON public.social_discussion_edit_history USING btree (target_type, target_id, created_at);


--
-- Name: idx_28912_idx_social_library_items_community; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28912_idx_social_library_items_community ON public.social_library_items USING btree (community_id, visibility, status, updated_at);


--
-- Name: idx_28912_idx_social_library_items_content_class; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28912_idx_social_library_items_content_class ON public.social_library_items USING btree (content_class, commercial_status, visibility, status);


--
-- Name: idx_28912_idx_social_library_items_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28912_idx_social_library_items_owner ON public.social_library_items USING btree (owner_user_id, status, updated_at);


--
-- Name: idx_28912_idx_social_library_items_remix_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28912_idx_social_library_items_remix_source ON public.social_library_items USING btree (remix_source_item_id);


--
-- Name: idx_28912_idx_social_library_items_variant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28912_idx_social_library_items_variant ON public.social_library_items USING btree (catalog_variant_id, status);


--
-- Name: idx_28927_idx_social_library_files_analyzed; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28927_idx_social_library_files_analyzed ON public.social_library_files USING btree (analyzed_at, validation_status);


--
-- Name: idx_28927_idx_social_library_files_quarantine; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28927_idx_social_library_files_quarantine ON public.social_library_files USING btree (quarantine_key);


--
-- Name: idx_28927_idx_social_library_files_sha256; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28927_idx_social_library_files_sha256 ON public.social_library_files USING btree (sha256);


--
-- Name: idx_28927_idx_social_library_files_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28927_idx_social_library_files_status ON public.social_library_files USING btree (validation_status, uploaded_at);


--
-- Name: idx_28935_idx_social_library_downloads_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28935_idx_social_library_downloads_item ON public.social_library_downloads USING btree (item_id, created_at);


--
-- Name: idx_28935_idx_social_library_downloads_version; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28935_idx_social_library_downloads_version ON public.social_library_downloads USING btree (version_id, created_at);


--
-- Name: idx_28941_idx_social_library_versions_item_current; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28941_idx_social_library_versions_item_current ON public.social_library_versions USING btree (item_id, is_current, created_at);


--
-- Name: idx_28951_idx_social_library_favorites_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28951_idx_social_library_favorites_item ON public.social_library_favorites USING btree (item_id, created_at);


--
-- Name: idx_28957_idx_social_library_collections_community; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28957_idx_social_library_collections_community ON public.social_library_collections USING btree (community_id, visibility, status, updated_at);


--
-- Name: idx_28957_idx_social_library_collections_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28957_idx_social_library_collections_owner ON public.social_library_collections USING btree (owner_user_id, status, updated_at);


--
-- Name: idx_28972_idx_social_print_lists_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28972_idx_social_print_lists_owner ON public.social_print_lists USING btree (owner_user_id, status, updated_at);


--
-- Name: idx_28980_sqlite_autoindex_social_print_list_items_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_28980_sqlite_autoindex_social_print_list_items_1 ON public.social_print_list_items USING btree (print_list_id, item_id, version_id);


--
-- Name: idx_28988_idx_social_technical_configs_community; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28988_idx_social_technical_configs_community ON public.social_technical_printer_configs USING btree (community_id, visibility, status, updated_at);


--
-- Name: idx_28988_idx_social_technical_configs_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28988_idx_social_technical_configs_owner ON public.social_technical_printer_configs USING btree (owner_user_id, status, updated_at);


--
-- Name: idx_28988_idx_social_technical_configs_variant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_28988_idx_social_technical_configs_variant ON public.social_technical_printer_configs USING btree (catalog_variant_id, visibility, status, updated_at);


--
-- Name: idx_29000_idx_social_material_profiles_community; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29000_idx_social_material_profiles_community ON public.social_material_profiles USING btree (community_id, visibility, status, updated_at);


--
-- Name: idx_29000_idx_social_material_profiles_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29000_idx_social_material_profiles_owner ON public.social_material_profiles USING btree (owner_user_id, status, updated_at);


--
-- Name: idx_29000_idx_social_material_profiles_variant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29000_idx_social_material_profiles_variant ON public.social_material_profiles USING btree (catalog_variant_id, material_type, nozzle_diameter_mm, status);


--
-- Name: idx_29012_sqlite_autoindex_social_slicing_profiles_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29012_sqlite_autoindex_social_slicing_profiles_1 ON public.social_slicing_profiles USING btree (material_profile_id);


--
-- Name: idx_29023_sqlite_autoindex_social_content_tags_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29023_sqlite_autoindex_social_content_tags_1 ON public.social_content_tags USING btree (slug);


--
-- Name: idx_29033_idx_social_tag_links_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29033_idx_social_tag_links_entity ON public.social_content_tag_links USING btree (entity_type, entity_id);


--
-- Name: idx_29039_idx_social_search_index_community; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29039_idx_social_search_index_community ON public.social_search_index USING btree (community_id, visibility, source_updated_at);


--
-- Name: idx_29039_idx_social_search_index_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29039_idx_social_search_index_type ON public.social_search_index USING btree (entity_type, visibility, source_updated_at);


--
-- Name: idx_29039_idx_social_search_index_variant; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29039_idx_social_search_index_variant ON public.social_search_index USING btree (catalog_variant_id, visibility, source_updated_at);


--
-- Name: idx_29050_idx_social_quality_signals_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29050_idx_social_quality_signals_entity ON public.social_quality_signals USING btree (entity_type, entity_id, signal_type);


--
-- Name: idx_29050_idx_social_quality_signals_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29050_idx_social_quality_signals_target ON public.social_quality_signals USING btree (target_user_id, signal_type, created_at);


--
-- Name: idx_29050_sqlite_autoindex_social_quality_signals_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29050_sqlite_autoindex_social_quality_signals_1 ON public.social_quality_signals USING btree (signal_type, source_table, source_id);


--
-- Name: idx_29058_idx_social_user_reputation_score; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29058_idx_social_user_reputation_score ON public.social_user_reputation_snapshots USING btree (reputation_score, contribution_count);


--
-- Name: idx_29073_idx_social_moderation_reports_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29073_idx_social_moderation_reports_entity ON public.social_moderation_reports USING btree (entity_type, entity_id, status);


--
-- Name: idx_29073_idx_social_moderation_reports_queue; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29073_idx_social_moderation_reports_queue ON public.social_moderation_reports USING btree (status, created_at);


--
-- Name: idx_29073_sqlite_autoindex_social_moderation_reports_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29073_sqlite_autoindex_social_moderation_reports_1 ON public.social_moderation_reports USING btree (entity_type, entity_id, reporter_user_id, reason);


--
-- Name: idx_29082_idx_social_moderation_actions_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29082_idx_social_moderation_actions_entity ON public.social_moderation_actions USING btree (entity_type, entity_id, created_at);


--
-- Name: idx_29090_idx_social_notifications_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29090_idx_social_notifications_entity ON public.social_notifications USING btree (entity_type, entity_id, created_at);


--
-- Name: idx_29090_idx_social_notifications_recipient; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29090_idx_social_notifications_recipient ON public.social_notifications USING btree (recipient_user_id, status, created_at);


--
-- Name: idx_29107_idx_social_content_follows_entity; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29107_idx_social_content_follows_entity ON public.social_content_follows USING btree (entity_type, entity_id, muted);


--
-- Name: idx_29107_sqlite_autoindex_social_content_follows_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29107_sqlite_autoindex_social_content_follows_1 ON public.social_content_follows USING btree (user_id, entity_type, entity_id);


--
-- Name: idx_29128_idx_social_rate_limit_events_actor_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29128_idx_social_rate_limit_events_actor_action ON public.social_rate_limit_events USING btree (actor_user_id, action, created_at);


--
-- Name: idx_29128_idx_social_rate_limit_events_subject_action; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29128_idx_social_rate_limit_events_subject_action ON public.social_rate_limit_events USING btree (subject_hash, action, created_at);


--
-- Name: idx_29136_idx_social_abuse_signals_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29136_idx_social_abuse_signals_status ON public.social_abuse_signals USING btree (status, severity, created_at);


--
-- Name: idx_29136_idx_social_abuse_signals_subject; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29136_idx_social_abuse_signals_subject ON public.social_abuse_signals USING btree (subject_user_id, action, status);


--
-- Name: idx_29147_idx_social_file_storage_policies_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29147_idx_social_file_storage_policies_scope ON public.social_file_storage_policies USING btree (scope_type, scope_id, status);


--
-- Name: idx_29147_sqlite_autoindex_social_file_storage_policies_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29147_sqlite_autoindex_social_file_storage_policies_1 ON public.social_file_storage_policies USING btree (scope_type, scope_id);


--
-- Name: idx_29157_idx_social_file_retention_reviews_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29157_idx_social_file_retention_reviews_owner ON public.social_file_retention_reviews USING btree (owner_user_id, created_at);


--
-- Name: idx_29169_idx_slicing_engine_checks_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29169_idx_slicing_engine_checks_created ON public.slicing_engine_checks USING btree (created_at);


--
-- Name: idx_29177_idx_slicing_dry_run_logs_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29177_idx_slicing_dry_run_logs_created ON public.slicing_dry_run_logs USING btree (created_at);


--
-- Name: idx_29186_idx_slicing_jobs_owner_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29186_idx_slicing_jobs_owner_created ON public.slicing_jobs USING btree (owner_user_id, created_at);


--
-- Name: idx_29186_idx_slicing_jobs_print_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29186_idx_slicing_jobs_print_project ON public.slicing_jobs USING btree (print_project_id, owner_user_id, created_at);


--
-- Name: idx_29186_idx_slicing_jobs_printer_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29186_idx_slicing_jobs_printer_created ON public.slicing_jobs USING btree (printer_id, created_at);


--
-- Name: idx_29186_idx_slicing_jobs_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29186_idx_slicing_jobs_status ON public.slicing_jobs USING btree (status, created_at);


--
-- Name: idx_29201_idx_slicing_job_artifacts_job; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29201_idx_slicing_job_artifacts_job ON public.slicing_job_artifacts USING btree (job_id, artifact_kind);


--
-- Name: idx_29209_idx_print_preflight_checks_printer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29209_idx_print_preflight_checks_printer ON public.print_preflight_checks USING btree (printer_id, created_at);


--
-- Name: idx_29209_idx_print_preflight_checks_remote_job; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29209_idx_print_preflight_checks_remote_job ON public.print_preflight_checks USING btree (remote_agent_job_id);


--
-- Name: idx_29209_idx_print_preflight_checks_slicing_job; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29209_idx_print_preflight_checks_slicing_job ON public.print_preflight_checks USING btree (slicing_job_id, created_at);


--
-- Name: idx_29221_idx_print_gcode_deliveries_owner_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29221_idx_print_gcode_deliveries_owner_created ON public.print_gcode_deliveries USING btree (owner_user_id, created_at);


--
-- Name: idx_29221_idx_print_gcode_deliveries_preflight; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29221_idx_print_gcode_deliveries_preflight ON public.print_gcode_deliveries USING btree (preflight_id);


--
-- Name: idx_29221_idx_print_gcode_deliveries_printer_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29221_idx_print_gcode_deliveries_printer_created ON public.print_gcode_deliveries USING btree (printer_id, created_at);


--
-- Name: idx_29236_idx_print_job_history_library_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29236_idx_print_job_history_library_status ON public.print_job_history USING btree (library_item_id, status, visibility);


--
-- Name: idx_29236_idx_print_job_history_owner_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29236_idx_print_job_history_owner_created ON public.print_job_history USING btree (owner_user_id, created_at);


--
-- Name: idx_29236_idx_print_job_history_printer_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29236_idx_print_job_history_printer_created ON public.print_job_history USING btree (printer_id, created_at);


--
-- Name: idx_29236_sqlite_autoindex_print_job_history_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29236_sqlite_autoindex_print_job_history_1 ON public.print_job_history USING btree (delivery_id);


--
-- Name: idx_29249_idx_print_job_feedback_history_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29249_idx_print_job_feedback_history_created ON public.print_job_feedback USING btree (history_id, created_at);


--
-- Name: idx_29258_idx_social_library_commercial_reviews_item; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29258_idx_social_library_commercial_reviews_item ON public.social_library_commercial_reviews USING btree (item_id, created_at);


--
-- Name: idx_29265_sqlite_autoindex_external_content_sources_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29265_sqlite_autoindex_external_content_sources_1 ON public.external_content_sources USING btree (owner_user_id, base_url);


--
-- Name: idx_29275_idx_external_library_references_checksum; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29275_idx_external_library_references_checksum ON public.external_library_references USING btree (checksum_sha256);


--
-- Name: idx_29275_idx_external_library_references_owner_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29275_idx_external_library_references_owner_created ON public.external_library_references USING btree (owner_user_id, created_at);


--
-- Name: idx_29275_sqlite_autoindex_external_library_references_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29275_sqlite_autoindex_external_library_references_1 ON public.external_library_references USING btree (owner_user_id, external_url);


--
-- Name: idx_29287_idx_print_projects_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29287_idx_print_projects_owner ON public.print_projects USING btree (owner_user_id, lifecycle_status, updated_at);


--
-- Name: idx_29287_idx_print_projects_publication_commercial; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29287_idx_print_projects_publication_commercial ON public.print_projects USING btree (publication_status, commercial_class, visibility, updated_at);


--
-- Name: idx_29287_idx_print_projects_visibility; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29287_idx_print_projects_visibility ON public.print_projects USING btree (visibility, lifecycle_status, publication_status, updated_at);


--
-- Name: idx_29287_sqlite_autoindex_print_projects_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29287_sqlite_autoindex_print_projects_1 ON public.print_projects USING btree (slug);


--
-- Name: idx_29308_idx_print_project_files_checksum; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29308_idx_print_project_files_checksum ON public.print_project_files USING btree (sha256, validation_status);


--
-- Name: idx_29308_idx_print_project_files_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29308_idx_print_project_files_project ON public.print_project_files USING btree (project_id, file_role, validation_status);


--
-- Name: idx_29308_idx_print_project_files_storage; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29308_idx_print_project_files_storage ON public.print_project_files USING btree (project_id, quarantine_key, uploaded_at);


--
-- Name: idx_29319_idx_print_project_versions_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29319_idx_print_project_versions_project ON public.print_project_versions USING btree (project_id, created_at);


--
-- Name: idx_29328_idx_print_project_shares_community; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29328_idx_print_project_shares_community ON public.print_project_community_shares USING btree (community_id, status, updated_at);


--
-- Name: idx_29328_sqlite_autoindex_print_project_community_shares_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29328_sqlite_autoindex_print_project_community_shares_1 ON public.print_project_community_shares USING btree (project_id, community_id);


--
-- Name: idx_29336_idx_print_project_saves_owner; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29336_idx_print_project_saves_owner ON public.print_project_saves USING btree (owner_user_id, status, updated_at);


--
-- Name: idx_29336_idx_print_project_saves_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29336_idx_print_project_saves_project ON public.print_project_saves USING btree (project_id, status);


--
-- Name: idx_29336_sqlite_autoindex_print_project_saves_1; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_29336_sqlite_autoindex_print_project_saves_1 ON public.print_project_saves USING btree (owner_user_id, project_id, save_kind);


--
-- Name: idx_29345_idx_print_project_publication_reviews_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_29345_idx_print_project_publication_reviews_project ON public.print_project_publication_reviews USING btree (project_id, created_at);


--
-- Name: idx_social_file_storage_policies_unique_scope; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_social_file_storage_policies_unique_scope ON public.social_file_storage_policies USING btree (scope_type, COALESCE(scope_id, (0)::bigint));


--
-- Name: agent_credentials agent_credentials_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_credentials
    ADD CONSTRAINT agent_credentials_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE CASCADE;


--
-- Name: agent_credentials agent_credentials_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_credentials
    ADD CONSTRAINT agent_credentials_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: agent_jobs agent_jobs_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_jobs
    ADD CONSTRAINT agent_jobs_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.printer_agents(id) ON DELETE SET NULL;


--
-- Name: agent_jobs agent_jobs_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.agent_jobs
    ADD CONSTRAINT agent_jobs_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: app_events app_events_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_events
    ADD CONSTRAINT app_events_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE SET NULL;


--
-- Name: app_update_runs app_update_runs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_update_runs
    ADD CONSTRAINT app_update_runs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE SET NULL;


--
-- Name: app_update_runs app_update_runs_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_update_runs
    ADD CONSTRAINT app_update_runs_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: app_update_steps app_update_steps_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_update_steps
    ADD CONSTRAINT app_update_steps_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.app_update_runs(id) ON DELETE CASCADE;


--
-- Name: auth_mfa_challenges auth_mfa_challenges_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_mfa_challenges
    ADD CONSTRAINT auth_mfa_challenges_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: auth_organization_invites auth_organization_invites_accepted_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organization_invites
    ADD CONSTRAINT auth_organization_invites_accepted_by_user_id_fkey FOREIGN KEY (accepted_by_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: auth_organization_invites auth_organization_invites_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organization_invites
    ADD CONSTRAINT auth_organization_invites_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: auth_organization_invites auth_organization_invites_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organization_invites
    ADD CONSTRAINT auth_organization_invites_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE CASCADE;


--
-- Name: auth_organization_members auth_organization_members_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organization_members
    ADD CONSTRAINT auth_organization_members_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE CASCADE;


--
-- Name: auth_organization_members auth_organization_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organization_members
    ADD CONSTRAINT auth_organization_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: auth_organization_printers auth_organization_printers_linked_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organization_printers
    ADD CONSTRAINT auth_organization_printers_linked_by_user_id_fkey FOREIGN KEY (linked_by_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: auth_organization_printers auth_organization_printers_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organization_printers
    ADD CONSTRAINT auth_organization_printers_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE CASCADE;


--
-- Name: auth_organization_printers auth_organization_printers_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organization_printers
    ADD CONSTRAINT auth_organization_printers_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: auth_organizations auth_organizations_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_organizations
    ADD CONSTRAINT auth_organizations_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE RESTRICT;


--
-- Name: auth_sessions auth_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_sessions
    ADD CONSTRAINT auth_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: auth_step_up_tokens auth_step_up_tokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.auth_step_up_tokens
    ADD CONSTRAINT auth_step_up_tokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: backup_policies backup_policies_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backup_policies
    ADD CONSTRAINT backup_policies_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: backup_runs backup_runs_policy_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backup_runs
    ADD CONSTRAINT backup_runs_policy_id_fkey FOREIGN KEY (policy_id) REFERENCES public.backup_policies(id) ON DELETE CASCADE;


--
-- Name: backup_runs backup_runs_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.backup_runs
    ADD CONSTRAINT backup_runs_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: calibration_execution_attempts calibration_execution_attempts_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_execution_attempts
    ADD CONSTRAINT calibration_execution_attempts_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: calibration_execution_attempts calibration_execution_attempts_test_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_execution_attempts
    ADD CONSTRAINT calibration_execution_attempts_test_key_fkey FOREIGN KEY (test_key) REFERENCES public.calibration_tests(test_key) ON DELETE RESTRICT;


--
-- Name: calibration_test_runs calibration_test_runs_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_test_runs
    ADD CONSTRAINT calibration_test_runs_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: calibration_test_runs calibration_test_runs_test_key_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.calibration_test_runs
    ADD CONSTRAINT calibration_test_runs_test_key_fkey FOREIGN KEY (test_key) REFERENCES public.calibration_tests(test_key) ON DELETE RESTRICT;


--
-- Name: can_bus_records can_bus_records_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.can_bus_records
    ADD CONSTRAINT can_bus_records_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: catalog_audit_events catalog_audit_events_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_audit_events
    ADD CONSTRAINT catalog_audit_events_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: catalog_manufacturers catalog_manufacturers_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_manufacturers
    ADD CONSTRAINT catalog_manufacturers_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: catalog_printer_models catalog_printer_models_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_printer_models
    ADD CONSTRAINT catalog_printer_models_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: catalog_printer_models catalog_printer_models_manufacturer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_printer_models
    ADD CONSTRAINT catalog_printer_models_manufacturer_id_fkey FOREIGN KEY (manufacturer_id) REFERENCES public.catalog_manufacturers(id) ON DELETE RESTRICT;


--
-- Name: catalog_printer_variants catalog_printer_variants_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_printer_variants
    ADD CONSTRAINT catalog_printer_variants_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: catalog_printer_variants catalog_printer_variants_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.catalog_printer_variants
    ADD CONSTRAINT catalog_printer_variants_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.catalog_printer_models(id) ON DELETE RESTRICT;


--
-- Name: external_content_sources external_content_sources_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_content_sources
    ADD CONSTRAINT external_content_sources_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: external_library_references external_library_references_duplicate_library_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_library_references
    ADD CONSTRAINT external_library_references_duplicate_library_file_id_fkey FOREIGN KEY (duplicate_library_file_id) REFERENCES public.social_library_files(id) ON DELETE SET NULL;


--
-- Name: external_library_references external_library_references_library_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_library_references
    ADD CONSTRAINT external_library_references_library_item_id_fkey FOREIGN KEY (library_item_id) REFERENCES public.social_library_items(id) ON DELETE SET NULL;


--
-- Name: external_library_references external_library_references_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_library_references
    ADD CONSTRAINT external_library_references_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: external_library_references external_library_references_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.external_library_references
    ADD CONSTRAINT external_library_references_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.external_content_sources(id) ON DELETE SET NULL;


--
-- Name: firmware_boards firmware_boards_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firmware_boards
    ADD CONSTRAINT firmware_boards_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: firmware_build_runs firmware_build_runs_board_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firmware_build_runs
    ADD CONSTRAINT firmware_build_runs_board_id_fkey FOREIGN KEY (board_id) REFERENCES public.firmware_boards(id) ON DELETE CASCADE;


--
-- Name: firmware_build_runs firmware_build_runs_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firmware_build_runs
    ADD CONSTRAINT firmware_build_runs_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: firmware_flash_runs firmware_flash_runs_board_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firmware_flash_runs
    ADD CONSTRAINT firmware_flash_runs_board_id_fkey FOREIGN KEY (board_id) REFERENCES public.firmware_boards(id) ON DELETE CASCADE;


--
-- Name: firmware_flash_runs firmware_flash_runs_build_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firmware_flash_runs
    ADD CONSTRAINT firmware_flash_runs_build_run_id_fkey FOREIGN KEY (build_run_id) REFERENCES public.firmware_build_runs(id) ON DELETE SET NULL;


--
-- Name: firmware_flash_runs firmware_flash_runs_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.firmware_flash_runs
    ADD CONSTRAINT firmware_flash_runs_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: maintenance_events maintenance_events_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_events
    ADD CONSTRAINT maintenance_events_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: maintenance_tasks maintenance_tasks_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.maintenance_tasks
    ADD CONSTRAINT maintenance_tasks_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: operation_action_execution_attempts operation_action_execution_attempts_preview_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.operation_action_execution_attempts
    ADD CONSTRAINT operation_action_execution_attempts_preview_id_fkey FOREIGN KEY (preview_id) REFERENCES public.operation_action_previews(id) ON DELETE CASCADE;


--
-- Name: operation_action_execution_attempts operation_action_execution_attempts_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.operation_action_execution_attempts
    ADD CONSTRAINT operation_action_execution_attempts_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: operation_action_previews operation_action_previews_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.operation_action_previews
    ADD CONSTRAINT operation_action_previews_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: print_gcode_deliveries print_gcode_deliveries_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_gcode_deliveries
    ADD CONSTRAINT print_gcode_deliveries_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: print_gcode_deliveries print_gcode_deliveries_preflight_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_gcode_deliveries
    ADD CONSTRAINT print_gcode_deliveries_preflight_id_fkey FOREIGN KEY (preflight_id) REFERENCES public.print_preflight_checks(id) ON DELETE CASCADE;


--
-- Name: print_gcode_deliveries print_gcode_deliveries_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_gcode_deliveries
    ADD CONSTRAINT print_gcode_deliveries_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: print_gcode_deliveries print_gcode_deliveries_remote_agent_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_gcode_deliveries
    ADD CONSTRAINT print_gcode_deliveries_remote_agent_job_id_fkey FOREIGN KEY (remote_agent_job_id) REFERENCES public.agent_jobs(id) ON DELETE SET NULL;


--
-- Name: print_gcode_deliveries print_gcode_deliveries_rollback_agent_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_gcode_deliveries
    ADD CONSTRAINT print_gcode_deliveries_rollback_agent_job_id_fkey FOREIGN KEY (rollback_agent_job_id) REFERENCES public.agent_jobs(id) ON DELETE SET NULL;


--
-- Name: print_gcode_deliveries print_gcode_deliveries_slicing_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_gcode_deliveries
    ADD CONSTRAINT print_gcode_deliveries_slicing_job_id_fkey FOREIGN KEY (slicing_job_id) REFERENCES public.slicing_jobs(id) ON DELETE CASCADE;


--
-- Name: print_job_feedback print_job_feedback_history_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_job_feedback
    ADD CONSTRAINT print_job_feedback_history_id_fkey FOREIGN KEY (history_id) REFERENCES public.print_job_history(id) ON DELETE CASCADE;


--
-- Name: print_job_feedback print_job_feedback_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_job_feedback
    ADD CONSTRAINT print_job_feedback_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: print_job_history print_job_history_delivery_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_job_history
    ADD CONSTRAINT print_job_history_delivery_id_fkey FOREIGN KEY (delivery_id) REFERENCES public.print_gcode_deliveries(id) ON DELETE SET NULL;


--
-- Name: print_job_history print_job_history_library_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_job_history
    ADD CONSTRAINT print_job_history_library_item_id_fkey FOREIGN KEY (library_item_id) REFERENCES public.social_library_items(id) ON DELETE SET NULL;


--
-- Name: print_job_history print_job_history_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_job_history
    ADD CONSTRAINT print_job_history_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: print_job_history print_job_history_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_job_history
    ADD CONSTRAINT print_job_history_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: print_job_history print_job_history_slicing_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_job_history
    ADD CONSTRAINT print_job_history_slicing_job_id_fkey FOREIGN KEY (slicing_job_id) REFERENCES public.slicing_jobs(id) ON DELETE SET NULL;


--
-- Name: print_preflight_checks print_preflight_checks_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_preflight_checks
    ADD CONSTRAINT print_preflight_checks_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: print_preflight_checks print_preflight_checks_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_preflight_checks
    ADD CONSTRAINT print_preflight_checks_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: print_preflight_checks print_preflight_checks_remote_agent_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_preflight_checks
    ADD CONSTRAINT print_preflight_checks_remote_agent_job_id_fkey FOREIGN KEY (remote_agent_job_id) REFERENCES public.agent_jobs(id) ON DELETE SET NULL;


--
-- Name: print_preflight_checks print_preflight_checks_slicing_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_preflight_checks
    ADD CONSTRAINT print_preflight_checks_slicing_job_id_fkey FOREIGN KEY (slicing_job_id) REFERENCES public.slicing_jobs(id) ON DELETE CASCADE;


--
-- Name: print_project_community_shares print_project_community_shares_community_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_community_shares
    ADD CONSTRAINT print_project_community_shares_community_id_fkey FOREIGN KEY (community_id) REFERENCES public.social_communities(id) ON DELETE CASCADE;


--
-- Name: print_project_community_shares print_project_community_shares_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_community_shares
    ADD CONSTRAINT print_project_community_shares_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.print_projects(id) ON DELETE CASCADE;


--
-- Name: print_project_community_shares print_project_community_shares_shared_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_community_shares
    ADD CONSTRAINT print_project_community_shares_shared_by_user_id_fkey FOREIGN KEY (shared_by_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: print_project_files print_project_files_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_files
    ADD CONSTRAINT print_project_files_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.print_projects(id) ON DELETE CASCADE;


--
-- Name: print_project_publication_reviews print_project_publication_reviews_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_publication_reviews
    ADD CONSTRAINT print_project_publication_reviews_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.print_projects(id) ON DELETE CASCADE;


--
-- Name: print_project_publication_reviews print_project_publication_reviews_reviewer_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_publication_reviews
    ADD CONSTRAINT print_project_publication_reviews_reviewer_user_id_fkey FOREIGN KEY (reviewer_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: print_project_saves print_project_saves_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_saves
    ADD CONSTRAINT print_project_saves_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: print_project_saves print_project_saves_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_saves
    ADD CONSTRAINT print_project_saves_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.print_projects(id) ON DELETE CASCADE;


--
-- Name: print_project_versions print_project_versions_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_versions
    ADD CONSTRAINT print_project_versions_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: print_project_versions print_project_versions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_project_versions
    ADD CONSTRAINT print_project_versions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.print_projects(id) ON DELETE CASCADE;


--
-- Name: print_projects print_projects_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.print_projects
    ADD CONSTRAINT print_projects_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: printer_agent_events printer_agent_events_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_agent_events
    ADD CONSTRAINT printer_agent_events_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.printer_agents(id) ON DELETE SET NULL;


--
-- Name: printer_agent_events printer_agent_events_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_agent_events
    ADD CONSTRAINT printer_agent_events_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: printer_agents printer_agents_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_agents
    ADD CONSTRAINT printer_agents_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE SET NULL;


--
-- Name: printer_agents printer_agents_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_agents
    ADD CONSTRAINT printer_agents_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: printer_agents printer_agents_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_agents
    ADD CONSTRAINT printer_agents_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: printer_pairing_tokens printer_pairing_tokens_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_pairing_tokens
    ADD CONSTRAINT printer_pairing_tokens_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: printer_pairing_tokens printer_pairing_tokens_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_pairing_tokens
    ADD CONSTRAINT printer_pairing_tokens_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE SET NULL;


--
-- Name: printer_pairing_tokens printer_pairing_tokens_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_pairing_tokens
    ADD CONSTRAINT printer_pairing_tokens_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: printer_pairing_tokens printer_pairing_tokens_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_pairing_tokens
    ADD CONSTRAINT printer_pairing_tokens_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: printer_snapshots printer_snapshots_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_snapshots
    ADD CONSTRAINT printer_snapshots_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: printer_ssh_access printer_ssh_access_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printer_ssh_access
    ADD CONSTRAINT printer_ssh_access_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: printers printers_catalog_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printers
    ADD CONSTRAINT printers_catalog_variant_id_fkey FOREIGN KEY (catalog_variant_id) REFERENCES public.catalog_printer_variants(id) ON DELETE SET NULL;


--
-- Name: printers printers_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printers
    ADD CONSTRAINT printers_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE SET NULL;


--
-- Name: printers printers_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.printers
    ADD CONSTRAINT printers_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: setup_can_runs setup_can_runs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_can_runs
    ADD CONSTRAINT setup_can_runs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE SET NULL;


--
-- Name: setup_can_runs setup_can_runs_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_can_runs
    ADD CONSTRAINT setup_can_runs_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: setup_final_validation_runs setup_final_validation_runs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_final_validation_runs
    ADD CONSTRAINT setup_final_validation_runs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE SET NULL;


--
-- Name: setup_final_validation_runs setup_final_validation_runs_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_final_validation_runs
    ADD CONSTRAINT setup_final_validation_runs_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: setup_firmware_runs setup_firmware_runs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_firmware_runs
    ADD CONSTRAINT setup_firmware_runs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE SET NULL;


--
-- Name: setup_firmware_runs setup_firmware_runs_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_firmware_runs
    ADD CONSTRAINT setup_firmware_runs_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: setup_flash_runs setup_flash_runs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_flash_runs
    ADD CONSTRAINT setup_flash_runs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE SET NULL;


--
-- Name: setup_flash_runs setup_flash_runs_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_flash_runs
    ADD CONSTRAINT setup_flash_runs_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: setup_ssh_runs setup_ssh_runs_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_ssh_runs
    ADD CONSTRAINT setup_ssh_runs_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.auth_organizations(id) ON DELETE SET NULL;


--
-- Name: setup_ssh_runs setup_ssh_runs_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.setup_ssh_runs
    ADD CONSTRAINT setup_ssh_runs_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: slicing_job_artifacts slicing_job_artifacts_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slicing_job_artifacts
    ADD CONSTRAINT slicing_job_artifacts_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.slicing_jobs(id) ON DELETE CASCADE;


--
-- Name: slicing_jobs slicing_jobs_material_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slicing_jobs
    ADD CONSTRAINT slicing_jobs_material_profile_id_fkey FOREIGN KEY (material_profile_id) REFERENCES public.social_material_profiles(id) ON DELETE SET NULL;


--
-- Name: slicing_jobs slicing_jobs_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slicing_jobs
    ADD CONSTRAINT slicing_jobs_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: slicing_jobs slicing_jobs_print_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slicing_jobs
    ADD CONSTRAINT slicing_jobs_print_project_id_fkey FOREIGN KEY (print_project_id) REFERENCES public.print_projects(id) ON DELETE SET NULL;


--
-- Name: slicing_jobs slicing_jobs_print_project_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slicing_jobs
    ADD CONSTRAINT slicing_jobs_print_project_version_id_fkey FOREIGN KEY (print_project_version_id) REFERENCES public.print_project_versions(id) ON DELETE SET NULL;


--
-- Name: slicing_jobs slicing_jobs_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.slicing_jobs
    ADD CONSTRAINT slicing_jobs_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE SET NULL;


--
-- Name: social_abuse_signals social_abuse_signals_subject_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_abuse_signals
    ADD CONSTRAINT social_abuse_signals_subject_user_id_fkey FOREIGN KEY (subject_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_abuse_signals social_abuse_signals_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_abuse_signals
    ADD CONSTRAINT social_abuse_signals_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_communities social_communities_manufacturer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_communities
    ADD CONSTRAINT social_communities_manufacturer_id_fkey FOREIGN KEY (manufacturer_id) REFERENCES public.catalog_manufacturers(id) ON DELETE RESTRICT;


--
-- Name: social_communities social_communities_merged_into_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_communities
    ADD CONSTRAINT social_communities_merged_into_id_fkey FOREIGN KEY (merged_into_id) REFERENCES public.social_communities(id) ON DELETE SET NULL;


--
-- Name: social_communities social_communities_model_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_communities
    ADD CONSTRAINT social_communities_model_id_fkey FOREIGN KEY (model_id) REFERENCES public.catalog_printer_models(id) ON DELETE RESTRICT;


--
-- Name: social_communities social_communities_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_communities
    ADD CONSTRAINT social_communities_variant_id_fkey FOREIGN KEY (variant_id) REFERENCES public.catalog_printer_variants(id) ON DELETE RESTRICT;


--
-- Name: social_community_members social_community_members_community_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_community_members
    ADD CONSTRAINT social_community_members_community_id_fkey FOREIGN KEY (community_id) REFERENCES public.social_communities(id) ON DELETE CASCADE;


--
-- Name: social_community_members social_community_members_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_community_members
    ADD CONSTRAINT social_community_members_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: social_community_members social_community_members_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_community_members
    ADD CONSTRAINT social_community_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_content_follows social_content_follows_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_content_follows
    ADD CONSTRAINT social_content_follows_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_content_tag_links social_content_tag_links_tag_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_content_tag_links
    ADD CONSTRAINT social_content_tag_links_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.social_content_tags(id) ON DELETE CASCADE;


--
-- Name: social_discussion_comments social_discussion_comments_author_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_discussion_comments
    ADD CONSTRAINT social_discussion_comments_author_user_id_fkey FOREIGN KEY (author_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_discussion_comments social_discussion_comments_feed_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_discussion_comments
    ADD CONSTRAINT social_discussion_comments_feed_item_id_fkey FOREIGN KEY (feed_item_id) REFERENCES public.social_feed_items(id) ON DELETE CASCADE;


--
-- Name: social_discussion_comments social_discussion_comments_parent_comment_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_discussion_comments
    ADD CONSTRAINT social_discussion_comments_parent_comment_id_fkey FOREIGN KEY (parent_comment_id) REFERENCES public.social_discussion_comments(id) ON DELETE CASCADE;


--
-- Name: social_discussion_edit_history social_discussion_edit_history_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_discussion_edit_history
    ADD CONSTRAINT social_discussion_edit_history_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_discussion_reactions social_discussion_reactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_discussion_reactions
    ADD CONSTRAINT social_discussion_reactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_feed_items social_feed_items_author_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_feed_items
    ADD CONSTRAINT social_feed_items_author_user_id_fkey FOREIGN KEY (author_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_feed_items social_feed_items_community_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_feed_items
    ADD CONSTRAINT social_feed_items_community_id_fkey FOREIGN KEY (community_id) REFERENCES public.social_communities(id) ON DELETE CASCADE;


--
-- Name: social_file_retention_reviews social_file_retention_reviews_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_file_retention_reviews
    ADD CONSTRAINT social_file_retention_reviews_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_file_retention_reviews social_file_retention_reviews_requested_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_file_retention_reviews
    ADD CONSTRAINT social_file_retention_reviews_requested_by_user_id_fkey FOREIGN KEY (requested_by_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_file_storage_policies social_file_storage_policies_updated_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_file_storage_policies
    ADD CONSTRAINT social_file_storage_policies_updated_by_user_id_fkey FOREIGN KEY (updated_by_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_library_collection_items social_library_collection_items_added_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_collection_items
    ADD CONSTRAINT social_library_collection_items_added_by_user_id_fkey FOREIGN KEY (added_by_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_library_collection_items social_library_collection_items_collection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_collection_items
    ADD CONSTRAINT social_library_collection_items_collection_id_fkey FOREIGN KEY (collection_id) REFERENCES public.social_library_collections(id) ON DELETE CASCADE;


--
-- Name: social_library_collection_items social_library_collection_items_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_collection_items
    ADD CONSTRAINT social_library_collection_items_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.social_library_items(id) ON DELETE CASCADE;


--
-- Name: social_library_collection_items social_library_collection_items_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_collection_items
    ADD CONSTRAINT social_library_collection_items_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.social_library_versions(id) ON DELETE SET NULL;


--
-- Name: social_library_collections social_library_collections_community_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_collections
    ADD CONSTRAINT social_library_collections_community_id_fkey FOREIGN KEY (community_id) REFERENCES public.social_communities(id) ON DELETE SET NULL;


--
-- Name: social_library_collections social_library_collections_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_collections
    ADD CONSTRAINT social_library_collections_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_library_commercial_reviews social_library_commercial_reviews_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_commercial_reviews
    ADD CONSTRAINT social_library_commercial_reviews_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.social_library_items(id) ON DELETE CASCADE;


--
-- Name: social_library_commercial_reviews social_library_commercial_reviews_reviewer_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_commercial_reviews
    ADD CONSTRAINT social_library_commercial_reviews_reviewer_user_id_fkey FOREIGN KEY (reviewer_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_library_downloads social_library_downloads_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_downloads
    ADD CONSTRAINT social_library_downloads_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.social_library_items(id) ON DELETE CASCADE;


--
-- Name: social_library_downloads social_library_downloads_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_downloads
    ADD CONSTRAINT social_library_downloads_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_library_downloads social_library_downloads_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_downloads
    ADD CONSTRAINT social_library_downloads_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.social_library_versions(id) ON DELETE SET NULL;


--
-- Name: social_library_favorites social_library_favorites_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_favorites
    ADD CONSTRAINT social_library_favorites_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.social_library_items(id) ON DELETE CASCADE;


--
-- Name: social_library_favorites social_library_favorites_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_favorites
    ADD CONSTRAINT social_library_favorites_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_library_files social_library_files_deduplicated_from_file_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_files
    ADD CONSTRAINT social_library_files_deduplicated_from_file_id_fkey FOREIGN KEY (deduplicated_from_file_id) REFERENCES public.social_library_files(id) ON DELETE SET NULL;


--
-- Name: social_library_files social_library_files_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_files
    ADD CONSTRAINT social_library_files_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.social_library_items(id) ON DELETE CASCADE;


--
-- Name: social_library_items social_library_items_catalog_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_items
    ADD CONSTRAINT social_library_items_catalog_variant_id_fkey FOREIGN KEY (catalog_variant_id) REFERENCES public.catalog_printer_variants(id) ON DELETE SET NULL;


--
-- Name: social_library_items social_library_items_community_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_items
    ADD CONSTRAINT social_library_items_community_id_fkey FOREIGN KEY (community_id) REFERENCES public.social_communities(id) ON DELETE SET NULL;


--
-- Name: social_library_items social_library_items_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_items
    ADD CONSTRAINT social_library_items_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_library_items social_library_items_remix_source_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_items
    ADD CONSTRAINT social_library_items_remix_source_item_id_fkey FOREIGN KEY (remix_source_item_id) REFERENCES public.social_library_items(id) ON DELETE SET NULL;


--
-- Name: social_library_versions social_library_versions_created_by_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_versions
    ADD CONSTRAINT social_library_versions_created_by_user_id_fkey FOREIGN KEY (created_by_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_library_versions social_library_versions_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_library_versions
    ADD CONSTRAINT social_library_versions_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.social_library_items(id) ON DELETE CASCADE;


--
-- Name: social_material_profiles social_material_profiles_catalog_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_material_profiles
    ADD CONSTRAINT social_material_profiles_catalog_variant_id_fkey FOREIGN KEY (catalog_variant_id) REFERENCES public.catalog_printer_variants(id) ON DELETE SET NULL;


--
-- Name: social_material_profiles social_material_profiles_community_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_material_profiles
    ADD CONSTRAINT social_material_profiles_community_id_fkey FOREIGN KEY (community_id) REFERENCES public.social_communities(id) ON DELETE SET NULL;


--
-- Name: social_material_profiles social_material_profiles_linked_library_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_material_profiles
    ADD CONSTRAINT social_material_profiles_linked_library_item_id_fkey FOREIGN KEY (linked_library_item_id) REFERENCES public.social_library_items(id) ON DELETE SET NULL;


--
-- Name: social_material_profiles social_material_profiles_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_material_profiles
    ADD CONSTRAINT social_material_profiles_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_material_profiles social_material_profiles_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_material_profiles
    ADD CONSTRAINT social_material_profiles_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE SET NULL;


--
-- Name: social_moderation_actions social_moderation_actions_moderator_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_moderation_actions
    ADD CONSTRAINT social_moderation_actions_moderator_user_id_fkey FOREIGN KEY (moderator_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_moderation_actions social_moderation_actions_report_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_moderation_actions
    ADD CONSTRAINT social_moderation_actions_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.social_moderation_reports(id) ON DELETE SET NULL;


--
-- Name: social_moderation_reports social_moderation_reports_assigned_moderator_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_moderation_reports
    ADD CONSTRAINT social_moderation_reports_assigned_moderator_user_id_fkey FOREIGN KEY (assigned_moderator_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_moderation_reports social_moderation_reports_reporter_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_moderation_reports
    ADD CONSTRAINT social_moderation_reports_reporter_user_id_fkey FOREIGN KEY (reporter_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_notification_preferences social_notification_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_notification_preferences
    ADD CONSTRAINT social_notification_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_notifications social_notifications_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_notifications
    ADD CONSTRAINT social_notifications_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_notifications social_notifications_recipient_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_notifications
    ADD CONSTRAINT social_notifications_recipient_user_id_fkey FOREIGN KEY (recipient_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_print_list_items social_print_list_items_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_print_list_items
    ADD CONSTRAINT social_print_list_items_item_id_fkey FOREIGN KEY (item_id) REFERENCES public.social_library_items(id) ON DELETE CASCADE;


--
-- Name: social_print_list_items social_print_list_items_print_list_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_print_list_items
    ADD CONSTRAINT social_print_list_items_print_list_id_fkey FOREIGN KEY (print_list_id) REFERENCES public.social_print_lists(id) ON DELETE CASCADE;


--
-- Name: social_print_list_items social_print_list_items_version_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_print_list_items
    ADD CONSTRAINT social_print_list_items_version_id_fkey FOREIGN KEY (version_id) REFERENCES public.social_library_versions(id) ON DELETE CASCADE;


--
-- Name: social_print_lists social_print_lists_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_print_lists
    ADD CONSTRAINT social_print_lists_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_print_lists social_print_lists_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_print_lists
    ADD CONSTRAINT social_print_lists_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE SET NULL;


--
-- Name: social_profile_slug_history social_profile_slug_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_profile_slug_history
    ADD CONSTRAINT social_profile_slug_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_profiles social_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_profiles
    ADD CONSTRAINT social_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_quality_signals social_quality_signals_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_quality_signals
    ADD CONSTRAINT social_quality_signals_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_quality_signals social_quality_signals_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_quality_signals
    ADD CONSTRAINT social_quality_signals_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_rate_limit_events social_rate_limit_events_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_rate_limit_events
    ADD CONSTRAINT social_rate_limit_events_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_relationships social_relationships_actor_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_relationships
    ADD CONSTRAINT social_relationships_actor_user_id_fkey FOREIGN KEY (actor_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_relationships social_relationships_target_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_relationships
    ADD CONSTRAINT social_relationships_target_user_id_fkey FOREIGN KEY (target_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_search_index social_search_index_catalog_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_search_index
    ADD CONSTRAINT social_search_index_catalog_variant_id_fkey FOREIGN KEY (catalog_variant_id) REFERENCES public.catalog_printer_variants(id) ON DELETE SET NULL;


--
-- Name: social_search_index social_search_index_community_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_search_index
    ADD CONSTRAINT social_search_index_community_id_fkey FOREIGN KEY (community_id) REFERENCES public.social_communities(id) ON DELETE SET NULL;


--
-- Name: social_search_index social_search_index_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_search_index
    ADD CONSTRAINT social_search_index_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE SET NULL;


--
-- Name: social_slicing_profiles social_slicing_profiles_material_profile_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_slicing_profiles
    ADD CONSTRAINT social_slicing_profiles_material_profile_id_fkey FOREIGN KEY (material_profile_id) REFERENCES public.social_material_profiles(id) ON DELETE CASCADE;


--
-- Name: social_technical_printer_configs social_technical_printer_configs_catalog_variant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_technical_printer_configs
    ADD CONSTRAINT social_technical_printer_configs_catalog_variant_id_fkey FOREIGN KEY (catalog_variant_id) REFERENCES public.catalog_printer_variants(id) ON DELETE SET NULL;


--
-- Name: social_technical_printer_configs social_technical_printer_configs_community_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_technical_printer_configs
    ADD CONSTRAINT social_technical_printer_configs_community_id_fkey FOREIGN KEY (community_id) REFERENCES public.social_communities(id) ON DELETE SET NULL;


--
-- Name: social_technical_printer_configs social_technical_printer_configs_linked_library_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_technical_printer_configs
    ADD CONSTRAINT social_technical_printer_configs_linked_library_item_id_fkey FOREIGN KEY (linked_library_item_id) REFERENCES public.social_library_items(id) ON DELETE SET NULL;


--
-- Name: social_technical_printer_configs social_technical_printer_configs_owner_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_technical_printer_configs
    ADD CONSTRAINT social_technical_printer_configs_owner_user_id_fkey FOREIGN KEY (owner_user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_technical_printer_configs social_technical_printer_configs_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_technical_printer_configs
    ADD CONSTRAINT social_technical_printer_configs_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE SET NULL;


--
-- Name: social_user_reputation_snapshots social_user_reputation_snapshots_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_user_reputation_snapshots
    ADD CONSTRAINT social_user_reputation_snapshots_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: social_user_safety_settings social_user_safety_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.social_user_safety_settings
    ADD CONSTRAINT social_user_safety_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.auth_users(id) ON DELETE CASCADE;


--
-- Name: update_alert_silences update_alert_silences_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.update_alert_silences
    ADD CONSTRAINT update_alert_silences_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- Name: z_offset_records z_offset_records_printer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.z_offset_records
    ADD CONSTRAINT z_offset_records_printer_id_fkey FOREIGN KEY (printer_id) REFERENCES public.printers(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--
