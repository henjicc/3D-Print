from pathlib import Path
import sys,json
folder=Path(__file__).resolve().parent;sys.path.insert(0,str(folder))
from fusion_mcp import FusionSession
phase=sys.argv[1]
s=(folder/'model_builder.py').read_text().replace('Sink Organizer B - R01','Sink Organizer B - R04')
soft="def soften(m,c,grate=False):\n body=c.bRepBodies.item(0);z=ev('('+m['z']+')+PanHeight');edges=adsk.core.ObjectCollection.create()\n for e in body.edges:\n  p=e.startVertex.geometry;q=e.endVertex.geometry\n  if abs(p.z-z)>1e-6 or abs(q.z-z)>1e-6:continue\n  # Exclude curved edges' internal endpoints and all grate locator notches by only exterior long edges.\n  if e.length<ev('20 mm'):continue\n  if grate:\n   bb=body.boundingBox\n   exterior=any(abs(getattr(p,a)-getattr(bb.minPoint,a))<1e-6 and abs(getattr(q,a)-getattr(bb.minPoint,a))<1e-6 or abs(getattr(p,a)-getattr(bb.maxPoint,a))<1e-6 and abs(getattr(q,a)-getattr(bb.maxPoint,a))<1e-6 for a in ('x','y'))\n   if not exterior:continue\n  # Rear plane is the printing bed for pans, so leave that perimeter square.\n  if not grate:\n   def localv(p):\n    if m['orient']=='rear':return p.y-ev(m['y'])\n    if m['orient']=='left':return p.x-ev(m['x'])\n    return ev(m['x'])+ev(m['d'])-p.x\n   if abs(localv(p))<1e-6 and abs(localv(q))<1e-6:continue\n  edges.add(e)\n assert edges.count>0,c.name\n inp=c.features.chamferFeatures.createInput2();inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges,vi('TouchChamfer'),False)\n f=c.features.chamferFeatures.add(inp);f.name='R03 touch edge chamfer'\n assert f.healthState==adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,f.errorOrWarningMessage\n return edges.count\n"
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
  doc=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(archive));doc.name='Sink Organizer B - R03 INTEGRATED'
  old=adsk.fusion.Design.cast(app.activeProduct)
  pars=[(p.name,p.expression,p.unit,p.comment) for p in old.userParameters]
  app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);app.activeDocument.name='Sink Organizer B - R04 SINGLE LOW'
  design=adsk.fusion.Design.cast(app.activeProduct);root=design.rootComponent
  for n,e,u,c in pars:
   if n=='FootHeight':e='10 mm'
   if n=='DrainSlope':e='6 deg'
   if n=='DrainExtension':e='0 mm';c='R04 no projection and no inherited thickness offset'
   design.userParameters.add(n,vi(e),u,c)
 elif PHASE=='locators':
  bind()
  for m in single_specs():
   c=next(c for c in design.allComponents if c.name==m['key']+'_Integrated');g=next(c for c in design.allComponents if c.name==m['key']+'_RemovableGrate')
   for i,u in enumerate(('Wall','('+m['w']+')-Wall-2 mm')):
    mapped_rect(g,m,'('+u+')-DeckClearance','10 mm-DeckClearance','2 mm+2*DeckClearance','5 mm+2*DeckClearance','FootHeight+PanHeight-DeckThick','DeckThick',CUT,'R04 grate locating notch '+str(i))
    mapped_rect(c,m,u,'10 mm','2 mm','5 mm',m['z'],'PanHeight',JOIN,'R04 grate locating key '+str(i))
 else:
  bind();m=next(m for m in single_specs() if m['key']==PHASE)
  c=component(PHASE+'_Integrated')
  f=mapped_rect(c,m,'0 mm','0 mm',m['w'],m['d'],m['z'],'PanHeight',NEW,'R04 pan blank')
  round_vertical(c,f.bodies.item(0),'3 mm','Outside corner rounds')
  v0='Wall';v1=m['d'];ztop='FootHeight+PanHeight+1 mm'
  slope_extrude(c,m,'Wall','('+m['w']+')-2*Wall',[(v0,floor(m,v0)),(v1,floor(m,v1)),(v1,ztop),(v0,ztop)],CUT,'R04 continuous slope and open edge')
  for i,u in enumerate(('Wall','('+m['w']+')-Wall-12 mm')):
   for j,v in enumerate(('Wall','('+m['d']+')-Wall-12 mm')):
    mapped_rect(c,m,u,v,'12 mm','12 mm',m['z'],'PanHeight-DeckThick',JOIN,'Grate seat '+str(i)+str(j))
  for i,u in enumerate(('3 mm','('+m['w']+')-3 mm-RunnerWidth')):
   mapped_rect(c,m,u,'0 mm','RunnerWidth','('+m['d']+')-9 mm','0 mm','FootHeight',JOIN,'R04 low integral runner '+str(i))
  soften(m,c);c.bRepBodies.item(0).name=c.name
  g=make_grate(m);soften(m,g,True)
 design.computeAll();summarize()
 bad=[design.timeline.item(i).name for i in range(design.timeline.count) if design.timeline.item(i).healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState];assert not bad,bad
 save_checkpoint('R04-'+PHASE,CHECKDIR)
 app.activeViewport.fit()
'''
s=s.replace('ARCHIVE',ascii(str(folder/'R03-delivery/Sink_Organizer_B_R03_Integrated.f3d')))
s=s.replace('PHASE',repr(phase)).replace('CHECKDIR',ascii(str(folder/'checkpoints/R04')))
with FusionSession() as session:
 r=session.call('fusion_mcp_execute',{'featureType':'script','object':{'script':s}})
 for b in r['content']:
  if b['type']=='text':print(json.loads(b['text']).get('message',''))
