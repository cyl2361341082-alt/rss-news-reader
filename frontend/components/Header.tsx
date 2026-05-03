import Link from "next/link";

import { ThemeToggle } from "@/components/ThemeToggle";

export function Header() {
  return (
    <header className="sticky top-0 z-20 border-b border-line/80 bg-page/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 md:px-8">
        <div className="space-y-1">
          <Link href="/" className="text-sm uppercase tracking-[0.28em] text-muted">
            rss-news-reader
          </Link>
          <p className="text-sm text-muted">Quiet local reading for collected news.</p>
        </div>
        <nav className="flex items-center gap-3 text-sm text-muted">
          <Link href="/" className="hover:text-text">
            Home
          </Link>
          <Link href="/search" className="hover:text-text">
            Search
          </Link>
          <Link href="/sources" className="hover:text-text">
            Sources
          </Link>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
