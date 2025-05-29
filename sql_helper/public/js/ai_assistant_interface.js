// Frappe Client Script for AI Assistant Interface DocType

frappe.ui.form.on("AI Assistant Interface", {
    refresh: function(frm) {
        // Clear results on refresh
        frm.set_value("results_html", "");
        frm.set_value("chart_html", "");
        frm.set_df_property("save_query_button", "hidden", 1);
        frm.set_df_property("save_chart_button", "hidden", 1);

        // Add custom buttons if they don't exist (Frappe might remove them on refresh)
        // We will trigger actions from the fields defined as Button type instead.
    },

    onload: function(frm) {
        // Fetch available doctypes and populate the select field
        frappe.call({
            method: "sql_helper.sql_helper.utils.schema_utils.get_available_doctypes",
            callback: function(r) {
                if (r.message) {
                    frm.set_df_property("doctype_select", "options", [""].concat(r.message));
                    frm.refresh_field("doctype_select");
                } else {
                    frappe.msgprint(__("Could not load available DocTypes."));
                }
            }
        });

        // Setup Chart.js (ensure library is loaded - might need to add to build.json or include manually)
        // Placeholder for chart instance
        frm.chart_instance = null;
    },

    // --- Button Handlers ---

    run_query_button: function(frm) {
        frm.set_value("results_html", "<p><i>Processing query...</i></p>");
        frm.set_value("chart_html", "");
        frm.refresh_fields(); // Show processing message
        frm.set_df_property("save_query_button", "hidden", 1);
        frm.set_df_property("save_chart_button", "hidden", 1);
        if (frm.chart_instance) {
            frm.chart_instance.destroy();
            frm.chart_instance = null;
        }

        const doctype = frm.doc.doctype_select;
        const question = frm.doc.question;
        const doc_name = frm.doc.document_name;

        if (!doctype || !question) {
            frappe.msgprint(__("Please select a DocType and enter your question."));
            frm.set_value("results_html", "");
            return;
        }

        // 1. Get Schema
        frappe.call({
            method: "sql_helper.sql_helper.utils.schema_utils.get_doctype_schema",
            args: {
                doctype_name: doctype
            },
            callback: function(r_schema) {
                if (r_schema.exc) {
                    frappe.msgprint(__("Error fetching schema: {0}").format(r_schema.exc));
                    frm.set_value("results_html", `<p class="text-danger">Error fetching schema: ${r_schema.exc}</p>`);
                    return;
                }
                if (!r_schema.message) {
                     frappe.msgprint(__("Could not fetch schema for {0}").format(doctype));
                     frm.set_value("results_html", `<p class="text-danger">Could not fetch schema for ${doctype}</p>`);
                     return;
                }
                const schema_json = r_schema.message;

                // 2. Generate ORM Query using Gemini
                frappe.call({
                    method: "sql_helper.sql_helper.utils.gemini_api.generate_orm_query",
                    args: {
                        question: question,
                        doctype_schema: schema_json,
                        document_name: doc_name
                    },
                    callback: function(r_gen) {
                        if (r_gen.exc) {
                            frappe.msgprint(__("Error generating query: {0}").format(r_gen.exc));
                            frm.set_value("results_html", `<p class="text-danger">Error generating query: ${r_gen.exc}</p>`);
                            return;
                        }
                        if (r_gen.message.error) {
                            frappe.msgprint(__("AI Error: {0}").format(r_gen.message.error));
                            frm.set_value("results_html", `<p class="text-danger">AI Error: ${r_gen.message.error}</p>`);
                            return;
                        }
                        const orm_json = r_gen.message.orm_json;
                        frm.doc.generated_orm_json_for_saving = JSON.stringify(orm_json); // Store for saving

                        // 3. Execute ORM Query
                        frappe.call({
                            method: "sql_helper.sql_helper.utils.query_executor.execute_orm_query",
                            args: {
                                orm_json_str: JSON.stringify(orm_json)
                            },
                            callback: function(r_exec) {
                                if (r_exec.exc) {
                                    frappe.msgprint(__("Error executing query: {0}").format(r_exec.exc));
                                    frm.set_value("results_html", `<p class="text-danger">Error executing query: ${r_exec.exc}</p>`);
                                    return;
                                }
                                if (r_exec.message.error) {
                                    frappe.msgprint(__("Query Execution Error: {0}").format(r_exec.message.error));
                                    frm.set_value("results_html", `<p class="text-danger">Query Execution Error: ${r_exec.message.error}</p>`);
                                    return;
                                }
                                const results = r_exec.message.result;
                                const is_aggregate = r_exec.message.is_aggregate;

                                // 4. Display Results
                                if (is_aggregate) {
                                     frm.set_value("results_html", `<div class="alert alert-info">Result: <strong>${results}</strong></div>`);
                                     // No table or chart for single aggregate value
                                     frm.set_df_property("save_query_button", "hidden", 0);
                                     frm.set_df_property("save_chart_button", "hidden", 1);
                                } else if (results && results.length > 0) {
                                    frm.set_value("results_html", sql_helper_render_table(results));
                                    // Allow saving query and potentially chart
                                    frm.set_df_property("save_query_button", "hidden", 0);
                                    // Check if data is suitable for charting before showing button
                                    if (sql_helper_is_chartable(results)) {
                                        frm.set_df_property("save_chart_button", "hidden", 0);
                                        // Render initial chart preview
                                        sql_helper_render_chart(frm, results, "Bar"); // Default to Bar chart
                                    } else {
                                         frm.set_df_property("save_chart_button", "hidden", 1);
                                         frm.set_value("chart_html", "<p><i>Data not suitable for charting. Requires at least one text/label column and one numeric column.</i></p>");
                                    }
                                } else {
                                    frm.set_value("results_html", "<p><i>Query executed successfully, but returned no results.</i></p>");
                                    frm.set_df_property("save_query_button", "hidden", 0); // Allow saving the query even if no results
                                    frm.set_df_property("save_chart_button", "hidden", 1);
                                }
                                frm.refresh_fields();
                            }
                        });
                    }
                });
            }
        });
    },

    save_query_button: function(frm) {
        if (!frm.doc.generated_orm_json_for_saving) {
            frappe.msgprint(__("No query generated or executed yet to save."));
            return;
        }

        frappe.prompt([
            {fieldname: 'query_name', fieldtype: 'Data', label: __('Query Name'), reqd: 1}
        ], function(values){
            frappe.call({
                method: "sql_helper.sql_helper.utils.persistence.save_query",
                args: {
                    query_name: values.query_name,
                    natural_language_question: frm.doc.question,
                    generated_orm_json: frm.doc.generated_orm_json_for_saving
                },
                callback: function(r) {
                    if (!r.exc && r.message) {
                        frappe.show_alert({message: __("Query '{0}' saved successfully.").format(values.query_name), indicator: 'green'});
                        // Optionally refresh saved query list
                    } else {
                         frappe.show_alert({message: __("Error saving query: {0}").format(r.exc || r._server_messages || "Unknown error"), indicator: 'red'});
                    }
                }
            });
        }, __("Save Query"), __("Save"));
    },

    save_chart_button: function(frm) {
        // Requires a saved query first
         if (!frm.doc.generated_orm_json_for_saving) {
            frappe.msgprint(__("Cannot save chart without a saved query. Please save the query first."));
            return;
        }
        // Find the associated saved query (or prompt user to save first)
        // This part needs refinement: how to link chart to the *saved* query?
        // Option 1: Force save query first, then save chart referencing the saved query name.
        // Option 2: Save query implicitly when saving chart (might be confusing).
        // Let's go with Option 1 for clarity.
        frappe.msgprint(__("Please save the query first using the 'Save Query' button. Then, load the saved query and save the chart."));
        // TODO: Improve this workflow. Maybe allow saving query and chart together?
        // Or, after saving query, enable save chart with the saved query name pre-filled?
    },

    load_saved_query: function(frm) {
        if (frm.doc.load_saved_query) {
            frappe.db.get_doc("Saved Query", frm.doc.load_saved_query)
                .then(doc => {
                    frm.set_value("question", doc.natural_language_question);
                    // Store the loaded ORM JSON to potentially re-run or save chart
                    frm.doc.generated_orm_json_for_saving = doc.generated_orm_json;
                    // Clear results and trigger query run?
                    frm.set_value("results_html", "");
                    frm.set_value("chart_html", "");
                    frm.set_df_property("save_query_button", "hidden", 1); // Don't save again immediately
                    frm.set_df_property("save_chart_button", "hidden", 1);
                    frappe.msgprint(__("Loaded query '{0}'. Press 'Run Query' to execute.").format(doc.query_name));
                    // Maybe automatically run?
                    // frm.trigger("run_query_button");
                });
        }
    },

    load_saved_chart: function(frm) {
        if (frm.doc.load_saved_chart) {
            frappe.call({
                method: "sql_helper.sql_helper.utils.persistence.get_chart_data",
                args: { chart_docname: frm.doc.load_saved_chart },
                callback: function(r) {
                    if (r.exc) {
                        frappe.msgprint(__("Error loading chart data: {0}").format(r.exc));
                        return;
                    }
                    if (r.message.error) {
                         frappe.msgprint(__("Error loading chart data: {0}").format(r.message.error));
                         return;
                    }
                    const chart_data = r.message;
                    frm.set_value("question", chart_data.natural_language_question);
                    frm.set_value("results_html", sql_helper_render_table(chart_data.data));
                    sql_helper_render_chart(frm, chart_data.data, chart_data.chart_type);
                    frm.set_df_property("save_query_button", "hidden", 1); // Loaded, not new
                    frm.set_df_property("save_chart_button", "hidden", 1);
                    frappe.show_alert(__("Loaded chart '{0}'").format(chart_data.chart_name));
                }
            });
        }
    }
});

