-- Dọn phiên học lỗi (noi_dung sai định dạng) của 2 tài khoản demo dựng bằng script cũ trước
-- khi sửa lỗi 2026-08-08. CHỈ nhắm đúng hoc_sinh_id 16 (hsdemo_dahoc) và 17 (hsdemo_danglam)
-- — không đụng bất kỳ tài khoản/dữ liệu nào khác. Gói trong transaction để tự rollback nếu
-- có lỗi giữa chừng.
BEGIN;

-- Xác nhận đúng 2 tài khoản trước khi xoá bất cứ gì (dừng cả transaction nếu không khớp).
DO $$
DECLARE
    dn16 text;
    dn17 text;
BEGIN
    SELECT dang_nhap INTO dn16 FROM users WHERE id = 16;
    SELECT dang_nhap INTO dn17 FROM users WHERE id = 17;
    IF dn16 IS DISTINCT FROM 'hsdemo_dahoc' OR dn17 IS DISTINCT FROM 'hsdemo_danglam' THEN
        RAISE EXCEPTION 'ID khong khop ten dang nhap mong doi (16=%, 17=%) - dung lai!', dn16, dn17;
    END IF;
END $$;

DELETE FROM yeu_cau_tro_giup WHERE hoc_sinh_id IN (16, 17);
DELETE FROM flags WHERE session_id IN (SELECT id FROM sessions WHERE hoc_sinh_id IN (16, 17))
                     OR turn_id IN (SELECT id FROM turns WHERE session_id IN (
                         SELECT id FROM sessions WHERE hoc_sinh_id IN (16, 17)));
DELETE FROM turns WHERE session_id IN (SELECT id FROM sessions WHERE hoc_sinh_id IN (16, 17));
DELETE FROM sessions WHERE hoc_sinh_id IN (16, 17);
DELETE FROM phan_tich_hs WHERE hoc_sinh_id IN (16, 17);
DELETE FROM progress WHERE hoc_sinh_id IN (16, 17);
DELETE FROM cot_moc WHERE hoc_sinh_id IN (16, 17);

-- In ra số dòng còn lại (phải = 0 hết) để xác nhận ngay trong output trước khi COMMIT.
SELECT 'sessions' AS bang, count(*) FROM sessions WHERE hoc_sinh_id IN (16, 17)
UNION ALL
SELECT 'turns', count(*) FROM turns WHERE session_id IN (SELECT id FROM sessions WHERE hoc_sinh_id IN (16, 17))
UNION ALL
SELECT 'flags', count(*) FROM flags WHERE session_id IN (SELECT id FROM sessions WHERE hoc_sinh_id IN (16, 17))
UNION ALL
SELECT 'phan_tich_hs', count(*) FROM phan_tich_hs WHERE hoc_sinh_id IN (16, 17)
UNION ALL
SELECT 'progress', count(*) FROM progress WHERE hoc_sinh_id IN (16, 17)
UNION ALL
SELECT 'cot_moc', count(*) FROM cot_moc WHERE hoc_sinh_id IN (16, 17);

COMMIT;
