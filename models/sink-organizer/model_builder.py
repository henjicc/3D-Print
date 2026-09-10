"""Task-specific Fusion native feature builder. All expressions use mm / degrees.
The active document is checked before every phase. No source document is closed.
"""
import adsk.core, adsk.fusion, json, math

def bind():
    global app, design, root
    app=adsk.core.Application.get()
    assert app.activeDocument.name.startswith('Sink Organizer B - R01'), 'Wrong target document'
    design=adsk.fusion.Design.cast(app.activeProduct)
    root=design.rootComponent

def vi(s): return adsk.core.ValueInput.createByString(str(s))
def ev(s): return design.unitsManager.evaluateExpression(str(s),'mm')
def pt(x,y,z='0 mm'): return adsk.core.Point3D.create(ev(x),ev(y),ev(z))
def plus(a,b): return '('+str(a)+')+('+str(b)+')'
def minus(a,b): return '('+str(a)+')-('+str(b)+')'
def mul(a,b): return '('+str(a)+')*('+str(b)+')'

def component(name):
    assert not any(c.name==name for c in design.allComponents), 'Component already exists: '+name
    o=root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    o.component.name=name
    return o.component

def plane(c,kind,offset,name):
    base={'xy':c.xYConstructionPlane,'yz':c.yZConstructionPlane,'xz':c.xZConstructionPlane}[kind]
    inp=c.constructionPlanes.createInput()
    assert inp.setByOffset(base,vi(offset))
    p=c.constructionPlanes.add(inp);p.name=name;p.isLightBulbOn=False
    return p

def sketch(c,kind,offset,name):
    s=c.sketches.add(plane(c,kind,offset,name+' datum'))
    s.name=name
    return s

def dim(s,a,b,orientation,expr):
    p=b.geometry.copy();p.x+=0.3;p.y+=0.3
    d=s.sketchDimensions.addDistanceDimension(a,b,orientation,p)
    d.parameter.expression=expr
    return d

H=adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation
V=adsk.fusion.DimensionOrientations.VerticalDimensionOrientation
NEW=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
JOIN=adsk.fusion.FeatureOperations.JoinFeatureOperation
CUT=adsk.fusion.FeatureOperations.CutFeatureOperation

def rectangle(s,x,y,w,d):
    ls=s.sketchCurves.sketchLines.addTwoPointRectangle(pt(x,y),pt(plus(x,w),plus(y,d)))
    for i in range(4):
        if i%2==0: s.geometricConstraints.addHorizontal(ls.item(i))
        else: s.geometricConstraints.addVertical(ls.item(i))
    a=ls.item(0).startSketchPoint;b=ls.item(0).endSketchPoint;c=ls.item(1).endSketchPoint
    dim(s,s.originPoint,a,H,x);dim(s,s.originPoint,a,V,y)
    dim(s,a,b,H,w);dim(s,b,c,V,d)
    return ls

def polygon_world(s,xyz):
    # Projection of global coordinates into the verified sketch coordinate basis.
    zero=s.modelToSketchSpace(adsk.core.Point3D.create(0,0,0))
    basis=[s.modelToSketchSpace(adsk.core.Point3D.create(int(i==0),int(i==1),int(i==2))) for i in range(3)]
    mapped=[]
    for coords in xyz:
        vals=[]
        for axis in ('x','y'):
            coeff=[getattr(p,axis)-getattr(zero,axis) for p in basis]
            assert abs(getattr(zero,axis))<1e-7, 'Unexpected in-plane datum offset'
            terms=[('' if a>0 else '-')+'('+e+')' for a,e in zip(coeff,coords) if abs(a)>0.5]
            vals.append('+'.join(terms) if terms else '0 mm')
        mapped.append(vals)
    ls=[]
    for i,p in enumerate(mapped):
        if i==0: a=pt(*p)
        else: a=ls[-1].endSketchPoint
        b=ls[0].startSketchPoint if i==len(mapped)-1 else pt(*mapped[i+1])
        ls.append(s.sketchCurves.sketchLines.addByTwoPoints(a,b))
    for constraint in list(s.geometricConstraints):
        if constraint.objectType in ('adsk::fusion::HorizontalConstraint','adsk::fusion::VerticalConstraint'):
            constraint.deleteMe()
    groups=[list(range(len(ls))),list(range(len(ls)))]
    def leader(axis,i):
        while groups[axis][i]!=i: i=groups[axis][i]
        return i
    for i,l in enumerate(ls):
        j=(i+1)%len(ls)
        if abs(ev(mapped[i][0])-ev(mapped[j][0]))<1e-7:
            s.geometricConstraints.addVertical(l)
            groups[0][leader(0,j)]=leader(0,i)
        elif abs(ev(mapped[i][1])-ev(mapped[j][1]))<1e-7:
            s.geometricConstraints.addHorizontal(l)
            groups[1][leader(1,j)]=leader(1,i)
    seen=[set(),set()]
    for i,(l,coords) in enumerate(zip(ls,mapped)):
        for axis,(ori,e) in enumerate(zip((H,V),coords)):
            key=leader(axis,i)
            if key in seen[axis]: continue
            seen[axis].add(key)
            val=ev(e)
            assert abs(val)>1e-7, 'Polygon vertex on datum axis requires special constraint'
            dim(s,s.originPoint,l.startSketchPoint,ori,e if val>0 else '-('+e+')')
    assert s.isFullyConstrained, 'Unconstrained polygon '+s.name

