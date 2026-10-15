package vn.edu.atbm.mssv1150080127.crypto;

import vn.edu.atbm.mssv1150080127.model.SecurePackageResult;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.SecureRandom;
import java.util.Arrays;

/**
 * Trái tim xử lý mã hóa lai: Đóng gói và Mở gói định dạng tệp an toàn .secpkg
 * Kết hợp mã hóa đối xứng AES-256-GCM với bọc khóa RSA-2048-OAEP.
 * 
 * Tác giả: Trần Phạm Thiên Ân - MSSV: 1150080127
 */
public class SecurePackageEngine {

    // 4 byte nhận diện file "SECP"
    public static final byte[] MAGIC_HEADER = new byte[]{'S', 'E', 'C', 'P'};
    public static final byte CURRENT_VERSION = 0x01;

    // Cờ trạng thái
    public static final byte FLAG_BASELINE = 0x00;  // Không nén
    public static final byte FLAG_VARIANT_GZIP = 0x01; // Biến thể có nén GZIP

    public static final int GCM_TAG_LENGTH_BITS = 128; // 16 bytes authentication tag
    public static final int GCM_IV_LENGTH_BYTES = 12;  // 96-bit recommended nonce

    /**
     * Sinh khóa phiên đối xứng AES-256 ngẫu nhiên an toàn.
     */
    public static SecretKey generateAesKey() throws Exception {
        KeyGenerator keyGen = KeyGenerator.getInstance("AES");
        keyGen.init(256, new SecureRandom());
        return keyGen.generateKey();
    }

    /**
     * Sinh vector khởi tạo IV 12 bytes ngẫu nhiên an toàn.
     */
    public static byte[] generateIv() {
        byte[] iv = new byte[GCM_IV_LENGTH_BYTES];
        new SecureRandom().nextBytes(iv);
        return iv;
    }

    /**
     * Đóng gói và mã hóa tệp nhị phân sang định dạng .secpkg
     *
     * @param plainData Dữ liệu gốc cần mã hóa
     * @param originalFilename Tên tệp gốc (sẽ đưa vào AAD để bảo vệ toàn vẹn)
     * @param recipientPublicKey Khóa công khai RSA của người nhận
     * @param useGzip true nếu dùng Biến thể nén GZIP, false nếu dùng Baseline
     * @return Toàn bộ mảng byte gói tệp .secpkg hoàn chỉnh
     */
    public static byte[] pack(byte[] plainData, String originalFilename, PublicKey recipientPublicKey, boolean useGzip) throws Exception {
        // 1. Chuẩn bị dữ liệu mã hóa: Nén nếu ở chế độ Biến thể
        byte[] payloadToEncrypt = useGzip ? GzipUtil.compress(plainData) : plainData;
        byte flag = useGzip ? FLAG_VARIANT_GZIP : FLAG_BASELINE;

        // 2. Sinh khóa phiên AES-256 và IV 12 bytes
        SecretKey aesKey = generateAesKey();
        byte[] iv = generateIv();

        // 3. Bọc khóa AES bằng RSA-2048 OAEP
        byte[] wrappedKey = RsaKeyManager.wrapKey(aesKey, recipientPublicKey);

        // 4. Chuẩn bị trường AAD chứa tên tệp gốc
        byte[] aadBytes = (originalFilename != null) ? originalFilename.getBytes(StandardCharsets.UTF_8) : new byte[0];

        // 5. Xây dựng khối Header bytes
        // Header = [Magic (4B) | Version (1B) | Flags (1B) | WrappedKeyLen (2B) | WrappedKey | IV (12B) | AadLen (2B) | AadBytes]
        ByteArrayOutputStream headerOut = new ByteArrayOutputStream();
        headerOut.write(MAGIC_HEADER);
        headerOut.write(CURRENT_VERSION);
        headerOut.write(flag);

        // Ghi độ dài Wrapped Key (short big-endian) và mảng byte Wrapped Key
        ByteBuffer shortBuffer = ByteBuffer.allocate(2);
        shortBuffer.putShort((short) wrappedKey.length);
        headerOut.write(shortBuffer.array());
        headerOut.write(wrappedKey);

        // Ghi IV (12 bytes)
        headerOut.write(iv);

        // Ghi độ dài AAD và dữ liệu AAD
        ByteBuffer aadLenBuffer = ByteBuffer.allocate(2);
        aadLenBuffer.putShort((short) aadBytes.length);
        headerOut.write(aadLenBuffer.array());
        if (aadBytes.length > 0) {
            headerOut.write(aadBytes);
        }

        byte[] headerBytes = headerOut.toByteArray();

        // 6. Mã hóa AES-256-GCM với toàn bộ Header được xác thực trong AAD
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH_BITS, iv);
        cipher.init(Cipher.ENCRYPT_MODE, aesKey, gcmSpec);

        // RÀNG BUỘC TOÀN BỘ HEADER VÀO AAD ĐỂ CHỐNG CAN THIỆP BIT
        cipher.updateAAD(headerBytes);

        // doFinal() của AES-GCM tự động nối thêm 16 bytes Authentication Tag vào cuối Ciphertext
        byte[] ciphertextWithTag = cipher.doFinal(payloadToEncrypt);

