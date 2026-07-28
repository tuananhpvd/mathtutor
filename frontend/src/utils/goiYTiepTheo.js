/*
 * Chọn dạng bài nên luyện tiếp cho màn hình "Hoàn thành bài" (khép vòng học tập, tránh
 * HS phải tự sang trang Chọn bài mới thấy gợi ý). Dùng LẠI đúng nguồn dữ liệu của thẻ
 * "Gợi ý cho em" (trang Chọn bài) — không phải một luồng tính gợi ý mới.
 *
 * Hàm thuần (không React, không API) để test được bằng vitest.
 */

/**
 * @param pt  kết quả api.getPhanTichMe() — { diem_yeu: [{ten, chuyen_de, dang_id, diem_thanh_thao}, ...] }
 * @returns dòng diem_yeu đầu tiên có dang_id hợp lệ, hoặc null nếu chưa đủ dữ liệu để gợi ý
 *   (HS mới, hoặc dạng yếu không gắn được dang_id để điều hướng tới).
 */
export function baiNenLuyenTiep(pt) {
  const r = pt?.diem_yeu?.[0]
  if (!r || !r.dang_id) return null
  return r
}
