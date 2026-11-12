"""Reproducible synthetic sales events derived from a local Financial Sample export.
Never interprets equal dimension combinations as duplicate transactions.
"""
import argparse,csv,datetime,random
from pathlib import Path
FIELDS=['record_id','source_row_id','version','ingested_at','segment','country','product','discount_band',
        'units_sold','manufacturing_price','sale_price','gross_sales','discounts','sales','cogs','profit','sale_date','currency_code']
NUMERIC=['units_sold','manufacturing_price','sale_price','gross_sales','discounts','sales','cogs','profit']

def generate(source,count=100000,seed=42,inject_errors=True):
    if count<1:raise ValueError('count must be positive')
    with open(source,newline='') as f:base=list(csv.DictReader(f))
    if not base:raise ValueError('Source CSV empty')
    if any(r.get('currency_code') != 'GBP' for r in base):
        raise ValueError('FSAP v1 requires GBP-denominated source rows; rerun prepare_source.py')
    rng=random.Random(seed)
    for i in range(count):
        src=base[rng.randrange(len(base))]
        # Source financial metrics remain internally consistent; synthetic date shifts
        # preserve original seasonal distribution while spanning multiple years.
        r={k:src[k] for k in src if k in FIELDS}
        original=datetime.date.fromisoformat(src['sale_date'])
        shift=rng.choice([-365,0,365,730])
        r['sale_date']=(original+datetime.timedelta(days=shift)).isoformat()
        r['record_id']=f'sale-{i:09d}'
        r['source_row_id']=f'synthetic-{i:09d}'
        r['version']=1
        r['ingested_at']='2026-11-12T09:00:00'
        # Periodic defects are explicit, deterministic and mutually exclusive.
        if inject_errors and i%101==0:r['country']=''
        elif inject_errors and i%103==0:r['sale_date']='not-a-date'
        elif inject_errors and i%107==0:r['sales']=str(round(float(r['sales'])+100,2))
        elif inject_errors and i%109==0:r['units_sold']='-2'
        yield r
        # Corrections are additional event versions for the same synthetic sale.
        if inject_errors and i%97==0 and i%101!=0 and i%103!=0 and i%107!=0 and i%109!=0:
            corrected=r.copy();corrected['version']=2;corrected['source_row_id']=f'synthetic-{i:09d}-v2';corrected['ingested_at']='2026-11-13T09:00:00'
            yield corrected

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='data/source_sales.csv');ap.add_argument('--output',default='data/sales_events.csv');ap.add_argument('--count',type=int,default=100000);ap.add_argument('--seed',type=int,default=42);ap.add_argument('--no-errors',action='store_true');a=ap.parse_args()
    p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True)
    n=0
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
        for row in generate(a.source,a.count,a.seed,not a.no_errors):w.writerow(row);n+=1
    print(f'Generated {n} events (from {a.count} synthetic sales) to {p}')
if __name__=='__main__':main()
