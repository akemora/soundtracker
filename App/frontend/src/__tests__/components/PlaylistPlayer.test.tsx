import { fireEvent, render, screen } from "@testing-library/react";
import { PlaylistPlayer } from "@/components/PlaylistPlayer";

const tracks = [
  {
    position: 1,
    film: "Star Wars",
    film_year: 1977,
    track_title: "Main Title",
    is_original_pick: true,
    source: "youtube",
    url: "https://www.youtube.com/watch?v=abc",
    embed_url: "https://www.youtube.com/embed/abc",
    is_free: true,
    duration: "2:03",
    thumbnail: "https://i.ytimg.com/vi/abc/hqdefault.jpg",
    alternatives: [],
  },
  {
    position: 2,
    film: "Schindler's List",
    film_year: 1993,
    track_title: "Theme",
    is_original_pick: true,
    source: "itunes",
    url: "https://music.apple.com/track/1",
    embed_url: null,
    is_free: false,
    duration: null,
    thumbnail: null,
    alternatives: [],
    purchase_links: [
      { source: "itunes", url: "https://music.apple.com/track/1" },
    ],
  },
];


describe("PlaylistPlayer", () => {
  it("renders playlist and switches tracks", () => {
    render(
      <PlaylistPlayer
        composerSlug="john_williams"
        composerName="John Williams"
        tracks={tracks}
      />
    );

    expect(screen.getByText("Main Title")).toBeInTheDocument();
    expect(screen.getByText("Star Wars")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Theme"));

    expect(
      screen.getByText("Este track no está disponible gratuitamente.")
    ).toBeInTheDocument();
    expect(screen.getByText("Comprar en itunes")).toBeInTheDocument();
  });
});
