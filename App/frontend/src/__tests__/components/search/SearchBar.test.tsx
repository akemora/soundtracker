import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SearchBar, LoadingSpinner } from "@/components/search/SearchBar";
import type { SearchResponse } from "@/lib/types";

// Mock the API module
jest.mock("@/lib/api", () => ({
  search: jest.fn(),
  getAssetUrl: (type: string, filename: string) =>
    `http://localhost:8000/api/assets/${type}/${filename}`,
}));

// Import the mocked module
import { search } from "@/lib/api";
const mockedSearch = search as jest.MockedFunction<typeof search>;

// Mock the router
const mockPush = jest.fn();
jest.mock("@/i18n/routing", () => ({
  Link: ({
    children,
    href,
    onClick,
    ...rest
  }: {
    children: React.ReactNode;
    href: string;
    onClick?: (event: React.MouseEvent<HTMLAnchorElement>) => void;
  }) => (
    <a
      href={href}
      onClick={(event) => {
        event.preventDefault();
        onClick?.(event);
      }}
      {...rest}
    >
      {children}
    </a>
  ),
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
    back: jest.fn(),
  }),
  usePathname: () => "/",
}));

describe("SearchBar", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("renders search input", () => {
    render(<SearchBar />);
    expect(screen.getByRole("searchbox")).toBeInTheDocument();
  });

  it("renders with custom placeholder", () => {
    render(<SearchBar placeholder="Buscar compositores..." />);
    expect(
      screen.getByPlaceholderText("Buscar compositores...")
    ).toBeInTheDocument();
  });

  it("renders with default value", () => {
    render(<SearchBar defaultValue="Williams" />);
    expect(screen.getByDisplayValue("Williams")).toBeInTheDocument();
  });

  it("disables submit button when query is too short", () => {
    render(<SearchBar />);
    const button = screen.getByRole("button");
    expect(button).toBeDisabled();
  });

  it("enables submit button when query has at least 2 characters", () => {
    render(<SearchBar defaultValue="ab" />);
    const button = screen.getByRole("button");
    expect(button).not.toBeDisabled();
  });

  it("navigates to search page on form submit", async () => {
    render(<SearchBar defaultValue="Williams" />);

    const form = screen.getByRole("searchbox").closest("form");
    fireEvent.submit(form!);

    expect(mockPush).toHaveBeenCalledWith("/search?q=Williams");
  });

  it("trims whitespace from query before navigating", async () => {
    render(<SearchBar defaultValue="  Williams  " />);

    const form = screen.getByRole("searchbox").closest("form");
    fireEvent.submit(form!);

    expect(mockPush).toHaveBeenCalledWith("/search?q=Williams");
  });

  it("does not submit when query is less than 2 characters", () => {
    render(<SearchBar defaultValue="a" />);

    const form = screen.getByRole("searchbox").closest("form");
    fireEvent.submit(form!);

    expect(mockPush).not.toHaveBeenCalled();
  });

  it("renders LoadingSpinner without className", () => {
    const { container } = render(<LoadingSpinner />);
    expect(container.querySelector("svg")).toBeInTheDocument();
  });

  it("calls search API after typing (debounced)", async () => {
    jest.useRealTimers();

    mockedSearch.mockResolvedValue({
      query: "wil",
      results: [
        {
          id: 1,
          name: "John Williams",
          slug: "john_williams",
          country: "USA",
          birth_year: 1932,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 1,
        },
      ],
      count: 1,
    });

    render(<SearchBar />);

    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    // Wait for debounce and API call
    await waitFor(
      () => {
        expect(mockedSearch).toHaveBeenCalledWith("wil", 5);
      },
      { timeout: 1000 }
    );
  });

  it("does not search when query is too short", () => {
    render(<SearchBar />);

    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "a" } });

    // Should not trigger search for single character
    jest.advanceTimersByTime(500);
    expect(mockedSearch).not.toHaveBeenCalled();
  });

  it("does not call search when showAutocomplete is false", () => {
    render(<SearchBar showAutocomplete={false} />);

    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "williams" } });

    jest.advanceTimersByTime(500);
    expect(mockedSearch).not.toHaveBeenCalled();
  });

  it("renders suggestions and handles keyboard navigation", async () => {
    jest.useRealTimers();
    mockedSearch.mockResolvedValue({
      query: "wil",
      results: [
        {
          id: 1,
          name: "John Williams",
          slug: "john_williams",
          country: "USA",
          birth_year: 1932,
          death_year: null,
          photo_local: "photo.jpg",
          biography: null,
          rank: 1,
        },
        {
          id: 2,
          name: "Howard Shore",
          slug: "howard_shore",
          country: null,
          birth_year: null,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 2,
        },
      ],
      count: 2,
    });

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    await waitFor(() => {
      expect(screen.getByText("John Williams")).toBeInTheDocument();
    });
    expect(screen.getByRole("listbox")).toBeInTheDocument();

    fireEvent.keyDown(input, { key: "ArrowDown", code: "ArrowDown" });
    expect(screen.getAllByRole("option")[0]).toHaveAttribute("aria-selected", "true");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(mockPush).toHaveBeenCalledWith("/composers/john_williams");
  });

  it("wraps selection with ArrowUp", async () => {
    jest.useRealTimers();
    mockedSearch.mockResolvedValue({
      query: "wil",
      results: [
        {
          id: 1,
          name: "John Williams",
          slug: "john_williams",
          country: "USA",
          birth_year: 1932,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 1,
        },
        {
          id: 2,
          name: "Howard Shore",
          slug: "howard_shore",
          country: null,
          birth_year: null,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 2,
        },
      ],
      count: 2,
    });

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    await waitFor(() => {
      expect(screen.getByText("Howard Shore")).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: "ArrowUp", code: "ArrowUp" });
    expect(screen.getAllByRole("option")[1]).toHaveAttribute("aria-selected", "true");
  });

  it("moves selection up when possible", async () => {
    jest.useRealTimers();
    mockedSearch.mockResolvedValue({
      query: "wil",
      results: [
        {
          id: 1,
          name: "John Williams",
          slug: "john_williams",
          country: "USA",
          birth_year: 1932,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 1,
        },
        {
          id: 2,
          name: "Howard Shore",
          slug: "howard_shore",
          country: null,
          birth_year: null,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 2,
        },
      ],
      count: 2,
    });

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    await waitFor(() => {
      expect(screen.getByText("Howard Shore")).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: "ArrowDown", code: "ArrowDown" });
    fireEvent.keyDown(input, { key: "ArrowDown", code: "ArrowDown" });
    fireEvent.keyDown(input, { key: "ArrowUp", code: "ArrowUp" });
    expect(screen.getAllByRole("option")[0]).toHaveAttribute("aria-selected", "true");
  });

  it("closes suggestions on escape and outside click", async () => {
    jest.useRealTimers();
    mockedSearch.mockResolvedValue({
      query: "wil",
      results: [
        {
          id: 1,
          name: "John Williams",
          slug: "john_williams",
          country: "USA",
          birth_year: 1932,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 1,
        },
      ],
      count: 1,
    });

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    await waitFor(() => {
      expect(screen.getByText("John Williams")).toBeInTheDocument();
    });
    expect(screen.getByRole("listbox")).toBeInTheDocument();

    fireEvent.keyDown(input, { key: "Escape" });
    expect(screen.queryByText("John Williams")).not.toBeInTheDocument();

    fireEvent.change(input, { target: { value: "will" } });
    await waitFor(() => {
      expect(screen.getByText("John Williams")).toBeInTheDocument();
    });
    fireEvent.mouseDown(document.body);
    expect(screen.queryByText("John Williams")).not.toBeInTheDocument();
  });

  it("handles view all results and suggestion click", async () => {
    jest.useRealTimers();
    mockedSearch.mockResolvedValue({
      query: "wil",
      results: [
        {
          id: 1,
          name: "John Williams",
          slug: "john_williams",
          country: "USA",
          birth_year: 1932,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 1,
        },
      ],
      count: 1,
    });

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    await waitFor(() => {
      expect(screen.getByText("John Williams")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("John Williams"));
    expect((input as HTMLInputElement).value).toBe("");

    fireEvent.change(input, { target: { value: "wil" } });
    await waitFor(() => {
      expect(screen.getByText("Ver todos los resultados")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Ver todos los resultados"));
    expect(mockPush).toHaveBeenCalledWith("/search?q=wil");
  });

  it("shows loading spinner during search and opens on focus", async () => {
    let resolveSearch: (value: SearchResponse) => void = () => undefined;
    mockedSearch.mockReturnValue(
      new Promise<SearchResponse>((resolve) => {
        resolveSearch = resolve;
      })
    );

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });
    jest.advanceTimersByTime(300);

    const spinner = document.querySelector("svg.animate-spin");
    expect(spinner).toBeInTheDocument();
    expect(spinner?.getAttribute("class")).toContain("animate-spin");

    resolveSearch({ query: "wil", results: [], count: 0 });
    await waitFor(() => {
      expect(mockedSearch).toHaveBeenCalled();
    });

    fireEvent.focus(input);
  });

  it("opens suggestions on focus when results exist", async () => {
    jest.useRealTimers();
    mockedSearch.mockResolvedValue({
      query: "wil",
      results: [
        {
          id: 1,
          name: "John Williams",
          slug: "john_williams",
          country: "USA",
          birth_year: 1932,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 1,
        },
      ],
      count: 1,
    });

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    await waitFor(() => {
      expect(screen.getByText("John Williams")).toBeInTheDocument();
    });

    fireEvent.blur(input);
    fireEvent.focus(input);
    expect(screen.getByRole("listbox")).toBeInTheDocument();
  });

  it("clears debounce timer on rapid input changes", () => {
    const clearSpy = jest.spyOn(global, "clearTimeout");
    render(<SearchBar />);
    const input = screen.getByRole("searchbox");

    fireEvent.change(input, { target: { value: "wil" } });
    fireEvent.change(input, { target: { value: "will" } });
    expect(clearSpy).toHaveBeenCalled();
    clearSpy.mockRestore();
  });

  it("handles search errors by clearing suggestions", async () => {
    jest.useRealTimers();
    mockedSearch.mockRejectedValue(new Error("fail"));
    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    await waitFor(() => {
      expect(mockedSearch).toHaveBeenCalled();
    });
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("ignores key navigation when dropdown is closed", () => {
    render(<SearchBar defaultValue="wil" />);
    const input = screen.getByRole("searchbox");
    fireEvent.keyDown(input, { key: "ArrowDown" });
    fireEvent.keyDown(input, { key: "Enter" });
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("renders death year in suggestions", async () => {
    jest.useRealTimers();
    mockedSearch.mockResolvedValue({
      query: "enn",
      results: [
        {
          id: 1,
          name: "Ennio Morricone",
          slug: "ennio_morricone",
          country: "Italy",
          birth_year: 1928,
          death_year: 2020,
          photo_local: null,
          biography: null,
          rank: 1,
        },
      ],
      count: 1,
    });

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "enn" } });

    await waitFor(() => {
      expect(screen.getByText("1928-2020")).toBeInTheDocument();
      expect(screen.getByText("Italy")).toBeInTheDocument();
    });
  });

  it("clears pending debounce on unmount", () => {
    const clearSpy = jest.spyOn(global, "clearTimeout");
    const { unmount } = render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });
    jest.advanceTimersByTime(1);
    unmount();
    expect(clearSpy).toHaveBeenCalled();
    clearSpy.mockRestore();
  });

  it("does not clear debounce when none is scheduled", () => {
    const clearSpy = jest.spyOn(global, "clearTimeout");
    const { unmount } = render(<SearchBar />);
    unmount();
    expect(clearSpy).not.toHaveBeenCalled();
    clearSpy.mockRestore();
  });


  it("ignores outside click when target is inside container", async () => {
    jest.useRealTimers();
    mockedSearch.mockResolvedValue({
      query: "wil",
      results: [
        {
          id: 1,
          name: "John Williams",
          slug: "john_williams",
          country: "USA",
          birth_year: 1932,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 1,
        },
      ],
      count: 1,
    });

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });

    fireEvent.mouseDown(input);
    expect(screen.getByRole("listbox")).toBeInTheDocument();
  });

  it("does not navigate on Enter when nothing is selected", async () => {
    jest.useRealTimers();
    mockedSearch.mockResolvedValue({
      query: "wil",
      results: [
        {
          id: 1,
          name: "John Williams",
          slug: "john_williams",
          country: "USA",
          birth_year: 1932,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 1,
        },
      ],
      count: 1,
    });

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    await waitFor(() => {
      expect(screen.getByRole("listbox")).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: "Enter", code: "Enter" });
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("wraps selection with ArrowDown", async () => {
    jest.useRealTimers();
    mockedSearch.mockResolvedValue({
      query: "wil",
      results: [
        {
          id: 1,
          name: "John Williams",
          slug: "john_williams",
          country: "USA",
          birth_year: 1932,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 1,
        },
        {
          id: 2,
          name: "Howard Shore",
          slug: "howard_shore",
          country: null,
          birth_year: null,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 2,
        },
      ],
      count: 2,
    });

    render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    await waitFor(() => {
      expect(screen.getByText("Howard Shore")).toBeInTheDocument();
    });

    fireEvent.keyDown(input, { key: "ArrowDown", code: "ArrowDown" });
    fireEvent.keyDown(input, { key: "ArrowDown", code: "ArrowDown" });
    fireEvent.keyDown(input, { key: "ArrowDown", code: "ArrowDown" });
    await waitFor(() => {
      expect(screen.getAllByRole("option")[0]).toHaveAttribute("aria-selected", "true");
    });
  });

  it("cleans up outside click listener on unmount", async () => {
    jest.useRealTimers();
    mockedSearch.mockResolvedValue({
      query: "wil",
      results: [
        {
          id: 1,
          name: "John Williams",
          slug: "john_williams",
          country: "USA",
          birth_year: 1932,
          death_year: null,
          photo_local: null,
          biography: null,
          rank: 1,
        },
      ],
      count: 1,
    });

    const removeSpy = jest.spyOn(document, "removeEventListener");
    const { unmount } = render(<SearchBar />);
    const input = screen.getByRole("searchbox");
    fireEvent.change(input, { target: { value: "wil" } });

    await waitFor(() => {
      expect(screen.getByText("John Williams")).toBeInTheDocument();
    });

    fireEvent.mouseDown(document.body);
    unmount();
    expect(removeSpy).toHaveBeenCalledWith("mousedown", expect.any(Function));
    removeSpy.mockRestore();
  });
});
