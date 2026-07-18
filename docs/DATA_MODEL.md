# DATA_MODEL.md — Mô hình dữ liệu & dữ liệu mẫu (v3)

Ánh xạ từ mục 4 đặc tả v3. Dùng SQLAlchemy. Dev/test SQLite, đích PostgreSQL.

> ⚠️ **Nguồn sự thật về schema là code, KHÔNG phải file này.** Các bảng mục 1–8 dưới đây mô tả
> **LÕI sư phạm** (dựng ở Phase 0, ổn định) và chỉ liệt kê **cột cốt lõi để hiểu nghiệp vụ** —
> không phải mọi cột hiện tại (nhiều cột thêm dần qua các phiên: `sessions` có thêm
> `tong_so_lan_sai`, `diem_qua_trinh`, `so_lan_het_goi_y`, `thoi_gian_hoat_dong_giay`...;
> `users` có `lop_id`, `la_quan_ly`...). Khi cần schema ĐẦY ĐỦ & CHÍNH XÁC HÔM NAY:
> - **`backend/app/models/*.py`** — 1 file/nhóm bảng, tên khớp bảng, luôn đúng.
> - **Alembic baseline** `backend/alembic/versions/2929ecbc70fc_*.py` — toàn bộ schema hiện tại
>   dưới dạng code chạy được (mọi bảng + cột + FK + index).
>
> Ngoài 8 bảng lõi, dự án còn **12 nhóm bảng mở rộng** (nhiệm vụ, mục tiêu, đề thi, thông báo,
> trợ giúp...) — xem mục 13 cuối file.

## 1. `users`
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| id | PK | |
| vai_tro | enum | `admin` / `gv` / `hs` |
| ho_ten | str | |
| dang_nhap | str unique | tên đăng nhập |
| mat_khau_hash | str | bcrypt |
| trang_thai | enum | `hoat_dong` / `khoa` |

## 2. `lop`
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| id | PK | |
| ten | str | |
| gv_id | FK users | giáo viên phụ trách |

HS gắn `lop_id` (FK) để GV theo dõi. Quan hệ HS–lớp–GV phục vụ phân quyền theo dõi tiến bộ.

## 3. `problems`
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| id | PK | |
| chuyen_de | str | "Khảo sát hàm số" / "Nguyên hàm - Tích phân" / "Xác suất" |
| loai_cau | enum | `TN4PA` / `TNDS` / `TLN` |
| do_kho | enum | `de` / `tb` / `kho` |
| de_bai | text (LaTeX) | đề / ngữ cảnh chung |
| hinh_anh | str, null được | URL `/uploads/<file>` — ảnh minh họa (tùy chọn, tối đa 1/câu). GV upload/dán clipboard, hoặc tự vẽ (đồ thị/BBT bằng CAS — xem `app/core/ve_hinh.py`) rồi xuất PNG. HS xem ở cột phải màn làm bài. |
| loai_dap_an_nhap | enum | `chon_phuong_an` / `dung_sai_4y` / `gia_tri` |
| che_do_so_khop | enum | `tuong_duong` (chấp nhận mọi dạng) / `dung_dang` (yêu cầu đúng dạng) |
| trang_thai_duyet | enum | `cho_duyet` / `da_duyet` / `loai` |
| nguon | enum | `gv_nhap` / `ai_sinh` |
| nguoi_tao_id | FK users | |
| meta | json | trường riêng theo loại (xem dưới) |

Trường riêng trong `meta`:
- **TN4PA**: `{"phuong_an":{"A":"...","B":"...","C":"...","D":"..."}, "dap_an_dung":"B"}`
- **TNDS**: `{"y":[{"ky_hieu":"a","noi_dung_y":"...","dap_an":"Dung","loi_giai_y":"..."}, ...4 ý]}`
- **TLN**: `{"dap_an_cuoi":"20","quy_tac_lam_tron":null,"don_vi":null}`
- **hinh_spec** (mọi loại câu, tùy chọn): `{"loai":"do_thi"|"bang_bien_thien","bieu_thuc":"x^3-3*x+1","x_min":..,"x_max":..}`
  — lưu lại hàm số đã dùng để tự vẽ `hinh_anh`, để GV mở "Vẽ lại" sửa tiếp mà không cần nhập lại.

