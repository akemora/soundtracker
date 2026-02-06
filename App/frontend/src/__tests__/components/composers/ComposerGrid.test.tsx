import { render, screen } from "@testing-library/react";
import { ComposerGrid } from "@/components/composers/ComposerGrid";

const composer = {
  id: 1,
  name: "Composer",
  slug: "composer",
  country: "USA",
  index_num: 1,
  birth_year: 1900,
  death_year: null,
  photo_local: null,
  film_count: 1,
  top10_count: 1,
  wins: 0,
  nominations: 0,
  total_awards: 0,
  source_count: 0,
};

describe("ComposerGrid", () => {
  it("returns null on empty list", () => {
    const { container } = render(<ComposerGrid composers={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders composers", () => {
    render(<ComposerGrid composers={[composer]} />);
    expect(screen.getByText("Composer")).toBeInTheDocument();
  });
});
