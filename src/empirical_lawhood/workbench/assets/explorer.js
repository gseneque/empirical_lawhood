/* SPDX-License-Identifier: MPL-2.0 */
import {$,esc,action,pill,note,recordDetails,narrow,fingerprint,unpack,human} from './explorer-core.js';
import {ApplicationTransport,StaleView} from './explorer-transport.js';
import {layoutConnections,motif,svgStart} from './explorer-geometry.js';
import {investigationCanvas,bounds} from './explorer-diagrams.js';
import {results,knowledge,selectedKnowledgeDetail} from './explorer-collection.js';
import {investigationBrief,inspector,costDetails,questionReadouts} from './explorer-details.js';
import {activity,shouldRefresh} from './explorer-activity.js';

const state={view:'results',selectionId:null,branch:'overview',selected:'0',expanded:null,depth:0,caseIndex:0,tab:'question',outline:narrow(),lens:'programme',
  graphPage:0,groupPage:0,relationPage:0,query:'',programme:'all',filter:'all',collection:null,neighbourhood:null,entry:null,body:null,companions:null,observation:null,localExecution:null,
  observing:false,observed:new Map(),unavailable:new Map(),readerIndex:0};
const transport=new ApplicationTransport(status);
let pollTimer=null,renderFrame=0,lastFocus=null,download=null,observationEpoch=0;
function status(text) {$('#notice').textContent=text;$('#notice').hidden=!text;}
function clearError() {$('#error').textContent='';$('#error').hidden=true;}
function stopObservation() {observationEpoch++;clearTimeout(pollTimer);pollTimer=null;state.observing=false;}
function clearScientific() {
  stopObservation();state.body=null;state.companions=null;state.observation=null;state.localExecution=null;state.observed.clear();
  closeModal();download=null;
}
function closeModal() {$('#modal').close();$('#modal-body').replaceChildren();download=null;}
function modal(title,content,kicker='ORIGINAL RECORD') {
  lastFocus=document.activeElement;$('#modal-title').textContent=title;$('#modal-kicker').textContent=kicker;$('#modal-body').innerHTML=content;
  if(!$('#modal').open)$('#modal').showModal();$('#modal-close').focus();
}
function exactModal(title,result) {
  const raw=result.canonical_text||result.source_text||result.original_text||JSON.stringify(result,null,2)+'\n';
  download={text:raw,name:result.source_path?.split('/').at(-1)||'original-record.json'};
  modal(title,`${recordDetails('Read scope and source identity',Object.fromEntries(Object.entries(result).filter(([key])=>!['canonical_text','source_text','original_text','record'].includes(key))))}<pre tabindex="0">${esc(raw)}</pre><div class="modal-actions">${action('download','','Export exact displayed bytes')}</div>`);
}
async function run(work) {
  clearError();
  try {await work();}
  catch(error) {
    if(error instanceof StaleView)return;
    clearScientific();if(state.selectionId)state.unavailable.set(state.selectionId,error.message);
    $('#error').textContent=error.message;$('#error').hidden=false;status('Original data cleared. Select a fresh permitted read.');render();
  }
}
function navDocument() {return {view:state.view,selectionId:state.selectionId,branch:state.branch,selected:state.selected,expanded:state.expanded,depth:state.depth,
  caseIndex:state.caseIndex,tab:state.tab,outline:state.outline,lens:state.lens,graphPage:state.graphPage,groupPage:state.groupPage};}
