import type { ReactNode } from 'react'

export type BentoSlot = 'lead' | 'stack' | 'status' | 'trend' | 'allocation' | 'highlight' | 'salary' | 'skills' | 'activity'

export function Web3Bento({ children }: { children: ReactNode }) {
  return <div className="bento-grid">{children}</div>
}

export function Tile({
  title,
  action,
  className = '',
  children,
}: {
  title?: ReactNode
  action?: ReactNode
  className?: string
  children: ReactNode
}) {
  return (
    <section className={`bento-tile ${className}`}>
      {(title || action) && <header className="tile-head">{title && <h2>{title}</h2>}{action}</header>}
      {children}
    </section>
  )
}

export function MarketMetric({ title, value, detail, tone }: { title: string; value: string; detail: string; tone: 'lime' | 'lilac' | 'copper' | 'mint' }) {
  return <section className={`bento-tile tile--metric market-metric market-metric--${tone}`} aria-label={`${title}: ${value}`}>
    <span>{title}</span>
    <strong>{value}</strong>
    <small>{detail}</small>
  </section>
}
