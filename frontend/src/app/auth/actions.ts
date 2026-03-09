"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

interface AuthFormData {
  email: string;
  password: string;
}

function extractAuthFields(formData: FormData): AuthFormData {
  const email = formData.get("email");
  const password = formData.get("password");

  if (typeof email !== "string" || typeof password !== "string") {
    throw new Error("Invalid form data: email and password must be strings.");
  }

  const trimmedEmail = email.trim().toLowerCase();

  if (trimmedEmail.length === 0 || password.length === 0) {
    throw new Error("Email and password are required.");
  }

  if (trimmedEmail.length > 320) {
    throw new Error("Email address is too long.");
  }

  if (password.length < 6) {
    throw new Error("Password must be at least 6 characters.");
  }

  if (password.length > 256) {
    throw new Error("Password is too long.");
  }

  return { email: trimmedEmail, password };
}

export async function login(formData: FormData): Promise<void> {
  const supabase = await createClient();

  let fields: AuthFormData;
  try {
    fields = extractAuthFields(formData);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Invalid form data.";
    redirect(`/auth?error=${encodeURIComponent(message)}`);
  }

  const { error } = await supabase.auth.signInWithPassword({
    email: fields.email,
    password: fields.password,
  });

  if (error) {
    redirect(`/auth?error=${encodeURIComponent(error.message)}`);
  }

  revalidatePath("/", "layout");
  redirect("/dashboard");
}

export async function signup(formData: FormData): Promise<void> {
  const supabase = await createClient();

  let fields: AuthFormData;
  try {
    fields = extractAuthFields(formData);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Invalid form data.";
    redirect(`/auth?error=${encodeURIComponent(message)}`);
  }

  const { error } = await supabase.auth.signUp({
    email: fields.email,
    password: fields.password,
  });

  if (error) {
    redirect(`/auth?error=${encodeURIComponent(error.message)}`);
  }

  revalidatePath("/", "layout");
  redirect(
    `/auth?message=${encodeURIComponent(
      "Check your email to confirm your account before signing in."
    )}`
  );
}

export async function signOut(): Promise<void> {
  const supabase = await createClient();
  const { error } = await supabase.auth.signOut();

  if (error) {
    throw new Error(`Sign out failed: ${error.message}`);
  }

  revalidatePath("/", "layout");
  redirect("/auth");
}
