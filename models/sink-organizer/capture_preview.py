"""Capture the actual Fusion graphics view using the dedicated read tool."""
from pathlib import Path
import sys,json,base64
from fusion_mcp import FusionSession
revision=sys.argv[3] if len(sys.argv)>3 else 'R01'
assert revision in ('R01','R02')
out=Path(__file__).resolve().parent/(revision+'-delivery')/'previews'
name=sys.argv[1];direction=sys.argv[2]
assert name in ('assembly','drainage-structure','plan')
with FusionSession() as s:
 width,height=(1000,1800) if name=='plan' else (1600,1000)
 result=s.call('fusion_mcp_read',{'queryType':'screenshot','direction':direction,'width':width,'height':height,'transparentBackground':False})
 for c in result.get('content',[]):
  if c.get('type')=='image':data=c.get('data') or c.get('base64Data')
  elif c.get('type')=='text':
   p=json.loads(c['text']);data=p.get('base64Data')
  else:continue
  if data:
   path=out/(name+'.png');path.write_bytes(base64.b64decode(data));print(json.dumps({'file':str(path),'bytes':path.stat().st_size}));break
 else:raise RuntimeError('No screenshot image: '+str(result)[:500])
