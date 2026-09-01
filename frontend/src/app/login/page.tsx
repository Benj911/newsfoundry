"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("test");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      const response = await fetch(`${apiUrl}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Échec de l'authentification.");
      }

      localStorage.setItem("token", data.access_token);
      router.push("/");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Une erreur inattendue est survenue.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-[#1a1b23] px-4 overflow-hidden">
      {/* Motif de grille sombre d'arrière-plan */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, #4f5b66 1px, transparent 1px),
            linear-gradient(to bottom, #4f5b66 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
        }}
      />

      <div className="relative z-10 w-full max-w-[420px] rounded-2xl bg-white p-10 shadow-2xl">
        <div className="text-center">
          <h1 className="flex items-center justify-center gap-2 text-xl font-bold tracking-wider text-[#7c5cfc]">
            NEWSFOUNDRY <span className="text-lg">🤖</span>
          </h1>
          <p className="mt-2 text-xs leading-relaxed text-gray-500">
            Connectez-vous pour accéder à votre assistant <br />
            d'actualités IA
          </p>
        </div>

        {error && (
          <div
            role="alert"
            className="mt-4 rounded-lg bg-red-50 p-3 text-xs font-medium text-red-600 text-center"
          >
            {error}
          </div>
        )}

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="email"
              className="block text-xs font-medium text-gray-700 mb-1.5"
            >
              Adresse email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="block w-full rounded-lg bg-[#ebf0f5] border-0 px-3.5 py-2.5 text-xs text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#7c5cfc]"
              placeholder="votre.email@exemple.com"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-lg bg-[#272930] py-2.5 text-xs font-medium text-white transition-colors hover:bg-[#1e2025] focus:outline-none focus:ring-2 focus:ring-[#272930] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 mt-2"
          >
            {isLoading ? "Connexion..." : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  );
}