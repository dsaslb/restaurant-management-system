"use client"

import * as React from "react"
import { Moon, Sun } from "lucide-react"

export function ThemeToggle() {
  const [theme, setTheme] = React.useState<"light" | "dark">(() => {
    if (typeof window !== "undefined") {
      return window.localStorage.getItem("theme") === "dark" ? "dark" : "light"
    }
    return "light"
  })

  React.useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark")
      window.localStorage.setItem("theme", "dark")
    } else {
      document.documentElement.classList.remove("dark")
      window.localStorage.setItem("theme", "light")
    }
  }, [theme])

  return (
    <button
      type="button"
      aria-label="테마 토글"
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="inline-flex items-center justify-center rounded-md p-2 transition-colors hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring"
    >
      {theme === "dark" ? (
        <Sun className="h-5 w-5 text-yellow-400" />
      ) : (
        <Moon className="h-5 w-5 text-gray-800" />
      )}
    </button>
  )
} 