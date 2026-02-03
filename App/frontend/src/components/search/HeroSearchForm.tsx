import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface HeroSearchFormProps {
  placeholder: string;
  buttonLabel: string;
}

export function HeroSearchForm({ placeholder, buttonLabel }: HeroSearchFormProps) {
  return (
    <form action="/search" method="get" className="flex gap-2 w-full">
      <div className="relative flex-1">
        <Input
          type="search"
          name="q"
          placeholder={placeholder}
          minLength={2}
          required
          autoComplete="off"
          className="flex-1 pr-8"
        />
      </div>
      <Button type="submit">
        <span className="sr-only sm:not-sr-only">{buttonLabel}</span>
      </Button>
    </form>
  );
}