        // 7. Ghi toàn bộ gói tệp: [HeaderBytes | CiphertextWithTagLen (8B long) | CiphertextWithTag]
        ByteArrayOutputStream pkgOut = new ByteArrayOutputStream();
        pkgOut.write(headerBytes);

        ByteBuffer longBuffer = ByteBuffer.allocate(8);
        longBuffer.putLong(ciphertextWithTag.length);
        pkgOut.write(longBuffer.array());
        pkgOut.write(ciphertextWithTag);

        return pkgOut.toByteArray();
    }

    /**
     * Mở gói và giải mã tệp .secpkg bằng khóa bí mật RSA của bên nhận.
     *
     * @param packageBytes Mảng byte của gói tệp .secpkg
     * @param recipientPrivateKey Khóa bí mật RSA của người nhận
     * @return Đối tượng SecurePackageResult chứa dữ liệu gốc đã phục hồi
     * @throws Exception Ngoại lệ nếu cấu trúc sai hoặc bị tấn công làm hỏng bit (AEADBadTagException)
     */
    public static SecurePackageResult unpack(byte[] packageBytes, PrivateKey recipientPrivateKey) throws Exception {
        if (packageBytes == null || packageBytes.length < (4 + 1 + 1 + 2 + 256 + 12 + 2 + 8 + 16)) {
            throw new IllegalArgumentException("Dữ liệu gói tệp quá ngắn hoặc không đúng định dạng .secpkg!");
        }

        ByteBuffer buffer = ByteBuffer.wrap(packageBytes);

        // 1. Kiểm tra Magic Bytes
        byte[] magic = new byte[4];
        buffer.get(magic);
        if (!Arrays.equals(magic, MAGIC_HEADER)) {
            throw new SecurityException("Magic bytes không hợp lệ! Đây không phải tệp .secpkg chuẩn.");
        }

        // 2. Kiểm tra Version
        byte version = buffer.get();
        if (version != CURRENT_VERSION) {
            throw new SecurityException("Phiên bản gói tệp không được hỗ trợ (Version: " + version + ")");
        }

        // 3. Đọc cờ Flags (Baseline hay GZIP)
        byte flags = buffer.get();
        boolean isGzip = (flags == FLAG_VARIANT_GZIP);

        // 4. Đọc Wrapped Key
        short wrappedKeyLen = buffer.getShort();
        if (wrappedKeyLen <= 0 || wrappedKeyLen > 1024) {
            throw new SecurityException("Độ dài khóa bọc không hợp lệ: " + wrappedKeyLen);
        }
        byte[] wrappedKey = new byte[wrappedKeyLen];
        buffer.get(wrappedKey);

        // 5. Đọc IV (12 bytes)
        byte[] iv = new byte[GCM_IV_LENGTH_BYTES];
        buffer.get(iv);

        // 6. Đọc AAD (Original Filename)
        short aadLen = buffer.getShort();
        byte[] aadBytes = new byte[aadLen];
        if (aadLen > 0) {
            buffer.get(aadBytes);
        }
        String originalFilename = new String(aadBytes, StandardCharsets.UTF_8);

        // Xác định chính xác các byte của Header để kiểm chứng AAD
        int headerLength = buffer.position();
        byte[] headerBytes = Arrays.copyOfRange(packageBytes, 0, headerLength);

        // 7. Mở bọc khóa AES-256 bằng RSA Private Key
        SecretKey aesKey = RsaKeyManager.unwrapKey(wrappedKey, recipientPrivateKey);

        // 8. Đọc Ciphertext + Tag
        long cipherLen = buffer.getLong();
        if (cipherLen <= 16 || cipherLen > (packageBytes.length - headerLength - 8)) {
            throw new SecurityException("Độ dài bản mã không hợp lệ: " + cipherLen);
        }
        byte[] ciphertextWithTag = new byte[(int) cipherLen];
        buffer.get(ciphertextWithTag);

        // 9. Xác thực và giải mã bằng AES-GCM
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH_BITS, iv);
        cipher.init(Cipher.DECRYPT_MODE, aesKey, gcmSpec);

        // Nạp đúng phần Header vào AAD để đối chiếu mã xác thực GMAC
        cipher.updateAAD(headerBytes);

        // doFinal() sẽ kiểm tra Auth Tag. Nếu bị sửa 1 bit dù ở Ciphertext hay Header -> Ném AEADBadTagException
        byte[] decryptedPayload = cipher.doFinal(ciphertextWithTag);

        // 10. Giải nén nếu gói tin được tạo với biến thể GZIP
        byte[] finalPlainData = isGzip ? GzipUtil.decompress(decryptedPayload) : decryptedPayload;

        return new SecurePackageResult(finalPlainData, originalFilename, isGzip, packageBytes.length);
    }

    /**
     * Hàm hỗ trợ giải mã AES-GCM raw phục vụ kiểm thử đối chiếu NIST ACVP.
     */
    public static byte[] decryptAesGcmRaw(byte[] key, byte[] iv, byte[] aad, byte[] ctWithTag) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        SecretKeySpec keySpec = new SecretKeySpec(key, "AES");
        GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH_BITS, iv);
        cipher.init(Cipher.DECRYPT_MODE, keySpec, gcmSpec);
        if (aad != null && aad.length > 0) {
            cipher.updateAAD(aad);
        }
        return cipher.doFinal(ctWithTag);
    }
}

