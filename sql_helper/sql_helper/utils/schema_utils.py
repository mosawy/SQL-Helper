# -*- coding: utf-8 -*-
import frappe
import json

@frappe.whitelist()
def get_available_doctypes():
    """Returns a list of DocTypes the user can query.
    
    TODO: Implement filtering based on user permissions or a specific setting.
          For now, returns a basic list of common queryable DocTypes.
          Ideally, filter out system/internal DocTypes.
    """
    # This is a placeholder. A more robust implementation would:
    # 1. Get all DocTypes: frappe.get_all("DocType", filters={"issingle": 0, "istable": 0, "module": ["not in", ["Core", "Desk", "Custom", "Workflow"]]}, fields=["name"])
    # 2. Check read permission for each DocType for the current user.
    # 3. Cache the results.
    common_doctypes = [
        "Customer", "Supplier", "Item", "Sales Order", "Sales Invoice", 
        "Purchase Order", "Purchase Invoice", "Lead", "Opportunity", 
        "Quotation", "Project", "Task", "Timesheet", "Stock Entry",
        "Delivery Note", "Purchase Receipt", "Journal Entry", "Payment Entry",
        "Asset", "Employee", "Leave Application"
        # Add more as needed or fetch dynamically
    ]
    # Sort alphabetically for better UX
    common_doctypes.sort()
    return common_doctypes

@frappe.whitelist()
def get_doctype_schema(doctype_name: str):
    """Fetches schema information for a given DocType to provide context to the AI."""
    if not doctype_name:
        frappe.throw("DocType name is required.")

    try:
        meta = frappe.get_meta(doctype_name)
        if not meta.has_permission("read"):
            frappe.throw(f"You do not have permission to read DocType: {doctype_name}")

        schema_info = {
            "doctype": meta.name,
            "fields": [],
            "links": [], # Information about linked doctypes might be useful
            "child_tables": [] # Information about child tables
        }

        for df in meta.fields:
            # Exclude fields that are usually not useful for querying or might confuse the AI
            if df.hidden or df.fieldtype in ["Section Break", "Column Break", "HTML", "Button", "Read Only", "Tab Break", "Image"]:
                continue
            
            field_info = {
                "fieldname": df.fieldname,
                "fieldtype": df.fieldtype,
                "label": df.label,
            }
            if df.options:
                field_info["options"] = df.options # e.g., Link target DocType, Select options
            if df.description:
                field_info["description"] = df.description
                
            schema_info["fields"].append(field_info)

            # Capture Link fields for relationship context
            if df.fieldtype == "Link" and df.options:
                 schema_info["links"].append({"fieldname": df.fieldname, "linked_doctype": df.options})
            
            # Capture Table fields (child tables)
            if df.fieldtype == "Table" and df.options:
                schema_info["child_tables"].append({"fieldname": df.fieldname, "child_doctype": df.options})

        # Convert to JSON string for easy passing
        return json.dumps(schema_info, indent=2)

    except frappe.DoesNotExistError:
        frappe.throw(f"DocType 	{doctype_name}	 not found.")
    except Exception as e:
        frappe.log_error(f"Error fetching schema for {doctype_name}: {e}", "Schema Utils Error")
        frappe.throw(f"Could not retrieve schema for {doctype_name}: {e}")

