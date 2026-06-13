import type { CSSProperties } from 'react'

type ProgressRingProps = {
  value: number
  label: string
  caption: string
  tone?: 'violet' | 'cyan' | 'amber' | 'emerald'
  size?: number
}

const toneMap = {
  violet: '#8b5cf6',
  cyan: '#06b6d4',
  amber: '#f59e0b',
  emerald: '#10b981',
} as const

export function ProgressRing({
  value,
  label,
  caption,
  tone = 'violet',
  size = 150,
}: ProgressRingProps) {
  const progress = Math.max(0, Math.min(100, value))
  const style = {
    background: `conic-gradient(${toneMap[tone]} ${progress * 3.6}deg, rgba(255, 255, 255, 0.08) 0deg)`,
    width: `${size}px`,
    height: `${size}px`,
  } satisfies CSSProperties

  return (
    <div className="progress-ring" style={style} aria-label={`${label} ${progress}%`}>
      <div className="progress-ring__inner">
        <span className="progress-ring__value">{progress}%</span>
        <strong>{label}</strong>
        <p>{caption}</p>
      </div>
    </div>
  )
}