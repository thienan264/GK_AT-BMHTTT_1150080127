package vn.edu.atbm.mssv1150080127;
import org.junit.jupiter.api.*;
import java.util.stream.Stream;
import vn.edu.atbm.mssv1150080127.util.KtsOaepVectors;
import static org.junit.jupiter.api.Assertions.*;
class RsaOaepVectorTest {
    @TestFactory Stream<DynamicTest> nistOaepSha256ExactPackageParameters() throws Exception {
        return KtsOaepVectors.cases().stream().map(tc -> DynamicTest.dynamicTest("NIST-GenVal-KTS/tg"+tc.get("sourceGroup").getAsInt()+"/tc"+tc.get("tcId").getAsInt(), () -> KtsOaepVectors.verify(tc)));
    }
    @Test void wrongNistAnswerIsRejected() throws Exception {
        var tc=KtsOaepVectors.cases().get(0).deepCopy();
        String field=tc.has("iutK")?"iutK":"serverK";
        String key=tc.get(field).getAsString();tc.addProperty(field, (key.startsWith("00")?"01":"00")+key.substring(2));
        assertThrows(SecurityException.class, () -> KtsOaepVectors.verify(tc));
    }
    @Test void savedNistValidatorAcceptedBothProductionDirectionsAndRejectedNegativeControl() throws Exception {
        var base=java.nio.file.Path.of("src/test/resources/nist-acvp/generated-kts-sha256");
        var evidence=com.google.gson.JsonParser.parseString(java.nio.file.Files.readString(base.resolve("java-validation-evidence.json"))).getAsJsonObject();
        var verdict=com.google.gson.JsonParser.parseString(java.nio.file.Files.readString(base.resolve("validation.json"))).getAsJsonObject();
        assertEquals("passed",verdict.get("disposition").getAsString());
        assertEquals(20,verdict.getAsJsonArray("tests").size());
        assertEquals(10,evidence.get("wrap_cases").getAsInt());assertEquals(10,evidence.get("unwrap_cases").getAsInt());
        var negative=com.google.gson.JsonParser.parseString(java.nio.file.Files.readString(base.resolve("negative-validation.json"))).getAsJsonObject();
        assertNotEquals("passed",negative.get("disposition").getAsString());
        for(var entry:evidence.getAsJsonObject("source_sha256").entrySet()) {
            var current=java.nio.file.Path.of(entry.getKey());
            var snapshot=java.nio.file.Path.of("src/test/resources/nist-acvp/validated-source").resolve(current.getFileName()+".txt");
            byte[] bytes=java.nio.file.Files.readAllBytes(java.nio.file.Files.exists(snapshot)?snapshot:current);
            assertEquals(entry.getValue().getAsString(),java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)),"Historical source hash mismatch");
            if(java.nio.file.Files.exists(snapshot)) {
                var original=java.nio.file.Files.readAllLines(snapshot).stream().filter(line->!line.stripLeading().startsWith("//")).toList();
                var cleaned=java.nio.file.Files.readAllLines(current).stream().filter(line->!line.isBlank()).toList();
                assertEquals(original.stream().filter(line->!line.isBlank()).toList(),cleaned,"Only standalone comments may differ from validated source");
            }
        }
    }
}
