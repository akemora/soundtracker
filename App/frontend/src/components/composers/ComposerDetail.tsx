import Image from "next/image";
import { useTranslations } from "next-intl";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { ComposerDetail as ComposerDetailType, ComposerStats } from "@/lib/types";
import { getAssetUrl } from "@/lib/api";

interface ComposerDetailProps {
  composer: ComposerDetailType;
  stats: ComposerStats | null;
}

export function ComposerDetail({ composer, stats }: ComposerDetailProps) {
  const t = useTranslations("composer");

  const hasPhoto = composer.photo_local != null;
  const photoUrl = hasPhoto
    ? getAssetUrl("photos", composer.photo_local!)
    : null;

  const lifespan = [
    composer.birth_year ? String(composer.birth_year) : "?",
    composer.death_year ? String(composer.death_year) : t("born").includes("present") ? "present" : "",
  ]
    .filter(Boolean)
    .join(" - ");

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Left Column - Photo and Quick Stats */}
      <div className="lg:col-span-1">
        {/* Photo */}
        <Card className="overflow-hidden">
          <div className="relative aspect-[3/4] bg-muted">
            {photoUrl ? (
              <Image
                src={photoUrl}
                alt={composer.name}
                fill
                className="object-cover"
                priority
                sizes="(max-width: 1024px) 100vw, 33vw"
                unoptimized
              />
            ) : (
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-6xl font-display text-muted-foreground">
                  {composer.name.charAt(0)}
                </span>
              </div>
            )}
          </div>
        </Card>

        {/* Quick Stats */}
        {stats && (
          <Card className="mt-4">
            <CardContent className="p-4 space-y-3">
              <StatRow label={t("country")} value={composer.country || "—"} />
              <StatRow label={t("born")} value={lifespan} />
              {stats.film_count > 0 && (
                <StatRow label="Películas" value={String(stats.film_count)} />
              )}
              {stats.total_awards > 0 && (
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Premios</span>
                  <div className="flex gap-2">
                    {stats.wins > 0 && (
                      <Badge className="bg-gold text-gold-foreground font-bold">
                        ★ {stats.wins} wins
                      </Badge>
                    )}
                    {stats.nominations > 0 && (
                      <Badge variant="secondary">{stats.nominations} nom.</Badge>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Right Column - Biography and Details */}
      <div className="lg:col-span-2 space-y-8">
        {/* Header */}
        <div>
          <h1 className="font-display text-3xl md:text-4xl font-bold mb-2">
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
          </h1>
          {composer.country && (
            <p className="text-lg text-muted-foreground">{composer.country}</p>
          )}
        </div>

        {/* Biography */}
        {composer.biography && (
          <section>
            <h2 className="font-display text-xl font-semibold mb-3">
              {t("biography")}
            </h2>
            <div className="prose prose-neutral dark:prose-invert max-w-none">
              {composer.biography.split("\n\n").map((paragraph, i) => (
                <p key={i} className="text-muted-foreground leading-relaxed mb-4">
                  {paragraph}
                </p>
              ))}
            </div>
          </section>
        )}

        {/* Musical Style */}
        {composer.style && (
          <>
            <Separator className="bg-accent" />
            <section>
              <h2 className="font-display text-xl font-semibold mb-3">
                {t("style")}
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                {composer.style}
              </p>
            </section>
          </>
        )}

        {/* Anecdotes */}
        {composer.anecdotes && (
          <>
            <Separator className="bg-accent" />
            <section>
              <h2 className="font-display text-xl font-semibold mb-3">
                Anécdotas
              </h2>
              <div className="bg-muted/50 rounded-lg p-4 border-l-4 border-accent">
                <p className="text-muted-foreground italic leading-relaxed">
                  {composer.anecdotes}
                </p>
              </div>
            </section>
          </>
        )}
      </div>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
