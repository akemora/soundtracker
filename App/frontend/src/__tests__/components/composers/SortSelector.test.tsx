import { fireEvent, render, screen } from "@testing-library/react";
import { SortSelector } from "@/components/composers/SortSelector";

const pushMock = jest.fn();

jest.mock("@/i18n/routing", () => ({
  useRouter: () => ({ push: pushMock }),
  usePathname: () => "/composers",
}));

describe("SortSelector", () => {
  beforeEach(() => {
    pushMock.mockReset();
  });

  it("pushes sort changes", () => {
    render(<SortSelector currentSort="name" currentOrder="asc" />);
    fireEvent.click(screen.getByText("sortFilms"));
    expect(pushMock).toHaveBeenCalledWith("/composers?sort=film_count&order=asc");
  });

  it("toggles order when clicking current sort", () => {
    render(<SortSelector currentSort="name" currentOrder="asc" />);
    fireEvent.click(screen.getByText("sortName"));
    expect(pushMock).toHaveBeenCalledWith("/composers?sort=name&order=desc");
    expect(screen.getByText("↑")).toBeInTheDocument();
  });

  it("shows descending arrow when order is desc", () => {
    render(<SortSelector currentSort="wins" currentOrder="desc" />);
    expect(screen.getByText("↓")).toBeInTheDocument();
  });
});
