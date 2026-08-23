/* Data Model tab — the tables behind everything above, derived from this
   project's own requirements rather than named after a vendor. This is a
   proposed starting point, not a schema that has been created anywhere —
   no database exists yet, so nothing here claims otherwise. */

window.TABS = window.TABS || {};

const DATA_MODEL_TABLES = [
  {
    id: "user",
    name: "User",
    from: ["REQ-009"],
    purpose: "A person using the assistant, with the role that governs what they can do.",
    fields: [
      ["id", "uuid, primary key"],
      ["name", "text"],
      ["email", "text, unique"],
      ["role", "enum: business_user, data_analyst, data_engineer, executive, admin"],
      ["created_at", "timestamp"],
    ],
    relationships: ["Has many DataConnection", "Has many CsvUpload", "Has many Conversation", "Has many Alert"],
  },
  {
    id: "data_connection",
    name: "DataConnection",
    from: ["REQ-001", "REQ-014", "REQ-015"],
    purpose: "A configured connection to a SQL Server database, including how it authenticates and whether it's encrypted.",
    fields: [
      ["id", "uuid, primary key"],
      ["user_id", "uuid, foreign key -> User"],
      ["server_host", "text"],
      ["auth_type", "enum: windows_integrated, sql_authentication"],
      ["is_encrypted", "boolean — must be true per REQ-015"],
      ["created_at", "timestamp"],
    ],
    relationships: ["Belongs to User", "Has many SchemaProfile"],
  },
  {
    id: "csv_upload",
    name: "CsvUpload",
    from: ["REQ-002", "REQ-016"],
    purpose: "A CSV file a user has uploaded for analysis, with the data-quality checks run against it.",
    fields: [
      ["id", "uuid, primary key"],
      ["user_id", "uuid, foreign key -> User"],
      ["filename", "text"],
      ["null_value_count", "integer"],
      ["duplicate_record_count", "integer"],
      ["uploaded_at", "timestamp"],
    ],
    relationships: ["Belongs to User", "Has many AnalysisResult"],
  },
  {
    id: "conversation",
    name: "Conversation",
    from: ["REQ-003", "REQ-008"],
    purpose: "A thread of natural-language questions from one user, so follow-ups don't need to repeat context.",
    fields: [
      ["id", "uuid, primary key"],
      ["user_id", "uuid, foreign key -> User"],
      ["started_at", "timestamp"],
    ],
    relationships: ["Belongs to User", "Has many Question"],
  },
  {
    id: "question",
    name: "Question",
    from: ["REQ-003", "REQ-004", "REQ-011"],
    purpose: "A single natural-language question, plus the system's interpretation of it (and the SQL it generated, if any).",
    fields: [
      ["id", "uuid, primary key"],
      ["conversation_id", "uuid, foreign key -> Conversation"],
      ["question_text", "text"],
      ["interpreted_as", "text, nullable — the system's suggested interpretation when uncertain"],
      ["generated_sql", "text, nullable"],
      ["asked_at", "timestamp"],
    ],
    relationships: ["Belongs to Conversation", "Has one AnalysisResult"],
  },
  {
    id: "analysis_result",
    name: "AnalysisResult",
    from: ["REQ-005", "REQ-010"],
    purpose: "The answer to a question: the finding, and a business-friendly explanation of how it was reached.",
    fields: [
      ["id", "uuid, primary key"],
      ["question_id", "uuid, foreign key -> Question"],
      ["summary", "text"],
      ["business_explanation", "text"],
      ["source_type", "enum: data_connection, csv_upload"],
      ["source_id", "uuid"],
      ["created_at", "timestamp"],
    ],
    relationships: ["Belongs to Question", "Has many Visualization", "Has many Report"],
  },
  {
    id: "visualization",
    name: "Visualization",
    from: ["REQ-006"],
    purpose: "A chart generated from an analysis result, with the parameters used to configure it.",
    fields: [
      ["id", "uuid, primary key"],
      ["analysis_result_id", "uuid, foreign key -> AnalysisResult"],
      ["chart_type", "text"],
      ["parameters", "jsonb"],
      ["created_at", "timestamp"],
    ],
    relationships: ["Belongs to AnalysisResult"],
  },
  {
    id: "report",
    name: "Report",
    from: ["REQ-007", "REQ-013", "REQ-018"],
    purpose: "A generated report or executive summary built from one or more analysis results, downloadable by the user.",
    fields: [
      ["id", "uuid, primary key"],
      ["analysis_result_id", "uuid, foreign key -> AnalysisResult"],
      ["report_type", "enum: standard, executive_summary"],
      ["format", "enum: pdf, csv"],
      ["generated_at", "timestamp"],
    ],
    relationships: ["Belongs to AnalysisResult"],
  },
  {
    id: "schema_profile",
    name: "SchemaProfile",
    from: ["REQ-012"],
    purpose: "A data engineer's inspection of a connected schema — tables, columns, and basic profiling stats.",
    fields: [
      ["id", "uuid, primary key"],
      ["data_connection_id", "uuid, foreign key -> DataConnection"],
      ["table_name", "text"],
      ["column_profile", "jsonb"],
      ["profiled_at", "timestamp"],
    ],
    relationships: ["Belongs to DataConnection"],
  },
  {
    id: "alert",
    name: "Alert",
    from: ["REQ-017"],
    purpose: "A recommendation or alert surfaced to a user based on analysis of their data.",
    fields: [
      ["id", "uuid, primary key"],
      ["user_id", "uuid, foreign key -> User"],
      ["analysis_result_id", "uuid, foreign key -> AnalysisResult, nullable"],
      ["message", "text"],
      ["created_at", "timestamp"],
    ],
    relationships: ["Belongs to User", "References AnalysisResult"],
  },
];

