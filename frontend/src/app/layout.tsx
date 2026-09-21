import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NewsFoundry | Assistant Revue de Presse IA",
  description: "Générez vos revues de presse intelligentes et discutez de l'actualité grâce à l'IA.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-['Inter']">
        {children}
      </body>
    </html>
  );
}