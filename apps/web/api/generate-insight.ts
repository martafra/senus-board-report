// Vercel serverless function. Google blocks direct Gemini calls from most cloud-hosting
// datacenter IP ranges (confirmed against Render specifically, mid-2026), even with a correctly
// restricted API key. This function exists purely to make that one outbound call from a network
// Google doesn't block, keeping GEMINI_API_KEY server-side here (never sent to the browser).
// The backend (apps/api/app/ai/insights.py) builds the actual prompt; this function is a plain
// relay to Gemini's REST API, not a second place that knows about board report content.

interface GenerateInsightRequestBody {
  model?: string
  system_instruction?: string
  prompt?: string
}

export default async function handler(req: any, res: any): Promise<void> {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' })
    return
  }

  const secret = req.headers['x-proxy-secret']
  if (!secret || secret !== process.env.INSIGHT_PROXY_SECRET) {
    res.status(401).json({ error: 'Unauthorized' })
    return
  }

  const { model, system_instruction, prompt } = (req.body ?? {}) as GenerateInsightRequestBody
  if (!model || !system_instruction || !prompt) {
    res.status(400).json({ error: 'Missing model, system_instruction or prompt' })
    return
  }

  const apiKey = process.env.GEMINI_API_KEY
  if (!apiKey) {
    res.status(500).json({ error: 'GEMINI_API_KEY not configured' })
    return
  }

  const geminiResponse = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: system_instruction }] },
        contents: [{ parts: [{ text: prompt }] }],
      }),
    },
  )

  if (!geminiResponse.ok) {
    const errorText = await geminiResponse.text()
    res.status(502).json({ error: `Gemini request failed (${geminiResponse.status}): ${errorText}` })
    return
  }

  const geminiData = await geminiResponse.json()
  const text = geminiData?.candidates?.[0]?.content?.parts?.[0]?.text
  if (!text) {
    res.status(502).json({ error: `Gemini response had no text: ${JSON.stringify(geminiData)}` })
    return
  }

  res.status(200).json({ text })
}
