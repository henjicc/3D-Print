"""One-shot native backup before MCP recovery. Does not model or close documents."""
import adsk.core, adsk.fusion, pathlib, json

def run(context):
    folder=pathlib.Path(__file__).parent.parent
    out=folder/'mcp-recovery-20260910'
    out.mkdir(exist_ok=True)
    app=adsk.core.Application.get()
    original=app.activeDocument
    docs=[app.documents.item(i) for i in range(app.documents.count)]
    records=[]
    for i,doc in enumerate(docs):
        doc.activate()
        design=adsk.fusion.Design.cast(app.activeProduct)
        record={'index':i,'name':doc.name,'isSaved':doc.isSaved,'isModified':doc.isModified}
        if design:
            path=out/('recovery_doc_%02d.f3d'%i)
            assert not path.exists(), 'Recovery file already exists; inspect before retry'
            options=design.exportManager.createFusionArchiveExportOptions(str(path))
            assert design.exportManager.execute(options), 'Archive export failed'
            record.update({'archive':str(path),'bytes':path.stat().st_size,'parameters':design.userParameters.count,'components':design.allComponents.count,'rootBodies':design.rootComponent.bRepBodies.count,'timeline':design.timeline.count})
        else:
            record['skipped']='Not a Fusion design; preserved open'
        records.append(record)
        (out/'backup-index.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    original.activate()
    (out/'backup-complete.txt').write_text('Native archive backup completed; original documents remain open.\n')
