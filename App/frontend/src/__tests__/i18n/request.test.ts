jest.unmock("@/i18n/routing");

jest.mock("next-intl/routing", () => ({
  defineRouting: (config: unknown) => config,
}));

jest.mock("next-intl/navigation", () => ({
  createNavigation: () => ({
    Link: () => null,
    redirect: jest.fn(),
    usePathname: jest.fn(),
    useRouter: jest.fn(),
    getPathname: jest.fn(),
  }),
}));

jest.mock("next-intl/server", () => ({
  getRequestConfig: (fn: unknown) => fn,
}));

import requestConfig from "@/i18n/request";

describe("i18n request", () => {
  it("uses provided locale", async () => {
    const result = await requestConfig({ requestLocale: Promise.resolve("es") });
    expect(result.locale).toBe("es");
    expect(result.messages).toBeDefined();
  });

  it("falls back to default locale", async () => {
    const result = await requestConfig({ requestLocale: Promise.resolve("fr") });
    expect(result.locale).toBe("es");
  });
});
