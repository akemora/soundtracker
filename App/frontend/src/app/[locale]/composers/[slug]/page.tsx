import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/routing";

import { getComposer, getPlaylist } from "@/lib/api";
import { ComposerDetail } from "@/components/composers/ComposerDetail";
import { Top10Gallery } from "@/components/composers/Top10Gallery";
import { FilmographyList } from "@/components/composers/FilmographyList";
import { AwardsList } from "@/components/composers/AwardsList";
import { PlaylistPlayer } from "@/components/PlaylistPlayer";

type Props = {
  params: Promise<{ locale: string; slug: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;

  try {
    const data = await getComposer(slug);
    const composer = data.composer;

    return {
      title: `${composer.name} - SOUNDTRACKER`,
      description: composer.biography?.slice(0, 160) || `Film composer ${composer.name}`,
      openGraph: {
        title: composer.name,
        description: composer.biography?.slice(0, 160) || `Discover ${composer.name}'s filmography`,
        type: "profile",
      },
    };
  } catch {
    return {
      title: "Composer - SOUNDTRACKER",
    };
  }
}

export default async function ComposerPage({ params }: Props) {
  const { locale, slug } = await params;
  setRequestLocale(locale);

  const t = await getTranslations("composer");

  let data;
  try {
    data = await getComposer(slug);
  } catch {
    notFound();
  }

  let playlist = null;
  try {
    playlist = await getPlaylist(slug);
  } catch {
    playlist = null;
  }

  const { composer, stats, top10 } = data;

  return (
    <div className="container py-8 md:py-12">
      {/* Composer Detail Section */}
      <ComposerDetail composer={composer} stats={stats} />

      {/* Top 10 Films */}
      {top10.length > 0 && (
        <section className="mt-12">
          <h2 className="font-display text-2xl font-bold mb-6">{t("top10")}</h2>
          <Top10Gallery films={top10} />
        </section>
      )}

      {/* Playlist Section */}
      {playlist && playlist.tracks.length > 0 && (
        <section className="mt-12">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-3">
            <h2 className="font-display text-2xl font-bold">
              🎵 Escucha sus mejores temas
            </h2>
            <Link
              href={`/composers/${slug}/playlist`}
              className="text-sm text-accent hover:underline"
            >
              Ver playlist completa →
            </Link>
          </div>
          <p className="text-sm text-muted-foreground mb-4">
            {playlist.free_count} tracks gratuitos, {playlist.paid_count} de pago
          </p>
          <PlaylistPlayer
            composerSlug={playlist.composer_slug}
            composerName={playlist.composer_name}
            tracks={playlist.tracks}
          />
        </section>
      )}

      {/* Full Filmography - loaded client-side */}
      {stats && stats.film_count > 0 && (
        <section className="mt-12">
          <h2 className="font-display text-2xl font-bold mb-6">
            {t("filmography")} ({stats.film_count})
          </h2>
          <FilmographyList slug={slug} />
        </section>
      )}

      {/* Awards Section - loaded client-side */}
      {stats && stats.total_awards > 0 && (
        <section className="mt-12">
          <h2 className="font-display text-2xl font-bold mb-6">
            {t("awards")} ({stats.total_awards})
          </h2>
          <AwardsList slug={slug} />
        </section>
      )}
    </div>
  );
}
