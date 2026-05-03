import { ArticleDetail, PaginatedArticles, SearchResponse, Source } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";
const FETCH_TIMEOUT_MS = 15_000;

async function apiFetch<T>(path: string): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE}${path}`, {
      cache: "no-store",
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }

    return (await response.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export async function getSources(): Promise<Source[]> {
  return apiFetch<Source[]>("/sources");
}

export async function getArticles(params: {
  page?: number;
  pageSize?: number;
  source?: string;
  category?: string;
  q?: string;
}): Promise<PaginatedArticles> {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.pageSize) search.set("page_size", String(params.pageSize));
  if (params.source) search.set("source", params.source);
  if (params.category) search.set("category", params.category);
  if (params.q) search.set("q", params.q);
  return apiFetch<PaginatedArticles>(`/articles?${search.toString()}`);
}

export async function getArticle(slug: string): Promise<ArticleDetail> {
  return apiFetch<ArticleDetail>(`/articles/${encodeURIComponent(slug)}`);
}

export async function searchArticles(query: string): Promise<SearchResponse> {
  return apiFetch<SearchResponse>(`/search?q=${encodeURIComponent(query)}`);
}
