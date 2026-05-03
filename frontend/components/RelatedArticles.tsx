import Link from "next/link";

import { ArticleSummary } from "@/lib/types";
import { formatDate } from "@/lib/utils";

interface RelatedArticlesProps {
  items: ArticleSummary[];
}

export function RelatedArticles({ items }: RelatedArticlesProps) {
  if (!items.length) {
    return null;
  }

  return (
    <section className="space-y-4">
      <h2 className="text-xl font-semibold tracking-tight">Related reading</h2>
      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => (
          <Link
            key={item.slug}
            href={`/article/${item.slug}`}
            className="rounded-[1.3rem] border border-line/70 bg-surface px-5 py-4"
          >
            <div className="space-y-2">
              <p className="text-sm text-muted">
                {item.source_id} · {formatDate(item.published_at)}
              </p>
              <h3 className="text-lg font-semibold tracking-tight">{item.title}</h3>
              <p className="text-sm leading-6 text-muted">{item.summary}</p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
