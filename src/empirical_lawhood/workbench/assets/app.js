import {mountInvocationProgress} from "./invocation-progress.js";

function errorExplanation(row) {
  const d = row.diagnostic;
  if (!d) return `${row.reason_code}: ${row.message}`;
  return `${row.reason_code}: ${row.message}\nObject: ${d.authored_object || "unspecified"}; operation: ${d.operation}\nOwner: ${d.owner}; contract: ${d.contract}\nExpected: ${d.expected}\nObserved: ${d.actual}\nImplementation: ${d.implementation}\nRemediation: ${d.remediation}${d.evidence ? "\nDiagnostic: " + d.evidence : ""}`;
}

/* SPDX-License-Identifier: MPL-2.0 */
const $ = id => document.getElementById(id);
const node = (tag, text, className) => { const value = document.createElement(tag); if (text !== undefined) value.textContent = text; if (className) value.className = className; return value; };
const state = {contexts: [], context: null, section: "results", generation: 0, pending: false, last: null, page: null, inspectorFocus: null, drafts:new Map(), polling:null, presentations:[], knowledgeDrafts:new Map(), inquiryDrafts:new Map(), programmeDrafts:new Map()};
let disposeInvocations = null;
let token = new URLSearchParams(location.hash.slice(1)).get("session") || sessionStorage.getItem("el-session");
if (token) sessionStorage.setItem("el-session", token);
history.replaceState(null, "", location.pathname);
const stringify = value => JSON.stringify(value, null, 2);
const exact = value => value === null || value === undefined ? "Not supplied" : typeof value === "object" ?
  (Object.keys(value).length === 1 && "decimal" in value ? value.decimal : Object.keys(value).length === 1 && "integer" in value ? value.integer : JSON.stringify(value)) : String(value);
