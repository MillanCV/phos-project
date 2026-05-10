import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

type ToastVariant = 'default' | 'danger'

type ToastProps = HTMLAttributes<HTMLDivElement> & {
  variant?: ToastVariant
}

const variantStyles: Record<ToastVariant, string> = {
  default: 'border-primary/40 bg-primary/10 text-foreground',
  danger: 'border-danger/50 bg-danger/10 text-danger',
}

export function Toast({ className, variant = 'default', ...props }: ToastProps) {
  return <div className={cn('rounded-md border px-3 py-2 text-sm', variantStyles[variant], className)} {...props} />
}
