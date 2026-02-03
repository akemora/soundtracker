import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/routing";
import { Button } from "@/components/ui/button";
import { SearchBar } from "@/components/search/SearchBar";
import { ComposerGrid } from "@/components/composers/ComposerGrid";
import { getComposers } from "@/lib/api";

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function HomePage({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);

  const t = await getTranslations("home");

  // Fetch featured composers (first 8)
  let composers: Awaited<ReturnType<typeof getComposers>>["composers"] = [];
  try {
    const data = await getComposers({ per_page: 8, sort_by: "wins", order: "desc" });
    composers = data.composers;
  } catch {
    // API might not be running in development
    console.warn("Could not fetch composers from API");
  }

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative py-20 md:py-32 bg-gradient-to-b from-muted/50 to-background">
        <div className="container flex flex-col items-center text-center gap-8">
          <h1 className="font-display text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight text-balance">
            SOUND<span className="text-accent">TRACKER</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl text-balance">
            {t("subtitle")}
          </p>

          {/* Search Bar */}
          <div className="w-full max-w-lg mt-4">
            <SearchBar placeholder={t("searchPlaceholder")} />
          </div>

          {/* CTA */}
          <div className="flex gap-4 mt-4">
            <Button asChild size="lg" className="bg-accent hover:bg-accent/90 text-accent-foreground">
              <Link href="/composers">{t("exploreAll")}</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Featured Composers */}
      {composers.length > 0 && (
        <section className="py-16 md:py-24">
          <div className="container">
            <ComposerGrid composers={composers} />
          </div>
        </section>
      )}
    </div>
  );
}
