package vn.edu.atbm.mssv1150080127.util;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Bộ trích xuất dữ liệu kiểm chuẩn NIST ACVP thuần Java (Zero-Dependency).
 * Giúp hệ thống hoạt động hoàn toàn độc lập, không bị phụ thuộc vào thư viện ngoài,
 * không gặp lỗi khi máy chấm thi không có kết nối Internet để tải Gson/Jackson.
 * 
 * Tác giả: Trần Phạm Thiên Ân - MSSV: 1150080127
 */
public class NistAcvpParser {

    public static class AesGcmTestCase {
        public int tcId;
        public String comment;
        public byte[] key;
        public byte[] iv;
        public byte[] pt;
        public byte[] aad;
        public byte[] ct;
        public byte[] tag;
        public boolean expectPass;
    }

    /**
     * Phân tích tệp JSON NIST ACVP AES-GCM và trả về danh sách các ca kiểm thử.
     */
    public static List<AesGcmTestCase> parseAesGcmFile(File jsonFile) throws IOException {
        String content = Files.readString(jsonFile.toPath());
        List<AesGcmTestCase> resultList = new ArrayList<>();

        // Tìm kiếm các khối test case bên trong mảng tests
        Pattern testBlockPattern = Pattern.compile("\\{[^\\{\\}]*\"tcId\"\\s*:\\s*(\\d+)[^\\{\\}]*\\}", Pattern.DOTALL);
        Matcher matcher = testBlockPattern.matcher(content);

        while (matcher.find()) {
            String block = matcher.group(0);
            AesGcmTestCase tc = new AesGcmTestCase();
            tc.tcId = Integer.parseInt(extractValue(block, "tcId", "0"));
            tc.comment = extractValue(block, "comment", "NIST Test Case #" + tc.tcId);

            String keyHex = extractValue(block, "key", null);
            String ivHex = extractValue(block, "iv", null);
            String ptHex = extractValue(block, "pt", null);
            String aadHex = extractValue(block, "aad", "");
            String ctHex = extractValue(block, "ct", null);
            String tagHex = extractValue(block, "tag", null);
            String passedStr = extractValue(block, "testPassed", "true");

            if (keyHex != null) tc.key = HexFormat.of().parseHex(keyHex);
            if (ivHex != null) tc.iv = HexFormat.of().parseHex(ivHex);
            if (ptHex != null) tc.pt = HexFormat.of().parseHex(ptHex);
            if (aadHex != null && !aadHex.isEmpty()) tc.aad = HexFormat.of().parseHex(aadHex);
            else tc.aad = new byte[0];
            if (ctHex != null) tc.ct = HexFormat.of().parseHex(ctHex);
            if (tagHex != null) tc.tag = HexFormat.of().parseHex(tagHex);
            tc.expectPass = Boolean.parseBoolean(passedStr);

            resultList.add(tc);
        }

        return resultList;
    }

    private static String extractValue(String block, String key, String defaultValue) {
        // Regex bắt giá trị chuỗi ("key": "value") hoặc số/boolean ("key": 123)
        Pattern pString = Pattern.compile("\"" + key + "\"\\s*:\\s*\"([^\"]*)\"");
        Matcher mString = pString.matcher(block);
        if (mString.find()) {
            return mString.group(1);
        }

        Pattern pPrimitive = Pattern.compile("\"" + key + "\"\\s*:\\s*([^\\s,\\}]+)");
        Matcher mPrimitive = pPrimitive.matcher(block);
        if (mPrimitive.find()) {
            return mPrimitive.group(1).trim();
        }

        return defaultValue;
    }
}

