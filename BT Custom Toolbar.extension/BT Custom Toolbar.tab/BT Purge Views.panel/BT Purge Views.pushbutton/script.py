# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, View, Viewport, Transaction
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views (excluding templates and schedules)
views = [
    v for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()
    if not v.IsTemplate
]

# Collect all viewports (which contain views placed on sheets)
viewports = FilteredElementCollector(doc).OfClass(Viewport).ToElements()
views_on_sheets = {vp.ViewId.IntegerValue for vp in viewports}  # Store view IDs as integers

# Debugging Output
output = script.get_output()
output.print_md("### 🔍 Checking Views NOT Placed in Viewports (to be deleted)")

# List of views to delete (ONLY those that are NOT in any viewport)
views_to_delete = []
for v in views:
    if v.Id.IntegerValue not in views_on_sheets:  # Ensure view is NOT in a viewport
        views_to_delete.append(v)
        output.print_md("🗑 Marking for Deletion: {}".format(v.Name))
    else:
        output.print_md("✅ Keeping: {} (Placed in a Viewport)".format(v.Name))

# Stop if no views to delete
if not views_to_delete:
    forms.alert("No unplaced views found. Nothing to delete.", exitscript=True)

else:
    # Show a list of views that will be deleted
    view_names = "\n".join(["{}".format(v.Name) for v in views_to_delete])
    confirm = forms.alert(
        title="Confirm Deletion",
        msg="The following {} views are NOT placed in a viewport and will be deleted:\n\n{}\n\nContinue?".format(len(views_to_delete), view_names),
        ok=True, cancel=True
    )

    if confirm:
        try:
            # Start a transaction
            t = Transaction(doc, "Delete Views NOT Placed on Sheets")
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
            forms.alert("✅ Deleted {} views NOT placed on sheets!".format(deleted_count))

        except Exception as e:
            t.RollBack()
            forms.alert("❌ Transaction failed: {}".format(e))
            output.print_md("❌ Transaction failed: {}".format(e))
