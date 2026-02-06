import React from "react";
import { render, screen } from "@testing-library/react";

jest.mock("next-intl/server", () => ({
  getTranslations: async () => (key: string) => key,
}));

jest.mock("@/components/ThemeToggle", () => ({
  ThemeToggle: () => <div>ThemeToggle</div>,
}));

jest.mock("@/components/layout/LanguageSelector", () => ({
  LanguageSelector: () => <div>LanguageSelector</div>,
}));

import { Header } from "@/components/layout/Header";

describe("Header", () => {
  it("renders navigation links", async () => {
    const element = await Header();
    render(element);
    expect(screen.getByText("home")).toBeInTheDocument();
    expect(screen.getAllByText("composers").length).toBeGreaterThan(0);
  });
});
