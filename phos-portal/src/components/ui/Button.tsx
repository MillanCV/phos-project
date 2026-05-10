import type { ButtonHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-primary text-primaryForeground border-primary/70 hover:bg-primary/90 focus-visible:ring-primary/80',
  secondary:
    'bg-muted text-foreground border-border hover:bg-muted/80 focus-visible:ring-primary/50',
  ghost: 'bg-transparent text-mutedForeground border-border hover:bg-muted/60 focus-visible:ring-primary/40',
  danger: 'bg-danger/90 text-white border-danger/70 hover:bg-danger focus-visible:ring-danger/60',
}

export function Button({ className, variant = 'primary', type = 'button', ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-md border px-3 py-2 text-sm font-medium',
        'transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-60',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-background',
        variantStyles[variant],
        className,
      )}
      {...props}
    />
  )
}
