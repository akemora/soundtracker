import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SearchBar } from "@/components/search/SearchBar";

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
  Link: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
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
});
