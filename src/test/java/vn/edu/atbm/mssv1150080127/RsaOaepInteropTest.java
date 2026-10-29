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

class RsaOaepInteropTest {
    @TempDir Path temp;
    static KeyPair keys;
    @BeforeAll static void init() throws Exception { keys=RsaKeyManager.generateKeyPair(2048); }
    private void openssl(String... args) throws Exception {
        List<String> command = new ArrayList<>(); command.add("openssl"); command.addAll(List.of(args));
        Path log = temp.resolve("openssl.log");
        Process process = new ProcessBuilder(command).redirectErrorStream(true).redirectOutput(log.toFile()).start();
        if (!process.waitFor(20, TimeUnit.SECONDS)) { process.destroyForcibly(); fail("OpenSSL timed out"); }
        assertEquals(0, process.exitValue(), Files.readString(log));
    }
    @Test void rsaOaepJavaOpenSslBothDirections() throws Exception {
        Path pub = temp.resolve("public.der"), priv = temp.resolve("private.der");
        Files.write(pub, keys.getPublic().getEncoded()); Files.write(priv, keys.getPrivate().getEncoded());
        byte[] raw = HexFormat.of().parseHex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f");
        Path input = temp.resolve("input.bin"), wrapped = temp.resolve("wrapped.bin"), out = temp.resolve("out.bin");
        Files.write(input, raw);
        Files.write(wrapped, RsaKeyManager.wrapKey(new SecretKeySpec(raw, "AES"), keys.getPublic()));
        openssl("pkeyutl", "-decrypt", "-keyform", "DER", "-inkey", priv.toString(), "-in", wrapped.toString(), "-out", out.toString(),
                "-pkeyopt", "rsa_padding_mode:oaep", "-pkeyopt", "rsa_oaep_md:sha256", "-pkeyopt", "rsa_mgf1_md:sha256");
        assertArrayEquals(raw, Files.readAllBytes(out));
        openssl("pkeyutl", "-encrypt", "-pubin", "-keyform", "DER", "-inkey", pub.toString(), "-in", input.toString(), "-out", wrapped.toString(),
                "-pkeyopt", "rsa_padding_mode:oaep", "-pkeyopt", "rsa_oaep_md:sha256", "-pkeyopt", "rsa_mgf1_md:sha256");
        assertArrayEquals(raw, RsaKeyManager.unwrapKey(Files.readAllBytes(wrapped), keys.getPrivate()).getEncoded());
    }
}
