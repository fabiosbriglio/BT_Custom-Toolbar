# Import Revit API modules
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, ViewSheet, Viewport, XYZ, Transaction
)

# Import pyRevit tools
from pyrevit import revit, script

# Get the active Revit document
doc = revit.doc

# Start a transaction
t = Transaction(doc, "Center Views on Sheets")
t.Start()

# Get all sheets in the project
sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()

# Loop through each sheet
for sheet in sheets:
    # Get all viewports (views placed on the sheet)
    viewports = FilteredElementCollector(doc).OfClass(Viewport).WhereElementIsNotElementType().ToElements()

    for viewport in viewports:
        # Check if the viewport belongs to the current sheet
        if viewport.SheetId == sheet.Id:
            # Get the bounding box of the sheet (title block)
            sheet_bbox = sheet.Outline
            if not sheet_bbox:
                print("⚠️ Sheet {} has no valid outline.".format(sheet.Name))
                continue

            # Calculate the center of the sheet
            sheet_center = (sheet_bbox.Min + sheet_bbox.Max) * 0.5

            # Get the current center of the viewport
            vp_center = viewport.GetBoxCenter()

            # Calculate the vector needed to move the viewport to the center
            move_vector = XYZ(sheet_center.X - vp_center.X, sheet_center.Y - vp_center.Y, 0)

            # Move the viewport
            viewport.Location.Move(move_vector)

# Commit transaction
t.Commit()

print("✅ All views centered on sheets successfully!")
