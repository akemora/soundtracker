jest.mock("next-intl/middleware", () => ({
  __esModule: true,
  default: jest.fn(() => "middleware"),
}));

import middleware, { config } from "@/middleware";

describe("middleware", () => {
  it("creates middleware with routing config", () => {
    const mocked = require("next-intl/middleware").default as jest.Mock;
    expect(mocked).toHaveBeenCalled();
    expect(middleware).toBe("middleware");
  });

  it("exports matcher config", () => {
    expect(config.matcher).toBeDefined();
    expect(config.matcher[0]).toContain("api");
  });
});
