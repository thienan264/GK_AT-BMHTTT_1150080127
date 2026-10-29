# Ôn nhanh RSA-PSS và fingerprint

Tài liệu ghi nhớ cơ chế đã học, không yêu cầu học thuộc công thức RSA.

Các kích thước bên dưới dành riêng cho cấu hình **RSA-2048, SHA-256, MGF1-SHA-256, salt 32 byte**. Cấu hình khác có thể có kích thước khác.

## 1. Nhìn một lần để nhớ toàn bộ luồng

```text
ALICE — KÝ

Dữ liệu cần ký M
       │
       ▼ SHA-256
mHash: 32 byte                 Sinh salt ngẫu nhiên: 32 byte
       │                                  │
       └────────────────┬─────────────────┘
                        ▼
             [8 byte 0 | mHash | salt]
                        │ SHA-256
                        ▼
                    H: 32 byte
                        │
                        ├── MGF1 ──► mặt nạ: 223 byte
                        │                       │
DB = [190 byte 0 | 01 | salt] ────── XOR ────────┘
                                    │
                                    ▼
                         maskedDB: 223 byte
                         (đặt bit cao nhất về 0)
                                    │
                                    ▼
                    EM = [maskedDB | H | BC]
                                    │ RSA bằng private key Alice
                                    ▼
                          Chữ ký S: 256 byte
```

**Bob dùng public key Alice đã tin cậy để kiểm tra chữ ký. Private key Alice không được gửi cho Bob.**

## 2. Sơ đồ EM — phần quan trọng trong ảnh

```text
EM:
┌──────────────────────┬─────────────────┬───────────────────┐
│ maskedDB: 223 byte   │ H: 32 byte      │ BC: một byte      │
└──────────────────────┴─────────────────┴───────────────────┘
                       Tổng: 256 byte
```

| Thành phần | Ý nghĩa |
|---|---|
| `maskedDB` | Khối DB sau khi XOR với mặt nạ và xử lý bit theo quy định |
| `H` | SHA-256 của khối `8 byte 0 \| mHash \| salt` |
| `BC` | Một byte kết thúc cố định, giá trị hexadecimal `0xBC` |
| `EM` | Khối đã được chuẩn bị theo cấu trúc PSS, **chưa phải chữ ký** |
| `S` | Chữ ký thu được sau phép toán RSA bằng private key trên EM |

```text
EM (256 byte) ── RSA bằng private key Alice ──► S (256 byte)
```

EM và S cùng dài 256 byte trong cấu hình này nhưng là hai dãy dữ liệu khác nhau. EM không được ghép vào tệp như một trường riêng bên cạnh chữ ký; bên kiểm tra khôi phục khối cần kiểm tra từ chữ ký bằng phép toán RSA công khai.

## 3. Những tên gọi cần nhớ

**PSS — Probabilistic Signature Scheme:** cơ chế chữ ký có yếu tố ngẫu nhiên. Phần mã hoá cấu trúc PSS chuẩn bị dữ liệu; phép toán RSA với private key tạo chữ ký. Không gọi ký là “mã hoá tệp bằng private key”.

**mHash:** SHA-256 của toàn bộ dữ liệu cần ký M, dài 32 byte. Đây không phải bản tóm tắt đọc được bằng mắt và không thể dùng để khôi phục M.

**Salt:** 32 byte ngẫu nhiên mới cho mỗi lần ký trong cấu hình này. Không phải mật khẩu, private key hay IV của AES. Không cần bí mật. Cùng dữ liệu và cùng khoá nhưng salt khác thường cho chữ ký khác; cả hai vẫn có thể hợp lệ.

**MGF1:** bộ tạo mặt nạ có độ dài theo yêu cầu từ một đầu vào. Cùng đầu vào và cấu hình luôn cho cùng mặt nạ; MGF1 không tự sinh ngẫu nhiên.

**XOR:** phép xử lý từng bit: giống nhau cho 0, khác nhau cho 1. XOR hai lần với cùng mặt nạ sẽ khôi phục dữ liệu ban đầu.

## 4. Cấu trúc từng bước khi Alice ký

### Bước A — Băm dữ liệu

```text
M ── SHA-256 ──► mHash: 32 byte
```

M là toàn bộ dãy byte cần bảo vệ bằng chữ ký. Trong thiết kế đã học, M gồm chuỗi ngữ cảnh cố định, header SSP2, độ dài và gói mã hoá lai SECP; chưa gồm chính chữ ký.

### Bước B — Sinh salt và tính H

```text
┌────────────────┬─────────────────┬─────────────────┐
│ 8 byte bằng 0  │ mHash: 32 byte  │ salt: 32 byte   │
└────────────────┴─────────────────┴─────────────────┘
                      Tổng: 72 byte
                              │ SHA-256
                              ▼
                          H: 32 byte
```

Phân biệt: mHash phụ thuộc vào M; H phụ thuộc vào cả mHash và salt.

### Bước C — Dựng DB

```text
DB:
┌────────────────────────┬───────────────┬─────────────────┐
│ 190 byte bằng 0        │ 01: một byte  │ salt: 32 byte   │
└────────────────────────┴───────────────┴─────────────────┘
                       Tổng: 223 byte
```

Vùng 0 là phần đệm. `01` là byte phân cách `0x01`, không phải hai ký tự văn bản. Salt ở đây là cùng salt đã dùng để tính H.

