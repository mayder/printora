UPDATE printers
SET host_audit_mode = 'local'
WHERE host_audit_mode = 'disabled';
