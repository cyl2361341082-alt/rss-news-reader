export interface Source {
  id: string;
  name: string;
  category: string;
  rss_url: string;
  enabled: boolean;
  site_url: string;
  language: string;
  extraction_strategy: string;
  article_count: number;
}

export interface ArticleSummary {
  id: number;
  source_id: string;
  url: string;
  canonical_url?: string | null;
  title: string;
  slug: string;
  published_at?: string | null;
  fetched_at: string;
  language?: string | null;
  category?: string | null;
  summary: string;
  reading_time_minutes: number;
  top_image?: string | null;
  extraction_method: string;
}

export interface ArticleDetail extends ArticleSummary {
  authors: string[];
  content_text: string;
  content_html: string;
  metadata: {
    html_excerpt?: string;
    tags?: string[];
    source_name?: string;
  };
  related_articles: ArticleSummary[];
}

export interface PaginatedArticles {
  items: ArticleSummary[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface SearchResponse {
  query: string;
  results: ArticleSummary[];
}
