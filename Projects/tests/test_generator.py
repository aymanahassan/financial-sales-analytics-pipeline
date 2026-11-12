import csv,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from generate_events import generate

def test_generator_reproducible(tmp_path):
    p=tmp_path/'source.csv'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['source_row_id','segment','country','product','discount_band','units_sold','manufacturing_price','sale_price','gross_sales','discounts','sales','cogs','profit','sale_date','currency_code'])
        w.writeheader();w.writerow(dict(source_row_id='row1',segment='Government',country='Canada',product='A',discount_band='None',units_sold='2',manufacturing_price='3',sale_price='10',gross_sales='20',discounts='0',sales='20',cogs='6',profit='14',sale_date='2014-01-01',currency_code='GBP'))
    a=list(generate(p,110,42));b=list(generate(p,110,42))
    assert a==b
    assert all(r['currency_code']=='GBP' for r in a)
    assert len(a)>110
    assert len({x['record_id'] for x in a})==110
    assert any(x['country']=='' for x in a)
    assert any(x['version']==2 for x in a)
