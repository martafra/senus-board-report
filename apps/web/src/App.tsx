import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function App() {
  const [apiStatus, setApiStatus] = useState<'checking' | 'ok' | 'error'>('checking')

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => (res.ok ? setApiStatus('ok') : setApiStatus('error')))
      .catch(() => setApiStatus('error'))
  }, [])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-slate-50 text-slate-900">
      <h1 className="text-2xl font-semibold">Senus PLC Board Report</h1>
      <p className="text-slate-500">
        API status:{' '}
        <span
          className={
            apiStatus === 'ok'
              ? 'text-green-600'
              : apiStatus === 'error'
                ? 'text-red-600'
                : 'text-slate-400'
          }
        >
          {apiStatus}
        </span>
      </p>
    </main>
  )
}

export default App
