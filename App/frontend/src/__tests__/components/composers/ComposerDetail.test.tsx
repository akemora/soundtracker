import { render, screen } from "@testing-library/react";
import { ComposerDetail } from "@/components/composers/ComposerDetail";

let bornLabel = "born present";
jest.mock("next-intl", () => ({
  useTranslations: () => (key: string) => (key === "born" ? bornLabel : key),
}));

jest.mock("@/lib/api", () => ({
  getAssetUrl: (type: string, filename: string) =>
    `http://localhost:8000/api/assets/${type}/${filename}`,
}));

describe("ComposerDetail", () => {
  const composer = {
    id: 1,
    name: "John Williams",
    slug: "john_williams",
    country: "USA",
    index_num: 1,
    birth_year: 1932,
    death_year: null,
    photo_local: "photo.jpg",
    photo_url: null,
    biography: "Bio\n\nMore",
    style: "Style",
    anecdotes: "Story",
  };

  it("renders composer details", () => {
    bornLabel = "born present";
    render(
      <ComposerDetail
        composer={composer}
        stats={{ film_count: 1, top10_count: 1, wins: 2, nominations: 3, total_awards: 5, source_count: 0 }}
      />
    );
    expect(screen.getByText("John")).toBeInTheDocument();
    expect(screen.getAllByText("USA").length).toBeGreaterThan(0);
    expect(screen.getByText("Bio")).toBeInTheDocument();
    expect(screen.getByText("Style")).toBeInTheDocument();
    expect(screen.getByText("Story")).toBeInTheDocument();
  });

  it("renders placeholder when no photo", () => {
    bornLabel = "born";
    render(
      <ComposerDetail
        composer={{
          ...composer,
          photo_local: null,
          biography: null,
          style: null,
          anecdotes: null,
          country: null,
          birth_year: null,
          death_year: null,
        }}
        stats={{ film_count: 0, top10_count: 0, wins: 0, nominations: 0, total_awards: 0, source_count: 0 }}
      />
    );
    expect(screen.getByText("J")).toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("renders lifespan when death year exists", () => {
    bornLabel = "born";
    render(
      <ComposerDetail
        composer={{ ...composer, death_year: 2001 }}
        stats={{ film_count: 0, top10_count: 0, wins: 0, nominations: 0, total_awards: 0, source_count: 0 }}
      />
    );
    expect(screen.getByText("1932 - 2001")).toBeInTheDocument();
  });
});
