'use client'

import { useState } from 'react'
import { useEmailTemplates, deleteEmailTemplate, type EmailTemplate } from '@/hooks/useReferrals'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader } from '@/components/ui/loader'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { CreateEmailTemplateForm } from './CreateEmailTemplateForm'
import { Edit, Trash2, Plus } from 'lucide-react'
import { useToast } from '@/hooks/useToast'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog'

interface EmailTemplateListProps {
  orgId: string
  isAdmin: boolean
}

export function EmailTemplateList({ orgId, isAdmin }: EmailTemplateListProps) {
  const { templates, isLoading, mutate } = useEmailTemplates(orgId)
  const { toast } = useToast()
  const { handleError } = useErrorHandler()
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<EmailTemplate | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const handleDelete = async (templateId: string) => {
    setIsDeleting(true)
    try {
      await deleteEmailTemplate(orgId, templateId)
      toast({
        title: 'Template deleted',
        description: 'The template has been removed.',
        variant: 'success',
      })
      mutate()
    } catch (err) {
      handleError(err, { title: 'Failed to delete template' })
    } finally {
      setIsDeleting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">Templates</h2>
          <p className="text-sm text-muted-foreground">
            Manage email templates for referrals and interventions
          </p>
        </div>
        {isAdmin && (
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Template
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Email Template</DialogTitle>
              </DialogHeader>
              <CreateEmailTemplateForm 
                orgId={orgId} 
                onSuccess={() => {
                  setIsCreateOpen(false)
                  mutate()
                }} 
              />
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="rounded-lg border-2 border-border/80 bg-background shadow-sm">
        <div className="rounded-md">
          <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Scope</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {templates.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center">
                  No templates found.
                </TableCell>
              </TableRow>
            ) : (
              templates.map((template) => (
                <TableRow key={template.id}>
                  <TableCell className="font-medium">
                    {template.name}
                    {template.scope === 'system' && (
                      <span className="ml-2 text-xs text-muted-foreground">(System)</span>
                    )}
                  </TableCell>
                  <TableCell className="capitalize">{template.type}</TableCell>
                  <TableCell className="capitalize">{template.scope}</TableCell>
                  <TableCell>
                    <Badge variant={template.is_active ? 'default' : 'secondary'} className={template.is_active ? 'bg-green-600 hover:bg-green-700' : ''}>
                      {template.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    {isAdmin && template.scope !== 'system' && (
                      <div className="flex justify-end gap-2">
                        <Dialog open={editingTemplate?.id === template.id} onOpenChange={(open) => !open && setEditingTemplate(null)}>
                          <DialogTrigger asChild>
                            <Button 
                              variant="ghost" 
                              size="icon"
                              onClick={() => setEditingTemplate(template)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
                            <DialogHeader>
                              <DialogTitle>Edit Email Template</DialogTitle>
                            </DialogHeader>
                            <CreateEmailTemplateForm 
                              orgId={orgId} 
                              initialData={template}
                              onSuccess={() => {
                                setEditingTemplate(null)
                                mutate()
                              }} 
                            />
                          </DialogContent>
                        </Dialog>

                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="ghost" size="icon" className="text-destructive">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete Template?</AlertDialogTitle>
                              <AlertDialogDescription>
                                This action cannot be undone. This will permanently delete the
                                template "{template.name}".
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction 
                                onClick={() => handleDelete(template.id)}
                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                              >
                                {isDeleting ? 'Deleting...' : 'Delete'}
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        </div>
      </div>
    </div>
  )
}