def extrude(c,s,distance,op,name):
    assert s.profiles.count>0, 'No closed profile: '+s.name
    profiles=adsk.core.ObjectCollection.create()
    for p in s.profiles: profiles.add(p)
    if op==CUT:
        assert c.bRepBodies.count==1, 'Cut requires one explicit target body'
        inp=c.features.extrudeFeatures.createInput(profiles,op)
        extent=adsk.fusion.DistanceExtentDefinition.create(vi(distance if ev(distance)>0 else '-('+distance+')'))
        direction=adsk.fusion.ExtentDirections.PositiveExtentDirection if ev(distance)>0 else adsk.fusion.ExtentDirections.NegativeExtentDirection
        assert inp.setOneSideExtent(extent,direction)
        inp.participantBodies=[c.bRepBodies.item(0)]
        f=c.features.extrudeFeatures.add(inp)
    else:
        f=c.features.extrudeFeatures.addSimple(profiles,vi(distance),op)
    f.name=name;s.isVisible=False
    assert f.healthState==adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState, f.errorOrWarningMessage
    return f

def block(c,x,y,w,d,z,h,op,name):
    s=sketch(c,'xy',z,name+' sketch');rectangle(s,x,y,w,d)
    assert s.isFullyConstrained, 'Unconstrained rectangle '+name
    return extrude(c,s,h,op,name)

def round_vertical(c,body,radius,name):
    edges=adsk.core.ObjectCollection.create()
    for e in body.edges:
        p=e.startVertex.geometry;q=e.endVertex.geometry
        if abs(p.x-q.x)<1e-7 and abs(p.y-q.y)<1e-7 and abs(p.z-q.z)>1e-5: edges.add(e)
    assert edges.count==4, 'Expected four exterior vertical edges'
    inp=c.features.filletFeatures.createInput()
    inp.edgeSetInputs.addConstantRadiusEdgeSet(edges,vi(radius),False)
    f=c.features.filletFeatures.add(inp);f.name=name
    assert f.healthState==adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState,f.errorOrWarningMessage

def specs():
    return [
      dict(key='L1',x='BaseX+TowerFrame+TowerClearance',y='BaseY',w='TowerWidth-2*(TowerFrame+TowerClearance)',d='Depth',z='FootHeight',out='TowerWidth-2*(TowerFrame+TowerClearance)-31 mm',orient='rear',feet=True),
      dict(key='L2',x='BaseX+TowerWidth+ModuleGap',y='BaseY',w='LeftRun-TowerWidth-ModuleGap',d='Depth',z='FootHeight',out='(LeftRun-TowerWidth-ModuleGap)/2',orient='rear',feet=True),
      dict(key='R1',x='BaseX+LeftRun+FaucetGap',y='BaseY',w='(RightRun-ModuleGap)/2',d='Depth',z='FootHeight',out='(RightRun-ModuleGap)/4',orient='rear',feet=True),
      dict(key='R2',x='BaseX+LeftRun+FaucetGap+(RightRun+ModuleGap)/2',y='BaseY',w='(RightRun-ModuleGap)/2',d='Depth',z='FootHeight',out='18 mm',orient='rear',feet=True),
      dict(key='LS',x='BaseX',y='BaseY+Depth+ModuleGap',w='LeftReach',d='LeftSideDepth',z='FootHeight',out='LeftReach/2',orient='left',feet=True),
      dict(key='RS',x='BaseX+LeftRun+FaucetGap+RightRun-RightSideDepth',y='BaseY+Depth+ModuleGap',w='RightReach',d='RightSideDepth',z='FootHeight',out='RightReach/2',orient='right',feet=True),
      dict(key='UP',x='BaseX',y='BaseY',w='TowerWidth',d='Depth',z='UpperDeckHeight-PanHeight',out='TowerWidth-35 mm',orient='rear',feet=False)]

