import { Navigate, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { LoginForm } from '@/components/LoginForm'
import { useAuth } from '@/hooks/useAuth'

const SECTIONS = [
  { label: 'Growth & Revenue', color: 'var(--color-chart-1)' },
  { label: 'Profitability', color: 'var(--color-chart-2)' },
  { label: 'Cash & Liquidity', color: 'var(--color-chart-3)' },
  { label: 'Solvency & Leverage', color: 'var(--color-chart-4)' },
  { label: 'Returns', color: 'var(--color-chart-5)' },
]

export function LandingPage() {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-900 p-6">
      <div className="flex max-w-xl flex-col items-center gap-6 rounded-2xl border bg-background p-10 text-center shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-xl">
        <div className="flex flex-col gap-3">
          <h1 className="text-3xl font-semibold text-balance">
            One place to actually understand how Senus PLC is doing
          </h1>
          <p className="text-muted-foreground">
            Real figures from Senus PLC's official filings, turned into a live board report with
            AI-written commentary in plain language, for Management, the Board, Investors and
            Credit Providers alike.
          </p>
        </div>
        <ul className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 text-sm">
          {SECTIONS.map((section) => (
            <li key={section.label} className="flex items-center gap-1.5">
              <span
                className="inline-block size-2 rounded-full"
                style={{ backgroundColor: section.color }}
              />
              {section.label}
            </li>
          ))}
        </ul>
        <Dialog>
          <DialogTrigger render={<Button size="lg" />}>Sign in</DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Senus PLC Board Report</DialogTitle>
            </DialogHeader>
            <LoginForm onSuccess={() => navigate('/dashboard', { replace: true })} />
          </DialogContent>
        </Dialog>
      </div>
    </div>
  )
}
