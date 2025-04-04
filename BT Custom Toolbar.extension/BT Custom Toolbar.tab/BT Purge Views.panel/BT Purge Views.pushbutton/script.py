# -*- coding: utf-8 -*-

from Autodesk.Revit.DB import FilteredElementCollector, View, ViewSheet, ViewType, Transaction
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views, EXCLUDING sheets
views = FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()

# Collect all sheets to check if a view is placed
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
views_on_sheets = set()
for sheet in sheets:
    for v_id in sheet.GetAllPlacedViews():
        views_on_sheets.add(v_id)

# Debugging Output
output = script.get_output()
output.print_md("### Checking Views, Legends, and Schedules to Delete")

# View types to be deleted if NOT on a sheet
deletable_view_types = {
    ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.ThreeD, ViewType.EngineeringPlan,
    ViewType.Section, ViewType.Elevation, ViewType.Detail, ViewType.DraftingView, 
    ViewType.Schedule, ViewType.Legend
}

# List of views, legends, and schedules to delete
unused_elements = []
for v in views:
    try:
        # Skip if it's a SHEET
        if v.ViewType == ViewType.DrawingSheet:
            output.print_md("Keeping Sheet: {}".format(v.Name))
            continue

        # Skip views that ARE placed on sheets
        if v.Id in views_on_sheets:
            output.print_md("Keeping View on Sheet: {}".format(v.Name))
            continue

        # Only delete specific view types (no templates, no system views)
        if v.ViewType in deletable_view_types and not v.IsTemplate:
            unused_elements.append(v)
            output.print_md("Marking for Deletion: {} ({})".format(v.Name, v.ViewType))

    except Exception as e:
        output.print_md("Error processing {}: {}".format(v.Name, e))

# Stop if nothing to delete
if not unused_elements:
    forms.alert("No unused views, legends, or schedules found!", exitscript=True)

else:
    # Show a list of views, legends, and schedules that will be deleted
    element_names = "\n".join([v.Name for v in unused_elements])
    confirm = forms.alert(
        title="Confirm Deletion",
        msg="The following {} elements will be deleted:\n\n{}\n\nContinue?".format(len(unused_elements), element_names),
        ok=True, cancel=True
    )

    if confirm:
        try:
            # Start a transaction
            t = Transaction(doc, "Purge Unused Views, Legends, and Schedules")
            t.Start()

            deleted_count = 0
            for v in unused_elements:
                try:
                    doc.Delete(v.Id)
                    deleted_count += 1
                    output.print_md("Deleted: {} ({})".format(v.Name, v.ViewType))
                except Exception as e:
                    output.print_md("Could not delete {}: {}".format(v.Name, e))

            t.Commit()
            forms.alert("Deleted {} unused views, legends, and schedules!".format(deleted_count))

        except Exception as e:
            t.RollBack()
            output.print_md("Transaction failed: {}".format(e))
            forms.alert("Error: {}\nCheck output for details.".format(e))
