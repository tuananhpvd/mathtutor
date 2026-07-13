// Nhận diện thương hiệu dùng chung: logo trong "chip" trắng bo tròn + wordmark "MathTutor".
// Dùng ở trang Đăng nhập (panel thương hiệu + header mobile) và trang Bảo trì — để 2 nơi luôn
// đồng bộ, sửa 1 chỗ áp cả hai. Đặt logo trong chip trắng để logo màu LUÔN nổi rõ dù nền tối
// (gradient indigo) hay sáng. `onDark`: true → chữ trắng (trên nền tối); false → chữ mực.
const SIZE = {
  sm: { chip: 'h-9 w-9 p-1 rounded-lg', ten: 'text-lg' },
  md: { chip: 'h-12 w-12 p-1.5 rounded-xl', ten: 'text-2xl' },
  lg: { chip: 'h-16 w-16 p-2 rounded-2xl', ten: 'text-3xl' },
}

export default function ThuongHieu({ size = 'md', onDark = true, className = '' }) {
  const s = SIZE[size]
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className={`bg-white shadow-sm shrink-0 ${s.chip}`}>
        <img src="/logomt.png" alt="MathTutor" className="h-full w-full object-contain" />
      </div>
      <span className={`font-bold tracking-tight ${s.ten} ${onDark ? 'text-white' : 'text-ink'}`}>
        MathTutor
      </span>
    </div>
  )
}
