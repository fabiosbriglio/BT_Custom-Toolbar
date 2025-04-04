# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, View, ViewSheet, Transaction
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views, EXCLUDING templates
views = [
    v for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()
    if not v.IsTemplate
]

# Collect all sheets and get views placed on them
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
views_on_sheets = set()
for sheet in sheets:
    for v_id in sheet.GetAllPlacedViews():  # Get view IDs placed on the sheet
        views_on_sheets.add(v_id.IntegerValue)  # Store as integer for comparison

# Debugging Output
output = script.get_output()
output.print_md("### 🔍 Checking Views Not Placed on Sheets (to be deleted)")

# List of views to delete (ONLY those NOT placed on sheets)
views_to_delete = []
for v in views:
    try:
        # Only delete views that are NOT placed on a sheet
        if v.Id.IntegerValue not in views_on_sheets:
            views_to_delete.append(v)
            output.print_md("🗑 Marking for Deletion: {} (Not on Sheet)".format(v.Name))
        else:
            output.print_md("✅ Keeping: {} (Placed on Sheet)".format(v.Name))

    except Exception as e:
        output.print_md("⚠️ Error processing {}: {}".format(v.Name, e))

# Stop if no views to delete
if not views_to_delete:
    forms.alert("No views found that are NOT placed on sheets. Nothing to delete.", exitscript=True)

else:
    # Show a list of views that will be deleted
    view_names = "\n".join([v.Name for v in views_to_delete])
    confirm = forms.alert(
        title="Confirm Deletion",
        msg="The following {} views are NOT placed on sheets and will be deleted:\n\n{}\n\nContinue?".format(len(views_to_delete), view_names),
        ok=True, cancel=True
    )

    if confirm:
        try:
            # Start a transaction
            t = Transaction(doc, "Delete Views Not Placed on Sheets")
            t.Start()

            deleted_count = 0
            for v in views_to_delete:
                try:
                    if doc.GetElement(v.Id):  # Ensure the view still exists before deleting
                        doc.Delete(v.Id)
                        deleted_count += 1
                        output.print_md("🗑 Deleted: {}".format(v.Name))
                    else:
                        output.print_md("⚠️ Skipping: {} (Already Deleted)".format(v.Name))

                except Exception as e:
                    output.print_md("❌ Could not delete {}: {}".format(v.Name, e))

            t.Commit()

            # Show result
            forms.alert("✅ Deleted {} views that were NOT placed on sheets!".format(deleted_count))

        except Exception as e:
            t.RollBack()
            forms.alert("❌ Transaction failed: {}".format(e))
            output
