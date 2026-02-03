"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getAwards } from "@/lib/api";
import type { AwardDetail, AwardListResponse } from "@/lib/types";

interface AwardsListProps {
  slug: string;
}

export function AwardsList({ slug }: AwardsListProps) {
  const [data, setData] = useState<AwardListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAwards() {
      try {
        const result = await getAwards(slug);
        setData(result);
      } catch (err) {
        setError("Error loading awards");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchAwards();
  }, [slug]);

  if (loading) {
    return <AwardsListSkeleton />;
  }

  if (error || !data) {
    return <p className="text-muted-foreground">{error || "No awards found"}</p>;
  }

  // Group awards by award_name
  const grouped = data.awards.reduce(
    (acc, award) => {
      const key = award.award_name;
      if (!acc[key]) {
        acc[key] = [];
      }
      acc[key].push(award);
      return acc;
    },
    {} as Record<string, AwardDetail[]>
  );

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="flex gap-4">
        <Badge className="bg-gold text-gold-foreground text-sm px-3 py-1 font-bold">
          ★ {data.summary.wins} Victorias
        </Badge>
        <Badge variant="secondary" className="text-sm px-3 py-1">
          {data.summary.nominations} Nominaciones
        </Badge>
      </div>

      {/* Grouped by Award Type */}
      <div className="grid gap-4">
        {Object.entries(grouped).map(([awardName, awards]) => (
          <Card key={awardName}>
            <CardContent className="p-4">
              <h3 className="font-semibold mb-3">{awardName}</h3>
              <div className="space-y-2">
                {awards
                  .sort((a, b) => (b.year ?? 0) - (a.year ?? 0))
                  .map((award) => (
                    <AwardItem key={award.id} award={award} />
                  ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function AwardItem({ award }: { award: AwardDetail }) {
  const isWin = award.status === "win";

  return (
    <div className="flex items-center justify-between py-1 border-b border-border/50 last:border-0">
      <div className="flex items-center gap-3">
        <span className="text-lg">{isWin ? "🏆" : "📋"}</span>
        <div>
          {award.category && (
            <p className="text-sm font-medium">{award.category}</p>
          )}
          {award.film_title && (
            <p className="text-xs text-muted-foreground">{award.film_title}</p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        {award.year && (
          <span className="text-sm text-muted-foreground">{award.year}</span>
        )}
        <Badge variant={isWin ? "default" : "secondary"} className={isWin ? "bg-gold text-gold-foreground font-bold" : ""}>
          {isWin ? "★ Win" : "Nom."}
        </Badge>
      </div>
    </div>
  );
}

function AwardsListSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-8 w-40" />
      </div>
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-24 w-full" />
    </div>
  );
}
