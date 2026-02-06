import { locales, defaultLocale, localeNames } from "@/i18n/config";

describe("i18n config", () => {
  it("defines locales", () => {
    expect(locales).toEqual(["es", "en"]);
    expect(defaultLocale).toBe("es");
    expect(localeNames.es).toBe("Español");
    expect(localeNames.en).toBe("English");
  });
});
