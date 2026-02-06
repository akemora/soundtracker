import { render, screen, waitFor } from "@testing-library/react";
import { AwardsList } from "@/components/composers/AwardsList";

const getAwardsMock = jest.fn();
jest.mock("@/lib/api", () => ({
  getAwards: () => getAwardsMock(),
}));

describe("AwardsList", () => {
  beforeEach(() => {
    getAwardsMock.mockReset();
  });

  it("renders awards data", async () => {
    getAwardsMock.mockResolvedValue({
      composer_id: 1,
      composer_name: "Composer",
      awards: [
        { id: 1, composer_id: 1, award_name: "Oscar", category: "Best", year: 1999, film_title: "Film", status: "win" },
        { id: 2, composer_id: 1, award_name: "Oscar", category: "Best", year: 2000, film_title: "Film 2", status: "nomination" },
      ],
      summary: { total: 1, wins: 1, nominations: 0 },
    });
    render(<AwardsList slug="composer" />);
    await waitFor(() => {
      expect(screen.getByText("Oscar")).toBeInTheDocument();
      expect(screen.getByText("★ Win")).toBeInTheDocument();
    });
  });

  it("handles error state", async () => {
    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => undefined);
    getAwardsMock.mockRejectedValue(new Error("fail"));
    render(<AwardsList slug="composer" />);
    await waitFor(() => {
      expect(screen.getByText("Error loading awards")).toBeInTheDocument();
    });
    errorSpy.mockRestore();
  });

  it("shows fallback when no data", async () => {
    getAwardsMock.mockResolvedValue(null);
    render(<AwardsList slug="composer" />);
    await waitFor(() => {
      expect(screen.getByText("No awards found")).toBeInTheDocument();
    });
  });

  it("sorts awards by year descending", async () => {
    const sortSpy = jest.spyOn(Array.prototype, "sort");
    getAwardsMock.mockResolvedValue({
      composer_id: 1,
      composer_name: "Composer",
      awards: [
        { id: 1, composer_id: 1, award_name: "Oscar", category: "Best", year: 1999, film_title: "Film", status: "win" },
        { id: 2, composer_id: 1, award_name: "Oscar", category: "Best", year: 2000, film_title: "Film 2", status: "nomination" },
      ],
      summary: { total: 2, wins: 1, nominations: 1 },
    });
    render(<AwardsList slug="composer" />);
    await waitFor(() => {
      const year2000 = screen.getAllByText("2000")[0];
      const year1999 = screen.getAllByText("1999")[0];
      expect(
        year2000.compareDocumentPosition(year1999) & Node.DOCUMENT_POSITION_FOLLOWING
      ).toBeTruthy();
    });
    expect(sortSpy).toHaveBeenCalled();
    sortSpy.mockRestore();
  });

  it("handles awards without year", async () => {
    getAwardsMock.mockResolvedValue({
      composer_id: 1,
      composer_name: "Composer",
      awards: [
        { id: 1, composer_id: 1, award_name: "Oscar", category: "Best", year: null, film_title: "Film", status: "win" },
        { id: 2, composer_id: 1, award_name: "Oscar", category: "Best", year: 2020, film_title: "Film 2", status: "nomination" },
      ],
      summary: { total: 2, wins: 1, nominations: 1 },
    });
    render(<AwardsList slug="composer" />);
    await waitFor(() => {
      expect(screen.getByText("2020")).toBeInTheDocument();
      expect(screen.getByText("Oscar")).toBeInTheDocument();
    });
  });

  it("sorts awards when years are null", async () => {
    getAwardsMock.mockResolvedValue({
      composer_id: 1,
      composer_name: "Composer",
      awards: [
        { id: 1, composer_id: 1, award_name: "Oscar", category: "Best", year: null, film_title: "Film", status: "win" },
        { id: 2, composer_id: 1, award_name: "Oscar", category: "Best", year: null, film_title: "Film 2", status: "nomination" },
      ],
      summary: { total: 2, wins: 1, nominations: 1 },
    });
    render(<AwardsList slug="composer" />);
    await waitFor(() => {
      expect(screen.getByText("Oscar")).toBeInTheDocument();
    });
  });
});
