-- Roster Database Schema
-- Multi-tenant model with Organisation > Team > Member hierarchy

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (global, can belong to multiple organisations/teams)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    auth_provider VARCHAR(20) NOT NULL CHECK (auth_provider IN ('github')),
    provider_subject VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(auth_provider, provider_subject)
);

-- Organisations table (top-level container)
CREATE TABLE IF NOT EXISTS organisations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Teams table (belongs to an organisation)
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organisation_id, name)
);

-- Memberships table (user's role within a team)
CREATE TABLE IF NOT EXISTS memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'member')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, team_id)
);

-- Organisation admins (users who can manage an organisation)
CREATE TABLE IF NOT EXISTS organisation_admins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organisation_id UUID NOT NULL REFERENCES organisations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, organisation_id)
);

-- Super admins (global admins who can manage everything)
CREATE TABLE IF NOT EXISTS super_admins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_auth ON users(auth_provider, provider_subject);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_team ON memberships(team_id);
CREATE INDEX IF NOT EXISTS idx_teams_org ON teams(organisation_id);
CREATE INDEX IF NOT EXISTS idx_org_admins_user ON organisation_admins(user_id);
CREATE INDEX IF NOT EXISTS idx_org_admins_org ON organisation_admins(organisation_id);

-- MVP Seed Data: Single organisation, single team, single user as admin
-- This will be populated by your application logic, but here's the structure:
-- 
-- INSERT INTO organisations (name) VALUES ('Default Organisation') ON CONFLICT DO NOTHING;
-- 
-- INSERT INTO teams (organisation_id, name) 
-- VALUES (
--     (SELECT id FROM organisations WHERE name = 'Default Organisation' LIMIT 1),
--     'Default Team'
-- ) ON CONFLICT DO NOTHING;
--
-- -- When a user authenticates via GitHub, your app will:
-- -- 1. Insert into users (if not exists)
-- -- 2. Make them admin of Default Organisation
-- -- 3. Make them admin of Default Team
-- -- 4. Add them as member of Default Team

-- Future: Subscription limits tables (for when you add paid plans)
-- CREATE TABLE organisation_limits (
--     organisation_id UUID PRIMARY KEY REFERENCES organisations(id) ON DELETE CASCADE,
--     max_teams INTEGER DEFAULT 10,
--     max_members_per_team INTEGER DEFAULT 50,
--     max_organisations INTEGER DEFAULT 1
-- );
