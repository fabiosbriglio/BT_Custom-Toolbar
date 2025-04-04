from Autodesk.Revit.DB import FilteredElementCollector, View, Transaction

doc = __revit__.ActiveUIDocument.Document

views = FilteredElementCollector(doc).OfClass(View).ToElements()

t = Transaction(doc, "Delete Unused Views")
t.Start()

deleted_count = 0
for v in views:
    if not v.IsTemplate and v.ViewType not in [ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.ThreeD]:
        try:
            doc.Delete(v.Id)
            deleted_count += 1
        except:
            pass

t.Commit()

print(f"Deleted {deleted_count} unused views.")