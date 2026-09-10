"""Fixed-resolved-state model experiment, distinct from live longitudinal evidence.

Uses installed local Ollama models only. No model downloads and no silent fallback.
The exported messages are held constant for model comparisons. This does not
measure model-dependent subsequent cognition or human recognition automatically.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen


def get(host,path):
    with urlopen(host+path,timeout=5) as r: return json.load(r)


def collect(requests_path, models, output, host='http://127.0.0.1:11434'):
    catalog={m['name']:m for m in get(host,'/api/tags')['models']}
    if any(m not in catalog or not catalog[m].get('digest') for m in models):
        raise ValueError('every model must be installed with a recorded digest')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    inputs=json.loads(Path(requests_path).read_text())
    meta={'evidence_class':'actual-model evidence','scope':'fixed-resolved-state expression, not live trajectory',
          'models':{m:catalog[m]['digest'] for m in models},'runtime':get(host,'/api/version'),
          'requests_sha256':hashlib.sha256(Path(requests_path).read_bytes()).hexdigest(),'complete':False}
    (output/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    try:
      with (output/'responses.jsonl').open('x') as log:
        for i,item in enumerate(inputs):
          ordered=models[i%len(models):]+models[:i%len(models)]
          for model in ordered:
            current={m['name']:m.get('digest') for m in get(host,'/api/tags')['models']}
            if current.get(model)!=meta['models'][model]: raise ValueError('model digest changed')
            payload={'model':model,'messages':item['messages'],'stream':False,'think':False,'options':item['options']}
            start=time.perf_counter()
            req=Request(host+'/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with urlopen(req,timeout=120) as response: raw=json.load(response)
            text=raw.get('message',{}).get('content','')
            if not text.strip() or raw.get('error') or not raw.get('done'): raise ValueError('incomplete model response')
            record={'sample_id':item['sample_id'],'model':model,'digest':meta['models'][model],
                    'messages_sha256':item['messages_sha256'],'options':item['options'],
                    'output':text,'latency_ms':1000*(time.perf_counter()-start),
                    'prompt_tokens':raw.get('prompt_eval_count'),'output_tokens':raw.get('eval_count'),
                    'done_reason':raw.get('done_reason'),'fallback':False,'raw':raw}
            log.write(json.dumps(record)+'\n');log.flush()
      meta['complete']=True
    except Exception as exc:
      meta['failure']={'type':type(exc).__name__,'message':str(exc)}
      raise
    finally: (output/'manifest.json').write_text(json.dumps(meta,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--requests',required=True);p.add_argument('--models',nargs='+',required=True);p.add_argument('--output',required=True);p.add_argument('--host',default='http://127.0.0.1:11434')
    a=p.parse_args();collect(a.requests,a.models,a.output,a.host)
