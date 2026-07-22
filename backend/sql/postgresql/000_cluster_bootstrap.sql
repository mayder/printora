\set ON_ERROR_STOP on

SELECT 'CREATE ROLE printora_owner NOLOGIN'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'printora_owner')
\gexec

SELECT 'CREATE ROLE printora_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'printora_app')
\gexec

SELECT format('ALTER ROLE printora_app PASSWORD %L', :'app_password')
\gexec

SELECT 'CREATE DATABASE printora_cloud OWNER printora_owner'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'printora_cloud')
\gexec
