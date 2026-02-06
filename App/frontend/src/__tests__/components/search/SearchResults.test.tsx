import { render, screen } from "@testing-library/react";
import { SearchResults } from "@/components/search/SearchResults";

jest.mock("@/lib/api", () => ({
  getAssetUrl: (type: string, filename: string) =>
    `http://localhost:8000/api/assets/${type}/${filename}`,
}));

describe("SearchResults", () => {
  const results = [
    {
      id: 1,
      name: "Composer One",
      slug: "composer_one",
      country: "USA",
      birth_year: 1900,
      death_year: 1950,
      photo_local: "photo.jpg",
      biography: "Bio",
      rank: 1,
    },
    {
      id: 2,
      name: "Composer Two",
      slug: "composer_two",
      country: null,
      birth_year: null,
      death_year: null,
      photo_local: null,
      biography: null,
      rank: 2,
    },
  ];

  it("renders results", () => {
    render(<SearchResults results={results} />);
    expect(screen.getByText("Composer One")).toBeInTheDocument();
    expect(screen.getByText("Composer Two")).toBeInTheDocument();
  });
});