function datamodelList(container) {
  container.innerHTML = `
    <h1>Data Model</h1>
    <p class="lede">A starting point, not the answer — derived from this project's own requirements. Nothing here has been created in a database yet.</p>
    <div class="card-grid">
      ${DATA_MODEL_TABLES.map(
        (t) => `
        <a class="card" href="#datamodel/${t.id}">
          <span class="card-label">Table</span>
          <span class="card-value" style="font-size:1.15rem;">${esc(t.name)}</span>
          <span class="card-sub">${esc(t.purpose)}</span>
          <span class="card-drill">Fields & relationships &rarr;</span>
        </a>`
      ).join("")}
    </div>
  `;
}

function datamodelDetail(container, id) {
  const t = DATA_MODEL_TABLES.find((x) => x.id === id);
  if (!t) {
    container.innerHTML = `${breadcrumb("Data Model", "datamodel", "Not found")}${emptyState("Not found", "No table with this id in the proposed model.")}`;
    return;
  }
  container.innerHTML = `
    ${breadcrumb("Data Model", "datamodel", t.name)}
    <h1>${esc(t.name)}</h1>
    <p class="lede">${esc(t.purpose)}</p>
    <div class="section">
      <h2>Fields</h2>
      <table>
        <thead><tr><th>Field</th><th>Type</th></tr></thead>
        <tbody>
        ${t.fields.map(([f, d]) => `<tr><td>${esc(f)}</td><td>${esc(d)}</td></tr>`).join("")}
        </tbody>
      </table>
    </div>
    <div class="section">
      <h2>Relationships</h2>
      <ul>${t.relationships.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
    </div>
    <div class="section">
      <h2>Derived from</h2>
      <p>${t.from.map((id) => `<a href="#kb/${id}">${esc(id)}</a>`).join(", ")}</p>
    </div>
  `;
}

window.TABS.datamodel = function renderDatamodel(container, state, mode, subpath) {
  if (subpath && subpath[0]) {
    datamodelDetail(container, subpath[0]);
  } else {
    datamodelList(container);
  }
};
