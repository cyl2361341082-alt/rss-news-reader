import { ArticleCard } from "@/components/ArticleCard";
import { SearchBar } from "@/components/SearchBar";
import { searchArticles } from "@/lib/api";

export const dynamic = "force-dynamic";

interface SearchPageProps {
  searchParams?: {
    q?: string;
  };
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const query = (searchParams?.q || "").trim();

  try {
    const response = query ? await searchArticles(query) : null;

    return (
      <div className="mx-auto flex max-w-5xl flex-col gap-8 px-5 py-10 md:px-8 md:py-14">
        <section className="space-y-4">
          <p className="text-sm uppercase tracking-[0.28em] text-muted">Search</p>
          <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">Search across collected articles</h1>
          <SearchBar defaultValue={query} />
        </section>

        {!query ? (
          <div className="rounded-[1.8rem] border border-dashed border-line bg-surface px-8 py-12 text-center text-muted">
            Enter a keyword to search titles and extracted article text.
          </div>
        ) : response && response.results.length ? (
          <section className="space-y-4">
            <p className="text-sm text-muted">
              Found {response.results.length} result{response.results.length === 1 ? "" : "s"} for “{query}”.
            </p>
            {response.results.map((article) => (
              <ArticleCard key={article.slug} article={article} />
            ))}
          </section>
        ) : (
          <div className="rounded-[1.8rem] border border-dashed border-line bg-surface px-8 py-12 text-center text-muted">
            No results for “{query}”.
          </div>
        )}
      </div>
    );
  } catch (error) {
    console.error("Search failed:", error);
    return (
      <div className="mx-auto max-w-4xl px-5 py-16 md:px-8">
        <div className="rounded-[1.8rem] border border-line bg-surface px-8 py-12 text-muted">
          Search is unavailable because the backend API could not be reached.
        </div>
      </div>
    );
  }
}
