import { AppSidebar } from "@/components/app-sidebar"
import { HealthBadges } from "@/components/health-badges"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="min-h-0 overflow-hidden">
        <header className="flex h-14 shrink-0 items-center gap-3 border-b px-4">
          <SidebarTrigger />
          <Separator orientation="vertical" />
          <HealthBadges />
        </header>
        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto p-6">
          {children}
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
