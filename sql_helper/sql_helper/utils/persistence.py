# -*- coding: utf-8 -*-
import frappe
import json
from frappe.utils import cint, cstr, now
from frappe import _

# Import the query executor to re-run queries for charts
from .query_executor import execute_orm_query

@frappe.whitelist()
def save_query(query_name: str, natural_language_question: str, generated_orm_json: str):
    """Saves a natural language question and its generated ORM JSON as a Saved Query document."""
    if not frappe.has_role("System Manager"):
        frappe.throw(_("Only System Managers can save queries."), frappe.PermissionError)

    if not query_name or not natural_language_question or not generated_orm_json:
        frappe.throw(_("Query Name, Question, and ORM JSON are required to save."))

    try:
        # Validate JSON before saving
        json.loads(generated_orm_json)

        # Check if query name already exists (optional, depends on desired behavior)
        if frappe.db.exists("Saved Query", query_name):
            # Option 1: Throw error
            # frappe.throw(_("A saved query with the name 	{0}	 already exists.").format(query_name))
            # Option 2: Overwrite (Update existing doc)
            doc = frappe.get_doc("Saved Query", query_name)
            doc.natural_language_question = natural_language_question
            doc.generated_orm_json = generated_orm_json
            doc.modified = now()
            doc.save(ignore_permissions=True) # System Manager saving
            return {"status": "updated", "docname": doc.name}
        else:
            # Create new doc
            doc = frappe.new_doc("Saved Query")
            doc.query_name = query_name
            doc.natural_language_question = natural_language_question
            doc.generated_orm_json = generated_orm_json
            # Owner is set automatically by default=__user on DocType field
            doc.insert(ignore_permissions=True) # System Manager saving
            return {"status": "created", "docname": doc.name}

    except json.JSONDecodeError:
        frappe.throw(_("Invalid JSON format provided for ORM parameters."))
    except Exception as e:
        frappe.log_error(f"Error saving query 	{query_name}	: {e}", "Persistence Error")
        frappe.throw(_("Could not save query: {0}").format(e))

@frappe.whitelist()
def save_chart(chart_name: str, chart_type: str, saved_query_docname: str):
    """Saves chart configuration linked to a Saved Query."""
    if not frappe.has_role("System Manager"):
        frappe.throw(_("Only System Managers can save charts."), frappe.PermissionError)

    if not chart_name or not chart_type or not saved_query_docname:
        frappe.throw(_("Chart Name, Chart Type, and Saved Query are required."))

    if not frappe.db.exists("Saved Query", saved_query_docname):
        frappe.throw(_("Selected Saved Query 	{0}	 does not exist.").format(saved_query_docname))

    try:
        # Check if chart name already exists (optional)
        if frappe.db.exists("Saved Chart", chart_name):
            # Option 1: Throw error
            # frappe.throw(_("A saved chart with the name 	{0}	 already exists.").format(chart_name))
            # Option 2: Overwrite
            doc = frappe.get_doc("Saved Chart", chart_name)
            doc.chart_type = chart_type
            doc.saved_query = saved_query_docname
            doc.modified = now()
            # Ensure owner doesn't change on update if overwriting
            doc.save(ignore_permissions=True) # System Manager saving
            return {"status": "updated", "docname": doc.name}
        else:
            # Create new doc
            doc = frappe.new_doc("Saved Chart")
            doc.chart_name = chart_name
            doc.chart_type = chart_type
            doc.saved_query = saved_query_docname
            # Owner is set automatically by default=__user on DocType field
            doc.insert(ignore_permissions=True) # System Manager saving
            return {"status": "created", "docname": doc.name}

    except Exception as e:
        frappe.log_error(f"Error saving chart 	{chart_name}	: {e}", "Persistence Error")
        frappe.throw(_("Could not save chart: {0}").format(e))

@frappe.whitelist()
def get_saved_queries():
    """Returns a list of Saved Query documents accessible to the user."""
    # System Manager sees all, others might see specific ones if permissions allow
    # For now, restrict to System Manager based on DocType permissions
    if not frappe.has_permission("Saved Query", "read"):
         return [] # Or throw permission error
         
    # Fetching basic info for the dropdown/link field
    queries = frappe.get_all("Saved Query", fields=["name", "query_name", "natural_language_question"], order_by="query_name ASC")
    return queries

@frappe.whitelist()
def get_saved_charts():
    """Returns a list of Saved Chart documents owned by the current user."""
    # The DocType permission already filters by owner (`read_filter`: {"owner": "[user]"})
    # So, a simple get_all respecting permissions should work.
    if not frappe.has_permission("Saved Chart", "read"):
         return [] # Or throw permission error
         
    charts = frappe.get_all("Saved Chart", fields=["name", "chart_name", "chart_type", "saved_query"], order_by="chart_name ASC")
    return charts

@frappe.whitelist()
def get_chart_data(chart_docname: str):
    """Fetches chart details, re-runs the associated query, and returns data for rendering."""
    if not chart_docname:
        frappe.throw(_("Chart document name is required."))

    try:
        # Get the saved chart document, respecting permissions (owner filter)
        chart_doc = frappe.get_doc("Saved Chart", chart_docname)
        
        # Get the linked saved query document
        saved_query_doc = frappe.get_doc("Saved Query", chart_doc.saved_query)
        
        # Re-run the query
        query_result = execute_orm_query(saved_query_doc.generated_orm_json)
        
        if query_result.get("error"):
            # Propagate the error from query execution
            return query_result 

        return {
            "chart_type": chart_doc.chart_type,
            "chart_name": chart_doc.chart_name,
            "query_name": saved_query_doc.query_name,
            "natural_language_question": saved_query_doc.natural_language_question,
            "data": query_result.get("result")
        }

    except frappe.DoesNotExistError:
        frappe.throw(_("Saved Chart or associated Saved Query not found."))
    except frappe.PermissionError:
        frappe.throw(_("You do not have permission to access this chart."))
    except Exception as e:
        frappe.log_error(f"Error fetching chart data for 	{chart_docname}	: {e}", "Persistence Error")
        frappe.throw(_("Could not retrieve chart data: {0}").format(e))

