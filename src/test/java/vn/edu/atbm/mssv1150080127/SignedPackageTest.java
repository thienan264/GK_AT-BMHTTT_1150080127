package vn.edu.atbm.mssv1150080127;

import org.junit.jupiter.api.*;
import vn.edu.atbm.mssv1150080127.crypto.*;
import java.security.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class SignedPackageTest {
    static KeyPair alice,bob,mallory;
    @BeforeAll static void keys() throws Exception {
        alice=RsaKeyManager.generateKeyPair(2048);bob=RsaKeyManager.generateKeyPair(2048);mallory=RsaKeyManager.generateKeyPair(2048);
    }
    @Test void signedRoundTripBothModes() throws Exception {
        for(boolean gzip:new boolean[]{false,true}) {
            byte[] data="Tệp của Alice — dữ liệu công khai".getBytes(java.nio.charset.StandardCharsets.UTF_8);
            byte[] inner=SecurePackageEngine.pack(data,"bài.txt",bob.getPublic(),gzip);
            byte[] signed=SignedPackage.sign(inner,alice.getPrivate());
            assertArrayEquals(data,SecurePackageEngine.unpack(SignedPackage.verify(signed,alice.getPublic()),bob.getPrivate()).getPlainData());
        }
    }
    @Test void publicRecipientKeyDoesNotAllowImpersonatingAlice() throws Exception {
        byte[] inner=SecurePackageEngine.pack(new byte[]{1,2},"Alice.txt",bob.getPublic(),false);
        byte[] forged=SignedPackage.sign(inner,mallory.getPrivate());
        assertThrows(SignatureException.class,()->SignedPackage.verify(forged,alice.getPublic()));
    }
    @Test void tamperingHeaderPayloadSignatureAndLengthsIsRejected() throws Exception {
        byte[] signed=SignedPackage.sign(SecurePackageEngine.pack(new byte[]{1,2},"a",bob.getPublic(),false),alice.getPrivate());
        for(int pos:new int[]{0,4,7,8,50,signed.length-257,signed.length-1}) {
            byte[] changed=signed.clone();changed[pos]^=1;
            assertThrows(GeneralSecurityException.class,()->SignedPackage.verify(changed,alice.getPublic()),"position "+pos);
        }
        assertThrows(SignatureException.class,()->SignedPackage.verify(Arrays.copyOf(signed,signed.length+1),alice.getPublic()));
        assertThrows(SignatureException.class,()->SignedPackage.verify(Arrays.copyOf(signed,signed.length-1),alice.getPublic()));
    }
    @Test void unsignedLegacyHasNoAutomaticDowngrade() throws Exception {
        byte[] old=SecurePackageEngine.pack(new byte[0],"",bob.getPublic(),false);
        assertThrows(SignatureException.class,()->SignedPackage.verify(old,alice.getPublic()));
    }
    @Test void validSenderDoesNotBypassRecipientKey() throws Exception {
        byte[] signed=SignedPackage.sign(SecurePackageEngine.pack(new byte[0],"",bob.getPublic(),false),alice.getPrivate());
        byte[] verified=SignedPackage.verify(signed,alice.getPublic());
        assertThrows(Exception.class,()->SecurePackageEngine.unpack(verified,mallory.getPrivate()));
    }
    @Test void decompressionIsBoundedEvenForAuthenticatedInput() throws Exception {
        byte[] compressed=GzipUtil.compress(new byte[GzipUtil.MAX_DECOMPRESSED_BYTES+1]);
        assertThrows(java.io.IOException.class,()->GzipUtil.decompress(compressed));
    }
    @Test void signatureInteroperatesWithOpenSsl() throws Exception {
        var dir=java.nio.file.Files.createTempDirectory("pss-interop-");
        try {
            byte[] signed=SignedPackage.sign(new byte[]{4,5,6},alice.getPrivate());
            byte[] content=Arrays.copyOf(signed,signed.length-256);
            byte[] domain="ATBM-SIGNED-PACKAGE-V2".getBytes(java.nio.charset.StandardCharsets.US_ASCII);
            var msg=java.nio.ByteBuffer.allocate(domain.length+content.length).put(domain).put(content).array();
            java.nio.file.Files.write(dir.resolve("msg"),msg);
            java.nio.file.Files.write(dir.resolve("sig"),Arrays.copyOfRange(signed,signed.length-256,signed.length));
            java.nio.file.Files.write(dir.resolve("pub.der"),alice.getPublic().getEncoded());
            Process p=new ProcessBuilder("openssl","dgst","-sha256","-verify",dir.resolve("pub.der").toString(),"-keyform","DER",
                "-signature",dir.resolve("sig").toString(),"-sigopt","rsa_padding_mode:pss","-sigopt","rsa_pss_saltlen:32",
                "-sigopt","rsa_mgf1_md:sha256",dir.resolve("msg").toString()).redirectErrorStream(true).start();
            String output=new String(p.getInputStream().readAllBytes());assertEquals(0,p.waitFor(),output);
        } finally {try(var stream=java.nio.file.Files.walk(dir)){for(var f:stream.sorted(Comparator.reverseOrder()).toList())java.nio.file.Files.delete(f);}}
    }
}
