import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { FilterPanel } from "@/components/search/FilterPanel";

const pushMock = jest.fn();

jest.mock("@/i18n/routing", () => ({
  useRouter: () => ({
    push: pushMock,
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
  usePathname: () => "/composers",
}));

jest.mock("next/navigation", () => ({
  useSearchParams: () => new URLSearchParams("page=2"),
}));

const getComposerFiltersMock = jest.fn();
jest.mock("@/lib/api", () => ({
  getComposerFilters: () => getComposerFiltersMock(),
}));

const getAt = (items: HTMLElement[], index: number, label: string) => {
  const item = items[index];
  if (!item) {
    throw new Error(`Missing ${label}`);
  }
  return item;
};

describe("FilterPanel", () => {
  beforeEach(() => {
    pushMock.mockReset();
    getComposerFiltersMock.mockReset();
  });

  it("loads filters and renders options", async () => {
    getComposerFiltersMock.mockResolvedValue({
      countries: ["USA"],
      award_types: ["Oscar"],
    });
    render(<FilterPanel />);
    expect(await screen.findByText("USA")).toBeInTheDocument();
    expect(await screen.findByText("Oscar")).toBeInTheDocument();
  });

  it("handles filter actions", async () => {
    getComposerFiltersMock.mockResolvedValue({ countries: ["USA"], award_types: ["Oscar"] });
    render(<FilterPanel currentDecade={1990} hasAwards={true} currentCountry="USA" awardType="Oscar" />);
    await waitFor(() => {
      expect(screen.getByText("Limpiar filtros")).toBeInTheDocument();
    });

    fireEvent.click(getAt(screen.getAllByText("Todas"), 0, "Todas"));
    expect(pushMock).toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Todos" }));
    expect(pushMock).toHaveBeenCalled();

    fireEvent.click(getAt(screen.getAllByText("1890s"), 0, "1890s"));
    expect(pushMock).toHaveBeenCalled();

    fireEvent.click(getAt(screen.getAllByText("Con premios"), 0, "Con premios"));
    expect(pushMock).toHaveBeenCalled();
    fireEvent.click(getAt(screen.getAllByText("Sin premios"), 0, "Sin premios"));
    expect(pushMock).toHaveBeenCalled();

    const selects = screen.getAllByRole("combobox");
    const countrySelect = getAt(selects, 0, "country select");
    const awardSelect = getAt(selects, 1, "award select");
    fireEvent.change(countrySelect, { target: { value: "USA" } });
    expect(pushMock).toHaveBeenCalled();
    fireEvent.change(countrySelect, { target: { value: "" } });
    expect(pushMock).toHaveBeenCalled();

    fireEvent.change(awardSelect, { target: { value: "Oscar" } });
    expect(pushMock).toHaveBeenCalled();

    fireEvent.click(screen.getByText("Limpiar filtros"));
    expect(pushMock).toHaveBeenCalled();

    screen.getAllByText("x").forEach((btn) => fireEvent.click(btn));
    expect(pushMock).toHaveBeenCalled();
  });

  it("handles filters API error", async () => {
    getComposerFiltersMock.mockRejectedValue(new Error("fail"));
    render(<FilterPanel />);
    await waitFor(() => {
      expect(getComposerFiltersMock).toHaveBeenCalled();
    });
  });

  it("avoids state updates after unmount", async () => {
    let resolveFilters: (value: unknown) => void = () => undefined;
    getComposerFiltersMock.mockReturnValue(
      new Promise((resolve) => {
        resolveFilters = resolve;
      })
    );

    const { unmount } = render(<FilterPanel />);
    unmount();

    resolveFilters({ countries: ["ES"], award_types: ["Goya"] });
    await Promise.resolve();
  });

  it("ignores rejected fetch after unmount", async () => {
    let rejectFilters: (reason?: unknown) => void = () => undefined;
    getComposerFiltersMock.mockReturnValue(
      new Promise((_, reject) => {
        rejectFilters = reject;
      })
    );

    const { unmount } = render(<FilterPanel />);
    unmount();

    rejectFilters(new Error("fail"));
    await Promise.resolve();
  });

  it("renders hasAwards false state", async () => {
    getComposerFiltersMock.mockResolvedValue({ countries: [], award_types: [] });
    render(<FilterPanel hasAwards={false} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Sin premios" })).toBeInTheDocument();
    });
    screen.getAllByText("x").forEach((btn) => fireEvent.click(btn));
  });

  it("handles missing filter arrays", async () => {
    getComposerFiltersMock.mockResolvedValue({});
    render(<FilterPanel />);
    await waitFor(() => {
      expect(getComposerFiltersMock).toHaveBeenCalled();
    });
    const selects = screen.getAllByRole("combobox");
    expect(selects.length).toBeGreaterThan(0);
  });
});
