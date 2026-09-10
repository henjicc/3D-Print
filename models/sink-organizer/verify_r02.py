"""Reopen and audit the delivered R02 native geometry against its export manifest."""
from pathlib import Path
import sys,json
from fusion_mcp import FusionSession
folder=Path(__file__).resolve().parent;out=folder/'R02-delivery'
m=json.loads((out/'model-manifest.json').read_text())
source=(folder/'model_builder.py').read_text().replace("'Sink Organizer B - R01'","'Sink Organizer B - R02'")
source+='''
def run(_context:str):
 a=adsk.core.Application.get()
 doc=a.importManager.importToNewDocument(a.importManager.createFusionArchiveImportOptions(ARCHIVE))
 assert doc;doc.name='Sink Organizer B - R02 OPEN EDGE'
 bind()
 bodies={c.name:b for c in design.allComponents for b in c.bRepBodies}
 assert len(bodies)==43 and design.userParameters.count==38
 assert all(b.isValid and b.isSolid and b.volume>0 and b.faces.count>0 for b in bodies.values())
 for name,volume in EXPECTED.items():assert abs(bodies[name].volume*1000-volume)<0.001,name
 assert all(s.isFullyConstrained for c in design.allComponents for s in c.sketches)
 assert all(design.timeline.item(i).healthState==adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState for i in range(design.timeline.count))
 for n,b in bodies.items():
  if '_Foot_' in n:assert abs(b.volume*1000-5216)<0.001,n
  if n.startswith('Tower_'):assert abs(b.volume*1000-32523)<0.001,n
 rows=[]
 for m in specs():
  b=bodies[m['key']+'_DrainPan']
  count=0
  for factor in (0.01,0.25,0.5,0.75,0.99):
   u='Wall+('+m['w']+'-2*Wall)*'+str(factor)
   for v in ('('+m['d']+')-0.5 mm','('+m['d']+')-0.1 mm'):
    x,y=xy(m,u,v)
    assert b.pointContainment(pt(x,y,plus(floor(m,v),'0.05 mm')))==adsk.fusion.PointContainment.PointOutsidePointContainment,m['key']+' blocked lip'
    assert b.pointContainment(pt(x,y,minus(floor(m,v),'0.05 mm')))==adsk.fusion.PointContainment.PointInsidePointContainment,m['key']+' floor missing'
    count+=1
  gaps=[]
  if m['feet']:
   for name in (m['key']+'_Foot_01',m['key']+'_Foot_11'):
    bb=bodies[name].boundingBox
    if m['orient']=='rear':gap=(ev(plus(m['y'],m['d']))-bb.maxPoint.y)*10
    elif m['orient']=='left':gap=(ev(plus(m['x'],m['d']))-bb.maxPoint.x)*10
    else:gap=(bb.minPoint.x-ev(m['x']))*10
    assert abs(gap-9)<0.001,(name,gap)
    gaps.append(round(gap,3))
  rows.append({'module':m['key'],'open_lip_sample_pairs':count,'front_foot_edge_setback_mm':gaps})
 items=adsk.core.ObjectCollection.create()
 for o in root.occurrences:
  if not o.component.name.startswith('FIT_'):items.add(o)
 inp=design.createInterferenceInput(items);inp.areCoincidentFacesIncluded=False
 assert design.analyzeInterference(inp).count==0
 print(json.dumps({'native_archive_reopened':True,'revision':'R02','parameters':38,'positive_bodies':43,'healthy_features':design.timeline.count,'fully_constrained_sketches':True,'all_native_volumes_match_exports':True,'complete_foot_pegs_and_frame_keys':True,'interferences':0,'open_edge_check':'70 above/below-floor point pairs; geometry check only, not a fluid simulation','modules':rows}))
'''
source=source.replace('ARCHIVE',ascii(str(out/'Sink_Organizer_B_R02_Prototype.f3d'))).replace('EXPECTED',repr({p['component']:p['volume_mm3'] for p in m['parts']}))
with FusionSession() as s:
 r=s.call('fusion_mcp_execute',{'featureType':'script','object':{'script':source}})
 for b in r['content']:
  if b['type']=='text':
   result=json.loads(json.loads(b['text'])['message'])
   (out/'native-reopen-check.json').write_text(json.dumps(result,indent=2))
   print(json.dumps(result))
