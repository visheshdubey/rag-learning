"use client"

import * as React from "react"
import {
  ArrowUpIcon,
  ChatTeardropTextIcon,
  FileTextIcon,
} from "@phosphor-icons/react"
import { toast } from "sonner"

import { queryRag, type SourceHit } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "@/components/ui/input-group"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Spinner } from "@/components/ui/spinner"

type Message = {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: SourceHit[]
}

export function AskPanel() {
  const [question, setQuestion] = React.useState("")
  const [pending, setPending] = React.useState(false)
  const [messages, setMessages] = React.useState<Message[]>([])
  const bottomRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, pending])

  async function onAsk() {
    const trimmed = question.trim()
    if (!trimmed || pending) {
      return
    }

    setQuestion("")
    setPending(true)
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content: trimmed },
    ])

    try {
      const result = await queryRag(trimmed)
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: result.answer,
          sources: result.sources,
        },
      ])
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : "Query failed"
      toast.error(message)
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `I could not answer that. ${message}`,
        },
      ])
    } finally {
      setPending(false)
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4">
      <ScrollArea className="min-h-0 flex-1">
        {messages.length === 0 ? (
          <Empty className="h-full border">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <ChatTeardropTextIcon />
              </EmptyMedia>
              <EmptyTitle>Ask your documents</EmptyTitle>
              <EmptyDescription>
                Ingest files on the Documents page, then ask a question. Answers
                stay grounded in the indexed sources.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : (
          <div className="flex flex-col gap-4 p-1">
            {messages.map((message) => (
              <article
                key={message.id}
                className={
                  message.role === "user"
                    ? "ml-auto max-w-2xl rounded-3xl bg-primary px-4 py-3 text-primary-foreground"
                    : "mr-auto flex w-full max-w-3xl flex-col gap-3 rounded-3xl bg-muted px-4 py-3"
                }
              >
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {message.content}
                </p>
                {message.sources && message.sources.length > 0 ? (
                  <div className="flex flex-col gap-2">
                    <p className="text-xs font-medium text-muted-foreground">
                      Sources
                    </p>
                    {message.sources.map((hit, index) => (
                      <div
                        key={`${hit.source}-${index}`}
                        className="flex flex-col gap-1 rounded-2xl bg-background px-3 py-2"
                      >
                        <div className="flex items-center gap-2">
                          <FileTextIcon />
                          <span className="truncate text-xs font-medium">
                            {hit.source}
                          </span>
                          <Badge variant="outline">
                            {(hit.score * 100).toFixed(0)}%
                          </Badge>
                        </div>
                        <p className="line-clamp-3 text-xs text-muted-foreground">
                          {hit.text}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
            {pending ? (
              <div className="mr-auto flex items-center gap-2 rounded-3xl bg-muted px-4 py-3 text-sm text-muted-foreground">
                <Spinner />
                Retrieving context and generating an answer
              </div>
            ) : null}
            <div ref={bottomRef} />
          </div>
        )}
      </ScrollArea>

      <form
        className="shrink-0"
        onSubmit={(event) => {
          event.preventDefault()
          void onAsk()
        }}
      >
        <InputGroup className="h-auto min-h-16">
          <InputGroupTextarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault()
                void onAsk()
              }
            }}
            placeholder="Ask a question about your documents"
            disabled={pending}
            rows={2}
          />
          <InputGroupAddon align="inline-end">
            <InputGroupButton
              type="submit"
              variant="default"
              size="icon-sm"
              disabled={pending || !question.trim()}
              aria-label="Ask"
            >
              {pending ? <Spinner /> : <ArrowUpIcon />}
            </InputGroupButton>
          </InputGroupAddon>
        </InputGroup>
      </form>
    </div>
  )
}
