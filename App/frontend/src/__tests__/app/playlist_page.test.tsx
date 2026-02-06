import { render, screen } from "@testing-library/react";

const getPlaylistMock = jest.fn();

jest.mock("next-intl/server", () => ({
  setRequestLocale: jest.fn(),
}));

jest.mock("@/lib/api", () => ({
  getPlaylist: () => getPlaylistMock(),
}));

jest.mock("@/components/PlaylistPlayer", () => ({
  PlaylistPlayer: () => <div>PlaylistPlayer</div>,
}));

import PlaylistPage, { generateMetadata } from "@/app/[locale]/composers/[slug]/playlist/page";

describe("PlaylistPage", () => {
  beforeEach(() => {
    getPlaylistMock.mockReset();
  });

  it("generates metadata", async () => {
    getPlaylistMock.mockResolvedValue({ composer_name: "John" });
    const data = await generateMetadata({ params: Promise.resolve({ locale: "es", slug: "john" }) });
    expect(data.title).toContain("John");
  });

  it("generates fallback metadata on error", async () => {
    getPlaylistMock.mockRejectedValue(new Error("fail"));
    const data = await generateMetadata({ params: Promise.resolve({ locale: "es", slug: "john" }) });
    expect(data.title).toBe("Playlist - SOUNDTRACKER");
  });

  it("renders fallback when no playlist", async () => {
    getPlaylistMock.mockRejectedValue(new Error("fail"));
    const element = await PlaylistPage({ params: Promise.resolve({ locale: "es", slug: "john" }) });
    render(element);
    expect(screen.getByText("No hay playlist disponible.")).toBeInTheDocument();
  });

  it("renders playlist when available", async () => {
    getPlaylistMock.mockResolvedValue({
      composer_slug: "john",
      composer_name: "John",
      free_count: 1,
      paid_count: 0,
      tracks: [{ position: 1 }],
    });
    const element = await PlaylistPage({ params: Promise.resolve({ locale: "es", slug: "john" }) });
    render(element);
    expect(screen.getByText("PlaylistPlayer")).toBeInTheDocument();
  });
});
