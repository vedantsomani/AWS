import { Suspense } from "react";
import type { Metadata } from "next";

import { AuthForm } from "@/app/auth/auth-form";

export const metadata: Metadata = {
  title: "Sign In | CodeSaaS",
  description: "Sign in or create an account to get started.",
};

export default function AuthPage() {
  return (
    <Suspense fallback={null}>
      <AuthForm />
    </Suspense>
  );
}
