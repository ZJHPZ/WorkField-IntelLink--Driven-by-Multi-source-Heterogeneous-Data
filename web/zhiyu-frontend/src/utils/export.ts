// ═══════════════════════════════════════════════
// 浏览器端 CSV 导出工具 —— 企业侧「导出」按钮的真实下载实现。
// 纯前端：UTF-8 BOM + CRLF，Excel 直接打开不乱码；
// Blob 触发浏览器下载，离线（Silent Fallback demo 数据）也可用，无需后端端点。
// ═══════════════════════════════════════════════

export function csvEscape(v: unknown): string {
  const s = v === null || v === undefined ? '' : String(v)
  // 含逗号 / 引号 / 换行 → 加引号包裹，内部引号翻倍（RFC 4180）
  if (/[",\n\r]/.test(s)) return '"' + s.replace(/"/g, '""') + '"'
  return s
}

export function buildCsv(headers: string[], rows: unknown[][]): string {
  const lines: string[] = [headers.map(csvEscape).join(',')]
  for (const r of rows) lines.push(r.map(csvEscape).join(','))
  // ﻿ BOM 让 Excel 识别 UTF-8 中文；CRLF 为 Excel 标准换行
  return '﻿' + lines.join('\r\n')
}

export function today(d: Date = new Date()): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}

export function downloadCsv(filename: string, headers: string[], rows: unknown[][]): void {
  const blob = new Blob([buildCsv(headers, rows)], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  // 延迟释放 URL，避免个别浏览器在下载尚未开始时即撤销引用
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
