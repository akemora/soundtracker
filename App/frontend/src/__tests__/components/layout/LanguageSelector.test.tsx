import { fireEvent, render, screen } from "@testing-library/react";
import { LanguageSelector } from "@/components/layout/LanguageSelector";

const replaceMock = jest.fn();
let localeValue = "es";

jest.mock("next-intl", () => ({
  useLocale: () => localeValue,
}));

jest.mock("@/i18n/routing", () => ({
  useRouter: () => ({ replace: replaceMock }),
  usePathname: () => "/",
}));

describe("LanguageSelector", () => {
  it("toggles locale", () => {
    render(<LanguageSelector />);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("title", "Switch to English");
    fireEvent.click(button);
    expect(replaceMock).toHaveBeenCalledWith("/", { locale: "en" });
  });

  it("toggles from English to Spanish", () => {
    localeValue = "en";
    render(<LanguageSelector />);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("title", "Switch to Español");
    fireEvent.click(button);
    expect(replaceMock).toHaveBeenCalledWith("/", { locale: "es" });
    localeValue = "es";
  });
});
