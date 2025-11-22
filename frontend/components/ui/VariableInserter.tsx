'use client'

import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Plus } from "lucide-react"
import { useEmailVariables } from "@/hooks/useReferrals"
import { Loader } from "@/components/ui/loader"

interface VariableInserterProps {
  orgId: string
  onInsert: (value: string) => void
}

export function VariableInserter({ orgId, onInsert }: VariableInserterProps) {
  const { variables, isLoading } = useEmailVariables(orgId)

  if (isLoading) {
    return <div className="flex justify-center py-2"><Loader className="h-4 w-4" /></div>
  }

  return (
    <div className="space-y-2">
      <div className="text-xs font-medium text-muted-foreground">Insert Variables</div>
      <div className="flex flex-wrap gap-2">
        <TooltipProvider>
          {variables.map((variable) => (
            <Tooltip key={variable.value}>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 px-2 text-xs"
                  onClick={() => onInsert(variable.value)}
                >
                  <Plus className="mr-1 h-3 w-3" />
                  {variable.label}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{variable.description}</p>
                <p className="text-xs text-muted-foreground font-mono mt-1">{variable.value}</p>
              </TooltipContent>
            </Tooltip>
          ))}
        </TooltipProvider>
      </div>
    </div>
  )
}


