"""Export the 700-row Financial Sample Excel worksheet as normalized CSV using stdlib only.
Usage: python src/prepare_source.py --workbook /path/to/Financial_Sample.xlsx
No workbook is committed to Git. The resulting CSV is generated locally.
"""
import argparse,csv,datetime,re,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
NS={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
HEADERS=['segment','country','product','discount_band','units_sold','manufacturing_price',
         'sale_price','gross_sales','discounts','sales','cogs','profit','sale_date','currency_code']
def read_workbook(path):
    with zipfile.ZipFile(path) as z:
        ss=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            doc=ET.fromstring(z.read('xl/sharedStrings.xml'))
            ss=[''.join(t.text or '' for t in si.findall('.//x:t',NS)) for si in doc.findall('x:si',NS)]
        doc=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        rows=[]
        for row in doc.findall('.//x:sheetData/x:row',NS):
            vals={}
            for cell in row.findall('x:c',NS):
                col=re.match(r'[A-Z]+',cell.attrib['r']).group()
                v=cell.find('x:v',NS)
                if v is not None: val=ss[int(v.text)] if cell.get('t')=='s' else v.text
                else: val=''.join(t.text or '' for t in cell.findall('.//x:is/x:t',NS))
                vals[col]=val
            rows.append(vals)
        if not rows:raise ValueError('Workbook has no rows')
        expected=['Segment','Country','Product','Discount Band','Units Sold','Manufacturing Price',
                  'Sale Price','Gross Sales','Discounts','Sales','COGS','Profit','Date']
        actual=[rows[0].get(chr(65+i),'').strip() for i in range(13)]
        if actual!=expected:raise ValueError(f'Unexpected header schema: {actual}')
        for i,row in enumerate(rows[1:],start=2):
            if not any(row.values()):continue
            d={k:row.get(chr(65+j),'').strip() for j,k in enumerate(HEADERS)}
            excel_date=float(d['sale_date'])
            d['sale_date']=(datetime.datetime(1899,12,30)+datetime.timedelta(days=excel_date)).date().isoformat()
            d['source_row_id']=f'financial-sample-row-{i}'
            # Fictional reporting assumption; no FX conversion of original values.
            d['currency_code']='GBP'
            yield d

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workbook',required=True);ap.add_argument('--output',default='data/source_sales.csv');a=ap.parse_args()
    rows=list(read_workbook(a.workbook))
    p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['source_row_id']+HEADERS);w.writeheader();w.writerows(rows)
    print(f'Exported {len(rows)} rows to {p}')
if __name__=='__main__':main()
