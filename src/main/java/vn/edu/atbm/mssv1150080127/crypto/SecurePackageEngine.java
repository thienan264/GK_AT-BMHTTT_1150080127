package vn.edu.atbm.mssv1150080127.crypto;

import vn.edu.atbm.mssv1150080127.model.SecurePackageResult;

import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import java.io.*;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.SecureRandom;
import java.util.Arrays;

public class SecurePackageEngine {


    public static final byte[] MAGIC_HEADER = new byte[]{'S', 'E', 'C', 'P'};
    public static final byte CURRENT_VERSION = 0x01;


    public static final byte FLAG_BASELINE = 0x00;
    public static final byte FLAG_VARIANT_GZIP = 0x01;

    public static final int GCM_TAG_LENGTH_BITS = 128;
    public static final int GCM_IV_LENGTH_BYTES = 12;

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
        if (plainData == null) throw new IllegalArgumentException("Plaintext is null");

        byte[] payloadToEncrypt = useGzip ? GzipUtil.compress(plainData) : plainData;
        byte flag = useGzip ? FLAG_VARIANT_GZIP : FLAG_BASELINE;


        SecretKey aesKey = generateAesKey();
        byte[] iv = generateIv();


        byte[] wrappedKey = RsaKeyManager.wrapKey(aesKey, recipientPublicKey);
        if (wrappedKey.length != 256) throw new IllegalArgumentException("Package v1 requires RSA-2048");


        byte[] aadBytes = (originalFilename != null) ? originalFilename.getBytes(StandardCharsets.UTF_8) : new byte[0];

        if (aadBytes.length > 65535) throw new IllegalArgumentException("Filename exceeds 65535 UTF-8 bytes");



        ByteArrayOutputStream headerOut = new ByteArrayOutputStream();
        headerOut.write(MAGIC_HEADER);
        headerOut.write(CURRENT_VERSION);
        headerOut.write(flag);


        ByteBuffer shortBuffer = ByteBuffer.allocate(2);
        shortBuffer.putShort((short) wrappedKey.length);
        headerOut.write(shortBuffer.array());
        headerOut.write(wrappedKey);


        headerOut.write(iv);


        ByteBuffer aadLenBuffer = ByteBuffer.allocate(2);
        aadLenBuffer.putShort((short) aadBytes.length);
        headerOut.write(aadLenBuffer.array());
        if (aadBytes.length > 0) {
            headerOut.write(aadBytes);
        }

        byte[] headerBytes = headerOut.toByteArray();


        byte[] ciphertextWithTag = AesGcm.encrypt(aesKey.getEncoded(), iv, headerBytes, payloadToEncrypt);


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


        byte[] magic = new byte[4];
        buffer.get(magic);
        if (!Arrays.equals(magic, MAGIC_HEADER)) {
            throw new SecurityException("Magic bytes không hợp lệ! Đây không phải tệp .secpkg chuẩn.");
        }


        byte version = buffer.get();
        if (version != CURRENT_VERSION) {
            throw new SecurityException("Phiên bản gói tệp không được hỗ trợ (Version: " + version + ")");
        }


        byte flags = buffer.get();
        if (flags != FLAG_BASELINE && flags != FLAG_VARIANT_GZIP) throw new SecurityException("Unknown flags");
        boolean isGzip = (flags == FLAG_VARIANT_GZIP);


        int wrappedKeyLen = Short.toUnsignedInt(buffer.getShort());
        if (wrappedKeyLen != 256 || buffer.remaining() < wrappedKeyLen + 12 + 2 + 8 + 16) {
            throw new SecurityException("Độ dài khóa bọc không hợp lệ: " + wrappedKeyLen);
        }
        byte[] wrappedKey = new byte[wrappedKeyLen];
        buffer.get(wrappedKey);


        byte[] iv = new byte[GCM_IV_LENGTH_BYTES];
        buffer.get(iv);


        int aadLen = Short.toUnsignedInt(buffer.getShort());
        if (buffer.remaining() < aadLen + 8 + 16) throw new SecurityException("Truncated filename/header");
        byte[] aadBytes = new byte[aadLen];
        if (aadLen > 0) {
            buffer.get(aadBytes);
        }
        String originalFilename = new String(aadBytes, StandardCharsets.UTF_8);


        int headerLength = buffer.position();
        byte[] headerBytes = Arrays.copyOfRange(packageBytes, 0, headerLength);


        SecretKey aesKey = RsaKeyManager.unwrapKey(wrappedKey, recipientPrivateKey);


        long cipherLen = buffer.getLong();
        if (cipherLen < 16 || cipherLen != buffer.remaining()) {
            throw new SecurityException("Độ dài bản mã không hợp lệ: " + cipherLen);
        }
        byte[] ciphertextWithTag = new byte[(int) cipherLen];
        buffer.get(ciphertextWithTag);


        byte[] decryptedPayload = AesGcm.decrypt(aesKey.getEncoded(), iv, headerBytes, ciphertextWithTag);


        byte[] finalPlainData = isGzip ? GzipUtil.decompress(decryptedPayload) : decryptedPayload;

        return new SecurePackageResult(finalPlainData, originalFilename, isGzip, packageBytes.length);
    }

}
