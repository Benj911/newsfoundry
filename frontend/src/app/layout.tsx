/**
 * Module : Layout Principal (Root Layout)
 * =======================================
 * Ce fichier définit la structure HTML de base de l'application Next.js.
 * Il agit comme un conteneur parent pour toutes les pages, ce qui permet 
 * de configurer les métadonnées (SEO), d'importer les styles globaux, 
 * et d'appliquer une structure DOM persistante.
 */

import type { Metadata } from "next";
import "./globals.css";

// ============================================================================
// MÉTADONNÉES ET RÉFÉRENCEMENT (SEO)
// ============================================================================

/**
 * Configuration des balises meta globales de l'application.
 * Next.js utilise cet objet pour générer automatiquement la section <head> 
 * du document HTML (titre de l'onglet, description pour les moteurs de recherche).
 */
export const metadata: Metadata = {
  title: "NewsFoundry | Assistant Revue de Presse IA",
  description: "Générez vos revues de presse intelligentes et discutez de l'actualité grâce à l'IA.",
};

// ============================================================================
// COMPOSANT RACINE
// ============================================================================

/**
 * Composant RootLayout englobant toute l'application.
 * 
 * @param {React.ReactNode} children - Les pages ou composants enfants (injectés dynamiquement par le routeur).
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // "lang='fr'" est indispensable pour l'accessibilité et le référencement.
    // "antialiased" permet un lissage optique des polices sur les écrans modernes.
    <html lang="fr" className="h-full antialiased">
      {/* 
        Le body est configuré pour occuper au minimum toute la hauteur de l'écran (min-h-full)
        et utiliser Flexbox en colonne pour faciliter le placement des composants enfants.
        La police 'Inter' est déclarée ici pour s'appliquer à toute l'application par défaut.
      */}
      <body className="min-h-full flex flex-col font-['Inter']">
        {children}
      </body>
    </html>
  );
}