import { Button } from '../ui'
import Formula from '../Formula'
import AnswerInputTLN from './AnswerInputTLN'

function renderY(text) {
  return String(text)
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
    )
}

// TNDS xét từng ý a→d. Mỗi ý có thể bắt buộc suy luận (nhập biểu thức) trước khi chốt Đúng/Sai.
export default function AnswerInputTNDS({
  y = [],
  y_hien_tai,
  trang_thai_y = {},
  cho_chon = true,
  onGui,
  dang_gui,
}) {
  const yDangXet = y.find((item) => item.ky_hieu === y_hien_tai)

  return (
    <div className="flex flex-col gap-4">
      {/* Tiến trình các ý */}
      <div className="flex gap-1.5">
        {y.map((item) => {
          const st = trang_thai_y?.[item.ky_hieu]
          const cls =
            item.ky_hieu === y_hien_tai
              ? 'bg-primary text-white'
              : st === 'xong'
                ? 'bg-success-soft text-success'
                : 'bg-surface-2 text-muted'
          return (
            <span
              key={item.ky_hieu}
              className={`h-7 w-7 grid place-items-center rounded-full text-xs font-medium ${cls}`}
            >
              {item.ky_hieu}
            </span>
          )
        })}
      </div>

      {yDangXet ? (
        <>
          <div className="rounded-md border border-border px-3 py-2.5">
            <p className="text-xs text-muted mb-1">Mệnh đề {yDangXet.ky_hieu})</p>
            <p className="text-sm text-ink">{renderY(yDangXet.noi_dung_y)}</p>
          </div>

          {cho_chon === false ? (
            // Pha suy luận: nhập biểu thức để máy chấm trước khi được chốt Đúng/Sai
            <>
              <p className="text-sm font-medium text-ink">Trả lời câu hỏi gợi ý bên ô chat vào đây</p>
              <AnswerInputTLN onGui={onGui} dang_gui={dang_gui} />
            </>
          ) : (
            // Pha chốt
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="success"
                disabled={dang_gui}
                onClick={() => onGui({ dap_an_nhap: 'Dung', noi_dung: 'Em chọn: Đúng' })}
              >
                Đúng
              </Button>
              <Button
                variant="danger"
                disabled={dang_gui}
                onClick={() => onGui({ dap_an_nhap: 'Sai', noi_dung: 'Em chọn: Sai' })}
              >
                Sai
              </Button>
            </div>
          )}
        </>
      ) : (
        <p className="text-sm text-muted">Đã xét xong các mệnh đề.</p>
      )}
    </div>
  )
}
