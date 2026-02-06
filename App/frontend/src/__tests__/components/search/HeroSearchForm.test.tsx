import { render, screen } from "@testing-library/react";
import { HeroSearchForm } from "@/components/search/HeroSearchForm";

describe("HeroSearchForm", () => {
  it("renders input and button", () => {
    render(<HeroSearchForm placeholder="Buscar..." buttonLabel="Buscar" />);
    expect(screen.getByPlaceholderText("Buscar...")).toBeInTheDocument();
    expect(screen.getByText("Buscar")).toBeInTheDocument();
  });
});
