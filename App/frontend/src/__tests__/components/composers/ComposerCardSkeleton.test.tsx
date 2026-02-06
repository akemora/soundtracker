import { render } from "@testing-library/react";
import { ComposerCardSkeleton, ComposerGridSkeleton } from "@/components/composers/ComposerCardSkeleton";

describe("ComposerCardSkeleton", () => {
  it("renders skeleton card", () => {
    const { container } = render(<ComposerCardSkeleton />);
    expect(container.querySelector('[data-slot="skeleton"]')).toBeInTheDocument();
  });

  it("renders grid skeleton count", () => {
    const { container } = render(<ComposerGridSkeleton count={3} />);
    const cards = container.querySelectorAll('[data-slot="card"]');
    expect(cards.length).toBe(3);
  });

  it("uses default count when not provided", () => {
    const { container } = render(<ComposerGridSkeleton />);
    const cards = container.querySelectorAll('[data-slot="card"]');
    expect(cards.length).toBe(8);
  });
});
