import React from "react";

describe("i18n routing", () => {
  it("exports routing config", async () => {
    jest.resetModules();
    jest.unmock("@/i18n/routing");
    jest.doMock("next-intl/routing", () => ({
      defineRouting: (config: unknown) => config,
    }));
    jest.doMock("next-intl/navigation", () => ({
      createNavigation: () => ({
        Link: ({ children, href }: { children: React.ReactNode; href: string }) => (
          <a href={href}>{children}</a>
        ),
        redirect: jest.fn(),
        usePathname: jest.fn(),
        useRouter: jest.fn(),
        getPathname: jest.fn(),
      }),
    }));

    await jest.isolateModulesAsync(async () => {
      const actual = await import("@/i18n/routing");
      expect(actual.routing.locales).toEqual(["es", "en"]);
      expect(actual.routing.defaultLocale).toBe("es");
    });
  });

  it("exports Link component", async () => {
    jest.resetModules();
    jest.unmock("@/i18n/routing");
    jest.doMock("next-intl/routing", () => ({
      defineRouting: (config: unknown) => config,
    }));
    jest.doMock("next-intl/navigation", () => ({
      createNavigation: () => ({
        Link: ({ children, href }: { children: React.ReactNode; href: string }) => (
          <a href={href}>{children}</a>
        ),
        redirect: jest.fn(),
        usePathname: jest.fn(),
        useRouter: jest.fn(),
        getPathname: jest.fn(),
      }),
    }));

    await jest.isolateModulesAsync(async () => {
      const actual = await import("@/i18n/routing");
      const element = <actual.Link href="/test">Test</actual.Link>;
      expect(element.props.href).toBe("/test");
    });
  });

  it("creates navigation helpers", async () => {
    jest.resetModules();
    jest.unmock("@/i18n/routing");
    const createNavigationMock = jest.fn(() => ({
      Link: ({ children, href }: { children: React.ReactNode; href: string }) => (
        <a href={href}>{children}</a>
      ),
      redirect: jest.fn(),
      usePathname: jest.fn(),
      useRouter: jest.fn(),
      getPathname: jest.fn(),
    }));
    jest.doMock("next-intl/routing", () => ({
      defineRouting: (config: unknown) => config,
    }));
    jest.doMock("next-intl/navigation", () => ({
      createNavigation: createNavigationMock,
    }));

    await jest.isolateModulesAsync(async () => {
      const actual = await import("@/i18n/routing");
      expect(actual.getPathname).toBeDefined();
    });
  });
});
