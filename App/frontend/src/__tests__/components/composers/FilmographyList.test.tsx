import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { FilmographyList } from "@/components/composers/FilmographyList";

const getFilmographyMock = jest.fn();
jest.mock("@/lib/api", () => ({
  getFilmography: () => getFilmographyMock(),
  getAssetUrl: (type: string, filename: string) =>
    `http://localhost:8000/api/assets/${type}/${filename}`,
}));

const film = (
  id: number,
  year: number | null,
  poster: string | null,
  originalTitle: string | null = null
) => ({
  id,
  title: `Film ${id}`,
  year,
  original_title: originalTitle,
  poster_local: poster,
  is_top10: false,
  top10_rank: null,
  composer_id: 1,
  title_es: null,
  poster_url: null,
  tmdb_id: null,
  imdb_id: null,
  vote_average: 7.5,
  vote_count: 10,
  popularity: null,
  spotify_popularity: null,
  youtube_views: null,
});

describe("FilmographyList", () => {
  beforeEach(() => {
    getFilmographyMock.mockReset();
  });

  it("renders films and loads more", async () => {
    getFilmographyMock
      .mockResolvedValueOnce({
        composer_id: 1,
        composer_name: "Composer",
        films: [film(1, 1990, "poster.jpg"), film(2, 2000, null)],
        pagination: { page: 1, per_page: 20, total: 3, pages: 2 },
      })
      .mockResolvedValueOnce({
        composer_id: 1,
        composer_name: "Composer",
        films: [film(3, 2001, null)],
        pagination: { page: 2, per_page: 20, total: 3, pages: 2 },
      });

    render(<FilmographyList slug="composer" />);
    await waitFor(() => {
      expect(screen.getByText("Film 1")).toBeInTheDocument();
    });
    expect(screen.getByText("1990s")).toBeInTheDocument();
    expect(screen.getByText("2000s")).toBeInTheDocument();
    const decade2000 = screen.getByText("2000s");
    const decade1990 = screen.getByText("1990s");
    expect(
      decade2000.compareDocumentPosition(decade1990) & Node.DOCUMENT_POSITION_FOLLOWING
    ).toBeTruthy();

    const loadMore = screen.getByText(/Cargar más/);
    await act(async () => {
      fireEvent.click(loadMore);
    });

    await waitFor(() => {
      expect(screen.getByText("Film 3")).toBeInTheDocument();
    });
    expect(getFilmographyMock).toHaveBeenCalledTimes(2);
  });

  it("filters by decade", async () => {
    getFilmographyMock.mockResolvedValue({
      composer_id: 1,
      composer_name: "Composer",
      films: [film(1, 1990, null), film(2, 2000, null), film(3, null, null)],
      pagination: { page: 1, per_page: 20, total: 3, pages: 1 },
    });

    render(<FilmographyList slug="composer" />);
    await waitFor(() => {
      expect(screen.getByText("Film 1")).toBeInTheDocument();
    });
    expect(screen.getByText("Film 3")).toBeInTheDocument();

    fireEvent.click(screen.getByText("1990s"));
    expect(screen.queryByText("Film 2")).not.toBeInTheDocument();
    expect(screen.queryByText("Film 3")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Todas"));
    expect(screen.getByText("Film 2")).toBeInTheDocument();
    expect(screen.getByText("Film 3")).toBeInTheDocument();
  });

  it("shows error when loading fails", async () => {
    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => undefined);
    getFilmographyMock.mockRejectedValue(new Error("fail"));
    render(<FilmographyList slug="composer" />);
    await waitFor(() => {
      expect(screen.getByText("Error loading filmography")).toBeInTheDocument();
    });
    errorSpy.mockRestore();
  });

  it("handles load more errors", async () => {
    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => undefined);
    getFilmographyMock
      .mockResolvedValueOnce({
        composer_id: 1,
        composer_name: "Composer",
        films: [film(1, 1990, null)],
        pagination: { page: 1, per_page: 20, total: 2, pages: 2 },
      })
      .mockRejectedValueOnce(new Error("fail"));

    render(<FilmographyList slug="composer" />);
    await waitFor(() => {
      expect(screen.getByText("Film 1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/Cargar más/));
    await waitFor(() => {
      expect(screen.getByText("Film 1")).toBeInTheDocument();
    });
    errorSpy.mockRestore();
  });

  it("skips load more when already loading", async () => {
    let resolveNext: (value: unknown) => void = () => undefined;
    getFilmographyMock
      .mockResolvedValueOnce({
        composer_id: 1,
        composer_name: "Composer",
        films: [film(1, 1990, null)],
        pagination: { page: 1, per_page: 20, total: 2, pages: 2 },
      })
      .mockReturnValueOnce(
        new Promise((resolve) => {
          resolveNext = resolve;
        })
      );

    render(<FilmographyList slug="composer" />);
    await waitFor(() => {
      expect(screen.getByText("Film 1")).toBeInTheDocument();
    });

    const loadMore = screen.getByText(/Cargar más/);
    await act(async () => {
      fireEvent.click(loadMore);
    });
    await waitFor(() => {
      expect(loadMore).toBeDisabled();
    });
    await act(async () => {
      loadMore.removeAttribute("disabled");
      fireEvent.click(loadMore);
      loadMore.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });

    expect(getFilmographyMock).toHaveBeenCalledTimes(2);

    await act(async () => {
      resolveNext({
        composer_id: 1,
        composer_name: "Composer",
        films: [film(2, 2000, null)],
        pagination: { page: 2, per_page: 20, total: 2, pages: 2 },
      });
    });
  });

  it("shows original title when different", async () => {
    getFilmographyMock.mockResolvedValue({
      composer_id: 1,
      composer_name: "Composer",
      films: [film(1, 1990, null, "Original Film 1")],
      pagination: { page: 1, per_page: 20, total: 1, pages: 1 },
    });

    render(<FilmographyList slug="composer" />);
    await waitFor(() => {
      expect(screen.getByText("(Original Film 1)")).toBeInTheDocument();
    });
  });

});
