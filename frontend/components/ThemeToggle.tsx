"use client";

import { useEffect, useState } from "react";

type ThemeMode = "light" | "dark";

const VALID_THEMES: ThemeMode[] = ["light", "dark"];

function readTheme(): ThemeMode {
  if (typeof document !== "undefined" && document.documentElement.dataset.theme) {
    const v = document.documentElement.dataset.theme as ThemeMode;
    if (VALID_THEMES.includes(v)) return v;
  }
  if (typeof window !== "undefined") {
    try {
      const raw = window.localStorage.getItem("theme-mode");
      if (raw && VALID_THEMES.includes(raw as ThemeMode)) return raw as ThemeMode;
    } catch {
      /* localStorage unavailable */
    }
  }
  return "light";
}

export function ThemeToggle() {
  const [theme, setTheme] = useState<ThemeMode>(readTheme);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const resolved = readTheme();
    document.documentElement.dataset.theme = resolved;
    setTheme(resolved);
  }, []);

  function toggleTheme() {
    const next: ThemeMode = theme === "light" ? "dark" : "light";
    document.documentElement.dataset.theme = next;
    try {
      window.localStorage.setItem("theme-mode", next);
    } catch {
      /* ignore */
    }
    setTheme(next);
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="rounded-full border border-line/80 bg-surface px-3 py-2 text-sm text-muted hover:text-text"
      aria-label="Toggle theme"
    >
      {mounted ? (theme === "light" ? "Dark" : "Light") : " "}
    </button>
  );
}
