import { fireEvent, render, screen } from "@testing-library/react";
import { Top10Gallery } from "@/components/composers/Top10Gallery";

jest.mock("@/lib/api", () => ({
  getAssetUrl: (type: string, filename: string) =>
    `http://localhost:8000/api/assets/${type}/${filename}`,
}));

describe("Top10Gallery", () => {
  const films = [
    {
      id: 1,
      title: "Film One",
      year: 2000,
      original_title: "Original One",
      poster_local: null,
      is_top10: true,
      top10_rank: 1,
      composer_id: 1,
      title_es: null,
      poster_url: null,
      tmdb_id: null,
      imdb_id: "tt123",
      vote_average: 7.2,
      vote_count: 10,
      popularity: null,
      spotify_popularity: null,
      youtube_views: null,
    },
    {
      id: 2,
      title: "Film Two",
      year: 1999,
      original_title: null,
      poster_local: null,
      is_top10: true,
      top10_rank: null,
      composer_id: 1,
      title_es: null,
      poster_url: null,
      tmdb_id: null,
      imdb_id: null,
      vote_average: null,
      vote_count: null,
      popularity: null,
      spotify_popularity: null,
      youtube_views: null,
    },
    {
      id: 3,
      title: "Film Three",
      year: 2001,
      original_title: "Original Three",
      poster_local: "poster.jpg",
      is_top10: true,
      top10_rank: 2,
      composer_id: 1,
      title_es: null,
      poster_url: null,
      tmdb_id: null,
      imdb_id: null,
      vote_average: 8.1,
      vote_count: 100,
      popularity: null,
      spotify_popularity: null,
      youtube_views: null,
    },
  ];

  it("renders films and opens modal", () => {
    render(<Top10Gallery films={films} />);
    fireEvent.click(screen.getAllByText("Film Three")[0]);
    expect(screen.getAllByAltText("Film Three").length).toBeGreaterThan(1);
    expect(screen.getAllByAltText("Film Three")[1].getAttribute("src")).toContain("poster.jpg");
    expect(screen.getAllByText("Film One").length).toBeGreaterThan(0);
    expect(screen.getByText("Original Three")).toBeInTheDocument();
    expect(screen.getByText("Puntuación TMDB")).toBeInTheDocument();

    fireEvent.click(screen.getAllByText("Close")[0]);
  });

  it("opens modal without poster when missing", () => {
    render(<Top10Gallery films={films} />);
    fireEvent.click(screen.getAllByText("Film One")[0]);
    expect(screen.queryByAltText("Film One")).not.toBeInTheDocument();
  });
});
