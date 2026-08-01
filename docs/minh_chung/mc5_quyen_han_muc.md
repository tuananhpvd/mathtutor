# MC-5 — Ma trận kiểm thử quyền/hạn mức

**30/30 ca đúng cấu hình** (chạy lại thật qua subprocess pytest, không suy đoán).

## `test_monitor_idor.py` — Chống truy cập chéo dữ liệu (IDOR) — cờ/hội thoại/nhật ký GV (9/9)

- ✅ `test_gv_khac_khong_thay_co_cua_gv_khac`
- ✅ `test_gv_khac_khong_gan_co_cho_session_khong_thuoc`
- ✅ `test_gv_khac_khong_sua_co_cua_gv_khac`
- ✅ `test_gv_khac_khong_xem_hoi_thoai_cua_hs_khong_thuoc`
- ✅ `test_gv_khac_khong_thay_nhat_ky_hoan_thanh_cua_gv_khac`
- ✅ `test_gv_chinh_chu_van_thao_tac_binh_thuong`
- ✅ `test_admin_thay_toan_bo_khong_bi_loc`
- ✅ `test_nhat_ky_hoan_thanh_loc_theo_hoc_sinh_id`
- ✅ `test_nhat_ky_hoan_thanh_hoc_sinh_id_ngoai_pham_vi_403`

## `test_sessions_idor.py` — Chống truy cập chéo dữ liệu (IDOR) — phiên học của HS (4/4)

- ✅ `test_hs_tao_phien_bai_cua_minh_ok`
- ✅ `test_hs_khong_tao_phien_bai_gv_khac`
- ✅ `test_hs_khong_tao_phien_bai_bi_an`
- ✅ `test_hs_tao_phien_bai_duoc_giao_nhiem_vu_ok`

## `test_llm_quota.py` — Hạn mức sử dụng AI theo HS/hệ thống + suy giảm khi hết hạn mức (13/13)

- ✅ `test_ghi_luot_cong_don`
- ✅ `test_ghi_luot_so_khong_duong_bo_qua`
- ✅ `test_vuot_nguong_hs_va_he_thong`
- ✅ `test_gioi_han_0_la_khong_gioi_han`
- ✅ `test_gioi_han_gia_tri_rac_coi_nhu_khong_gioi_han`
- ✅ `test_hoi_thoai_stub_khong_dem_khong_gioi_han`
- ✅ `test_hoi_thoai_llm_that_dem_va_thay_stub_khi_vuot`
- ✅ `test_hoi_thoai_vuot_nguong_he_thong_cung_thay_stub`
- ✅ `test_tac_vu_vuot_nguong_tra_none`
- ✅ `test_tac_vu_stub_di_qua_khong_dem`
- ✅ `test_endpoint_llm_su_dung_chi_admin`
- ✅ `test_sinh_cau_hoi_429_khi_het_quota`
- ✅ `test_thong_ke_su_dung_du_truong`

## `test_config_safety.py` — An toàn cấu hình bí mật (JWT_SECRET, DATABASE_URL production) (4/4)

- ✅ `test_chan_postgres_voi_secret_mac_dinh`
- ✅ `test_chan_postgres_voi_secret_mau_trong_env_example`
- ✅ `test_cho_phep_postgres_voi_secret_rieng`
- ✅ `test_cho_phep_sqlite_du_secret_mac_dinh`

