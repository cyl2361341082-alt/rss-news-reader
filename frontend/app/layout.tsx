import type { ReactNode } from "react";
import type { Metadata } from "next";

import { Header } from "@/components/Header";
import "./globals.css";

export const metadata: Metadata = {
  title: "rss-news-reader",
  description: "A quiet local reading interface for collected RSS articles."
};

const themeScript = `
  try {
    var theme = localStorage.getItem("theme-mode") || "light";
    var readerFont = localStorage.getItem("reader-font-size") || "md";
    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.readerFont = readerFont;
  } catch (error) {}
`;

export default function RootLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-page text-text antialiased">
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <Header />
        <main>{children}</main>
      </body>
    </html>
  );
}
