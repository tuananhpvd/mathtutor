-- Rải ngày hoàn thành 7 phiên của hsdemo_dahoc (id=16) ra trong tuần 30/7 - 5/8/2026, thay vì
-- dồn hết vào 1 ngày lúc dựng lại dữ liệu demo. Giữ nguyên thời lượng làm bài (bat_dau_luc
-- cách cap_nhat_luc đúng bằng thoi_gian_giay cũ) — chỉ dịch cả cặp sang mốc mới.
-- Giờ nhập theo giờ Việt Nam (ICT = UTC+7), lưu xuống DB bằng UTC (trừ 7 giờ).
BEGIN;

DO $$
DECLARE
    dn text;
    sai_id int;
BEGIN
    SELECT dang_nhap INTO dn FROM users WHERE id = 16;
    IF dn IS DISTINCT FROM 'hsdemo_dahoc' THEN
        RAISE EXCEPTION 'ID 16 khong phai hsdemo_dahoc (la %) - dung lai!', dn;
    END IF;
    SELECT id INTO sai_id FROM sessions
        WHERE id IN (51,52,53,54,55,56,57) AND hoc_sinh_id <> 16 LIMIT 1;
    IF sai_id IS NOT NULL THEN
        RAISE EXCEPTION 'Session % khong thuoc hoc_sinh_id 16 - dung lai!', sai_id;
    END IF;
END $$;

-- Ứng dụng của đạo hàm (mạnh) — Thứ Năm 30/7 tối, Thứ Bảy 1/8 sáng
UPDATE sessions SET bat_dau_luc = '2026-07-30 12:14:58+00', cap_nhat_luc = '2026-07-30 12:15:00+00' WHERE id = 51;
UPDATE sessions SET bat_dau_luc = '2026-07-30 13:04:58+00', cap_nhat_luc = '2026-07-30 13:05:00+00' WHERE id = 52;
UPDATE sessions SET bat_dau_luc = '2026-08-01 02:39:58+00', cap_nhat_luc = '2026-08-01 02:40:00+00' WHERE id = 53;

-- Nguyên hàm và tích phân (yếu) — trải Chủ Nhật 2/8, Thứ Hai 3/8, Thứ Tư 5/8 (nghỉ 4/8)
UPDATE sessions SET bat_dau_luc = '2026-08-02 13:29:52+00', cap_nhat_luc = '2026-08-02 13:30:00+00' WHERE id = 54;
UPDATE sessions SET bat_dau_luc = '2026-08-03 14:09:54+00', cap_nhat_luc = '2026-08-03 14:10:00+00' WHERE id = 55;
UPDATE sessions SET bat_dau_luc = '2026-08-05 12:49:52+00', cap_nhat_luc = '2026-08-05 12:50:00+00' WHERE id = 56;
UPDATE sessions SET bat_dau_luc = '2026-08-05 13:39:52+00', cap_nhat_luc = '2026-08-05 13:40:00+00' WHERE id = 57;

-- Đồng bộ "cập nhật lần cuối" của bảng tiến độ theo đúng ngày mới nhất mỗi chuyên đề.
UPDATE progress SET cap_nhat_luc = '2026-08-01 02:40:00+00'
    WHERE hoc_sinh_id = 16 AND chuyen_de = 'Ứng dụng của đạo hàm';
UPDATE progress SET cap_nhat_luc = '2026-08-05 13:40:00+00'
    WHERE hoc_sinh_id = 16 AND chuyen_de = 'Nguyên hàm và tích phân';

-- In ra để xác nhận ngay trong output trước khi COMMIT.
SELECT id, hoc_sinh_id, bat_dau_luc, cap_nhat_luc
FROM sessions WHERE id IN (51,52,53,54,55,56,57) ORDER BY id;

COMMIT;
