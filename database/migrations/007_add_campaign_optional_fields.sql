-- Migration 007: Add optional campaign fields

ALTER TABLE campaigns
ADD COLUMN date DATE,
ADD COLUMN location VARCHAR(255),
ADD COLUMN age_group VARCHAR(100),
ADD COLUMN customer_segment VARCHAR(100),
ADD COLUMN device VARCHAR(100);
