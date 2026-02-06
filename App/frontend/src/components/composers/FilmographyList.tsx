"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getFilmography } from "@/lib/api";
import type { FilmDetail, FilmListResponse } from "@/lib/types";
import { getAssetUrl } from "@/lib/api";

const POSTER_BLUR_DATA_URL =
  "data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPScyJyBoZWlnaHQ9JzMnPjxkZWZzPjxsaW5lYXJHcmFkaWVudCBpZD0nZycgeDE9JzAnIHkxPScwJyB4Mj0nMCcgeTI9JzEnPjxzdG9wIG9mZnNldD0nMCUnIHN0b3AtY29sb3I9JyMyYjJiMmInLz48c3RvcCBvZmZzZXQ9JzEwMCUnIHN0b3AtY29sb3I9JyMzYTNhM2EnLz48L2xpbmVhckdyYWRpZW50PjwvZGVmcz48cmVjdCB3aWR0aD0nMicgaGVpZ2h0PSczJyBmaWxsPSd1cmwoI2cpJy8+PC9zdmc+";

interface FilmographyListProps {
  slug: string;
}

export function FilmographyList({ slug }: FilmographyListProps) {
  const [data, setData] = useState<FilmListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [allFilms, setAllFilms] = useState<FilmDetail[]>([]);
  const [decadeFilter, setDecadeFilter] = useState<string | null>(null);

  useEffect(() => {
    async function fetchFilms() {
      try {
        const result = await getFilmography(slug, { page: 1, per_page: 20 });
        setData(result);
        setAllFilms(result.films);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchFilms();
  }, [slug]);

  const loadMore = async () => {
    setLoadingMore(true);
    try {
      const nextPage = page + 1;
      const result = await getFilmography(slug, { page: nextPage, per_page: 20 });
      setAllFilms((prev) => [...prev, ...result.films]);
      setPage(nextPage);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingMore(false);
    }
  };

  if (loading) {
    return <FilmographySkeleton />;
  }

  if (!data) {
    return <p className="text-muted-foreground">Error loading filmography</p>;
  }

  // Get unique decades
  const decades = [
    ...new Set(
      allFilms
        .map((film) => (film.year ? Math.floor(film.year / 10) * 10 : null))
        .filter((value): value is number => value !== null)
    ),
  ].sort((a, b) => b - a);

  // Filter films by decade
  const filteredFilms = decadeFilter
    ? allFilms.filter((f) => f.year && Math.floor(f.year / 10) * 10 === parseInt(decadeFilter))
    : allFilms;

  const hasMore = data.pagination.pages > page;

  return (
    <div className="space-y-6">
      {/* Decade Filter */}
      {decades.length > 1 && (
        <div className="flex flex-wrap gap-2">
          <Button
            variant={decadeFilter === null ? "default" : "outline"}
            size="sm"
            onClick={() => setDecadeFilter(null)}
          >
            Todas
          </Button>
          {decades.map((decade) => (
            <Button
              key={decade}
              variant={decadeFilter === String(decade) ? "default" : "outline"}
              size="sm"
              onClick={() => setDecadeFilter(String(decade))}
            >
              {decade}s
            </Button>
          ))}
        </div>
      )}

      {/* Films list */}
      <div className="grid gap-3">
        {filteredFilms.map((film) => (
          <FilmRow key={film.id} film={film} />
        ))}
      </div>

      {/* Load more button */}
      {hasMore && !decadeFilter && (
        <div className="flex justify-center">
          <Button onClick={loadMore} disabled={loadingMore} variant="outline">
            {loadingMore ? "Cargando..." : `Cargar más (${data.pagination.total - allFilms.length} restantes)`}
          </Button>
        </div>
      )}

      {/* Summary */}
      <p className="text-sm text-muted-foreground text-center">
        Mostrando {filteredFilms.length} de {data.pagination.total} películas
      </p>
    </div>
  );
}

function FilmRow({ film }: { film: FilmDetail }) {
  const hasPoster = film.poster_local != null;
  const posterUrl = hasPoster ? getAssetUrl("posters", film.poster_local!) : null;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-3">
        <div className="flex gap-3">
          {/* Poster */}
          <div className="relative w-12 h-16 rounded overflow-hidden bg-muted flex-shrink-0">
            {posterUrl ? (
              <Image
                src={posterUrl}
                alt={film.title}
                fill
                className="object-cover"
                sizes="48px"
                loading="lazy"
                placeholder="blur"
                blurDataURL={POSTER_BLUR_DATA_URL}
                unoptimized
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center text-xs text-muted-foreground">
                🎬
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="font-medium truncate">{film.title}</h4>
            </div>
            <div className="flex items-center gap-3 text-sm text-muted-foreground mt-1">
              {film.year && <span>{film.year}</span>}
              {film.vote_average && (
                <span>⭐ {film.vote_average.toFixed(1)}</span>
              )}
              {film.original_title && film.original_title !== film.title && (
                <span className="truncate hidden sm:block">({film.original_title})</span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function FilmographySkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-3">
            <div className="flex gap-3">
              <Skeleton className="w-12 h-16" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
