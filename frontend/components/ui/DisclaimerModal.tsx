'use client'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { AlertTriangle } from 'lucide-react'

interface DisclaimerModalProps {
  open: boolean
  title: string
  content: string
  onAcknowledge: () => void
}

export function DisclaimerModal({
  open,
  title,
  content,
  onAcknowledge,
}: DisclaimerModalProps) {
  return (
    <Dialog open={open} onOpenChange={() => {}}>
      <DialogContent showCloseButton={false} className="sm:max-w-2xl">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
              <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
            </div>
            <DialogTitle className="text-xl">{title}</DialogTitle>
          </div>
        </DialogHeader>
        <DialogDescription className="max-h-[60vh] overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed">
          {content}
        </DialogDescription>
        <DialogFooter>
          <Button onClick={onAcknowledge} className="w-full sm:w-auto">
            I Acknowledge
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

