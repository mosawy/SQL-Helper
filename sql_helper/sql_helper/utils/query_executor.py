# -*- coding: utf-8 -*-
import frappe
import json
from frappe.utils import cint, cstr, nowdate
from frappe.model.db_query import DatabaseQuery
from frappe.core.doctype.server_script.server_script_utils import get_safe_eval_locals

# Define allowed ORM methods and parameters to prevent misuse
ALLOWED_METHODS = ["frappe.get_all", "frappe.db.get_list", "frappe.db.get_value", "frappe.db.count"]
ALLOWED_KEYS = ["doctype", "filters", "fields", "or_filters", "order_by", "group_by", "limit_page_length", "limit_start", "as_dict", "distinct", "ignore_permissions", "strict"]
# Note: We will force ignore_permissions=False later

# Potentially dangerous keywords/functions to block in filters/fields if not handled carefully
# This is a basic check; more robust validation might be needed depending on security requirements.
BLOCKED_KEYWORDS = ["delete", "update", "insert", "exec", "commit", "rollback", "drop", "truncate", "alter", "import", "subprocess", "os.", "eval(", "compile("]

def is_safe_value(value):
    """Basic check to prevent potentially harmful values in filters or fields."""
    if isinstance(value, str):
        for keyword in BLOCKED_KEYWORDS:
            if keyword in value.lower():
                return False
    # Allow lists/tuples (like filter operators [">", 100]) but check their contents
    if isinstance(value, (list, tuple)):
        for item in value:
            if not is_safe_value(item):
                return False
    # Allow basic types
    return isinstance(value, (str, int, float, bool, list, tuple)) or value is None

def validate_orm_params(params):
    """Validates the structure and content of the ORM parameters received from the AI."""
    if not isinstance(params, dict):
        raise ValueError("ORM parameters must be a dictionary.")
    
    if "doctype" not in params or not isinstance(params["doctype"], str):
        raise ValueError("Missing or invalid 'doctype' in ORM parameters.")

    # Check if doctype exists and user has permission
    if not frappe.db.exists("DocType", params["doctype"]):
        raise ValueError(f"DocType 	{params['doctype']}	 does not exist.")
    if not frappe.has_permission(params["doctype"], "read"):
        raise PermissionError(f"You do not have permission to read DocType: {params['doctype']}")

    for key, value in params.items():
        if key not in ALLOWED_KEYS:
            raise ValueError(f"Disallowed key in ORM parameters: {key}")
        
        # Validate filters
        if key == "filters":
            if not isinstance(value, (dict, list)): # Filters can be dict or list of lists
                raise ValueError("Filters must be a dictionary or a list of lists.")
            if isinstance(value, dict):
                for f_key, f_val in value.items():
                    if not is_safe_value(f_key) or not is_safe_value(f_val):
                        raise ValueError(f"Potentially unsafe value detected in filters: {f_key}={f_val}")
            elif isinstance(value, list):
                 for f_item in value:
                    if not isinstance(f_item, (list, tuple)) or len(f_item) < 2:
                         raise ValueError("List filters must be lists/tuples with at least 2 elements.")
                    for item_part in f_item:
                        if not is_safe_value(item_part):
                            raise ValueError(f"Potentially unsafe value detected in list filter: {f_item}")
                            
        # Validate fields
        if key == "fields":
            if not isinstance(value, list):
                raise ValueError("Fields must be a list.")
            for field in value:
                if not is_safe_value(field):
                    raise ValueError(f"Potentially unsafe value detected in fields: {field}")

    # Force ignore_permissions to False for safety
    params["ignore_permissions"] = False
    # Ensure as_dict is True for consistent output
    params["as_dict"] = True

    return params

@frappe.whitelist()
def execute_orm_query(orm_json_str: str):
    """Executes a Frappe ORM query based on validated JSON parameters."""
    try:
        orm_params = json.loads(orm_json_str)
        validated_params = validate_orm_params(orm_params)
        
        # Use DatabaseQuery for robust permission handling and query building
        db_query = DatabaseQuery(validated_params["doctype"])
        results = db_query.execute(**validated_params)

        # Simple heuristic: if only one aggregate field is requested, return the value directly
        fields = validated_params.get("fields", [])
        if len(results) == 1 and len(fields) == 1 and isinstance(fields[0], str) and ("(" in fields[0] and ")" in fields[0]): # Basic check for aggregate like SUM(qty)
             # Extract the alias or the function call itself if no alias
             field_key = fields[0].split(" AS ")[-1].strip() if " AS " in fields[0].upper() else fields[0]
             # Check if the key exists in the result dictionary
             if field_key in results[0]:
                 return {"result": results[0][field_key], "is_aggregate": True}
             else: # Fallback if alias logic is complex or key doesn't match
                 # Return the first value from the dict
                 first_value = next(iter(results[0].values()), None)
                 return {"result": first_value, "is_aggregate": True}

        return {"result": results, "is_aggregate": False}

    except json.JSONDecodeError as e:
        frappe.log_error(f"Invalid JSON received for query execution: {orm_json_str}", "Query Executor Error")
        return {"error": f"Invalid query format: {e}"}
    except (ValueError, PermissionError) as e:
        frappe.log_error(f"Validation Error: {e}\nQuery: {orm_json_str}", "Query Executor Error")
        return {"error": str(e)}
    except Exception as e:
        frappe.log_error(f"Error executing ORM query: {e}\nQuery: {orm_json_str}", "Query Executor Error")
        # Avoid leaking potentially sensitive database errors to the frontend
        return {"error": f"An error occurred while executing the query. Please check logs or refine your question."}

