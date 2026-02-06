import { render, screen } from "@testing-library/react";

const getComposersMock = jest.fn();

jest.mock("next-intl/server", () => ({
  getTranslations: async () => (key: string) => key,
  setRequestLocale: jest.fn(),
}));

jest.mock("@/lib/api", () => ({
  getComposers: () => getComposersMock(),
}));

jest.mock("@/components/composers/ComposerGrid", () => ({
  ComposerGrid: () => <div>ComposerGrid</div>,
}));

jest.mock("@/components/search/HeroSearchForm", () => ({
  HeroSearchForm: () => <div>HeroSearchForm</div>,
}));

jest.mock("@/components/ui/button", () => ({
  Button: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import HomePage from "@/app/[locale]/page";

describe("HomePage", () => {
  beforeEach(() => {
    getComposersMock.mockReset();
    jest.spyOn(console, "warn").mockImplementation(() => undefined);
  });

  afterEach(() => {
    (console.warn as jest.Mock).mockRestore();
  });

  it("renders hero and featured composers", async () => {
    getComposersMock.mockResolvedValue({ composers: [{ id: 1 }], pagination: { page: 1, per_page: 8, total: 1, pages: 1 } });
    const element = await HomePage({ params: Promise.resolve({ locale: "es" }) });
    render(element);
    expect(screen.getByText("HeroSearchForm")).toBeInTheDocument();
    expect(screen.getByText("ComposerGrid")).toBeInTheDocument();
  });

  it("handles API failure", async () => {
    getComposersMock.mockRejectedValue(new Error("fail"));
    const element = await HomePage({ params: Promise.resolve({ locale: "es" }) });
    render(element);
    expect(screen.queryByText("ComposerGrid")).not.toBeInTheDocument();
  });
});