def xy(m,u,v):
    if m['orient']=='rear': return plus(m['x'],u),plus(m['y'],v)
    if m['orient']=='left': return plus(m['x'],v),plus(m['y'],minus(m['w'],u))
    return plus(m['x'],minus(m['d'],v)),plus(m['y'],u)

def mapped_rect(c,m,u,v,w,d,z,h,op,name):
    if m['orient']=='rear': x,y=xy(m,u,v);ww,dd=w,d
    elif m['orient']=='left': x,y=xy(m,plus(u,w),v);ww,dd=d,w
    else: x,y=xy(m,u,plus(v,d));ww,dd=d,w
    return block(c,x,y,ww,dd,z,h,op,name)

def slope_extrude(c,m,u,width,vz,op,name):
    # Cross section follows inward depth; extrusion follows transverse module width.
    if m['orient']=='rear':
        kind='yz';off=plus(m['x'],u);length=width
    elif m['orient']=='left':
        kind='xz';off=plus(m['y'],minus(m['w'],u));length='-('+width+')'
    else:
        kind='xz';off=plus(m['y'],u);length=width
    s=sketch(c,kind,off,name+' section')
    coords=[]
    for v,z in vz:
        x,y=xy(m,u,v);coords.append((x,y,z))
    polygon_world(s,coords)
    return extrude(c,s,length,op,name)

def floor(m,v): return '('+m['z']+')+FloorMin+DrainExtension*tan(DrainSlope)+(('+m['d']+')-('+v+'))*tan(DrainSlope)'

def make_pan(m):
    c=component(m['key']+'_DrainPan')
    f=mapped_rect(c,m,'0 mm','0 mm',m['w'],m['d'],m['z'],'PanHeight',NEW,'Pan blank')
    round_vertical(c,f.bodies.item(0),'3 mm','Outside corner rounds')
    # Main open cavity with a continuously sloping floor.
    v0='Wall';v1='('+m['d']+')-Wall';ztop='('+m['z']+')+PanHeight+1 mm'
    slope_extrude(c,m,'Wall','('+m['w']+')-2*Wall',[(v0,floor(m,v0)),(v1,floor(m,v1)),(v1,ztop),(v0,ztop)],CUT,'Sloped catch cavity')
    # Full-width open tongue floor and its two side rails.
    u='('+m['out']+')-DrainWidth/2-Wall';v0='('+m['d']+')-Wall';v1='('+m['d']+')+DrainExtension'
    floorpoly=[(v0,m['z']),(v1,m['z']),(v1,floor(m,v1)),(v0,floor(m,v0))]
    slope_extrude(c,m,u,'DrainWidth+2*Wall',floorpoly,JOIN,'Drain tongue floor')
    for side in (u,'('+m['out']+')+DrainWidth/2'):
        poly=[(v0,m['z']),(v1,m['z']),(v1,plus(floor(m,v1),'6 mm')),(v0,plus(floor(m,v0),'6 mm'))]
        slope_extrude(c,m,side,'Wall',poly,JOIN,'Tongue side rail')
    # Open the front wall all the way down to the same slope. No dam at the outlet.
    slope_extrude(c,m,'('+m['out']+')-DrainWidth/2','DrainWidth',[(v0,floor(m,v0)),(v1,floor(m,v1)),(v1,ztop),(v0,ztop)],CUT,'Open drain mouth')
    # Four internal seats, keeping the grate horizontal and removable from above.
    for i,u0 in enumerate(('Wall','('+m['w']+')-Wall-12 mm')):
        for j,v in enumerate(('Wall','('+m['d']+')-Wall-12 mm')):
            seat_u='('+m['out']+')+DrainWidth/2+3 mm' if m['key']=='R2' and i==0 and j==1 else u0
            mapped_rect(c,m,seat_u,v,'12 mm','12 mm',m['z'],'PanHeight-DeckThick',JOIN,'Grate seat '+str(i)+str(j))
    # Drain-end underside relief to interrupt water tracking back along the tongue.
    v='('+m['d']+')+DrainExtension-2 mm'
    slope_extrude(c,m,u,'DrainWidth+2*Wall',[(v,minus(m['z'],'0.2 mm')),(plus(v,'1 mm'),minus(m['z'],'0.2 mm')),(plus(v,'1 mm'),plus(m['z'],'0.6 mm')),(v,plus(m['z'],'0.6 mm'))],CUT,'Drip break underside groove')
    if m['feet']:
        for i,u0 in enumerate(('11 mm','('+m['w']+')-11 mm')):
            for j,v in enumerate(('11 mm','('+m['d']+')-11 mm')):
                mapped_rect(c,m,'('+u0+')-PegSize/2-FitClearance','('+v+')-PegSize/2-FitClearance','PegSize+2*FitClearance','PegSize+2*FitClearance',m['z'],'PegHeight+0.3 mm',CUT,'Foot socket '+str(i)+str(j))
    c.bRepBodies.item(0).name=c.name
    assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid
    return c

