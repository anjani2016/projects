'use client'

import { useState } from 'react'
import { X, ShieldCheck, MessageSquare, FileDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/primitives'
import { VerdictBadge } from '@/components/ui/badges'
import { AnnotatedImage } from '@/components/annotated-image'
import { DefectsTable } from '@/components/defects-table'
import { WorkflowSteps } from '@/components/workflow-steps'
import { useToast } from '@/components/toast'
import { submitFeedback } from '@/lib/api'
import { getRole, getApiUrl } from '@/lib/config'
import type { AuditEvent, InspectionRecord } from '@/lib/types'

export function RecordDetail({
  record,
  onClose,
  updateRecord,
  addAudit,
}: {
  record: InspectionRecord
  onClose: () => void
  updateRecord: (id: string, patch: Partial<InspectionRecord>) => void
  addAudit: (a: AuditEvent['action'], details: string) => void
}) {
  const { toast } = useToast()
  const [comment, setComment] = useState('')
  const role = getRole()
  const canApprove = role === 'Supervisor' || role === 'Admin'

  const handleApprove = async () => {
    if (!canApprove) {
      addAudit('UNAUTHORIZED', `${role} attempted to approve ${record.report_id}`)
      toast({
        variant: 'error',
        title: 'Unauthorized',
        description: 'Only Supervisors can approve records.',
      })
      return
    }
    try {
      await submitFeedback(record.report_id, comment || 'Approved', role)
    } catch {
      /* offline: still update locally */
    }
    updateRecord(record.report_id, {
      workflow: 'Supervisor Approved',
      supervisor_remarks: comment || 'Disposition confirmed. Record closed.',
    })
    addAudit('APPROVE_RECORD', `Supervisor approved ${record.report_id}`)
    toast({
      variant: 'success',
      title: 'Record approved',
      description: `${record.report_id} marked as Supervisor Approved.`,
    })
    setComment('')
  }

  return (
    <div className="fixed inset-0 z-40">
      <div
        className="absolute inset-0 bg-background/70 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <div className="absolute inset-y-0 right-0 flex w-full max-w-2xl flex-col border-l border-border bg-card shadow-2xl animate-fade-in-up">
        <div className="flex items-center justify-between border-b border-border p-5">
          <div className="flex items-center gap-3">
            <span className="font-mono text-sm font-semibold text-foreground">
              {record.report_id}
            </span>
            <VerdictBadge verdict={record.verdict} />
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                window.open(`${getApiUrl()}/static/reports/${record.report_id}.pdf`, '_blank')
                toast({
                  variant: 'success',
                  title: 'Opening Report',
                  description: `Downloading report ${record.report_id}.pdf`,
                })
              }}
            >
              <FileDown className="size-4 mr-1.5" />
              Download PDF
            </Button>
            <Button size="icon-sm" variant="ghost" onClick={onClose} aria-label="Close panel">
              <X />
            </Button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          <div className="mb-6 rounded-lg border border-border bg-secondary/30 p-4">
            <WorkflowSteps stage={record.workflow} />
          </div>

          <div className="mb-6 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
            <Meta label="Material" value={record.material} />
            <Meta label="Code" value={record.regulatory_code} />
            <Meta label="Model" value={record.model} />
            <Meta label="Thickness" value={`${record.thickness} mm`} />
            <Meta label="Application" value={record.app_type} />
            <Meta label="Usage" value={record.usage} />
            <Meta
              label="Date"
              value={new Date(record.timestamp).toLocaleDateString()}
            />
            <Meta label="Client Spec" value={record.client_spec || '—'} />
            <Meta label="Defects" value={String(record.defects.length)} />
          </div>

          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Annotated Radiograph
          </p>
          <AnnotatedImage
            src={record.annotated_image}
            defects={record.defects}
            label={`${record.defects.length} indications`}
            className="mb-6"
          />

          <p className="mb-2 text-sm font-semibold text-foreground">AI Reasoning</p>
          <div className="mb-6 rounded-lg border border-border bg-secondary/30 p-4 text-sm leading-relaxed text-muted-foreground">
            {record.reasoning}
          </div>

          <p className="mb-2 text-sm font-semibold text-foreground">Defects</p>
          <div className="mb-6">
            <DefectsTable defects={record.defects} />
          </div>

          <div className="mb-6 flex flex-col gap-3">
            <Comment
              icon={<MessageSquare className="size-4 text-primary" />}
              title="Performer Remarks"
              body={record.performer_remarks}
            />
            <Comment
              icon={<ShieldCheck className="size-4 text-success" />}
              title="Supervisor Remarks"
              body={record.supervisor_remarks}
            />
          </div>
        </div>

        <div className="border-t border-border p-5">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Supervisor Comment
          </p>
          <Textarea
            rows={2}
            placeholder={
              canApprove
                ? 'Add disposition comment…'
                : 'Switch to Supervisor role in Settings to approve'
            }
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="mb-3"
          />
          <Button
            onClick={handleApprove}
            disabled={record.workflow === 'Supervisor Approved'}
            className="w-full"
          >
            <ShieldCheck />
            {record.workflow === 'Supervisor Approved'
              ? 'Already Approved'
              : 'Approve Record'}
          </Button>
        </div>
      </div>
    </div>
  )
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
        {label}
      </p>
      <p className="font-medium text-foreground">{value}</p>
    </div>
  )
}

function Comment({
  icon,
  title,
  body,
}: {
  icon: React.ReactNode
  title: string
  body?: string
}) {
  return (
    <div className="rounded-lg border border-border bg-secondary/20 p-3">
      <div className="mb-1 flex items-center gap-2">
        {icon}
        <p className="text-xs font-semibold text-foreground">{title}</p>
      </div>
      <p className="text-sm text-muted-foreground">
        {body ?? 'No remarks recorded yet.'}
      </p>
    </div>
  )
}
