import { render, screen } from "@testing-library/react";

const getComposerMock = jest.fn();
const getPlaylistMock = jest.fn();
const notFoundMock = jest.fn(() => {
  throw new Error("not-found");
});

jest.mock("next-intl/server", () => ({
  getTranslations: async () => (key: string) => key,
  setRequestLocale: jest.fn(),
}));

jest.mock("next/navigation", () => ({
  notFound: () => notFoundMock(),
}));

jest.mock("@/lib/api", () => ({
  getComposer: () => getComposerMock(),
  getPlaylist: () => getPlaylistMock(),
}));

jest.mock("@/components/composers/ComposerDetail", () => ({
  ComposerDetail: () => <div>ComposerDetail</div>,
}));

jest.mock("@/components/composers/Top10Gallery", () => ({
  Top10Gallery: () => <div>Top10Gallery</div>,
}));

jest.mock("@/components/composers/FilmographyList", () => ({
  FilmographyList: () => <div>FilmographyList</div>,
}));

jest.mock("@/components/composers/AwardsList", () => ({
  AwardsList: () => <div>AwardsList</div>,
}));

jest.mock("@/components/PlaylistPlayer", () => ({
  PlaylistPlayer: () => <div>PlaylistPlayer</div>,
}));

import ComposerPage, { generateMetadata } from "@/app/[locale]/composers/[slug]/page";

describe("ComposerPage", () => {
  beforeEach(() => {
    getComposerMock.mockReset();
    getPlaylistMock.mockReset();
    notFoundMock.mockClear();
  });

  it("generates metadata from composer", async () => {
    getComposerMock.mockResolvedValue({
      composer: { name: "John", biography: "Bio" },
    });
    const data = await generateMetadata({ params: Promise.resolve({ locale: "es", slug: "john" }) });
    expect(data.title).toContain("John");
  });

  it("generates metadata without biography", async () => {
    getComposerMock.mockResolvedValue({
      composer: { name: "John", biography: null },
    });
    const data = await generateMetadata({ params: Promise.resolve({ locale: "es", slug: "john" }) });
    expect(data.description).toContain("Film composer John");
  });

  it("generates fallback metadata on error", async () => {
    getComposerMock.mockRejectedValue(new Error("fail"));
    const data = await generateMetadata({ params: Promise.resolve({ locale: "es", slug: "john" }) });
    expect(data.title).toBe("Composer - SOUNDTRACKER");
  });

  it("renders composer page with playlist", async () => {
    getComposerMock.mockResolvedValue({
      composer: { name: "John" },
      stats: { film_count: 1, total_awards: 1 },
      top10: [{ id: 1 }],
    });
    getPlaylistMock.mockResolvedValue({
      composer_slug: "john",
      composer_name: "John",
      tracks: [{ position: 1 }],
      free_count: 1,
      paid_count: 0,
    });
    const element = await ComposerPage({
      params: Promise.resolve({ locale: "es", slug: "john" }),
    });
    render(element);
    expect(screen.getByText("ComposerDetail")).toBeInTheDocument();
    expect(screen.getByText("Top10Gallery")).toBeInTheDocument();
    expect(screen.getByText("PlaylistPlayer")).toBeInTheDocument();
    expect(screen.getByText("FilmographyList")).toBeInTheDocument();
    expect(screen.getByText("AwardsList")).toBeInTheDocument();
  });

  it("calls notFound on missing composer", async () => {
    getComposerMock.mockRejectedValue(new Error("fail"));
    await expect(
      ComposerPage({ params: Promise.resolve({ locale: "es", slug: "missing" }) })
    ).rejects.toThrow("not-found");
  });

  it("renders composer page without playlist on error", async () => {
    getComposerMock.mockResolvedValue({
      composer: { name: "John" },
      stats: { film_count: 1, total_awards: 0 },
      top10: [],
    });
    getPlaylistMock.mockRejectedValue(new Error("fail"));
    const element = await ComposerPage({
      params: Promise.resolve({ locale: "es", slug: "john" }),
    });
    render(element);
    expect(screen.getByText("ComposerDetail")).toBeInTheDocument();
    expect(screen.queryByText("PlaylistPlayer")).not.toBeInTheDocument();
  });
});
