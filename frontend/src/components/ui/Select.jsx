export default function Select({ label, options = [], className = '', id, ...props }) {
  return (
    <div className={className}>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-ink mb-1">
          {label}
        </label>
      )}
      <select
        id={id}
        className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm
          text-ink focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary"
        {...props}
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  )
}
