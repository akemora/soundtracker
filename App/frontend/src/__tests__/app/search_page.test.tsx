import { render, screen } from "@testing-library/react";

const searchMock = jest.fn();

jest.mock("next-intl/server", () => ({
  getTranslations: async () => (key: string) => key,
  setRequestLocale: jest.fn(),
}));

jest.mock("@/lib/api", () => ({
  search: () => searchMock(),
}));

jest.mock("@/components/search/SearchBar", () => ({
  SearchBar: () => <div>SearchBar</div>,
}));

jest.mock("@/components/search/SearchResults", () => ({
  SearchResults: () => <div>SearchResults</div>,
}));

import SearchPage from "@/app/[locale]/search/page";

describe("SearchPage", () => {
  beforeEach(() => {
    searchMock.mockReset();
  });

  it("renders empty prompt when no query", async () => {
    const element = await SearchPage({
      params: Promise.resolve({ locale: "es" }),
      searchParams: Promise.resolve({}),
    });
    render(element);
    expect(screen.getByText("Escribe al menos 2 caracteres para buscar")).toBeInTheDocument();
  });

  it("renders results when query has matches", async () => {
    searchMock.mockResolvedValue({ query: "ab", results: [{ id: 1 }], count: 1 });
    const element = await SearchPage({
      params: Promise.resolve({ locale: "es" }),
      searchParams: Promise.resolve({ q: "ab" }),
    });
    render(element);
    expect(screen.getByText("SearchResults")).toBeInTheDocument();
  });

  it("renders error when search fails", async () => {
    searchMock.mockRejectedValue(new Error("fail"));
    const element = await SearchPage({
      params: Promise.resolve({ locale: "es" }),
      searchParams: Promise.resolve({ q: "ab" }),
    });
    render(element);
    expect(screen.getByText("Error al buscar. Intenta de nuevo.")).toBeInTheDocument();
  });
});
