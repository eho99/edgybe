"use client"

import Link from "next/link"
import { useMemo, useState } from "react"
import {
  ReferralConfig,
  ReferralStatsBreakdownItem,
  ReferralStatsFilters,
  ReferralStatsData,
  useReferralStats,
} from "@/hooks/useReferrals"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorDisplay } from "@/components/error/ErrorDisplay"

const MS_PER_DAY = 24 * 60 * 60 * 1000

const toDateInputValue = (date: Date) => date.toISOString().slice(0, 16)
const defaultStartDateValue = toDateInputValue(new Date(Date.now() - 30 * MS_PER_DAY))
const defaultEndDateValue = toDateInputValue(new Date())

interface ReferralStatsPanelProps {
  orgId: string
  config?: ReferralConfig
}

const breakdownItemsToMax = (items?: ReferralStatsBreakdownItem[]) => {
  if (!items || items.length === 0) {
    return 1
  }
  return Math.max(...items.map((item) => item.count), 1)
}

const BreakdownBar = ({
  label,
  count,
  max,
}: {
  label: string
  count: number
  max: number
}) => {
  const widthPercent = Math.min(100, Math.round((count / max) * 100))

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span className="truncate pr-2">{label}</span>
        <span className="font-semibold">{count}</span>
      </div>
      <div className="h-2 rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all duration-200"
          style={{ width: `${widthPercent}%` }}
        />
      </div>
    </div>
  )
}

const BreakdownChartPanel = ({
  title,
  items,
  maxValue,
}: {
  title: string
  items?: ReferralStatsBreakdownItem[]
  maxValue: number
}) => (
  <div className="rounded-lg border bg-background p-4">
    <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
      {title}
    </p>
    <div className="mt-3 space-y-3 text-sm">
      {items && items.length ? (
        items.slice(0, 6).map((item) => (
          <BreakdownBar key={item.label} label={item.label} count={item.count} max={maxValue} />
        ))
      ) : (
        <p className="text-xs text-muted-foreground">No data yet</p>
      )}
    </div>
  </div>
)

