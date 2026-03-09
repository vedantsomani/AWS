"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { TopBar } from "@/components/ide/TopBar";
import { StatusBar } from "@/components/ide/StatusBar";
import { useAuthStore } from "@/store/useAuthStore";

const IdeLayout = dynamic(
  () => import("@/components/ide/IdeLayout").then((m) => m.IdeLayout),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center bg-[#0A0A0B]">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-700 border-t-blue-500" />
      </div>
    ),
  }
);

interface DashboardShellProps {
  userEmail: string;
}

export function DashboardShell({ userEmail }: DashboardShellProps) {
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
    <div className="flex h-screen flex-col overflow-hidden bg-[#0A0A0B] text-zinc-200">
      <TopBar userEmail={userEmail} onSignOut={handleSignOut} />
      <div className="flex-1 overflow-hidden">
        <IdeLayout />
      </div>
      <StatusBar />
    </div>
  );
}