// --- Helper Functions ---

function sql_helper_render_table(data) {
    if (!data || data.length === 0) {
        return "<p><i>No data to display.</i></p>";
    }
    let headers = Object.keys(data[0]);
    let html = `<div class="table-responsive">
        <table class="table table-bordered table-condensed" style="width:auto; min-width: 100%;">
            <thead>
                <tr>`;
    headers.forEach(h => html += `<th>${frappe.unscrub(h)}</th>`);
    html += `       </tr>
            </thead>
            <tbody>`;
    data.forEach(row => {
        html += `<tr>`;
        headers.forEach(h => {
            let value = row[h];
            // Format numbers, dates etc. if needed
            html += `<td>${value === null || value === undefined ? '' : value}</td>`;
        });
        html += `</tr>`;
    });
    html += `   </tbody>
        </table>
    </div>`;
    // Add Export Button
    html += `<button class="btn btn-sm btn-default sql-helper-export-csv">Export to CSV</button>`;
    // Attach event listener after rendering
    setTimeout(() => {
         $('.sql-helper-export-csv').on('click', () => sql_helper_export_csv(data));
    }, 100);
    return html;
}

function sql_helper_is_chartable(data) {
    if (!data || data.length === 0) return false;
    let headers = Object.keys(data[0]);
    let has_numeric = headers.some(h => typeof data[0][h] === 'number');
    let has_string_or_date = headers.some(h => typeof data[0][h] === 'string' || frappe.datetime.is_date_obj(data[0][h])); // Basic check
    return has_numeric && has_string_or_date;
}

