import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import Home from "./page";

describe("Home", () => {
  it("見出しに「メモアプリ」が表示される", () => {
    render(<Home />);
    expect(screen.getByRole("heading", { name: "メモアプリ" })).toBeInTheDocument();
  });
});
