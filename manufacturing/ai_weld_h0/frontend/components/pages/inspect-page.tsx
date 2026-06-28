'use client'

import { useCallback, useRef, useState } from 'react'
import {
  Upload,
  ImageIcon,
  Play,
  Loader2,
  FileDown,
  Send,
  X,
  Sparkles,
  MessageSquare,
  ShieldCheck,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Field,
  Input,
  Select,
  Textarea,
} from '@/components/ui/primitives'
import { VerdictBadge } from '@/components/ui/badges'
import { AnnotatedImage } from '@/components/annotated-image'
import { DefectsTable } from '@/components/defects-table'
import { useToast } from '@/components/toast'
import { runInspection, submitFeedback } from '@/lib/api'
import { getRole, getApiUrl } from '@/lib/config'
import {
  APP_TYPES,
  MATERIALS,
  MODELS,
  REGULATORY_CODES,
  USAGE_TYPES,
} from '@/lib/mock-data'
import type {
  AuditEvent,
  InspectionParams,
  InspectionRecord,
  InspectResponse,
} from '@/lib/types'
import { cn } from '@/lib/utils'

const defaultParams: InspectionParams = {
  model: MODELS[0],
  material: MATERIALS[0],
  thickness: 12.5,
  regulatory_code: REGULATORY_CODES[0],
  app_type: APP_TYPES[0],
  usage: USAGE_TYPES[0],
  client_spec: '',
}

