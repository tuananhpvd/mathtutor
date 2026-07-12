// Cấu trúc mặc định cho từng loại câu khi tạo mới.
export function templateTheoLoai(loai) {
  if (loai === 'TN4PA') {
    return {
      meta: { phuong_an: { A: '', B: '', C: '', D: '' }, dap_an_dung: 'A', bat_buoc_suy_luan: false },
      solution_steps: [
        { thu_tu: 1, pham_vi: 'ca_bai', mo_ta: '', bieu_thuc_ket_qua: '', danh_sach_goi_y: [''] },
      ],
    }
  }
  if (loai === 'TNDS') {
    return {
      meta: {
        y: ['a', 'b', 'c', 'd'].map((k) => ({
          ky_hieu: k, noi_dung_y: '', dap_an: 'Dung', bat_buoc_suy_luan: false,
        })),
      },
      solution_steps: ['a', 'b', 'c', 'd'].map((k) => ({
        thu_tu: 1, pham_vi: k, mo_ta: '', bieu_thuc_ket_qua: '', danh_sach_goi_y: [''],
      })),
    }
  }
  // TLN
  return {
    meta: { dap_an_cuoi: '', quy_tac_lam_tron: null, don_vi: null },
    solution_steps: [
      { thu_tu: 1, pham_vi: 'ca_bai', mo_ta: '', bieu_thuc_ket_qua: '', danh_sach_goi_y: [''] },
    ],
  }
}
