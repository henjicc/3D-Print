from pathlib import Path
import sys,json
folder=Path(__file__).resolve().parent;sys.path.insert(0,str(folder))
from fusion_mcp import FusionSession
phase=sys.argv[1]
s=(folder/'model_builder.py').read_text().replace('Sink Organizer B - R01','Sink Organizer B - R05')
soft="def soften(m,c,grate=False):\n body=c.bRepBodies.item(0);z=ev('('+m['z']+')+PanHeight');edges=adsk.core.ObjectCollection.create()\n for e in body.edges:\n  p=e.startVertex.geometry;q=e.endVertex.geometry\n  if abs(p.z-z)>1e-6 or abs(q.z-z)>1e-6:continue\n  # Exclude curved edges' internal endpoints and all grate locator notches by only exterior long edges.\n  if e.length<ev('20 mm'):continue\n  if grate:\n   bb=body.boundingBox\n   exterior=any(abs(getattr(p,a)-getattr(bb.minPoint,a))<1e-6 and abs(getattr(q,a)-getattr(bb.minPoint,a))<1e-6 or abs(getattr(p,a)-getattr(bb.maxPoint,a))<1e-6 and abs(getattr(q,a)-getattr(bb.maxPoint,a))<1e-6 for a in ('x','y'))\n   if not exterior:continue\n  # Rear plane is the printing bed for pans, so leave that perimeter square.\n  if not grate:\n   def localv(p):\n    if m['orient']=='rear':return p.y-ev(m['y'])\n    if m['orient']=='left':return p.x-ev(m['x'])\n    return ev(m['x'])+ev(m['d'])-p.x\n   if abs(localv(p))<1e-6 and abs(localv(q))<1e-6:continue\n  edges.add(e)\n assert edges.count>0,c.name\n inp=c.features.chamferFeatures.createInput2();inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges,vi('TouchChamfer'),False)\n f=c.features.chamferFeatures.add(inp);f.name='R03 touch edge chamfer'\n assert f.healthState==adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,f.errorOrWarningMessage\n return edges.count\n"
soft=soft.replace("z=ev('('+m['z']+')+PanHeight')","z=ev('('+m['z']+')+PanHeight'+('' if grate else '+RimLift'))")
s='\n'.join(line for line in s.splitlines() if "CUT,'Finger lift notch'" not in line)
s+='\n'+soft
s+='''
def floor(m,v):return '('+m['z']+')+FloorMin+(('+m['d']+')-('+v+'))*tan(DrainSlope)'
def single_specs():
 ms=specs()[:6];ms[0].update(x='BaseX',w='TowerWidth');return ms

def run(context):
 global app,design,root
 app=adsk.core.Application.get()
 if PHASE=='init':
  archive=ARCHIVE
  doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(archive));doc.name='Sink Organizer B - R04 SINGLE LOW'
  old=adsk.fusion.Design.cast(app.activeProduct)
  pars=[(p.name,p.expression,p.unit,p.comment) for p in old.userParameters]
  app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);app.activeDocument.name='Sink Organizer B - R05 FLOW RIM'
  design=adsk.fusion.Design.cast(app.activeProduct);root=design.rootComponent
  for n,e,u,c in pars:
   if n=='FootHeight':e='10 mm'
   if n=='DrainSlope':e='6 deg'
   if n=='DrainExtension':e='0 mm';c='R05 no projection and no inherited thickness offset'
   design.userParameters.add(n,vi(e),u,c)
  design.userParameters.add('RimLift',vi('5 mm'),'mm','Three retaining edges above horizontal grate')
  design.userParameters.add('SeatReach',vi('7 mm'),'mm','Triangular seat projection from side wall')
  design.userParameters.add('SeatLength',vi('24 mm'),'mm','Flow aligned triangular seat base')
  design.userParameters.add('SeatTipRadius',vi('1 mm'),'mm','Rounded triangular flow tip')
 elif PHASE=='locators':
  bind()
  for m in single_specs():
   c=next(c for c in design.allComponents if c.name==m['key']+'_Integrated');g=next(c for c in design.allComponents if c.name==m['key']+'_RemovableGrate')
   for i,u in enumerate(('Wall','('+m['w']+')-Wall-2 mm')):
    mapped_rect(g,m,'('+u+')-DeckClearance','10 mm-DeckClearance','2 mm+2*DeckClearance','5 mm+2*DeckClearance','FootHeight+PanHeight-DeckThick','DeckThick',CUT,'R05 grate locating notch '+str(i))
    mapped_rect(c,m,u,'10 mm','2 mm','5 mm',m['z'],'PanHeight',JOIN,'R05 grate locating key '+str(i))
 else:
  bind();m=next(m for m in single_specs() if m['key']==PHASE)
  c=component(PHASE+'_Integrated')
  f=mapped_rect(c,m,'0 mm','0 mm',m['w'],m['d'],m['z'],'PanHeight+RimLift',NEW,'R05 pan blank')
  round_vertical(c,f.bodies.item(0),'3 mm','Outside corner rounds')
  v0='Wall';v1=m['d'];ztop='FootHeight+PanHeight+RimLift+1 mm'
  slope_extrude(c,m,'Wall','('+m['w']+')-2*Wall',[(v0,floor(m,v0)),(v1,floor(m,v1)),(v1,ztop),(v0,ztop)],CUT,'R05 continuous slope and open edge')
  for i in range(2):
   side='Wall' if i==0 else '('+m['w']+')-Wall'
   inner='Wall+SeatReach' if i==0 else '('+m['w']+')-Wall-SeatReach'
   for j,start in enumerate(('Wall','('+m['d']+')-Wall-SeatLength')):
    mid='('+start+')+SeatLength/2';end='('+start+')+SeatLength'
    sk=sketch(c,'xy',m['z'],'R05 flow seat section '+str(i)+str(j))
    polygon_world(sk,[(*xy(m,side,start),m['z']),(*xy(m,inner,mid),m['z']),(*xy(m,side,end),m['z'])])
    extrude(c,sk,'PanHeight-DeckThick',JOIN,'R05 triangular flow seat '+str(i)+str(j))
    px,py=xy(m,inner,mid);edges=adsk.core.ObjectCollection.create()
    for edge in c.bRepBodies.item(0).edges:
     p=edge.startVertex.geometry;q=edge.endVertex.geometry
     if abs(p.x-ev(px))<1e-6 and abs(q.x-ev(px))<1e-6 and abs(p.y-ev(py))<1e-6 and abs(q.y-ev(py))<1e-6 and abs(p.z-q.z)>1e-5:edges.add(edge)
    if edges.count:
     inp=c.features.filletFeatures.createInput();inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,vi('SeatTipRadius'),False)
     fillet=c.features.filletFeatures.add(inp);fillet.name='R05 soften flow seat tip'
     assert fillet.healthState==adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,fillet.errorOrWarningMessage
  for i,u in enumerate(('3 mm','('+m['w']+')-3 mm-RunnerWidth')):
   mapped_rect(c,m,u,'0 mm','RunnerWidth','('+m['d']+')-9 mm','0 mm','FootHeight',JOIN,'R05 low integral runner '+str(i))
  soften(m,c);c.bRepBodies.item(0).name=c.name
  g=make_grate(m);soften(m,g,True)
 design.computeAll();summarize()
 bad=[design.timeline.item(i).name for i in range(design.timeline.count) if design.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
 save_checkpoint('R05-'+PHASE,CHECKDIR)
 app.activeViewport.fit()
'''
s=s.replace('ARCHIVE',ascii(str(folder/'R04-delivery/Sink_Organizer_B_R04_Single_Low.f3d')))
s=s.replace('PHASE',repr(phase)).replace('CHECKDIR',ascii(str(folder/'checkpoints/R05')))
with FusionSession() as session:
 r=session.call('fusion_mcp_execute',{'featureType':'script','object':{'script':s}})
 for b in r['content']:
  if b['type']=='text':print(json.loads(b['text']).get('message',''))
