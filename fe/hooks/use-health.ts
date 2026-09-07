"use client"

import * as React from "react"

import { getHealth, type Health } from "@/lib/api"

export function useHealth(intervalMs = 10000) {
  const [health, setHealth] = React.useState<Health | null>(null)
  const [error, setError] = React.useState<string | null>(null)

  const refresh = React.useCallback(async () => {
    try {
      const next = await getHealth()
      setHealth(next)
      setError(null)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Backend unreachable")
    }
  }, [])

  React.useEffect(() => {
    void refresh()
    const timer = window.setInterval(() => {
      void refresh()
    }, intervalMs)
    return () => window.clearInterval(timer)
  }, [intervalMs, refresh])

  return { health, error, refresh }
}
