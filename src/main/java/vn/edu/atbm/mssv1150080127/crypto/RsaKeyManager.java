package vn.edu.atbm.mssv1150080127.crypto;

import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.OAEPParameterSpec;
import javax.crypto.spec.PSource;
import javax.crypto.spec.SecretKeySpec;
import java.security.*;
import java.security.spec.MGF1ParameterSpec;

/**
 * Lớp quản lý khóa RSA-2048 và thực hiện cơ chế bọc khóa (Key Wrapping)
 * cho khóa phiên AES-256 bằng thuật toán RSA-OAEP chuẩn với SHA-256.
 * 
 * Tác giả: Trần Phạm Thiên Ân - MSSV: 1150080127
 */
public class RsaKeyManager {

    // Định danh thuật toán RSA-OAEP chuẩn trong Java Cryptography Architecture (JCA)
    public static final String RSA_OAEP_TRANSFORMATION = "RSA/ECB/OAEPWithSHA-256AndMGF1Padding";

    /**
     * Sinh cặp khóa RSA với độ dài chỉ định (mặc định cho đồ án là 2048 bits).
     *
     * @param keySize Độ dài khóa tính theo bit (ví dụ: 2048)
     * @return Cặp khóa KeyPair gồm PublicKey và PrivateKey
     * @throws NoSuchAlgorithmException Nếu thuật toán RSA không được hỗ trợ
     */
    public static KeyPair generateKeyPair(int keySize) throws NoSuchAlgorithmException {
        KeyPairGenerator keyPairGen = KeyPairGenerator.getInstance("RSA");
        // Khởi tạo bộ sinh số ngẫu nhiên an toàn SecureRandom
        keyPairGen.initialize(keySize, new SecureRandom());
        return keyPairGen.generateKeyPair();
    }

    /**
     * Cấu hình tham số OAEPParameterSpec chuẩn hóa với hàm băm SHA-256
     * và hàm tạo mặt nạ MGF1 sử dụng SHA-256.
     * Lưu ý: Java JCA nếu không chỉ định rõ OAEPParameterSpec thì một số phiên bản
     * sẽ mặc định sử dụng MGF1ParameterSpec.SHA1, gây nguy cơ bảo mật.
     */
    private static OAEPParameterSpec createOaepSpec() {
        return new OAEPParameterSpec(
                "SHA-256",
                "MGF1",
                MGF1ParameterSpec.SHA256,
                PSource.PSpecified.DEFAULT
        );
    }

    /**
     * Bọc (mã hóa) khóa đối xứng AES-256 bằng khóa công khai RSA-2048 của bên nhận.
     *
     * @param aesKey Khóa phiên AES cần bọc
     * @param publicKey Khóa công khai của người nhận
     * @return Mảng byte khóa bọc (Wrapped Key) có độ dài chính xác 256 bytes (2048 bits)
     * @throws Exception Các lỗi mật mã trong quá trình mã hóa
     */
    public static byte[] wrapKey(SecretKey aesKey, PublicKey publicKey) throws Exception {
        Cipher cipher = Cipher.getInstance(RSA_OAEP_TRANSFORMATION);
        OAEPParameterSpec oaepSpec = createOaepSpec();
        cipher.init(Cipher.WRAP_MODE, publicKey, oaepSpec);
        return cipher.wrap(aesKey);
    }

    /**
     * Mở bọc (giải mã) khóa đối xứng AES-256 bằng khóa bí mật RSA-2048 của bên nhận.
     *
     * @param wrappedKey Mảng byte khóa bọc nhận được từ gói tệp
     * @param privateKey Khóa bí mật của người nhận
     * @return Khóa đối xứng SecretKey phục hồi (AES-256)
     * @throws Exception Nếu khóa bị sửa đổi hoặc giải mã thất bại
     */
    public static SecretKey unwrapKey(byte[] wrappedKey, PrivateKey privateKey) throws Exception {
        Cipher cipher = Cipher.getInstance(RSA_OAEP_TRANSFORMATION);
        OAEPParameterSpec oaepSpec = createOaepSpec();
        cipher.init(Cipher.UNWRAP_MODE, privateKey, oaepSpec);
        Key unwrappedKey = cipher.unwrap(wrappedKey, "AES", Cipher.SECRET_KEY);
        return new SecretKeySpec(unwrappedKey.getEncoded(), "AES");
    }
}

