package vn.edu.atbm.mssv1150080127.util;

import java.nio.file.*;
import java.util.*;
import vn.edu.atbm.mssv1150080127.crypto.AesGcm;

/** Live reference checks used by the UI; source and parameter coverage remain explicit. */
public final class ReferenceChecks {
    public static Map<String,Object> run() throws Exception {
        List<Map<String,Object>> rows=new ArrayList<>();
        for (String[] set : new String[][]{
                {"NIST GenVal ACVP / AES-256", "src/test/resources/nist-acvp/aes-gcm-sample.json"}}) {
            for (var tc : NistAcvpParser.parseAesGcmFile(Path.of(set[1]).toFile())) {
                Map<String,Object> r=new LinkedHashMap<>();
                r.put("source",set[0]); r.put("caseId",tc.toString());r.put("operation",tc.direction);
                r.put("implementation","AesGcm."+tc.direction+" — also used by SecurePackageEngine");
                r.put("key",hex(tc.key));r.put("iv",hex(tc.iv));r.put("aad",hex(tc.aad));r.put("plaintext",tc.pt==null?null:hex(tc.pt));
                byte[] combined=new byte[tc.ct.length+tc.tag.length];
                System.arraycopy(tc.ct,0,combined,0,tc.ct.length);System.arraycopy(tc.tag,0,combined,tc.ct.length,tc.tag.length);
                r.put("expected",tc.direction.equals("encrypt")?hex(combined):(tc.expectPass?hex(tc.pt):"REJECT authentication"));
                try {
                    AesGcmVectorVerifier.verify(tc);
                    r.put("status","PASS");

                    try { r.put("actual",hex(tc.direction.equals("encrypt")?AesGcm.encrypt(tc.key,tc.iv,tc.aad,tc.pt):AesGcm.decrypt(tc.key,tc.iv,tc.aad,combined))); }
                    catch(javax.crypto.AEADBadTagException e) { r.put("actual","REJECT authentication"); }
                } catch(Exception e) {r.put("status","FAIL");r.put("actual",e.toString());}
                rows.add(r);
            }
        }
        for (var tc:KtsOaepVectors.cases()) {
            Map<String,Object> r=new LinkedHashMap<>();r.put("source","NIST GenVal ACVP / KTS-OAEP SHA-256");
            r.put("caseId","tg="+tc.get("sourceGroup").getAsInt()+"/tc="+tc.get("tcId").getAsInt());r.put("operation","unwrapKey RSA-2048 OAEP SHA-256, AES 32 bytes, empty label");
            r.put("implementation","RsaKeyManager.unwrapKey — exact method used by the package");
            r.put("expected",hex(KtsOaepVectors.expected(tc)));
            try {byte[] actual=KtsOaepVectors.actual(tc);KtsOaepVectors.verify(tc);r.put("actual",hex(actual));r.put("status","PASS");}
            catch(Exception e){r.put("actual",e.toString());r.put("status","FAIL");}rows.add(r);
        }
        long passed=rows.stream().filter(r->r.get("status").equals("PASS")).count();
        Map<String,Object> result=new LinkedHashMap<>();result.put("success",passed==rows.size());result.put("passed",passed);result.put("total",rows.size());result.put("testCases",rows);
        result.put("scope","120 AES-256-GCM + 20 OAEP SHA-256 unwrap checks from vectors generated locally by pinned NIST GenVal. Exact package parameters. Fresh wrap/unwrap responses are separately checked by the local NIST validator; see saved validation.json. Not NIST certification.");
        return result;
    }
    private static String hex(byte[] b){return HexFormat.of().formatHex(b);}
}
