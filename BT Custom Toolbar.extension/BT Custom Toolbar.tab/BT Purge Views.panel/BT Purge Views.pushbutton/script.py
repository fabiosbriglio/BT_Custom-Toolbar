# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, View, Transaction, BuiltInParameter
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views, EXCLUDING templates
views = [
    v for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()
    if not v.IsTemplate
]

# Debugging Output
output = script.get_output()
output.print_md("### 🔍 Checking Views with 'Detail Number' > 0 (to be deleted)")

# List of views to delete (ONLY those where Detail Number > 0)
views_to_delete = []
for v in views:
    try:
        # Get the Detail Number parameter
        detail_number_param = v.get_Parameter(BuiltInParameter.VIEW_DETAIL_NUMBER)
        
        if detail_number_param:
            detail_number = detail_number_param.AsString()  # Get value as string
            
            # Check if it's a number and greater than 0
            if detail_number and detail_number.isdigit() and int(detail_number) > 0:
                views_to_delete.append(v)
                output.print_md("🗑 Marking for Deletion: {} (Detail Number: {})".format(v.Name, detail_number))
            else:
                output.print_md("✅ Keeping: {} (Detail Number: {})".format(v.Name, detail_number))
        
        else:
            output.print_md("⚠️ Skipping {} (No Detail Number Parameter)".format(v.Name))

    except Exception as e:
        output.print_md("⚠️ Error processing {}: {}".format(v.Name, e))

# Stop if no views to delete
if not views_to_delete:
    forms.alert("No views found with 'Detail Number' > 0. Nothing to delete.", exitscript=True)

else:
    # Show a list of views that will be deleted
    view_names = "\n".join(["{} (Detail Number: {})".format(v.Name, v.get_Parameter(BuiltInParameter.VIEW_DETAIL_NUMBER).AsString()) for v in views_to_delete])
    confirm = forms.alert(
        title="Confirm Deletion",
        msg="The following {} views have 'Detail Number' > 0 and will be deleted:\n\n{}\n\nContinue?".format(len(views_to_delete), view_names),
        ok=True, cancel=True
    )

    if confirm:
        try:
            # Start a transaction
            t = Transaction(doc, "Delete Views with Detail Number > 0")
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
            forms.alert("✅ Deleted {} views with 'Detail Number' > 0!".format(deleted_count))

        except Exception as e:
            t.RollBack()
            forms.alert("❌ Transaction failed: {}".format(e))
            output.print_md("❌ Transaction failed: {}".format(e))
