"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import Image from "next/image";
import { useRouter, Link } from "@/i18n/routing";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { search, getAssetUrl } from "@/lib/api";
import type { SearchResult } from "@/lib/types";

interface SearchBarProps {
  placeholder?: string;
  defaultValue?: string;
  showAutocomplete?: boolean;
}

export function SearchBar({
  placeholder = "Search...",
  defaultValue = "",
  showAutocomplete = true,
}: SearchBarProps) {
  const [query, setQuery] = useState(defaultValue);
  const [suggestions, setSuggestions] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  // Debounced search for autocomplete
  useEffect(() => {
    if (!showAutocomplete) return;

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    if (query.trim().length < 2) {
      setSuggestions([]);
      setIsOpen(false);
      return;
    }

    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      try {
        const result = await search(query.trim(), 5);
        setSuggestions(result.results);
        setIsOpen(result.results.length > 0);
        setSelectedIndex(-1);
      } catch {
        setSuggestions([]);
        setIsOpen(false);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      clearTimeout(debounceRef.current as NodeJS.Timeout);
    };
  }, [query, showAutocomplete]);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (query.trim().length >= 2) {
        setIsOpen(false);
        router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      }
    },
    [query, router]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (!isOpen || suggestions.length === 0) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) => (prev < suggestions.length - 1 ? prev + 1 : 0));
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : suggestions.length - 1));
          break;
        case "Enter": {
          const selected = suggestions[selectedIndex];
          if (selectedIndex >= 0 && selected) {
            e.preventDefault();
            setIsOpen(false);
            router.push(`/composers/${selected.slug}`);
          }
          break;
        }
        case "Escape":
          setIsOpen(false);
          setSelectedIndex(-1);
          break;
      }
    },
    [isOpen, suggestions, selectedIndex, router]
  );

  const handleSuggestionClick = useCallback(() => {
    setIsOpen(false);
    setQuery("");
  }, []);

  return (
    <div ref={containerRef} className="relative w-full">
      <form onSubmit={handleSubmit} className="flex gap-2 w-full">
        <div className="relative flex-1">
          <Input
            ref={inputRef}
            type="search"
            placeholder={placeholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onFocus={() => suggestions.length > 0 && setIsOpen(true)}
            className="flex-1 pr-8"
            minLength={2}
            autoComplete="off"
            aria-autocomplete="list"
            aria-expanded={isOpen}
            aria-controls="search-suggestions"
          />
          {loading && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <LoadingSpinner className="h-4 w-4" />
            </div>
          )}
        </div>
        <Button type="submit" disabled={query.trim().length < 2}>
          <SearchIcon className="h-4 w-4 mr-2" />
          <span className="sr-only sm:not-sr-only">Buscar</span>
        </Button>
      </form>

      {/* Autocomplete dropdown */}
      {isOpen && suggestions.length > 0 && (
        <div
          id="search-suggestions"
          role="listbox"
          className="absolute z-50 top-full left-0 right-0 mt-1 bg-background border border-border rounded-md shadow-lg overflow-hidden"
        >
          {suggestions.map((suggestion, index) => (
            <Link
              key={suggestion.id}
              href={`/composers/${suggestion.slug}`}
              onClick={handleSuggestionClick}
              role="option"
              aria-selected={index === selectedIndex}
              className={`flex items-center gap-3 px-3 py-2 cursor-pointer transition-colors ${
                index === selectedIndex
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-muted"
              }`}
            >
              {/* Photo thumbnail */}
              <div className="relative w-8 h-8 rounded-full bg-muted overflow-hidden flex-shrink-0">
                {suggestion.photo_local ? (
                  <Image
                    src={getAssetUrl("photos", suggestion.photo_local)}
                    alt=""
                    fill
                    className="object-cover"
                    sizes="32px"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center text-xs text-muted-foreground">
                    🎵
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <div className="font-medium truncate">{suggestion.name}</div>
                <div className="text-xs text-muted-foreground">
                  {suggestion.country && <span>{suggestion.country}</span>}
                  {suggestion.birth_year && (
                    <span className="ml-2">
                      {suggestion.birth_year}
                      {suggestion.death_year && `-${suggestion.death_year}`}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}

          {/* View all results link */}
          <button
            type="button"
            onClick={() => {
              setIsOpen(false);
              router.push(`/search?q=${encodeURIComponent(query.trim())}`);
            }}
            className="w-full px-3 py-2 text-sm text-center text-muted-foreground hover:bg-muted border-t border-border"
          >
            Ver todos los resultados
          </button>
        </div>
      )}
    </div>
  );
}

function SearchIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

export function LoadingSpinner({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className={`animate-spin ${className || ""}`}
    >
      <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" strokeOpacity="1" />
    </svg>
  );
}
