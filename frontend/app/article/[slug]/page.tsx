import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ArticleMeta } from "@/components/ArticleMeta";
import { FontSizeControl } from "@/components/FontSizeControl";
import { RelatedArticles } from "@/components/RelatedArticles";
import { ThemeToggle } from "@/components/ThemeToggle";
import { getArticle } from "@/lib/api";
import { sanitizeHtml } from "@/lib/sanitize";

export const dynamic = "force-dynamic";

interface ArticlePageProps {
  params: {
    slug: string;
  };
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  try {
    const article = await getArticle(params.slug);
    const bodyAlreadyHasImage = /<img[\s\S]*?>/i.test(article.content_html);
    const topImage = article.top_image ?? null;
    const showTopImage = Boolean(topImage) && !bodyAlreadyHasImage;
    const safeHtml = sanitizeHtml(article.content_html);

    return (
      <div className="mx-auto max-w-6xl px-5 py-8 md:px-8 md:py-12">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-3 rounded-full border border-line/70 bg-surface px-4 py-3 text-sm text-muted">
          <div className="flex items-center gap-3">
            <Link href="/" className="hover:text-text">
              Back to home
            </Link>
            <span className="opacity-40">/</span>
            <span>{article.metadata.source_name || article.source_id}</span>
          </div>
          <div className="flex items-center gap-2">
            <FontSizeControl />
            <ThemeToggle />
          </div>
        </div>

        <article className="mx-auto max-w-reader space-y-8">
          <header className="space-y-5">
            <ArticleMeta
              sourceId={article.source_id}
              sourceName={article.metadata.source_name}
              publishedAt={article.published_at}
              fetchedAt={article.fetched_at}
              readingTimeMinutes={article.reading_time_minutes}
              category={article.category}
            />
            <h1 className="text-4xl font-semibold tracking-tight md:text-6xl">{article.title}</h1>
            {article.authors.length ? (
              <p className="text-base text-muted">By {article.authors.join(", ")}</p>
            ) : null}
            {article.extraction_method === "feed_fallback" ? (
              <div className="rounded-[1.2rem] border border-line bg-surface px-4 py-4 text-sm leading-7 text-muted">
                This entry is using the RSS summary fallback because the full article body could not be fetched.
                {" "}
                <a
                  href={article.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-text underline underline-offset-4"
                >
                  Open the original page
                </a>
                .
              </div>
            ) : null}
          </header>

          {showTopImage && topImage ? (
            <div className="overflow-hidden rounded-[1.6rem] border border-line/70">
              <Image
                src={topImage}
                alt={article.title}
                width={1600}
                height={900}
                className="h-auto w-full object-cover"
              />
            </div>
          ) : null}

          <section
            className="reader-prose"
            dangerouslySetInnerHTML={{ __html: safeHtml }}
          />
        </article>

        <div className="mx-auto mt-16 max-w-reader">
          <RelatedArticles items={article.related_articles} />
        </div>
      </div>
    );
  } catch (error) {
    console.error("Failed to load article:", error);
    notFound();
  }
}
