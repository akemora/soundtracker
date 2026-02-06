"use client";

import { useState } from "react";
import Image from "next/image";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { FilmDetail } from "@/lib/types";
import { getAssetUrl } from "@/lib/api";
const POSTER_BLUR_DATA_URL =
  "data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPScyJyBoZWlnaHQ9JzMnPjxkZWZzPjxsaW5lYXJHcmFkaWVudCBpZD0nZycgeDE9JzAnIHkxPScwJyB4Mj0nMCcgeTI9JzEnPjxzdG9wIG9mZnNldD0nMCUnIHN0b3AtY29sb3I9JyMyYjJiMmInLz48c3RvcCBvZmZzZXQ9JzEwMCUnIHN0b3AtY29sb3I9JyMzYTNhM2EnLz48L2xpbmVhckdyYWRpZW50PjwvZGVmcz48cmVjdCB3aWR0aD0nMicgaGVpZ2h0PSczJyBmaWxsPSd1cmwoI2cpJy8+PC9zdmc+";

interface Top10GalleryProps {
  films: FilmDetail[];
}

export function Top10Gallery({ films }: Top10GalleryProps) {
  const [selectedFilm, setSelectedFilm] = useState<FilmDetail | null>(null);

  // Sort by top10_rank
  const sortedFilms = [...films].sort((a, b) => {
    const rankA = a.top10_rank ?? 999;
    const rankB = b.top10_rank ?? 999;
    return rankA - rankB;
  });

  return (
    <>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
        {sortedFilms.map((film) => (
          <FilmCard
            key={film.id}
            film={film}
            onClick={() => setSelectedFilm(film)}
          />
        ))}
      </div>

      {/* Film Detail Modal */}
      <Dialog open={!!selectedFilm} onOpenChange={() => setSelectedFilm(null)}>
        <DialogContent className="max-w-lg">
          {selectedFilm && (
            <>
              <DialogHeader>
                <DialogTitle className="font-display text-xl">
                  {selectedFilm.title}
                </DialogTitle>
                <DialogDescription className="sr-only">
                  Detalles de la banda sonora seleccionada.
                </DialogDescription>
              </DialogHeader>
              <FilmDetailModal film={selectedFilm} />
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

function FilmCard({
  film,
  onClick,
}: {
  film: FilmDetail;
  onClick: () => void;
}) {
  const hasPoster = film.poster_local != null;
  const posterUrl = hasPoster
    ? getAssetUrl("posters", film.poster_local!)
    : null;

  return (
    <Card
      className="group relative overflow-hidden cursor-pointer transition-all hover:scale-105 hover:shadow-xl"
      onClick={onClick}
    >
      {/* Poster */}
      <div className="relative aspect-[2/3] bg-muted">
        {posterUrl ? (
          <Image
            src={posterUrl}
            alt={film.title}
            fill
            className="object-cover"
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 25vw, 20vw"
            placeholder="blur"
            blurDataURL={POSTER_BLUR_DATA_URL}
            unoptimized
          />
        ) : (
          <div className="absolute inset-0 flex items-end justify-center p-2 pb-4">
            <span className="text-xs text-center text-muted-foreground line-clamp-2">
              {film.title}
            </span>
          </div>
        )}

        {/* Rank Badge - positioned outside poster area to avoid overlap */}
        {film.top10_rank && (
          <Badge className="absolute top-2 left-2 bg-primary text-primary-foreground font-bold text-sm shadow-lg z-10">
            #{film.top10_rank}
          </Badge>
        )}

        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-3">
          <p className="text-white text-sm font-medium line-clamp-2">
            {film.title}
          </p>
          {film.year && (
            <p className="text-white/70 text-xs mt-1">{film.year}</p>
          )}
        </div>
      </div>
    </Card>
  );
}

function FilmDetailModal({ film }: { film: FilmDetail }) {
  const hasPoster = film.poster_local != null;
  const posterUrl = hasPoster
    ? getAssetUrl("posters", film.poster_local!)
    : null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {/* Poster */}
      {posterUrl && (
        <div className="relative aspect-[2/3] bg-muted rounded-lg overflow-hidden">
          <Image
            src={posterUrl}
            alt={film.title}
            fill
            className="object-cover"
            sizes="(max-width: 640px) 100vw, 200px"
            priority
            placeholder="blur"
            blurDataURL={POSTER_BLUR_DATA_URL}
            unoptimized
          />
        </div>
      )}

      {/* Details */}
      <div className="space-y-3">
        {film.original_title && film.original_title !== film.title && (
          <div>
            <p className="text-xs text-muted-foreground">Título original</p>
            <p className="font-medium">{film.original_title}</p>
          </div>
        )}

        {film.year && (
          <div>
            <p className="text-xs text-muted-foreground">Año</p>
            <p className="font-medium">{film.year}</p>
          </div>
        )}

        {film.vote_average && (
          <div>
            <p className="text-xs text-muted-foreground">Puntuación TMDB</p>
            <p className="font-medium">
              ⭐ {film.vote_average.toFixed(1)} / 10
              {film.vote_count && (
                <span className="text-muted-foreground text-sm ml-1">
                  ({film.vote_count.toLocaleString()} votos)
                </span>
              )}
            </p>
          </div>
        )}

        {film.top10_rank && (
          <Badge className="bg-primary text-primary-foreground font-bold">
            ★ Top #{film.top10_rank}
          </Badge>
        )}

        {film.imdb_id && (
          <a
            href={`https://www.imdb.com/title/${film.imdb_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block text-sm text-accent hover:underline"
          >
            Ver en IMDb →
          </a>
        )}
      </div>
    </div>
  );
}
