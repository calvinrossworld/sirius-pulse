-- Add bios column to plans table (run in Supabase SQL Editor)
ALTER TABLE plans ADD COLUMN IF NOT EXISTS bios JSONB DEFAULT '[]'::jsonb;
