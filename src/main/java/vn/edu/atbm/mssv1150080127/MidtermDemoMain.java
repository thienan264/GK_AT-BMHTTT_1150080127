package vn.edu.atbm.mssv1150080127;

import vn.edu.atbm.mssv1150080127.crypto.RsaKeyManager;
import vn.edu.atbm.mssv1150080127.crypto.SecurePackageEngine;
import vn.edu.atbm.mssv1150080127.model.SecurePackageResult;
import vn.edu.atbm.mssv1150080127.util.NistAcvpParser;

import javax.crypto.AEADBadTagException;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.KeyPair;
import java.util.List;
import java.util.Random;
import java.util.Scanner;

/**
 * Chương trình Demo Giữa kỳ môn An toàn & Bảo mật Hệ thống Thông tin
 * Đề tài: Quy trình mã hóa lai AES-GCM kết hợp RSA-OAEP cho trao đổi tệp
 * 
 * Sinh viên thực hiện: Trần Phạm Thiên Ân - MSSV: 1150080127
 */
public class MidtermDemoMain {

    private static KeyPair aliceKeyPair;
    private static KeyPair bobKeyPair;

    public static void main(String[] args) {
        try {
            initKeys();
            Scanner scanner = new Scanner(System.in);
            while (true) {
                printMenu();
                System.out.print("👉 Vui lòng chọn chức năng (0-4): ");
                String choice = scanner.nextLine().trim();

                switch (choice) {
                    case "1" -> demoEncryptDecrypt();
                    case "2" -> demoBitFlippingAttack();
                    case "3" -> demoNistAcvpValidation();
                    case "4" -> demoBenchmark();
                    case "0" -> {
                        System.out.println("\n👋 Cảm ơn Thầy Cô đã theo dõi buổi báo cáo Giữa kỳ!");
                        return;
                    }
                    default -> System.out.println("❌ Lựa chọn không hợp lệ, vui lòng chọn từ 0 đến 4.");
                }
                System.out.println("\nNhấn phím [Enter] để quay lại Menu...");
                scanner.nextLine();
            }
        } catch (Exception e) {
            System.err.println("❌ Đã xảy ra lỗi hệ thống: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private static void initKeys() throws Exception {
        System.out.println("================================================================================");
        System.out.println("      ĐỒ ÁN GIỮA KỲ: AN TOÀN VÀ BẢO MẬT HỆ THỐNG THÔNG TIN - MSSV: 1150080127   ");
        System.out.println("      Sinh viên: Trần Phạm Thiên Ân | Đề tài: AES-GCM kết hợp RSA-OAEP         ");
        System.out.println("================================================================================");
        System.out.print("⏳ Đang khởi tạo cặp khóa RSA-2048 cho Bên Gửi (Alice) và Bên Nhận (Bob)... ");
        aliceKeyPair = RsaKeyManager.generateKeyPair(2048);
        bobKeyPair = RsaKeyManager.generateKeyPair(2048);
        System.out.println(" [OK]");
    }

    private static void printMenu() {
        System.out.println("\n---------------------------------- MENU DEMO -----------------------------------");
        System.out.println(" [1] Demo Đóng gói & Giải mã (.secpkg) - So sánh Baseline vs Variant (GZIP)");
        System.out.println(" [2] Demo Giả lập Tấn công sửa 1 bit (Bit-flipping Attack) & Báo lỗi AEADBadTag");
        System.out.println(" [3] Demo Kiểm thử xác thực tính đúng đắn với Bộ vector chuẩn NIST ACVP");
        System.out.println(" [4] Chạy Thực nghiệm Đo hiệu năng (Benchmark 3 lần chạy) -> Xuất results.csv");
        System.out.println(" [0] Thoát chương trình");
        System.out.println("--------------------------------------------------------------------------------");
    }

    /**
     * Chức năng 1: Demo Đóng gói & Giải mã
     */
    private static void demoEncryptDecrypt() {
        try {
            System.out.println("\n>>> [CHỨC NĂNG 1] DEMO ĐÓNG GÓI VÀ GIẢI MÃ TỆP AN TOÀN");
            String sampleText = """
                    BÁO CÁO GIỮA KỲ MÔN AN TOÀN VÀ BẢO MẬT HỆ THỐNG THÔNG TIN
                    Học viên / Sinh viên: Trần Phạm Thiên Ân - MSSV: 1150080127
                    Mô hình: Mã hóa lai kết hợp AES-256-GCM và RSA-2048-OAEP.
                    Đặc tả gói tệp: .secpkg gồm Header xác thực, Khóa bọc, IV, AAD và Bản mã kèm Tag.
                    Nội dung thử nghiệm với nhiều dòng lặp lại để kiểm tra khả năng nén của Biến thể GZIP...
                    """.repeat(10);

            byte[] originalBytes = sampleText.getBytes(StandardCharsets.UTF_8);
            String filename = "sample_midterm_doc.txt";
            System.out.println("📄 Tệp thử nghiệm: " + filename + " | Kích thước gốc: " + originalBytes.length + " bytes");

            // 1. Thử nghiệm Baseline (Không nén)
            System.out.println("\n--- [A] THỰC THI BASELINE (FLAG = 0x00: Không nén) ---");
            long t1 = System.nanoTime();
            byte[] baselinePkg = SecurePackageEngine.pack(originalBytes, filename, bobKeyPair.getPublic(), false);
            long t2 = System.nanoTime();
            SecurePackageResult baselineResult = SecurePackageEngine.unpack(baselinePkg, bobKeyPair.getPrivate());
            long t3 = System.nanoTime();

            boolean baselineCorrect = sampleText.equals(new String(baselineResult.getPlainData(), StandardCharsets.UTF_8));
            System.out.printf("  + Kích thước gói .secpkg: %d bytes (Overhead: +%d bytes)\n",
                    baselinePkg.length, (baselinePkg.length - originalBytes.length));
            System.out.printf("  + Thời gian đóng gói: %.3f ms | Thời gian giải mã: %.3f ms\n",
                    (t2 - t1) / 1e6, (t3 - t2) / 1e6);
            System.out.println("  + Kiểm tra tính đúng đắn (Correctness): " + (baselineCorrect ? "✅ 100% TRÙNG KHỚP" : "❌ LỖI"));

            // 2. Thử nghiệm Biến thể (Variant: Nén GZIP trước khi mã hóa)
            System.out.println("\n--- [B] THỰC THI BIẾN THỂ (FLAG = 0x01: Nén GZIP + Mã hóa) ---");
            long t4 = System.nanoTime();
            byte[] variantPkg = SecurePackageEngine.pack(originalBytes, filename, bobKeyPair.getPublic(), true);
            long t5 = System.nanoTime();
            SecurePackageResult variantResult = SecurePackageEngine.unpack(variantPkg, bobKeyPair.getPrivate());
            long t6 = System.nanoTime();

            boolean variantCorrect = sampleText.equals(new String(variantResult.getPlainData(), StandardCharsets.UTF_8));
            double ratio = (1.0 - (double) variantPkg.length / baselinePkg.length) * 100;
            System.out.printf("  + Kích thước gói .secpkg: %d bytes (Tiết kiệm được: %.2f%% so với Baseline)\n",
                    variantPkg.length, ratio);
            System.out.printf("  + Thời gian đóng gói: %.3f ms | Thời gian giải mã: %.3f ms\n",
                    (t5 - t4) / 1e6, (t6 - t5) / 1e6);
            System.out.println("  + Kiểm tra tính đúng đắn (Correctness): " + (variantCorrect ? "✅ 100% TRÙNG KHỚP" : "❌ LỖI"));

        } catch (Exception e) {
            System.err.println("❌ Lỗi trong demo đóng gói: " + e.getMessage());
        }
    }

    /**
     * Chức năng 2: Demo Giả lập Tấn công can thiệp sửa 1 bit
     */
    private static void demoBitFlippingAttack() {
        try {
            System.out.println("\n>>> [CHỨC NĂNG 2] GIẢ LẬP TẤN CÔNG SỬA 1 BIT (BIT-FLIPPING ATTACK)");
            String secretMessage = "THÔNG TIN TÀI CHÍNH BẢO MẬT: CHUYỂN KHOẢN 10,000,000 VNĐ";
            byte[] data = secretMessage.getBytes(StandardCharsets.UTF_8);

            byte[] safePackage = SecurePackageEngine.pack(data, "chuyenkhoan.dat", bobKeyPair.getPublic(), false);
            System.out.println("🔒 Gói tệp an toàn nguyên bản đã được tạo: " + safePackage.length + " bytes");

            // Kẻ tấn công can thiệp sửa đúng 1 bit ở byte cuối cùng của Ciphertext
            byte[] tamperedPackage = safePackage.clone();
            int attackPos = tamperedPackage.length - 1; // Vị trí byte Auth Tag/Ciphertext
            tamperedPackage[attackPos] ^= 0x01; // Đảo 1 bit: 00000001 XOR

            System.out.printf("⚠️ Kẻ tấn công Mallory đã can thiệp lật 1 bit tại vị trí offset %d (0x%02X -> 0x%02X)\n",
                    attackPos, safePackage[attackPos], tamperedPackage[attackPos]);
            System.out.println("⏳ Phía người nhận Bob tiến hành giải mã gói tệp bị can thiệp...");

            try {
                SecurePackageEngine.unpack(tamperedPackage, bobKeyPair.getPrivate());
                System.out.println("❌ NGUY HIỂM: Hệ thống đã giải mã thành công một gói tin bị giả mạo!");
            } catch (AEADBadTagException e) {
                System.out.println("🛡️ [THÀNH CÔNG CHẶN ĐỨNG TẤN CÔNG]");
                System.out.println("  -> Ngoại lệ bắt được: javax.crypto.AEADBadTagException: Tag mismatch!");
                System.out.println("  -> Giải thích: Thuật toán AES-GCM với mã xác thực GMAC 128-bit trên trường Galois");
                System.out.println("     đã phát hiện giá trị hàm băm toàn vẹn bị sai lệch dù chỉ 1 bit.");
                System.out.println("  -> Kết quả: Không có bất kỳ dữ liệu giải mã nào bị rò rỉ ra ngoài.");
            }
        } catch (Exception e) {
            System.err.println("❌ Lỗi demo tấn công: " + e.getMessage());
        }
    }

    /**
     * Chức năng 3: Kiểm thử với bộ vector chuẩn NIST ACVP
     */
    private static void demoNistAcvpValidation() {
        System.out.println("\n>>> [CHỨC NĂNG 3] KIỂM THỬ TÍNH ĐÚNG ĐẮN VỚI BỘ VECTOR CHUẨN NIST ACVP");
        try {
            File nistFile = new File("src/test/resources/nist-acvp/aes-gcm-sample.json");
            if (!nistFile.exists()) {
                System.err.println("❌ Không tìm thấy tệp vector: " + nistFile.getAbsolutePath());
                return;
            }

            List<NistAcvpParser.AesGcmTestCase> testCases = NistAcvpParser.parseAesGcmFile(nistFile);
            System.out.println("📌 Thuật toán kiểm chuẩn: AES-GCM-256 | Tiêu chuẩn: NIST SP 800-38D");
            System.out.println("📌 Đã tải thành công " + testCases.size() + " test cases từ NIST ACVP JSON.");

            int passed = 0;
            for (NistAcvpParser.AesGcmTestCase tc : testCases) {
                byte[] ctWithTag = new byte[tc.ct.length + tc.tag.length];
                System.arraycopy(tc.ct, 0, ctWithTag, 0, tc.ct.length);
                System.arraycopy(tc.tag, 0, ctWithTag, tc.ct.length, tc.tag.length);

                try {
                    byte[] decrypted = SecurePackageEngine.decryptAesGcmRaw(tc.key, tc.iv, tc.aad, ctWithTag);
                    if (tc.expectPass) {
                        System.out.printf("  [tcId: %d] PASS (Hợp lệ): %s\n", tc.tcId, tc.comment);
                        passed++;
                    } else {
                        System.out.printf("  [tcId: %d] FAIL (Lẽ ra phải chặn lỗi giả mạo): %s\n", tc.tcId, tc.comment);
                    }
                } catch (AEADBadTagException e) {
                    if (!tc.expectPass) {
                        System.out.printf("  [tcId: %d] PASS (Đã phát hiện & chặn giả mạo chuẩn xác): %s\n", tc.tcId, tc.comment);
                        passed++;
                    } else {
                        System.out.printf("  [tcId: %d] FAIL (Lỗi bất ngờ): %s\n", tc.tcId, tc.comment);
                    }
                }
            }

            System.out.println("--------------------------------------------------------------------------------");
            System.out.printf("📊 TỔNG KẾT KIỂM CHUẨN NIST ACVP: %d/%d test cases đạt yêu cầu (Tỷ lệ: %.1f%%)\n",
                    passed, testCases.size(), ((double) passed / testCases.size()) * 100);

        } catch (Exception e) {
            System.err.println("❌ Lỗi kiểm chuẩn NIST ACVP: " + e.getMessage());
        }
    }

    /**
     * Chức năng 4: Thực nghiệm Benchmark 3 lần chạy -> Xuất CSV
     */
    private static void demoBenchmark() {
        System.out.println("\n>>> [CHỨC NĂNG 4] THỰC NGHIỆM ĐO HIỆU NĂNG & ĐỘ ỔN ĐỊNH (BENCHMARK)");
        System.out.println("Cấu hình: 3 lần chạy (Runs = 3), Cố định Random Seed = 42.");
        System.out.println("Tập kích thước kiểm thử: 1 KB, 100 KB, 1 MB, 10 MB.\n");

        int[] sizes = {1024, 100 * 1024, 1024 * 1024, 10 * 1024 * 1024};
        String[] sizeLabels = {"1KB", "100KB", "1MB", "10MB"};
        int runs = 3;

        File csvFile = new File("results.csv");

        try (PrintWriter writer = new PrintWriter(new FileWriter(csvFile))) {
            writer.println("FileSizeLabel,Size_Bytes,Mode,RunNumber,EncTime_ms,DecTime_ms,PackageSize_Bytes,Overhead_Bytes");

            for (int s = 0; s < sizes.length; s++) {
                int size = sizes[s];
                String label = sizeLabels[s];
                System.out.printf("🔄 Đang thử nghiệm kích thước: %-6s (%d bytes)...\n", label, size);

                // Sinh dữ liệu mẫu có tính lặp lại với seed cố định
                Random rand = new Random(42);
                byte[] testData = new byte[size];
                for (int i = 0; i < size; i++) {
                    testData[i] = (byte) ('A' + rand.nextInt(26));
                }

                // Chạy 2 chế độ: Baseline (useGzip = false) và Variant GZIP (useGzip = true)
                for (boolean useGzip : new boolean[]{false, true}) {
                    String modeName = useGzip ? "Variant_GZIP" : "Baseline";
                    double totalEnc = 0, totalDec = 0;
                    int pkgSize = 0;

                    for (int run = 1; run <= runs; run++) {
                        long t1 = System.nanoTime();
                        byte[] pkg = SecurePackageEngine.pack(testData, "bench_" + label + ".dat", bobKeyPair.getPublic(), useGzip);
                        long t2 = System.nanoTime();

                        SecurePackageResult res = SecurePackageEngine.unpack(pkg, bobKeyPair.getPrivate());
                        long t3 = System.nanoTime();

                        double encTime = (t2 - t1) / 1e6;
                        double decTime = (t3 - t2) / 1e6;
                        pkgSize = pkg.length;
                        int overhead = pkgSize - size;

                        totalEnc += encTime;
                        totalDec += decTime;

                        writer.printf("%s,%d,%s,%d,%.3f,%.3f,%d,%d\n",
                                label, size, modeName, run, encTime, decTime, pkgSize, overhead);
                    }

                    System.out.printf("   [%-12s] Trung bình: Mã hóa = %.2f ms | Giải mã = %.2f ms | Gói tin = %d bytes\n",
                            modeName, totalEnc / runs, totalDec / runs, pkgSize);
                }
            }

            System.out.println("\n✅ Đã ghi thành công toàn bộ kết quả thực nghiệm ra tệp: " + csvFile.getAbsolutePath());
        } catch (Exception e) {
            System.err.println("❌ Lỗi trong quá trình chạy Benchmark: " + e.getMessage());
        }
    }
}

