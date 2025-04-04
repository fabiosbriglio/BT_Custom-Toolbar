# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import (
    FilteredElementCollector, View, ViewSchedule, Viewport, ViewSheet, Transaction, BuiltInParameter
)
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# 🔹 Function to check if a view is a system browser view
def is_system_view(view):
    """Returns True if the view is a system browser view."""
    try:
        param = view.get_Parameter(BuiltInParameter.VIEW_TYPE)
        if param:
            return param.AsInteger() == 6  # 6 = System Browser View
    except:
        pass
    return False

# 🔹 Collect all non-template, non-system views (EXCLUDING schedules)
all_views = {
    v.Id.IntegerValue: v for v in FilteredElementCollector(doc)
    .OfClass(View)
    .WhereElementIsNotElementType()
    if not v.IsTemplate and not is_system_view(v) and not isinstance(v, ViewSchedule)  # ❌ Exclude system views & schedules
}

# 🔹 Collect all schedules separately
all_schedules = {
    s.Id.IntegerValue: s for s in FilteredElementCollector(doc)
    .OfClass(ViewSchedule)
    .WhereElementIsNotElementType()
}

# 🔹 Collect all Viewports (views placed on sheets)
viewports = FilteredElementCollector(doc).OfClass(Viewport).ToElements()

# 🔹 Collect all Sheets and check views placed on them
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
views_on_sheets = set()

# ✅ Check **Viewports** (views explicitly placed inside sheets)
for vp in viewports:
    views_on_sheets.add(vp.ViewId.IntegerValue)

# ✅ Check **ViewSheet** (some views might be directly placed on sheets)
for sheet in sheets:
    for view_id in sheet.GetAllPlacedViews():
        views_on_sheets.add(view_id.IntegerValue)

# ✅ Final filtering: Exclude **ALL views that are on sheets**
views_not_on_sheets = {
    vid: v for vid, v in all_views.items() if vid not in views_on_sheets
}
schedules_not_on_sheets = {
    sid: s for sid, s in all_schedules.items() if sid not in views_on_sheets
}

# 🔹 Ask user what to delete
delete_option = forms.SelectFromList.show(
    ["❌ Delete Views (Not on Sheets)", "📊 Delete Schedules (Not on Sheets)"],
    title="Select Deletion Category",
    multiselect=False
)

if not delete_option:
    forms.alert("No category selected. Exiting script.", exitscript=True)

# 🔹 Select category to delete
if "Views" in delete_option:
    elements_to_delete = views_not_on_sheets
    category_name = "Views"
elif "Schedules" in delete_option:
    elements_to_delete = schedules_not_on_sheets
    category_name = "Schedules"

# 🔹 Prepare list for user selection
view_options = []
view_name_map = {}  # Map displayed names to actual view objects

for element in elements_to_delete.values():
    display_name = "❌ {} (Not on Sheet)".format(element.Name)
    view_options.append(display_name)
    view_name_map[display_name] = element  # Store actual object

# 🔹 Stop if no views/schedules found
if not view_options:
    forms.alert("No {} found to delete!".format(category_name), exitscript=True)

# 🔹 User selection
selected_views = forms.SelectFromList.show(
    view_options,
    title="Select {} to Delete".format(category_name),
    multiselect=True
)

# 🔹 Stop if user cancels
if not selected_views:
    forms.alert("No {} selected. Exiting script.".format(category_name), exitscript=True)

# 🔹 Start transaction to delete views/schedules
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

# 🔹 Show result message
forms.alert("✅ Deleted {} {} successfully!".format(deleted_count, category_name))
