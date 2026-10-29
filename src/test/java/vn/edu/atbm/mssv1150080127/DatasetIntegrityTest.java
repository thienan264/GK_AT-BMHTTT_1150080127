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

class DatasetIntegrityTest {
    @TempDir Path temp;
    @Test void parserRejectsMalformedMetadata() throws Exception {
        String source = Files.readString(Path.of("src/test/resources/nist-acvp/aes-gcm-sample.json"));
        Path bad = temp.resolve("bad.json");
        Files.writeString(bad, source.replace("\"keyLen\": 256", "\"keyLen\": 128"));
        assertThrows(IllegalArgumentException.class, () -> NistAcvpParser.parseAesGcmFile(bad.toFile()));
    }

    @Test void datasetManifestAndSourceMapping() throws Exception {
        var base = Path.of("src/test/resources/nist-acvp");
        var manifest = com.google.gson.JsonParser.parseString(Files.readString(base.resolve("manifest.json"))).getAsJsonObject();
        for (var item : manifest.getAsJsonArray("files")) {
            var f = item.getAsJsonObject();
            byte[] bytes = Files.readAllBytes(base.resolve(f.get("name").getAsString()));
            assertEquals(f.get("sha256").getAsString(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
            assertEquals(f.get("size_bytes").getAsInt(), bytes.length);
        }
        var original = com.google.gson.JsonParser.parseString(Files.readString(base.resolve("generated-aes256/internalProjection.json"))).getAsJsonObject();
        var prepared = com.google.gson.JsonParser.parseString(Files.readString(base.resolve("aes-gcm-sample.json"))).getAsJsonObject();
        for (var g : prepared.getAsJsonArray("testGroups")) {
            var group = g.getAsJsonObject();
            var src = original.getAsJsonArray("testGroups").asList().stream()
                    .map(com.google.gson.JsonElement::getAsJsonObject)
                    .filter(x -> x.get("tgId").equals(group.get("tgId"))).findFirst().orElseThrow();
            assertEquals(src, group, "Selected groups must preserve all source values");
        }
    }
}
