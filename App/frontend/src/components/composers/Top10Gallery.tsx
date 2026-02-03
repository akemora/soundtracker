"use client";

import { useState } from "react";
import Image from "next/image";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { FilmDetail } from "@/lib/types";
import { getAssetUrl } from "@/lib/api";

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
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center p-2">
            <span className="text-xs text-center text-muted-foreground">
              {film.title}
            </span>
          </div>
        )}

        {/* Rank Badge */}
        {film.top10_rank && (
          <Badge className="absolute top-2 left-2 bg-gold text-gold-foreground font-bold">
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
          <Badge className="bg-gold text-gold-foreground">
            Top #{film.top10_rank}
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
