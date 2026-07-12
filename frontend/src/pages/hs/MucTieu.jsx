import { api } from '../../api'
import MucTieuPanel from '../../components/MucTieuPanel'

export default function MucTieu() {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h2 className="text-xl font-semibold text-black">Mục tiêu của em</h2>
        <p className="text-black/90 text-sm mt-1">
          Đặt mục tiêu theo tuần hoặc theo chủ đề để luyện tập có định hướng và theo dõi tiến bộ.
        </p>
      </div>
      <MucTieuPanel
        tieuDe="🎯 Danh sách mục tiêu"
        phuDe="Em có thể tự đặt, hoặc dùng gợi ý dựa trên điểm yếu"
        taiDs={api.hsMucTieu}
        taiDeXuat={api.hsMucTieuDeXuat}
        taoMt={api.hsTaoMucTieu}
        xoaMt={api.xoaMucTieu}
        haiCot
      />
    </div>
  )
}
