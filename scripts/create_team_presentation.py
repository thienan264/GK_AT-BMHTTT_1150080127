#!/usr/bin/env python3
"""Build a seven-slide, five-minute team presentation and rehearsal guide."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as E
from xml.sax.saxutils import escape
import json, re
from word_document import write_docx

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'presentation'
DOCS=ROOT/'docs'
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
for prefix,uri in [('p',P),('a',A),('r',R)]:E.register_namespace(prefix,uri)
NAVY='142D43';TEAL='087F75';INK='233E51';MUTED='5C7283';BG='F3F6FA';WHITE='FFFFFF';LIGHT='E3F3EF';BLUE='E7EEF9';GOLD='FFF1D6'
SLIDES=[]

SCRIPTS=[
('Thành viên 1 — AES-GCM',[
('Slide 1 · 00:00–00:30', 'Nhóm em xây dựng công cụ trao đổi tệp bằng mã hoá lai. Trước hết, AES-256-GCM xử lý nội dung tệp. Mỗi lần mã hoá, ứng dụng sinh khoá AES 32 byte và IV 12 byte mới bằng bộ sinh ngẫu nhiên an toàn. AES-GCM biến tệp gốc thành bản mã và tạo thêm tag xác thực. Vì vậy, người không có khoá phù hợp không đọc được nội dung.'),
('Slide 2 · 00:30–01:00', 'GCM còn phát hiện dữ liệu bị sửa. Khi giải mã, ứng dụng kiểm tra tag; sai thì không trả bản rõ. Header được đưa vào AAD, nên tên tệp vẫn nhìn thấy nhưng được bảo vệ toàn vẹn. Tuy nhiên, khoá AES phải được chuyển cho người nhận một cách an toàn. Phần tiếp theo trình bày cách RSA-OAEP giải quyết vấn đề này.')]),
('Thành viên 2 — RSA-OAEP',[
('Slide 3 · 01:00–01:30', 'RSA-OAEP chỉ bọc khoá AES, không mã hoá toàn bộ tệp. Alice dùng public key Bob để bọc khoá AES 32 byte thành khối 256 byte. Bob dùng private key tương ứng để mở lại khoá AES. OAEP là cấu trúc mã hoá có ngẫu nhiên; bài dùng SHA-256 và MGF1-SHA-256, không sử dụng RSA thuần.'),
('Slide 4 · 01:30–02:00', 'Gói trao đổi mang khoá AES đã bọc, IV, header và bản mã kèm tag. Bob mở khoá AES rồi dùng AES-GCM khôi phục tệp, chỉ nhận kết quả khi xác thực thành công. AES xử lý dữ liệu, RSA bảo vệ khoá: đó là mã hoá lai. Nhưng ai có public key Bob cũng tạo được gói hợp lệ, nên vẫn cần xác thực người gửi.')]),
('Thành viên 3 — Xác thực và quản lý khoá',[
('Slide 5 · 02:00–02:30', 'Để xác thực người gửi, Alice dùng private key ký riêng để ký toàn bộ gói bằng RSA-PSS. Bob kiểm tra bằng public key Alice đã tin cậy trước khi giải mã. Fingerprint là SHA-256 của public key, được đối chiếu qua kênh tin cậy để tránh nhận nhầm khoá. Chữ ký hợp lệ xác thực theo khoá; không bảo đảm tệp sạch mã độc.'),
('Slide 6 · 02:30–03:00', 'Private key được lưu trong keystore có mật khẩu, nên khởi động lại không phải tạo RSA mới. Public key được chia sẻ qua chứng thư; private key giữ kín. Bản này chạy HTTP chỉ trên localhost. Bộ 157 kiểm thử đã đạt. Hướng phát triển là ứng dụng desktop, hoặc thêm HTTPS khi dùng server qua mạng. Sau đây là phần demo trong hai phút.')])]

class Slide:
    def __init__(self,section,title,subtitle,time,hidden=False):
        self.items=[];self.hidden=hidden;self.notes='';self.section=section;self.title=title;self.time=time
        self.rect(0,0,1280,720,BG)
        self.rect(0,0,1280,9,TEAL)
        self.text(section.upper(),58,38,950,26,15,TEAL,True)
        self.text(title,58,94,1160,105,36,NAVY,True)
        self.text(subtitle,60,197,1150,60,19,MUTED)
        self.line(58,670,1164,'D9E3EB')
        self.text('MÃ HOÁ LAI  ·  NHÓM 4 THÀNH VIÊN',60,686,800,20,12,MUTED)
        self.text(time,920,683,300,24,14,TEAL,True,align='r')
        SLIDES.append(self)
    def rect(self,x,y,w,h,fill,line=None,radius=False):self.items.append(dict(kind='rect',x=x,y=y,w=w,h=h,fill=fill,line=line,radius=radius))
    def line(self,x,y,w,color):self.rect(x,y,w,1,color)
    def text(self,text,x,y,w,h,size=24,color=INK,bold=False,align='l',mono=False):self.items.append(dict(kind='text',text=text,x=x,y=y,w=w,h=h,size=size,color=color,bold=bold,align=align,mono=mono))
    def card(self,x,y,w,h,label,body,fill=WHITE):
        self.rect(x,y,w,h,fill,radius=True)
        self.text(label,x+22,y+20,w-44,52,22,TEAL,True)
        self.text(body,x+22,y+81,w-44,h-92,23,INK)
    def box(self,x,y,w,label,body,fill=WHITE):
        self.rect(x,y,w,150,fill,radius=True)
        self.text(label,x+12,y+18,w-24,45,23,TEAL,True,align='ctr')
        self.text(body,x+12,y+73,w-24,62,22,INK,align='ctr')
    def arrow(self,x,y):self.text('→',x,y,58,65,36,TEAL,True,align='ctr')
    def banner(self,text,y=573,fill=LIGHT):
        self.rect(58,y,1164,70,fill,radius=True);self.text(text,80,y+19,1120,44,21,TEAL,True)

s=Slide('01 / AES-GCM · Thành viên 1','Mã hoá nội dung bằng AES-GCM','Bài toán: gửi tệp bí mật và phát hiện dữ liệu bị sửa.','00:00–00:30')
s.box(60,300,300,'TỆP GỐC','Văn bản, ảnh, tài liệu')
s.arrow(365,342)
s.box(430,300,340,'AES-256-GCM','Khoá AES mới + IV mới',LIGHT)
s.arrow(775,342)
s.box(840,300,380,'KẾT QUẢ','Bản mã + tag xác thực')
s.banner('AES: 32 byte khoá  ·  IV: 12 byte  ·  Tag: 16 byte')

s=Slide('01 / AES-GCM · Thành viên 1','GCM kiểm tra toàn vẹn trước khi trả tệp','AEAD: bảo mật nội dung, đồng thời xác thực bản mã và AAD.','00:30–01:00')
s.card(60,283,550,245,'NỘI DUNG TỆP','Được mã hoá thành bản mã.\nTag sai → từ chối bản rõ.')
s.card(635,283,585,245,'HEADER → AAD','Tên tệp vẫn nhìn thấy.\nSửa header → kiểm tra thất bại.')
s.banner('Câu hỏi tiếp theo: chuyển khoá AES cho Bob thế nào?')

s=Slide('02 / RSA-OAEP · Thành viên 2','RSA chỉ bảo vệ khoá AES','Không dùng RSA để mã hoá toàn bộ nội dung tệp.','01:00–01:30')
s.box(60,300,295,'KHOÁ AES','32 byte ngẫu nhiên')
s.arrow(360,342)
s.box(425,300,345,'RSA-2048-OAEP','Public key của Bob',LIGHT)
s.arrow(775,342)
s.box(840,300,380,'KHOÁ ĐÃ BỌC','256 byte')
s.banner('Bob dùng private key để mở  ·  OAEP: SHA-256 / MGF1-SHA-256')

s=Slide('02 / RSA-OAEP · Thành viên 2','Hai thuật toán, một gói trao đổi','AES xử lý nội dung  ·  RSA chuyển khoá AES cho người nhận.','01:30–02:00')
widths=[220,250,150,400];labels=['METADATA','AES ĐÃ BỌC','IV','BẢN MÃ + TAG'];x=60
for w,label in zip(widths,labels):
    s.rect(x,290,w,95,LIGHT if label=='AES ĐÃ BỌC' else WHITE,radius=True)
    s.text(label,x+8,323,w-16,44,20,TEAL,True,align='ctr');x+=w+15
s.text('Sơ đồ thành phần gói lai; chữ ký được bổ sung bên ngoài.',64,405,1130,45,20,MUTED)
s.text('BOB: mở AES → xác thực GCM → khôi phục tệp',64,480,1140,62,28,NAVY,True)
s.banner('Có public key Bob chưa chứng minh người gửi là Alice.',fill=GOLD)

s=Slide('03 / Xác thực · Thành viên 3','Đúng người gửi: chữ ký RSA-PSS','Alice và Bob dùng hai cặp khoá với mục đích riêng.','02:00–02:30')
s.card(60,280,550,225,'ALICE KÝ','Gói mã hoá + private key Alice\n→ Chữ ký RSA-PSS',LIGHT)
s.card(635,280,585,225,'BOB KIỂM TRA','Public key Alice đã tin cậy\n→ Hợp lệ mới giải mã')
s.text('Fingerprint = SHA-256(public key DER)',76,530,1110,45,25,NAVY,True)
s.banner('Đối chiếu fingerprint qua kênh tin cậy để nhận đúng khoá.')

s=Slide('03 / Quản lý khoá · Thành viên 3','Lưu khoá để sử dụng qua nhiều lần chạy','Không sinh cặp RSA mới mỗi khi mở lại ứng dụng.','02:30–03:00')
s.card(60,280,550,215,'PRIVATE KEY · .p12','Keystore có mật khẩu\nGiữ kín, sao lưu có bảo vệ')
s.card(635,280,585,215,'PUBLIC KEY · .cer','Chia sẻ cho bên còn lại\nXác minh bằng fingerprint')
s.text('157 kiểm thử đạt  ·  Demo chỉ chạy trên localhost',76,519,1130,45,25,NAVY,True)
s.banner('Phát triển: desktop cục bộ  /  Có server qua mạng → HTTPS')

s=Slide('04 / Demo · Trần Phạm Thiên Ân','Tạo gói, mở gói và thử sửa đổi','Demo trực tiếp  ·  http://127.0.0.1:8080','03:00–05:00')
for i,(time,title,body) in enumerate([
    ('25 GIÂY','Mã hoá và ký','Tạo gói .signed.secpkg'),
    ('35 GIÂY','Xác thực và giải mã','Khôi phục đúng nội dung'),
    ('30 GIÂY','Gói bị sửa một bit','Bị từ chối, không trả bản rõ'),
    ('30 GIÂY','Đối chiếu và kết luận','140 ca AES/OAEP trên web')]):
    x=60+(i%2)*585;y=275+(i//2)*148
    s.rect(x,y,560,130,WHITE,radius=True)
    s.text(time,x+17,y+13,125,30,13,TEAL,True)
    s.text(title,x+150,y+14,390,44,23,NAVY,True)
    s.text(body,x+150,y+65,390,48,20,INK)
s.banner('Kết quả mong đợi: đúng khoá mở được; gói bị sửa bị từ chối.')
s.notes='''03:00–03:25: Chọn tệp nhỏ đã chuẩn bị, mã hoá và ký, tải gói xuống. Nói: “Mỗi gói có AES mới; AES được RSA bọc và gói được Alice ký.”
03:25–04:00: Giải mã gói vừa tạo, chỉ senderVerified=true, tải tệp phục hồi và mở nội dung đã chuẩn bị. Nói: “Chữ ký được kiểm tra trước; nội dung khôi phục khớp tệp gốc.”
04:00–04:30: Chọn bản sao gói đã sửa bit và chuẩn bị từ trước bằng cùng bộ khoá. Thử giải mã, chỉ lỗi và không có link tải bản rõ. Không sửa hex trực tiếp trong giờ nếu chưa tập chắc.
04:30–04:50: Chuyển tab kiểm thử, chạy 140 ca AES/OAEP và chỉ kết quả. Không gọi đây là chứng nhận NIST hay kiểm thử PSS.
04:50–05:00: Kết luận: “Nhóm đã kết hợp bảo mật nội dung, bảo vệ khoá và xác thực người gửi trong một công cụ cục bộ. Em cảm ơn thầy.”
Không demo restart, tạo khoá, nhập mật khẩu hoặc thử khoá khác trong 2 phút. Các tình huống này đã kiểm thử và để trả lời khi được hỏi. Nếu lỗi thao tác, dừng sau 5 giây và báo đúng trạng thái; chỉ dùng bằng chứng đã lưu nếu nói rõ đó là kết quả đã chạy, không giả kết quả trực tiếp.'''

s=Slide('Dự phòng / Không trình bày trong 5 phút','RSA-PSS: cấu trúc bên trong chữ ký','Chỉ mở khi thầy hỏi; không nằm trong luồng trình chiếu chính.','DỰ PHÒNG',True)
s.text('EM trước phép toán RSA',70,273,1100,40,25,NAVY,True)
for x,w,label,body in [(60,620,'maskedDB','223 byte'),(695,300,'H','32 byte'),(1010,210,'0xBC','1 byte')]:
    s.box(x,340,w,label,body,LIGHT if label=='maskedDB' else WHITE)
s.banner('EM: 256 byte  →  RSA bằng private key Alice  →  Chữ ký: 256 byte')
s.notes='RSA-2048, SHA-256, MGF1-SHA-256, salt32. mHash=SHA256(M). H=SHA256(8 byte0 || mHash || salt). DB=190 byte0 || 01 || salt =223 byte. MGF1(H) tạo mask223; XOR và đặt bit cao nhất0 thành maskedDB. EM=maskedDB || H || BC. Bob dùng public key Alice khôi phục EM để kiểm tra cấu trúc và tính lại H. EM không phải chữ ký, salt không bí mật và không tự chống replay. Nguồn: RFC8017 mục9.1.'

s=Slide('Dự phòng / Không trình bày trong 5 phút','Giới hạn và hướng phát triển','Dùng để trả lời câu hỏi; không mở sau demo nếu hết thời gian.','DỰ PHÒNG',True)
s.card(60,280,550,260,'GIỚI HẠN HIỆN TẠI','Tin máy và người vận hành.\nChưa chống replay.\nChữ ký không quét mã độc.')
s.card(635,280,585,260,'HAI HƯỚNG PHÁT TRIỂN','Desktop: chỉ gửi gói bảo mật.\nServer qua mạng: HTTPS,\nxác thực và phân quyền.')
s.banner('140 vector AES/OAEP không phải chứng nhận NIST cho hệ thống.')
s.notes='157 JUnit gồm kiểm thử primitive/gói/chữ ký; OpenSSL xác minh PSS độc lập. 140 ca trên web chỉ là120 AES và20 OAEP, không cộng chúng thành157 ca cùng loại. Benchmark lịch sử SECPv1 không gồm PSS. Private key trong keystore có thể xuất nếu có mật khẩu; chưa KMS/HSM. Public key phải xác minh qua kênh tin cậy. HTTP chỉloopback, không dùng qua LAN. Nguồn: mã nguồn dự án, bộ kiểm thử, RFC5116/RFC8017, tài liệu JDK21 keytool.'

for i,(_,parts) in enumerate(SCRIPTS):
    for j,(timing,speech) in enumerate(parts):
        SLIDES[i*2+j].notes=timing+'\n'+speech+'\n\nMục tiêu: nói khoảng 25–27 giây, dành phần còn lại để chỉ sơ đồ hoặc đổi slide/chuyển người. Mốc 60 giây là giới hạn cho cả phần, gồm chuyển lượt. Phải tập có bấm giờ; không tự thêm giải thích khi đang trình bày.'

def xml(node):return E.tostring(node,encoding='utf-8',xml_declaration=True)
def shape_xml(item,index):
    x,y,w,h=[round(item[key]*9525) for key in ('x','y','w','h')]
    transform=f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'
    start=f'<p:sp><p:nvSpPr><p:cNvPr id="{index}" name="Element {index}"/><p:cNvSpPr'+(' txBox="1"' if item['kind']=='text' else '')+'/><p:nvPr/></p:nvSpPr>'
    if item['kind']=='rect':
        geometry='roundRect' if item['radius'] else 'rect'
        return start+f'<p:spPr>{transform}<a:prstGeom prst="{geometry}"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{item["fill"]}"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr></p:sp>'
    paragraphs=[]
    for line in item['text'].split('\n'):
        paragraphs.append(f'<a:p><a:pPr algn="{item["align"]}"><a:lnSpc><a:spcPct val="112000"/></a:lnSpc><a:spcAft><a:spcPts val="600"/></a:spcAft></a:pPr><a:r><a:rPr lang="vi-VN" sz="{round(item["size"]*75)}" b="{int(item["bold"])}"><a:solidFill><a:srgbClr val="{item["color"]}"/></a:solidFill><a:latin typeface="Arial"/><a:ea typeface="Arial"/><a:cs typeface="Arial"/></a:rPr><a:t>{escape(line)}</a:t></a:r></a:p>')
    return start+f'<p:spPr>{transform}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody><a:bodyPr wrap="square" lIns="0" rIns="0" tIns="0" bIns="0"><a:noAutofit/></a:bodyPr><a:lstStyle/>'+''.join(paragraphs)+'</p:txBody></p:sp>'

def slide_xml(slide):
    hidden=' show="0"' if slide.hidden else ''
    shapes=''.join(shape_xml(item,i+2) for i,item in enumerate(slide.items))
    return (f'<p:sld xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"{hidden}><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'+shapes+'</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>').encode()

def notes_xml(text):
    paragraphs=''.join('<a:p><a:r><a:rPr lang="vi-VN"/><a:t>'+escape(line)+'</a:t></a:r></a:p>' for line in text.split('\n'))
    return (f'<p:notes xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/><p:sp><p:nvSpPr><p:cNvPr id="2" name="Notes"/><p:cNvSpPr/><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>'+paragraphs+'</p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>').encode()

def build_pptx():
    with ZipFile(OUT/'1150080127_Bao_cao_GK.pptx') as z:
        data={n:z.read(n) for n in z.namelist() if not n.startswith(('ppt/slides/','ppt/notesSlides/'))}
    presentation=E.fromstring(data['ppt/presentation.xml'])
    ids=presentation.find('{'+P+'}sldIdLst');ids.clear()
    rels=E.fromstring(data['ppt/_rels/presentation.xml.rels'])
    for n in list(rels):
        if n.get('Type').endswith('/slide'):rels.remove(n)
    types=E.fromstring(data['[Content_Types].xml'])
    for n in list(types):
        if n.get('PartName','').startswith(('/ppt/slides/','/ppt/notesSlides/')):types.remove(n)
    for i,s in enumerate(SLIDES,1):
        rid='rIdTeam'+str(i)
        E.SubElement(ids,'{'+P+'}sldId',{'id':str(2000+i),'{'+R+'}id':rid})
        E.SubElement(rels,'{'+REL+'}Relationship',Id=rid,Type=R+'/slide',Target=f'slides/slide{i}.xml')
        data[f'ppt/slides/slide{i}.xml']=slide_xml(s)
        sr=E.Element('{'+REL+'}Relationships')
        E.SubElement(sr,'{'+REL+'}Relationship',Id='rId1',Type=R+'/slideLayout',Target='../slideLayouts/slideLayout7.xml')
        E.SubElement(sr,'{'+REL+'}Relationship',Id='rId2',Type=R+'/notesSlide',Target=f'../notesSlides/notesSlide{i}.xml')
        data[f'ppt/slides/_rels/slide{i}.xml.rels']=xml(sr)
        data[f'ppt/notesSlides/notesSlide{i}.xml']=notes_xml(s.notes)
        nr=E.Element('{'+REL+'}Relationships')
        E.SubElement(nr,'{'+REL+'}Relationship',Id='rId1',Type=R+'/notesMaster',Target='../notesMasters/notesMaster1.xml')
        E.SubElement(nr,'{'+REL+'}Relationship',Id='rId2',Type=R+'/slide',Target=f'../slides/slide{i}.xml')
        data[f'ppt/notesSlides/_rels/notesSlide{i}.xml.rels']=xml(nr)
        for kind in ['slide','notesSlide']:
            part=f'/ppt/{"slides" if kind=="slide" else "notesSlides"}/{kind}{i}.xml'
            E.SubElement(types,'{'+CT+'}Override',PartName=part,ContentType='application/vnd.openxmlformats-officedocument.presentationml.'+kind+'+xml')
    data['ppt/presentation.xml']=xml(presentation)
    data['ppt/_rels/presentation.xml.rels']=xml(rels)
    data['[Content_Types].xml']=xml(types)
    app=E.fromstring(data['docProps/app.xml'])
    for n in app:
        if n.tag.endswith(('}Slides','}Notes')):n.text=str(len(SLIDES))
        if n.tag.endswith('}HiddenSlides'):n.text='2'
    data['docProps/app.xml']=xml(app)
    core=E.fromstring(data['docProps/core.xml'])
    for n in core:
        if n.tag.endswith('}title'):n.text='Mã hoá lai — Nhóm 4 người — Báo cáo 5 phút'
        if n.tag.endswith('}description'):n.text='3 phần lý thuyết x 60 giây; demo 120 giây. 7 slide chính, 2 slide dự phòng ẩn.'
    data['docProps/core.xml']=xml(core)
    path=OUT/'Ma_hoa_lai_Nhom_4_nguoi_5_phut.pptx'
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        for n,b in data.items():z.writestr(n,b)
    return path

DEMO=[
('03:00–03:25 · 25 giây','Chọn tệp nhỏ → mã hoá và ký → tải gói xuống.','Mỗi gói có AES mới; AES được RSA bọc và gói được Alice ký.'),
('03:25–04:00 · 35 giây','Giải mã gói vừa tạo → chỉ senderVerified=true → tải và mở nội dung phục hồi.','Chữ ký được kiểm tra trước; tệp phục hồi khớp nội dung gốc.'),
('04:00–04:30 · 30 giây','Nạp bản sao gói đã sửa bit chuẩn bị trước → giải mã bị từ chối.','Gói đã bị sửa nên không vượt qua xác thực; ứng dụng không trả bản rõ.'),
('04:30–04:50 · 20 giây','Tab bằng chứng → chạy đối chiếu → chỉ 140/140.','Đây là 140 ca đối chiếu AES và OAEP, không phải chứng nhận NIST.'),
('04:50–05:00 · 10 giây','Kết luận và dừng.','Nhóm đã kết hợp bảo mật nội dung, bảo vệ khoá và xác thực người gửi trong một công cụ cục bộ. Em cảm ơn thầy.')]

def build_guide():
    sections=[('1. Phân công và giới hạn thời gian',[
        [['Người','Nội dung','Slide','Mốc toàn bài'],['Thành viên 1','AES-GCM','1–2','00:00–01:00'],['Thành viên 2','RSA-OAEP và mã hoá lai','3–4','01:00–02:00'],['Thành viên 3','PSS, fingerprint, keystore, phạm vi','5–6','02:00–03:00'],['Trần Phạm Thiên Ân','Demo và kết luận','7 + trình duyệt','03:00–05:00']],
        'Không có slide chào hỏi hoặc kết thúc riêng. Câu mở bài nằm trong phần AES; câu kết nằm trong 10 giây cuối demo. Thay tên thành viên 1–3 khi nhóm phân công.',
        'Mỗi slide lý thuyết có ngân sách 30 giây. Mục tiêu nói 25–27 giây, còn lại chỉ sơ đồ/chuyển slide. Một phút mỗi người bao gồm chuyển lượt. Đây là lịch tập, không phải bảo đảm tự động: nhóm phải bấm giờ và chỉnh theo tốc độ nói thực tế.',
        'Slide 8–9 là dự phòng, được đặt ẩn khi trình chiếu. Chỉ mở khi được hỏi, không tính vào nội dung 5 phút.'
    ])]
    for role,parts in SCRIPTS:
        items=[]
        for timing,speech in parts:items.extend([timing,speech])
        items.append('Điểm dừng: hoàn thành lượt đúng mốc 01:00 / 02:00 / 03:00 tương ứng. Nếu nói xong sớm, chỉ sơ đồ và giữ nhịp; không tự bổ sung công thức hoặc chi tiết OAEP/PSS.')
        sections.append((role,items))
    sections.append(('5. Demo 2 phút — chuẩn bị trước giờ báo cáo',[
        'Mở sẵn ứng dụng bằng python3 scripts/demo.py run; nhập mật khẩu trước khi bắt đầu. Mở http://127.0.0.1:8080. Không chạy init, cài chứng thư hoặc tạo khoá trên sân khấu.',
        'Tạo tệp demo.txt ngắn với nội dung dễ nhận biết, ví dụ: “Nhóm 4 — thử nghiệm mã hoá lai — tệp gốc”. Dùng dữ liệu công khai.',
        'Mã hoá một gói trước giờ báo cáo bằng chính bộ khoá trình diễn. Tạo bản sao bị sửa bằng python3 scripts/tamper_file.py <goi.signed.secpkg> <goi_tampered.secpkg>. Chạy thử và bảo đảm bị từ chối. Để các tệp trong một thư mục dễ chọn, không đổi khoá sau đó.',
        'Mở sẵn thư mục tải xuống và trình xem văn bản để kiểm tra tệp phục hồi nhanh. Đóng các cửa sổ không liên quan. Nếu tệp phục hồi trùng tên, xác định đúng bản mới tải.',
        'Một bạn giữ đồng hồ và ra hiệu ở mốc 01:00, 02:00, 03:00, 04:30. Luyện thao tác chuyển PowerPoint sang trình duyệt trước.',
        'Không đưa private key/mật khẩu lên màn chiếu. Không demo sửa hex, khởi động lại hoặc thử khoá khác trong 2 phút; để làm phần trả lời nếu được hỏi.'
    ]))
    items=[]
    for timing,action,speech in DEMO:items.extend([timing,action,'Lời nói: '+speech])
    sections.append(('6. Kịch bản demo theo đồng hồ',items))
    sections.append(('7. Cách tập và rút ngắn',[
        'Vòng 1: mỗi bạn tự tập đúng hai slide, đo riêng từng nửa phút. Vòng 2: cả nhóm chạy một mạch 5 phút, tính cả đổi người và đổi cửa sổ. Vòng 3: lặp lại với tệp demo đúng bộ khoá sẽ dùng.',
        'Nếu lượt 1 quá giờ: bỏ câu ví dụ về loại tệp hoặc rút lời giải thích AAD. Giữ ý AES mã hoá nội dung, có tag, không trả bản rõ khi xác thực thất bại.',
        'Nếu lượt 2 quá giờ: bỏ câu giải thích MGF1 khỏi lời nói, thông số vẫn có trên slide. Giữ ý RSA chỉ bọc AES và Bob dùng private key để mở.',
        'Nếu lượt 3 quá giờ: bỏ câu nói số lượng test vì demo sẽ trình bày bằng chứng. Giữ PSS, fingerprint, keystore và câu bàn giao demo.',
        'Nếu demo chậm: chỉ kết quả tệp phục hồi thay vì mở nhiều cửa sổ; dành đủ thời gian cho gói bị sửa. Nếu không còn thời gian chạy vector, nêu đúng rằng có kết quả đã kiểm thử, không giả như vừa chạy trực tiếp.',
        'Không thêm một slide giới thiệu nhóm dài hoặc lời cảm ơn riêng. Khi hết 5 phút dừng, để thầy hỏi tiếp.'
    ]))
    sections.append(('8. Giải thích thêm khi được hỏi — không đọc trong 5 phút',[
        'PSS: EM=maskedDB223 | H32 | BC1 =256 byte; private key Alice tạo chữ ký256 byte. Public key kiểm tra, không giữ bí mật EM/salt. Chi tiết ở docs/04_On_tap_RSA_PSS.md và slide dự phòng8.',
        'Fingerprint là hash public key DER; không phải hash tệp và không phải mật khẩu. Phải xác nhận qua kênh tin cậy. Nhận khoá và fingerprint từ cùng nguồn có thể bị thay thế chưa chứng minh danh tính.',
        'Keystore có mật khẩu bảo vệ private key khi lưu. Thư mục ẩn không phải cơ chế bảo mật. AES mới mỗi gói; RSA được giữ qua restart. Đổi mật khẩu không phải đổi cặp RSA.',
        'Chữ ký hợp lệ xác thực theo khoá đã tin cậy, không chứng minh tệp sạch mã độc. Private key bị lộ có thể bị lợi dụng để ký. Chưa chống replay.',
        'HTTP chỉ chạy loopback và có kiểm tra Host/Origin; không mở cổng ra mạng. Hướng desktop xử lý tại máy; nếu có server qua LAN/Internet cần HTTPS và kiểm soát truy cập.',
        '157 ca JUnit là toàn bộ các nhóm kiểm thử hiện có. 140 ca trên web gồm120 AES và20 OAEP. PSS còn có OpenSSL đối chiếu độc lập. Không gọi bất kỳ tổng nào là chứng nhận NIST.',
        'Benchmark cũ đo SECPv1, không có PSS; không gán số đó cho hiệu năng phiên bản có chữ ký.',
        'Nguồn: RFC5116 (AEAD), RFC8017 (OAEP/PSS), tài liệu JDK21 keytool, mã nguồn và log kiểm thử của dự án.'
    ]))
    DOCS.mkdir(exist_ok=True)
    word=DOCS/'05_Kich_ban_nhom_4_nguoi_5_phut.docx'
    write_docx(word,'Kịch bản thuyết trình 5 phút — Nhóm 4 người',sections)
    md=['# Kịch bản thuyết trình 5 phút — Nhóm 4 người','']
    for heading,items in sections:
        md.extend(['## '+heading,''])
        for item in items:
            if isinstance(item,list):
                md.append('| '+' | '.join(item[0])+' |');md.append('| '+' | '.join(['---']*len(item[0]))+' |')
                md.extend('| '+' | '.join(row)+' |' for row in item[1:]);md.append('')
            else:md.extend([item,''])
    (DOCS/'05_Kich_ban_nhom_4_nguoi_5_phut.md').write_text('\n'.join(md))
    return word

def build_preview():
    pages=[]
    for i,s in enumerate(SLIDES,1):
        elements=[]
        for item in s.items:
            common=f'left:{item["x"]}px;top:{item["y"]}px;width:{item["w"]}px;height:{item["h"]}px;'
            if item['kind']=='rect':style=common+f'background:#{item["fill"]};border-radius:{14 if item["radius"] else 0}px;'
            else:style=common+f'font-size:{item["size"]}px;color:#{item["color"]};font-weight:{700 if item["bold"] else 400};text-align:'+{'l':'left','r':'right','ctr':'center'}[item['align']]+';line-height:1.12;'
            elements.append('<div style="position:absolute;'+style+'">'+(escape(item['text']).replace('\n','<br>') if item['kind']=='text' else '')+'</div>')
        pages.append(f'<section><p class="caption">Slide {i}'+(' · DỰ PHÒNG, ẨN' if s.hidden else '')+'</p><div class="frame"><div class="slide">'+''.join(elements)+'</div></div><details><summary>Lời nói / ghi chú</summary><pre>'+escape(s.notes)+'</pre></details></section>')
    html='''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nhóm 4 người · 5 phút</title><style>body{font-family:Arial,sans-serif;background:#dce4ec;margin:24px}section{max-width:1280px;margin:30px auto}.frame{width:1280px;height:720px;box-shadow:0 5px 22px #0002;overflow:hidden}.slide{position:relative;width:1280px;height:720px}pre{white-space:pre-wrap;line-height:1.6;background:white;padding:20px}.caption{font-weight:bold;color:#233e51}details{margin-top:12px}@media(max-width:1330px){.frame{zoom:.75}}@media(max-width:1000px){.frame{zoom:.5}}@media print{body{margin:0}details,.caption{display:none}.frame{box-shadow:none;zoom:1}section{break-after:page;margin:0}@page{size:13.333in 7.5in;margin:0}}</style><body>'''+''.join(pages)+'</body></html>'
    path=OUT/'Xem_truoc_Nhom_4_nguoi_5_phut.html';path.write_text(html);return path

def main():
    current=OUT/'Ma_hoa_lai_Nhom_4_nguoi_5_phut.pptx'
    if current.exists():
        with ZipFile(current) as archive:
            if any('BẢO MẬT MÁY TÍNH VÀ HỆ THỐNG' in archive.read(name).decode('utf-8') for name in archive.namelist() if name.startswith('ppt/slides/slide') and name.endswith('.xml')):
                print('Giữ nguyên bản PowerPoint đã được chỉnh trực tiếp; không tái tạo bố cục cũ hoặc khôi phục slide đã xoá.')
                return
    assert len(SLIDES)==9 and sum(not s.hidden for s in SLIDES)==7
    for i,s in enumerate(SLIDES,1):
        for item in s.items:
            assert 0<=item['x'] and 0<=item['y'] and item['x']+item['w']<=1280 and item['y']+item['h']<=720,(i,item)
    for path in [build_pptx(),build_guide(),build_preview()]:print(path)
    print('7 main slides + 2 hidden backup slides; notes included. Timing requires rehearsal.')
    print('Speech lengths (whitespace units): '+str([sum(len(t.split()) for _,t in parts) for _,parts in SCRIPTS]))
if __name__=='__main__':main()