## 4. `solution_steps` (gợi ý linh hoạt dạng Ý CHÍNH)
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| id | PK | |
| problem_id | FK | |
| thu_tu | int | |
| pham_vi | str | `ca_bai` hoặc `a`/`b`/`c`/`d` (TNDS) |
| mo_ta | text | ý chính của bước (nội bộ) |
| bieu_thuc_ket_qua | str (rỗng được) | kết quả trung gian (cú pháp SymPy) để CAS đối chiếu |
| danh_sach_goi_y | json (mảng chuỗi) | **danh sách Ý CHÍNH theo thứ tự tăng dần mức trợ giúp; SỐ PHẦN TỬ KHÔNG CỐ ĐỊNH** (la bàn cho LLM, không phải câu thoại) |

**Phương án C — số gợi ý linh hoạt:** `so_goi_y` = `len(danh_sach_goi_y)`, thay đổi theo từng
bước. Mặc định thông minh khi tạo bài (GV hoặc AI sinh): câu `de`→2, `tb`→3, `kho`→4 gợi ý;
GV thêm/bớt khi soạn (khuyến nghị 1–5). Orchestrator đọc độ dài danh sách của bước hiện tại,
KHÔNG hard-code 3. Gợi ý cuối là mức mạnh nhất nhưng vẫn không đọc kết quả.

Ràng buộc: mọi phần tử trong `danh_sach_goi_y` không chứa `bieu_thuc_ket_qua`/`dap_an_cuoi`
(có test kiểm, Phase 5).

## 5. `sessions` (hỗ trợ khôi phục để làm tiếp)
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| id | PK | |
| hoc_sinh_id | FK users | |
| problem_id | FK | |
| trang_thai | enum | `dang_lam` / `hoan_thanh` / `bo_do` |
| buoc_hien_tai | int | |
| y_hien_tai | str/null | TNDS: ý đang xét |
| trang_thai_y | json/null | TNDS: {"a":"xong","b":"dang_lam",...} |
| cap_goi_y_hien_tai | int | 0..3 |
| so_lan_sai_lien_tiep | int | |
| so_lan_khong_hieu | int | |
| cap_nhat_luc | datetime | để khôi phục đúng trạng thái |

## 6. `turns`
session_id, vai_tro (`hoc_sinh`/`gia_su`), noi_dung, dap_an_nhap, ket_qua_so_khop (json),
cap_goi_y, co_bi_chot_chan (bool), thoi_diem.

## 7. `flags`
session_id, loai_co (`khong_hieu_nhieu`/`chot_chan_nhieu`/`an_toan_bao_dong`), thoi_diem,
da_xu_ly (bool), ghi_chu_gv (text).

## 8. `progress`
hoc_sinh_id, chuyen_de, so_bai_lam, so_bai_hoan_thanh, ty_le_dung_trung_binh, cap_nhat_luc.
Phục vụ bảng tiến độ HS và theo dõi của GV.

## 9. Tài khoản seed — `data/seed/users.json`
4 tài khoản mẫu: `admin/admin123`, `gv1/gv123`, `hs1/hs123`, `quanly/quanly123` (GV quản lý).
Seed hash mật khẩu khi nạp. **CHỈ dùng cho local/dev (SQLite).**

> ⚠️ Từ v120: trên **production (Postgres) rỗng**, `init_db()` KHÔNG seed các tài khoản mật
> khẩu công khai này (chúng nằm trong repo GitHub) — chỉ tạo 1 admin mật khẩu NGẪU NHIÊN in ra
> log khởi động một lần. Xem `backend/app/db/init_db.py`.

## 10. Bài mẫu — `data/seed/problems.json` (1 bài mỗi loại, ý gợi ý dạng Ý CHÍNH)

