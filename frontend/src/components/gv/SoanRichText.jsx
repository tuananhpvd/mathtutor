import { useEffect } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import { Bold, Italic, Heading2, List, ListOrdered, Quote, ImagePlus } from 'lucide-react'
import { api } from '../../api'
import MathPalette from '../answer/MathPalette'

/* Trình soạn thảo văn bản (Rich Text Editor) nhỏ gọn — TipTap + StarterKit + Image.
   Công thức toán vẫn gõ trong cặp $...$ (dạng chữ thường trong nội dung, không phải node
   riêng) — giữ đúng quy ước KaTeX dùng chung toàn app; NoiDungLyThuyet.jsx render lại bằng
   katex/contrib/auto-render khi hiển thị. Lưu/đọc dạng HTML (editor.getHTML()). */

function NutToolbar({ active, disabled, onClick, title, children }) {
  return (
    <button type="button" title={title} disabled={disabled} onClick={onClick}
      className={`grid h-8 w-8 place-items-center rounded-md border transition-colors
        ${active ? 'border-primary bg-primary-soft text-primary' : 'border-border text-ink hover:bg-surface-2'}
        disabled:opacity-40 disabled:cursor-not-allowed`}>
      {children}
    </button>
  )
}

export default function SoanRichText({ value, onChange }) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Image.configure({ HTMLAttributes: { class: 'max-w-full rounded-md border border-border' } }),
    ],
    content: value || '',
    editorProps: {
      attributes: {
        class: 'min-h-[380px] max-h-[520px] overflow-y-auto rounded-b-lg border border-t-0 ' +
          'border-border bg-surface px-3.5 py-3 text-sm text-ink leading-relaxed focus:outline-none ' +
          '[&_h2]:text-lg [&_h2]:font-bold [&_h2]:text-ink [&_h2]:mt-2 [&_h2]:mb-1 ' +
          '[&_h3]:text-base [&_h3]:font-bold [&_h3]:text-ink [&_h3]:mt-2 [&_h3]:mb-1 ' +
          '[&_p]:mb-2 [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:mb-2 [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:mb-2 ' +
          '[&_blockquote]:border-l-4 [&_blockquote]:border-primary/40 [&_blockquote]:pl-3 [&_blockquote]:text-muted',
      },
    },
    onUpdate: ({ editor: e }) => onChange(e.getHTML()),
    immediatelyRender: false,
  })

  // Đồng bộ khi mở form ở chế độ Sửa (value đổi từ ngoài, vd load xong dữ liệu tóm tắt cần sửa)
  // — chỉ set lại khi nội dung thực sự khác, tránh vòng lặp/mất vị trí con trỏ lúc gõ.
  useEffect(() => {
    if (!editor) return
    if (value !== editor.getHTML()) editor.commands.setContent(value || '', { emitUpdate: false })
  }, [editor, value])

  async function chenAnh(e) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || !editor) return
    try {
      const { url } = await api.uploadHinh(file)
      editor.chain().focus().setImage({ src: url }).run()
    } catch {
      // Lỗi upload không chặn soạn thảo — GV thử lại được ngay.
    }
  }

  // Adapter cho MathPalette (cùng kiểu getMf() dùng ở MixedChatInput — ô "Nhờ thầy/cô"):
  // mỗi lần chèn tự bọc $...$ quanh công thức, GV không cần tự gõ dấu $.
  function getMf() {
    if (!editor) return null
    return {
      focus() { editor.commands.focus() },
      insert(latex) {
        const clean = latex.replace(/\\placeholder\{\}/g, '')
        editor.chain().focus().insertContent(`$${clean}$`).run()
      },
      executeCommand(cmd) {
        if (cmd !== 'deleteBackward') return
        const { from } = editor.state.selection
        if (from <= 0) return
        editor.chain().focus().deleteRange({ from: from - 1, to: from }).run()
      },
    }
  }

  if (!editor) return null

  return (
    <div>
      <div className="flex items-center gap-1 rounded-t-lg border border-border bg-surface-2/60 px-2 py-1.5 flex-wrap">
        <NutToolbar title="In đậm" active={editor.isActive('bold')}
          onClick={() => editor.chain().focus().toggleBold().run()}><Bold size={15} /></NutToolbar>
        <NutToolbar title="In nghiêng" active={editor.isActive('italic')}
          onClick={() => editor.chain().focus().toggleItalic().run()}><Italic size={15} /></NutToolbar>
        <NutToolbar title="Tiêu đề" active={editor.isActive('heading', { level: 2 })}
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}><Heading2 size={15} /></NutToolbar>
        <NutToolbar title="Danh sách gạch đầu dòng" active={editor.isActive('bulletList')}
          onClick={() => editor.chain().focus().toggleBulletList().run()}><List size={15} /></NutToolbar>
        <NutToolbar title="Danh sách đánh số" active={editor.isActive('orderedList')}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}><ListOrdered size={15} /></NutToolbar>
        <NutToolbar title="Trích dẫn" active={editor.isActive('blockquote')}
          onClick={() => editor.chain().focus().toggleBlockquote().run()}><Quote size={15} /></NutToolbar>
        <label className="grid h-8 w-8 cursor-pointer place-items-center rounded-md border border-border
          text-ink hover:bg-surface-2" title="Chèn ảnh tại vị trí con trỏ">
          <input type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={chenAnh} />
          <ImagePlus size={15} />
        </label>
      </div>
      <EditorContent editor={editor} />
      <div className="mt-2">
        <p className="text-[11px] text-muted mb-1.5">
          Bấm ký hiệu để chèn công thức — tự động bọc trong <b>$...$</b>.
        </p>
        <MathPalette getMf={getMf} onInserted={() => {}} />
      </div>
    </div>
  )
}
