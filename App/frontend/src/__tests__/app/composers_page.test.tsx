import { render, screen } from "@testing-library/react";

const getComposersMock = jest.fn();
let paginationProps: { baseUrl?: string } | null = null;

jest.mock("next-intl/server", () => ({
  getTranslations: async () => (key: string) => key,
  setRequestLocale: jest.fn(),
}));

jest.mock("@/lib/api", () => ({
  getComposers: (...args: unknown[]) => getComposersMock(...args),
}));

jest.mock("@/components/composers/ComposerGrid", () => ({
  ComposerGrid: () => <div>ComposerGrid</div>,
}));

jest.mock("@/components/ui/Pagination", () => ({
  Pagination: (props: { baseUrl: string }) => {
    paginationProps = props;
    return <div>Pagination</div>;
  },
}));

jest.mock("@/components/composers/SortSelector", () => ({
  SortSelector: () => <div>SortSelector</div>,
}));

jest.mock("@/components/search/FilterPanel", () => ({
  FilterPanel: () => <div>FilterPanel</div>,
}));

jest.mock("@/components/search/SearchBar", () => ({
  SearchBar: () => <div>SearchBar</div>,
}));

import ComposersPage from "@/app/[locale]/composers/page";

describe("ComposersPage", () => {
  beforeEach(() => {
    getComposersMock.mockReset();
    paginationProps = null;
  });

  it("renders data with pagination", async () => {
    getComposersMock.mockResolvedValue({
      composers: [{ id: 1 }],
      pagination: { page: 1, per_page: 20, total: 2, pages: 2 },
    });
    const element = await ComposersPage({
      params: Promise.resolve({ locale: "es" }),
      searchParams: Promise.resolve({ page: "1" }),
    });
    render(element);
    expect(screen.getByText("ComposerGrid")).toBeInTheDocument();
    expect(screen.getByText("Pagination")).toBeInTheDocument();
  });

  it("renders no results when API fails", async () => {
    getComposersMock.mockRejectedValue(new Error("fail"));
    const element = await ComposersPage({
      params: Promise.resolve({ locale: "es" }),
      searchParams: Promise.resolve({}),
    });
    render(element);
    expect(screen.getByText("noResults")).toBeInTheDocument();
  });

  it("builds pagination URL with filters", async () => {
    getComposersMock.mockResolvedValue({
      composers: [{ id: 1 }],
      pagination: { page: 2, per_page: 20, total: 40, pages: 3 },
    });
    const element = await ComposersPage({
      params: Promise.resolve({ locale: "es" }),
      searchParams: Promise.resolve({
        page: "2",
        sort: "wins",
        order: "desc",
        decade: "1990",
        has_awards: "false",
        country: "USA",
        award_type: "Oscar",
      }),
    });
    render(element);

    expect(getComposersMock).toHaveBeenCalledWith({
      page: 2,
      per_page: 20,
      sort_by: "wins",
      order: "desc",
      decade: 1990,
      has_awards: false,
      country: "USA",
      award_type: "Oscar",
    });
    expect(paginationProps?.baseUrl).toContain("decade=1990");
    expect(paginationProps?.baseUrl).toContain("has_awards=false");
    expect(paginationProps?.baseUrl).toContain("country=USA");
    expect(paginationProps?.baseUrl).toContain("award_type=Oscar");
  });
});
