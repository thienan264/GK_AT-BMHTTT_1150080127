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

class SecurePackageTest {
    @TempDir Path temp;
    static KeyPair keys;
    @BeforeAll static void init() throws Exception { keys=RsaKeyManager.generateKeyPair(2048); }
    @Test void gzipMetadataAndSharedCipherWiring() throws Exception {
        byte[] data="Dữ liệu lặp phục vụ test tích hợp. ".repeat(100).getBytes(java.nio.charset.StandardCharsets.UTF_8);
        int baselineSize=0;
        for(boolean gzip:new boolean[]{false,true}) {
            byte[] pkg=SecurePackageEngine.pack(data,"tệp.txt",keys.getPublic(),gzip);
            var result=SecurePackageEngine.unpack(pkg,keys.getPrivate());
            assertArrayEquals(data,result.getPlainData());
            assertEquals("tệp.txt",result.getOriginalFilename());assertEquals(gzip,result.isCompressed());
            if(!gzip)baselineSize=pkg.length; else assertTrue(pkg.length<baselineSize);

            ByteBuffer b=ByteBuffer.wrap(pkg);b.position(6);int wrappedLength=Short.toUnsignedInt(b.getShort());
            byte[] wrapped=new byte[wrappedLength];b.get(wrapped);byte[] iv=new byte[12];b.get(iv);
            int nameLength=Short.toUnsignedInt(b.getShort());b.position(b.position()+nameLength);
            byte[] aad=Arrays.copyOf(pkg,b.position());int size=(int)b.getLong();byte[] body=new byte[size];b.get(body);
            byte[] aes=RsaKeyManager.unwrapKey(wrapped,keys.getPrivate()).getEncoded();
            byte[] expectedPayload=gzip?GzipUtil.compress(data):data;
            assertArrayEquals(body,AesGcm.encrypt(aes,iv,aad,expectedPayload));
            assertArrayEquals(expectedPayload,AesGcm.decrypt(aes,iv,aad,body));
        }
    }

    @Test void emptyUnicodeBinaryAndLargeNames() throws Exception {
        byte[] binary = new byte[4097]; new Random(42).nextBytes(binary);
        for (byte[] data : new byte[][]{new byte[0], new byte[]{0}, binary}) {
            for (boolean gzip : new boolean[]{false, true}) {
                var result = SecurePackageEngine.unpack(SecurePackageEngine.pack(data, "tệp-秘密.bin", keys.getPublic(), gzip), keys.getPrivate());
                assertArrayEquals(data, result.getPlainData());
                assertEquals("tệp-秘密.bin", result.getOriginalFilename());
            }
        }
        String longName = "a".repeat(40000);
        assertEquals(longName, SecurePackageEngine.unpack(SecurePackageEngine.pack(new byte[0], longName, keys.getPublic(), false), keys.getPrivate()).getOriginalFilename());
        assertThrows(IllegalArgumentException.class, () -> SecurePackageEngine.pack(binary, "a".repeat(65536), keys.getPublic(), false));
    }

    @Test void tamperingAndMalformedPackages() throws Exception {
        byte[] data = new byte[100]; new Random(42).nextBytes(data);
        byte[] valid = SecurePackageEngine.pack(data, "x", keys.getPublic(), false);

        for (int offset : new int[]{287, valid.length - 1, 264, 278, 5}) {
            byte[] changed = valid.clone(); changed[offset] ^= 1;
            assertThrows(AEADBadTagException.class, () -> SecurePackageEngine.unpack(changed, keys.getPrivate()), "offset=" + offset);
        }
        for (int offset : new int[]{0, 4, 8}) {
            byte[] changed = valid.clone(); changed[offset] ^= 1;
            assertThrows(Exception.class, () -> SecurePackageEngine.unpack(changed, keys.getPrivate()));
        }
        for (int len : new int[]{0, 100, 300, valid.length - 1})
            assertThrows(Exception.class, () -> SecurePackageEngine.unpack(Arrays.copyOf(valid, len), keys.getPrivate()));
        assertThrows(SecurityException.class, () -> SecurePackageEngine.unpack(Arrays.copyOf(valid, valid.length + 1), keys.getPrivate()));
        byte[] wrongLength = valid.clone(); ByteBuffer.wrap(wrongLength).putLong(279, Long.MAX_VALUE);
        assertThrows(SecurityException.class, () -> SecurePackageEngine.unpack(wrongLength, keys.getPrivate()));
        byte[] badFlags = valid.clone(); badFlags[5] = 2;
        assertThrows(SecurityException.class, () -> SecurePackageEngine.unpack(badFlags, keys.getPrivate()));
        byte[] badNameLength = valid.clone(); ByteBuffer.wrap(badNameLength).putShort(276, (short)65535);
        assertThrows(SecurityException.class, () -> SecurePackageEngine.unpack(badNameLength, keys.getPrivate()));
        KeyPair wrong = RsaKeyManager.generateKeyPair(2048);
        assertThrows(GeneralSecurityException.class, () -> SecurePackageEngine.unpack(valid, wrong.getPrivate()));
    }
}
