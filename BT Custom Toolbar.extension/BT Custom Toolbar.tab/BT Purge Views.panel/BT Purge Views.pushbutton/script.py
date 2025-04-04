# Import Revit API modules
from Autodesk.Revit.DB import FilteredElementCollector, View, Transaction, ViewType
from pyrevit import forms

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views in the project
views = FilteredElementCollector(doc).OfClass(View).ToElements()

# View types to keep (essential ones)
protected_view_types = [
    ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.ThreeD, ViewType.EngineeringPlan,
    ViewType.Section, ViewType.Elevation, ViewType.Detail, ViewType.DraftingView, ViewType.Schedule
]

# Filter unused views (excluding view templates and protected view types)
unused_views = [v for v in views if not v.IsTemplate and v.ViewType not in protected_view_types]

# Ask for confirmation before deleting
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
                print(f"Could not delete {v.Name}: {e}")

        t.Commit()

        # Show result
        forms.alert(f"Deleted {deleted_count} unused views successfully!")
