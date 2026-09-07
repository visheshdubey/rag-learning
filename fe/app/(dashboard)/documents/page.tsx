import { DocumentsPanel } from "@/components/documents-panel"

export default function DocumentsPage() {
  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-4 pb-8">
      <div className="flex flex-col gap-1">
        <h1 className="font-heading text-2xl font-medium tracking-tight">
          Documents
        </h1>
        <p className="text-sm text-muted-foreground">
          Ingest files into the index and remove sources you no longer need.
        </p>
      </div>
      <DocumentsPanel />
    </div>
  )
}
