import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger'

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-primary/20 text-primary border-primary/30',
  success: 'bg-success/15 text-success border-success/40',
  warning: 'bg-warning/15 text-warning border-warning/40',
  danger: 'bg-danger/15 text-danger border-danger/40',
}

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  variant?: BadgeVariant
}

export function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex w-fit items-center rounded-full border px-2 py-1 text-xs font-medium uppercase tracking-wide',
        variantStyles[variant],
        className,
      )}
      {...props}
    />
  )
}
