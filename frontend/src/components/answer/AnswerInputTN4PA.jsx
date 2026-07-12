import { useState } from 'react'
import { Button } from '../ui'
import Formula from '../Formula'

function renderPA(text) {
  return String(text)
    .split(/(\$[^$]+\$)/g)
    .map((p, i) =>
      p.startsWith('$') ? <Formula key={i} latex={p.slice(1, -1)} /> : <span key={i}>{p}</span>
    )
}

export default function AnswerInputTN4PA({ phuong_an = {}, onGui, dang_gui }) {
  const [chon, setChon] = useState(null)
  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-1 gap-2">
        {Object.entries(phuong_an).map(([k, v]) => (
          <button
            key={k}
            onClick={() => setChon(k)}
            className={`flex items-center gap-2 rounded-md border px-3 py-2.5 text-left transition-colors ${
              chon === k ? 'border-primary bg-primary-soft' : 'border-border hover:bg-surface-2'
            }`}
          >
            <span className="font-semibold text-primary">{k}.</span>
            <span>{renderPA(v)}</span>
          </button>
        ))}
      </div>
      <Button disabled={!chon || dang_gui}
        onClick={() => onGui({ dap_an_nhap: chon, noi_dung: `Em chọn: ${chon}` })}>
        Gửi đáp án
      </Button>
    </div>
  )
}
