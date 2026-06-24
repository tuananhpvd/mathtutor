import ChatBubble from './ui/ChatBubble'

// Danh sách bong bóng hội thoại. turns: [{ vai_tro, noi_dung }]
export default function ChatPanel({ turns }) {
  return (
    <div className="flex flex-col gap-3 overflow-y-auto">
      {turns.map((t, i) => (
        <ChatBubble key={i} vai_tro={t.vai_tro} text={t.noi_dung} />
      ))}
    </div>
  )
}
