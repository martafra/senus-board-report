import { NavLink, Outlet } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/hooks/useAuth'

const SECTIONS = [
  { to: '/', label: 'Growth & Revenue', end: true },
  { to: '/profitability', label: 'Profitability' },
  { to: '/cash-liquidity', label: 'Cash & Liquidity' },
  { to: '/solvency', label: 'Solvency & Leverage' },
  { to: '/returns', label: 'Returns' },
]

export function DashboardLayout() {
  const { logout } = useAuth()

  return (
    <div className="min-h-screen bg-muted/30">
      <header className="flex items-center justify-between border-b bg-background px-6 py-4">
        <h1 className="text-lg font-semibold">Senus PLC Board Report</h1>
        <Button variant="outline" size="sm" onClick={logout}>
          Sign out
        </Button>
      </header>
      <nav className="flex gap-1 border-b bg-background px-6">
        {SECTIONS.map((section) => (
          <NavLink
            key={section.to}
            to={section.to}
            end={section.end}
            className={({ isActive }) =>
              `border-b-2 px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`
            }
          >
            {section.label}
          </NavLink>
        ))}
      </nav>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
