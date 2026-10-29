package vn.edu.atbm.mssv1150080127;

import vn.edu.atbm.mssv1150080127.util.AesGcmVectorVerifier;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.io.TempDir;
import vn.edu.atbm.mssv1150080127.crypto.*;
import vn.edu.atbm.mssv1150080127.util.NistAcvpParser;
import javax.crypto.*;
import javax.crypto.spec.SecretKeySpec;
import java.nio.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;
import static org.junit.jupiter.api.Assertions.*;

class AesGcmVectorTest {
    @TempDir Path temp;
    @TestFactory Stream<DynamicTest> nistCases() throws Exception {
        var cases = NistAcvpParser.parseAesGcmFile(Path.of("src/test/resources/nist-acvp/aes-gcm-sample.json").toFile());
        assertEquals(120, cases.size());
        return cases.stream().map(tc -> DynamicTest.dynamicTest(tc.toString(), () -> AesGcmVectorVerifier.verify(tc)));
    }

    @Test void assertionsReallyRejectWrongAnswers() throws Exception {
        var cases = NistAcvpParser.parseAesGcmFile(Path.of("src/test/resources/nist-acvp/aes-gcm-sample.json").toFile());
        var enc = cases.stream().filter(tc -> tc.direction.equals("encrypt")).findFirst().orElseThrow();
        enc.tag[0] ^= 1;
        assertThrows(SecurityException.class, () -> AesGcmVectorVerifier.verify(enc));
        var dec = cases.stream().filter(tc -> tc.direction.equals("decrypt") && tc.expectPass).findFirst().orElseThrow();
        dec.pt = new byte[]{42};
        assertThrows(SecurityException.class, () -> AesGcmVectorVerifier.verify(dec));
    }
}
