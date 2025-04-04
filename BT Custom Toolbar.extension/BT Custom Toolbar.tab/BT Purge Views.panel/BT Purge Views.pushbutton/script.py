from Autodesk.Revit.DB import FilteredElementCollector, View, ViewSheet, Transaction
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views, EXCLUDING SHEETS
views = FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()

# Collect all sheets to check if a view is placed
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
views_on_sheets = set()
for sheet in sheets:
    for v_id in sheet.GetAllPlacedViews():
        views_on_sheets.add(v_id)

# Debugging Output
output = script.get_output()
output.print_md("### 🔍 **Checking Views to Delete**")

# List of views to delete (only views NOT on sheets, and NOT sheets themselves)
unused_views = []
for v in views:
    try:
        # Skip if the view is a SHEET
        if isinstance(v, ViewSheet) or v.ViewType == ViewType.DrawingSheet:
            output.print_md(f"📄 Keeping Sheet: {v.Name}")
            continue

        # Skip views that ARE placed on sheets
        if v.Id in views_on_sheets:
            output.print_md(f"📌 Keeping View on Sheet: {v.Name}")
            continue

        # If a view is NOT on a sheet, mark it for deletion
        unused_views.append(v)
        output.print_md(f"✅ View NOT on Sheet (Deleting): {v.Name}")

    except Exception as e:
        output.print_md(f"⚠️ Error processing {v.Name}: {e}")

# Stop if no views to delete
if not unused_views:
    forms.alert("No unused views found! All views are either on sheets or are sheets themselves.", exitscript=True)

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
        t = Transaction(doc, "Delete Views Not on Sheets")
        t.Start()

        deleted_count = 0
        for v in unused_views:
            try:
                doc.Delete(v.Id)
                deleted_count += 1
                output.print_md(f"🗑 Deleted: {v.Name}")
            except Exception as e:
                output.print_md(f"⚠️ Could not delete {v.Name}: {e}")

        t.Commit()

        # Show result
        forms.alert(f"Deleted {deleted_count} views that were not on sheets! 🚀")
