package vn.edu.atbm.mssv1150080127.crypto;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

/**
 * Tiện ích nén và giải nén dữ liệu lossless bằng chuẩn GZIP.
 * Được tích hợp trong Biến thể (Variant) nhằm đánh giá sự thay đổi kích thước và hiệu năng.
 * 
 * Tác giả: Trần Phạm Thiên Ân - MSSV: 1150080127
 */
public class GzipUtil {

    /**
     * Nén mảng byte bằng luồng GZIPOutputStream.
     *
     * @param data Dữ liệu gốc chưa nén
     * @return Mảng byte đã nén theo định dạng GZIP
     * @throws IOException Lỗi I/O luồng
     */
    public static byte[] compress(byte[] data) throws IOException {
        if (data == null || data.length == 0) {
            return new byte[0];
        }
        ByteArrayOutputStream byteOut = new ByteArrayOutputStream();
        try (GZIPOutputStream gzipOut = new GZIPOutputStream(byteOut)) {
            gzipOut.write(data);
            gzipOut.finish();
        }
        return byteOut.toByteArray();
    }

    /**
     * Giải nén mảng byte GZIP bằng GZIPInputStream.
     *
     * @param compressedData Mảng byte đã nén
     * @return Dữ liệu gốc đã phục hồi
     * @throws IOException Lỗi định dạng nén hoặc dữ liệu bị hỏng
     */
    public static byte[] decompress(byte[] compressedData) throws IOException {
        if (compressedData == null || compressedData.length == 0) {
            return new byte[0];
        }
        ByteArrayInputStream byteIn = new ByteArrayInputStream(compressedData);
        ByteArrayOutputStream byteOut = new ByteArrayOutputStream();
        try (GZIPInputStream gzipIn = new GZIPInputStream(byteIn)) {
            byte[] buffer = new byte[4096];
            int bytesRead;
            while ((bytesRead = gzipIn.read(buffer)) != -1) {
                byteOut.write(buffer, 0, bytesRead);
            }
        }
        return byteOut.toByteArray();
    }
}

