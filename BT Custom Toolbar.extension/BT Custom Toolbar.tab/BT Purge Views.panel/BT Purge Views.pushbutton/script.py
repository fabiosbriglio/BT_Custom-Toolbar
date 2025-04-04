# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import (
    FilteredElementCollector, View, ViewSchedule, Viewport, Transaction, BuiltInParameter
)
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Function to check if a view is a system browser view
def is_system_view(view):
    """Returns True if the view is a system browser view."""
    try:
        param = view.get_Parameter(BuiltInParameter.VIEW_TYPE)
        if param:
            view_type = param.AsInteger()
            return view_type == 6  # 6 = System Browser View
    except:
        pass
    return False  # Default to False if not found

# Collect all views (excluding templates & system browser views)
all_views = {
    v.Id.IntegerValue: v for v in FilteredElementCollector(doc)
    .OfClass(View)
    .WhereElementIsNotElementType()
    if not v.IsTemplate and not is_system_view(v)  # Exclude system browser views
}

# Collect all schedules separately
all_schedules = {
    s.Id.IntegerValue: s for s in FilteredElementCollector(doc)
    .OfClass(ViewSchedule)
    .WhereElementIsNotElementType()
}

# Collect all viewports (which contain views placed on sheets)
viewports = FilteredElementCollector(doc).OfClass(Viewport).ToElements()

# Dictionaries to store views placed inside viewports and their sheets
views_on_sheets = {}
views_not_on_sheets = all_views.copy()  # Assume all views are NOT on sheets initially
schedules_not_on_sheets = all_schedules.copy()  # Assume all schedules are NOT on sheets initially

for vp in viewports:
    view = doc.GetElement(vp.ViewId)
    if view:
        views_on_sheets[view.Id.IntegerValue] = view
        views_not_on_sheets.pop(view.Id.IntegerValue, None)  # Remove from "not on sheets" since it's placed
        schedules_not_on_sheets.pop(view.Id.IntegerValue, None)  # Remove schedules if placed

# Ask user what to delete
delete_option = forms.SelectFromList.show(
    ["❌ Delete Views (Not on Sheets)", "📊 Delete Schedules (Not on Sheets)"],
    title="Select Deletion Category",
    multiselect=False
)

if not delete_option:
    forms.alert("No category selected. Exiting script.", exitscript=True)

# Select category to delete
if "Views" in delete_option:
    elements_to_delete = views_not_on_sheets
    category_name = "Views"
elif "Schedules" in delete_option:
    elements_to_delete = schedules_not_on_sheets
    category_name = "Schedules"

# Prepare list for user selection
view_options = []
view_name_map = {}  # Map displayed names to actual view objects

for element in elements_to_delete.values():
    display_name = "❌ {} (Not on Sheet)".format(element.Name)
    view_options.append(display_name)
    view_name_map[display_name] = element  # Store actual object

# Stop if no views/schedules found
if not view_options:
    forms.alert("No {} found to delete!".format(category_name), exitscript=True)

# User selection
selected_views = forms.SelectFromList.show(
    view_options,
    title="Select {} to Delete".format(category_name),
    multiselect=True
)

# Stop if user cancels
if not selected_views:
    forms.alert("No {} selected. Exiting script.".format(category_name), exitscript=True)

# Start transaction to delete views/schedules
t = Transaction(doc, "Delete Selected {}".format(category_name))
t.Start()

deleted_count = 0

for view_text in selected_views:
    element_to_delete = view_name_map.get(view_text, None)
    if element_to_delete:
        try:
            doc.Delete(element_to_delete.Id)
            deleted_count += 1
        except Exception as e:
            script.get_output().print_md("⚠️ Could not delete {}: {}".format(view_text, e))

t.Commit()

# Show result message
forms.alert("✅ Deleted {} {} successfully!".format(deleted_count, category_name))
