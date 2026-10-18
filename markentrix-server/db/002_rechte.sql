-- Rechte für die Anwendungsrolle mk_app (kein Superuser, umgeht Row-Level-Security nicht).
-- Die Rolle selbst legt install.sh an.
GRANT USAGE ON SCHEMA public TO mk_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mk_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mk_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mk_app;
