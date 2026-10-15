package vn.edu.atbm.mssv1150080127.model;

/**
 * Lớp đóng gói kết quả sau khi giải mã gói tệp an toàn .secpkg thành công.
 * 
 * Tác giả: Trần Phạm Thiên Ân - MSSV: 1150080127
 */
public class SecurePackageResult {
    private final byte[] plainData;
    private final String originalFilename;
    private final boolean compressed;
    private final int packageSize;

    public SecurePackageResult(byte[] plainData, String originalFilename, boolean compressed, int packageSize) {
        this.plainData = plainData;
        this.originalFilename = originalFilename;
        this.compressed = compressed;
        this.packageSize = packageSize;
    }

    public byte[] getPlainData() {
        return plainData;
    }

    public String getOriginalFilename() {
        return originalFilename;
    }

    public boolean isCompressed() {
        return compressed;
    }

    public int getPackageSize() {
        return packageSize;
    }

    public int getPlainSize() {
        return plainData != null ? plainData.length : 0;
    }
}

