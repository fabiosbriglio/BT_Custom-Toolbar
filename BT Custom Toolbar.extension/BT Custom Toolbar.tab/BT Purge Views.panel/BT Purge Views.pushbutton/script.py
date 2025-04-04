# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import FilteredElementCollector, View, Viewport, Transaction, BuiltInParameter
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Function to check if a view is a system browser view
def is_system_view(view):
    """Returns True if the view is a system browser view."""
    try:
        view_type = view.get_Parameter(BuiltInParameter.VIEW_TYPE).AsInteger()
        return view_type == 6  # 6 = System Browser View
    except:
        return False

# Collect all views (excluding templates and system browser views)
all_views = {
    v.Id.IntegerValue: v for v in FilteredElementCollector(doc)
    .OfClass(View)
    .WhereElementIsNotElementType()
    if not v.IsTemplate and not is_system_view(v)  # Exclude system views
}

# Collect all viewports (which contain views placed on sheets)
viewports = FilteredElementCollector(doc).OfClass(Viewport).ToElements()

# Dictionary to store views placed inside viewports and their sheets
views_on_sheets = {}
views_not_on_sheets = all_views.copy()  # Assume all views are NOT on sheets initially

for vp in viewports:
    view = doc.GetElement(vp.ViewId)
    if view:
        views_on_sheets[view.Id.IntegerValue] = view
        views_not_on_sheets.pop(view.Id.IntegerValue, None)  # Remove from "not on sheets" since it's placed

# Prepare list for user selection
view_options = []
view_name_map = {}  # Map displayed names to actual view objects

# Add views NOT on sheets (these are the ones we will delete)
for view in views_not_on_sheets.values():
    display_name = "❌ {} (Not on Sheet)".format(view.Name)
    view_options.append(display_name)
    view_name_map[display_name] = view  # Store actual view object

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

# Start transaction to delete views
t = Transaction(doc, "Delete Selected Views")
t.Start()

deleted_count = 0

for view_text in selected_views:
    view_to_delete = view_name_map.get(view_text, None)
    if view_to_delete:
        try:
            doc.Delete(view_to_delete.Id)
            deleted_count += 1
        except Exception as e:
            script.get_output().print_md("⚠️ Could not delete {}: {}".format(view_text, e))

t.Commit()

# Show result message
forms.alert("✅ Deleted {} views successfully!".format(deleted_count))
