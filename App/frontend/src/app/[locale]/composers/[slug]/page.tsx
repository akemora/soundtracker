import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { getComposer } from "@/lib/api";
import { ComposerDetail } from "@/components/composers/ComposerDetail";
import { Top10Gallery } from "@/components/composers/Top10Gallery";
import { AwardsList } from "@/components/composers/AwardsList";

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
