"""Check native meshes and create print-oriented, millimeter STL/3MF derivatives."""
from pathlib import Path
import sys,json,zipfile,xml.etree.ElementTree as ET
sys.path.insert(0,'/tmp/sink-validation-libs')
import numpy as np
import trimesh

revision=sys.argv[1] if len(sys.argv)>1 else 'R01'
assert revision in ('R01','R02')
root=Path(__file__).resolve().parent/(revision+'-delivery')
manifest=json.loads((root/'model-manifest.json').read_text())
stl=root/'print-stl';stl.mkdir(exist_ok=True)
mf=root/'print-3mf';mf.mkdir(exist_ok=True)
NS='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
ET.register_namespace('',NS)
def node(name,attrs=None):return ET.Element('{'+NS+'}'+name,attrs or {})
def write_3mf(mesh,path,qty):
    model=node('model',{'unit':'millimeter','{http://www.w3.org/XML/1998/namespace}lang':'en-US'})
    meta=node('metadata',{'name':'Title'});meta.text=path.stem;model.append(meta)
    resources=node('resources');model.append(resources)
    obj=node('object',{'id':'1','type':'model','name':path.stem});resources.append(obj)
    geom=node('mesh');obj.append(geom);verts=node('vertices');geom.append(verts)
    for p in mesh.vertices:verts.append(node('vertex',dict(zip(('x','y','z'),(format(float(x),'.8f') for x in p)))))
    tris=node('triangles');geom.append(tris)
    for tri in mesh.faces:tris.append(node('triangle',dict(zip(('v1','v2','v3'),map(str,tri)))))
    build=node('build');model.append(build)
    for i in range(qty):
        attrs={'objectid':'1'}
        if qty>1:attrs['transform']='1 0 0 0 1 0 0 0 1 %g %g 0'%((i%6)*20,(i//6)*20)
        build.append(node('item',attrs))
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('[Content_Types].xml','<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        archive.writestr('_rels/.rels','<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        archive.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        parsed=ET.fromstring(archive.read('3D/3dmodel.model'))
        assert parsed.attrib['unit']=='millimeter'
        assert len(parsed.find('{'+NS+'}build'))==qty
        v=np.array([[float(e.attrib[a]) for a in ('x','y','z')] for e in parsed.findall('.//{'+NS+'}vertex')])
        assert np.allclose(v,mesh.vertices,atol=1e-7)

def connected_faces(mesh):
    parents=list(range(len(mesh.faces)))
    def find(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]];i=parents[i]
        return i
    for a,b in mesh.face_adjacency:
        a,b=find(int(a)),find(int(b))
        if a!=b:parents[b]=a
    return len({find(i) for i in range(len(parents))})

checks=[]
for part in manifest['parts']:
    mesh=trimesh.load_mesh(root/'cad-meshes'/part['file'],process=True)
    assert np.isfinite(mesh.vertices).all(),part['file']
    assert mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume,part['file']
    assert connected_faces(mesh)==1,part['file']
    assert (mesh.area_faces>1e-10).all(),part['file']
    assert np.allclose(mesh.bounds,part['bounds_mm'],atol=0.001),part['file']
    volume_error=abs(mesh.volume-part['volume_mm3'])/part['volume_mm3']
    assert volume_error<0.01,(part['file'],volume_error)
    if part['component'].startswith('Tower_'):
        transform=np.eye(4);transform[:3,:3]=[[0,1,0],[0,0,1],[1,0,0]]
        mesh.apply_transform(transform)
    mesh.apply_translation(-mesh.bounds[0])
    dims=mesh.extents
    assert dims[0]+10<=235.5 and dims[1]+10<=256 and dims[2]<=256,(part['file'],dims)
    path=stl/part['file'];mesh.export(path,file_type='stl')
    back=trimesh.load_mesh(path,process=True)
    assert back.is_watertight and back.is_winding_consistent and np.allclose(back.extents,dims,atol=.001)
    write_3mf(mesh,mf/(path.stem+'.3mf'),part['quantity'])
    checks.append({'file':part['file'],'quantity':part['quantity'],'print_size_mm':dims.round(3).tolist(),'triangles':len(mesh.faces),'watertight':True,'consistent_normals':True,'connected_parts':1,'cad_volume_relative_error':float(volume_error)})
report={'units':'mm','files_checked':len(checks),'assembly_printed_pieces':40,'optional_fit_coupons':3,'cad_interferences':manifest['interferences'],'sliced':False,'physically_tested':False,'verification_scope':'Native solid and feature checks; native interference; mesh closure, winding, connectivity, finite nondegenerate triangles, bounds and volume comparison; STL/3MF round-trip. Not a complete triangle intersection or toolpath test.','parts':checks}
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'checked':len(checks),'max_relative_volume_error':max(c['cad_volume_relative_error'] for c in checks),'parts':[{k:c[k] for k in ('file','quantity','print_size_mm')} for c in checks]},ensure_ascii=False))