export function ReferralStatsPanel({ orgId, config }: ReferralStatsPanelProps) {
  const [dateRange, setDateRange] = useState({
    start: defaultStartDateValue,
    end: defaultEndDateValue,
  })
  const [selectedLocation, setSelectedLocation] = useState<string | undefined>(undefined)
  const [selectedTime, setSelectedTime] = useState<string | undefined>(undefined)
  const [selectedBehaviors, setSelectedBehaviors] = useState<string[]>([])

  const behaviorOptions = config?.behaviors?.options || []
  const locationOptions = config?.locations?.options || []
  const timeOptions = config?.time_of_day?.options || []

  const statsFilters: ReferralStatsFilters = useMemo(() => {
    const filters: ReferralStatsFilters = {}

    if (dateRange.start) {
      const parsed = new Date(dateRange.start)
      if (!Number.isNaN(parsed.getTime())) {
        filters.start_date = parsed.toISOString()
      }
    }

    if (dateRange.end) {
      const parsed = new Date(dateRange.end)
      if (!Number.isNaN(parsed.getTime())) {
        filters.end_date = parsed.toISOString()
      }
    }

    if (selectedLocation) {
      filters.location = selectedLocation
    }

    if (selectedTime) {
      filters.time_of_day = selectedTime
    }

    if (selectedBehaviors.length > 0) {
      filters.behaviors = selectedBehaviors
    }

    return filters
  }, [dateRange, selectedLocation, selectedTime, selectedBehaviors])

  const { stats, isLoading, error } = useReferralStats(orgId, statsFilters)

  const toggleBehavior = (behavior: string) => {
    setSelectedBehaviors((prev) =>
      prev.includes(behavior) ? prev.filter((item) => item !== behavior) : [...prev, behavior]
    )
  }

  const resetFilters = () => {
    setDateRange({ start: defaultStartDateValue, end: defaultEndDateValue })
    setSelectedLocation(undefined)
    setSelectedTime(undefined)
    setSelectedBehaviors([])
  }

  const chartMax = useMemo(() => {
    if (!stats) {
      return 1
    }
    const candidates = [
      ...stats.breakdown_by_location.map((item) => item.count),
      ...stats.breakdown_by_time_of_day.map((item) => item.count),
      ...stats.breakdown_by_behavior.map((item) => item.count),
    ]
    return Math.max(...candidates, 1)
  }, [stats])

  const formattedRange = stats
    ? `${new Date(stats.start_date).toLocaleString()} → ${new Date(stats.end_date).toLocaleString()}`
    : "Last 30 days"

  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <CardTitle>Referral Dashboard</CardTitle>
            <CardDescription>
              Track submissions, trends, and quick actions for your organization.
            </CardDescription>
          </div>
          <div className="text-right text-xs text-muted-foreground">{formattedRange}</div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/dashboard/referrals">
            <Button size="sm" variant="outline">
              View referrals
            </Button>
          </Link>
          <Link href="/dashboard/referrals/create">
            <Button size="sm">Create referral</Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground">Start</p>
            <Input
              type="datetime-local"
              value={dateRange.start}
              onChange={(event) => setDateRange((prev) => ({ ...prev, start: event.target.value }))}
            />
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">End</p>
            <Input
              type="datetime-local"
              value={dateRange.end}
              onChange={(event) => setDateRange((prev) => ({ ...prev, end: event.target.value }))}
            />
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Location</p>
            <Select
              value={selectedLocation ?? "__CLEAR_SELECT_LOCATION__"}
              onValueChange={(value) =>
                setSelectedLocation(value === "__CLEAR_SELECT_LOCATION__" ? undefined : value)
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="All locations" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__CLEAR_SELECT_LOCATION__">All locations</SelectItem>
                {locationOptions.map((location) => (
                  <SelectItem key={location} value={location}>
                    {location}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Time of day</p>
            <Select
              value={selectedTime ?? "__CLEAR_SELECT_TIME__"}
              onValueChange={(value) =>
                setSelectedTime(value === "__CLEAR_SELECT_TIME__" ? undefined : value)
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="All times" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="__CLEAR_SELECT_TIME__">All times</SelectItem>
                {timeOptions.map((time) => (
                  <SelectItem key={time} value={time}>
                    {time}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Behaviors</p>
            <button
              type="button"
              className="text-xs text-primary underline-offset-2 hover:underline"
              onClick={() => setSelectedBehaviors([])}
            >
              Clear
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {behaviorOptions.length === 0 && (
              <p className="text-xs text-muted-foreground">No behavior options configured.</p>
            )}
            {behaviorOptions.map((behavior) => (
              <Button
                key={behavior}
                size="sm"
                variant={selectedBehaviors.includes(behavior) ? "default" : "outline"}
                onClick={() => toggleBehavior(behavior)}
              >
                {behavior}
              </Button>
            ))}
          </div>
        </div>

        {isLoading && !stats ? (
          <div className="space-y-6">
            {/* Stats Cards Skeleton */}
            <div className="grid gap-4 md:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="rounded-lg border border-border bg-background p-4">
                  <Skeleton className="h-4 w-24 mb-2" />
                  <Skeleton className="h-8 w-16" />
                </div>
              ))}
            </div>

            {/* Chart Panels Skeleton */}
            <div className="grid gap-4 md:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="rounded-lg border border-border bg-background p-4 space-y-3">
                  <Skeleton className="h-3 w-20" />
                  {Array.from({ length: 4 }).map((_, j) => (
                    <div key={j} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <Skeleton className="h-3 w-24" />
                        <Skeleton className="h-3 w-8" />
                      </div>
                      <Skeleton className="h-2 w-full rounded-full" />
                    </div>
                  ))}
                </div>
              ))}
            </div>

            {/* Recent Referrals Skeleton */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-24" />
              </div>
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="rounded-lg border border-muted/60 p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-3 w-24" />
                      </div>
                      <div className="flex items-center gap-2">
                        <Skeleton className="h-5 w-16" />
                        <Skeleton className="h-4 w-24" />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Skeleton className="h-3 w-20" />
                      <Skeleton className="h-3 w-20" />
                      <Skeleton className="h-3 w-20" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : error ? (
          <ErrorDisplay
            error={error instanceof Error ? error : new Error("Failed to load referral stats")}
          />
        ) : (
          stats && (
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="rounded-lg border bg-background p-4">
                  <p className="text-xs font-semibold text-muted-foreground">Total referrals</p>
                  <p className="text-3xl font-bold">{stats.total_referrals}</p>
                </div>
                <div className="rounded-lg border bg-background p-4">
                  <p className="text-xs font-semibold text-muted-foreground">Recent submissions</p>
                  <p className="text-3xl font-bold">{stats.recent_referrals.length}</p>
                </div>
                <div className="rounded-lg border bg-background p-4">
                  <p className="text-xs font-semibold text-muted-foreground">Behaviors tracked</p>
                  <p className="text-3xl font-bold">{stats.breakdown_by_behavior.length}</p>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <BreakdownChartPanel
                  title="Location"
                  items={stats.breakdown_by_location}
                  maxValue={chartMax}
                />
                <BreakdownChartPanel
                  title="Time of day"
                  items={stats.breakdown_by_time_of_day}
                  maxValue={chartMax}
                />
                <BreakdownChartPanel
                  title="Behavior"
                  items={stats.breakdown_by_behavior}
                  maxValue={chartMax}
                />
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">Recent referrals</p>
                  <p className="text-xs text-muted-foreground">
                    Showing the {stats.recent_referrals.length} most recent
                  </p>
                </div>
                <div className="mt-3 space-y-3">
                  {stats.recent_referrals.map((referral) => (
                    <Link
                      key={referral.id}
                      href={`/dashboard/referrals/${referral.id}`}
                      className="flex flex-col gap-1 rounded-lg border border-muted/60 px-4 py-3 transition hover:border-primary/80"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="text-sm font-semibold">
                            {referral.student_name || "Unknown Student"}
                          </p>
                          {referral.student_student_id && (
                            <p className="text-xs text-muted-foreground">{referral.student_student_id}</p>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <Badge variant="outline">{referral.status}</Badge>
                          <span>{new Date(referral.created_at).toLocaleString()}</span>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                        <span>{referral.type}</span>
                        <span>•</span>
                        <span>{referral.location || "Location not set"}</span>
                        <span>•</span>
                        <span>{referral.time_of_day || "Time not set"}</span>
                      </div>
                      {referral.behaviors && referral.behaviors.length > 0 && (
                        <p className="text-xs text-muted-foreground">
                          Behaviors: {referral.behaviors.join(", ")}
                        </p>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          )
        )}

        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">Filters based on your referral config</p>
          <button
            type="button"
            className="text-xs text-muted-foreground underline-offset-2 hover:underline"
            onClick={resetFilters}
          >
            Reset
          </button>
        </div>
      </CardContent>
    </Card>
  )
}



