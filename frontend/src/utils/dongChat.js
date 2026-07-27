/*
 * Dựng danh sách hiển thị của khung chat phòng học: xen "dải phân cách bước" vào giữa các
 * lượt hội thoại tại đúng chỗ bước/ý chuyển.
 *
 * Vì sao cần: trước đây khung chat là một dòng phẳng — HS đọc gợi ý mà không biết nó thuộc
 * bước nào, và khi làm đúng sang bước mới cũng không có mốc nào đánh dấu. Dải phân cách đóng
 * vai trò "mốc chương hồi", chỉ xuất hiện ĐÚNG 1 LẦN tại điểm chuyển (không lặp nhãn trên
 * từng bong bóng, vốn rất nhiễu).
 *
 * Hàm thuần (không React, không API) để test được bằng vitest.
 */

// Chỉ đi TỚI, không lùi: lượt GV trả lời "Nhờ thầy/cô" được gắn theo bước hiện tại của phiên,
// nhưng lịch sử cũ (buoc = null) hoặc dữ liệu lạ vẫn có thể tạo mốc nhỏ hơn — khi đó bỏ qua
// thay vì vẽ một mốc "lùi bước" gây rối.
//
// LƯU Ý HÌNH DẠNG DỮ LIỆU (đã kiểm trên CSDL thật): với TNDS, MỌI bước đều có thu_tu = 1,
// chỉ khác pham_vi (ý a/b/c/d) — tức "buoc" KHÔNG đổi khi HS sang ý mới, chỉ "y" đổi. Nên
// không thể chỉ so sánh "buoc" (bản đầu làm vậy nên TNDS không bao giờ hiện dải phân cách).
function laBuocTienLen(moc, mocTruoc) {
  if (mocTruoc == null) return true
  if (moc.buoc !== mocTruoc.buoc) return moc.buoc > mocTruoc.buoc
  // Cùng bước: coi là tiến lên khi ý đi tới (a → b → c → d).
  if (moc.y && mocTruoc.y) return moc.y > mocTruoc.y
  return false
}

/**
 * @param turns  [{vai_tro, noi_dung, buoc, y}] — buoc/y có thể null (lượt tạo trước khi có cột)
 * @param opts   { loaiCau, tongBuoc, moTaCacBuoc }
 *   moTaCacBuoc: {"1": "Tính y′", ...} hoặc {"a": "..."} với TNDS — CHỈ chứa bước đã tới.
 * @returns mảng phần tử { kieu: 'turn', turn } | { kieu: 'phan_cach', buoc, y, nhan, moTa }
 */
export function dungDongChat(turns = [], opts = {}) {
  const { loaiCau, tongBuoc, moTaCacBuoc = {} } = opts
  const ra = []
  let mocTruoc = null

  turns.forEach((turn) => {
    const buoc = turn?.buoc ?? null
    const y = turn?.y ?? null
    // Lượt cũ chưa có dữ liệu bước → không dựng phân cách (thoái lui êm, không đoán bừa).
    if (buoc != null) {
      const moc = { buoc, y }
      const doiMoc = mocTruoc == null || moc.buoc !== mocTruoc.buoc || moc.y !== mocTruoc.y
      // TN4PA còn tăng buoc thêm 1 QUÁ số bước thật, chỉ để làm mốc mở khóa chọn đáp án —
      // đó không phải bước có nội dung, đừng vẽ mốc "BƯỚC 2" trống cho nó.
      const buocCoThat = !tongBuoc || loaiCau === 'TNDS' || buoc <= tongBuoc
      if (doiMoc && buocCoThat && laBuocTienLen(moc, mocTruoc)) {
        // Mốc đầu tiên (mocTruoc == null) KHÔNG cần phân cách: HS vừa vào bài, bước 1 đã hiện
        // sẵn ở Khu vực trả lời — thêm 1 dải "Bước 1" ngay dòng đầu chỉ tổ thừa.
        if (mocTruoc != null) {
          ra.push({ kieu: 'phan_cach', buoc, y, ...nhanPhanCach({ buoc, y, loaiCau, tongBuoc, moTaCacBuoc }) })
        }
        mocTruoc = moc
      }
    }
    ra.push({ kieu: 'turn', turn })
  })

  return ra
}

/**
 * Nhãn của dải phân cách. TNDS đi theo Ý (a/b/c/d), các loại khác đi theo BƯỚC.
 * Mô tả tra động từ moTaCacBuoc (theo bản solution_steps mới nhất) — GV sửa mô tả thì lịch
 * sử hiển thị theo bản mới. Mô tả rỗng/thiếu → chỉ hiện nhãn bước, KHÔNG để dòng trống.
 */
export function nhanPhanCach({ buoc, y, loaiCau, tongBuoc, moTaCacBuoc = {} }) {
  if (loaiCau === 'TNDS' && y) {
    return { nhan: `Ý ${y})`, moTa: (moTaCacBuoc[y] || '').trim() }
  }
  const nhan = tongBuoc ? `Bước ${buoc}/${tongBuoc}` : `Bước ${buoc}`
  return { nhan, moTa: (moTaCacBuoc[String(buoc)] || '').trim() }
}
