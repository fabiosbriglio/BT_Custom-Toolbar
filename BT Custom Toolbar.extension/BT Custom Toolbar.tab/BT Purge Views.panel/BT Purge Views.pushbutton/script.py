# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, View, Viewport, Transaction
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all viewports (which contain views placed on sheets)
viewports = FilteredElementCollector(doc).OfClass(Viewport).ToElements()

# Dictionary to store views placed inside viewports and their sheets
views_on_sheets = {}

for vp in viewports:
    view = doc.GetElement(vp.ViewId)
    sheet = doc.GetElement(vp.SheetId)
    
    if view and sheet:
        views_on_sheets[view.Id.IntegerValue] = (view, sheet.Name)

# Debug Output
output = script.get_output()
output.print_md("### 📋 Views Placed in Viewports on Sheets")

# Stop if no views found
if not views_on_sheets:
    forms.alert("No views found inside viewports on sheets!", exitscript=True)

# Convert views into a list for user selection
view_options = ["{} (Sheet: {})".format(view.Name, sheet_name) 
                for _, (view, sheet_name) in views_on_sheets.items()]

# Use pyRevit forms to allow user selection
selected_views = forms.SelectFromList.show(
    view_options,
    title="Select Views to Delete",
    multiselect=True
)

# Stop if user cancels
if not selected_views:
    forms.alert("No views selected. Exiting script.", exitscript=True)

# Start a transaction to delete selected views
t = Transaction(doc, "Delete Selected Views in Viewports")
t.Start()

deleted_count = 0

try:
    for view_text in selected_views:
        # Extract the view name from selected list
        view_name = view_text.split(" (Sheet:")[0]
        
        # Find the view by name
        view_to_delete = next((v for v, _ in views_on_sheets.values() if v.Name == view_name), None)
        
        if view_to_delete:
            doc.Delete(view_to_delete.Id)
            deleted_count += 1
            output.print_md("🗑 Deleted: {}".format(view_to_delete.Name))

    t.Commit()
    forms.alert("✅ Deleted {} views placed in viewports!".format(deleted_count))

except Exception as e:
    t.RollBack()
    forms.alert("❌ Error: {}".format(e))
    output.print_md("❌ Error: {}".format(e))
