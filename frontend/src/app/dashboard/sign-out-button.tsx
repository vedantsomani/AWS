"use client";

import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { Button } from "@/components/ui/button";

export function SignOutButton() {
  const router = useRouter();
  const { signOut } = useAuthStore();

  const handleSignOut = async () => {
    try {
      await signOut();
      router.push("/auth");
    } catch {
      // Error handled in store
    }
  };

  return (
    <Button variant="outline" type="button" onClick={handleSignOut}>
      Sign Out
    </Button>
  );
}
