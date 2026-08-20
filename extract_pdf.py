from PyPDF2 import PdfReader

reader = PdfReader(r'C:\Users\34619\Desktop\前后\XH-202621_多源异构数据驱动岗位和能力图谱构建与动态演化分析研究(1).pdf')
print(f'Total pages: {len(reader.pages)}')
for i, page in enumerate(reader.pages):
    text = page.extract_text()
    if text:
        print(f'\n===== Page {i+1} =====')
        print(text)
    else:
        print(f'\n===== Page {i+1} =====')
        print('[No extractable text on this page]')
