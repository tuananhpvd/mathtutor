import { useEffect, useRef } from 'react'
import DOMPurify from 'dompurify'
import renderMathInElement from 'katex/contrib/auto-render'
import 'katex/dist/katex.min.css'

/* Hiển thị nội dung tóm tắt lý thuyết — noiDung là HTML do SoanRichText.jsx (TipTap) sinh ra.
   2 bước bắt buộc trước khi đưa ra màn hình:
   1) DOMPurify.sanitize — GV soạn qua RTE nên trên đường thường sẽ luôn là HTML sạch, nhưng
      API vẫn nhận HTML thô từ client → PHẢI khử trùng phòng trường hợp ai đó gọi thẳng API
      (bỏ qua giao diện soạn) chèn <script>/onerror=... — không tin ngược từ FE.
   2) katex/contrib/auto-render — quét DOM đã render, thay mọi đoạn $...$ bằng công thức KaTeX
      thật (cùng quy ước $...$ dùng chung toàn app, không cần node công thức riêng trong TipTap).
   Dùng chung cho khung xem trước lúc GV soạn lẫn trang HS xem lại. */
export default function NoiDungLyThuyet({ noiDung }) {
  const ref = useRef(null)

  useEffect(() => {
    if (!ref.current) return
    try {
      renderMathInElement(ref.current, {
        delimiters: [{ left: '$', right: '$', display: false }],
        throwOnError: false,
      })
    } catch {
      // Công thức lỗi cú pháp không được làm sập cả trang — bỏ qua, phần còn lại vẫn hiện.
    }
  }, [noiDung])

  return (
    <div
      ref={ref}
      className="text-sm text-ink leading-relaxed [&_h2]:text-lg [&_h2]:font-bold [&_h2]:text-ink
        [&_h2]:mt-2 [&_h2]:mb-1 [&_h3]:text-base [&_h3]:font-bold [&_h3]:text-ink [&_h3]:mt-2
        [&_h3]:mb-1 [&_p]:mb-2 [&_img]:max-w-full [&_img]:rounded-md [&_img]:border
        [&_img]:border-border [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:mb-2 [&_ol]:list-decimal
        [&_ol]:pl-5 [&_ol]:mb-2 [&_blockquote]:border-l-4 [&_blockquote]:border-primary/40
        [&_blockquote]:pl-3 [&_blockquote]:text-muted"
      dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(noiDung || '') }}
    />
  )
}
