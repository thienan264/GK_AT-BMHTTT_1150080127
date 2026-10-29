package vn.edu.atbm.mssv1150080127.crypto;

import javax.crypto.Cipher;
import javax.crypto.spec.OAEPParameterSpec;
import javax.crypto.spec.PSource;
import java.security.*;
import java.security.spec.MGF1ParameterSpec;

/** Shared OAEP primitive. Package and NIST-generated tests use SHA-256 with an empty label. */
public final class RsaOaep {
    private RsaOaep() {}
    public static byte[] encrypt(byte[] data, PublicKey key, String hash, byte[] label) throws Exception {
        return process(Cipher.ENCRYPT_MODE, data, key, hash, label);
    }
    public static byte[] decrypt(byte[] ciphertext, PrivateKey key, String hash, byte[] label) throws Exception {
        return process(Cipher.DECRYPT_MODE, ciphertext, key, hash, label);
    }
    private static byte[] process(int mode, byte[] data, Key key, String hash, byte[] label) throws Exception {
        if (!hash.equals("SHA-256") && !hash.equals("SHA-512")) throw new IllegalArgumentException("Unsupported OAEP hash");
        Cipher cipher = Cipher.getInstance("RSA/ECB/OAEPPadding");
        OAEPParameterSpec spec = new OAEPParameterSpec(hash, "MGF1", new MGF1ParameterSpec(hash), new PSource.PSpecified(label));
        cipher.init(mode, key, spec);
        return cipher.doFinal(data);
    }
}
