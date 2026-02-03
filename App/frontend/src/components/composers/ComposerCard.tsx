import Image from "next/image";
import { Link } from "@/i18n/routing";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ComposerWithStats } from "@/lib/types";
import { getAssetUrl } from "@/lib/api";

interface ComposerCardProps {
  composer: ComposerWithStats;
}

export function ComposerCard({ composer }: ComposerCardProps) {
  const hasPhoto = composer.photo_local != null;
  const photoUrl = hasPhoto
    ? getAssetUrl("photos", composer.photo_local!)
    : "/placeholder-composer.jpg";

  const lifespan = [
    composer.birth_year ? String(composer.birth_year) : "?",
    composer.death_year ? String(composer.death_year) : "present",
  ].join(" - ");

  return (
    <Link href={`/composers/${composer.slug}`}>
      <Card className="group overflow-hidden transition-all hover:shadow-lg hover:-translate-y-1">
        {/* Photo */}
        <div className="relative aspect-[3/4] bg-muted">
          {hasPhoto ? (
            <Image
              src={photoUrl}
              alt={composer.name}
              fill
              className="object-cover transition-transform group-hover:scale-105"
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
              unoptimized
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center bg-muted">
              <span className="text-4xl font-display text-muted-foreground">
                {composer.name.charAt(0)}
              </span>
            </div>
          )}

          {/* Awards badge */}
          {composer.wins > 0 && (
            <div className="absolute top-2 right-2">
              <Badge variant="secondary" className="bg-primary text-primary-foreground font-bold shadow-md">
                ★ {composer.wins}
              </Badge>
            </div>
          )}
        </div>

        {/* Info */}
        <CardContent className="p-4">
          <h3 className="font-display font-semibold text-lg truncate transition-colors">
            {(() => {
              const parts = composer.name.split(" ");
              const firstName = parts[0];
              const lastName = parts.slice(1).join(" ");
              return (
                <>
                  {firstName}{lastName && <> <span className="text-accent">{lastName}</span></>}
                </>
              );
            })()}
          </h3>

          <p className="text-sm text-muted-foreground mt-1">
            {composer.country ? `${composer.country} • ` : ""}{lifespan}
          </p>

          {/* Stats */}
          <div className="flex gap-4 mt-3 text-xs text-muted-foreground">
            <span>{composer.film_count} películas</span>
            {composer.total_awards > 0 && (
              <span>{composer.total_awards} premios</span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
