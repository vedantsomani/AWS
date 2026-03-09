/**
 * Resolves Supabase environment variables.
 * Supports both the legacy NEXT_PUBLIC_SUPABASE_ANON_KEY and the newer
 * NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY naming convention.
 */

function getUrl(): string {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!url) throw new Error("Missing NEXT_PUBLIC_SUPABASE_URL");
  return url;
}

function getAnonKey(): string {
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY;
  if (!key) throw new Error("Missing NEXT_PUBLIC_SUPABASE_ANON_KEY");
  return key;
}

export function getSupabaseEnv(): { url: string; anonKey: string } {
  return { url: getUrl(), anonKey: getAnonKey() };
}

/** Direct access for client components that need the raw values. */
export const supabaseEnv = {
  get NEXT_PUBLIC_SUPABASE_URL() {
    return getUrl();
  },
  get NEXT_PUBLIC_SUPABASE_ANON_KEY() {
    return getAnonKey();
  },
};
