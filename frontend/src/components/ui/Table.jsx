/*
 * Table cho GV/Admin.
 * columns: [{ key, header, render?(row), className? }]
 * rows: list object; rowKey: hàm lấy key.
 */
export default function Table({ columns, rows, rowKey, empty = 'Chưa có dữ liệu' }) {
  return (
    <div className="overflow-x-auto rounded-card border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-surface-2 text-left text-muted">
            {columns.map((c) => (
              <th key={c.key} className={`px-4 py-2.5 font-medium ${c.className || ''}`}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-muted">
                {empty}
              </td>
            </tr>
          ) : (
            rows.map((row, i) => (
              <tr
                key={rowKey ? rowKey(row) : i}
                className="border-t border-border bg-surface hover:bg-surface-2/60"
              >
                {columns.map((c) => (
                  <td key={c.key} className={`px-4 py-2.5 text-ink ${c.className || ''}`}>
                    {c.render ? c.render(row) : row[c.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
