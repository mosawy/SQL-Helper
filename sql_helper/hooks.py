# -*- coding: utf-8 -*-
from ._version import __version__

app_name = "sql_helper"
app_title = "SQL Helper"
app_publisher = "Manus (AI Agent)"
app_description = "AI Assistant to query ERPNext data using natural language (powered by Google Gemini)"
app_email = "noreply@example.com"
app_license = "MIT"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/sql_helper/css/sql_helper.css"
# app_include_js = "/assets/sql_helper/js/sql_helper.js"

# include js, css files in header of web template
# web_include_css = "/assets/sql_helper/css/sql_helper.css"
# web_include_js = "/assets/sql_helper/js/sql_helper.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sql_helper/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "AI Assistant Interface" : "public/js/ai_assistant_interface.js"
}
doctype_list_js = {}
doctype_tree_js = {}
doctype_calendar_js = {}

# Svg Icons
# -----------
# app_include_icons = "sql_helper/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# -----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "sql_helper.utils.jinja_methods",
#	"filters": "sql_helper.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "sql_helper.install.before_install"
# after_install = "sql_helper.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "sql_helper.uninstall.before_uninstall"
# after_uninstall = "sql_helper.uninstall.after_uninstall"

# Integration Setup
# -------------------
# requirements = ["google-generativeai"]

# Permissions
# -----------=
# Permissions evaluated in scripted ways
# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------=
# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------=
# Hook on document methods and events
# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------=

# scheduler_events = {
#	"all": [
#		"sql_helper.tasks.all"
#	],
#	"daily": [
#		"sql_helper.tasks.daily"
#	],
#	"hourly": [
#		"sql_helper.tasks.hourly"
#	],
#	"weekly": [
#		"sql_helper.tasks.weekly"
#	],
#	"monthly": [
#		"sql_helper.tasks.monthly"
#	],
# }

# Testing
# -------=

# before_tests = "sql_helper.install.before_tests"

# Overriding Methods
# ------------------=
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "sql_helper.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "sql_helper.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
# cancel_linked_documents_on_cancel = []

# Request Events
# ----------------
# before_request = []
# after_request = []

# Job Events
# ----------
# before_job = []
# after_job = []

# User Data Protection
# --------------------=

# user_data_fields = [
#	{
#		"doctype": "{doctype_name}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_name}",
#		"filter_by": "{filter_by}",
#		"delete": 1,
#	},
#	{
#		"doctype": "{doctype_name}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_name}",
#		"filter_by": "{filter_by}",
#		"delete": 1,
#	},
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"sql_helper.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
#	"Logging DocType Name": 30  # days to retain logs
# }


# Whitelisted methods accessible from client-side scripts
# Make sure the paths are correct
fixtures = ["Custom Field"] # Add Gemini Settings if needed as fixture


# Add whitelisted methods here
# Ensure the paths point to the actual functions
whitelisted_methods = [
    "sql_helper.sql_helper.utils.gemini_api.generate_orm_query",
    "sql_helper.sql_helper.utils.schema_utils.get_available_doctypes",
    "sql_helper.sql_helper.utils.schema_utils.get_doctype_schema",
    "sql_helper.sql_helper.utils.query_executor.execute_orm_query",
    "sql_helper.sql_helper.utils.persistence.save_query",
    "sql_helper.sql_helper.utils.persistence.save_chart",
    "sql_helper.sql_helper.utils.persistence.get_saved_queries",
    "sql_helper.sql_helper.utils.persistence.get_saved_charts",
    "sql_helper.sql_helper.utils.persistence.get_chart_data"
]

