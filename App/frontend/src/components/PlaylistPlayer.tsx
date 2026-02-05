"use client";

import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { PlaylistTrack } from "@/lib/types";

interface PlaylistPlayerProps {
  composerSlug: string;
  composerName: string;
  tracks: PlaylistTrack[];
}

export function PlaylistPlayer({ composerSlug, composerName, tracks }: PlaylistPlayerProps) {
  const [currentTrack, setCurrentTrack] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const safeTracks = useMemo(() => tracks || [], [tracks]);
  const activeTrack = safeTracks[currentTrack];

  if (!safeTracks.length) {
    return (
      <Card className="p-6">
        <p className="text-muted-foreground">No hay playlist disponible todavía.</p>
      </Card>
    );
  }

  const handleSelect = (index: number) => {
    setCurrentTrack(index);
    setIsPlaying(false);
  };

  return (
    <Card className="overflow-hidden border-muted/60">
      <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr]">
        <div className="p-6 space-y-5">
          <header>
            <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">
              Playlist destacada
            </p>
            <h2 className="font-display text-2xl md:text-3xl font-semibold">
              {composerName}
            </h2>
            <p className="text-muted-foreground">Top 10 reproducible</p>
          </header>

          <div className="rounded-2xl border border-muted/60 bg-muted/30 p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Ahora suena</p>
                <h3 className="font-semibold text-lg">{activeTrack.track_title}</h3>
                <p className="text-sm text-muted-foreground">{activeTrack.film}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={activeTrack.is_free ? "default" : "secondary"}>
                  {activeTrack.is_free ? "Gratis" : "De pago"}
                </Badge>
                <Badge variant="outline" className="uppercase text-xs">
                  {activeTrack.source}
                </Badge>
              </div>
            </div>

            <div className="mt-4 aspect-video w-full overflow-hidden rounded-lg bg-black">
              {activeTrack.embed_url && activeTrack.is_free ? (
                <iframe
                  key={activeTrack.embed_url}
                  src={activeTrack.embed_url}
                  title={`${composerSlug}-${activeTrack.position}`}
                  allow="autoplay; encrypted-media"
                  allowFullScreen
                  className="h-full w-full"
                />
              ) : (
                <div className="h-full w-full flex flex-col items-center justify-center gap-3 text-center p-6">
                  <p className="text-sm text-muted-foreground">
                    Este track no está disponible gratuitamente.
                  </p>
                  {activeTrack.purchase_links && activeTrack.purchase_links.length > 0 && (
                    <div className="flex flex-wrap items-center justify-center gap-3">
                      {activeTrack.purchase_links.map((link) => (
                        <a
                          key={link.source}
                          href={link.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sm text-accent hover:underline"
                        >
                          Comprar en {link.source}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Button
                type="button"
                variant={isPlaying ? "secondary" : "default"}
                onClick={() => setIsPlaying((value) => !value)}
              >
                {isPlaying ? "Pausar" : "Reproducir"}
              </Button>
              {activeTrack.duration && (
                <span className="text-xs text-muted-foreground">
                  Duración {activeTrack.duration}
                </span>
              )}
              {activeTrack.fallback_reason && (
                <span className="text-xs text-muted-foreground">
                  {activeTrack.fallback_reason}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="border-t lg:border-t-0 lg:border-l border-muted/40">
          <div className="p-4 text-sm text-muted-foreground">Lista de tracks</div>
          <ul className="max-h-[520px] overflow-y-auto">
            {safeTracks.map((track, index) => (
              <li
                key={`${track.source}-${track.position}-${track.track_title}`}
                className={`flex items-center gap-3 px-4 py-3 cursor-pointer transition-colors ${
                  index === currentTrack
                    ? "bg-accent/10"
                    : "hover:bg-muted/40"
                }`}
                onClick={() => handleSelect(index)}
                role="button"
                tabIndex={0}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    handleSelect(index);
                  }
                }}
              >
                <div className="h-12 w-12 rounded-md bg-muted flex items-center justify-center overflow-hidden">
                  {track.thumbnail ? (
                    <img
                      src={track.thumbnail}
                      alt=""
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <span className="text-xs text-muted-foreground">#{track.position}</span>
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm">{track.track_title}</span>
                    {!track.is_free && (
                      <Badge variant="secondary" className="text-xs">
                        $
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{track.film}</p>
                </div>
                <span className="text-xs uppercase text-muted-foreground">
                  {track.source}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </Card>
  );
}