### 10.1. TLN (làm trước — lát cắt dọc Phase 2)
```json
{
  "chuyen_de":"Khảo sát hàm số", "loai_cau":"TLN", "do_kho":"tb",
  "de_bai":"Tìm giá trị lớn nhất của hàm số $f(x)=x^3-3x+2$ trên đoạn $[0;3]$.",
  "loai_dap_an_nhap":"gia_tri", "che_do_so_khop":"tuong_duong",
  "meta":{"dap_an_cuoi":"20","quy_tac_lam_tron":null,"don_vi":null},
  "solution_steps":[
    {"thu_tu":1,"pham_vi":"ca_bai","mo_ta":"Tính đạo hàm","bieu_thuc_ket_qua":"3*x**2-3",
     "danh_sach_goi_y":["hỏi HS để tìm GTLN trên đoạn cần xét gì",
                        "gợi HS bắt đầu bằng tính đạo hàm",
                        "nhắc quy tắc đạo hàm từng hạng tử, để HS tự ghép"]},
    {"thu_tu":2,"pham_vi":"ca_bai","mo_ta":"Giải f'(x)=0 trong [0;3]","bieu_thuc_ket_qua":"1",
     "danh_sach_goi_y":["hỏi điểm tới hạn xuất hiện khi nào",
                        "gợi giải f'(x)=0 rồi lọc nghiệm thuộc đoạn",
                        "nhắc giữ nghiệm thuộc [0;3], để HS tự chọn"]},
    {"thu_tu":3,"pham_vi":"ca_bai","mo_ta":"So sánh giá trị tại đầu mút và điểm tới hạn",
     "bieu_thuc_ket_qua":"20",
     "danh_sach_goi_y":["hỏi GTLN nằm trong giá trị tại những điểm nào",
                        "gợi tính giá trị tại các mốc rồi so sánh",
                        "nhắc so sánh các giá trị vừa tính, để HS tự chọn lớn nhất"]}
  ]
}
```
Ghi chú: bài `tb` → mặc định 3 gợi ý mỗi bước.

### 10.2. TN4PA
```json
{
  "chuyen_de":"Khảo sát hàm số","loai_cau":"TN4PA","do_kho":"de",
  "de_bai":"Hàm số $y=x^3-3x+2$ đồng biến trên khoảng nào?",
  "loai_dap_an_nhap":"chon_phuong_an","che_do_so_khop":"tuong_duong",
  "meta":{"phuong_an":{"A":"$(-1;1)$","B":"$(1;+\\infty)$","C":"$(-\\infty;0)$","D":"$(0;2)$"},
          "dap_an_dung":"B"},
  "solution_steps":[
    {"thu_tu":1,"pham_vi":"ca_bai","mo_ta":"Tính y' và xét dấu","bieu_thuc_ket_qua":"3*x**2-3",
     "danh_sach_goi_y":["hỏi đồng biến liên quan tới dấu của đại lượng nào",
                        "nhắc xét dấu y' để suy ra khoảng, để HS tự kết luận rồi đối chiếu phương án"]}
  ]
}
```
Ghi chú: bài `de` → mặc định 2 gợi ý mỗi bước.

### 10.3. TNDS (4 ý, mỗi ý có bước riêng)
```json
{
  "chuyen_de":"Khảo sát hàm số","loai_cau":"TNDS","do_kho":"kho",
  "de_bai":"Cho hàm số $f(x)=2\\cos x + x$. Xét tính đúng/sai của các mệnh đề.",
  "loai_dap_an_nhap":"dung_sai_4y","che_do_so_khop":"tuong_duong",
  "meta":{"y":[
    {"ky_hieu":"a","noi_dung_y":"$f(0)=2$","dap_an":"Dung","loi_giai_y":"f(0)=2cos0+0=2"},
    {"ky_hieu":"b","noi_dung_y":"$f'(x)=-2\\sin x+1$","dap_an":"Dung","loi_giai_y":"đạo hàm từng hạng tử"},
    {"ky_hieu":"c","noi_dung_y":"Nghiệm $f'(x)=0$ trên $[0;\\pi/2]$ là $\\pi/6$","dap_an":"Dung","loi_giai_y":"sinx=1/2 => x=pi/6"},
    {"ky_hieu":"d","noi_dung_y":"GTLN của $f$ trên $[0;\\pi/2]$ là $2$","dap_an":"Sai","loi_giai_y":"GTLN=sqrt(3)+pi/6>2"}
  ]},
  "solution_steps":[
    {"thu_tu":1,"pham_vi":"a","mo_ta":"Thay x=0","bieu_thuc_ket_qua":"2",
     "danh_sach_goi_y":["hỏi ý a cần tính giá trị nào","gợi xác định cần thay giá trị nào của x",
                        "gợi thay x=0","nhắc cos0=1, để HS tự tính"]},
    {"thu_tu":1,"pham_vi":"b","mo_ta":"Đạo hàm","bieu_thuc_ket_qua":"-2*sin(x)+1",
     "danh_sach_goi_y":["hỏi đạo hàm của f","gợi nhớ đạo hàm cosx và x",
                        "gợi đạo hàm từng hạng tử","nhắc d/dx(2cosx)=-2sinx"]},
    {"thu_tu":1,"pham_vi":"c","mo_ta":"Giải f'(x)=0 trên đoạn","bieu_thuc_ket_qua":"pi/6",
     "danh_sach_goi_y":["hỏi nghiệm f'(x)=0 trong đoạn","gợi cho f'(x)=0",
                        "gợi đặt -2sinx+1=0","nhắc sinx=1/2 trong [0;pi/2]"]},
    {"thu_tu":1,"pham_vi":"d","mo_ta":"So sánh GTLN với 2","bieu_thuc_ket_qua":"sqrt(3)+pi/6",
     "danh_sach_goi_y":["hỏi GTLN thật sự bằng bao nhiêu","gợi cần xét các điểm nào để tìm GTLN",
                        "gợi tính f tại điểm tới hạn và đầu mút","nhắc so f(pi/6) với 2"]}
  ]
}
```
Ghi chú: bài `kho` → mặc định 4 gợi ý mỗi bước/ý.

