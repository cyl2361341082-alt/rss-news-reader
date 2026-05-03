import Link from "next/link";

import { ArticleMeta } from "@/components/ArticleMeta";
import { ArticleSummary } from "@/lib/types";

interface ArticleCardProps {
  article: ArticleSummary;
}

export function ArticleCard({ article }: ArticleCardProps) {
  return (
    <article className="rounded-[1.6rem] border border-line/70 bg-surface px-6 py-6 shadow-quiet">
      <div className="space-y-4">
        <ArticleMeta
          sourceId={article.source_id}
          publishedAt={article.published_at}
          fetchedAt={article.fetched_at}
          readingTimeMinutes={article.reading_time_minutes}
          category={article.category}
        />
        <div className="space-y-3">
          <Link href={`/article/${article.slug}`} className="block text-2xl font-semibold tracking-tight text-text">
            {article.title}
          </Link>
          <p className="max-w-3xl text-[15px] leading-7 text-muted">{article.summary}</p>
        </div>
        <div>
          <Link href={`/article/${article.slug}`} className="text-sm text-accent hover:opacity-80">
            Read article
          </Link>
        </div>
      </div>
    </article>
  );
}
