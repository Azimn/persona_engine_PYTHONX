"""Versioned diagnostic entry point; does not modify frozen v1 collection."""
import argparse
from pathlib import Path
from persona_engine.evaluation.model_hardening import replay_frozen, run_matrix

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=('replay','matrix'))
    p.add_argument('--model',default='gemma4:latest')
    p.add_argument('--split',choices=('development','confirmation'),default='development')
    p.add_argument('--user-id',default='hardening_v2')
    p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=False)
    if args.mode=='replay': replay_frozen(args.output_dir,args.model)
    else:run_matrix(args.output_dir,args.model,split=args.split,user_id=args.user_id)
