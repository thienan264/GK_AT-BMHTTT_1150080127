#!/usr/bin/env python3
"""Generate study DOCX and updated slides with stdlib OOXML; no extra packages."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as E
from xml.sax.saxutils import escape
from word_document import write_docx
ROOT=Path(__file__).resolve().parents[1]
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
for prefix,uri in [('p',P),('a',A),('r',R)]:E.register_namespace(prefix,uri)
def xml(element):return E.tostring(element,encoding='utf-8',xml_declaration=True)
def slide(title, lines):
    def box(i,x,y,w,h,text,size,color,bold=False):
        paragraphs=''.join('<a:p><a:r><a:rPr lang="vi-VN" sz="'+str(size)+'" b="'+('1' if bold else '0')+'"><a:solidFill><a:srgbClr val="'+color+'"/></a:solidFill><a:latin typeface="Arial"/></a:rPr><a:t>'+escape(line)+'</a:t></a:r></a:p>' for line in text.split('\n'))
        return f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="Text {i}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody><a:bodyPr wrap="square"/><a:lstStyle/>{paragraphs}</p:txBody></p:sp>'
    shapes=box(2,450000,250000,11000000,950000,title,3000,'132B43',True)
    for i,line in enumerate(lines):shapes+=box(i+3,550000,1450000+i*780000,10800000,730000,line,2100,'183247')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<p:sld xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"><p:cSld><p:bg><p:bgPr><a:solidFill><a:srgbClr val="F5F7FA"/></a:solidFill><a:effectLst/></p:bgPr></p:bg><p:spTree>'
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
        +shapes+'</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>').encode()
def main():
    text=(ROOT/'docs/03_Hoan_thien_va_thuyet_trinh.md').read_text()
    sections=[];heading='';items=[]
    for paragraph in text.split('\n\n'):
        if paragraph.startswith('# '):continue
        if paragraph.startswith('## '):
            if items:sections.append((heading,items))
            heading=paragraph[3:];items=[]
        else:items.append(paragraph)
    if items:sections.append((heading,items))
    write_docx(ROOT/'docs/03_Hoan_thien_va_thuyet_trinh.docx','Bản hoàn thiện — Học và thuyết trình',sections)
    source=ROOT/'presentation/1150080127_Bao_cao_GK.pptx'
    with ZipFile(source) as z:data={name:z.read(name) for name in z.namelist()}
    # Keep original AES/OAEP teaching slides, add three new slides before demo.
    additions=[
      ('Quản lý khoá: sử dụng qua nhiều lần khởi động',[
       'AES mới mỗi gói; bản AES được RSA bọc nằm trong .secpkg.',
       'Alice và Bob: hai cặp RSA riêng, lưu trong PKCS#12.',
       'Mật khẩu mở keystore; không phải khoá AES hoặc RSA.',
       'Public key chia sẻ; private key giữ kín và sao lưu có bảo vệ.',
       'Sai mật khẩu: từ chối chạy. Không tự sinh khoá thay thế.'],
       'Demo init tạo khoá một lần; run nạp lại cùng keystore. Mất cache không làm mất khả năng đọc gói đã lưu. Private key vẫn ở RAM khi dùng. Đổi mật khẩu khác đổi cặp RSA. Không đưa keystore hoặc mật khẩu vào slide.'),
      ('RSA-PSS: xác thực người gửi theo khoá đã tin cậy',[
       'Alice: mã hoá lai cho Bob → ký toàn bộ gói bằng private key Alice.',
       'Bob: kiểm tra bằng public key Alice đã xác minh → mới giải mã.',
       'PSS: SHA-256, MGF1-SHA-256, salt 32 byte; cặp khoá ký riêng.',
       'Gói SSP2 = header ngoài + SECP v1 + chữ ký; thêm 264 byte.',
       'Có public key Bob không đủ giả chữ ký Alice. Không tự tin khoá trong gói.'],
       'Nguồn RFC 8017 mục 8.1. Chữ ký không phải mã hoá bằng private key. SHA-256 public key DER dùng để đối chiếu qua kênh tin cậy. Tag GCM không xác định Alice vì ai có public key Bob cũng có thể tạo gói đúng. Chữ ký đúng không chứng minh tệp không có mã độc. Chưa chống replay.'),
      ('Phạm vi cục bộ và hai hướng phát triển',[
       'Hiện tại: HTTP tại 127.0.0.1; không mở dịch vụ ra mạng.',
       'Máy và người vận hành tin cậy; kiểm tra Host/Origin.',
       'Hướng 1: desktop cục bộ, chỉ gửi gói đã mã hoá và ký.',
       'Hướng 2: có server qua mạng → HTTPS, xác thực, phân quyền.',
       'Nội bộ không tự an toàn; server đọc bản rõ vẫn phải được tin cậy.'],
       'HTTPS thuộc hướng phát triển khi có kết nối qua mạng. Hiện giao diện trình duyệt gọi JVM trên cùng máy qua loopback. Chưa chống phần mềm độc hại trên máy. Cache TTL 5 phút, tối đa 64 MiB. Không tự mở tệp nhận được.')]
    presentation=E.fromstring(data['ppt/presentation.xml']);ids=presentation.find('{'+P+'}sldIdLst')
    relationships=E.fromstring(data['ppt/_rels/presentation.xml.rels']);types=E.fromstring(data['[Content_Types].xml'])
    # Clone only the existing layout relationship for newly built slides.
    layoutrels=E.fromstring(data['ppt/slides/_rels/slide16.xml.rels'])
    layout=next(n.attrib['Target'] for n in layoutrels if n.attrib['Type'].endswith('/slideLayout'))
    for i,(title,lines,note) in enumerate(additions,17):
        data[f'ppt/slides/slide{i}.xml']=slide(title,lines)
        rels=E.Element('{'+REL+'}Relationships')
        E.SubElement(rels,'{'+REL+'}Relationship',Id='rId1',Type=R+'/slideLayout',Target=layout)
        E.SubElement(rels,'{'+REL+'}Relationship',Id='rId2',Type=R+'/notesSlide',Target=f'../notesSlides/notesSlide{i}.xml')
        data[f'ppt/slides/_rels/slide{i}.xml.rels']=xml(rels)
        notes=E.fromstring(data['ppt/notesSlides/notesSlide15.xml'])
        for sp in notes.iter('{'+P+'}sp'):
            ph=sp.find('.//{'+P+'}ph')
            if ph is not None and ph.get('type')=='body':
                for n in sp.iter('{'+A+'}t'):n.text=''
                texts=list(sp.iter('{'+A+'}t'))
                if texts:texts[0].text=note
        data[f'ppt/notesSlides/notesSlide{i}.xml']=xml(notes)
        nr=E.fromstring(data['ppt/notesSlides/_rels/notesSlide15.xml.rels'])
        for n in nr:
            if n.get('Type').endswith('/slide'):n.set('Target',f'../slides/slide{i}.xml')
        data[f'ppt/notesSlides/_rels/notesSlide{i}.xml.rels']=xml(nr)
        rid='rIdUpgrade'+str(i)
        E.SubElement(relationships,'{'+REL+'}Relationship',Id=rid,Type=R+'/slide',Target=f'slides/slide{i}.xml')
        ids.insert(13+i-17,E.Element('{'+P+'}sldId',{'id':str(1000+i),'{'+R+'}id':rid}))
        for part,kind in [(f'/ppt/slides/slide{i}.xml','slide'),(f'/ppt/notesSlides/notesSlide{i}.xml','notesSlide')]:
            E.SubElement(types,'{'+CT+'}Override',PartName=part,ContentType='application/vnd.openxmlformats-officedocument.presentationml.'+kind+'+xml')
    data['ppt/slides/slide15.xml']=slide('Kết quả, bằng chứng và giới hạn',[
        'Giữ AES-GCM/OAEP; thêm keystore, PSS và tách vai trò.',
        '157 kiểm thử JUnit; có đối chiếu PSS bằng OpenSSL độc lập.',
        'HTTP cục bộ: chặn khác nguồn, tách vai trò, restart, sai mật khẩu.',
        '140 vector trên web chỉ kiểm tra AES/OAEP, không chứng nhận NIST.',
        'Chưa chống replay, quét mã độc hoặc E2EE chống server.'])
    # Replace stale notes on demo/summary; body placeholder contains presentation notes.
    for number,message in [(14,'Mở http://127.0.0.1:8080. Tạo gói có chữ ký, tải xuống, xác thực và giải mã. Sửa bit trực tiếp trong bản sao tệp rồi tải lên phải bị từ chối; thử private key khác cũng bị từ chối. Dừng và mở lại cùng keystore để giải mã gói đã lưu. Tab NIST chỉ đối chiếu AES/OAEP. Không tự mở tệp không rõ nguồn.'),(15,'157 ca kiểm thử hiện tại gồm primitive, định dạng và các ca chữ ký mới. PSS được OpenSSL xác minh độc lập. scripts/check_upgrade.py kiểm tra HTTP loopback, hai vai trò và restart thật. Benchmark cũ là SECP v1 không có PSS, không dùng nó để tuyên bố hiệu năng bản mới. Chưa kiểm toán hoặc chứng nhận an toàn toàn hệ thống.')]:
        rels=E.fromstring(data[f'ppt/slides/_rels/slide{number}.xml.rels'])
        target=next(n.get('Target') for n in rels if n.get('Type').endswith('/notesSlide'))
        name='ppt/'+target.removeprefix('../');notes=E.fromstring(data[name])
        for sp in notes.iter('{'+P+'}sp'):
            ph=sp.find('.//{'+P+'}ph')
            if ph is not None and ph.get('type')=='body':
                texts=list(sp.iter('{'+A+'}t'))
                for n in texts:n.text=''
                if texts:texts[0].text=message
        data[name]=xml(notes)
    # Correct slide numbering for the new order without altering teaching diagrams.
    for number in range(1,17):
        name=f'ppt/slides/slide{number}.xml';tree=E.fromstring(data[name])
        for n in tree.iter('{'+A+'}t'):
            if n.text and '/ 16' in n.text:n.text=n.text.replace(f'{number:02d} / 16',f'{number if number<14 else number+3:02d} / 19')
        data[name]=xml(tree)
    data['ppt/presentation.xml']=xml(presentation)
    data['ppt/_rels/presentation.xml.rels']=xml(relationships)
    data['[Content_Types].xml']=xml(types)
    app=E.fromstring(data['docProps/app.xml'])
    for n in app:
        if n.tag.endswith('}Slides'):n.text='19'
        if n.tag.endswith('}Notes'):n.text=str(sum(name.startswith('ppt/notesSlides/notesSlide') and name.endswith('.xml') for name in data))
    data['docProps/app.xml']=xml(app)
    with ZipFile(ROOT/'presentation/1150080127_Bao_cao_GK_Hoan_thien.pptx','w',ZIP_DEFLATED) as z:
        for name,content in data.items():z.writestr(name,content)
    print('Generated study DOCX and 19-slide final presentation; original deck preserved.')
if __name__=='__main__':main()
