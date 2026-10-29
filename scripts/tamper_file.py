#!/usr/bin/env python3
"""
Kịch bản can thiệp bit (Bit-flipping Attack Tool) cho Đồ án ATBM Giữa kỳ.
Sinh viên thực hiện: Trần Phạm Thiên Ân - MSSV: 1150080127

Cách dùng:
    python3 scripts/tamper_file.py <input.secpkg> [output.secpkg]
"""

import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Sử dụng: python3 scripts/tamper_file.py <file.secpkg> [file_tampered.secpkg]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace(".secpkg", "_tampered.secpkg")

    if not os.path.exists(input_file):
        print(f"❌ Không tìm thấy tệp: {input_file}")
        sys.exit(1)

    with open(input_file, "rb") as f:
        data = bytearray(f.read())

    if len(data) < 20:
        print("❌ Tệp quá nhỏ, không đúng cấu trúc .secpkg!")
        sys.exit(1)

    # Byte cuối: chữ ký PSS với SSP2 mới, tag GCM với SECP v1.
    target_offset = len(data) - 1
    orig_byte = data[target_offset]
    
    # Thực hiện phép toán đảo 1 bit nhỏ nhất (XOR 0x01)
    flipped_byte = orig_byte ^ 0x01
    data[target_offset] = flipped_byte

    with open(output_file, "wb") as f:
        f.write(data)

    print("=" * 70)
    print("😈 CÔNG CỤ CAN THIỆP BIT NHỊ PHÂN THỰC TẾ (MANUAL BIT-FLIPPING)")
    print(f"📄 Tệp gốc:             {input_file} ({len(data)} bytes)")
    print(f"🎯 Vị trí can thiệp:     Byte cuối cùng (Offset: {target_offset})")
    print(f"🔍 Byte gốc:            0x{orig_byte:02X} ({orig_byte:08b}b)")
    print(f"⚡ Byte sau khi lật bit: 0x{flipped_byte:02X} ({flipped_byte:08b}b) [XOR 00000001b]")
    print(f"💾 Tệp giả mạo đã tạo:  {output_file}")
    print("=" * 70)
    print("👉 Hãy nạp tệp giả mạo này vào ô giải mã của Bob trên Web để xem cảnh báo!")

if __name__ == "__main__":
    main()

