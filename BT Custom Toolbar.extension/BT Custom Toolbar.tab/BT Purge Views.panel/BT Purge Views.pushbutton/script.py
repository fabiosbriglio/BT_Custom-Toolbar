# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, View, ViewSheet, Transaction, BuiltInParameter
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views, EXCLUDING sheets and templates
views = [
    v for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()
    if not isinstance(v, ViewSheet) and not v.IsTemplate
]

# Debugging Output
output = script.get_output()
output.print_md("### Checking Views Without Detail Numbers")

# List of views to delete (only views WITHOUT a Detail Number)
views_to_delete = []
for v in views:
    try:
        # Get the "Detail Number" parameter
        detail_param = v.get_Parameter(BuiltInParameter.VIEW_DETAIL_NUMBER)
        detail_number = detail_param.AsString() if detail_param else None

        # If the detail number is missing or empty, mark for deletion
        if not detail_number or detail_number.strip() == "":
            views_to_delete.append(v)
            output.print_md("Marking for Deletion: {}".format(v.Name))

        else:
            output.print_md("Keeping: {} (Detail Number: {})".format(v.Name, detail_number))

    except Exception as e:
        output.print_md("Error processing {}: {}".format(v.Name, e))

# Stop if no views to delete
if not views_to_delete:
    forms.alert("No views found without a Detail Number. Nothing to delete!", exitscript=True)

else:
    # Show a list of views that will be deleted
    view_names = "\n".join([v.Name for v in views_to_delete])
    confirm = forms.alert(
        title="Confirm Deletion",
        msg="The following {} views will be deleted:\n\n{}\n\nContinue?".format(len(views_to_delete), view_names),
        ok=True, cancel=True
    )

    if confirm:
        try:
            # Start a transaction
            t = Transaction(doc, "Delete Views Without Detail Numbers")
            t.Start()

            deleted_count = 0
            for v in views_to_delete:
                try:
                    doc.Delete(v.Id)
                    deleted_count += 1
                    output.print_md("Deleted: {}".format(v.Name))

                except Exception as e:
                    output.print_md("Could not delete {}: {}".format(v.Name, e))

            t.Commit()

            # Show result
            forms.alert("Deleted {} views that had no Detail Number!".format(deleted_count))

        except Exception as e:
            t.RollBack()
            forms.alert("Transaction failed: {}".format(e))
            output.print_md("Transaction failed: {}".format(e))
