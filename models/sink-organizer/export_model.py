"""Export verified native geometry. Capture previews separately through the UI.
The camera/export-image sequence stalled Fusion on this host; never couple it to delivery.
"""
from pathlib import Path
import json,sys
from fusion_mcp import FusionSession
folder=Path(__file__).resolve().parent
revision=sys.argv[1] if len(sys.argv)>1 else 'R01'
assert revision in ('R01','R02')
source=(folder/'model_builder.py').read_text().replace("'Sink Organizer B - R01'","'Sink Organizer B - "+revision+"'")
source+='''
def run(_context: str):
    import pathlib
    bind()
    out=pathlib.Path(OUTPUT)
    out.mkdir(exist_ok=True)
    raw=out/'cad-meshes';raw.mkdir(exist_ok=True)
    previews=out/'previews';previews.mkdir(exist_ok=True)
    assert len([b for c in design.allComponents for b in c.bRepBodies])==43
    design.computeAll()
    for i in range(design.timeline.count):
        t=design.timeline.item(i)
        assert t.healthState==adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,t.name+': '+t.errorOrWarningMessage
    for c in design.allComponents:
        for sk in c.sketches:assert sk.isFullyConstrained,c.name+'/'+sk.name
    items=adsk.core.ObjectCollection.create()
    for o in root.occurrences:
        if not o.component.name.startswith('FIT_'):items.add(o)
    inter=design.createInterferenceInput(items);inter.areCoincidentFacesIncluded=False
    assert design.analyzeInterference(inter).count==0,'Assembly interference'
    archive=out/'Sink_Organizer_B_REVISION_Prototype.f3d'
    # This task's delivery archive is regenerated from the checked active design.
    for occurrence in root.occurrences:
        occurrence.isLightBulbOn=not occurrence.component.name.startswith('FIT_')
        for body in occurrence.component.bRepBodies:body.isLightBulbOn=True
    app.activeViewport.refresh()
    assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(archive)))
    record={'document':app.activeDocument.name,'revision':'REVISION prototype','parameters':[{'name':p.name,'expression':p.expression,'comment':p.comment} for p in design.userParameters],'assembly_body_count':40,'fit_coupons':3,'features':design.timeline.count,'interferences':0,'parts':[]}
    for c in sorted(design.allComponents,key=lambda c:c.name):
        if c.bRepBodies.count==0:continue
        assert c.bRepBodies.count==1
        b=c.bRepBodies.item(0);assert b.isValid and b.isSolid and b.faces.count>0 and b.volume>0,c.name
        if '_Foot_' in c.name:assert abs(b.volume*1000-5216)<0.01,c.name+' peg incomplete'
        if '_Foot_' in c.name and c.name!='L1_Foot_00':continue
        name='Foot_x24' if '_Foot_' in c.name else c.name
        path=raw/(name+'.stl')
        opts=design.exportManager.createSTLExportOptions(b,str(path))
        opts.unitType=adsk.fusion.DistanceUnits.MillimeterDistanceUnits
        opts.isBinaryFormat=True;opts.sendToPrintUtility=False
        opts.surfaceDeviation=0.005
        opts.isIncludingInvisibleBodies=True
        assert design.exportManager.execute(opts)
        bb=b.boundingBox
        record['parts'].append({'file':path.name,'component':c.name,'quantity':24 if name=='Foot_x24' else 1,'volume_mm3':b.volume*1000,'bounds_mm':[[getattr(p,a)*10 for a in ('x','y','z')] for p in (bb.minPoint,bb.maxPoint)],'solid':b.isSolid})
    (out/'model-manifest.json').write_text(json.dumps(record,ensure_ascii=True,indent=2))
    print(json.dumps({'archive':str(archive),'mesh_files':len(record['parts']),'body_count':43,'interferences':0}))
'''
source=source.replace('OUTPUT',ascii(str(folder/(revision+'-delivery')))).replace('REVISION',revision)
with FusionSession() as session:
    print(json.dumps(session.call('fusion_mcp_execute',{'featureType':'script','object':{'script':source}}),ensure_ascii=False))
