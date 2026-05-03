import Link from "next/link";

import { ArticleCard } from "@/components/ArticleCard";
import { SearchBar } from "@/components/SearchBar";
import { SourceFilter } from "@/components/SourceFilter";
import { getArticles, getSources } from "@/lib/api";

export const dynamic = "force-dynamic";

interface HomePageProps {
  searchParams?: {
    page?: string;
    source?: string;
    category?: string;
  };
}

function buildPaginationUrl(page: number, source?: string, category?: string): string {
  const params = new URLSearchParams();
  params.set("page", String(page));
  if (source) params.set("source", source);
  if (category) params.set("category", category);
  return `/?${params.toString()}`;
}

export default async function HomePage({ searchParams }: HomePageProps) {
  const rawPage = Number(searchParams?.page);
  const page = Number.isFinite(rawPage) && rawPage >= 1 ? Math.floor(rawPage) : 1;
  const currentSource = searchParams?.source || "";
  const currentCategory = searchParams?.category || "";

  try {
    const [sources, articlePage] = await Promise.all([
      getSources(),
      getArticles({
        page,
        pageSize: 10,
        source: currentSource || undefined,
        category: currentCategory || undefined
      })
    ]);

    return (
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-5 py-10 md:px-8 md:py-14">
        <section className="max-w-3xl space-y-5">
          <p className="text-sm uppercase tracking-[0.28em] text-muted">Collected reading</p>
          <h1 className="text-4xl font-semibold tracking-tight md:text-6xl">
            A calmer way to read the news you collect.
          </h1>
          <p className="max-w-2xl text-base leading-8 text-muted md:text-lg">
            Fresh articles are gathered from RSS, cleaned for reading, and presented with quiet spacing,
            warm neutrals, and a layout tuned for focus rather than urgency.
          </p>
          <SearchBar action="/search" />
        </section>

        <form action="/" className="space-y-4">
          <SourceFilter
            sources={sources}
            currentSource={currentSource}
            currentCategory={currentCategory}
          />
        </form>

        {articlePage.items.length ? (
          <section className="space-y-5">
            {articlePage.items.map((article) => (
              <ArticleCard key={article.slug} article={article} />
            ))}
          </section>
        ) : (
          <section className="rounded-[1.8rem] border border-dashed border-line bg-surface px-8 py-12 text-center text-muted">
            No articles match the current filters.
          </section>
        )}

        <section className="flex items-center justify-between rounded-[1.4rem] border border-line/70 bg-surface px-5 py-4 text-sm text-muted">
          <span>
            Page {articlePage.page} of {articlePage.total_pages}
          </span>
          <div className="flex gap-3">
            {articlePage.page > 1 ? (
              <Link
                href={buildPaginationUrl(articlePage.page - 1, currentSource, currentCategory)}
                className="rounded-full border border-line px-4 py-2 hover:text-text"
              >
                Previous
              </Link>
            ) : (
              <span className="rounded-full border border-line px-4 py-2 opacity-40">Previous</span>
            )}
            {articlePage.page < articlePage.total_pages ? (
              <Link
                href={buildPaginationUrl(articlePage.page + 1, currentSource, currentCategory)}
                className="rounded-full border border-line px-4 py-2 hover:text-text"
              >
                Next
              </Link>
            ) : (
              <span className="rounded-full border border-line px-4 py-2 opacity-40">Next</span>
            )}
          </div>
        </section>
      </div>
    );
  } catch (error) {
    console.error("Failed to load articles:", error);
    return (
      <div className="mx-auto max-w-4xl px-5 py-16 md:px-8">
        <div className="rounded-[1.8rem] border border-line bg-surface px-8 py-12">
          <h1 className="text-2xl font-semibold">Unable to load articles</h1>
          <p className="mt-3 text-muted">
            Start the backend API on <code>http://localhost:8000</code> and run the ingestion pipeline first.
          </p>
        </div>
      </div>
    );
  }
}
