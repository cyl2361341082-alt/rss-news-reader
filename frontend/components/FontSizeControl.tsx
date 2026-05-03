"use client";

import { useEffect, useState } from "react";

type FontSizeMode = "sm" | "md" | "lg";

const sizes: FontSizeMode[] = ["sm", "md", "lg"];
const VALID_SIZES: FontSizeMode[] = sizes;

const LABELS: Record<FontSizeMode, string> = {
  sm: "Small font size",
  md: "Medium font size",
  lg: "Large font size",
};

function readSize(): FontSizeMode {
  if (typeof document !== "undefined" && document.documentElement.dataset.readerFont) {
    const v = document.documentElement.dataset.readerFont as FontSizeMode;
    if (VALID_SIZES.includes(v)) return v;
  }
  if (typeof window !== "undefined") {
    try {
      const raw = window.localStorage.getItem("reader-font-size");
      if (raw && VALID_SIZES.includes(raw as FontSizeMode)) return raw as FontSizeMode;
    } catch {
      /* localStorage unavailable */
    }
  }
  return "md";
}

export function FontSizeControl() {
  const [size, setSize] = useState<FontSizeMode>(readSize);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const resolved = readSize();
    document.documentElement.dataset.readerFont = resolved;
    setSize(resolved);
  }, []);

  function update(next: FontSizeMode) {
    document.documentElement.dataset.readerFont = next;
    try {
      window.localStorage.setItem("reader-font-size", next);
    } catch {
      /* ignore */
    }
    setSize(next);
  }

  if (!mounted) return null;

  return (
    <div className="inline-flex items-center gap-1 rounded-full border border-line/80 bg-surface p-1">
      {sizes.map((item) => (
        <button
          key={item}
          type="button"
          onClick={() => update(item)}
          aria-label={LABELS[item]}
          className={`rounded-full px-3 py-1.5 text-sm ${
            size === item ? "bg-text text-page" : "text-muted hover:text-text"
          }`}
        >
          {item.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
