-- Migration 005: Create application_logs table
CREATE TABLE IF NOT EXISTS application_logs (
    id VARCHAR(36) PRIMARY KEY,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    context VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
