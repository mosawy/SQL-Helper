# -*- coding: utf-8 -*-
import frappe
import google.generativeai as genai
import json
from frappe.utils import cint, cstr

# Cache for Gemini settings to avoid repeated DB calls
GEMINI_SETTINGS_CACHE = None

def get_gemini_settings(use_cache=True):
    """Fetches Gemini Settings singleton DocType and caches it."""
    global GEMINI_SETTINGS_CACHE
    if use_cache and GEMINI_SETTINGS_CACHE:
        return GEMINI_SETTINGS_CACHE

    try:
        settings = frappe.get_single("Gemini Settings")
        if not settings.is_enabled:
            frappe.throw("SQL Helper AI Assistant is disabled in settings.")
        if not settings.api_key:
            frappe.throw("Gemini API Key is not configured in SQL Helper settings.")
        
        GEMINI_SETTINGS_CACHE = settings
        return settings
    except frappe.DoesNotExistError:
        frappe.throw("Gemini Settings not found. Please configure them via Desk.")
    except Exception as e:
        frappe.log_error(f"Error fetching Gemini Settings: {e}", "Gemini API Error")
        frappe.throw(f"Error accessing Gemini settings: {e}")

@frappe.whitelist()
def generate_orm_query(question: str, doctype_schema: str, document_name: str = None):
    """Generates Frappe ORM query parameters using Google Gemini API."""
    settings = get_gemini_settings()
    
    if not settings.is_enabled:
        return {"error": "AI Assistant is disabled."}

    try:
        genai.configure(api_key=settings.api_key)
        model = genai.GenerativeModel(settings.model_name or "gemini-1.5-flash-latest")

        # Construct the prompt for Gemini
        prompt = f"""You are an expert in Frappe Framework and ERPNext. Your task is to convert a natural language question about ERPNext data into a structured JSON object that can be used with Frappe ORM methods like frappe.get_all(), frappe.db.get_list(), or frappe.qb. 

Strictly adhere to the following JSON output format:
{{
  "doctype": "<Target DocType>",
  "filters": {{ "field1": "value1", "field2": ["operator", "value2"] }},
  "fields": ["field1", "field2", "SUM(field3) AS alias"],
  "joins": [
    {{
      "table": "<Join Table (e.g., tabChildTable)>",
      "on": "<SQL ON condition (e.g., tabParent.name = tabChild.parent)>"
    }}
  ],
  "group_by": "field1",
  "order_by": "field2 DESC",
  "limit_page_length": 100
}}

- Only include keys in the JSON if they are needed for the query. For simple queries, you might only need "doctype", "filters", and "fields".
- Use standard Frappe filter syntax (e.g., [">", 1000], ["like", "%value%"]).
- Use standard field names from the provided schema.
- If joins are needed, specify the full table name (e.g., `tabSales Invoice Item`) and the ON condition.
- Ensure the generated JSON is valid.
- Do NOT generate raw SQL queries.

Context:
Target DocType Schema:
```json
{doctype_schema}
```

{f'Specific Document Name context (if provided): {document_name}' if document_name else ''}

User Question: "{question}"

Generate the ORM JSON:
"""

        if settings.debug_mode:
            frappe.log_error(f"Gemini Prompt:\n{prompt}", "SQL Helper Debug")

        response = model.generate_content(prompt)
        
        if settings.debug_mode:
            frappe.log_error(f"Gemini Response:\n{response.text}", "SQL Helper Debug")

        # Clean the response - Gemini might wrap it in ```json ... ```
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()

        # Validate and parse the JSON
        try:
            orm_json = json.loads(cleaned_response)
            # Basic validation
            if not isinstance(orm_json, dict) or "doctype" not in orm_json:
                raise ValueError("Invalid JSON structure received from AI.")
            return {"orm_json": orm_json}
        except json.JSONDecodeError as e:
            frappe.log_error(f"Failed to parse Gemini JSON response: {e}\nResponse: {cleaned_response}", "Gemini API Error")
            return {"error": f"AI returned invalid JSON format: {e}"}
        except ValueError as e:
            frappe.log_error(f"Invalid JSON structure from AI: {e}\nResponse: {cleaned_response}", "Gemini API Error")
            return {"error": str(e)}

    except Exception as e:
        frappe.log_error(f"Error calling Gemini API: {e}", "Gemini API Error")
        return {"error": f"Failed to generate query via AI: {e}"}

# Add other utility functions as needed

