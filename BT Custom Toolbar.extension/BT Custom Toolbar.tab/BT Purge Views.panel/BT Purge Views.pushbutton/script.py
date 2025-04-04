# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, View, Viewport, Transaction, ElementId
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views (excluding templates)
all_views = {v.Id.IntegerValue: v for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType() if not v.IsTemplate}

# Collect all viewports (which contain views placed on sheets)
viewports = FilteredElementCollector(doc).OfClass(Viewport).ToElements()

# Dictionary to store views placed inside viewports and their sheets
views_on_sheets = {}
views_not_on_sheets = all_views.copy()  # Assume all views are NOT on sheets initially

for vp in viewports:
    view = doc.GetElement(vp.ViewId)
    sheet = doc.GetElement(vp.SheetId)

    if view and sheet:
        views_on_sheets[view.Id.IntegerValue] = (view, sheet.Name)
        views_not_on_sheets.pop(view.Id.IntegerValue, None)  # Remove from "not on sheets" since it's placed

# Debug Output
output = script.get_output()
output.print_md("### 📋 **Views on Sheets (in Viewports)**")

# Prepare list for user selection
view_options = []
view_name_map = {}  # Map displayed names to actual view objects

# Add views on sheets (in viewports)
for _, (view, sheet_name) in views_on_sheets.items():
    display_name = "{} (📄 Sheet: {})".format(view.Name, sheet_name)
    view_options.append(display_name)
    view_name_map[display_name] = view  # Store actual view object

# Add views NOT on sheets (marked in red)
output.print_md("\n### ❌ **Views NOT in Viewports (not on any sheet)**")
for view in views_not_on_sheets.values():
    display_name = "❌ {} (Not on Sheet)".format(view.Name)
    view_options.append(display_name)
    view_name_map[display_name] = view  # Store actual view object

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
invalid_views = []

try:
    for view_text in selected_views:
        # Get the actual view object from the map
        view_to_delete = view_name_map.get(view_text, None)

        # **CHECK IF VIEW STILL EXISTS BEFORE DELETING**
        if view_to_delete:
            existing_view = doc.GetElement(view_to_delete.Id)
            if existing_view:
                try:
                    doc.Delete(existing_view.Id)
                    deleted_count += 1
                    output.print_md("🗑 Deleted: {}".format(existing_view.Name))
                except Exception as delete_error:
                    invalid_views.append(existing_view.Name)
                    output.print_md("⚠️ Could not delete {}: {}".format(existing_view.Name, delete_error))
            else:
                invalid_views.append(view_to_delete.Name)
                output.print_md("⚠️ View already deleted: {}".format(view_to_delete.Name))

    t.Commit()
    
    # Show result message
    msg = "✅ Deleted {} selected views!".format(deleted_count)
    if invalid_views:
        msg += "\n⚠️ The following views could not be deleted:\n" + "\n".join(invalid_views)
    
    forms.alert(msg)

except Exception as e:
    t.RollBack()
    forms.alert("❌ Error: {}".format(e))
    output.print_md("❌ Error: {}".format(e))
