import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { ThemeProvider } from "@/components/ThemeProvider";
import { ThemeToggle } from "@/components/ThemeToggle";

const setThemeMock = jest.fn();
let currentTheme = "dark";

jest.mock("next-themes", () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="theme-provider">{children}</div>
  ),
  useTheme: () => ({ theme: currentTheme, setTheme: setThemeMock }),
}));

describe("ThemeProvider", () => {
  it("renders children", () => {
    render(
      <ThemeProvider>
        <div>Child</div>
      </ThemeProvider>
    );
    expect(screen.getByText("Child")).toBeInTheDocument();
  });
});

describe("ThemeToggle", () => {
  it("renders placeholder before mount", () => {
    const useStateSpy = jest.spyOn(React, "useState");
    useStateSpy.mockImplementationOnce(() => [false, jest.fn()]);
    render(<ThemeToggle />);
    expect(screen.getByText("Toggle theme")).toBeInTheDocument();
    useStateSpy.mockRestore();
  });

  it("toggles theme on click", () => {
    currentTheme = "dark";
    render(<ThemeToggle />);
    const button = screen.getByRole("button");
    fireEvent.click(button);
    expect(setThemeMock).toHaveBeenCalledWith("light");
  });

  it("toggles from light to dark", () => {
    currentTheme = "light";
    render(<ThemeToggle />);
    const button = screen.getByRole("button");
    fireEvent.click(button);
    expect(setThemeMock).toHaveBeenCalledWith("dark");
  });
});
