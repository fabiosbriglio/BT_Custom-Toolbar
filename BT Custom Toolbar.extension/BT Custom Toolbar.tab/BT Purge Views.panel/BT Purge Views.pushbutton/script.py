# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, View, Viewport, Transaction
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views (excluding templates)
all_views = {v.Id.IntegerValue: v for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType() if not v.IsTemplate}

# Collect all viewports (which contain views placed on sheets)
viewports = FilteredElementCollector(doc).OfClass(Viewport).ToElements()

# Dictionary to store views placed inside viewports and their sheets
views_on_sheets = {}
views_not_on_sheets = all_views.copy()  # Start assuming all views are NOT on sheets

for vp in viewports:
    view = doc.GetElement(vp.ViewId)
    sheet = doc.GetElement(vp.SheetId)
    
    if view and sheet:
        views_on_sheets[view.Id.IntegerValue] = (view, sheet.Name)
        # Remove from "not on sheets" since it's placed
        views_not_on_sheets.pop(view.Id.IntegerValue, None)

# Debug Output
output = script.get_output()
output.print_md("### 📋 **Views on Sheets (in Viewports)**")

# Prepare list for user selection
view_options = []

# Add views on sheets (in viewports)
for _, (view, sheet_name) in views_on_sheets.items():
    view_options.append("{} (📄 Sheet: {})".format(view.Name, sheet_name))

# Add views NOT on sheets (marked in red)
output.print_md("\n### ❌ **Views NOT in Viewports (not on any sheet)**")
for view in views_not_on_sheets.values():
    view_options.append("❌ {} (Not on Sheet)".format(view.Name))

# Stop if no views found
if not view_options:
    forms.alert("No views found!", exitscript=True)

# User selection
selected_views = forms.SelectFromList.show(
    view_options,
    title="Select Views to Delete",
    multiselect=True
)

# Stop if user cancels
if not selected_views:
    forms.alert("No views selected. Exiting script.", exitscript=True)

# Start a transaction to delete selected views
t = Transaction(doc, "Delete Selected Views")
t.Start()

deleted_count = 0

try:
    for view_text in selected_views:
        # Extract view name
        view_name = view_text.split(" (")[0]
        
        # Find the view by name
        view_to_delete = next((v for v in all_views.values() if v.Name == view_name), None)
        
        if view_to_delete:
            doc.Delete(view_to_delete.Id)
            deleted_count += 1
            output.print_md("🗑 Deleted: {}".format(view_to_delete.Name))

    t.Commit()
    forms.alert("✅ Deleted {} selected views!".format(deleted_count))

except Exception as e:
    t.RollBack()
    forms.alert("❌ Error: {}".format(e))
    output.print_md("❌ Error: {}".format(e))