### Bước D — Tạo và áp dụng mặt nạ

```text
H ── MGF1 với SHA-256 ──► mặt nạ: 223 byte

DB XOR mặt nạ ──► maskedDB
```

MGF1 băm `H || bộ đếm` nhiều lần, nối các kết quả rồi lấy đủ 223 byte. Bộ đếm được biểu diễn bằng 4 byte theo chuẩn. Ở đây cần 7 kết quả SHA-256 (224 byte), rồi bỏ byte cuối để còn 223 byte. Ký hiệu `||` chỉ việc nối byte, không phải một phép mã hoá.

Sau XOR, đặt bit cao nhất của maskedDB về 0. Với modulus RSA dài 2048 bit, khối PSS dùng tối đa 2047 bit để nằm trong miền đầu vào phù hợp; biểu diễn của nó vẫn dài 256 byte.

Mặt nạ không nhằm giữ bí mật DB: H có trong EM nên bên kiểm tra cũng tạo lại được mặt nạ. Đây là một phần cấu trúc của cơ chế ký an toàn.

### Bước E — Ghép EM, rồi tạo chữ ký

```text
EM = maskedDB (223) | H (32) | BC (1) = 256 byte

EM ── RSA bằng private key Alice ──► chữ ký S: 256 byte
```

Không cần tự cài đặt các bước này. Thư viện mật mã thực hiện khi gọi RSA-PSS với đúng tham số.

## 5. Bob kiểm tra theo thứ tự nào?

Bob có **M, chữ ký S và public key Alice đã xác minh**.

1. Kiểm tra chữ ký có kích thước và giá trị phù hợp; dùng phép toán RSA với public key Alice để thu được EM cần kiểm tra.
2. Tách `maskedDB | H | BC`; kiểm tra độ dài, byte BC và bit cao nhất theo quy định.
3. Dùng H tạo lại mặt nạ bằng MGF1.
4. XOR maskedDB với mặt nạ; xử lý bit cao nhất theo quy định để khôi phục DB.
5. Kiểm tra vùng đệm 0 và byte phân cách 01; lấy salt 32 byte.
6. Tự tính `mHash = SHA-256(M)` từ chính dữ liệu nhận được.
7. Tính `H_mới = SHA-256(8 byte 0 || mHash || salt)`.
8. H_mới phải khớp H trong EM, đồng thời mọi kiểm tra cấu trúc đều phải đạt.

```text
Chữ ký S ── RSA công khai ──► EM ──► lấy H và salt
                                             │
M nhận được ── SHA-256 ──► mHash              │
                              └──────┬───────┘
                                     ▼
                    Tính H_mới rồi so sánh với H
```

Bob không cần biết salt từ trước và không cần nhận salt riêng. Bob không khôi phục tệp gốc từ chữ ký; việc giải mã tệp là công đoạn khác.

## 6. Fingerprint liên quan thế nào?

```text
PUBLIC KEY ── biểu diễn DER ── SHA-256 ──► fingerprint
GÓI DỮ LIỆU ──────────────── SHA-256 ──► mHash dùng trong PSS
```

Fingerprint giúp đối chiếu đúng public key. Chữ ký giúp kiểm tra gói bằng public key đó. Fingerprint SHA-256 dài 32 byte, viết thành 64 ký tự hex chưa tính dấu hai chấm.

Phải xác nhận fingerprint qua nguồn tin cậy. Nhận cả khoá và fingerprint từ cùng nguồn có thể bị thay thế chưa chứng minh đó là khoá Alice. Fingerprint public key khác fingerprint toàn chứng thư; chỉ so sánh cùng loại.

## 7. Các tình huống để tự nhớ

| Tình huống | Điều xảy ra |
|---|---|
| Sửa dữ liệu, giữ chữ ký | Băm tính lại thay đổi; kiểm tra chữ ký thất bại với xác suất áp đảo |
| Mallory ký bằng khoá của mình | Không vượt qua kiểm tra bằng đúng public key Alice |
| Bob tin nhầm public key Mallory là Alice | Thuật toán có thể chạy đúng nhưng Bob xác thực nhầm danh tính |
| Cùng dữ liệu ký hai lần | Salt mới thường làm hai chữ ký khác nhau; đều kiểm tra được |
| Phát lại nguyên gói đã ký | Chữ ký vẫn hợp lệ; PSS không tự chống replay |
| Private key Alice bị đánh cắp | Người lấy được có thể ký; chữ ký không chứng minh ai đang dùng khoá |
| Tệp có chữ ký hợp lệ | Không có nghĩa tệp sạch mã độc |

## 8. Nối với mã hoá lai

```text
Alice: mã hoá lai cho Bob → ký gói bằng private key Alice
Bob: kiểm tra bằng public key Alice → mở AES bằng private key Bob
                                   → xác thực/giải mã GCM → khôi phục tệp
```

**RSA-OAEP của Bob bảo vệ khoá AES. RSA-PSS của Alice xác thực nguồn ký theo khoá đã tin cậy. AES-GCM bảo vệ nội dung và toàn vẹn.**

Nguồn đối chiếu: [RFC 8017, mục 8.1 (RSASSA-PSS), 9.1 (cấu trúc PSS) và B.2.1 (MGF1)](https://www.rfc-editor.org/rfc/rfc8017.html).
