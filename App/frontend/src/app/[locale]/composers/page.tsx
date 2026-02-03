import { getTranslations, setRequestLocale } from "next-intl/server";
import { ComposerGrid } from "@/components/composers/ComposerGrid";
import { Pagination } from "@/components/ui/Pagination";
import { SortSelector } from "@/components/composers/SortSelector";
import { FilterPanel } from "@/components/search/FilterPanel";
import { getComposers } from "@/lib/api";

type Props = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{
    page?: string;
    sort?: string;
    order?: string;
    decade?: string;
    has_awards?: string;
  }>;
};

export default async function ComposersPage({ params, searchParams }: Props) {
  const { locale } = await params;
  const search = await searchParams;
  setRequestLocale(locale);

  const t = await getTranslations("composers");

  const page = Number(search.page) || 1;
  const sort_by = search.sort || "name";
  const order = (search.order as "asc" | "desc") || "asc";
  const decade = search.decade ? Number(search.decade) : undefined;
  const has_awards = search.has_awards !== undefined ? search.has_awards === "true" : undefined;

  let data;
  try {
    data = await getComposers({
      page,
      per_page: 20,
      sort_by,
      order,
      decade,
      has_awards,
    });
  } catch {
    data = null;
  }

  // Build base URL for pagination that preserves filters
  const buildPaginationUrl = () => {
    const params = new URLSearchParams();
    params.set("sort", sort_by);
    params.set("order", order);
    if (decade) params.set("decade", String(decade));
    if (has_awards !== undefined) params.set("has_awards", String(has_awards));
    return `/composers?${params.toString()}`;
  };

  return (
    <div className="container py-8 md:py-12">
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-display text-3xl md:text-4xl font-bold mb-2">
          {t("title")}
        </h1>
        <p className="text-muted-foreground">{t("subtitle")}</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Sidebar with filters */}
        <aside className="lg:w-64 flex-shrink-0">
          <FilterPanel currentDecade={decade} hasAwards={has_awards} />
        </aside>

        {/* Main content */}
        <div className="flex-1">
          {/* Controls */}
          <div className="flex justify-between items-center mb-6">
            <p className="text-sm text-muted-foreground">
              {data
                ? `${data.pagination.total} compositores`
                : "Cargando..."}
            </p>
            <SortSelector currentSort={sort_by} currentOrder={order} />
          </div>

          {/* Grid */}
          {data ? (
            <>
              <ComposerGrid composers={data.composers} />

              {/* Pagination */}
              {data.pagination.pages > 1 && (
                <div className="mt-8 flex justify-center">
                  <Pagination
                    currentPage={data.pagination.page}
                    totalPages={data.pagination.pages}
                    baseUrl={buildPaginationUrl()}
                  />
                </div>
              )}
            </>
          ) : (
            <p className="text-muted-foreground text-center py-12">
              {t("noResults")}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
