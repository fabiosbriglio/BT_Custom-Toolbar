# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, View, Viewport, Transaction, ElementId
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views (excluding templates)
all_views = {v.Id.IntegerValue: v for v in FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType() if not v.IsTemplate}

# Collect all viewports (views placed on sheets)
viewports = FilteredElementCollector(doc).OfClass(Viewport).ToElements()

# Dictionary to store views inside viewports
views_on_sheets = set()
for vp in viewports:
    view = doc.GetElement(vp.ViewId)
    if view:
        views_on_sheets.add(view.Id.IntegerValue)  # Track views placed on sheets

# Filter out views **not placed on a sheet**
views_not_on_sheets = {k: v for k, v in all_views.items() if k not in views_on_sheets}

# Prepare selection list
view_options = []
view_name_map = {}

for view in views_not_on_sheets.values():
    display_name = "❌ {} (Not on Sheet)".format(view.Name)
    view_options.append(display_name)
    view_name_map[display_name] = view.Id  # Store actual ElementId

# Stop if no views found
if not view_options:
    forms.alert("No views found to delete!", exitscript=True)

# User selection
selected_views = forms.SelectFromList.show(
    view_options,
    title="Select Views to Delete",
    multiselect=True
)

# Stop if user cancels
if not selected_views:
    forms.alert("No views selected. Exiting script.", exitscript=True)

# Convert selection back to ElementId list
views_to_delete = [view_name_map[v] for v in selected_views]

# Start transaction to delete views
t = Transaction(doc, "Delete Selected Views")
t.Start()

deleted_count = 0

for view_id in views_to_delete:
    try:
        element = doc.GetElement(ElementId(view_id))
        if element:  # Ensure the element is still valid
            doc.Delete(element.Id)
            deleted_count += 1
    except Exception as e:
        script.get_output().print_md(f"⚠️ Could not delete view {view_id}: {e}")

t.Commit()

# Show result message
forms.alert(f"✅ Deleted {deleted_count} views successfully!")
