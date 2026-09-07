"use client"

import * as React from "react"
import { FilesIcon, TrashIcon, UploadSimpleIcon } from "@phosphor-icons/react"
import { toast } from "sonner"

import {
  deleteDocument,
  getDocuments,
  ingestFiles,
  type DocumentSource,
} from "@/lib/api"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Spinner } from "@/components/ui/spinner"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export function DocumentsPanel() {
  const inputRef = React.useRef<HTMLInputElement>(null)
  const [loading, setLoading] = React.useState(true)
  const [uploading, setUploading] = React.useState(false)
  const [sources, setSources] = React.useState<DocumentSource[]>([])
  const [types, setTypes] = React.useState<string[]>([])
  const [chunks, setChunks] = React.useState(0)
  const [pendingDelete, setPendingDelete] = React.useState<string | null>(null)
  const [deleting, setDeleting] = React.useState(false)

  const refresh = React.useCallback(async () => {
    const stats = await getDocuments()
    setSources(stats.sources)
    setTypes(stats.supported_types)
    setChunks(stats.chunks)
  }, [])

  React.useEffect(() => {
    refresh()
      .catch((cause) => {
        toast.error(cause instanceof Error ? cause.message : "Could not load documents")
      })
      .finally(() => setLoading(false))
  }, [refresh])

  async function onFiles(fileList: FileList | null) {
    if (!fileList?.length) {
      return
    }
    setUploading(true)
    try {
      const ingested = await ingestFiles(Array.from(fileList))
      const count = ingested.reduce((sum, item) => sum + item.chunks, 0)
      toast.success(
        `Indexed ${ingested.length} file${ingested.length === 1 ? "" : "s"} into ${count} chunks`
      )
      await refresh()
    } catch (cause) {
      toast.error(cause instanceof Error ? cause.message : "Ingest failed")
    } finally {
      setUploading(false)
      if (inputRef.current) {
        inputRef.current.value = ""
      }
    }
  }

  async function onConfirmDelete() {
    if (!pendingDelete) {
      return
    }
    setDeleting(true)
    try {
      const result = await deleteDocument(pendingDelete)
      toast.success(`Removed ${result.deleted_chunks} chunks from ${result.source}`)
      setPendingDelete(null)
      await refresh()
    } catch (cause) {
      toast.error(cause instanceof Error ? cause.message : "Delete failed")
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Upload</CardTitle>
          <CardDescription>
            Files are chunked, embedded with Ollama, and stored in Chroma.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="document-upload">Documents</FieldLabel>
              <input
                id="document-upload"
                ref={inputRef}
                type="file"
                className="hidden"
                multiple
                accept={types.join(",")}
                onChange={(event) => void onFiles(event.target.files)}
              />
              <Button
                type="button"
                variant="outline"
                disabled={uploading}
                onClick={() => inputRef.current?.click()}
              >
                {uploading ? (
                  <Spinner data-icon="inline-start" />
                ) : (
                  <UploadSimpleIcon data-icon="inline-start" />
                )}
                {uploading ? "Indexing…" : "Choose files"}
              </Button>
              <FieldDescription>
                {types.length > 0
                  ? `Supported: ${types.join(", ")}`
                  : "Loading supported types…"}
              </FieldDescription>
            </Field>
          </FieldGroup>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Indexed sources</CardTitle>
          <CardDescription>
            {chunks} chunk{chunks === 1 ? "" : "s"} across {sources.length} file
            {sources.length === 1 ? "" : "s"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Spinner />
              Loading index
            </div>
          ) : sources.length === 0 ? (
            <Empty className="border">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <FilesIcon />
                </EmptyMedia>
                <EmptyTitle>No documents yet</EmptyTitle>
                <EmptyDescription>
                  Upload a handbook, PDF, or notes to start asking questions.
                </EmptyDescription>
              </EmptyHeader>
              <EmptyContent>
                <Button
                  variant="outline"
                  onClick={() => inputRef.current?.click()}
                >
                  <UploadSimpleIcon data-icon="inline-start" />
                  Upload a file
                </Button>
              </EmptyContent>
            </Empty>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>File</TableHead>
                  <TableHead>Chunks</TableHead>
                  <TableHead className="w-16">
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sources.map((item) => (
                  <TableRow key={item.source}>
                    <TableCell className="font-medium">{item.source}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{item.chunks}</Badge>
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`Delete ${item.source}`}
                        onClick={() => setPendingDelete(item.source)}
                      >
                        <TrashIcon />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <AlertDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => {
          if (!open && !deleting) {
            setPendingDelete(null)
          }
        }}
      >
        <AlertDialogContent size="sm">
          <AlertDialogHeader>
            <AlertDialogMedia className="bg-destructive/10 text-destructive">
              <TrashIcon />
            </AlertDialogMedia>
            <AlertDialogTitle>Remove this file?</AlertDialogTitle>
            <AlertDialogDescription>
              This deletes every indexed chunk for {pendingDelete}. You can
              upload it again later.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={deleting}
              onClick={() => void onConfirmDelete()}
            >
              {deleting ? <Spinner data-icon="inline-start" /> : null}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
