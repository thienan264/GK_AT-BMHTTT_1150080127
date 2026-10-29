# Mã hoá lai cho trao đổi tệp

Nguyên mẫu chạy cục bộ với giao diện web: AES-256-GCM mã hoá nội dung, RSA-2048-OAEP SHA-256 bọc khoá AES, RSA-PSS SHA-256 xác thực gói theo khoá Alice đã tin cậy. Khoá RSA lưu trong keystore PKCS#12 có mật khẩu.

## Chạy demo

Yêu cầu JDK 21, Maven, Python 3 và OpenSSL. Tại thư mục dự án:

```sh
mvn clean test
python3 scripts/demo.py init
python3 scripts/demo.py run
```

`init` chỉ chạy một lần để tạo khoá Alice/Bob và yêu cầu mật khẩu ít nhất 12 ký tự. Nếu đã có `.local-keys`, bỏ qua `init`; dùng lại bộ khoá và mật khẩu cũ. Không ghi đè, không xoá khoá để khởi động lại.

Mở **http://127.0.0.1:8080**. Không cần chứng thư TLS hoặc thao tác Keychain. Giữ terminal chạy, nhấn Ctrl+C để dừng. Ứng dụng chỉ bind `127.0.0.1`; không dùng để phục vụ máy khác qua mạng.

Khoá trong `.local-keys/` không đưa vào Git hoặc bản nộp. Public key nằm trong `.cer`; private key trong `.p12`. Sao lưu keystore có bảo vệ; quên mật khẩu hoặc mất khoá có thể mất khả năng giải mã tệp cũ.

## Kiểm thử

```sh
python3 scripts/verify_data.py
mvn clean test
python3 scripts/check_upgrade.py
```

157 kiểm thử JUnit kiểm tra các primitive, cấu trúc gói, giả mạo/sửa đổi, chữ ký và giải nén. `check_upgrade.py` tự tạo khoá tạm, kiểm tra HTTP loopback, chặn Host/Origin không hợp lệ, tách vai trò, nhập public key và đọc gói sau hai lần khởi động; không thay khoá của bạn.

Tab kiểm thử trên web chạy 140 ca AES/OAEP. Đây là đối chiếu dữ liệu sinh cục bộ bằng công cụ NIST, không phải chứng nhận NIST cho toàn hệ thống. Bằng chứng nguồn lịch sử được giữ nguyên; bản snapshot `.java.txt` chỉ phục vụ kiểm tra nguồn cũ trước khi bỏ chú thích.

## Tài liệu

- `docs/03_Hoan_thien_va_thuyet_trinh.md` và `.docx`: quy trình, demo, giới hạn, hướng phát triển.
- `docs/04_On_tap_RSA_PSS.md`: ôn PSS, salt, fingerprint và sơ đồ từng byte.
- `presentation/Ma_hoa_lai_Nhom_4_nguoi_5_phut.pptx`: bản trình bày nhóm 4 người, 7 slide chính và 2 slide dự phòng ẩn.
- `docs/05_Kich_ban_nhom_4_nguoi_5_phut.docx`: lời nói cho 3 lượt 60 giây và kịch bản demo 120 giây.
- `presentation/1150080127_Bao_cao_GK.pptx`: bản nền dùng để tạo lại slide, không phải trạng thái hiện tại.
- `artifacts/local-verification/`: bằng chứng kiểm thử bản HTTP cục bộ.
- `artifacts/run-20261017T154209Z/`: số đo SECP v1 lịch sử, chưa gồm chữ ký PSS.

Tạo tài liệu NIST: `python3 scripts/create_documents.py`. Tạo slide nhóm và kịch bản: `python3 scripts/create_team_presentation.py`.
Tạo bộ đo SECP v1 mới: `sh scripts/run_midterm.sh`.
Tạo bản nộp không chứa khoá cá nhân hoặc bài LAB9: `python3 scripts/package_submission.py`.

## Phạm vi bảo vệ và hướng phát triển

Máy và người vận hành được tin cậy. Combined mô phỏng Alice/Bob trong cùng tiến trình; không có đăng nhập nhiều người dùng. Private key ở RAM khi dùng. Chữ ký hợp lệ không bảo đảm tệp sạch mã độc. Chưa có chống replay, thu hồi/luân chuyển khoá tự động hoặc forward secrecy.

Hướng 1: đóng gói thành ứng dụng desktop, xử lý tệp và khoá trên từng máy, chỉ gửi gói đã mã hoá và ký.
Hướng 2: nếu triển khai hệ thống nội bộ có gửi dữ liệu qua mạng tới server, bổ sung HTTPS/TLS, xác thực và phân quyền. Server thực hiện giải mã vẫn có thể đọc bản rõ. HTTP hiện tại chỉ dành cho loopback, không bảo vệ dữ liệu truyền qua LAN/Internet.
