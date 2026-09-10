import adsk.core, adsk.fusion, json

def run(_context: str):
    app=adsk.core.Application.get()
    doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    doc.name='Sink Organizer B - R01 PROTOTYPE'
    design=adsk.fusion.Design.cast(app.activeProduct)
    design.designType=adsk.fusion.DesignTypes.ParametricDesignType
    params=[
      ('LeftAvailable','400 mm','mm','User approximate dimension: left of faucet'),
      ('RightAvailable','300 mm','mm','User approximate dimension: right of faucet'),
      ('RearAvailable','100 mm','mm','User approximate rear strip depth'),
      ('LeftSideAvailable','130 mm','mm','User approximate left strip width'),
      ('MirrorClearance','300 mm','mm','User approximate countertop to mirror cabinet'),
      ('RightSideAvailable','100 mm','mm','ASSUMPTION: awaiting measurement'),
      ('LeftReach','180 mm','mm','ASSUMPTION: forward side extension beyond rear rack'),
      ('RightReach','180 mm','mm','ASSUMPTION: forward side extension beyond rear rack'),
      ('FaucetGap','160 mm','mm','ASSUMPTION: faucet and lever clearance, awaiting measurement'),
      ('LeftRun','LeftAvailable - 20 mm','mm','Design clearance allowance; check on site'),
      ('RightRun','RightAvailable - 30 mm','mm','Design clearance allowance; check lever'),
      ('Depth','RearAvailable - 10 mm','mm','Rear standing module depth'),
      ('LeftSideDepth','LeftSideAvailable - 10 mm','mm','Left side module depth'),
      ('RightSideDepth','RightSideAvailable - 10 mm','mm','Right side module depth, provisional'),
      ('ModuleGap','2 mm','mm','Open cleaning / assembly seam, not watertight'),
      ('TowerWidth','180 mm','mm','Local upper tier only'),
      ('TowerFrame','8 mm','mm','Side portal frame thickness'),
      ('TowerClearance','2 mm','mm','Clearance from lower tray to side frames'),
      ('FootHeight','20 mm','mm','Clear gap below pan'),
      ('PanHeight','20 mm','mm','Pan rim above underside'),
      ('FloorMin','3 mm','mm','Minimum pan floor at outlet'),
      ('Wall','3 mm','mm','Pan walls'),
      ('DrainSlope','4 deg','deg','Initial design slope; verify with water test'),
      ('DeckThick','4 mm','mm','Removable horizontal grate thickness'),
      ('DeckClearance','0.3 mm','mm','Per-side clearance; fit coupon required'),
      ('RimBorder','7 mm','mm','Solid grate border'),
      ('SlotWidth','4 mm','mm','Open slat gaps'),
      ('SlotPitch','10 mm','mm','Initial grate slot spacing'),
      ('DrainWidth','28 mm','mm','Clear outlet width'),
      ('DrainExtension','25 mm','mm','ASSUMPTION: reaches at least 10 mm inside basin'),
      ('UpperDeckHeight','145 mm','mm','Small jars only; verify cabinet swing'),
      ('FootSize','16 mm','mm','Support foot footprint'),
      ('PegSize','8 mm','mm','Square locating peg'),
      ('PegHeight','1.5 mm','mm','Foot locating peg, not a locking fastener'),
      ('FitClearance','0.25 mm','mm','Per-side foot fit allowance; test first'),
      ('BaseX','50 mm','mm','Model datum offset'),
      ('BaseY','50 mm','mm','Model datum offset')]
    for name,expr,unit,note in params:
        design.userParameters.add(name,adsk.core.ValueInput.createByString(expr),unit,note)
    print(json.dumps({'document':doc.name,'version':app.version,'parameters':design.userParameters.count,'designType':int(design.designType),'originalDocumentsPreserved':app.documents.count},ensure_ascii=False))
