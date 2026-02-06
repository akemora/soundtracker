import { render, screen } from "@testing-library/react";
import { Footer } from "@/components/layout/Footer";

describe("Footer", () => {
  it("renders footer content", () => {
    render(<Footer />);
    expect(screen.getByText(/SOUNDTRACKER/)).toBeInTheDocument();
    const year = new Date().getFullYear();
    expect(screen.getByText(new RegExp(String(year)))).toBeInTheDocument();
  });
});
