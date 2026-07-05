import { useNavigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LoginForm } from '@/components/LoginForm'

export function LoginPage() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Senus PLC Board Report</CardTitle>
        </CardHeader>
        <CardContent>
          <LoginForm onSuccess={() => navigate('/dashboard', { replace: true })} />
        </CardContent>
      </Card>
    </div>
  )
}
