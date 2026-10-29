package vn.edu.atbm.mssv1150080127.crypto;

import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

/** Single AES-GCM implementation for packages AND reference-vector verification. */
public final class AesGcm {
    private AesGcm() {}
    public static final int TAG_BITS = 128;

    public static byte[] encrypt(byte[] key, byte[] iv, byte[] aad, byte[] plaintext) throws Exception {
        return process(Cipher.ENCRYPT_MODE, key, iv, aad, plaintext);
    }
    public static byte[] decrypt(byte[] key, byte[] iv, byte[] aad, byte[] ciphertextAndTag) throws Exception {
        return process(Cipher.DECRYPT_MODE, key, iv, aad, ciphertextAndTag);
    }
    private static byte[] process(int mode, byte[] key, byte[] iv, byte[] aad, byte[] input) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(mode, new SecretKeySpec(key, "AES"), new GCMParameterSpec(TAG_BITS, iv));
        if (aad != null) cipher.updateAAD(aad);
        return cipher.doFinal(input);
    }
}