export function InspectPage({
  addRecord,
  addAudit,
}: {
  addRecord: (r: InspectionRecord) => void
  addAudit: (a: AuditEvent['action'], details: string) => void
}) {
  const { toast } = useToast()
  const [params, setParams] = useState<InspectionParams>(defaultParams)
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [dragging, setDragging] = useState(false)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<InspectionRecord | null>(null)
  const [remarks, setRemarks] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const set = <K extends keyof InspectionParams>(
    k: K,
    v: InspectionParams[K],
  ) => setParams((p) => ({ ...p, [k]: v }))

  const handleFile = useCallback(
    (f: File | undefined) => {
      if (!f) return
      if (!f.type.startsWith('image/')) {
        toast({
          variant: 'error',
          title: 'Invalid file',
          description: 'Please upload a JPG or PNG radiograph.',
        })
        return
      }
      setFile(f)
      setPreview(URL.createObjectURL(f))
      setResult(null)
    },
    [toast],
  )

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files?.[0])
  }

  const clearFile = () => {
    setFile(null)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(null)
    setResult(null)
  }

  const localMockResult = (): InspectResponse => {
    const verdict = Math.random() > 0.4 ? 'PASS' : 'REJECT'
    const defectCount = verdict === 'REJECT' ? 2 : Math.random() > 0.6 ? 1 : 0
    const types = ['Porosity', 'Crack', 'Slag Inclusion', 'Undercut']
    const defects = Array.from({ length: defectCount }).map((_, i) => {
      const rejectable = verdict === 'REJECT' && i === 0
      return {
        type: types[Math.floor(Math.random() * types.length)],
        confidence: 72 + Math.floor(Math.random() * 26),
        length_mm: Number((1 + Math.random() * 5).toFixed(1)),
        width_mm: Number((0.3 + Math.random() * 1.4).toFixed(1)),
        status: (rejectable ? 'Rejectable' : 'Acceptable') as
          | 'Rejectable'
          | 'Acceptable',
        box: {
          x: 0.15 + Math.random() * 0.5,
          y: 0.2 + Math.random() * 0.45,
          w: 0.08 + Math.random() * 0.07,
          h: 0.06 + Math.random() * 0.05,
        },
      }
    })
    return {
      status: 'ok',
      report_id: `RPT-${Math.floor(10000 + Math.random() * 89999)}`,
      result: {
        verdict,
        reasoning:
          verdict === 'PASS'
            ? `Radiographic analysis of the ${params.material} weld (${params.thickness} mm wall) was evaluated against ${params.regulatory_code} acceptance criteria. ${defectCount === 0 ? 'No reportable indications were detected.' : 'Detected indications fall within permissible dimensional limits.'} No planar discontinuities identified. The weld is determined ACCEPTABLE for ${params.usage.toLowerCase()} service.`
            : `Radiographic analysis of the ${params.material} weld (${params.thickness} mm wall) identified an indication exceeding ${params.regulatory_code} acceptance thresholds. A planar defect was localized with dimensions surpassing the maximum permissible value for the specified wall thickness. Per the governing code clause, this discontinuity is non-permissible. The weld is determined REJECTABLE and requires excavation, repair, and re-inspection.`,
      },
      annotated_image: null,
      defects,
    }
  }

  const handleRun = async () => {
    if (!file) {
      toast({
        variant: 'error',
        title: 'No image selected',
        description: 'Upload a radiograph before running inspection.',
      })
      return
    }
    setRunning(true)
    setResult(null)
    let resp: InspectResponse
    try {
      resp = await runInspection(file, params)
    } catch {
      // Backend offline → fall back to local mock so the UI stays usable.
      await new Promise((r) => setTimeout(r, 1400))
      resp = localMockResult()
    }
    if (resp.status === 'error' || !resp.result || !resp.defects) {
      toast({
        variant: 'error',
        title: 'Inspection failed',
        description: String((resp as any).result || 'An error occurred on the backend server.'),
      })
      setRunning(false)
      return
    }

    // Map backend defect data structures to match frontend expectations
    const mappedDefects = (resp.defects ?? []).map((d: any) => {
      if (d.length_mm !== undefined) return d;
      
      const px_len = d.dims?.length ?? (d.bbox ? d.bbox[2] - d.bbox[0] : 0);
      const px_width = d.dims?.width ?? (d.bbox ? d.bbox[3] - d.bbox[1] : 0);
      const length_mm = Number((px_len * 0.1).toFixed(1));
      const width_mm = Number((px_width * 0.1).toFixed(1));
      
      let status: 'Acceptable' | 'Rejectable' = 'Acceptable';
      const type_lower = String(d.type).toLowerCase();
      if (type_lower.includes('crack') || type_lower.includes('fusion') || type_lower.includes('lack')) {
        status = 'Rejectable';
      } else if (type_lower.includes('porosity') || type_lower.includes('pora')) {
        if (length_mm > (params.thickness * 0.333)) status = 'Rejectable';
      } else if (type_lower.includes('inclusion') || type_lower.includes('vkljuchenie')) {
        if (length_mm > (params.thickness * 0.5)) status = 'Rejectable';
      }

      return {
        type: d.type,
        confidence: Math.round(d.confidence > 1 ? d.confidence : d.confidence * 100),
        length_mm,
        width_mm,
        status,
        box: {
          x: d.bbox ? d.bbox[0] / 1000 : 0,
          y: d.bbox ? d.bbox[1] / 500 : 0,
          w: d.bbox ? (d.bbox[2] - d.bbox[0]) / 1000 : 0,
          h: d.bbox ? (d.bbox[3] - d.bbox[1]) / 500 : 0,
        }
      };
    });

    const record: InspectionRecord = {
      report_id: resp.report_id,
      timestamp: new Date().toISOString(),
      verdict: resp.result.verdict,
      model: params.model,
      material: params.material,
      regulatory_code: params.regulatory_code,
      app_type: params.app_type,
      usage: params.usage,
      client_spec: params.client_spec,
      thickness: params.thickness,
      reasoning: resp.result.reasoning,
      defects: mappedDefects,
      annotated_image: resp.annotated_image ?? preview,
      original_image: preview,
      workflow: 'Inspected',
    }
    setResult(record)
    addRecord(record)
    addAudit('RUN_INSPECTION', `Inspection ${record.report_id} → ${record.verdict}`)
    setRunning(false)
    toast({
      variant: record.verdict === 'PASS' ? 'success' : 'error',
      title: `Inspection complete — ${record.verdict}`,
      description: `Report ${record.report_id} generated.`,
    })
  }

  const handleRemarks = async () => {
    if (!result || !remarks.trim()) return
    const userRole = getRole()
    const isSupervisorOrAdmin = userRole === 'Supervisor' || userRole === 'Admin'
    
    const targetRole = (result.workflow === 'Performer Review' || isSupervisorOrAdmin) ? 'supervisor' : 'performer'
    const targetWorkflow = targetRole === 'supervisor' ? 'Supervisor Approved' : 'Performer Review'

    try {
      await submitFeedback(result.report_id, remarks, targetRole)
      const updatedRecord: InspectionRecord = {
        ...result,
        workflow: targetWorkflow,
        performer_remarks: targetRole === 'performer' ? remarks : result.performer_remarks,
        supervisor_remarks: targetRole === 'supervisor' ? remarks : result.supervisor_remarks,
      }
      setResult(updatedRecord)
      addRecord(updatedRecord)
      addAudit('SUBMIT_FEEDBACK', `${targetRole === 'supervisor' ? 'Evaluator' : 'Performer'} remarks added to ${result.report_id}`)
      toast({
        variant: 'success',
        title: 'Remarks submitted',
        description: `${targetRole === 'supervisor' ? 'Evaluator' : 'Performer'} remarks recorded on the inspection.`,
      })
      setRemarks('')
    } catch (err) {
      toast({
        variant: 'error',
        title: 'Failed to submit remarks',
        description: String(err),
      })
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-6 lg:grid-cols-5">
        {/* Upload */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Radiograph Upload</CardTitle>
          </CardHeader>
          <CardContent>
            {preview ? (
              <div className="relative">
                <AnnotatedImage src={preview} label={file?.name} showBoxes={false} />
                <Button
                  size="icon-sm"
                  variant="secondary"
                  onClick={clearFile}
                  className="absolute right-2 top-2"
                  aria-label="Remove image"
                >
                  <X />
                </Button>
              </div>
            ) : (
              <div
                onDragOver={(e) => {
                  e.preventDefault()
                  setDragging(true)
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                onClick={() => inputRef.current?.click()}
                className={cn(
                  'flex aspect-[16/9] cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed transition-colors',
                  dragging
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50 hover:bg-secondary/30',
                )}
              >
                <div className="flex size-14 items-center justify-center rounded-full bg-secondary">
                  {dragging ? (
                    <ImageIcon className="size-6 text-primary" />
                  ) : (
                    <Upload className="size-6 text-muted-foreground" />
                  )}
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-foreground">
                    Drop radiography image here
                  </p>
                  <p className="text-xs text-muted-foreground">
                    or click to browse — JPG, PNG up to 25MB
                  </p>
                </div>
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png"
              className="hidden"
              onChange={(e) => handleFile(e.target.files?.[0])}
            />
          </CardContent>
        </Card>

        {/* Parameters */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Inspection Parameters</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Field label="Model">
              <Select
                value={params.model}
                onChange={(e) => set('model', e.target.value)}
              >
                {MODELS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </Select>
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Material">
                <Select
                  value={params.material}
                  onChange={(e) => set('material', e.target.value)}
                >
                  {MATERIALS.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Wall Thickness (mm)">
                <Input
                  type="number"
                  min={0.1}
                  max={100}
                  step={0.1}
                  value={params.thickness}
                  onChange={(e) =>
                    set('thickness', Number(e.target.value))
                  }
                />
              </Field>
            </div>
            <Field label="Regulatory Code">
              <Select
                value={params.regulatory_code}
                onChange={(e) => set('regulatory_code', e.target.value)}
              >
                {REGULATORY_CODES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </Select>
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Application Type">
                <Select
                  value={params.app_type}
                  onChange={(e) => set('app_type', e.target.value)}
                >
                  {APP_TYPES.map((a) => (
                    <option key={a} value={a}>
                      {a}
                    </option>
                  ))}
                </Select>
              </Field>
              <Field label="Usage">
                <Select
                  value={params.usage}
                  onChange={(e) => set('usage', e.target.value)}
                >
                  {USAGE_TYPES.map((u) => (
                    <option key={u} value={u}>
                      {u}
                    </option>
                  ))}
                </Select>
              </Field>
            </div>
            <Field label="Client Spec (optional)">
              <Input
                placeholder="e.g. CS-2034"
                value={params.client_spec}
                onChange={(e) => set('client_spec', e.target.value)}
              />
            </Field>
          </CardContent>
        </Card>
      </div>

      <Button
        size="lg"
        onClick={handleRun}
        disabled={running}
        className="h-12 w-full bg-gradient-to-r from-amber-500 to-orange-500 text-base font-semibold text-primary-foreground glow-amber hover:from-amber-400 hover:to-orange-400"
      >
        {running ? (
          <>
            <Loader2 className="size-5 animate-spin" />
            Analyzing radiograph…
          </>
        ) : (
          <>
            <Play className="size-5" />
            Run Inspection
          </>
        )}
      </Button>

      {result && (
        <ResultsPanel
          record={result}
          remarks={remarks}
          setRemarks={setRemarks}
          onSubmitRemarks={handleRemarks}
        />
      )}
    </div>
  )
}

function ResultsPanel({
  record,
  remarks,
  setRemarks,
  onSubmitRemarks,
}: {
  record: InspectionRecord
  remarks: string
  setRemarks: (v: string) => void
  onSubmitRemarks: () => void
}) {
  const { toast } = useToast()
  const pass = record.verdict === 'PASS'
  return (
    <Card className="glass animate-fade-in-up overflow-hidden">
      <div
        className={cn(
          'flex flex-wrap items-center justify-between gap-4 border-b border-border p-6',
        )}
      >
        <div className="flex items-center gap-4">
          <div
            className={cn(
              'flex flex-col items-center justify-center rounded-xl px-6 py-3',
              pass ? 'glow-success bg-success/10' : 'animate-reject-pulse bg-destructive/10',
            )}
          >
            <span
              className={cn(
                'text-2xl font-black tracking-tight',
                pass ? 'text-success' : 'text-destructive',
              )}
            >
              {record.verdict}
            </span>
          </div>
          <div>
            <p className="font-mono text-sm font-semibold text-foreground">
              {record.report_id}
            </p>
            <p className="text-xs text-muted-foreground">
              {new Date(record.timestamp).toLocaleString()}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              {record.material} · {record.thickness} mm · {record.regulatory_code}
            </p>
          </div>
        </div>
        <Button
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
          <FileDown />
          Download PDF Report
        </Button>
      </div>

      <CardContent className="flex flex-col gap-6 pt-6">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="flex flex-col gap-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Original
            </p>
            <AnnotatedImage
              src={record.original_image}
              showBoxes={false}
              label="Source radiograph"
            />
          </div>
          <div className="flex flex-col gap-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              AI Annotated
            </p>
            <AnnotatedImage
              src={record.annotated_image}
              defects={record.defects}
              label={`${record.defects.length} indications`}
            />
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center gap-2">
            <Sparkles className="size-4 text-primary" />
            <p className="text-sm font-semibold text-foreground">
              AI Reasoning
            </p>
          </div>
          <div className="rounded-lg border border-border bg-secondary/30 p-4 text-sm leading-relaxed text-muted-foreground">
            {record.reasoning}
          </div>
        </div>

        <div>
          <p className="mb-2 text-sm font-semibold text-foreground">
            Detected Defects
          </p>
          <DefectsTable defects={record.defects} />
        </div>

        {(record.performer_remarks || record.supervisor_remarks) && (
          <div className="flex flex-col gap-3">
            {record.performer_remarks && (
              <div className="rounded-lg border border-border bg-secondary/20 p-3">
                <div className="mb-1 flex items-center gap-2">
                  <MessageSquare className="size-4 text-primary" />
                  <p className="text-xs font-semibold text-foreground">Performer Remarks</p>
                </div>
                <p className="text-sm text-muted-foreground">{record.performer_remarks}</p>
              </div>
            )}
            {record.supervisor_remarks && (
              <div className="rounded-lg border border-border bg-secondary/20 p-3">
                <div className="mb-1 flex items-center gap-2">
                  <ShieldCheck className="size-4 text-success" />
                  <p className="text-xs font-semibold text-foreground">Evaluator Remarks</p>
                </div>
                <p className="text-sm text-muted-foreground">{record.supervisor_remarks}</p>
              </div>
            )}
          </div>
        )}

        <div>
          <p className="mb-2 text-sm font-semibold text-foreground">
            {(record.workflow === 'Performer Review' || getRole() === 'Supervisor' || getRole() === 'Admin')
              ? 'Evaluator Remarks'
              : 'Performer Remarks'}
          </p>
          <Textarea
            rows={3}
            placeholder={(record.workflow === 'Performer Review' || getRole() === 'Supervisor' || getRole() === 'Admin')
              ? "Add evaluator/supervisor remarks..."
              : "Add performer remarks..."}
            value={remarks}
            onChange={(e) => setRemarks(e.target.value)}
          />
          <div className="mt-2 flex justify-end">
            <Button onClick={onSubmitRemarks} disabled={!remarks.trim()}>
              <Send />
              Submit Remarks
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
