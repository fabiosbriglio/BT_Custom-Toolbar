from Autodesk.Revit.DB import FilteredElementCollector, View, ViewSheet, ViewType, Transaction
from pyrevit import forms, script

# Get the active Revit document
doc = __revit__.ActiveUIDocument.Document

# Collect all views in the project (excluding system views)
views = FilteredElementCollector(doc).OfClass(View).WhereElementIsNotElementType().ToElements()

# Collect all sheets to check if a view is placed
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
views_on_sheets = set()
for sheet in sheets:
    for v_id in sheet.GetAllPlacedViews():
        views_on_sheets.add(v_id)

# Define protected view types (to avoid deleting essential views)
protected_view_types = {
    ViewType.FloorPlan, ViewType.CeilingPlan, ViewType.ThreeD, ViewType.EngineeringPlan,
    ViewType.Section, ViewType.Elevation, ViewType.Detail, ViewType.DraftingView, ViewType.Schedule
}

# List of known system views that should NOT be deleted
system_view_names = ["Vista di progetto", "Browser di sistema"]

# Debugging Output
output = script.get_output()
output.print_md("### 🔍 **Checking Views to Delete**")

# Detect unused views correctly
unused_views = []
for v in views:
    try:
        # Skip system views by name
        if v.Name in system_view_names:
            output.print_md(f"🚫 Skipping system view: {v.Name}")
            continue

        # Skip templates
        if v.IsTemplate:
            output.print_md(f"⚠️ Skipping template view: {v.Name}")
            continue

        # Skip protected view types
        if v.ViewType in protected_view_types:
            output.print_md(f"🔒 Protected view type: {v.Name} ({v.ViewType})")
            continue

        # Skip dependent views
        if v.GetPrimaryViewId().IntegerValue != -1:
            output.print_md(f"🔗 Skipping dependent view: {v.Name}")
            continue

        # Skip views placed on a sheet
        if v.Id in views_on_sheets:
            output.print_md(f"📌 Skipping view placed on sheet: {v.Name}")
            continue

        # If a view passes all checks, add it to deletion list
        unused_views.append(v)
        output.print_md(f"✅ Marking for deletion: {v.Name}")

    except Exception as e:
        output.print_md(f"⚠️ Error processing {v.Name}: {e}")

# Stop if no views to delete
if not unused_views:
    forms.alert("No unused views found! Check if your duplicate views are still linked to something.", exitscript=True)

else:
    # Show a list of views that will be deleted
    view_names = "\n".join([v.Name for v in unused_views])
    confirm = forms.alert(
        title="Confirm Deletion",
        msg="The following {} views will be deleted:\n\n{}\n\nContinue?".format(len(unused_views), view_names),
        ok=True, cancel=True
    )

    if confirm:
        # Start a transaction
        t = Transaction(doc, "Purge Unused Views")
        t.Start()

        deleted_count = 0
        for v in unused_views:
            try:
                doc.Delete(v.Id)
                deleted_count += 1
                output.print_md(f"🗑 Deleted: {v.Name}")
            except Exception as e:
                output.print_md(f"⚠️ Could not delete {v.Name}: {e}")

        t.Commit()

        # Show result
        forms.alert(f"Deleted {deleted_count} unused views successfully! 🚀")
