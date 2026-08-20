import fs from 'fs';
import pdfParse from 'pdf-parse';

const buf = fs.readFileSync('C:/Users/34619/Desktop/前后/XH-202621_多源异构数据驱动岗位和能力图谱构建与动态演化分析研究(1).pdf');
try {
  const data = await pdfParse(buf);
  console.log('=== PAGES:', data.numpages, '===');
  console.log(data.text);
} catch (e) {
  console.error('Error:', e.message);
}
