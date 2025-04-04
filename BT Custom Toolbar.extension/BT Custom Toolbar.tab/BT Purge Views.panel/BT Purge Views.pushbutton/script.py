# Import Revit API modules
from Autodesk.Revit.DB import FilteredElementCollector, View, Transaction, ViewType
from pyrevit import forms

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views in the project
views = FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()

# View types to keep (essential ones)
protected_view_types = [
    ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.ThreeD, ViewType.EngineeringPlan,
    ViewType.Section, ViewType.Elevation, ViewType.Detail, ViewType.DraftingView, ViewType.Schedule
]

# Ensure the collected elements are valid views
unused_views = []
for v in views:
    try:
        if v and not v.IsTemplate and v.ViewType not in protected_view_types and not v.IsDependent:
            unused_views.append(v)
    except Exception as e:
        print("Skipping element due to error: {}".format(e))

# Stop if no views to delete
if not unused_views:
    forms.alert("No unused views found!", exitscript=True)
else:
    confirm = forms.alert(
        title="Confirm Deletion",
        msg="This will delete {} unused views. Continue?".format(len(unused_views)),
        ok=True, cancel=True
    )

    if confirm:
        # Start a transaction
        t = Transaction(doc, "Purge Unused Views")
        t.Start()

        deleted_count = 0
        for v in unused_views:
            try:
                doc.Delete(v.Id)
                deleted_count += 1
            except Exception as e:
                print("Could not delete {}: {}".format(v.Name, e))  # Fixed string formatting

        t.Commit()

        # Show result
        forms.alert("Deleted {} unused views successfully!".format(deleted_count))