def summarize():
    issues=[];bodies=[];under=[]
    for c in design.allComponents:
        for s in c.sketches:
            if not s.isFullyConstrained: under.append(c.name+'/'+s.name)
        for b in c.bRepBodies:
            q=b.boundingBox
            bodies.append({'name':c.name+'/'+b.name,'solid':b.isSolid,'volume_mm3':round(b.volume*1000,2),'size_mm':[round((getattr(q.maxPoint,a)-getattr(q.minPoint,a))*10,3) for a in ('x','y','z')]})
    for i in range(design.timeline.count):
        t=design.timeline.item(i)
        if t.healthState!=adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState: issues.append({'name':t.name,'message':t.errorOrWarningMessage})
    print(json.dumps({'document':app.activeDocument.name,'features':design.timeline.count,'bodies':bodies,'issues':issues,'underconstrained':under},ensure_ascii=False))

def make_grate(m):
    c=component(m['key']+'_RemovableGrate')
    inset='Wall+DeckClearance'
    z='('+m['z']+')+PanHeight-DeckThick'
    mapped_rect(c,m,inset,inset,'('+m['w']+')-2*('+inset+')','('+m['d']+')-2*('+inset+')',z,'DeckThick',NEW,'Horizontal removable deck')
    n=max(1,int((ev(m['w'])-2*ev(inset)-2*ev('RimBorder'))/ev('SlotPitch')))
    start='(('+m['w']+')-('+str(n-1)+'*SlotPitch+SlotWidth))/2'
    for i in range(n):
        u=plus(start,str(i)+'*SlotPitch')
        mapped_rect(c,m,u,'Wall+DeckClearance+RimBorder','SlotWidth','('+m['d']+')-2*(Wall+DeckClearance+RimBorder)',z,'DeckThick',CUT,'Drain slot '+str(i+1))
    mapped_rect(c,m,'('+m['w']+')/2-8 mm','('+m['d']+')-Wall-DeckClearance-4 mm','16 mm','5 mm',z,'DeckThick',CUT,'Finger lift notch')
    assert c.bRepBodies.count==1 and c.bRepBodies.item(0).isSolid
    c.bRepBodies.item(0).name=c.name
    return c

def make_feet(m):
    for i,u in enumerate(('11 mm','('+m['w']+')-11 mm')):
        for j,v in enumerate(('11 mm','('+m['d']+')-11 mm')):
            c=component(m['key']+'_Foot_'+str(i)+str(j))
            mapped_rect(c,m,'('+u+')-FootSize/2','('+v+')-FootSize/2','FootSize','FootSize','0 mm','FootHeight',NEW,'Foot base')
            mapped_rect(c,m,'('+u+')-PegSize/2','('+v+')-PegSize/2','PegSize','PegSize','FootHeight','PegHeight',JOIN,'Locating peg')
            c.bRepBodies.item(0).name=c.name

