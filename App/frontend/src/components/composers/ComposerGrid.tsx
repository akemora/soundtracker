import type { ComposerWithStats } from "@/lib/types";
import { ComposerCard } from "./ComposerCard";

interface ComposerGridProps {
  composers: ComposerWithStats[];
}

export function ComposerGrid({ composers }: ComposerGridProps) {
  if (composers.length === 0) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {composers.map((composer) => (
        <ComposerCard key={composer.id} composer={composer} />
      ))}
    </div>
  );
}
