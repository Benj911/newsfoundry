"use client";

/**
 * Module : Page de Connexion
 * ==========================
 * Ce composant gère l'interface d'authentification de l'application NewsFoundry.
 * Il permet à l'utilisateur de saisir ses identifiants, communique avec l'API 
 * pour valider la session, stocke le jeton JWT, et gère la redirection 
 * vers l'interface principale.
 */

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Bot } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  
  // ============================================================================
  // ÉTATS LOCAUX (STATE)
  // ============================================================================
  
  const [email, setEmail] = useState("");
  // Le mot de passe est pré-rempli pour faciliter le développement/test
  const [password, setPassword] = useState("test");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // ============================================================================
  // GESTIONNAIRES D'ÉVÉNEMENTS (HANDLERS)
  // ============================================================================

  /**
   * Gère la soumission du formulaire d'authentification.
   * 
   * @param {FormEvent<HTMLFormElement>} e - L'événement de soumission intercepté.
   */
  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    // Empêche le comportement par défaut du navigateur (rechargement de la page)
    e.preventDefault();
    
    // Réinitialisation de l'état avant la nouvelle tentative de connexion
    setError(null);
    setIsLoading(true);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      // Appel à la route d'authentification du backend
      const response = await fetch(`${apiUrl}/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      // Gestion des réponses non fructueuses (ex: 401 Unauthorized)
      if (!response.ok) {
        throw new Error(data.detail || "Échec de l'authentification.");
      }

      // Enregistrement du jeton de session dans le stockage local du navigateur
      localStorage.setItem("token", data.access_token);
      
      // Redirection immédiate vers l'application principale une fois connecté
      router.push("/");
      
    } catch (err: unknown) {
      // Affichage du message d'erreur approprié à l'utilisateur
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Une erreur inattendue est survenue.");
      }
    } finally {
      // Libération de l'interface indépendamment du succès ou de l'échec
      setIsLoading(false);
    }
  };

  // ============================================================================
  // RENDU VISUEL (RENDER)
  // ============================================================================

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-[#1a1b23] px-4 overflow-hidden font-['Inter']">
      
      {/* 1. ARRIÈRE-PLAN : Motif de grille sombre intégré en CSS inline */}
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

      {/* 2. CONTENEUR PRINCIPAL : Carte de connexion centrée */}
      <div className="relative z-10 w-full max-w-[420px] rounded-2xl bg-white p-10 shadow-2xl">
        
        {/* En-tête avec le logo et le sous-titre */}
        <div className="text-center">
          <h1 className="flex items-center justify-center gap-2 text-[17px] font-normal tracking-wider text-[#803CDA]">
            NEWSFOUNDRY <Bot size={20} />
          </h1>
          <p className="mt-2 text-[14px] font-normal leading-relaxed text-[#717182]">
            Connectez-vous pour accéder à votre assistant <br />
            d'actualités IA
          </p>
        </div>

        {/* 3. AFFICHAGE DES ERREURS : Bannière conditionnelle */}
        {error && (
          <div
            role="alert"
            className="mt-4 rounded-lg bg-red-50 p-3 text-xs font-medium text-red-600 text-center"
          >
            {error}
          </div>
        )}

        {/* 4. FORMULAIRE : Champs de saisie et bouton de validation */}
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="email"
              className="block text-[16px] font-normal text-[#2A2A31] mb-1.5"
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
              className="block w-full rounded-lg bg-[#ECEEF2] border-0 px-4 py-3 text-[16px] font-normal text-[#717182] placeholder-[#717182] focus:outline-none focus:ring-2 focus:ring-[#803CDA]"
              placeholder="votre.email@exemple.com"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-lg bg-[#2A2A31] py-3 text-[14px] font-normal text-white transition-colors hover:bg-[#717182] focus:outline-none focus:ring-2 focus:ring-[#272930] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 mt-2"
          >
            {isLoading ? "Connexion..." : "Se connecter"}
          </button>
        </form>
        
      </div>
    </div>
  );
}