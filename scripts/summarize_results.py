#!/usr/bin/env python3
"""Summarize all observations without discarding outliers (Python stdlib)."""
import csv, collections, statistics, pathlib, sys
from word_document import write_docx
folder = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'artifacts/midterm')
groups = collections.defaultdict(list)
with (folder / 'raw.csv').open() as f:
    for row in csv.DictReader(f):
        if row['Correct'] != 'true': raise ValueError('Incorrect recovery')
        groups[row['Dataset'], int(row['Size_Bytes']), row['Mode']].append(row)
rows = ['# Kết quả benchmark giữa kỳ', '', 'Sinh tự động từ `raw.csv`; không bỏ outlier. Thời gian là wall-clock toàn bộ pack/unpack, không phải thời gian AES thuần.', '', 'Mean ± sample SD; CI95% = mean ± 4.303 × SD/√3 (t, df=2). Chỉ 3 quan sát trong cùng JVM; CI mang tính thăm dò, giả định độc lập/xấp xỉ chuẩn còn yếu. Cận âm có thể xuất hiện do mẫu ít; không diễn giải thành thời gian âm.', '', '| Dữ liệu | Bytes | Chế độ | n | Pack ms (mean ± SD) | CI95% pack ms | Unpack ms (mean ± SD) | CI95% unpack ms | Gói bytes | Correct |', '|---|---:|---|---:|---:|---:|---:|---:|---:|---|']
with (folder / 'summary.csv').open('w') as f:
    writer = csv.writer(f); writer.writerow(['Dataset','Size_Bytes','Mode','N','EncMean_ms','EncSD_ms','EncCI95Low_ms','EncCI95High_ms','DecMean_ms','DecSD_ms','DecCI95Low_ms','DecCI95High_ms','PackageSize_Bytes','EncMiB_s'])
    for (dataset,size,mode), runs in groups.items():
        assert len(runs) == 3
        enc = [float(r['EncTime_ms']) for r in runs]; dec = [float(r['DecTime_ms']) for r in runs]
        em,es,dm,ds = statistics.mean(enc),statistics.stdev(enc),statistics.mean(dec),statistics.stdev(dec)
        eh,dh = 4.303*es/3**0.5,4.303*ds/3**0.5
        pkg = int(runs[0]['PackageSize_Bytes'])
        writer.writerow([dataset,size,mode,3,em,es,em-eh,em+eh,dm,ds,dm-dh,dm+dh,pkg,size/1048576/(em/1000)])
        rows.append(f'| {dataset} | {size} | {mode} | 3 | {em:.3f} ± {es:.3f} | [{em-eh:.3f}, {em+eh:.3f}] | {dm:.3f} ± {ds:.3f} | [{dm-dh:.3f}, {dm+dh:.3f}] | {pkg} | 3/3 |')
rows += ['', '## Cách diễn giải', '', '- So sánh bật/tắt GZIP là ablation một yếu tố; các tham số mật mã và tên tệp giữ nguyên.', '- Dữ liệu random-bytes là đối chứng khó nén, không phải plaintext mật mã sản xuất. Seed chỉ cố định dữ liệu.', '- Không suy rộng lợi ích nén sang mọi tệp; không đo mạng/đĩa nên không kết luận đã tiết kiệm thời gian truyền.', '- Chênh lệch nhỏ hơn mức dao động cần đo thêm. Không chọn lần tốt nhất và không tuyên bố vượt paper.', '- Độ phình baseline = 302 + số byte UTF-8 tên tệp. Tên benchmark.bin dài 13 byte nên overhead = 315 byte.', '- CI95% chi tiết và throughput nằm trong summary.csv; không bỏ outlier.']
write_docx(folder/'RESULTS.docx', 'Kết quả benchmark giữa kỳ', [('Phạm vi và thống kê', rows[2:6]), ('Bảng số liệu', [[['Dữ liệu','Bytes','Chế độ','Pack mean±SD ms','Unpack mean±SD ms','Gói bytes']] + [[k[0],k[1],k[2], f"{statistics.mean(float(x['EncTime_ms']) for x in v):.3f} ± {statistics.stdev(float(x['EncTime_ms']) for x in v):.3f}", f"{statistics.mean(float(x['DecTime_ms']) for x in v):.3f} ± {statistics.stdev(float(x['DecTime_ms']) for x in v):.3f}", v[0]['PackageSize_Bytes']] for k,v in groups.items()]]), ('Diễn giải', rows[-7:-1])])
print('Summarized', sum(map(len,groups.values())), 'measurements')
