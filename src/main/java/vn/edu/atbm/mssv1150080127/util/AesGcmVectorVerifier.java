package vn.edu.atbm.mssv1150080127.util;

import javax.crypto.AEADBadTagException;
import java.util.Arrays;
import vn.edu.atbm.mssv1150080127.crypto.AesGcm;
import vn.edu.atbm.mssv1150080127.util.NistAcvpParser.AesGcmTestCase;

/** Test oracle adapter; cryptographic processing lives exclusively in AesGcm. */
public final class AesGcmVectorVerifier {
    /** Shared by web and JUnit: compare outputs, not just absence of exceptions. */
    public static void verify(AesGcmTestCase tc) throws Exception {
        byte[] expected = new byte[tc.ct.length + tc.tag.length];
        System.arraycopy(tc.ct, 0, expected, 0, tc.ct.length);
        System.arraycopy(tc.tag, 0, expected, tc.ct.length, tc.tag.length);
        if (tc.direction.equals("encrypt")) {
            byte[] actual = AesGcm.encrypt(tc.key, tc.iv, tc.aad, tc.pt);
            if (!Arrays.equals(expected, actual)) throw new SecurityException("Ciphertext/tag mismatch: " + tc);
        } else {
            try {
                byte[] plain = AesGcm.decrypt(tc.key, tc.iv, tc.aad, expected);
                if (!tc.expectPass) throw new SecurityException("Invalid authentication accepted: " + tc);
                if (!Arrays.equals(tc.pt, plain)) throw new SecurityException("Plaintext mismatch: " + tc);
            } catch (AEADBadTagException e) {
                if (tc.expectPass) throw e;
            }
        }
    }
}
