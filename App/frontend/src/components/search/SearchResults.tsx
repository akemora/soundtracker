import Image from "next/image";
import { Link } from "@/i18n/routing";
import { Card, CardContent } from "@/components/ui/card";
import type { SearchResult } from "@/lib/types";
import { getAssetUrl } from "@/lib/api";

interface SearchResultsProps {
  results: SearchResult[];
}

export function SearchResults({ results }: SearchResultsProps) {
  return (
    <div className="grid gap-4">
      {results.map((result) => (
        <SearchResultCard key={result.id} result={result} />
      ))}
    </div>
  );
}

function SearchResultCard({ result }: { result: SearchResult }) {
  const hasPhoto = result.photo_local != null;
  const photoUrl = hasPhoto
    ? getAssetUrl("photos", result.photo_local!)
    : null;

  const lifespan = [
    result.birth_year ? String(result.birth_year) : "",
    result.death_year ? String(result.death_year) : "",
  ]
    .filter(Boolean)
    .join(" - ");

  return (
    <Link href={`/composers/${result.slug}`}>
      <Card className="hover:shadow-lg transition-shadow">
        <CardContent className="p-4">
          <div className="flex gap-4">
            {/* Photo */}
            <div className="relative w-16 h-20 rounded overflow-hidden bg-muted flex-shrink-0">
              {photoUrl ? (
                <Image
                  src={photoUrl}
                  alt={result.name}
                  fill
                  className="object-cover"
                  sizes="64px"
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xl font-display text-muted-foreground">
                    {result.name.charAt(0)}
                  </span>
                </div>
              )}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg truncate hover:text-accent transition-colors">
                {result.name}
              </h3>
              <p className="text-sm text-muted-foreground">
                {result.country || "Unknown"}
                {lifespan && ` • ${lifespan}`}
              </p>
              {result.biography && (
                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                  {result.biography.slice(0, 150)}...
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
