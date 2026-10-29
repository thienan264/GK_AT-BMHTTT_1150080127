#!/usr/bin/env python3
"""Redesign the currently saved team deck, without restoring deleted slides."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as E
from xml.sax.saxutils import escape
import hashlib,json,posixpath,shutil,re

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'presentation/Ma_hoa_lai_Nhom_4_nguoi_5_phut.pptx'
BACKUP=Path('/tmp/Ma_hoa_lai_Nhom_4_nguoi_truoc_doi_giao_dien.pptx')
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL='http://schemas.openxmlformats.org/package/2006/relationships'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
for prefix,uri in [('p',P),('a',A),('r',R)]:E.register_namespace(prefix,uri)
PAPER='F4EFE5';INK='24332F';DARK='182D28';RUST='A9472E';MUTED='667269';LINE='D5CDBE';PALE='E4E8DC';WHITE='FFFDF7';GOLD='D6B67D'
MEMBERS=[('Trần Phạm Thiên Ân','1150080127'),('Nguyễn Thành Việt',''),('Lê Công Đạt',''),('Nguyễn Trường Thịnh','')]
PAGES=[]

def xml(n):return E.tostring(n,encoding='utf-8',xml_declaration=True)
def target(base,relative):return relative.lstrip('/') if relative.startswith('/') else posixpath.normpath(posixpath.join(base,relative))

def read_slides(data):
    presentation=E.fromstring(data['ppt/presentation.xml'])
    rels={n.get('Id'):n.get('Target') for n in E.fromstring(data['ppt/_rels/presentation.xml.rels'])}
    result=[]
    for entry in presentation.find('{'+P+'}sldIdLst'):
        path=target('ppt',rels[entry.get('{'+R+'}id')]);tree=E.fromstring(data[path]);texts=[]
        for sp in tree.iter('{'+P+'}sp'):
            text='\n'.join(n.text or '' for n in sp.iter('{'+A+'}t'))
            if not text.strip():continue
            transform=sp.find('{'+P+'}spPr/{'+A+'}xfrm')
            off=transform.find('{'+A+'}off') if transform is not None else None
            texts.append({'text':text,'x':round(int(off.get('x'))/9525) if off is not None else 0,'y':round(int(off.get('y'))/9525) if off is not None else 0})
        result.append({'path':path,'hidden':tree.get('show')=='0','texts':texts})
    return result

class Page:
    def __init__(self,title='',section='',subtitle='',dark=False,hidden=False):
        self.items=[];self.hidden=hidden;self.title=title;self.dark=dark
        self.rect(0,0,1280,720,DARK if dark else PAPER)
        if title:
            self.rect(48,52,7,84,RUST)
            self.text(section,80,52,1100,34,15,RUST,True)
            self.text(title,78,105,1115,104,25,INK,True)
            self.text(subtitle,80,212,1115,66,18,MUTED)
        PAGES.append(self)
    def rect(self,x,y,w,h,fill):self.items.append(dict(kind='rect',x=x,y=y,w=w,h=h,fill=fill,radius=False,line=None))
    def text(self,text,x,y,w,h,size=18,color=INK,bold=False,align='l'):
        if text:self.items.append(dict(kind='text',text=text,x=x,y=y,w=w,h=h,size=size*4/3,color=color,bold=bold,align=align,mono=False))
    def rule(self,x,y,w,color=LINE):self.rect(x,y,w,1,color)
    def arrow(self,x,y,color=RUST):self.text('→',x,y,60,64,30,color,True,'ctr')
    def label(self,label,body,x,y,w=340,dark=False):
        self.rule(x,y,w,GOLD if dark else RUST)
        self.text(label,x,y+20,w,65,20,GOLD if dark else RUST,True)
        self.text(body,x,y+106,w,135,18,PAPER if dark else INK)
    def note(self,text,y=608):
        if text:
            self.rect(80,y,5,60,RUST);self.text(text,104,y+4,1090,68,18,INK)


def text_at(record,x,y):
    return next((n['text'] for n in record['texts'] if abs(n['x']-x)<=2 and abs(n['y']-y)<=2),'')

def original_title(record):return text_at(record,58,94) or next((t['text'] for t in record['texts'] if t['y']>70),'')

def cover():
    s=Page(dark=False);s.rect(750,0,530,720,DARK)
    s.text('BẢO MẬT MÁY TÍNH VÀ HỆ THỐNG',60,46,650,45,18,RUST,True)
    s.text('MÃ HOÁ LAI\nCHO TRAO ĐỔI TỆP',56,150,660,205,35,INK,True)
    s.rule(62,389,595,RUST)
    s.text('AES-GCM  /  RSA-OAEP\nChữ ký số RSA-PSS',62,416,620,100,22,INK)
    s.text('NHÓM 5  ·  LỚP 11_ĐH_CNPM2',62,575,635,42,18,RUST,True)
    s.text('Giảng viên: ThS. Hà Châu Hoàng',62,626,635,43,18,INK)
    s.text('THÀNH VIÊN NHÓM',795,119,425,45,22,GOLD,True)
    for i,(name,student) in enumerate(MEMBERS):
        y=222+i*108;s.rule(795,y-16,414,'496052')
        s.text(name,795,y,425,43,20,PAPER,True)
        s.text('MSSV: '+(student or '........................'),795,y+45,425,35,16,GOLD)
    return s


def redesign(record):
    title=original_title(record);section=text_at(record,58,38);subtitle=text_at(record,60,197)
    if 'DEMO' in section.upper() and not record['hidden']:
        s=Page(dark=True);s.text('DEMO',90,230,1100,230,88,PAPER,True,'ctr');return s
    s=Page(title,section,subtitle,hidden=record['hidden'])
    if 'Mã hoá nội dung' in title or 'RSA chỉ bảo vệ' in title:
        aes='Mã hoá nội dung' in title
        if aes:
            fields=[(text_at(record,72,318),text_at(record,72,373)),(text_at(record,442,318),text_at(record,442,373)),(text_at(record,852,318),text_at(record,852,373))]
        else:fields=[(text_at(record,72,318),text_at(record,72,373)),(text_at(record,437,318),text_at(record,437,373)),(text_at(record,852,318),text_at(record,852,373))]
        s.rect(438,301,382,238,DARK)
        for i,((label,body),x,w) in enumerate(zip(fields,[80,465,910],[285,325,290])):
            s.text(label,x,335,w,65,20,GOLD if i==1 else RUST,True)
            s.text(body,x,422,w,100,18,PAPER if i==1 else INK)
        s.arrow(363,389);s.arrow(835,389)
        s.note(text_at(record,80,592))
    elif 'GCM kiểm tra' in title:
        s.label(text_at(record,82,303),text_at(record,82,364),80,310,500)
        s.label(text_at(record,657,303),text_at(record,657,364),685,310,500)
        s.rect(626,307,1,240,LINE)
        s.note(text_at(record,80,592))
    elif 'Hai thuật toán' in title:
        labels=[text_at(record,x,323) for x in [68,303,568,733]]
        xs=[80,350,680,850];ws=[250,310,150,350]
        for i,(x,w,label) in enumerate(zip(xs,ws,labels)):
            s.rect(x,319,w,121,DARK if i==1 else PALE)
            s.text(label,x+12,354,w-24,74,19,GOLD if i==1 else INK,True,'ctr')
        s.text(text_at(record,64,405),80,468,1110,50,18,MUTED)
        s.text(text_at(record,64,480),80,533,1110,65,22,INK,True)
        s.note(text_at(record,80,592),621)
    elif 'Đúng người gửi' in title:
        s.rect(80,305,520,242,DARK)
        s.label(text_at(record,82,300),text_at(record,82,361),105,327,467,True)
        s.label(text_at(record,657,300),text_at(record,657,361),690,327,495)
        s.text(text_at(record,76,530),80,575,1110,49,20,RUST,True)
        s.text(text_at(record,80,592),80,640,1110,54,18,INK)
    elif 'Lưu khoá' in title:
        s.rect(80,309,1110,2,RUST)
        s.text(text_at(record,82,300),80,341,515,60,20,RUST,True)
        s.text(text_at(record,82,361),80,422,515,100,18,INK)
        s.rect(638,342,1,181,LINE)
        s.text(text_at(record,657,300),690,341,500,60,20,RUST,True)
        s.text(text_at(record,657,361),690,422,500,100,18,INK)
        s.text(text_at(record,76,519),80,566,1110,48,20,INK,True)
        s.note(text_at(record,80,592),629)
    elif 'RSA-PSS: cấu trúc' in title:
        s.text(text_at(record,70,273),80,303,1100,45,20,RUST,True)
        for x,w,label,body,dark in [(80,610,text_at(record,72,358),text_at(record,72,413),True),(710,285,text_at(record,707,358),text_at(record,707,413),False),(1015,180,text_at(record,1022,358),text_at(record,1022,413),False)]:
            s.rect(x,378,w,145,DARK if dark else PALE)
            s.text(label,x+14,397,w-28,47,20,GOLD if dark else INK,True,'ctr')
            s.text(body,x+14,459,w-28,45,18,PAPER if dark else INK,False,'ctr')
        s.note(text_at(record,80,592))
    elif 'Giới hạn' in title:
        s.label(text_at(record,82,300),text_at(record,82,361),80,318,495)
        s.label(text_at(record,657,300),text_at(record,657,361),690,318,500)
        s.note(text_at(record,80,592))
    else:
        # Preserve unknown retained slide text instead of reinstating an old template.
        body=[n['text'] for n in record['texts'] if n['text'] not in {title,section,subtitle} and n['y']<670]
        s.text('\n'.join(body),80,305,1110,350,18,INK)
    return s


def thanks():
    s=Page(dark=True)
    s.rule(462,198,356,GOLD)
    s.text('CẢM ƠN THẦY\nĐÃ LẮNG NGHE',90,267,1100,225,42,PAPER,True,'ctr')
    s.rule(462,552,356,GOLD)
    return s


def shape(item,index):
    x,y,w,h=[round(item[key]*9525) for key in ['x','y','w','h']]
    tx=f'<a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'
    prefix=f'<p:sp><p:nvSpPr><p:cNvPr id="{index}" name="Element {index}"/><p:cNvSpPr'+(' txBox="1"' if item['kind']=='text' else '')+'/><p:nvPr/></p:nvSpPr>'
    if item['kind']=='rect':return prefix+'<p:spPr>'+tx+f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{item["fill"]}"/></a:solidFill><a:ln><a:noFill/></a:ln></p:spPr></p:sp>'
    ps=[]
    for line in item['text'].split('\n'):
        ps.append(f'<a:p><a:pPr algn="{item["align"]}"><a:lnSpc><a:spcPct val="112000"/></a:lnSpc><a:spcAft><a:spcPts val="500"/></a:spcAft></a:pPr><a:r><a:rPr lang="vi-VN" sz="{round(item["size"]*75)}" b="{int(item["bold"])}"><a:solidFill><a:srgbClr val="{item["color"]}"/></a:solidFill><a:latin typeface="Times New Roman"/><a:ea typeface="Times New Roman"/><a:cs typeface="Times New Roman"/></a:rPr><a:t>{escape(line)}</a:t></a:r></a:p>')
    return prefix+'<p:spPr>'+tx+'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody><a:bodyPr wrap="square" lIns="0" rIns="0" tIns="0" bIns="0"><a:noAutofit/></a:bodyPr><a:lstStyle/>'+''.join(ps)+'</p:txBody></p:sp>'

def slide_xml(page):
    hidden=' show="0"' if page.hidden else ''
    start=f'<p:sld xmlns:p="{P}" xmlns:a="{A}" xmlns:r="{R}"{hidden}><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
    return (start+''.join(shape(item,i+2) for i,item in enumerate(page.items))+'</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>').encode()

def notes_xml(text):
    ps=''.join('<a:p><a:r><a:rPr lang="vi-VN" sz="1800"><a:latin typeface="Times New Roman"/><a:ea typeface="Times New Roman"/><a:cs typeface="Times New Roman"/></a:rPr><a:t>'+escape(line)+'</a:t></a:r></a:p>' for line in text.split('\n'))
    return (f'<p:notes xmlns:p="{P}" xmlns:a="{A}"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/><p:sp><p:nvSpPr><p:cNvPr id="2" name="Notes"/><p:cNvSpPr/><p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>'+ps+'</p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>').encode()

def add_page(data,presentation,rels,types,page,note,number,at_start=False):
    rid='rIdRestyle'+str(number)
    E.SubElement(rels,'{'+REL+'}Relationship',Id=rid,Type=R+'/slide',Target=f'slides/slide{number}.xml')
    entry=E.Element('{'+P+'}sldId',{'id':str(3000+number),'{'+R+'}id':rid})
    ids=presentation.find('{'+P+'}sldIdLst')
    if at_start:ids.insert(0,entry)
    else:ids.append(entry)
    data[f'ppt/slides/slide{number}.xml']=slide_xml(page)
    sr=E.Element('{'+REL+'}Relationships')
    E.SubElement(sr,'{'+REL+'}Relationship',Id='rId1',Type=R+'/slideLayout',Target='../slideLayouts/slideLayout7.xml')
    E.SubElement(sr,'{'+REL+'}Relationship',Id='rId2',Type=R+'/notesSlide',Target=f'../notesSlides/notesSlide{number}.xml')
    data[f'ppt/slides/_rels/slide{number}.xml.rels']=xml(sr)
    data[f'ppt/notesSlides/notesSlide{number}.xml']=notes_xml(note)
    nr=E.Element('{'+REL+'}Relationships')
    E.SubElement(nr,'{'+REL+'}Relationship',Id='rId1',Type=R+'/notesMaster',Target='../notesMasters/notesMaster1.xml')
    E.SubElement(nr,'{'+REL+'}Relationship',Id='rId2',Type=R+'/slide',Target=f'../slides/slide{number}.xml')
    data[f'ppt/notesSlides/_rels/notesSlide{number}.xml.rels']=xml(nr)
    for kind in ['slide','notesSlide']:
        part=f'/ppt/{"slides" if kind=="slide" else "notesSlides"}/{kind}{number}.xml'
        E.SubElement(types,'{'+CT+'}Override',PartName=part,ContentType='application/vnd.openxmlformats-officedocument.presentationml.'+kind+'+xml')

def preview():
    pages=[]
    for i,s in enumerate(PAGES,1):
        elements=[]
        for item in s.items:
            style=f'position:absolute;left:{item["x"]}px;top:{item["y"]}px;width:{item["w"]}px;height:{item["h"]}px;'
            if item['kind']=='rect':style+=f'background:#{item["fill"]};'
            else:style+=f'font-size:{item["size"]}px;color:#{item["color"]};font-weight:{700 if item["bold"] else 400};line-height:1.12;text-align:'+{'l':'left','ctr':'center','r':'right'}[item['align']]+';'
            elements.append('<div style="'+style+'">'+(escape(item['text']).replace('\n','<br>') if item['kind']=='text' else '')+'</div>')
        pages.append('<section><p>'+str(i)+(' · Dự phòng ẩn' if s.hidden else '')+'</p><div class="frame">'+''.join(elements)+'</div></section>')
    path=ROOT/'presentation/Xem_truoc_Nhom_4_nguoi_5_phut.html'
    path.write_text('<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nhóm 5 · Mã hoá lai</title><style>body{background:#cbc7bd;font-family:"Times New Roman",serif;margin:24px}section{max-width:1280px;margin:30px auto}.frame{position:relative;width:1280px;height:720px;box-shadow:0 8px 24px #0002;overflow:hidden}@media(max-width:1330px){.frame{zoom:.75}}@media(max-width:1000px){.frame{zoom:.5}}@media print{body{margin:0}section{margin:0;break-after:page}section>p{display:none}.frame{zoom:1;box-shadow:none}@page{size:13.333in 7.5in;margin:0}}</style><body>'+''.join(pages)+'</body></html>')

def main():
    original=PATH.read_bytes();checksum=hashlib.sha256(original).hexdigest()
    with ZipFile(PATH) as z:data={name:z.read(name) for name in z.namelist()}
    records=read_slides(data)
    if any('BẢO MẬT MÁY TÍNH VÀ HỆ THỐNG' in n['text'] for r in records for n in r['texts']):
        raise SystemExit('Already redesigned. Do not regenerate from the old template; edit the current deck directly.')
    shutil.copy2(PATH,BACKUP)
    presentation=E.fromstring(data['ppt/presentation.xml'])
    rels=E.fromstring(data['ppt/_rels/presentation.xml.rels']);types=E.fromstring(data['[Content_Types].xml'])
    cover_page=cover()
    for record in records:
        page=redesign(record);data[record['path']]=slide_xml(page)
        dirname=posixpath.dirname(record['path'])
        relpath=dirname+'/_rels/'+posixpath.basename(record['path'])+'.rels'
        if relpath in data:
            for relationship in E.fromstring(data[relpath]):
                if relationship.get('Type').endswith('/notesSlide'):
                    note_path=target(dirname,relationship.get('Target'))
                    text='\n'.join(n.text or '' for n in E.fromstring(data[note_path]).iter('{'+A+'}t'))
                    if 'DEMO' in text_at(record,58,38).upper():text=text.replace('04:50–05:00','04:50–04:55')+'\n04:55–05:00: chuyển trang cảm ơn cuối, nói ngắn và dừng đúng 5 phút.'
                    if 'Mã hoá nội dung' in original_title(record):text='Trang giới thiệu: 00:00–00:05. Slide AES đầu: 00:05–00:30.\n'+text
                    data[note_path]=notes_xml(text)
    closing=thanks()
    maximum=max(int(re.search(r'slide(\d+)\.xml$',n).group(1)) for n in data if re.fullmatch(r'ppt/slides/slide\d+\.xml',n))
    add_page(data,presentation,rels,types,cover_page,'00:00–00:05, nằm trong phút của thành viên 1. Nói: “Nhóm 5 trình bày đề tài mã hoá lai cho trao đổi tệp.” Không đọc hết tên nhóm. Ba MSSV còn trống để nhóm tự điền.',maximum+1,True)
    add_page(data,presentation,rels,types,closing,'04:55–05:00, nằm trong 2 phút demo. Nói: “Em cảm ơn thầy đã lắng nghe.” Dừng trình bày, không cộng thêm thời gian.',maximum+2)
    data['ppt/presentation.xml']=xml(presentation);data['ppt/_rels/presentation.xml.rels']=xml(rels);data['[Content_Types].xml']=xml(types)
    for name in list(data):
        if name.endswith('.xml') and name.startswith(('ppt/theme/','ppt/slideMasters/','ppt/slideLayouts/','ppt/notesMasters/')):
            tree=E.fromstring(data[name])
            for n in tree.iter():
                if n.tag in {'{'+A+'}latin','{'+A+'}ea','{'+A+'}cs'}:n.set('typeface','Times New Roman')
            data[name]=xml(tree)
    app=E.fromstring(data['docProps/app.xml'])
    for n in list(app):
        if n.tag.endswith(('}Slides','}Notes')):n.text=str(len(records)+2)
        if n.tag.endswith('}HiddenSlides'):n.text=str(sum(r['hidden'] for r in records))
        if n.tag.endswith(('}HeadingPairs','}TitlesOfParts')):app.remove(n)
    data['docProps/app.xml']=xml(app)
    for page in PAGES:
        for item in page.items:assert item['x']>=0 and item['y']>=0 and item['x']+item['w']<=1280 and item['y']+item['h']<=720,item
    if hashlib.sha256(PATH.read_bytes()).hexdigest()!=checksum:raise RuntimeError('PowerPoint changed while editing. Save and retry against the current file.')
    temp=PATH.with_suffix('.new.pptx')
    with ZipFile(temp,'w',ZIP_DEFLATED) as z:
        for name,content in data.items():z.writestr(name,content)
    temp.replace(PATH)
    preview()
    Path('/tmp/team-slide-data.json').write_text(json.dumps([s.items for s in PAGES]))
    print(f'Updated in place: {PATH}\nRetained {len(records)} saved slides; added cover and final thanks.\nBackup: {BACKUP}')
if __name__=='__main__':
    main()
