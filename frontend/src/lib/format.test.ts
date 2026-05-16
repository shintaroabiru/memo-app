import { describe, expect, it } from "vitest";

import { truncate } from "./format";

describe("truncate", () => {
  it("文字列が最大長以下の場合はそのまま返す", () => {
    expect(truncate("hello", 10)).toBe("hello");
  });

  it("文字列が最大長を超える場合は末尾を…で切り詰める", () => {
    expect(truncate("hello world", 5)).toBe("hello…");
  });

  it("最大長が0の場合は…のみを返す", () => {
    expect(truncate("hello", 0)).toBe("…");
  });
});