function sql_helper_render_chart(frm, data, chartType) {
    if (!sql_helper_is_chartable(data)) return;
    if (!window.Chart) {
        frappe.msgprint(__("Chart.js library not loaded. Cannot render chart."));
        return;
    }

    frm.set_value("chart_html", `<canvas id="sqlHelperChart" style="max-height: 300px;"></canvas>`);
    frm.refresh_field("chart_html");

    // Prepare data for Chart.js
    let headers = Object.keys(data[0]);
    let label_field = headers.find(h => typeof data[0][h] === 'string' || frappe.datetime.is_date_obj(data[0][h]));
    let data_field = headers.find(h => typeof data[0][h] === 'number');

    if (!label_field || !data_field) {
        frm.set_value("chart_html", "<p><i>Could not automatically determine labels and data for chart.</i></p>");
        return;
    }

    let labels = data.map(row => row[label_field]);
    let chartData = data.map(row => row[data_field]);

    const ctx = document.getElementById('sqlHelperChart').getContext('2d');
    
    // Destroy previous instance if exists
    if (frm.chart_instance) {
        frm.chart_instance.destroy();
    }

    frm.chart_instance = new Chart(ctx, {
        type: chartType.toLowerCase(), // 'bar', 'pie', 'line'
        data: {
            labels: labels,
            datasets: [{
                label: frappe.unscrub(data_field),
                data: chartData,
                backgroundColor: [
                    // Add more colors for variety, especially for pie charts
                    'rgba(54, 162, 235, 0.5)',
                    'rgba(255, 99, 132, 0.5)',
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(255, 206, 86, 0.5)',
                    'rgba(153, 102, 255, 0.5)',
                    'rgba(255, 159, 64, 0.5)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: chartType.toLowerCase() !== 'pie' ? {
                y: {
                    beginAtZero: true
                }
            } : {},
            plugins: {
                legend: {
                    display: chartType.toLowerCase() === 'pie' // Only show legend for pie usually
                }
            }
        }
    });
}

// Basic CSV Export
function sql_helper_export_csv(data) {
    if (!data || data.length === 0) {
        frappe.msgprint(__("No data to export."));
        return;
    }
    let headers = Object.keys(data[0]);
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += headers.map(h => `"${h.replace(/"/g, '""')}"`).join(",") + "\r\n"; // Header row

    data.forEach(row => {
        let rowContent = headers.map(h => {
            let value = row[h];
            if (value === null || value === undefined) {
                return "";
            }
            let stringValue = String(value);
            return `"${stringValue.replace(/"/g, '""')}"`; // Escape double quotes
        }).join(",");
        csvContent += rowContent + "\r\n";
    });

    var encodedUri = encodeURI(csvContent);
    var link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "query_results.csv");
    document.body.appendChild(link); // Required for FF
    link.click();
    document.body.removeChild(link);
}