function rememberNavigation(replace=false) {
  const nav=navDocument();history[replace?'replaceState':'pushState'](nav,'',`#${nav.view}/${encodeURIComponent(nav.selectionId||'')}/${nav.view==='knowledge'?nav.lens:nav.branch}`);
  // Only navigation choices survive a new page. Bodies, locators, access and
  // engine capabilities must always come from a fresh permitted session.
  localStorage.setItem('el-explorer-navigation',JSON.stringify({version:1,contextId:transport.context?.selection.value.context_id,nav}));
}
function navigate(patch,{push=true,focus=false}={}) {
  if(patch.view && patch.view!==state.view)stopObservation();
  Object.assign(state,patch);rememberNavigation(!push);render();if(focus)$('#main').focus({preventScroll:true});
}
function selectionRows() {return state.collection?.page.rows||state.neighbourhood?.page.rows||[];}
function selectionRow() {return selectionRows().find(row=>row.selection_id===state.selectionId)||state.entry?.value;}
function current() {
  const body=state.body,selected=selectionRow();
  if(!body)return `<div class="page-intro"><div class="intro-text"><p class="eyebrow">CURRENT EXPERIMENT</p><h1>${esc(selected?.question||'Choose a question to explore.')}</h1><p class="intro-summary">${selected?'This is a registered operator selection. Open the original result for its current scientific findings.':'Select an investigation from Results. Original paths and older engines remain available in Tools.'}</p></div></div>${selected?action('open',selected.selection_id,'Open original question and summary','primary-action'):action('view','results','Browse Results','primary-action')}${state.entry?activity(state):''}`;
  const selection=body.selection,view=body.exploration;
  const graph=view?investigationCanvas(view,state):`<div class="canvas-toolbar"><div class="breadcrumbs">${action('view','results','Results')}<span>/</span>${esc(selection?.label||body.title)}</div>${action('record','projection','Read exact projection ↗','quiet-button')}</div><div class="canvas">${svgStart('Original retained finding',360)}${motif(380,130,74,'@finding',[selection?.label||'Original investigation'],human(body.scope),'open','motif')}</svg></div>${note(body.value_semantics||body.scope)}`;
  return `<div class="page-intro"><div class="intro-text"><p class="eyebrow">${esc(selection?.classification?.programmes.map(row=>row.label).join(' / ')||'ORIGINAL INVESTIGATION')}</p><h1>${esc(view?.question||selection?.question||body.title)}</h1><p class="intro-summary">${esc(body.value_semantics||body.scope)}</p></div><div class="intro-aside">${pill(view?.summary.joint_outcome||body.summary?.execution_status||'ORIGINAL_SCOPE')}<p>${esc(selection?.label||'Selected original')}</p></div></div>${investigationBrief(body,state.companions)}<div class="workspace"><section class="canvas-column" aria-label="Investigation relationships">${graph}${state.companions?.companions.inquiry?`<div class="frontier"><span class="frontier-icon">↳</span><div><strong>Recorded next decision: ${esc(human(state.companions.companions.inquiry.summary.selected_action))}</strong><p>The original decision retains its own cutoff, reasons and authority.</p></div>${action('companion','inquiry','Inspect decision ↗')}</div>`:''}${questionReadouts(view)}</section>${inspector(state)}</div>${activity(state)}`;
}
function render() {
  const focus=document.activeElement,restore=$('#main').contains(focus)?{...focus.dataset}:null;
  document.querySelectorAll('[data-view]').forEach(button=>{if(button.dataset.view===state.view)button.setAttribute('aria-current','page');else button.removeAttribute('aria-current');});
  $('#context-note').textContent=state.view==='current'?(state.body?'Original scientific read · current access checked':'Select an original read'):'Selected collection · no automatic scientific reads';
  let content;
  if(state.view==='results')content=results(state);
  else if(state.view==='knowledge') {
    const row=state.neighbourhood?.page.rows.find(row=>row.selection_id===state.selectionId);
    const same=state.body && fingerprint(state.body.identity)===fingerprint(row?.identity);
    content=knowledge(state,same?inspector(state):inspector(state,{title:row?.label||'Select an investigation',content:selectedKnowledgeDetail(row,state)}));
  } else content=current();
  $('#main').innerHTML=content;
  for(const button of document.querySelectorAll('[data-action="outline"]'))button.setAttribute('aria-pressed',String((button.dataset.value==='true')===state.outline));
  $('#footer-scope').textContent=state.body?`Original scope: ${state.body.scope}`:'Collection metadata · no scientific result open';
  document.title=`EL · ${state.view==='current'?selectionRow()?.label||'Current experiment':state.view==='results'?'Results':'Knowledge'}`;
  if(restore?.action)document.querySelectorAll('[data-action]').forEach(element=>{if(element.dataset.action===restore.action&&element.dataset.value===restore.value)element.focus({preventScroll:true});});
  document.fonts.ready.then(()=>requestAnimationFrame(route));
}
function route() {
  const start=performance.now();
  try {layoutConnections();$('#main').dataset.routingMilliseconds=(performance.now()-start).toFixed(2);}
  catch(error) {
    // A bounded outline always retains every visible scientific relationship.
    if(!state.outline){state.outline=true;render();status('This neighbourhood has no clear diagram route. The complete outline is available.');}
    else {$('#error').textContent=error.message;$('#error').hidden=false;}
  }
}
async function collection(cursor) {
  status('Reading the selected collection…');
  const value=await transport.request('collection.list',{limit:200,...(cursor?{cursor}:{})});
  if(state.body && value.summary.collection_sha256!==state.body.current_reader?.collection_sha256)clearScientific();
  state.collection=value;state.neighbourhood=null;status('');render();
}
async function neighbourhood(cursor) {
  status('Reading the bounded Knowledge window…');
  state.neighbourhood=await transport.request('collection.neighbourhood',{limit:16,...(cursor?{cursor}:{})});
  state.groupPage=0;status('');render();
}
async function openOriginal(id,readerIndex=0,{activityOnly=false}={}) {
  stopObservation();transport.clear();clearScientific();state.selectionId=id;state.view='current';state.readerIndex=readerIndex;
  state.branch='overview';state.tab='question';state.graphPage=0;state.relationPage=0;state.depth=0;rememberNavigation();render();
  status('Resolving the registered original and its selected engine…');
  let entry=(await transport.request('collection.entry',{selection_id:id})).entry;
  const reader=entry.value.readers[readerIndex],contextId=activityOnly?entry.value.context_id:reader?.context_id||entry.value.context_id;
  if(!transport.contexts.some(row=>row.selection.value.context_id===contextId))throw new Error('The original engine context is not available in this session. Select it through the launcher.');
  if(contextId!==transport.context.selection.value.context_id){transport.select(contextId);$('#context').value=contextId;}
  state.entry=entry;render();
  if(activityOnly){status('');await observe();return;}
  const body=await transport.request('exploration.read',{selection_id:id,reader_index:readerIndex,limit:200});
  state.body=body;
  if(body.exploration)state.selected=String(body.exploration.nodes.findIndex(row=>row.id===body.exploration.root_id));
  if(body.selection?.companion_roles.some(role=>['inquiry','work-cost','acquisition','cost-observations'].includes(role))) {
    status('Joining the selected original decision and work account…');
    state.companions=await transport.request('exploration.summary',{selection_id:id,reader_index:readerIndex});
  }
  state.unavailable.delete(id);
  const summary=body.exploration?.summary||body.summary||{};
  const outcome=summary.joint_outcome||(summary.dispositions?'MIXED_ASSESSMENTS':summary.scientific_completion||summary.execution_status||'ORIGINAL_SCOPE');
  state.observed.set(id,{disposition:outcome,text:body.value_semantics||body.scope,observed_at:body.current_reader.observed_at_utc,identity:body.identity});
  status('');render();$('#announcement').textContent='Opened '+entry.value.label;
}
async function exactRecord(value) {
  if(!state.body)throw new Error('Open the original result before exact inspection.');
  stopObservation();status('Reopening the exact original record…');
  const recordId=/^\d+$/.test(value)?state.body.exploration?.nodes[Number(value)]?.id:value;
  const result=await transport.request('exploration.record',{selection_id:state.selectionId,reader_index:state.readerIndex,record_id:recordId});
  status('');exactModal('Exact original record',result);
}
async function companion(role) {
  stopObservation();status('Reopening the selected original companion…');
  const result=await transport.request('exploration.companion',{selection_id:state.selectionId,reader_index:state.readerIndex,role});
  const selected=result.companions[role];status('');exactModal(human(role),selected);
}
async function sourceReference(value,protocol=false) {
  stopObservation();const [id,index]=value.split('|'),method=state.body?.exploration?.methods.find(row=>row.id===id);
  if(!method)throw new Error('Open a declared method first.');
  const path=protocol?method.guides[Number(index)]:method.sources[Number(index)].path;
  const result=await transport.request('exploration.method',{selection_id:state.selectionId,reader_index:state.readerIndex,method_id:id,source_path:path});
  status('');exactModal(protocol?'Scientific protocol · current selected reader':'Method source · current selected reader',result);
}
function renderActivity() {
  const box=$('.activity-panel');if(!box){render();return;}
  const open=[...box.querySelectorAll('details[open]')].map(item=>item.querySelector('summary')?.textContent);
  const focus=box.contains(document.activeElement)?{...document.activeElement.dataset}:null;
  const replacement=document.createElement('div');replacement.innerHTML=activity(state);box.replaceWith(...replacement.childNodes);
  for(const item of document.querySelectorAll('.activity-panel details'))if(open.includes(item.querySelector('summary')?.textContent))item.open=true;
  if(focus?.action)document.querySelectorAll('.activity-panel [data-action]').forEach(button=>{if(button.dataset.action===focus.action)button.focus({preventScroll:true});});
}
async function observe() {
  clearTimeout(pollTimer);
  if(document.hidden||state.view!=='current')return;
  if(transport.pending){status('A read is already in flight. Its result will arrive through the original request.');return;}
  const selected=state.body?.selection||state.entry?.value;if(!selected)return;
  if(selected.deployment&&state.entry?.value.context_id!==transport.context.selection.value.context_id) {
    await openOriginal(state.selectionId,0,{activityOnly:true});return;
  }
  const epoch=observationEpoch;
  state.observing=true;
  const observed=selected.deployment?await transport.request('observation.read',{selection_id:state.selectionId}):
    await transport.request('exploration.execution',{selection_id:state.selectionId,reader_index:state.readerIndex,limit:200});
  if(epoch!==observationEpoch)return;
  if(selected.deployment)state.observation=observed;else state.localExecution=observed;
  const active=selected.deployment?shouldRefresh(state.observation):!['SUCCEEDED','FAILED','CANCELLED','INTERRUPTED'].includes(state.localExecution.summary.execution_status);
  state.observing=active;renderActivity();
  if(active) {
    const delay=Math.max(10000,(state.observation?.snapshot?.cadence_seconds||10)*1000),generation=transport.generation,id=state.selectionId;
    pollTimer=setTimeout(()=>{if(generation!==transport.generation||id!==state.selectionId||document.hidden||state.view!=='current')return;
      if(transport.pending){pollTimer=setTimeout(()=>run(observe),delay);return;}run(observe);},delay);
  }
}
async function dispatch(name,value) {
  if(name==='view') {
    if(value!==state.view){transport.clear();navigate({view:value},{focus:true});}
    if(transport.pending){status('A read is in flight. Its original handle remains available in Tools → Invocations.');return;}
    if(value==='results'&&!state.collection)await collection();
    if(value==='knowledge'&&!state.neighbourhood)await neighbourhood();return;
  }
  if(name==='collection'||name==='collection-next'){await collection(value||undefined);return;}
  if(name==='neighbourhood'||name==='neighbourhood-next'){await neighbourhood(value||undefined);return;}
  if(name==='open'){await openOriginal(value);return;}
  if(name==='open-activity'){await openOriginal(value,0,{activityOnly:true});return;}
  if(name==='tab'){navigate({tab:value},{push:false});$(`#tab-${value}`)?.focus({preventScroll:true});return;}
  if(name==='branch'){navigate({branch:value,graphPage:0,depth:0});return;}
  if(name==='node') {
    if(value.startsWith('@')){if(['@physical','@contrasts'].includes(value))navigate({branch:value.slice(1),graphPage:0});else navigate({tab:'finding'},{push:false});return;}
    navigate({selected:value,tab:'question'});$('#announcement').textContent='Selected '+state.body?.exploration?.nodes[Number(value)]?.label;return;
  }
  if(name==='expand') {
    if(state.depth>=bounds.depth){navigate({branch:'all',outline:true});status('The eight-level expansion bound was reached. All original requirements remain in the outline.');return;}
    navigate({branch:'node',expanded:value,depth:state.depth+1,graphPage:0});return;
  }
  if(name==='case'){navigate({caseIndex:Number(value),graphPage:0});return;}
  if(name==='outline'){navigate({outline:value==='true'},{push:false});return;}
  if(name==='graph-page'){navigate({graphPage:Number(value)});return;}
  if(name==='group-page'){navigate({groupPage:Number(value)});return;}
  if(name==='lens'){navigate({lens:value,groupPage:0});return;}
  if(name==='scientific-page'){navigate({relationPage:Number(value)});return;}
  if(name==='scientific-relationship'){
    const edge=state.body?.exploration?.edges[Number(value)];if(!edge)return;
    modal(human(edge.kind),recordDetails('Original relationship, direction, scope and source',edge),'ORIGINAL RELATIONSHIP');return;
  }
  if(name==='knowledge'){
    if(state.selectionId!==value){transport.clear();clearScientific();state.entry=null;}
    navigate({selectionId:value,tab:'question'});return;
  }
  if(name==='relationship'){const edge=state.neighbourhood.relationships[Number(value)];modal(human(edge.kind),`<p>${esc(edge.label)}</p>${recordDetails('Original reference, direction and stated scope',edge)}${note('This editorial reference supplies no scientific operand or destination admission.')}`,'RELATIONSHIP');return;}
  if(name==='record'){await exactRecord(value);return;}
  if(name==='companion'){await companion(value);return;}
  if(name==='method-source'||name==='method-guide'){await sourceReference(value,name==='method-guide');return;}
  if(name==='costs'){stopObservation();modal('Work, costs and comparison',costDetails(state.companions),'ORIGINAL WORK ACCOUNT');return;}
  if(name==='observe'){await observe();return;}
  if(name==='pause-observation'){stopObservation();renderActivity();return;}
  if(name==='open-return') {
    const readers=state.entry?.value.readers||[];
    if(readers.length<2){status('No additional returned-local original locator is registered. The terminal handoff must attach it before this read.');return;}
    modal('Select a returned original',`<ul class="selection-list">${readers.map((row,i)=>`<li>${action('return-reader',i,`<strong>${esc(row.operation)}</strong><small>${esc(row.context_id||state.entry.value.context_id)} · reader ${i+1}</small>`)}</li>`).join('')}</ul>`,'REGISTERED ORIGINAL LOCATORS');return;
  }
  if(name==='return-reader'){closeModal();await openOriginal(state.selectionId,Number(value));return;}
  if(name==='original-next') {
    stopObservation();state.body=await transport.request('exploration.read',{selection_id:state.selectionId,reader_index:state.readerIndex,limit:200,cursor:value});render();return;
  }
  if(name==='download'&&download) {
    const url=URL.createObjectURL(new Blob([download.text],{type:'text/plain;charset=utf-8'})),link=document.createElement('a');
    link.href=url;link.download=download.name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);return;
  }
}
document.addEventListener('click',event=>{
  const view=event.target.closest('[data-view]');if(view){run(()=>dispatch('view',view.dataset.view));return;}
  const button=event.target.closest('[data-action]');if(button){run(()=>dispatch(button.dataset.action,button.dataset.value||''));return;}
  const object=event.target.closest('[data-knowledge]');if(object){run(()=>dispatch('knowledge',object.dataset.knowledge));return;}
  const selected=event.target.closest('[data-node]');if(selected)run(()=>dispatch('node',selected.dataset.node));
});
document.addEventListener('keydown',event=>{
  const selected=event.target.closest('[data-node],[data-knowledge]');
  if(selected&&['Enter',' '].includes(event.key)){event.preventDefault();run(()=>dispatch(selected.dataset.knowledge?'knowledge':'node',selected.dataset.knowledge||selected.dataset.node));}
  if(event.target.matches('[role=tab]')&&['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) {
    event.preventDefault();const tabs=['question','finding','evidence','method'],i=tabs.indexOf(state.tab),next=event.key==='Home'?0:event.key==='End'?3:(i+(event.key==='ArrowRight'?1:3))%4;
    run(()=>dispatch('tab',tabs[next]));
  }
});
document.addEventListener('input',event=>{
  if(event.target.id==='search'){const position=event.target.selectionStart;state.query=event.target.value;render();$('#search').focus();$('#search').setSelectionRange(position,position);}
});
document.addEventListener('change',event=>{
  if(event.target.id==='programme-filter'){state.programme=event.target.value;render();}
  if(event.target.id==='disposition-filter'){state.filter=event.target.value;render();}
});
$('#context').addEventListener('change',()=>run(async()=>{
  transport.select($('#context').value);clearScientific();state.entry=null;state.collection=null;state.neighbourhood=null;state.selectionId=null;state.unavailable.clear();state.view='results';render();
  rememberNavigation(true);
  if(!transport.pending)await collection();else status('The previous read continues independently. Read this selected collection when it returns.');
}));
$('#source-button').addEventListener('click',()=>modal('Selected engine and original source',`${recordDetails('Current engine capability negotiation',transport.context?.engine)}${recordDetails('Original producing source',state.body?.provenance||null)}${note('Current reader, original producer and future worker identities remain distinct. No current GPU allocation or provider credential is supplied by this session.')}`,'SOURCE & SESSION'));
$('#modal-close').addEventListener('click',closeModal);
$('#modal').addEventListener('close',()=>{download=null;if(lastFocus?.isConnected)lastFocus.focus({preventScroll:true});});
window.addEventListener('popstate',event=>{
  transport.clear();stopObservation();if(event.state){Object.assign(state,event.state);if(state.body?.selection?.selection_id!==state.selectionId)clearScientific();render();}
});
document.addEventListener('visibilitychange',()=>{
  if(document.hidden){transport.clear();clearScientific();state.collection=null;state.neighbourhood=null;state.entry=null;render();status('The retained view was cleared while this tab was inactive. Open the selected original again for a current read.');}
});
window.addEventListener('resize',()=>{cancelAnimationFrame(renderFrame);renderFrame=requestAnimationFrame(route);});
matchMedia('(max-width:760px)').addEventListener('change',()=>{if(innerWidth>=160){state.outline=narrow();render();}});
await run(async()=>{
  const config=await transport.connect();$('#contract-version').textContent='Application '+config.application_version;
  $('#context').innerHTML=config.contexts.map(row=>`<option value="${esc(row.selection.value.context_id)}">${esc(row.selection.value.label)}${row.error?' · unavailable':''}</option>`).join('');$('#context').disabled=false;
  let saved;
  try {saved=JSON.parse(localStorage.getItem('el-explorer-navigation')||'null');} catch {}
  if(saved?.version===1&&config.contexts.some(row=>row.selection.value.context_id===saved.contextId)) {
    transport.select(saved.contextId);$('#context').value=saved.contextId;
    const nav=saved.nav||{};
    for(const [name,allowed] of Object.entries({view:['current','results','knowledge'],branch:['overview','physical','contrasts','suppliers','all','node'],
      tab:['question','finding','evidence','method'],lens:['programme','discipline']}))if(allowed.includes(nav[name]))state[name]=nav[name];
    if(typeof nav.selectionId==='string'&&/^[A-Za-z0-9_.:-]{1,192}$/.test(nav.selectionId))state.selectionId=nav.selectionId;
    if(typeof nav.outline==='boolean')state.outline=narrow()||nav.outline;
    for(const name of ['graphPage','groupPage','caseIndex','depth'])if(Number.isInteger(nav[name])&&nav[name]>=0&&nav[name]<=4096)state[name]=nav[name];
    for(const name of ['selected','expanded'])if(typeof nav[name]==='string'&&/^\d{1,4}$/.test(nav[name]))state[name]=nav[name];
  }
  const [view,id,lens]=location.hash.slice(1).split('/');
  if(['current','results','knowledge'].includes(view))state.view=view;
  if(id)state.selectionId=decodeURIComponent(id);if(['programme','discipline'].includes(lens))state.lens=lens;
  rememberNavigation(true);await collection();if(state.view==='knowledge')await neighbourhood();
});
