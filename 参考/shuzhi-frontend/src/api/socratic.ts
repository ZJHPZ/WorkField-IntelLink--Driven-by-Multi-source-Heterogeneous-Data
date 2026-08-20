const SOCRATIC_BASE = import.meta.env.VITE_SOCRATIC_API_URL || ''

export interface SocraticRequest {
  question: string
  topic?: string
  user_level?: string
  user_id?: string
}

export interface SocraticChunk {
  type: 'text' | 'done' | 'error'
  content: string
  section: '' | 'questions' | 'assumptions' | 'reflection'
}

export async function* streamSocraticReflection(
  params: SocraticRequest,
  signal?: AbortSignal,
): AsyncGenerator<SocraticChunk> {
  const uid = localStorage.getItem('user_id') || 'default_user'

  const response = await fetch(`${SOCRATIC_BASE}/api/socratic/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-Id': uid,
    },
    body: JSON.stringify({ ...params, user_id: uid }),
    signal,
  })

  if (!response.ok) {
    const errText = await response.text().catch(() => '')
    throw new Error(`苏格拉底服务错误 (${response.status}): ${errText.slice(0, 200)}`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('无法读取响应流')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data:')) {
        try {
          const data = JSON.parse(line.slice(5).trim())
          yield data as SocraticChunk
        } catch {
          // skip malformed
        }
      }
    }
  }
}

export async function checkSocraticHealth(): Promise<boolean> {
  try {
    const resp = await fetch(`${SOCRATIC_BASE}/api/socratic/health`)
    const data = await resp.json()
    return data.status === 'ok'
  } catch {
    return false
  }
}
