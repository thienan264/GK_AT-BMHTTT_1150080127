package vn.edu.atbm.mssv1150080127.crypto;

import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;
import java.security.*;

/** Package v1 policy: wrap exactly a 32-byte AES key using OAEP SHA-256/MGF1-SHA-256 and empty label. */
public final class RsaKeyManager {
    private RsaKeyManager() {}
    public static KeyPair generateKeyPair(int bits) throws NoSuchAlgorithmException {
        KeyPairGenerator generator = KeyPairGenerator.getInstance("RSA");
        generator.initialize(bits, new SecureRandom());
        return generator.generateKeyPair();
    }
    public static byte[] wrapKey(SecretKey aesKey, PublicKey key) throws Exception {
        byte[] encoded = aesKey.getEncoded();
        if (!"AES".equalsIgnoreCase(aesKey.getAlgorithm()) || encoded.length != 32)
            throw new InvalidKeyException("Package v1 requires AES-256");
        return RsaOaep.encrypt(encoded, key, "SHA-256", new byte[0]);
    }
    public static SecretKey unwrapKey(byte[] wrapped, PrivateKey key) throws Exception {
        byte[] encoded = RsaOaep.decrypt(wrapped, key, "SHA-256", new byte[0]);
        if (encoded.length != 32) throw new InvalidKeyException("Unwrapped key is not AES-256");
        return new SecretKeySpec(encoded, "AES");
    }
}
