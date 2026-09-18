-- Migration 006: Make campaign revenue nullable
ALTER TABLE campaigns
ALTER COLUMN revenue DROP DEFAULT;