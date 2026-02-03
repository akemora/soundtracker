import { getTranslations, setRequestLocale } from "next-intl/server";
import { SearchBar } from "@/components/search/SearchBar";
import { SearchResults } from "@/components/search/SearchResults";
import { search } from "@/lib/api";

type Props = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ q?: string }>;
};

export default async function SearchPage({ params, searchParams }: Props) {
  const { locale } = await params;
  const { q } = await searchParams;
  setRequestLocale(locale);

  const t = await getTranslations("search");

  let results = null;
  if (q && q.length >= 2) {
    try {
      results = await search(q, 50);
    } catch {
      results = null;
    }
  }

  return (
    <div className="container py-8 md:py-12">
      {/* Search Header */}
      <div className="max-w-2xl mx-auto mb-8">
        <h1 className="font-display text-3xl font-bold text-center mb-6">
          Buscar Compositores
        </h1>
        <SearchBar defaultValue={q || ""} placeholder="Buscar por nombre..." />
      </div>

      {/* Results */}
      {q ? (
        results ? (
          <div className="mt-8">
            <p className="text-muted-foreground mb-4">
              {results.count} {t("results")} para &quot;{q}&quot;
            </p>
            {results.count > 0 ? (
              <SearchResults results={results.results} />
            ) : (
              <p className="text-center py-12 text-muted-foreground">
                {t("noResults")} &quot;{q}&quot;
              </p>
            )}
          </div>
        ) : (
          <p className="text-center py-12 text-muted-foreground">
            Error al buscar. Intenta de nuevo.
          </p>
        )
      ) : (
        <p className="text-center py-12 text-muted-foreground">
          Escribe al menos 2 caracteres para buscar
        </p>
      )}
    </div>
  );
}
