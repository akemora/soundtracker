import { render, screen } from "@testing-library/react";
import { ComposerCard } from "@/components/composers/ComposerCard";
import type { ComposerWithStats } from "@/lib/types";

// Mock the API module
jest.mock("@/lib/api", () => ({
  getAssetUrl: (type: string, filename: string) => `http://localhost:8000/api/assets/${type}/${filename}`,
}));

describe("ComposerCard", () => {
  const mockComposer: ComposerWithStats = {
    id: 1,
    name: "John Williams",
    slug: "john_williams",
    country: "USA",
    index_num: 1,
    birth_year: 1932,
    death_year: null,
    photo_local: "john_williams.jpg",
    film_count: 150,
    top10_count: 10,
    wins: 5,
    nominations: 52,
    total_awards: 57,
    source_count: 3,
  };

  it("renders composer name", () => {
    render(<ComposerCard composer={mockComposer} />);
    expect(
      screen.getByRole("heading", { level: 3, name: /John Williams/ })
    ).toBeInTheDocument();
  });

  it("renders country and lifespan", () => {
    render(<ComposerCard composer={mockComposer} />);
    expect(screen.getByText(/USA.*1932.*present/)).toBeInTheDocument();
  });

  it("renders film count", () => {
    render(<ComposerCard composer={mockComposer} />);
    expect(screen.getByText("150 películas")).toBeInTheDocument();
  });

  it("renders awards count when composer has awards", () => {
    render(<ComposerCard composer={mockComposer} />);
    expect(screen.getByText("57 premios")).toBeInTheDocument();
  });

  it("renders wins badge when composer has wins", () => {
    render(<ComposerCard composer={mockComposer} />);
    expect(screen.getByText(/★\s*5/)).toBeInTheDocument();
  });

  it("renders photo when available", () => {
    render(<ComposerCard composer={mockComposer} />);
    const img = screen.getByRole("img", { name: "John Williams" });
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute(
      "src",
      "http://localhost:8000/api/assets/photos/john_williams.jpg"
    );
  });

  it("renders initial when no photo available", () => {
    const composerWithoutPhoto: ComposerWithStats = {
      ...mockComposer,
      photo_local: null,
    };
    render(<ComposerCard composer={composerWithoutPhoto} />);
    expect(screen.getByText("J")).toBeInTheDocument();
  });

  it("hides awards count when composer has no awards", () => {
    const composerWithoutAwards: ComposerWithStats = {
      ...mockComposer,
      wins: 0,
      nominations: 0,
      total_awards: 0,
    };
    render(<ComposerCard composer={composerWithoutAwards} />);
    expect(screen.queryByText(/premios/)).not.toBeInTheDocument();
  });

  it("links to composer detail page", () => {
    render(<ComposerCard composer={mockComposer} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/composers/john_williams");
  });

  it("renders deceased composer lifespan correctly", () => {
    const deceasedComposer: ComposerWithStats = {
      ...mockComposer,
      name: "Max Steiner",
      slug: "max_steiner",
      birth_year: 1888,
      death_year: 1971,
    };
    render(<ComposerCard composer={deceasedComposer} />);
    expect(screen.getByText(/1888.*-.*1971/)).toBeInTheDocument();
  });

  it("renders unknown birth year and no country", () => {
    const unknownComposer: ComposerWithStats = {
      ...mockComposer,
      country: null,
      birth_year: null,
      death_year: null,
    };
    render(<ComposerCard composer={unknownComposer} />);
    expect(screen.getByText(/\? - present/)).toBeInTheDocument();
  });
});
