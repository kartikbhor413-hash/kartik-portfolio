-- ==============================================================================
-- KARTIK BHOR PORTFOLIO - SUPABASE DATABASE SCHEMA
-- Project: https://supabase.com/dashboard/project/uhreznoytbvlommykqpe
-- ==============================================================================
-- Instructions:
-- 1. Open your Supabase Dashboard: https://supabase.com/dashboard/project/uhreznoytbvlommykqpe
-- 2. Go to the "SQL Editor" tab from the left sidebar.
-- 3. Click "New query", paste this entire script, and click "Run".
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. Table: contact_messages
-- Stores verified messages sent by visitors after successful email OTP verification.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.contact_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for searching messages by email or date
CREATE INDEX IF NOT EXISTS idx_contact_messages_email ON public.contact_messages(email);
CREATE INDEX IF NOT EXISTS idx_contact_messages_created ON public.contact_messages(created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE public.contact_messages ENABLE ROW LEVEL SECURITY;

-- Security Policy:
-- Service role (backend) has full read/write access.
-- Public / anonymous users CANNOT read contact messages.
DROP POLICY IF EXISTS "Service role full access on contact_messages" ON public.contact_messages;
CREATE POLICY "Service role full access on contact_messages" 
    ON public.contact_messages
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Optional: Allow backend using anon key with restricted INSERT only if service role is not used
DROP POLICY IF EXISTS "Allow anon insert for verified messages" ON public.contact_messages;
CREATE POLICY "Allow anon insert for verified messages"
    ON public.contact_messages
    FOR INSERT
    TO anon
    WITH CHECK (true);

-- ------------------------------------------------------------------------------
-- 2. Table: email_otps
-- Manages short-lived, cryptographically hashed OTPs and verification sessions.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.email_otps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    session_token VARCHAR(128) NOT NULL UNIQUE,
    otp_hash VARCHAR(128) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    attempts INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 5,
    verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for lightning-fast OTP lookups & expiration pruning
CREATE INDEX IF NOT EXISTS idx_email_otps_session ON public.email_otps(session_token);
CREATE INDEX IF NOT EXISTS idx_email_otps_email ON public.email_otps(email);
CREATE INDEX IF NOT EXISTS idx_email_otps_expires ON public.email_otps(expires_at);

-- Enable Row Level Security (RLS)
ALTER TABLE public.email_otps ENABLE ROW LEVEL SECURITY;

-- Security Policy:
-- OTP table must NEVER be readable by anonymous web visitors!
DROP POLICY IF EXISTS "Service role full access on email_otps" ON public.email_otps;
CREATE POLICY "Service role full access on email_otps"
    ON public.email_otps
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ------------------------------------------------------------------------------
-- 3. Maintenance Helper: Cleanup Expired OTPs
-- Can be called periodically or via Supabase Scheduled Edge Function/pg_cron.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.cleanup_expired_otps()
RETURNS INT AS $$
DECLARE
    deleted_count INT;
BEGIN
    DELETE FROM public.email_otps
    WHERE expires_at < NOW() - INTERVAL '1 day';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
