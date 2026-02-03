import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function ComposerCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      {/* Photo skeleton */}
      <Skeleton className="aspect-[3/4] w-full" />

      {/* Info skeleton */}
      <CardContent className="p-4 space-y-3">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <div className="flex gap-4">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-3 w-16" />
        </div>
      </CardContent>
    </Card>
  );
}

export function ComposerGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <ComposerCardSkeleton key={i} />
      ))}
    </div>
  );
}
