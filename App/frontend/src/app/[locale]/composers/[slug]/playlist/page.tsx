import type { Metadata } from "next";
import { setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/routing";

import { getPlaylist } from "@/lib/api";
import { PlaylistPlayer } from "@/components/PlaylistPlayer";


type Props = {
  params: Promise<{ locale: string; slug: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;

  try {
    const playlist = await getPlaylist(slug);
    return {
      title: `Playlist de ${playlist.composer_name} - SOUNDTRACKER`,
      description: `Escucha los temas esenciales de ${playlist.composer_name}.`,
    };
  } catch {
    return {
      title: "Playlist - SOUNDTRACKER",
    };
  }
}

export default async function PlaylistPage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);

  let playlist;
  try {
    playlist = await getPlaylist(slug);
  } catch {
    playlist = null;
  }

  if (!playlist) {
    return (
      <div className="container py-12">
        <p className="text-muted-foreground">No hay playlist disponible.</p>
      </div>
    );
  }

  return (
    <div className="container py-8 md:py-12 space-y-8">
      <div className="flex flex-col gap-2">
        <Link href={`/composers/${slug}`} className="text-sm text-muted-foreground hover:text-accent">
          ← Volver al compositor
        </Link>
        <h1 className="font-display text-3xl md:text-4xl font-bold">
          Playlist de {playlist.composer_name}
        </h1>
        <p className="text-muted-foreground">
          {playlist.free_count} tracks gratuitos · {playlist.paid_count} de pago
        </p>
      </div>

      <PlaylistPlayer
        composerSlug={playlist.composer_slug}
        composerName={playlist.composer_name}
        tracks={playlist.tracks}
      />
    </div>
  );
}