const title = value => value.replaceAll("_", " ").replaceAll("-", " ");
const descriptor = operation => state.context?.engine?.operations?.find(row => row.operation_id === operation);
function showError(message) { $("error").textContent = message; $("error").hidden = false; $("message").hidden = true; }
function message(text) { $("message").textContent = text; $("message").hidden = false; $("error").hidden = true; }
function closeInspector() { $("inspector").hidden = true; $("inspector-value").textContent = ""; state.inspectorFocus?.focus(); }
function clearResult() { disposeInvocations?.(); disposeInvocations=null; state.page = null; $("result").replaceChildren(); closeInspector(); $("read-stamp").textContent = "No scientific object is open."; }
function inspector(label, value, note) {
  state.inspectorFocus = document.activeElement; $("inspector-title").textContent = label;
  $("inspector-note").textContent = note || "Original values, including record schema, revision and exact numerical representation.";
  $("inspector-value").textContent = stringify(value); $("inspector").hidden = false; $("close-inspector").focus();
}
function badge(value, scientific=false) {
  const text = exact(value); const adverse = scientific && /CONTRADICT|FALSIF|REFUT|FAIL|REJECT/.test(text);
  const unresolved = /UNKNOWN|UNRESOLVED|UNAVAILABLE|DEFERRED|NOT_ESTABLISHED|UNEVALUABLE|ABSENT|PARTIAL|^OPEN$/.test(text);
  const supported = scientific && /^(SUPPORTED|PASS)$/.test(text);
  return node("span", title(text), "badge" + (adverse ? " adverse" : unresolved ? " unresolved" : supported ? " supported" : ""));
}
function button(label, action, className="secondary") { const value = node("button", label, className); value.type="button"; value.addEventListener("click", action); return value; }
function details(label, value) { const box = node("details", undefined, "details"); box.append(node("summary", label), node("pre", stringify(value), "exact")); return box; }
function panel(label, count) { const box = node("section", undefined, "panel"); const head=node("div", undefined, "panel-head"); head.append(node("h2", label)); if (count !== undefined) head.append(node("span", count, "count")); box.append(head); return box; }
async function fetchJSON(path, body, signal) {
  const headers = {"X-EL-Session": token || ""}; if (body !== undefined) headers["Content-Type"]="application/json";
  const response = await fetch(path, {method: body === undefined ? "GET" : "POST", headers, body: body === undefined ? undefined : JSON.stringify(body), cache:"no-store", credentials:"omit", redirect:"error", signal});
  const data = await response.json(); if (!response.ok) throw new Error(data.errors?.map(errorExplanation).join(" · ") || `Local request refused (${response.status}).`);
  return data;
}
function savedInvocations() { try { const rows=JSON.parse(localStorage.getItem("el-workbench-invocations")||"[]");return Array.isArray(rows)?rows.slice(-32):[]; } catch { return []; } }
function rememberInvocation(row) { const rows=savedInvocations().filter(old=>old.handle!==row.handle);rows.push(row);localStorage.setItem("el-workbench-invocations",JSON.stringify(rows.slice(-32))); }
async function durableRequest(document, generation) {
  const hash=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(document.context_id+":"+document.request_id));
  const handle=[...new Uint8Array(hash)].map(value=>value.toString(16).padStart(2,"0")).join("");
  rememberInvocation({handle,context_id:document.context_id,operation:document.operation,request_id:document.request_id});
  const response=await fetch("/api/invoke",{method:"POST",headers:{"X-EL-Session":token||"","Content-Type":"application/json"},body:JSON.stringify(document),cache:"no-store",credentials:"omit",redirect:"error"});
  if(!response.ok) {const error=await response.json();throw new Error(error.errors?.map(errorExplanation).join(" · ")||"Invocation request refused.");}
  const reader=response.body.getReader(), decoder=new TextDecoder();let text="", received=0, result=null;
  try { while(true) {const chunk=await reader.read();if(chunk.done)break;received+=chunk.value.byteLength;if(received>5*1024*1024)throw new Error("Invocation response exceeds its display limit.");text+=decoder.decode(chunk.value,{stream:true});let end;
    while((end=text.indexOf("\n"))>=0){const event=JSON.parse(text.slice(0,end));text=text.slice(end+1);
      if(event.event==="invocation" && generation===state.generation) message(`Invocation ${event.payload.handle.slice(0,12)} · ${event.payload.state}. Work continues if this view disconnects. Its handle is in Invocations.`);
      if(event.event==="result")result=event.payload;
      if(event.event==="existing" && generation===state.generation)message(event.payload.message+" Open Invocations for its current state.");
    }
  } if(text.trim())throw new Error("Invocation response ended before its complete record.");return result;
  } finally {reader.releaseLock();}
}
async function issue(operation, parameters={}, options={}) {
  if (state.pending) { message("This context is completing its current read. Its invocation continues independently of this view."); return null; }
  const selected = descriptor(operation);
  if (!selected?.browser_available) { showError(selected?.unavailable_reason || "This operation is unavailable in the selected engine."); return null; }
  const generation = ++state.generation; state.pending = true; $("open").disabled = true; $("session-state").textContent = "Reading";
  if(!options.keepView)clearResult(); message(selected.effects);
  try {
    const request={schema:"empirical-lawhood/application/request",version:"1.0.0",request_id:crypto.randomUUID(),context_id:state.context.selection.value.context_id,operation,parameters};
    const response = ["DURABLE_READ","EFFECT"].includes(selected.lifecycle) ? await durableRequest(request,generation) : await fetchJSON("/api/execute",request);
    if (generation !== state.generation) return null;
    if(response===null)return null;
    if (response.status !== "SUCCEEDED") throw new Error(response.errors?.map(errorExplanation).join(" · ") || response.status);
    if (options.render !== false) {state.last = {operation, parameters}; state.page = response.payload;render(response.payload, operation);}
    $("message").hidden = true; $("read-stamp").textContent = `Read at ${new Date().toLocaleTimeString()} · ${state.context.selection.value.label}`;
    return response.payload;
  } catch (error) { if (generation === state.generation) { if(!options.keepView || state.section==="results")clearResult(); showError(error.message); } return null; }
  finally { if(generation===state.generation){state.pending = false; $("open").disabled = false; $("session-state").textContent = "Connected";} }
}
function chooseSection(section) {
  if (state.pending && section!=="invocations") return;
  if(section==="invocations"){state.pending=false;$("open").disabled=false;$("session-state").textContent="Connected";}
  clearTimeout(state.polling);
  state.section=section; ++state.generation; state.last=null; clearResult(); $("error").hidden=true; $("message").hidden=true;
  for (const name of ["results","design","programme","inquiry","knowledge","workflows","invocations","context"]) { const target=$("nav-"+name); target.classList.toggle("selected", name===section); if(name===section) target.setAttribute("aria-current","page"); else target.removeAttribute("aria-current"); }
  const labels={results:"Retained results",design:"Design & run",programme:"Composite programmes",inquiry:"Inquiry & successors",knowledge:"Knowledge & exchange",workflows:"Installed workflows",invocations:"Invocations",context:"Context & access"};
  $("page-title").textContent=labels[section]; $("breadcrumb").textContent="Workspace / "+labels[section];
  $("page-description").textContent = section==="results" ? "Open an original result and follow its evidence, attempts and provenance." : section==="workflows" ? "Installed declarations describe available routes. Preparation and authority are checked at their owning boundaries." : "Explicit selections for this session. Original study identities stay with their retained records.";
  $("kind").closest("label").hidden=section!=="results"; $("directory").closest("label").hidden=section!=="results"; $("open").hidden=section!=="results";
  $("panel-field").hidden=section!=="results"||$("kind").value!=="presentation";
  sourceFields();
  if(section==="workflows") issue("workflow.list", {limit:20}); else if(section==="context") renderContext(); else if(section==="invocations")renderInvocations();else if(section==="design")renderDesign();else if(section==="knowledge")renderKnowledge();else if(section==="inquiry")renderInquiry();else if(section==="programme")renderProgramme();else renderEmpty();
  if(section==="results"&&$("kind").value==="presentation"&&!state.presentations.length)loadPresentations();
}
function renderEmpty() { const box=node("div",undefined,"empty"); box.append(node("div","◎","empty-mark"), node("h2","Start with the original record"),node("p","Select an engine context and an original directory. Each read checks the original custody and current access.")); $("result").append(box); }
function openResult() {
  const path=$("directory").value.trim(); if(!path.startsWith("/")) { showError("Select an absolute retained directory."); $("directory").focus(); return; }
  if($("kind").value.startsWith("continuing.")){
    const operation=$("kind").value,parameters={directory:path,limit:50};
    if(operation==="continuing.operation")parameters.request_id=$("source-request").value.trim();
    else for(const name of ["first-segment","segment-count","first-boundary","boundary-count"])parameters[name.replaceAll("-","_")]=Number($(name).value);
    issue(operation,parameters);return;
  }
  if($("kind").value==="presentation"){
    const selected=state.presentations.find(row=>row.panel_id===$("panel").value);
    if(!selected){showError("Select an installed presentation for this context.");return;}
    issue("presentation.read",{directory:path,panel_id:selected.panel_id,panel_version:selected.version,limit:50});return;
  }
  const operation={rc:"recursive.execution",execution:"recursive.execution",sci02d:"recursive.execution",analysis:"analysis.inspect",matrix:"matrix.inspect"}[$("kind").value];
  issue(operation,{directory:path,limit:50});
}
function tabs(active) {
  if(state.section!=="results") return;
  const bar=node("div",undefined,"tabs"); bar.setAttribute("aria-label","Retained object views");
  const choices=$("kind").value==="rc" ? [["Execution","recursive.execution"],["Question & relationships","rc.design"],["Findings","rc.findings"]] : $("kind").value==="sci02d" ? [["Execution","recursive.execution"],["Recorded findings","sci02d.findings"]] : [];
  for(const [label,operation] of choices) { const item=button(label,()=>issue(operation,{directory:$("directory").value.trim(),limit:50}),"tab"+(operation===active?" active":"")); item.disabled= !descriptor(operation)?.browser_available; if(operation===active) item.setAttribute("aria-current","page"); bar.append(item); }
  if($("kind").value==="rc")bar.append(button("Export complete report",async()=>{const value=await issue("rc.export",{directory:$("directory").value.trim()},{render:false,keepView:true});if(value){const url=URL.createObjectURL(new Blob([stringify(value)+"\n"],{type:"application/json"}));const link=node("a");link.href=url;link.download="rc-original-report.json";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message("Complete report reopened and exported. Its exposed development scope is unchanged.");}},"tab"));
  if($("kind").value==="sci02d"){
    const assess=button("Reconstruct & export full report",async()=>{const value=await issue("sci02d.assess",{directory:$("directory").value.trim()},{render:false,keepView:true});if(value){const url=URL.createObjectURL(new Blob([stringify(value)+"\n"],{type:"application/json"}));const link=node("a");link.href=url;link.download="sci02d-independent-read.json";link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message("Independent reconstruction completed for the downloaded original report. Qualification and molecular applicability retain their recorded limits.");}},"tab");
    assess.disabled=!descriptor("sci02d.assess")?.browser_available;bar.append(assess);
  }
  if(state.page?.provenance) bar.append(button("Provenance", async()=>{ const last=state.last; const fresh=await issue(last.operation,last.parameters); if(fresh) inspector("Original provenance",fresh.provenance,"Source identities and original custody. This read does not change the producing source."); },"tab"));
  if(bar.childNodes.length) $("result").append(bar);
}
function render(payload, operation) {
  $("result").replaceChildren();
  if(operation==="workflow.list") { renderWorkflows(payload); return; }
  if(operation==="workflow.show") { renderWorkflow(payload); return; }
  if(state.section==="knowledge")renderKnowledgeFields();
  if(state.section==="inquiry")renderInquiryFields();
  if(state.section==="programme")renderProgrammeFields();
  const head=node("div",undefined,"object-head"); const text=node("div"); text.append(node("div",payload.title||"Retained object","object-title"),node("div",payload.scope||"Original scope","object-scope")); head.append(text,badge(payload.summary?.qualification||payload.summary?.scientific_qualification||"ORIGINAL_RETAINED_SCOPE")); $("result").append(head);
  const summary=payload.summary||{}; const metrics=node("div",undefined,"cards");
  const selectedKeys= ["selected_action","admission_status","outcome_id","successor","verification_status","original_disposition","consumer_admission","unseen_updates","selected_imports","selected_objects","claim_disposition","assigned_units","assigned_opportunities","independent_units","nested_views_per_opportunity","retained_disposition","effect_disposition","event_window_status","source_generation","finite_requests_selected","selected_boundary_records","selected_event_segments","execution_status","assigned_tasks","assigned_roots","attempt_records","assessment_count","member_count","scientific_completion","requirement_count","connection_count","state"].filter(key=>key in summary);
  for(const key of selectedKeys.slice(0,6)) { const card=node("div",undefined,"metric"); const value=exact(summary[key]); card.append(node("div",title(key),"label"),node("div",title(value),"value"+(value.length>12?" small":""))); metrics.append(card); }
  if(metrics.childNodes.length) $("result").append(metrics);
  tabs(operation);
  if(payload.presentation){const box=panel("Original findings and presentation");box.append(badge(payload.presentation.status),node("p",`${payload.presentation.panel_id} · requested ${payload.presentation.requested_version} · installed ${payload.presentation.installed_version}`,"small-note"),details("Original result, contracts and exact values",payload.presentation.original_report));$("result").append(box);}
  if(payload.inquiry)renderInquiryLinks(payload.inquiry);
  if(payload.programme){const box=panel("Original components and frontier");box.append(details("Registered descriptor and original programme report",{descriptor:payload.descriptor,report:payload.programme}));$("result").append(box);}
  if(payload.knowledge){const box=panel("Original knowledge and verification");box.append(node("p","Original assertions retain their stated scope. Current verification, authorship, consumer admission and unseen updates are separate.","small-note"),details("Complete original report and remaining requirements",payload.knowledge));$("result").append(box);}
  if(payload.continuing){const box=panel("Original source history");box.append(badge(payload.summary.retained_disposition),node("p","Historical actors, windows and finite requests share the original dependence root. These records grant no current actor access or permission to repeat an effect.","small-note"),details("Session, actor boundaries and original finite records",payload.continuing));$("result").append(box);}
  if(state.section==="results"&&$("kind").value==="sci02d")$("result").append(node("p","Recorded findings authenticate the original products without repeating the calculations. Reconstruct & export explicitly repeats the independent scientific read and can take several minutes. It acquires no new trajectories.","small-note"));
  if(payload.kind==="sci02d")renderSci02d(payload);
  if(payload.kind==="design") renderRelationships(payload);
  if(payload.frontier) { const frontier=panel("Original programme frontier"); frontier.append(node("p","Phase denominators remain separate. Reconstruction is off for this inspection.","small-note"),details("Frontier and dependency records",{frontier:payload.frontier,dependencies:payload.dependencies})); $("result").append(frontier); }
  if(payload.page) renderTable(payload,operation);
  const meaning=panel("Scope & provenance"); meaning.append(node("p",payload.value_semantics||descriptor(operation)?.evidence_ceiling||"Original scope is retained.","small-note"));
  meaning.append(details("Complete summary and original identity",{summary,identity:payload.identity,scope:payload.scope}));
  if(payload.provenance) meaning.append(details("Source and custody identities",payload.provenance)); $("result").append(meaning);
}
function columns(kind) {
  if(kind==="inquiry"||kind==="composite")return ["member","record"];
  if(kind==="knowledge.query")return ["publisher_label","origin_namespace","identity","current_scientific_assessment"];
  if(kind==="knowledge.certificate"||kind==="knowledge.resolve")return ["field","value"];
  if(kind==="continuing.session")return ["record_kind","ordinal","disposition","actor_id","selected_identity"];
  if(kind==="continuing.operation")return ["field","value"];
  return {execution:["task_id","ordinal","operational_status","reason_code"],findings:["assessment_id","disposition","phase","reason_codes"],sci02d:["bank","ordinal","state","disposition","reasons"],design:["requirement_id","condition_role","consumer","assessment"],analysis:["relative_path","size_bytes","sha256"],"analysis-member":["field","value"],programme:["phase","operational_completion","scientific_read_completed","scientific_dispositions"]}[kind] || ["record"];
}
function renderSci02d(payload) {
  const box=panel("Recorded cohort findings");const aggregate=payload.aggregate, summary=payload.summary;
  box.append(badge(aggregate.pooled_disposition||"UNKNOWN",true),node("p",`Original banks: ${Object.entries(summary.bank_census).map(([key,value])=>`${title(key)} ${value}`).join(" · ")}. Nested numerical and starting-history views are not additional independent roots.`,"small-note"));
  box.append(details("Pooled estimates, uncertainty and complete counts",aggregate));
  box.append(details("Original quantity, units, precision and design",payload.design));
  box.append(details("Molecular applicability and qualification",{molecular_requirement:summary.molecular_requirement,equilibrium_state_coverage:summary.equilibrium_state_coverage,qualification:summary.qualification,inquiry_outcome:summary.inquiry_outcome,claim_assessment:summary.claim_assessment}));
  box.append(details("Measured work and its accounting scope",payload.costs));$("result").append(box);
}
async function inspectCurrent(index,label) {
  const last=state.last; const offset=state.page.page.offset; const census=state.page.page.census_sha256;
  const fresh=await issue(last.operation,last.parameters);
  if(!fresh) return;
  if(fresh.page.census_sha256!==census || fresh.page.offset!==offset) { message("The original census changed. Inspect the new page before selecting a record."); return; }
  inspector(label,fresh.page.rows[index]);
  state.inspectorFocus=document.querySelectorAll("tbody .record-exact")[index]||$("open");
}
function renderTable(payload,operation) {
  const data=payload.page; const labels={execution:"Original attempts",findings:"Independent assessments",sci02d:"Original independent roots",design:"Scientific requirements",analysis:"Closed package members","analysis-member":"Original member values",programme:"Programme phases"};
  const box=panel(labels[payload.kind]||"Retained records",`${data.matching_total} matching / ${data.total} total${payload.kind==="knowledge.query"?" in selected import page":""}`);
  const form=node("form",undefined,"filter"); const label=node("label","Filter these records","field"); const input=node("input"); input.value=data.filter; input.maxLength=256; input.placeholder="Identity, disposition or reason"; label.append(input); const submit=node("button","Apply filter","secondary"); submit.type="submit"; form.append(label,submit); form.addEventListener("submit",event=>{event.preventDefault();const parameters={...state.last.parameters,filter:input.value};delete parameters.cursor;issue(operation,parameters);}); box.append(form);
  const wrap=node("div",undefined,"table-wrap"); const table=node("table"); const thead=node("thead"), tr=node("tr"); const fields=payload.presentation?.columns||columns(payload.kind); for(const key of fields) tr.append(node("th",title(key))); tr.append(node("th","Inspect")); thead.append(tr); const tbody=node("tbody");
  data.rows.forEach((row,index)=>{const line=node("tr");for(const key of fields){ const value=key==="record"? row.value||row:row[key];const cell=node("td",undefined,key.endsWith("id")?"identity-cell":""); cell.dataset.label=title(key); if(["operational_status","disposition"].includes(key)) cell.append(badge(value,key==="disposition")); else cell.textContent=exact(value);line.append(cell);} const action=node("td"); const label=row.assessment_id||row.task_id||row.requirement_id||row.field||`Record ${data.offset+index+1}`;action.append(button("Exact record ↗",()=>inspectCurrent(index,label),"record-button record-exact")); if(payload.kind==="analysis"){const name=row.value?.relative_path||row.value?.filename||row.relative_path; if(name && /\.(json|txt|md)$/.test(name)) action.append(button("Preview member",()=>issue("analysis.member",{directory:$("directory").value.trim(),member:name,limit:50}),"record-button"));} if(payload.kind==="knowledge.query")knowledgeRowActions(action,row);line.append(action);tbody.append(line);});
  table.append(thead,tbody);wrap.append(table);box.append(wrap);
  if(!data.rows.length) box.append(node("p","No records match this selection. The total denominator is unchanged.","small-note"));
  const pages=node("div",undefined,"page-controls");pages.append(node("span",`Rows ${data.returned_count?data.offset+1:0}–${data.offset+data.returned_count} of ${data.matching_total}`,"count"));
  const actions=node("div");if(data.offset)actions.append(button("First page",()=>{const p={...state.last.parameters};delete p.cursor;issue(operation,p);}));if(data.next_cursor) actions.append(button("Next page →",()=>issue(operation,{...state.last.parameters,cursor:data.next_cursor})));pages.append(actions);box.append(pages);if(payload.kind==="knowledge.query"&&payload.knowledge.has_more)box.append(button("Next import page →",()=>{const p={...state.last.parameters,after_materialization_id:payload.knowledge.next_after_materialization_id};delete p.cursor;issue(operation,p);}));$("result").append(box);
}
function renderRelationships(payload) {
  const scientific=panel("Scientific relationships",`${payload.summary.requirement_count} requirements · ${payload.summary.connection_count} connections`);
  scientific.append(node("p","Requirements state what a consumer needs. An authored relationship has no assessed disposition until its independent result is read.","small-note"));
  const grid=node("div",undefined,"relationship-grid");payload.page.rows.forEach((row,index)=>{const value=button("",()=>inspectCurrent(index,row.requirement_id),"relationship-node");value.append(node("span",title(row.condition_role||"Requirement"),"node-role"),node("span",row.requirement_id,"node-id"),node("span",`Consumer → ${row.consumer}`,"node-edge"),node("span",`Assessment → ${row.assessment||"Unresolved"}`,"node-edge"));grid.append(value);});scientific.append(grid,details("Connections, suppliers and unresolved premises",payload.design));$("result").append(scientific);
  const execution=payload.execution_graph;if(execution){const box=panel("Execution dependency graph",`${execution.nodes.length} assigned tasks`);box.append(node("p","Edges come from the original authenticated execution plan. They describe scheduling dependencies.","small-note"));const list=node("div",undefined,"relationship-grid");for(const row of execution.nodes){const value=node("div",undefined,"relationship-node");value.append(node("span",title(row.stage),"node-role"),node("span",row.task_id,"node-id"),node("span",row.dependency_task_ids.length?`Requires → ${row.dependency_task_ids.join(", ")}`:"No task predecessor","node-edge"));list.append(value);}box.append(list,details("Execution plan identity",execution.identity));$("result").append(box);}
}
function renderWorkflows(payload) {
  const grid=node("div",undefined,"workflow-grid");for(const row of payload.page.rows){const card=node("article",undefined,"workflow-card");card.append(badge(row.kind),node("h2",row.title),node("p",row.scientific_ceiling),button("Inspect workflow →",()=>issue("workflow.show",{workflow_id:row.workflow_id}),"record-button"));grid.append(card);}$("result").append(grid);
  const controls=node("div",undefined,"page-controls");controls.append(node("span",`${payload.page.total} installed declarations · prerequisites not inspected`,"count"));if(payload.page.next_cursor) controls.append(button("More workflows →",()=>issue("workflow.list",{limit:20,cursor:payload.page.next_cursor})));$("result").append(controls);
}
function renderWorkflow(payload) {
  const workflow=payload.workflow;const box=panel(workflow.title);box.append(node("p",workflow.scientific_ceiling,"small-note"),details("Inputs, environment and guide",workflow));const list=node("div",undefined,"details");for(const operation of payload.application_operations||[]){const row=node("p");row.append(node("strong",operation.title+" · "),badge(operation.browser_available?"AVAILABLE":operation.unavailable_reason),node("span"," "+operation.effects));list.append(row);}box.append(list);$("result").append(box);
}
function renderContext() {
  const wrapper=node("div",undefined,"context-list");const selection=panel("Current selections");const dl=node("dl");for(const [key,value] of Object.entries(state.context.selection.value)){dl.append(node("dt",title(key)),node("dd",exact(value)));}selection.append(dl);const installation=panel("Selected installation");installation.append(node("p","Context stores locators and limits. Each retained read rechecks current access through the owning service.","small-note"));if(state.context.engine)installation.append(details("Observed engine and supported operations",state.context.engine));if(state.context.error)installation.append(details("Compatibility refusal",state.context.error));wrapper.append(selection,installation);$("result").append(wrapper);
}
function knowledgeDraft() {
  const key=state.context.selection.value.context_id;
  if(!state.knowledgeDrafts.has(key))state.knowledgeDrafts.set(key,{directory:"",namespace:"",certificate:"",source_profile:"",source_root_contract:"",transfer_directory:"",output_directory:"",resume:false,revision:0,selected:new Map(),review:null,last:null});
  return state.knowledgeDrafts.get(key);
}
function clearKnowledgeDraftViews() {for(const draft of state.knowledgeDrafts.values()){draft.review=null;draft.last=null;draft.selected.clear();draft.revision++;}}
function clearKnowledgeDisplay() {
  for(const child of [...$("result").children])if(child.id!=="knowledge-controls")child.remove();
  state.last=null;state.page=null;closeInspector();$("read-stamp").textContent="Open the original object for a current read.";
}
function invalidateKnowledge(draft,{store=false}={}) {
  draft.revision++;draft.review=null;draft.last=null;if(store)draft.selected.clear();
  if(state.pending){++state.generation;state.pending=false;$("open").disabled=false;$("session-state").textContent="Connected";message("Selections changed. The previous invocation keeps its original request; its handle remains in Invocations.");}
  $("knowledge-apply")?.setAttribute("disabled","");$("knowledge-review")?.replaceChildren();
  clearKnowledgeDisplay();
}
async function readKnowledge(operation,parameters) {
  const draft=knowledgeDraft(), revision=draft.revision;clearKnowledgeDisplay();
  const report=await issue(operation,parameters,{render:false,keepView:true});
  if(report && draft===knowledgeDraft() && revision===draft.revision){state.last={operation,parameters};state.page=report;render(report,operation);}
}
async function reviewKnowledge(action) {
  const draft=knowledgeDraft();draft.review=null;$("knowledge-apply").disabled=true;
  const revision=draft.revision,selection={action,directory:draft.directory.trim(),namespace:draft.namespace.trim()};
  if(action==="IMPORT"){Object.assign(selection,{source_profile:draft.source_profile.trim(),transfer_directory:draft.transfer_directory.trim(),resume:draft.resume});if(draft.source_root_contract.trim())selection.source_root_contract=draft.source_root_contract.trim();}
  if(action==="EXPORT"){const rows=[...draft.selected.values()];Object.assign(selection,{locators:rows.map(row=>row.locator),roots:rows.map(row=>row.identity),output_directory:draft.output_directory.trim()});}
  clearKnowledgeDisplay();
  const report=await issue("knowledge.review",{text:JSON.stringify(selection)},{render:false,keepView:true});
  if(report && draft===knowledgeDraft() && revision===draft.revision){draft.review=report;renderKnowledge();}
}
function renderKnowledge() {$("result").replaceChildren();renderKnowledgeFields();}
function renderKnowledgeFields() {
  const draft=knowledgeDraft(),controls=node("div");controls.id="knowledge-controls";
  const intro=panel("Original evidence and local exchange");intro.append(node("p","Inspect original certificates and select exact objects from a local store. Review the complete transfer and destination before applying it. Scientific suitability remains with the selected consumer.","small-note"));controls.append(intro);
  const inspect=panel("Certificate inspection"),certificateFields=node("div",undefined,"design-fields");
  certificateFields.append(designField("Original certificate directory",draft.certificate,value=>{draft.certificate=value;invalidateKnowledge(draft);}));
  certificateFields.append(button("Verify original certificate",()=>readKnowledge("knowledge.certificate",{directory:draft.certificate.trim(),allow_partial:true,limit:50})));
  inspect.append(certificateFields);controls.append(inspect);
  const store=panel("Selected local store"),fields=node("div",undefined,"design-fields");
  for(const [name,label] of [["directory","Store directory"],["namespace","Original store namespace"]])fields.append(designField(label,draft[name],value=>{draft[name]=value;invalidateKnowledge(draft,{store:true});}));
  fields.append(node("p",`Catalogue: ${state.context.selection.value.catalog_relative_path||"No catalogue selected in this context"}. It is a rebuildable index of original imports.`,"small-note"));
  const actions=node("div",undefined,"design-actions");actions.append(button("Browse current imports",()=>readKnowledge("knowledge.query",{directory:draft.directory.trim(),namespace:draft.namespace.trim(),import_limit:8,limit:50})),button("Review new store",()=>reviewKnowledge("INITIALIZE")),button("Review new catalogue",()=>reviewKnowledge("REBUILD")));fields.append(actions);
  const selected=node("div");selected.id="knowledge-selected";selected.append(node("p",`${draft.selected.size} exact objects selected for export`,"small-note"),details("Selected full identities and locators",[...draft.selected.values()]));fields.append(selected);store.append(fields);controls.append(store);
  const exchange=panel("Complete local transfers"),transfer=node("div",undefined,"design-fields");
  for(const [name,label] of [["source_profile","Source operator profile"],["source_root_contract","Source retained root contract (optional)"],["transfer_directory","Original transfer directory"],["output_directory","New export directory"]])transfer.append(designField(label,draft[name],value=>{draft[name]=value;invalidateKnowledge(draft);}));
  const recovery=node("label","Resume the original interrupted import plan","field"),checkbox=node("input");checkbox.type="checkbox";checkbox.checked=draft.resume;checkbox.addEventListener("change",()=>{draft.resume=checkbox.checked;invalidateKnowledge(draft);});recovery.append(checkbox);transfer.append(recovery);
  const transferActions=node("div",undefined,"design-actions");transferActions.append(button("Review import",()=>reviewKnowledge("IMPORT")),button("Review selected export",()=>reviewKnowledge("EXPORT")));transfer.append(transferActions);
  const reviewed=node("div");reviewed.id="knowledge-review";
  if(draft.review){reviewed.append(node("p",`${title(draft.review.selection.action)} · exact destination and current complete transfer reviewed`,"small-note"),details("Reviewed objects, closure, destinations and entry conditions",draft.review));}
  transfer.append(reviewed);
  const apply=button("Apply reviewed action",async()=>{const current=draft.review,revision=draft.revision;if(!current)return;draft.review=null;apply.disabled=true;clearKnowledgeDisplay();const result=await issue("knowledge.apply",{text:JSON.stringify(current.selection),expected_review_sha256:current.review_sha256},{render:false,keepView:true});if(draft===knowledgeDraft()&&draft.revision===revision){draft.last=result;renderKnowledge();}});apply.id="knowledge-apply";apply.disabled=!draft.review;transfer.append(apply);exchange.append(transfer);controls.append(exchange);
  if(draft.last){const result=panel("Original exchange result");result.append(badge(draft.last.status),details("Complete returned locations and records",draft.last));controls.append(result);}
  $("result").append(controls);
}
function knowledgeRowActions(action,row) {
  const draft=knowledgeDraft(), key=JSON.stringify(row.locator),identityKey=JSON.stringify(row.identity);
  const select=node("label","Select for export","field"),input=node("input");input.type="checkbox";input.checked=draft.selected.has(key);
  input.addEventListener("change",()=>{
    if(input.checked && (draft.selected.size>=16 || [...draft.selected.entries()].some(([other,value])=>other!==key&&JSON.stringify(value.identity)===identityKey))){input.checked=false;showError("Select at most sixteen distinct complete identities. Another import of this same identity is already selected.");return;}
    if(input.checked)draft.selected.set(key,{identity:row.identity,locator:row.locator});else draft.selected.delete(key);
    draft.revision++;draft.review=null;$("knowledge-apply").disabled=true;$("knowledge-review").replaceChildren();
    $("knowledge-selected").replaceChildren(node("p",`${draft.selected.size} exact objects selected for export`,"small-note"),details("Selected full identities and locators",[...draft.selected.values()]));
  });select.append(input);action.append(select,button("Resolve original",()=>readKnowledge("knowledge.resolve",{text:JSON.stringify({directory:draft.directory.trim(),namespace:draft.namespace.trim(),locator:row.locator}),allow_partial:true,limit:50}),"record-button"));
}
function programmeDraft() {
  const key=state.context.selection.value.context_id;
  if(!state.programmeDrafts.has(key))state.programmeDrafts.set(key,{input:"",sources:"",source_snapshot:"",environment_id:"",protocol:"",output_dir:"",directory:"",programme_request:"",action:"RUN",allow_partial:false,revision:0,review:null,last:null});
  return state.programmeDrafts.get(key);
}
function clearProgrammeViews(){for(const draft of state.programmeDrafts.values()){draft.review=null;draft.last=null;draft.revision++;}}
function clearProgrammeDisplay(){for(const child of [...$("result").children])if(child.id!=="programme-controls")child.remove();state.last=null;state.page=null;closeInspector();$("read-stamp").textContent="Open the original programme for a current read.";}
function invalidateProgramme(draft){
  draft.revision++;draft.review=null;draft.last=null;
  if(state.pending){++state.generation;state.pending=false;$("open").disabled=false;$("session-state").textContent="Connected";message("Selections changed. The previous invocation remains available in Invocations.");}
  $("programme-apply")?.setAttribute("disabled","");$("programme-review")?.replaceChildren();$("programme-last")?.remove();clearProgrammeDisplay();
}
async function readProgramme(){
  const draft=programmeDraft(),revision=draft.revision,parameters={directory:draft.directory.trim(),allow_partial:draft.allow_partial,limit:50};clearProgrammeDisplay();
  const report=await issue("programme.read",parameters,{render:false,keepView:true});
  if(report&&draft===programmeDraft()&&revision===draft.revision){state.last={operation:"programme.read",parameters};state.page=report;render(report,"programme.read");}
}
async function reviewProgramme(authoring){
  const draft=programmeDraft(),revision=draft.revision;draft.review=null;$("programme-apply").disabled=true;$("programme-review").replaceChildren();clearProgrammeDisplay();
  const parameters=authoring?Object.fromEntries(["input","sources","source_snapshot","environment_id","output_dir"].map(key=>[key,draft[key].trim()])):{directory:draft.directory.trim(),action:draft.action};
  if(authoring&&draft.protocol.trim())parameters.protocol=draft.protocol.trim();
  if(!authoring&&draft.programme_request.trim())parameters.programme_request=draft.programme_request.trim();
  const report=await issue(authoring?"programme.prepare":"programme.review",parameters,{render:false,keepView:true});
  if(report&&draft===programmeDraft()&&revision===draft.revision){draft.review={...report,operation:authoring?"programme.author":"programme.apply"};renderProgramme();}
}
function renderProgramme(){$("result").replaceChildren();renderProgrammeFields();}
function renderProgrammeFields(){
  const draft=programmeDraft(),controls=node("div");controls.id="programme-controls";
  const intro=panel("Original programme and component requirements");intro.append(node("p","Prepare and operate a registered composite programme through its original service. Each component retains its own source, input, execution and reveal requirements. Review does not supply missing authority.","small-note"));controls.append(intro);
  const selected=panel("Inspect or continue an original programme"),fields=node("div",undefined,"design-fields");
  fields.append(designField("Original programme directory",draft.directory,value=>{draft.directory=value;invalidateProgramme(draft);}));
  const partial=node("label","Allow partial retained inspection","field"),checkbox=node("input");checkbox.type="checkbox";checkbox.checked=draft.allow_partial;checkbox.addEventListener("change",()=>{draft.allow_partial=checkbox.checked;invalidateProgramme(draft);});partial.append(checkbox);fields.append(partial,button("Inspect original programme",readProgramme));
  fields.append(designField("Copied component request file (optional; otherwise context selection)",draft.programme_request,value=>{draft.programme_request=value;invalidateProgramme(draft);}));
  const label=node("label","Selected operation","field"),choice=node("select");for(const [value,text] of [["RUN","Run selected programme"],["RECOVER","Recover original programme"]]){const option=node("option",text);option.value=value;option.selected=draft.action===value;choice.append(option);}choice.addEventListener("change",()=>{draft.action=choice.value;invalidateProgramme(draft);});label.append(choice);fields.append(label,button("Review programme operation",()=>reviewProgramme(false)));selected.append(fields);controls.append(selected);
  const preparation=panel("Prepare and author a new programme"),inputs=node("div",undefined,"design-fields");
  for(const [key,label] of [["input","Copied programme specification"],["sources","Canonical scientific input selection"],["source_snapshot","Original implementation snapshot"],["environment_id","Selected environment ID"],["protocol","Scientific protocol file (if required)"],["output_dir","New programme directory"]])inputs.append(designField(label,draft[key],value=>{draft[key]=value;invalidateProgramme(draft);}));
  inputs.append(button("Review programme preparation",()=>reviewProgramme(true)));preparation.append(inputs);controls.append(preparation);
  const review=panel("Current programme review"),reviewFields=node("div",undefined,"design-fields"),reviewed=node("div");reviewed.id="programme-review";
  if(draft.review)reviewed.append(node("p",`${draft.review.action} · reviewed, not entered`,"small-note"),node("p",draft.review.entry_conditions,"small-note"),details("Original preparation, dependencies and exact selections",draft.review));
  const apply=button(draft.review?.action==="AUTHOR"?"Author reviewed programme":draft.review?.action==="RECOVER"?"Recover reviewed programme":"Run reviewed programme",async()=>{const current=draft.review,revision=draft.revision;if(!current)return;draft.review=null;apply.disabled=true;clearProgrammeDisplay();const report=await issue(current.operation,{...current.selection,expected_review_sha256:current.review_sha256},{render:false,keepView:true});if(draft===programmeDraft()&&draft.revision===revision){draft.last=report;if(report?.report?.authoring_dir)draft.directory=report.report.authoring_dir;renderProgramme();}});apply.id="programme-apply";apply.disabled=!draft.review;reviewFields.append(reviewed,apply);review.append(reviewFields);controls.append(review);
  if(draft.last){const box=panel("Original operation result");box.id="programme-last";box.append(badge(draft.last.report?.status||draft.last.report?.state||draft.last.status),details("Original returned paths, component state and retained results",draft.last));controls.append(box);}
  $("result").append(controls);
}
function inquiryDraft() {
  const key=state.context.selection.value.context_id;
  if(!state.inquiryDrafts.has(key))state.inquiryDrafts.set(key,{input:"",output_dir:"",directory:"",successor_directory:"",historical:false,origins:"",initial_draft:"",supplier_directory:"",contribution_directory:"",text:"",author_output:"",revision:0,review:null,last:null});
  return state.inquiryDrafts.get(key);
}
function clearInquiryViews() {for(const draft of state.inquiryDrafts.values()){draft.review=null;draft.last=null;draft.revision++;}}
function clearInquiryDisplay() {
  for(const child of [...$("result").children])if(child.id!=="inquiry-controls")child.remove();
  state.last=null;state.page=null;closeInspector();$("read-stamp").textContent="Open the original decision for a current read.";
}
function invalidateInquiry(draft) {
  draft.revision++;draft.review=null;draft.last=null;
  if(state.pending){++state.generation;state.pending=false;$("open").disabled=false;$("session-state").textContent="Connected";message("Selections changed. The previous invocation retains its original request in Invocations.");}
  $("inquiry-apply")?.setAttribute("disabled","");$("inquiry-review")?.replaceChildren();$("inquiry-last")?.remove();clearInquiryDisplay();
}
async function readInquiry(operation,parameters) {
  const draft=inquiryDraft(),revision=draft.revision;clearInquiryDisplay();
  const report=await issue(operation,parameters,{render:false,keepView:true});
  if(report && draft===inquiryDraft() && revision===draft.revision){state.last={operation,parameters};state.page=report;render(report,operation);}
}
async function reviewInquiry(authoring) {
  const draft=inquiryDraft(),revision=draft.revision;draft.review=null;$("inquiry-apply").disabled=true;$("inquiry-review").replaceChildren();clearInquiryDisplay();
  const parameters=authoring?{directory:draft.directory.trim(),origins:draft.origins.trim(),output_dir:draft.author_output.trim(),text:draft.text}:{input:draft.input.trim(),output_dir:draft.output_dir.trim()};
  if(authoring)for(const key of ["initial_draft","supplier_directory","contribution_directory"])if(draft[key].trim())parameters[key]=draft[key].trim();
  const report=await issue(authoring?"inquiry.review-author":"inquiry.review",parameters,{render:false,keepView:true});
  if(report && draft===inquiryDraft() && revision===draft.revision){draft.review={...report,operation:authoring?"inquiry.author":"inquiry.commit"};renderInquiry();}
}
function renderInquiry() {$("result").replaceChildren();renderInquiryFields();}
function renderInquiryFields() {
  const draft=inquiryDraft(),controls=node("div");controls.id="inquiry-controls";
  const intro=panel("Recorded choices and admitted successors");intro.append(node("p","Review a typed inquiry request, commit the owner's decision, then author its exact initial or registered successor. These actions preserve original cutoffs, decision rights, work and input origins.","small-note"));controls.append(intro);
  const inspect=panel("Original decision and successor"),readFields=node("div",undefined,"design-fields");
  for(const [key,label] of [["directory","Original decision directory"],["successor_directory","Original successor directory (optional)"]])readFields.append(designField(label,draft[key],value=>{draft[key]=value;invalidateInquiry(draft);}));
  const historical=node("label","Read as historical archive without current admission","field"),check=node("input");check.type="checkbox";check.checked=draft.historical;check.addEventListener("change",()=>{draft.historical=check.checked;invalidateInquiry(draft);});historical.append(check);readFields.append(historical);
  const actions=node("div",undefined,"design-actions");actions.append(button("Inspect original decision",()=>{const parameters={directory:draft.directory.trim(),historical:draft.historical,limit:50};if(draft.successor_directory.trim()&&!draft.historical)parameters.successor_directory=draft.successor_directory.trim();readInquiry("inquiry.read",parameters);}),button("Inspect successor admission",()=>readInquiry("inquiry.successor",{directory:draft.successor_directory.trim(),limit:50})));readFields.append(actions);inspect.append(readFields);controls.append(inspect);
  const decision=panel("Review and commit a request"),decisionFields=node("div",undefined,"design-fields");
  for(const [key,label] of [["input","Canonical inquiry request file"],["output_dir","New decision directory"]])decisionFields.append(designField(label,draft[key],value=>{draft[key]=value;invalidateInquiry(draft);}));
  decisionFields.append(button("Review inquiry decision",()=>reviewInquiry(false)));decision.append(decisionFields);controls.append(decision);
  const author=panel("Author the selected successor"),authorFields=node("div",undefined,"design-fields");
  authorFields.append(node("p","Use the original decision above. Select either an initial draft or its completed supplier. The supplier route uses its installed builder and original contribution. Authoring retains admission; execution is a separate operation.","small-note"));
  for(const [key,label] of [["origins","Canonical input origins file"],["initial_draft","Initial draft file (initial route only)"],["supplier_directory","Completed supplier directory (successor route only)"],["contribution_directory","Original contribution directory (if required)"],["author_output","New successor authoring directory"]])authorFields.append(designField(label,draft[key],value=>{draft[key]=value;invalidateInquiry(draft);}));
  const bindings=designField("External inputs · one INPUT_ID=/absolute/path per line",draft.text,value=>{draft.text=value;invalidateInquiry(draft);},{multiline:true});bindings.querySelector("textarea").rows=5;bindings.querySelector("textarea").removeAttribute("aria-describedby");authorFields.append(bindings,button("Review successor authoring",()=>reviewInquiry(true)));author.append(authorFields);controls.append(author);
  const review=panel("Current review"),reviewFields=node("div",undefined,"design-fields"),reviewed=node("div");reviewed.id="inquiry-review";
  if(draft.review){reviewed.append(node("p",`${title(draft.review.status)} · selected action ${draft.review.decision.selected_action}`,"small-note"),details("Original alternatives, decision rights, unresolved requirements, costs and exact inputs",draft.review));}
  const apply=button(draft.review?.operation==="inquiry.author"?"Author reviewed successor":"Commit reviewed decision",async()=>{const current=draft.review,revision=draft.revision;if(!current)return;draft.review=null;apply.disabled=true;clearInquiryDisplay();const report=await issue(current.operation,{...current.selection,expected_review_sha256:current.review_sha256},{render:false,keepView:true});if(draft===inquiryDraft()&&draft.revision===revision){draft.last=report;if(report?.decision_directory)draft.directory=report.decision_directory;if(report?.authoring_dir)draft.successor_directory=report.authoring_dir;renderInquiry();}});apply.id="inquiry-apply";apply.disabled=!draft.review;reviewFields.append(reviewed,apply);review.append(reviewFields);controls.append(review);
  if(draft.last){const result=panel("Original returned result");result.id="inquiry-last";result.append(badge(draft.last.status),details("Recorded decision, original returned paths and admission",draft.last));controls.append(result);}
  $("result").append(controls);
}
function renderInquiryLinks(report) {
  const box=panel("Decision and successor custody");box.append(badge(report.admission_status),details("Original alternatives, unresolved conditions, rights, work and admission",report));
  if(report.successor){const actions=node("div",undefined,"design-actions");actions.append(button("Open parent decision",()=>readInquiry("inquiry.read",{directory:report.decision_directory,successor_directory:report.successor.directory,limit:50})),button("Open admitted successor",()=>readInquiry("inquiry.successor",{directory:report.successor.directory,limit:50})));box.append(actions);}
  $("result").append(box);
}
function rcDraft() {
  const key=state.context.selection.value.context_id;
  if(!state.drafts.has(key))state.drafts.set(key,{input:"",text:"",format:".json",original:null,validation:null,prepared:null,review:null,authored:null,canonical:"",destination:"",existing:"",last:null});
  return state.drafts.get(key);
}
function designField(label,value,onChange,{multiline=false}={}) {
  const field=node("label",label,"field");const input=node(multiline?"textarea":"input");input.value=value;input.spellcheck=false;input.autocomplete="off";
  if(multiline){input.rows=18;input.className="input-editor";input.setAttribute("aria-describedby","exact-edit-note");}
  input.addEventListener("input",()=>onChange(input.value));field.append(input);return field;
}
function invalidatePreparation(draft, {original=false}={}) {
  if(original)draft.original=null;
  draft.validation=null;draft.prepared=null;draft.review=null;
  for(const id of ["prepare-input","review-design","author-wave"])if($(id))$(id).disabled=true;
  $("reviewed-design")?.replaceChildren();
  if(original)$("original-input-binding")?.remove();
}
function renderDesign() {
  $("result").replaceChildren();const draft=rcDraft();
  const intro=panel("One bounded RC development wave");intro.append(node("p","Review copied input, prepare exact canonical bytes, then author and run the selected wave. Each action keeps its own input and source binding. This route supplies exposed development evidence.","small-note"));$("result").append(intro);
  const input=panel("01 · Copied input & exact edits");const fields=node("div",undefined,"design-fields");
  fields.append(designField("Copied input file",draft.input,value=>{draft.input=value;invalidatePreparation(draft,{original:true});}));
  const open=button("Open copied input",async()=>{const input=draft.input;const selected=await issue("configuration.open",{input},{render:false,keepView:true});if(selected && draft.input===input){Object.assign(draft,{original:selected,text:selected.text,format:selected.format,validation:null,prepared:null,review:null,last:selected.validation});renderDesign();}});
  open.disabled=!descriptor("configuration.open")?.browser_available;fields.append(open);
  const note=node("p","Decimal tags, units and source references stay as exact text. Validation does not write files. Editing invalidates the previous preparation.","small-note");note.id="exact-edit-note";fields.append(note);
  fields.append(designField("Editable input text",draft.text,value=>{draft.text=value;invalidatePreparation(draft);},{multiline:true}));
  const validate=button("Validate current edits",async()=>{const text=draft.text;const report=await issue("configuration.validate",{text,format:draft.format},{render:false,keepView:true});if(report && draft.text===text){draft.validation=report;draft.last=report;renderDesign();}});
  fields.append(validate);if(draft.original){const binding=details("Original copied bytes",{input:draft.original.input,input_sha256:draft.original.input_sha256,input_bytes:draft.original.input_bytes,consumer:draft.original.consumer});binding.id="original-input-binding";fields.append(binding);}
  fields.append(designField("New canonical input file",draft.canonical,value=>{draft.canonical=value;}));
  const prepare=button("Prepare new canonical file",async()=>{const text=draft.text,original=draft.original;const report=await issue("configuration.prepare",{input:original.input,expected_input_sha256:original.input_sha256,text,format:draft.format,expected_edit_sha256:draft.validation.input_sha256,output_file:draft.canonical},{render:false,keepView:true});if(report && draft.text===text && draft.original===original){draft.prepared=report;draft.review=null;draft.last=report;renderDesign();}});
  prepare.id="prepare-input";prepare.disabled=!draft.original||!draft.validation;fields.append(prepare);input.append(fields);$("result").append(input);
  const design=panel("02 · Preparation & source review");const designBody=node("div",undefined,"design-fields");
  const review=button("Review prepared design",async()=>{const selected=draft.prepared;const report=await issue("rc.prepare",{input:selected.output_file,expected_input_sha256:selected.output_sha256},{render:false,keepView:true});if(report && draft.prepared===selected){draft.review=report;draft.last=report;renderDesign();}});review.id="review-design";review.disabled=!draft.prepared;designBody.append(review);
  const reviewed=node("div");reviewed.id="reviewed-design";if(draft.review){const r=draft.review;reviewed.append(node("p",`${r.selected_operation_count} selected operations · ${r.requirement_count} requirements · ${r.connection_count} connections · ${r.maximum_parallel_tasks} selected workers`,"small-note"),details("Reviewed design, source and entry requirements",r));}designBody.append(reviewed);
  designBody.append(designField("New authoring directory",draft.destination,value=>{draft.destination=value;}));
  const author=button("Author reviewed wave",async()=>{const report=await issue("recursive.author",{input:draft.review.input,expected_input_sha256:draft.review.input_sha256,expected_implementation_sha256:draft.review.implementation_sha256,output_dir:draft.destination},{render:false,keepView:true});if(report){draft.authored=report;draft.existing=report.authoring_dir;draft.last=report;renderDesign();}});author.id="author-wave";author.disabled=!draft.review;designBody.append(author);design.append(designBody);$("result").append(design);
  const run=panel("03 · Original execution & recovery");const runBody=node("div",undefined,"design-fields");
  runBody.append(designField("Authored directory to inspect",draft.existing,value=>{draft.existing=value;draft.authored=null;for(const id of ["run-wave","recover-wave"])if($(id))$(id).disabled=true;}));
  runBody.append(button("Inspect authored wave",async()=>{const report=await issue("rc.design",{directory:draft.existing,limit:50},{render:false,keepView:true});if(report){draft.authored={authoring_dir:draft.existing,packet_sha256:report.identity.value.object_fingerprint};draft.last=report;renderDesign();}}));
  if(draft.authored)runBody.append(details("Selected immutable execution target",draft.authored));
  const actions=node("div",undefined,"design-actions");for(const [label,operation,id] of [["Run selected wave","recursive.run","run-wave"],["Recover original receipts","recursive.recover","recover-wave"]]){const action=button(label,async()=>{const selected=draft.authored;const report=await issue(operation,{directory:selected.authoring_dir,expected_packet_sha256:selected.packet_sha256,terminal_product_format:"documents"},{render:false,keepView:true});if(report){draft.last=report;renderDesign();}});action.id=id;action.disabled=!draft.authored;actions.append(action);}runBody.append(actions);
  runBody.append(node("p","Run and recovery use the original scheduler and contact records. A lost reply never retries work. Interruption is unavailable in this view; a browser close leaves the invocation running.","small-note"));
  if(draft.authored)runBody.append(button("Open original results",()=>{const path=draft.authored.authoring_dir;chooseSection("results");$("kind").value="rc";$("directory").value=path;openResult();}));run.append(runBody);$("result").append(run);
  if(draft.last){const result=panel("Last operation result");result.append(details("Complete returned values",draft.last));$("result").append(result);}
}
function renderInvocations() {
  disposeInvocations?.();const generation=state.generation;const box=panel("Retained invocation handles");box.append(node("p","Progress describes reported work. Reopen original results for scientific findings. Active observations refresh every two seconds while this view is visible. Reports older than ten seconds are marked stale.","small-note"));
  const rows=savedInvocations().filter(row=>row.context_id===state.context.selection.value.context_id);
  const selection=node("div",undefined,"design-fields");let supplied="";selection.append(designField("Original invocation handle",supplied,value=>{supplied=value.trim();}),button("Inspect original handle",()=>{if(!/^[0-9a-f]{64}$/.test(supplied)){showError("Enter the complete original invocation handle.");return;}rememberInvocation({handle:supplied,context_id:state.context.selection.value.context_id,operation:"Original selected invocation"});$("result").replaceChildren();renderInvocations();}));box.append(selection);
  if(!rows.length)box.append(node("p","No invocation handle is saved for this context in this browser.","small-note"));
  $("result").append(box);
  disposeInvocations=mountInvocationProgress(box,rows,async(row,signal)=>{
    const response=await fetchJSON("/api/invocation-state",{context_id:row.context_id,handle:row.handle},signal);
    if(response.status!=="SUCCEEDED")throw new Error(response.errors?.map(errorExplanation).join(" · ")||response.status);
    return response.payload;
  },()=>generation===state.generation&&!document.hidden&&state.section==="invocations");
}
function selectContext() {
  clearKnowledgeDraftViews();clearInquiryViews();clearProgrammeViews();
  for(const draft of state.drafts.values()){draft.last=null;draft.review=null;draft.authored=null;}
  ++state.generation;state.pending=false;$("open").disabled=false;$("session-state").textContent="Connected"; state.context=state.contexts.find(row=>row.selection.value.context_id===$("context").value);state.last=null;$("directory").value="";clearResult();
  if(state.context.error)showError(state.context.error.errors?.map(errorExplanation).join(" · ")||"The selected engine is unavailable.");
  else {$("error").hidden=true;$("message").hidden=true;}
  clearTimeout(state.polling);if(state.section==="context")renderContext();else if(state.section==="workflows")issue("workflow.list",{limit:20});else if(state.section==="invocations")renderInvocations();else if(state.section==="design")renderDesign();else if(state.section==="knowledge")renderKnowledge();else if(state.section==="inquiry")renderInquiry();else if(state.section==="programme")renderProgramme();else renderEmpty();
  state.presentations=[];$("panel").replaceChildren();if(state.section==="results"&&$("kind").value==="presentation")loadPresentations();
}
async function loadPresentations(){
  sourceFields();
  $("panel-field").hidden=$("kind").value!=="presentation"||state.section!=="results";
  if($("kind").value!=="presentation")return;
  state.presentations=[];$("panel").replaceChildren();
  const result=await issue("presentation.list",{limit:200},{render:false,keepView:true});
  if(!result)return;
  state.presentations=result.page.rows;
  for(const row of state.presentations){const option=node("option",row.title+" · "+row.version);option.value=row.panel_id;$("panel").append(option);}
}
function sourceFields(){
  $("source-window-fields").hidden=state.section!=="results"||$("kind").value!=="continuing.session";
  $("source-request-field").hidden=state.section!=="results"||$("kind").value!=="continuing.operation";
}
for(const section of ["results","design","programme","inquiry","knowledge","workflows","invocations","context"])$("nav-"+section).addEventListener("click",()=>chooseSection(section));
$("open").addEventListener("click",openResult);$("directory").addEventListener("keydown",event=>{if(event.key==="Enter")openResult();});$("context").addEventListener("change",selectContext);
$("kind").addEventListener("change",()=>{++state.generation;state.pending=false;$("open").disabled=false;$("session-state").textContent="Connected";clearResult();state.last=null;renderEmpty();loadPresentations();});$("close-inspector").addEventListener("click",closeInspector);
$("panel").addEventListener("change",()=>{++state.generation;state.pending=false;$("open").disabled=false;$("session-state").textContent="Connected";clearResult();state.last=null;renderEmpty();});
document.addEventListener("keydown",event=>{if(event.key==="Escape")closeInspector();});
document.addEventListener("visibilitychange",()=>{if(document.hidden){clearKnowledgeDraftViews();clearInquiryViews();clearProgrammeViews();clearTimeout(state.polling);for(const draft of state.drafts.values()){draft.last=null;draft.review=null;draft.authored=null;}++state.generation;state.pending=false;$("open").disabled=false;$("session-state").textContent="Connected";clearResult();message("The retained view was cleared while this tab was inactive. Open it again for a current read. Durable handles remain in Invocations.");}else if(state.section==="design")renderDesign();else if(state.section==="knowledge")renderKnowledge();else if(state.section==="inquiry")renderInquiry();else if(state.section==="programme")renderProgramme();else if(state.section==="invocations")renderInvocations();});
try {
  if(!token)throw new Error("Open the session URL printed by the local workbench launcher.");
  const configuration=await fetchJSON("/api/context");state.contexts=configuration.contexts;$("contract-version").textContent=configuration.application_version;$("context").replaceChildren();for(const row of state.contexts){const value=node("option",row.selection.value.label);value.value=row.selection.value.context_id;$("context").append(value);}$("context").disabled=false;state.context=state.contexts[0];$("session-state").textContent="Connected";if(state.context.error)showError(state.context.error.errors?.map(errorExplanation).join(" · ")||"The selected engine is unavailable.");
} catch(error) {$("session-state").textContent="Unavailable";$("open").disabled=true;showError(error.message);}
