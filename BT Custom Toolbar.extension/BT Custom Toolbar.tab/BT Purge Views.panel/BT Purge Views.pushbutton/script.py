from Autodesk.Revit.DB import FilteredElementCollector, View, ViewSheet, ViewType
from pyrevit import script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views
views = FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()

# Collect all sheets to check if a view is placed
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
views_on_sheets = set()
for sheet in sheets:
    for v_id in sheet.GetAllPlacedViews():
        views_on_sheets.add(v_id)

# Protected view types that should NOT be deleted
protected_view_types = [
    ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.ThreeD, ViewType.EngineeringPlan,
    ViewType.Section, ViewType.Elevation, ViewType.Detail, ViewType.DraftingView, ViewType.Schedule
]

# Debugging Output
output = script.get_output()
output.print_md("### 🔍 **Debugging: Listing All Views & Their Status**")

for v in views:
    reason = []
    if v.IsTemplate:
        reason.append("Template View")
    if v.ViewType in protected_view_types:
        reason.append("Protected View Type ({})".format(v.ViewType))
    if v.GetPrimaryViewId().IntegerValue != -1:
        reason.append("Dependent View")
    if v.Id in views_on_sheets:
        reason.append("Placed on a Sheet")

    output.print_md("- **{}** → _{}_\n".format(v.Name, ", ".join(reason) if reason else "Possible for deletion"))
