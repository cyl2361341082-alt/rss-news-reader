import Link from "next/link";

import { ArticleCard } from "@/components/ArticleCard";
import { getArticles, getSources } from "@/lib/api";
import { titleCase } from "@/lib/utils";

export const dynamic = "force-dynamic";

interface SourcesPageProps {
  searchParams?: {
    source?: string;
  };
}

export default async function SourcesPage({ searchParams }: SourcesPageProps) {
  const currentSource = searchParams?.source || "";

  try {
    const [sources, articlePage] = await Promise.all([
      getSources(),
      currentSource ? getArticles({ page: 1, pageSize: 12, source: currentSource }) : Promise.resolve(null)
    ]);

    return (
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-5 py-10 md:px-8 md:py-14">
        <section className="max-w-3xl space-y-4">
          <p className="text-sm uppercase tracking-[0.28em] text-muted">Sources</p>
          <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">Browse by publication</h1>
          <p className="text-base leading-8 text-muted">
            Each source keeps its own tone and cadence, but the reading surface stays quiet and consistent.
          </p>
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          {sources.map((source) => (
            <Link
              key={source.id}
              href={`/sources?source=${source.id}`}
              className={`rounded-[1.4rem] border px-5 py-5 ${
                currentSource === source.id ? "border-text bg-surface" : "border-line bg-surface"
              }`}
            >
              <div className="space-y-2">
                <p className="text-sm text-muted">{titleCase(source.category)}</p>
                <h2 className="text-xl font-semibold tracking-tight">{source.name}</h2>
                <p className="text-sm text-muted">{source.article_count} stored articles</p>
              </div>
            </Link>
          ))}
        </section>

        {currentSource && articlePage ? (
          <section className="space-y-5">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-semibold tracking-tight">
                Recent from {sources.find((source) => source.id === currentSource)?.name || currentSource}
              </h2>
            </div>
            {articlePage.items.length ? (
              articlePage.items.map((article) => <ArticleCard key={article.slug} article={article} />)
            ) : (
              <div className="rounded-[1.6rem] border border-dashed border-line bg-surface px-8 py-12 text-center text-muted">
                No stored articles for this source yet.
              </div>
            )}
          </section>
        ) : null}
      </div>
    );
  } catch (error) {
    console.error("Failed to load sources:", error);
    return (
      <div className="mx-auto max-w-4xl px-5 py-16 md:px-8">
        <div className="rounded-[1.8rem] border border-line bg-surface px-8 py-12 text-muted">
          Unable to load sources. Confirm the backend API is running.
        </div>
      </div>
    );
  }
}
