"use client";

import { Link } from "@/i18n/routing";
import { Button } from "@/components/ui/button";

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  baseUrl: string;
}

export function Pagination({ currentPage, totalPages, baseUrl }: PaginationProps) {
  // Generate page numbers to show
  const getPageNumbers = () => {
    const pages: (number | "...")[] = [];
    const showPages = 5;
    const half = Math.floor(showPages / 2);

    let start = Math.max(1, currentPage - half);
    const end = Math.min(totalPages, start + showPages - 1);

    if (end - start + 1 < showPages) {
      start = Math.max(1, end - showPages + 1);
    }

    if (start > 1) {
      pages.push(1);
      if (start > 2) pages.push("...");
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    if (end < totalPages) {
      if (end < totalPages - 1) pages.push("...");
      pages.push(totalPages);
    }

    return pages;
  };

  const pageNumbers = getPageNumbers();
  const separator = baseUrl.includes("?") ? "&" : "?";

  return (
    <nav className="flex items-center gap-1" aria-label="Pagination">
      {/* Previous */}
      <Button
        variant="outline"
        size="sm"
        disabled={currentPage <= 1}
        asChild={currentPage > 1}
      >
        {currentPage > 1 ? (
          <Link href={`${baseUrl}${separator}page=${currentPage - 1}`}>
            ← Anterior
          </Link>
        ) : (
          <span>← Anterior</span>
        )}
      </Button>

      {/* Page numbers */}
      <div className="hidden sm:flex items-center gap-1">
        {pageNumbers.map((page, index) =>
          page === "..." ? (
            <span key={`ellipsis-${index}`} className="px-2 text-muted-foreground">
              ...
            </span>
          ) : (
            <Button
              key={page}
              variant={page === currentPage ? "default" : "outline"}
              size="sm"
              asChild={page !== currentPage}
            >
              {page !== currentPage ? (
                <Link href={`${baseUrl}${separator}page=${page}`}>{page}</Link>
              ) : (
                <span>{page}</span>
              )}
            </Button>
          )
        )}
      </div>

      {/* Mobile current page indicator */}
      <span className="sm:hidden px-3 text-sm text-muted-foreground">
        {currentPage} / {totalPages}
      </span>

      {/* Next */}
      <Button
        variant="outline"
        size="sm"
        disabled={currentPage >= totalPages}
        asChild={currentPage < totalPages}
      >
        {currentPage < totalPages ? (
          <Link href={`${baseUrl}${separator}page=${currentPage + 1}`}>
            Siguiente →
          </Link>
        ) : (
          <span>Siguiente →</span>
        )}
      </Button>
    </nav>
  );
}
