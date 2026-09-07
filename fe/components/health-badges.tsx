"use client"

import { CircleIcon } from "@phosphor-icons/react"

import { useHealth } from "@/hooks/use-health"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"

export function HealthBadges() {
  const { health, error } = useHealth()

  if (error) {
    return (
      <Badge variant="destructive">
        <CircleIcon data-icon="inline-start" weight="fill" />
        API offline
      </Badge>
    )
  }

  if (!health) {
    return <Skeleton className="h-5 w-40" />
  }

  const online = health.status === "ok"
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant={online ? "secondary" : "destructive"}>
        <CircleIcon data-icon="inline-start" weight="fill" />
        {online ? "Ollama ready" : "Ollama degraded"}
      </Badge>
      <Badge variant="outline">{health.llm_model}</Badge>
      <Badge variant="outline">{health.indexed_chunks} chunks</Badge>
    </div>
  )
}
