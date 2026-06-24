const VARIANTS = {
  primary: 'bg-primary text-white hover:bg-primary-hover disabled:opacity-50',
  secondary:
    'bg-surface text-ink border border-border hover:bg-surface-2 disabled:opacity-50',
  ghost: 'bg-transparent text-primary hover:bg-primary-soft disabled:opacity-50',
  success: 'bg-success text-white hover:opacity-90 disabled:opacity-50',
  warning: 'bg-warning text-white hover:opacity-90 disabled:opacity-50',
}

const SIZES = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
}

export default function Button({
  variant = 'primary',
  size = 'md',
  className = '',
  type = 'button',
  ...props
}) {
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-md font-medium
        transition-colors focus:outline-none focus:ring-2 focus:ring-primary/40
        disabled:cursor-not-allowed ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...props}
    />
  )
}
