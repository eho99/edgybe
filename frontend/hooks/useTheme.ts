"use client"

import { useEffect, useState, useCallback } from "react"

type Theme = "light" | "dark" | "system"

export function useTheme() {
  const [theme, setTheme] = useState<Theme>("system")
  const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">("light")
  const [mounted, setMounted] = useState(false)

  const updateTheme = useCallback((newTheme: Theme) => {
    const root = window.document.documentElement

    if (newTheme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
      root.classList.remove("light", "dark")
      root.classList.add(systemTheme)
      setResolvedTheme(systemTheme)
    } else {
      root.classList.remove("light", "dark")
      root.classList.add(newTheme)
      setResolvedTheme(newTheme)
    }

    localStorage.setItem("theme", newTheme)
  }, [])

  useEffect(() => {
    setMounted(true)
    // Get initial theme from localStorage or default to system
    const stored = localStorage.getItem("theme") as Theme | null
    const initialTheme = stored || "system"
    setTheme(initialTheme)
    updateTheme(initialTheme)
  }, [updateTheme])

  useEffect(() => {
    if (!mounted) return
    updateTheme(theme)
  }, [theme, mounted, updateTheme])

  const setThemeValue = useCallback((newTheme: Theme) => {
    setTheme(newTheme)
  }, [])

  // Listen for system theme changes
  useEffect(() => {
    if (!mounted || theme !== "system") return

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
    const handleChange = () => {
      updateTheme("system")
    }

    mediaQuery.addEventListener("change", handleChange)
    return () => mediaQuery.removeEventListener("change", handleChange)
  }, [mounted, theme, updateTheme])

  return {
    theme,
    setTheme: setThemeValue,
    resolvedTheme,
    mounted,
  }
}

