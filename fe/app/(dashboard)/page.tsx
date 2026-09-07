import { AskPanel } from "@/components/ask-panel"

export default function AskPage() {
  return (
    <div className="mx-auto flex min-h-0 w-full max-w-4xl flex-1 flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h1 className="font-heading text-2xl font-medium tracking-tight">Ask</h1>
        <p className="text-sm text-muted-foreground">
          Retrieve matching chunks and answer with your local model.
        </p>
      </div>
      <AskPanel />
    </div>
  )
}
