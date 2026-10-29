package vn.edu.atbm.mssv1150080127.util;

import com.google.gson.*;
import java.io.*;
import java.nio.file.Files;
import java.util.*;

/** Strict reader for the prepared NIST ACVP subset, not a general ACVP client. */
public class NistAcvpParser {
    public static class AesGcmTestCase {
        public int tcId, tgId, keyLen, tagLen;
        public String direction, comment;
        public byte[] key, iv, pt, aad, ct, tag;
        public boolean expectPass;
        @Override public String toString() { return "tg=" + tgId + "/tc=" + tcId + "/" + direction; }
    }

    private static byte[] hex(JsonObject obj, String field) {
        if (!obj.has(field)) throw new IllegalArgumentException("Missing field: " + field);
        return HexFormat.of().parseHex(obj.get(field).getAsString());
    }
    private static void length(byte[] value, int bits, String field) {
        if (value.length * 8 != bits) throw new IllegalArgumentException("Length mismatch: " + field);
    }
    public static List<AesGcmTestCase> parseAesGcmFile(File file) throws IOException {
        try (Reader reader = Files.newBufferedReader(file.toPath())) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            if (!Set.of("ACVP-AES-GCM", "AES-GCM").contains(root.get("algorithm").getAsString()))
                throw new IllegalArgumentException("Unsupported algorithm");
            List<AesGcmTestCase> cases = new ArrayList<>();
            Set<String> ids = new HashSet<>();
            for (JsonElement item : root.getAsJsonArray("testGroups")) {
                JsonObject group = item.getAsJsonObject();
                for (JsonElement entry : group.getAsJsonArray("tests")) {
                    JsonObject t = entry.getAsJsonObject();
                    AesGcmTestCase tc = new AesGcmTestCase();
                    tc.tgId = group.get("tgId").getAsInt();
                    tc.tcId = t.get("tcId").getAsInt();
                    if (!ids.add(tc.tgId + ":" + tc.tcId)) throw new IllegalArgumentException("Duplicate case ID");
                    tc.direction = group.get("direction").getAsString();
                    if (!Set.of("encrypt", "decrypt").contains(tc.direction)) throw new IllegalArgumentException("Invalid direction");
                    tc.keyLen = group.get("keyLen").getAsInt();
                    tc.tagLen = group.get("tagLen").getAsInt();
                    if (!Set.of(128, 192, 256).contains(tc.keyLen) || tc.tagLen != 128)
                        throw new IllegalArgumentException("Unsupported key/tag size in prepared subset");
                    tc.key = hex(t, "key"); tc.iv = hex(t, "iv"); tc.aad = hex(t, "aad");
                    tc.ct = hex(t, "ct"); tc.tag = hex(t, "tag");
                    tc.expectPass = t.has("testPassed") ? t.get("testPassed").getAsBoolean() : true;
                    tc.pt = t.has("pt") ? hex(t, "pt") : null;
                    if ((tc.expectPass || tc.direction.equals("encrypt")) && tc.pt == null)
                        throw new IllegalArgumentException("Positive case requires plaintext");
                    length(tc.key, tc.keyLen, "key"); length(tc.iv, group.get("ivLen").getAsInt(), "iv");
                    length(tc.aad, group.get("aadLen").getAsInt(), "aad"); length(tc.tag, tc.tagLen, "tag");
                    length(tc.ct, group.get("payloadLen").getAsInt(), "ct");
                    if (tc.pt != null) length(tc.pt, group.get("payloadLen").getAsInt(), "pt");
                    tc.comment = "NIST ACVP " + tc.keyLen + "-bit " + tc.direction + " (" + tc + ")";
                    cases.add(tc);
                }
            }
            if (cases.isEmpty()) throw new IllegalArgumentException("Empty vector set");
            return cases;
        }
    }

}
