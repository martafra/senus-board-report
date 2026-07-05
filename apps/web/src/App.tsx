import { Navigate, Route, Routes } from 'react-router-dom'
import { LandingPage } from '@/pages/LandingPage'
import { LoginPage } from '@/pages/LoginPage'
import { GrowthPage } from '@/pages/GrowthPage'
import { ProfitabilityPage } from '@/pages/ProfitabilityPage'
import { CashLiquidityPage } from '@/pages/CashLiquidityPage'
import { SolvencyPage } from '@/pages/SolvencyPage'
import { ReturnsPage } from '@/pages/ReturnsPage'
import { DashboardLayout } from '@/components/DashboardLayout'
import { ProtectedRoute } from '@/routes/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/dashboard" element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route index element={<GrowthPage />} />
          <Route path="profitability" element={<ProfitabilityPage />} />
          <Route path="cash-liquidity" element={<CashLiquidityPage />} />
          <Route path="solvency" element={<SolvencyPage />} />
          <Route path="returns" element={<ReturnsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
