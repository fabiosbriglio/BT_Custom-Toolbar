# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, View, ViewSheet, ViewType, Transaction
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views, EXCLUDING sheets
views = [
    v for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()
    if not isinstance(v, ViewSheet)  # Ensure we don't process sheets as views
]

# Collect all sheets to check if a view is placed
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
views_on_sheets = set()
for sheet in sheets:
    for v_id in sheet.GetAllPlacedViews():
        views_on_sheets.add(v_id)

# Debugging Output
output = script.get_output()
output.print_md("### 🔍 **Checking Views to Delete**")

# List of views to delete (only views NOT on sheets)
unused_views = []
for v in views:
    try:
        # Skip if it's a view template
        if v.IsTemplate:
            output.print_md(f"⚠️ Skipping View Template: {v.Name}")
            continue

        # Skip views that ARE on sheets
        if v.Id in views_on_sheets:
            output.print_md(f"📌 View on sheet (keeping): {v.Name}")
            continue

        # If a view is NOT on a sheet, mark it for deletion
        unused_views.append(v)
        output.print_md(f"✅ View not on sheet (deleting): {v.Name}")

    except Exception as e:
        output.print_md(f"⚠️ Error processing {v.Name}: {e}")

# Stop if no views to delete
if not unused_views:
    forms.alert("No views found to delete! All views are on sheets or are protected.", exitscript=True)

else:
    # Show a list of views that will be deleted
    view_names = "\n".join([v.Name for v in unused_views])
    confirm = forms.alert(
        title="Confirm Deletion",
        msg="The following {} views will be deleted:\n\n{}\n\nContinue?".format(len(unused_views), view_names),
        ok=True, cancel=True
    )

    if confirm:
        try:
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
            forms.alert(f"Deleted {deleted_count} views that were not on sheets! ✅")

        except Exception as e:
            t.RollBack()
            forms.alert(f"Transaction failed: {e}")
            output.print_md(f"❌ Transaction failed: {e}")
