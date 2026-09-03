import type { Metadata } from "next";
import { Archivo, Source_Serif_4 } from "next/font/google";

import "./globals.css";

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const sourceSerif = Source_Serif_4({
  variable: "--font-source-serif",
  subsets: ["latin"],
  weight: ["400", "600"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Nyhetsradar",
  description: "Ukens nyheter for Selvaag Eiendom.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="no"
      className={`${archivo.variable} ${sourceSerif.variable} h-full`}
    >
      <body className="min-h-full">{children}</body>
    </html>
  );
}
