"""Small DOCX writer using only Python standard library (OOXML, no network dependency)."""
from xml.sax.saxutils import escape
from zipfile import ZipFile,ZIP_DEFLATED
from pathlib import Path

def paragraph(text,style=None):
    props=f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ''
    runs=''.join('<w:r><w:t xml:space="preserve">'+escape(line)+'</w:t></w:r>'+('<w:r><w:br/></w:r>' if i<len(text.split('\n'))-1 else '') for i,line in enumerate(text.split('\n')))
    return '<w:p>'+props+runs+'</w:p>'
def table(rows):
    return '<w:tbl><w:tblPr><w:tblBorders>'+''.join(f'<w:{x} w:val="single" w:sz="4" w:color="CBD5E1"/>' for x in ['top','left','bottom','right','insideH','insideV'])+'</w:tblBorders></w:tblPr>'+''.join('<w:tr>'+''.join('<w:tc><w:tcPr><w:tcW w:w="2400" w:type="dxa"/></w:tcPr>'+paragraph(str(c))+'</w:tc>' for c in row)+'</w:tr>' for row in rows)+'</w:tbl>'
def write_docx(path,title,sections):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    body=paragraph(title,'Title')
    for heading,items in sections:
        if heading:body+=paragraph(heading,'Heading1')
        for item in items:body+=table(item) if isinstance(item,list) else paragraph(item)
    document='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'+body+'<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1100" w:right="1100" w:bottom="1100" w:left="1100"/></w:sectPr></w:body></w:document>'
    styles='''<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="23"/><w:lang w:val="vi-VN"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="140" w:line="285" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults><w:style w:type="paragraph" w:styleId="Normal" w:default="1"><w:name w:val="Normal"/></w:style><w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:b/><w:sz w:val="38"/><w:color w:val="125C56"/></w:rPr></w:style><w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:pPr><w:keepNext/><w:spacing w:before="260" w:after="140"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="29"/><w:color w:val="193146"/></w:rPr></w:style></w:styles>'''
    with ZipFile(path,'w',ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>''')
        z.writestr('_rels/.rels','''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>''')
        z.writestr('word/document.xml',document);z.writestr('word/styles.xml',styles)
        z.writestr('word/_rels/document.xml.rels','''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>''')
