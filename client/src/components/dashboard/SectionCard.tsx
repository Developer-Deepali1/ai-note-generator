import type { ReactNode } from 'react'
import { FiArrowUpRight } from 'react-icons/fi'

type SectionCardProps = {
  eyebrow?: string
  title: string
  description?: string
  actionLabel?: string
  onActionClick?: () => void
  children: ReactNode
  className?: string
}

export function SectionCard({
  eyebrow,
  title,
  description,
  actionLabel,
  onActionClick,
  children,
  className = '',
}: SectionCardProps) {
  return (
    <section className={`section-card ${className}`.trim()}>
      <header className="section-card__header">
        <div>
          {eyebrow ? <p className="eyebrow section-card__eyebrow">{eyebrow}</p> : null}
          <h2 className="section-card__title">{title}</h2>
          {description ? <p className="section-card__description">{description}</p> : null}
        </div>
        {actionLabel ? (
          <button type="button" className="section-card__action" onClick={onActionClick}>
            <span>{actionLabel}</span>
            <FiArrowUpRight />
          </button>
        ) : null}
      </header>

      <div className="section-card__body">{children}</div>
    </section>
  )
}