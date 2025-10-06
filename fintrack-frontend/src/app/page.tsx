"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "./providers";

export default function Home() {
  const router = useRouter();
  const { auth } = useApp();

  useEffect(() => {
    if (!auth.isLoading) {
      if (auth.isAuthenticated) {
        router.push("/dashboard");
      } else {
        router.push("/login");
      }
    }
  }, [auth.isAuthenticated, auth.isLoading, router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading FinTrack...</p>
      </div>
    </div>
  );
}
