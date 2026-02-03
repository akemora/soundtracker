"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, usePathname } from "@/i18n/routing";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getComposerFilters } from "@/lib/api";

interface FilterPanelProps {
  currentDecade?: number;
  hasAwards?: boolean;
  currentCountry?: string;
  awardType?: string;
}

// Decades available for film composers
const DECADES = [1880, 1890, 1900, 1910, 1920, 1930, 1940, 1950, 1960, 1970, 1980, 1990];

export function FilterPanel({ currentDecade, hasAwards, currentCountry, awardType }: FilterPanelProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [countries, setCountries] = useState<string[]>([]);
  const [awardTypes, setAwardTypes] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    getComposerFilters()
      .then((data) => {
        if (!active) return;
        setCountries(data.countries || []);
        setAwardTypes(data.award_types || []);
      })
      .catch(() => {
        if (!active) return;
        setCountries([]);
        setAwardTypes([]);
      });

    return () => {
      active = false;
    };
  }, []);

  const createQueryString = useCallback(
    (updates: Record<string, string | null>) => {
      const params = new URLSearchParams(searchParams.toString());

      // Reset to page 1 when changing filters
      params.set("page", "1");

      for (const [name, value] of Object.entries(updates)) {
        if (value === null) {
          params.delete(name);
        } else {
          params.set(name, value);
        }
      }

      return params.toString();
    },
    [searchParams]
  );

  const handleDecadeChange = useCallback(
    (decade: number | null) => {
      const query = createQueryString({ decade: decade ? String(decade) : null });
      router.push(`${pathname}?${query}`);
    },
    [createQueryString, pathname, router]
  );

  const handleAwardsChange = useCallback(
    (value: boolean | null) => {
      const query = createQueryString({ has_awards: value !== null ? String(value) : null });
      router.push(`${pathname}?${query}`);
    },
    [createQueryString, pathname, router]
  );

  const handleCountryChange = useCallback(
    (value: string | null) => {
      const query = createQueryString({ country: value || null });
      router.push(`${pathname}?${query}`);
    },
    [createQueryString, pathname, router]
  );

  const handleAwardTypeChange = useCallback(
    (value: string | null) => {
      const query = createQueryString({ award_type: value || null });
      router.push(`${pathname}?${query}`);
    },
    [createQueryString, pathname, router]
  );

  const clearAllFilters = useCallback(() => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("decade");
    params.delete("has_awards");
    params.delete("country");
    params.delete("award_type");
    params.set("page", "1");
    router.push(`${pathname}?${params.toString()}`);
  }, [pathname, router, searchParams]);

  const hasActiveFilters =
    currentDecade !== undefined || hasAwards !== undefined || !!currentCountry || !!awardType;

  return (
    <div className="space-y-4 p-4 border border-border rounded-lg bg-card">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">Filtros</h3>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearAllFilters} className="text-xs">
            Limpiar filtros
          </Button>
        )}
      </div>

      {/* Decade filter */}
      <div className="space-y-2">
        <label className="text-sm text-muted-foreground">Nacido en:</label>
        <div className="flex flex-wrap gap-1">
          <Button
            variant={currentDecade === undefined ? "default" : "outline"}
            size="sm"
            className={`text-xs ${currentDecade === undefined ? "bg-accent hover:bg-accent/90 text-accent-foreground" : ""}`}
            onClick={() => handleDecadeChange(null)}
          >
            Todas
          </Button>
          {DECADES.map((decade) => (
            <Button
              key={decade}
              variant={currentDecade === decade ? "default" : "outline"}
              size="sm"
              className={`text-xs ${currentDecade === decade ? "bg-accent hover:bg-accent/90 text-accent-foreground" : ""}`}
              onClick={() => handleDecadeChange(decade)}
            >
              {decade}s
            </Button>
          ))}
        </div>
      </div>

      {/* Awards filter */}
      <div className="space-y-2">
        <label className="text-sm text-muted-foreground">Premios:</label>
        <div className="flex flex-wrap gap-2">
          <Button
            variant={hasAwards === undefined ? "default" : "outline"}
            size="sm"
            className={`text-xs ${hasAwards === undefined ? "bg-accent hover:bg-accent/90 text-accent-foreground" : ""}`}
            onClick={() => handleAwardsChange(null)}
          >
            Todos
          </Button>
          <Button
            variant={hasAwards === true ? "default" : "outline"}
            size="sm"
            className={`text-xs ${hasAwards === true ? "bg-accent hover:bg-accent/90 text-accent-foreground" : ""}`}
            onClick={() => handleAwardsChange(true)}
          >
            Con premios
          </Button>
          <Button
            variant={hasAwards === false ? "default" : "outline"}
            size="sm"
            className={`text-xs ${hasAwards === false ? "bg-accent hover:bg-accent/90 text-accent-foreground" : ""}`}
            onClick={() => handleAwardsChange(false)}
          >
            Sin premios
          </Button>
        </div>
      </div>

      {/* Country filter */}
      <div className="space-y-2">
        <label className="text-sm text-muted-foreground">País:</label>
        <select
          className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
          value={currentCountry || ""}
          onChange={(event) => handleCountryChange(event.target.value || null)}
        >
          <option value="">Todos</option>
          {countries.map((country) => (
            <option key={country} value={country}>
              {country}
            </option>
          ))}
        </select>
      </div>

      {/* Award type filter */}
      <div className="space-y-2">
        <label className="text-sm text-muted-foreground">Tipo de premio:</label>
        <select
          className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
          value={awardType || ""}
          onChange={(event) => handleAwardTypeChange(event.target.value || null)}
        >
          <option value="">Todos</option>
          {awardTypes.map((award) => (
            <option key={award} value={award}>
              {award}
            </option>
          ))}
        </select>
      </div>

      {/* Active filters summary */}
      {hasActiveFilters && (
        <div className="flex flex-wrap gap-2 pt-2 border-t border-border">
          {currentDecade !== undefined && (
            <Badge variant="secondary" className="text-xs">
              {currentDecade}s
              <button
                type="button"
                className="ml-1 hover:text-destructive"
                onClick={() => handleDecadeChange(null)}
              >
                x
              </button>
            </Badge>
          )}
          {hasAwards !== undefined && (
            <Badge variant="secondary" className="text-xs">
              {hasAwards ? "Con premios" : "Sin premios"}
              <button
                type="button"
                className="ml-1 hover:text-destructive"
                onClick={() => handleAwardsChange(null)}
              >
                x
              </button>
            </Badge>
          )}
          {currentCountry && (
            <Badge variant="secondary" className="text-xs">
              {currentCountry}
              <button
                type="button"
                className="ml-1 hover:text-destructive"
                onClick={() => handleCountryChange(null)}
              >
                x
              </button>
            </Badge>
          )}
          {awardType && (
            <Badge variant="secondary" className="text-xs">
              {awardType}
              <button
                type="button"
                className="ml-1 hover:text-destructive"
                onClick={() => handleAwardTypeChange(null)}
              >
                x
              </button>
            </Badge>
          )}
        </div>
      )}
    </div>
  );
}
