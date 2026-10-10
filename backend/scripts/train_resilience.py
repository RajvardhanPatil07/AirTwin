"""Save spatial forecast models, monitor/time splits and sensor-loss predictions."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.data_loader import load_all
from app.services.resilience import train_resilience

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--withheld-station',default=None)
    parser.add_argument('--stride-hours',type=int,default=6)
    args=parser.parse_args()
    if args.stride_hours<1:
        parser.error('stride-hours must be positive')
    frame,warnings,fingerprint,_=load_all()
    report=train_resilience(frame,fingerprint,args.withheld_station,args.stride_hours)
    print('Saved',report['model_id'],'withheld monitor',report['withheld_station_id'])
    for r in report['results']:
        print(r['scope'],r['horizon'],r['loss_percent'],'MAE',round(r['mae'],2),'IDW',round(r['idw_mae'],2),'coverage',round(r['coverage_percent'],1))
