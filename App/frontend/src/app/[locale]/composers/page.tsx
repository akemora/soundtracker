import { getTranslations, setRequestLocale } from "next-intl/server";
import { ComposerGrid } from "@/components/composers/ComposerGrid";
import { Pagination } from "@/components/ui/Pagination";
import { SortSelector } from "@/components/composers/SortSelector";
import { getComposers } from "@/lib/api";

type Props = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{
    page?: string;
    sort?: string;
    order?: string;
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

  let data;
  try {
    data = await getComposers({
      page,
      per_page: 20,
      sort_by,
      order,
    });
  } catch {
    data = null;
  }

  return (
    <div className="container py-8 md:py-12">
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-display text-3xl md:text-4xl font-bold mb-2">
          {t("title")}
        </h1>
        <p className="text-muted-foreground">{t("subtitle")}</p>
      </div>

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
                baseUrl={`/composers?sort=${sort_by}&order=${order}`}
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
  );
}
