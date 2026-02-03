/**
 * SOUNDTRACKER API client for frontend.
 */

import type {
  ComposerListResponse,
  ComposerFilterOptions,
  ComposerResponse,
  FilmListResponse,
  AwardListResponse,
  SearchResponse,
} from "./types";

// Server-side uses Docker network name, client-side uses localhost
const isServer = typeof window === "undefined";
const API_URL = isServer
  ? (process.env.API_URL || "http://localhost:8000")
  : "http://localhost:8000";

/**
 * Base fetcher with error handling.
 */
async function fetcher<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API Error: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

/**
 * Get paginated list of composers with optional filters.
 */
export async function getComposers(params?: {
  page?: number;
  per_page?: number;
  sort_by?: string;
  order?: "asc" | "desc";
  decade?: number;
  has_awards?: boolean;
  country?: string;
}): Promise<ComposerListResponse> {
  const searchParams = new URLSearchParams();

  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.per_page) searchParams.set("per_page", String(params.per_page));
  if (params?.sort_by) searchParams.set("sort_by", params.sort_by);
  if (params?.order) searchParams.set("order", params.order);
  if (params?.decade) searchParams.set("decade", String(params.decade));
  if (params?.has_awards !== undefined) searchParams.set("has_awards", String(params.has_awards));
  if (params?.country) searchParams.set("country", params.country);

  const query = searchParams.toString();
  const endpoint = `/api/composers${query ? `?${query}` : ""}`;

  return fetcher<ComposerListResponse>(endpoint);
}

/**
 * Get available filter options for composers.
 */
export async function getComposerFilters(): Promise<ComposerFilterOptions> {
  return fetcher<ComposerFilterOptions>("/api/composers/filters");
}

/**
 * Get composer detail by slug.
 */
export async function getComposer(slug: string): Promise<ComposerResponse> {
  return fetcher<ComposerResponse>(`/api/composers/${slug}`);
}

/**
 * Get composer filmography.
 */
export async function getFilmography(
  slug: string,
  params?: { page?: number; per_page?: number }
): Promise<FilmListResponse> {
  const searchParams = new URLSearchParams();

  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.per_page) searchParams.set("per_page", String(params.per_page));

  const query = searchParams.toString();
  const endpoint = `/api/composers/${slug}/filmography${query ? `?${query}` : ""}`;

  return fetcher<FilmListResponse>(endpoint);
}

/**
 * Get composer awards.
 */
export async function getAwards(slug: string): Promise<AwardListResponse> {
  return fetcher<AwardListResponse>(`/api/composers/${slug}/awards`);
}

/**
 * Search composers using FTS5.
 */
export async function search(
  query: string,
  limit?: number
): Promise<SearchResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set("q", query);
  if (limit) searchParams.set("limit", String(limit));

  return fetcher<SearchResponse>(`/api/search?${searchParams.toString()}`);
}

/**
 * Get search suggestions for autocomplete.
 */
export async function getSuggestions(
  prefix: string,
  limit?: number
): Promise<string[]> {
  const searchParams = new URLSearchParams();
  searchParams.set("q", prefix);
  if (limit) searchParams.set("limit", String(limit));

  return fetcher<string[]>(`/api/search/suggestions?${searchParams.toString()}`);
}

/**
 * Get asset URL for posters and photos.
 * Handles both relative filenames and absolute paths from database.
 * Always returns browser-accessible URL (localhost), not Docker internal URL.
 */
export function getAssetUrl(type: "posters" | "photos", pathOrFilename: string): string {
  // If it's an absolute path, extract the relative part after 'outputs/'
  let relativePath = pathOrFilename;

  if (pathOrFilename.includes("/outputs/")) {
    const parts = pathOrFilename.split("/outputs/");
    const lastPart = parts[parts.length - 1];
    if (lastPart) {
      relativePath = lastPart;
    }
  }

  // For photos, the path is like: 053_john_williams/photo_john_williams.jpg
  // For posters, the path is like: 053_john_williams/posters/poster_name.jpg
  // Always use localhost URL since images are loaded by the browser, not the server
  const BROWSER_API_URL = "http://localhost:8000";

  return `${BROWSER_API_URL}/api/assets/${type}/${relativePath}`;
}
