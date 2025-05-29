# SQL Helper - ERPNext AI Assistant

This Frappe app provides an AI-powered assistant to query your ERPNext data using natural language.

## Features (Implemented based on prompt)

*   **Natural Language Querying:** Ask questions like "Show me customers from Germany" or "What was the total sales last month?".
*   **AI-Powered Translation:** Uses the Google Gemini API to convert your questions into safe Frappe ORM queries (no raw SQL).
*   **DocType Selection:** Choose the specific DocType you want to query.
*   **Document Context:** Optionally provide a specific document name (e.g., "INV-001") for context.
*   **Results Display:** View query results in a clear table.
*   **CSV Export:** Export results to a CSV file.
*   **Chart Visualization:** Visualize results using Bar, Pie, or Line charts (powered by Chart.js).
*   **Save & Load:**
    *   Save frequently used queries.
    *   Save chart configurations.
    *   Load saved queries and charts (charts automatically refresh data).
    *   Saved items are user-specific (except for System Managers who can manage all).
*   **Admin Settings:**
    *   Configure Google Gemini API Key and model.
    *   Enable/disable the assistant.
    *   Enable debug mode for logging.
*   **Security:**
    *   Uses safe Frappe ORM methods (`get_all`, `db.get_list`, `qb`).
    *   Respects user permissions.
    *   Uses whitelisted methods for backend calls.

## Setup

1.  **Install App:**
    ```bash
    bench get-app https://github.com/mosawy/SQL-Helper.git
    bench --site [your-site-name] install-app sql_helper
    ```
2.  **Install Dependencies:**
    ```bash
    # Ensure google-generativeai is installed in your bench environment
    # bench pip install google-generativeai
    ```
3.  **Configure Settings:**
    *   Go to Desk -> SQL Helper -> Gemini Settings.
    *   Enable the assistant.
    *   Enter your Google Gemini API Key.
    *   Save the settings.
4.  **Usage:**
    *   Go to Desk -> SQL Helper -> AI Assistant Interface.
    *   Select a DocType, ask your question, and click "Run Query".

## Development Notes

*   This app was developed by the Manus AI Agent based on a detailed prompt.
*   Requires Chart.js library. Ensure it is included in your Frappe build process if not already available (`bench build` might handle this if properly configured, or add manually).
*   Permissions for saving queries/charts are currently restricted to System Manager. Modify `persistence.py` and DocType permissions if needed.
*   The list of queryable DocTypes in `schema_utils.py` is currently hardcoded; a dynamic, permission-aware list is recommended for production.

## License

MIT

