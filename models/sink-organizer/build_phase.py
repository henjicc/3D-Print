"""Run one bounded organizer component phase through guarded native Fusion MCP."""
from pathlib import Path
import sys,json
from fusion_mcp import FusionSession

folder=Path(__file__).resolve().parent
phase=sys.argv[1]
assert phase in ('L1','L1-revised','L1-corner','R2-corner','L2','R1','R2','LS','RS','UP','tower','coupons')
checkpoints=folder/'checkpoints'/sys.argv[2] if len(sys.argv)>2 else folder/'checkpoints'
source=(folder/'model_builder.py').read_text()
source+='\ndef run(_context: str):\n    build_phase('+ascii(phase)+','+ascii(str(checkpoints))+')\n'
with FusionSession() as session:
    result=session.call('fusion_mcp_execute',{'featureType':'script','object':{'script':source}})
    for block in result.get('content',[]):
        if block.get('type')!='text':continue
        payload=json.loads(block['text'])
        for line in payload.get('message','').splitlines():
            item=json.loads(line)
            if 'bodies' in item:
                (folder/'cad-check.json').write_text(json.dumps(item,ensure_ascii=False,indent=2))
                item={'phase':phase,'features':item['features'],'body_count':len(item['bodies']),'new_parts':[b for b in item['bodies'] if b['name'].startswith(phase+'_')],'issues':item['issues'],'underconstrained':item['underconstrained']}
            print(json.dumps(item,ensure_ascii=False),flush=True)
