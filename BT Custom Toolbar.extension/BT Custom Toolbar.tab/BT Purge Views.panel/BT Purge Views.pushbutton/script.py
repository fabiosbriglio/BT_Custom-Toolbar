# Import Revit API modules
from Autodesk.Revit.DB import FilteredElementCollector, View, Transaction, ViewType, ViewSheet
from pyrevit import forms

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views in the project
views = FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()

# Collect all sheets to check if a view is placed
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
views_on_sheets = set()
for sheet in sheets:
    for v_id in sheet.GetAllPlacedViews():
        views_on_sheets.add(v_id)

# View types to keep (essential ones)
protected_view_types = [
    ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.ThreeD, ViewType.EngineeringPlan,
    ViewType.Section, ViewType.Elevation, ViewType.Detail, ViewType.DraftingView, ViewType.Schedule
]

# Ensure the collected elements are valid views and not placed on sheets
unused_views = []
for v in views:
    try:
        if (v and not v.IsTemplate and v.ViewType not in protected_view_types
                and not v.IsDependent and v.Id not in views_on_sheets):
            unused_views.append(v)
    except Exception as e:
        print("Skipping element due to error: {}".format(e))

# Stop if no views to delete
if not unused_views:
    forms.alert("No unused views found! Try making sure your duplicate view is not placed on a sheet.", exitscript=True)
else:
    # Show a list of views that will be deleted
    view_names = "\n".join([v.Name for v in unused_views])
    confirm = forms.alert(
        title="Confirm Deletion",
        msg="The following {} views will be deleted:\n\n{}\n\nContinue?".format(len(unused_views), view_names),
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
