# -*- coding: utf-8 -*-
from Autodesk.Revit.DB import (
    FilteredElementCollector, Transaction, ElementId, Wall, Floor, Ceiling, RoofType, 
    FamilyInstance, StructuralFraming, StructuralColumn, Pipe, Duct, ElectricalEquipment, 
    MechanicalEquipment, PlumbingFixture, LightingFixture, Furniture, GenericForm
)
from Autodesk.Revit.DB.Architecture import Room  # Correct import for Rooms
from pyrevit import forms, script

# Get active Revit document
doc = __revit__.ActiveUIDocument.Document

# Element types to choose from
element_types = [
    "Walls",
    "Floors",
    "Ceilings",
    "Roofs",
    "Doors",
    "Windows",
    "Columns",
    "Beams",
    "Pipes",
    "Ducts",
    "Electrical Equipment",
    "Mechanical Equipment",
    "Plumbing Fixtures",
    "Lighting Fixtures",
    "Furniture",
    "Rooms",
    "Generic Models"
]

# User selects an element type
selected_type = forms.ask_for_one_item(element_types, title="Select Element Type")

if not selected_type:
    forms.alert("No element type selected. Exiting script.", exitscript=True)

# Map selection to Revit classes
type_map = {
    "Walls": Wall,
    "Floors": Floor,
    "Ceilings": Ceiling,
    "Roofs": RoofType,
    "Doors": FamilyInstance,
    "Windows": FamilyInstance,
    "Columns": StructuralColumn,
    "Beams": StructuralFraming,
    "Pipes": Pipe,
    "Ducts": Duct,
    "Electrical Equipment": ElectricalEquipment,
    "Mechanical Equipment": MechanicalEquipment,
    "Plumbing Fixtures": PlumbingFixture,
    "Lighting Fixtures": LightingFixture,
    "Furniture": Furniture,
    "Rooms": Room,
    "Generic Models": FamilyInstance  # Generic Models are typically FamilyInstances
}

selected_class = type_map.get(selected_type, None)

if not selected_class:
    forms.alert("Invalid selection. Exiting script.", exitscript=True)

# Collect elements of the selected type
elements = FilteredElementCollector(doc).OfClass(selected_class).WhereElementIsNotElementType().ToElements()

if not elements:
    forms.alert("No {} found in the project.".format(selected_type.lower()), exitscript=True)

# Extract element IDs
element_data = [{"Element Name": el.Name, "Current ID": el.Id.IntegerValue, "New ID": ""} for el in elements]

# Display editable table
updated_data = forms.edit_table(element_data, title="Edit Element IDs", columns=["Element Name", "Current ID", "New ID"])

if not updated_data:
    forms.alert("No changes made. Exiting script.", exitscript=True)

# Start transaction to apply new IDs
t = Transaction(doc, "Update Element IDs")
t.Start()

try:
    for row in updated_data:
        element_id = int(row["Current ID"])
        new_id = row["New ID"].strip()
        
        if new_id and new_id.isdigit():
            element = doc.GetElement(ElementId(element_id))
            if element:
                param = element.LookupParameter("Mark")  # Most elements use "Mark"
                if selected_type == "Rooms":
                    param = element.LookupParameter("Number")  # Rooms use "Number"

                if param and not param.IsReadOnly:
                    param.Set(new_id)

    t.Commit()
    forms.alert("✅ Element IDs updated successfully!")
except Exception as e:
    t.RollBack()
    forms.alert("⚠️ Error updating elements: {}".format(str(e)))
