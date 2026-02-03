/**
 * TypeScript interfaces for SOUNDTRACKER API responses.
 */

// Composer types
export interface ComposerSummary {
  id: number;
  name: string;
  slug: string;
  country: string | null;
  index_num: number | null;
  birth_year: number | null;
  death_year: number | null;
  photo_local: string | null;
}

export interface ComposerWithStats extends ComposerSummary {
  film_count: number;
  top10_count: number;
  wins: number;
  nominations: number;
  total_awards: number;
  source_count: number;
}

export interface ComposerDetail extends ComposerSummary {
  photo_url: string | null;
  biography: string | null;
  style: string | null;
  anecdotes: string | null;
}

export interface ComposerStats {
  film_count: number;
  top10_count: number;
  wins: number;
  nominations: number;
  total_awards: number;
  source_count: number;
}

// Film types
export interface FilmSummary {
  id: number;
  title: string;
  year: number | null;
  original_title: string | null;
  poster_local: string | null;
  is_top10: boolean;
  top10_rank: number | null;
}

export interface FilmDetail extends FilmSummary {
  composer_id: number;
  title_es: string | null;
  poster_url: string | null;
  tmdb_id: number | null;
  imdb_id: string | null;
  vote_average: number | null;
  vote_count: number | null;
  popularity: number | null;
  spotify_popularity: number | null;
  youtube_views: number | null;
}

// Award types
export interface AwardDetail {
  id: number;
  composer_id: number;
  award_name: string;
  category: string | null;
  year: number | null;
  film_title: string | null;
  status: "win" | "nomination";
}

export interface AwardSummary {
  total: number;
  wins: number;
  nominations: number;
}

// Search types
export interface SearchResult {
  id: number;
  name: string;
  slug: string;
  country: string | null;
  birth_year: number | null;
  death_year: number | null;
  photo_local: string | null;
  biography: string | null;
  rank: number;
}

// Pagination
export interface PaginationInfo {
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

// API Responses
export interface ComposerListResponse {
  composers: ComposerWithStats[];
  pagination: PaginationInfo;
}

export interface ComposerFilterOptions {
  countries: string[];
}

export interface ComposerResponse {
  composer: ComposerDetail;
  stats: ComposerStats | null;
  top10: FilmDetail[];
}

export interface FilmListResponse {
  composer_id: number;
  composer_name: string;
  films: FilmDetail[];
  pagination: PaginationInfo;
}

export interface AwardListResponse {
  composer_id: number;
  composer_name: string;
  awards: AwardDetail[];
  summary: AwardSummary;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  count: number;
}
