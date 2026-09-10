"""Apply the user's full-width open-edge revision to a native R01 copy."""
from pathlib import Path
import sys,json
from fusion_mcp import FusionSession
folder=Path(__file__).resolve().parent
phase=sys.argv[1]
source=(folder/'model_builder.py').read_text().replace("'Sink Organizer B - R01'","'Sink Organizer B - R02'")
source+='''
def revise_module(key):
    bind()
    m=next(m for m in specs() if m['key']==key)
    c=next(c for c in design.allComponents if c.name==key+'_DrainPan')
    grate=next(c for c in design.allComponents if c.name==key+'_RemovableGrate')
    assert not any(f.name.startswith('R02 ') for f in c.features.extrudeFeatures),'Already revised'
    # Keep the inherited continuous 4-degree floor, trim exactly at the rack edge.
    mapped_rect(c,m,'-1 mm',m['d'],'('+m['w']+')+2 mm','DrainExtension+2 mm','('+m['z']+')-0.2 mm','PanHeight+0.4 mm',CUT,'R02 remove projecting spout')
    v0='('+m['d']+')-Wall-0.1 mm';v1='('+m['d']+')+1 mm';ztop='('+m['z']+')+PanHeight+1 mm'
    slope_extrude(c,m,'Wall','('+m['w']+')-2*Wall',[(v0,floor(m,v0)),(v1,floor(m,v1)),(v1,ztop),(v0,ztop)],CUT,'R02 full width open front')
    # Two side keys locate the removable grate without placing a dam at its low edge.
    z='('+m['z']+')+PanHeight-DeckThick'
    key_v='13 mm' if key=='UP' else '10 mm'
    for i,u in enumerate(('Wall','('+m['w']+')-Wall-2 mm')):
        mapped_rect(grate,m,'('+u+')-DeckClearance','('+key_v+')-DeckClearance','2 mm+2*DeckClearance','5 mm+2*DeckClearance',z,'DeckThick',CUT,'R02 side locating notch '+str(i))
        mapped_rect(c,m,u,key_v,'2 mm','5 mm',m['z'],'PanHeight',JOIN,'R02 side locating key '+str(i))
    if m['feet']:
        import re
        pattern=r'\(\s*'+m['d']+r'\s*\)\s*-\s*11\s*mm'
        targets=[]
        for comp in design.allComponents:
            if comp.name in (key+'_Foot_01',key+'_Foot_11'):targets.extend(list(comp.sketches))
        targets.extend(s for s in c.sketches if s.name in ('Foot socket 01 sketch','Foot socket 11 sketch'))
        edits=0
        for s in targets:
            for v in s.sketchDimensions:
                old=v.parameter.expression
                new,n=re.subn(pattern,'('+m['d']+')-FrontFootInset',old)
                if n:v.parameter.expression=new;edits+=n
        assert edits==6,(key,edits)
    design.computeAll()
    assert all(b.isValid and b.isSolid and b.faces.count>0 and b.volume>0 for comp in design.allComponents for b in comp.bRepBodies)
    assert all(design.timeline.item(i).healthState==adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState for i in range(design.timeline.count))
    assert all(s.isFullyConstrained for comp in design.allComponents for s in comp.sketches)
    assert c.bRepBodies.count==1 and grate.bRepBodies.count==1
    expected=sorted([ev(m['w'])*10,ev(m['d'])*10,ev('PanHeight')*10])
    bb=c.bRepBodies.item(0).boundingBox
    actual=sorted([(getattr(bb.maxPoint,a)-getattr(bb.minPoint,a))*10 for a in ('x','y','z')])
    assert all(abs(a-b)<0.001 for a,b in zip(actual,expected)),(actual,expected)
    save_checkpoint('R02-'+key,CHECKPOINTS)
    print(json.dumps({'module':key,'pan_size_mm':actual,'positive_bodies':43,'features':design.timeline.count,'health_errors':0}))

def run(_context:str):
    if PHASE=='init':
        a=adsk.core.Application.get()
        current=adsk.fusion.Design.cast(a.activeProduct)
        assert a.activeDocument.name.startswith('Sink Organizer B - R01')
        expected=EXPECTED
        bodies={c.name:b for c in current.allComponents for b in c.bRepBodies}
        for name,volume in expected.items():assert abs(bodies[name].volume*1000-volume)<0.001,'R01 geometry changed: '+name
        doc=a.importManager.importToNewDocument(a.importManager.createFusionArchiveImportOptions(ARCHIVE))
        doc.name='Sink Organizer B - R02 OPEN EDGE'
        bind()
        design.userParameters.add('FrontFootInset',vi('17 mm'),'mm','R02 front foot center inset; outer foot edge is 9 mm behind open lip')
        design.userParameters.itemByName('DrainExtension').comment='R01 construction parameter: R02 has no external projection; this value still contributes to inherited floor thickness'
        design.userParameters.itemByName('DrainWidth').comment='R01 construction history only: R02 opens the entire front between side walls'
        print(json.dumps({'revision':'R02','parameters':design.userParameters.count,'R01_preserved':True}))
    else:revise_module(PHASE)
'''
manifest=json.loads((folder/'R01-delivery/model-manifest.json').read_text())
source=source.replace('PHASE',ascii(phase)).replace('ARCHIVE',ascii(str(folder/'R01-delivery/Sink_Organizer_B_R01_Prototype.f3d'))).replace('CHECKPOINTS',ascii(str(folder/'checkpoints/R02'))).replace('EXPECTED',repr({p['component']:p['volume_mm3'] for p in manifest['parts']}))
with FusionSession() as s:
 r=s.call('fusion_mcp_execute',{'featureType':'script','object':{'script':source}})
 for b in r['content']:
  if b['type']=='text':print(json.loads(b['text']).get('message',''),flush=True)
