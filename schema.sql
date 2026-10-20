-- ==============================================================================
-- KARTIK BHOR PORTFOLIO - SUPABASE DATABASE SCHEMA
-- Project: https://supabase.com/dashboard/project/uhreznoytbvlommykqpe
-- ==============================================================================
-- INSTRUCTIONS:
-- 1. Open your Supabase Dashboard: https://supabase.com/dashboard/project/uhreznoytbvlommykqpe
-- 2. Go to "SQL Editor" in the left sidebar.
-- 3. Click "New query" (or clear your existing editor window).
-- 4. Paste this entire script below.
-- 5. IMPORTANT: Make sure NO text is highlighted/selected with your mouse!
-- 6. Click the green "Run" button (or press Ctrl + Enter).
-- ==============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. Create Table: contact_messages
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_contact_messages_email ON public.contact_messages(email);
CREATE INDEX IF NOT EXISTS idx_contact_messages_created ON public.contact_messages(created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE public.contact_messages ENABLE ROW LEVEL SECURITY;

-- Safe Policy Creation (Checks if policy exists first to prevent any 42P01 error)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'contact_messages' 
        AND policyname = 'Service role full access on contact_messages'
    ) THEN
        CREATE POLICY "Service role full access on contact_messages" 
        ON public.contact_messages
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'contact_messages' 
        AND policyname = 'Allow anon insert for verified messages'
    ) THEN
        CREATE POLICY "Allow anon insert for verified messages"
        ON public.contact_messages
        FOR INSERT
        TO anon
        WITH CHECK (true);
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- 2. Create Table: email_otps
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

-- Indexes for lightning-fast OTP lookups
CREATE INDEX IF NOT EXISTS idx_email_otps_session ON public.email_otps(session_token);
CREATE INDEX IF NOT EXISTS idx_email_otps_email ON public.email_otps(email);
CREATE INDEX IF NOT EXISTS idx_email_otps_expires ON public.email_otps(expires_at);

-- Enable Row Level Security (RLS)
ALTER TABLE public.email_otps ENABLE ROW LEVEL SECURITY;

-- Safe Policy Creation for email_otps
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'email_otps' 
        AND policyname = 'Service role full access on email_otps'
    ) THEN
        CREATE POLICY "Service role full access on email_otps"
        ON public.email_otps
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- 3. Maintenance Function: Cleanup Expired OTPs
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
