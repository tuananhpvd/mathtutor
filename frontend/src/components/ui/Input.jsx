export default function Input({ label, error, className = '', id, ...props }) {
  return (
    <div className={className}>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-ink mb-1">
          {label}
        </label>
      )}
      <input
        id={id}
        className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm
          text-ink placeholder:text-muted focus:outline-none focus:ring-2
          focus:ring-primary/40 focus:border-primary"
        {...props}
      />
      {error && <p className="text-sm text-danger mt-1">{error}</p>}
    </div>
  )
}
