"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { DashboardShell } from "@/app/dashboard/dashboard-shell";
import { useAuthStore } from "@/store/useAuthStore";
import { DisclaimerModal } from "@/components/ui/disclaimer-modal";

export default function DashboardPage() {
  const router = useRouter();
  const { user, loading, initialize } = useAuthStore();
  const [disclaimersComplete, setDisclaimersComplete] = useState(false);

  // Initialize auth listener on mount
  useEffect(() => {
    const unsubscribe = initialize();
    return unsubscribe;
  }, [initialize]);

  // Redirect to auth if not logged in
  useEffect(() => {
    if (!loading && !user) {
      router.push("/auth");
    }
  }, [user, loading, router]);

  const handleDisclaimersComplete = useCallback(() => {
    setDisclaimersComplete(true);
  }, []);

  // Show loading state while checking auth
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0A0A0B]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-700 border-t-blue-500" />
      </div>
    );
  }

  // Don't render if not authenticated
  if (!user) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#0A0A0B]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-zinc-700 border-t-blue-500" />
      </div>
    );
  }

  return (
    <>
      {!disclaimersComplete && (
        <DisclaimerModal
          userId={user.uid}
          onComplete={handleDisclaimersComplete}
        />
      )}
      <DashboardShell userEmail={user.email || "Unknown"} />
    </>
  );
}
