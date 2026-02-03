"use client";

import { useRouter, usePathname } from "@/i18n/routing";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";

interface SortSelectorProps {
  currentSort: string;
  currentOrder: string;
}

export function SortSelector({ currentSort, currentOrder }: SortSelectorProps) {
  const t = useTranslations("composers");
  const router = useRouter();
  const pathname = usePathname();

  const sortOptions = [
    { value: "name", label: t("sortName") },
    { value: "film_count", label: t("sortFilms") },
    { value: "wins", label: t("sortAwards") },
  ];

  const handleSort = (sort: string) => {
    const newOrder = sort === currentSort && currentOrder === "asc" ? "desc" : "asc";
    router.push(`${pathname}?sort=${sort}&order=${newOrder}`);
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">{t("sortBy")}:</span>
      <div className="flex gap-1">
        {sortOptions.map((option) => (
          <Button
            key={option.value}
            variant={currentSort === option.value ? "secondary" : "ghost"}
            size="sm"
            onClick={() => handleSort(option.value)}
          >
            {option.label}
            {currentSort === option.value && (
              <span className="ml-1">{currentOrder === "asc" ? "↑" : "↓"}</span>
            )}
          </Button>
        ))}
      </div>
    </div>
  );
}
