import React from "react";

describe("i18n routing (actual module)", () => {
  it("loads routing config and exports", async () => {
    jest.resetModules();
    jest.unmock("@/i18n/routing");
    const createNavigation = jest.fn(() => ({
      Link: ({ children, href }: { children: React.ReactNode; href: string }) => (
        <a href={href}>{children}</a>
      ),
      redirect: jest.fn(),
      usePathname: jest.fn(() => "/"),
      useRouter: jest.fn(() => ({ push: jest.fn() })),
      getPathname: jest.fn((path: string) => path),
    }));

    jest.doMock("next-intl/routing", () => ({
      defineRouting: (config: unknown) => config,
    }));

    jest.doMock("next-intl/navigation", () => ({
      createNavigation,
    }));

    await jest.isolateModulesAsync(async () => {
      const routingModule = await import("@/i18n/routing");
      expect(routingModule.routing.locales).toEqual(["es", "en"]);
      const element = <routingModule.Link href="/test">Test</routingModule.Link>;
      expect(element.props.href).toBe("/test");
      routingModule.redirect("/test");
      routingModule.usePathname();
      routingModule.useRouter();
      routingModule.getPathname("/test");
    });

    expect(createNavigation).toHaveBeenCalled();
  });
});
