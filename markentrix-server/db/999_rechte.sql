-- Rechte für die Anwendungsrolle mk_app (kein Superuser, umgeht Row-Level-Security nicht).
-- Die Rolle legt "mkctl migrate" an. Diese Datei läuft bei jeder Migration, damit neue Tabellen erfasst werden.
GRANT USAGE ON SCHEMA public TO mk_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mk_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mk_app;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO mk_app;
-- Protokolle sind unveränderlich
REVOKE UPDATE, DELETE ON audit_log FROM mk_app;
REVOKE UPDATE, DELETE ON loeschprotokoll FROM mk_app;
