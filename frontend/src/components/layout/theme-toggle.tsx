"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const { setTheme } = useTheme();

  function toggle() {
    // Read the live class (set by next-themes before hydration) at click time —
    // avoids reading theme state during render (no hydration mismatch).
    const isDark = document.documentElement.classList.contains("dark");
    setTheme(isDark ? "light" : "dark");
  }

  return (
    <button
      type="button"
      aria-label="Toggle theme"
      onClick={toggle}
      className="flex size-9 items-center justify-center rounded-md text-muted-foreground hover:text-foreground"
    >
      {/* Both render identically on server & client; CSS shows the right one. */}
      <Sun className="hidden size-5 dark:block" />
      <Moon className="size-5 dark:hidden" />
    </button>
  );
}
