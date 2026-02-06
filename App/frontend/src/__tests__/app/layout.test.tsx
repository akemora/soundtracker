import React from "react";
import { render, screen } from "@testing-library/react";

const notFoundMock = jest.fn(() => {
  throw new Error("not-found");
});

jest.mock("next/font/google", () => ({
  Inter: () => ({ variable: "inter" }),
  Playfair_Display: () => ({ variable: "playfair" }),
}));

jest.mock("next-intl/server", () => ({
  getMessages: async () => ({}),
  setRequestLocale: jest.fn(),
}));

jest.mock("next/navigation", () => ({
  notFound: () => notFoundMock(),
}));

jest.mock("@/components/layout/Header", () => ({
  Header: () => <div>Header</div>,
}));

jest.mock("@/components/layout/Footer", () => ({
  Footer: () => <div>Footer</div>,
}));

jest.mock("@/components/ThemeProvider", () => ({
  ThemeProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import LocaleLayout, { generateStaticParams, metadata } from "@/app/[locale]/layout";

describe("LocaleLayout", () => {
  it("generates static params", () => {
    const params = generateStaticParams();
    expect(params).toEqual([{ locale: "es" }, { locale: "en" }]);
  });

  it("exports metadata defaults", () => {
    expect(metadata.title).toBe("SOUNDTRACKER - Film Composers Encyclopedia");
  });

  it("renders layout for valid locale", async () => {
    const element = await LocaleLayout({
      params: Promise.resolve({ locale: "es" }),
      children: <div>Child</div>,
    });
    render(element);
    expect(screen.getByText("Child")).toBeInTheDocument();
  });

  it("calls notFound for invalid locale", async () => {
    await expect(
      LocaleLayout({ params: Promise.resolve({ locale: "fr" }), children: <div /> })
    ).rejects.toThrow("not-found");
  });
});
