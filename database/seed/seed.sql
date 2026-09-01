-- Seed default user and test data
INSERT INTO users (id, email, hashed_password, full_name, is_active)
VALUES ('usr-seed-001', 'demo@marketorbit.com', '$2b$12$e8Y0N0g.N7iJ8oK5b7tYeu6g8Qz2QW1E8f9aG2r5pL1', 'Demo Marketer', TRUE)
ON CONFLICT (id) DO NOTHING;