def make_tower():
    # Side frames print on their broad side; top pan acts as the cross tie.
    # Four small keys locate the pan; no claim of a snap-fit or load rating.
    for side,x in enumerate(('BaseX','BaseX+TowerWidth-TowerFrame')):
        c=component('Tower_SideFrame_'+str(side+1))
        top='UpperDeckHeight-PanHeight'
        block(c,x,'BaseY','TowerFrame','Depth','0 mm',top,NEW,'Portal frame blank')
        # Cut the opening sideways so it remains a one-piece rectangular portal.
        ss=sketch(c,'yz',x,'Open portal section')
        polygon_world(ss,[(x,'BaseY+12 mm','8 mm'),(x,'BaseY+Depth-12 mm','8 mm'),(x,'BaseY+Depth-12 mm',top+'-8 mm'),(x,'BaseY+12 mm',top+'-8 mm')])
        extrude(c,ss,'TowerFrame',CUT,'Open portal')
        for y in ('BaseY+8 mm','BaseY+Depth-8 mm'):
            block(c,plus(x,'(TowerFrame-5 mm)/2'),minus(y,'2.5 mm'),'5 mm','5 mm',top,'PegHeight',JOIN,'Upper tray locating key')
        c.bRepBodies.item(0).name=c.name
    upper=next(c for c in design.allComponents if c.name=='UP_DrainPan')
    for x in ('BaseX+(TowerFrame-5 mm)/2','BaseX+TowerWidth-TowerFrame+(TowerFrame-5 mm)/2'):
        for y in ('BaseY+8 mm','BaseY+Depth-8 mm'):
            block(upper,minus(x,'FitClearance'),minus(y,'2.5 mm+FitClearance'),'5 mm+2*FitClearance','5 mm+2*FitClearance','UpperDeckHeight-PanHeight','PegHeight+0.3 mm',CUT,'Upper frame key socket')

def save_checkpoint(label,folder):
    import pathlib
    folder=pathlib.Path(folder);folder.mkdir(parents=True,exist_ok=True)
    path=folder/(label+'.f3d')
    assert not path.exists(), 'Checkpoint already exists; inspect before retry'
    assert design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path)))
    print(json.dumps({'checkpoint':str(path),'bytes':path.stat().st_size}))

def make_fit_coupons():
    for i,(name,clearance) in enumerate((('Tight','FitClearance-0.05 mm'),('Nominal','FitClearance'),('Loose','FitClearance+0.05 mm'))):
        c=component('FIT_'+name)
        x='BaseX+LeftRun+FaucetGap+RightRun+20 mm+'+str(i*30)+' mm'
        block(c,x,'BaseY','24 mm','24 mm','0 mm','4 mm',NEW,'Fit coupon plate')
        width='PegSize+2*('+clearance+')'
        block(c,plus(x,'(24 mm-('+width+'))/2'),'BaseY+(24 mm-('+width+'))/2',width,width,'0 mm','PegHeight+0.3 mm',CUT,'Foot locating socket')
        c.bRepBodies.item(0).name=c.name
        next(o for o in root.occurrences if o.component==c).isLightBulbOn=False

def build_phase(phase,folder):
    bind()
    if phase in ('L1-corner','R2-corner'):
        key=phase.split('-')[0]
        for o in list(root.occurrences):
            if o.component.name==key+'_DrainPan': o.deleteMe()
        make_pan(next(m for m in specs() if m['key']==key))
    elif phase=='L1-revised':
        for o in list(root.occurrences):
            if o.component.name=='L1_DrainPan': o.deleteMe()
        make_pan(specs()[0])
        make_grate(specs()[0]);make_feet(specs()[0])
    elif phase=='tower': make_tower()
    elif phase=='coupons': make_fit_coupons()
    else:
        m=next(m for m in specs() if m['key']==phase)
        make_pan(m);make_grate(m)
        if m['feet']:make_feet(m)
    design.computeAll()
    summarize()
    save_checkpoint('R01-'+phase,folder)
    app.activeViewport.fit()

def run(_context: str):
    bind()
    design.userParameters.itemByName('PanHeight').expression='20 mm'
    make_pan(specs()[0])
    app.activeViewport.fit()
    summarize()
