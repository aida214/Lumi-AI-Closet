-- Lumi Closet database schema.
-- Run the whole file once in the Supabase SQL editor. It is safe to run again.
-- Every table uses Row Level Security: a signed-in user can only touch rows
-- where user_id = auth.uid(). The app only ships the public anon key.

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------- profiles
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  full_name text,
  username text,
  city text,
  favorite_aesthetics text,
  created_at timestamptz not null default now()
);
alter table public.profiles add column if not exists city text;

-- ---------------------------------------------------------------- wardrobe
create table if not exists public.wardrobe (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  name text,
  category text,
  color text,
  season text,
  style text,
  brand text,
  price numeric(10,2) check (price is null or price >= 0),
  image_url text,
  favorite boolean not null default false,
  created_at timestamptz not null default now()
);
alter table public.wardrobe add column if not exists price numeric(10,2);

-- ---------------------------------------------------------------- wear log
create table if not exists public.wear_log (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  wardrobe_item_id uuid not null references public.wardrobe(id) on delete cascade,
  worn_on date not null,
  created_at timestamptz not null default now(),
  unique (wardrobe_item_id, worn_on)
);

-- ---------------------------------------------------------------- outfits
create table if not exists public.saved_outfits (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  title text not null,
  notes text,
  occasion text,
  favorite boolean not null default false,
  created_at timestamptz not null default now()
);
alter table public.saved_outfits add column if not exists occasion text;
alter table public.saved_outfits add column if not exists favorite boolean not null default false;

create table if not exists public.outfit_items (
  id uuid primary key default gen_random_uuid(),
  outfit_id uuid not null references public.saved_outfits(id) on delete cascade,
  wardrobe_item_id uuid not null references public.wardrobe(id) on delete cascade,
  unique (outfit_id, wardrobe_item_id)
);

-- ---------------------------------------------------------------- planner
create table if not exists public.planner (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  date date not null,
  outfit_id uuid references public.saved_outfits(id) on delete set null,
  created_at timestamptz not null default now()
);
-- One outfit per day per user. If this fails, delete duplicate planner rows first.
create unique index if not exists planner_user_date_key on public.planner (user_id, date);

-- ---------------------------------------------------------------- chat
create table if not exists public.chat_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  message text not null,
  created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------- indexes
create index if not exists wardrobe_user_created_idx on public.wardrobe (user_id, created_at desc);
create index if not exists wear_log_user_idx on public.wear_log (user_id, worn_on);
create index if not exists outfits_user_created_idx on public.saved_outfits (user_id, created_at desc);
create index if not exists outfit_items_outfit_idx on public.outfit_items (outfit_id);
create index if not exists chat_user_created_idx on public.chat_history (user_id, created_at desc);

-- ---------------------------------------------------------------- RLS
alter table public.profiles enable row level security;
alter table public.wardrobe enable row level security;
alter table public.wear_log enable row level security;
alter table public.saved_outfits enable row level security;
alter table public.outfit_items enable row level security;
alter table public.planner enable row level security;
alter table public.chat_history enable row level security;

drop policy if exists "profiles_own" on public.profiles;
create policy "profiles_own" on public.profiles for all to authenticated
  using (id = auth.uid()) with check (id = auth.uid());

drop policy if exists "wardrobe_own" on public.wardrobe;
create policy "wardrobe_own" on public.wardrobe for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

drop policy if exists "wear_log_own" on public.wear_log;
create policy "wear_log_own" on public.wear_log for all to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid()
    and exists (select 1 from public.wardrobe w where w.id = wardrobe_item_id and w.user_id = auth.uid()));

drop policy if exists "outfits_own" on public.saved_outfits;
create policy "outfits_own" on public.saved_outfits for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

-- outfit_items has no user_id, so ownership is checked through the parent outfit
-- and the wardrobe item being linked.
drop policy if exists "outfit_items_own" on public.outfit_items;
create policy "outfit_items_own" on public.outfit_items for all to authenticated
  using (exists (select 1 from public.saved_outfits o where o.id = outfit_id and o.user_id = auth.uid()))
  with check (
    exists (select 1 from public.saved_outfits o where o.id = outfit_id and o.user_id = auth.uid())
    and exists (select 1 from public.wardrobe w where w.id = wardrobe_item_id and w.user_id = auth.uid())
  );

drop policy if exists "planner_own" on public.planner;
create policy "planner_own" on public.planner for all to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid()
    and (outfit_id is null or exists (select 1 from public.saved_outfits o where o.id = outfit_id and o.user_id = auth.uid())));

drop policy if exists "chat_own" on public.chat_history;
create policy "chat_own" on public.chat_history for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

-- ---------------------------------------------------------------- new users
-- Create the profile row automatically when someone signs up, so it exists
-- even when email confirmation is switched on.
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, coalesce(new.raw_user_meta_data ->> 'full_name', ''))
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- Backfill profiles for accounts created before this trigger existed.
insert into public.profiles (id, email)
select id, email from auth.users
on conflict (id) do nothing;

-- ---------------------------------------------------------------- storage
-- Public bucket: photos are served through Supabase's CDN. Object names are
-- random, and each user can only write inside a folder named after their id.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('wardrobe', 'wardrobe', true, 10485760, array['image/jpeg','image/png','image/webp'])
on conflict (id) do update
  set public = true, file_size_limit = 10485760,
      allowed_mime_types = array['image/jpeg','image/png','image/webp'];

drop policy if exists "wardrobe_images_read" on storage.objects;
create policy "wardrobe_images_read" on storage.objects for select
  using (bucket_id = 'wardrobe');

drop policy if exists "wardrobe_images_insert_own" on storage.objects;
create policy "wardrobe_images_insert_own" on storage.objects for insert to authenticated
  with check (bucket_id = 'wardrobe' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists "wardrobe_images_update_own" on storage.objects;
create policy "wardrobe_images_update_own" on storage.objects for update to authenticated
  using (bucket_id = 'wardrobe' and (storage.foldername(name))[1] = auth.uid()::text);

drop policy if exists "wardrobe_images_delete_own" on storage.objects;
create policy "wardrobe_images_delete_own" on storage.objects for delete to authenticated
  using (bucket_id = 'wardrobe' and (storage.foldername(name))[1] = auth.uid()::text);
