import { formatDate, titleCase } from "@/lib/utils";

interface ArticleMetaProps {
  sourceId: string;
  sourceName?: string | null;
  publishedAt?: string | null;
  fetchedAt?: string | null;
  readingTimeMinutes: number;
  category?: string | null;
}

export function ArticleMeta({
  sourceId,
  sourceName,
  publishedAt,
  fetchedAt,
  readingTimeMinutes,
  category
}: ArticleMetaProps) {
  const displayDate = formatDate(publishedAt || fetchedAt);
  const displayName = sourceName || titleCase(sourceId);

  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted">
      <span>{displayName}</span>
      <span>{publishedAt ? `Published ${displayDate}` : `Fetched ${displayDate}`}</span>
      <span>{readingTimeMinutes} min read</span>
      {category ? <span>{titleCase(category)}</span> : null}
    </div>
  );
}
