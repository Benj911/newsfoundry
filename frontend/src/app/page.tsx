"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const storedToken = localStorage.getItem("token");
    setToken(storedToken);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    router.refresh();
  };

  if (!mounted) return null;

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-50 text-gray-900">
      <div className="w-full max-w-xl rounded-xl bg-white p-8 shadow-md text-center space-y-6">
        <h1 className="text-4xl font-extrabold tracking-tight">NewsFoundry</h1>
        <p className="text-lg text-gray-600">
          Plateforme de revue de presse automatique
        </p>

        {token ? (
          <div className="space-y-4 rounded-lg bg-green-50 p-6 border border-green-200">
            <p className="text-green-800 font-semibold">
              ✅ Vous êtes authentifié !
            </p>
            <p className="text-xs text-gray-500 break-all bg-white p-3 rounded border font-mono">
              Token : {token}
            </p>
            <button
              onClick={handleLogout}
              className="mt-4 inline-flex items-center justify-center rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none"
            >
              Se déconnecter
            </button>
          </div>
        ) : (
          <div className="space-y-4 rounded-lg bg-gray-100 p-6">
            <p className="text-gray-700">Vous n'êtes pas connecté.</p>
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-md bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none"
            >
              Accéder à la page de connexion
            </Link>
          </div>
        )}
      </div>
    </main>
  );
}