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

class WebValidationTest {
    @TempDir Path temp;
    @Test void webUsesTheSameVerifierAndLabelsCoverage() {
        var result = vn.edu.atbm.mssv1150080127.web.service.CryptoWebService.getInstance().runNistValidation();
        assertEquals(true, result.get("success"));
        assertEquals(140, result.get("total"));
        assertEquals(140L, result.get("passed"));
        assertTrue(result.get("scope").toString().contains("Not NIST certification"));
    }
}
