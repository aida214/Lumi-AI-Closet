-- =====================================================================
-- LUMI CLOSET — SCHEMA
-- =====================================================================
-- This is the same schema as before, with a few additions needed for
-- the redesign, plus Row Level Security policies. The app used to run
-- every query through the Supabase *service role* key, which bypasses
-- RLS entirely -- fine for a trusted backend, but risky for a client
-- app, and it meant these tables had no real access control of their
-- own. The app now uses the anon key + the logged-in user's session,
-- so these policies are what actually keeps one user's wardrobe
-- private from another's.
--
-- Safe to re-run: every statement uses IF NOT EXISTS / OR REPLACE.
-- =====================================================================

-- =========================
-- PROFILES (User info)
-- =========================
create table if not exists profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    username text,
    full_name text,
    avatar_url text,
    preferred_aesthetic text[] default '{}',
    favorite_categories text[] default '{}',
    favorite_colors text[] default '{}',
    created_at timestamp default now()
);

alter table profiles add column if not exists preferred_aesthetic text[] default '{}';
alter table profiles add column if not exists favorite_categories text[] default '{}';
alter table profiles add column if not exists favorite_colors text[] default '{}';

-- =========================
-- WARDROBE (Clothes items)
-- =========================
create table if not exists wardrobe (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references profiles(id) on delete cascade,
    image_url text,
    name text,
    category text,
    color text,
    season text,
    style text,
    brand text,
    favorite boolean default false,
    created_at timestamp default now()
);

-- The original table was missing `name`, even though the upload form
-- always wrote one -- every insert was silently dropping it.
alter table wardrobe add column if not exists name text;

-- =========================
-- SAVED OUTFITS
-- =========================
create table if not exists saved_outfits (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references profiles(id) on delete cascade,
    title text,
    notes text,
    favorite boolean default false,
    created_at timestamp default now()
);

alter table saved_outfits add column if not exists favorite boolean default false;

-- Junction table: which wardrobe pieces make up a saved outfit
-- (needed for the Outfit Builder / Saved Looks pages).
create table if not exists outfit_items (
    id uuid default gen_random_uuid() primary key,
    outfit_id uuid references saved_outfits(id) on delete cascade,
    wardrobe_item_id uuid references wardrobe(id) on delete cascade,
    created_at timestamp default now()
);

-- =========================
-- PLANNER
-- =========================
create table if not exists planner (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references profiles(id) on delete cascade,
    outfit_id uuid references saved_outfits(id) on delete cascade,
    date date,
    created_at timestamp default now()
);

-- =========================
-- FAVORITES
-- =========================
create table if not exists favorites (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references profiles(id) on delete cascade,
    wardrobe_item_id uuid references wardrobe(id) on delete cascade,
    created_at timestamp default now()
);

-- =========================
-- CHAT HISTORY (AI Stylist)
-- =========================
create table if not exists chat_history (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references profiles(id) on delete cascade,
    role text,
    message text,
    created_at timestamp default now()
);

-- =====================================================================
-- ROW LEVEL SECURITY
-- =====================================================================
alter table profiles enable row level security;
alter table wardrobe enable row level security;
alter table saved_outfits enable row level security;
alter table outfit_items enable row level security;
alter table planner enable row level security;
alter table favorites enable row level security;
alter table chat_history enable row level security;

-- profiles: a user can read/update only their own row
drop policy if exists "profiles_select_own" on profiles;
create policy "profiles_select_own" on profiles
    for select using (auth.uid() = id);

drop policy if exists "profiles_insert_own" on profiles;
create policy "profiles_insert_own" on profiles
    for insert with check (auth.uid() = id);

drop policy if exists "profiles_update_own" on profiles;
create policy "profiles_update_own" on profiles
    for update using (auth.uid() = id);

-- generic "owns the row via user_id" policy, applied per table
do $$
declare
    t text;
begin
    foreach t in array array['wardrobe', 'saved_outfits', 'planner', 'favorites', 'chat_history']
    loop
        execute format('drop policy if exists "%1$s_owner_all" on %1$s;', t);
        execute format(
            'create policy "%1$s_owner_all" on %1$s for all using (auth.uid() = user_id) with check (auth.uid() = user_id);',
            t
        );
    end loop;
end $$;

-- outfit_items: access follows the parent outfit's owner
drop policy if exists "outfit_items_owner_all" on outfit_items;
create policy "outfit_items_owner_all" on outfit_items
    for all using (
        exists (
            select 1 from saved_outfits o
            where o.id = outfit_items.outfit_id and o.user_id = auth.uid()
        )
    )
    with check (
        exists (
            select 1 from saved_outfits o
            where o.id = outfit_items.outfit_id and o.user_id = auth.uid()
        )
    );

-- =====================================================================
-- STORAGE
-- =====================================================================
-- Create a public "wardrobe" storage bucket for clothing photos from
-- the Supabase dashboard (Storage -> New bucket -> name it "wardrobe",
-- toggle "Public bucket" on) if it doesn't already exist. The app
-- uploads to it via supabase.storage.from_("wardrobe").