## 11. Điểm bậc thang TNDS (Phase 1 scoring)
Đếm số ý đúng `k`: `0→0.0, 1→0.1, 2→0.25, 3→0.5, 4→1.0`. Test đủ 5 ca.

## 12. Mặc định số gợi ý theo độ khó (Phương án C)
Khi tạo bài mới hoặc AI sinh nháp, số gợi ý mỗi bước được khởi tạo theo bảng (cấu hình được ở
khu Admin): `de→2`, `tb→3`, `kho→4`. Đây chỉ là GIÁ TRỊ KHỞI TẠO; GV chỉnh tự do (khuyến nghị
1–5) khi soạn. Orchestrator luôn đọc độ dài `danh_sach_goi_y` thực tế của bước, không giả định 3.
Lưu bảng mặc định này trong cấu hình hệ thống (bảng config Admin) để đổi mà không sửa code.

## 13. Bảng mở rộng ngoài lõi Phase 0 (thêm dần qua các phiên)

Bản đồ tổng quan — **cột chi tiết đọc ở `backend/app/models/<file>.py`** (tên file ≈ tên bảng).
Một số file chứa nhiều bảng liên quan (ghi trong ngoặc).

| Model file | Bảng | Mục đích |
|---|---|---|
| `danh_muc.py` | `chuyen_de`, `dang` | Cây phân loại **Chuyên đề → Dạng** cho bài + lý thuyết |
| `tom_tat_ly_thuyet.py` | `tom_tat_ly_thuyet` | Tóm tắt lý thuyết theo chuyên đề/dạng (HS xem khi bí, GV soạn) |
| `nhiem_vu.py` | `nhiem_vu` (+ `nhiem_vu_bai`, `nhiem_vu_hoc_sinh`) | GV giao nhiệm vụ/bài theo lớp hoặc từng HS (A3) |
| `muc_tieu.py` | `muc_tieu` | Mục tiêu học tập: HS tự đặt / GV đặt / hệ thống gợi ý theo điểm yếu (B1) |
| `de_thi.py` | `de_thi` (+ `de_thi_cau`, `bai_thi`, `de_thi_hoc_sinh`) | Đề thi thử GV tạo + bài làm/điểm của HS |
| `thong_bao.py` | `thong_bao` | Thông báo (chuông) đa loại: nhận xét, cờ, nhiệm vụ, trả lời trợ giúp... |
| `yeu_cau_tro_giup.py` | `yeu_cau_tro_giup` | HS "nhờ thầy/cô" trong bài, GV trả lời inline (A2) |
| `yeu_cau_dat_lai.py` | `yeu_cau_dat_lai` | GV xin đặt lại tiến độ 1 HS, Admin duyệt (soft-reset phiên) |
| `cot_moc.py` | `cot_moc` | Cột mốc nhẹ + chuỗi ngày học liên tiếp (streak) (C1) |
| `phan_tich.py` | `phan_tich_hs` | Phân tích năng lực HS (AI sinh định kỳ hoặc GV nhập tay) |
| `cauhinh.py` | `cau_hinh` | Cấu hình hệ thống key-value (Admin chỉnh: quota LLM, từ khóa an toàn, bảo trì, provider... — đổi không cần sửa code) |
| `llm_su_dung.py` | `llm_su_dung` | Đếm lượt gọi LLM thật mỗi ngày (phanh chi phí, quota HS/hệ thống) |

Ghi chú: `flags.loai_co` thực tế đã mở rộng so với mục 7 (`ro_ri_dap_an`, `noi_dung_khong_phu_hop`,
`ngoai_pham_vi`, `khong_hieu_nhieu`, `chot_chan_nhieu`, `thu_cong`) — xem `models/flag.py`.
