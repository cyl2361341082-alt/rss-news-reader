"use client";

import { useEffect } from "react";

export default function ErrorPage({
  error,
  reset
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Page error:", error);
  }, [error]);

  return (
    <div className="mx-auto max-w-4xl px-5 py-16 md:px-8">
      <div className="space-y-4 rounded-[1.8rem] border border-line bg-surface px-8 py-12 text-muted">
        <p>Something went wrong while loading the page.</p>
        {error.digest ? (
          <p className="text-xs opacity-60">Error reference: {error.digest}</p>
        ) : null}
        <button type="button" onClick={reset} className="rounded-full bg-text px-5 py-3 text-sm text-page">
          Try again
        </button>
      </div>
    </div>
  );
}
