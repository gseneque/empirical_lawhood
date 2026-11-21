/* SPDX-License-Identifier: MPL-2.0 */
import {esc,action,pill,lines,note,recordDetails,fingerprint} from './explorer-core.js';
import {recursiveMark,svgStart,routeShape,connection} from './explorer-geometry.js';

function observed(row,state) {return state.observed.get(row.selection_id);}
function disposition(row,state) {return observed(row,state)?.disposition || (state.unavailable.get(row.selection_id)?'UNAVAILABLE':'NOT_READ');}
function selectedRows(state) {
  return (state.collection?.page.rows||[]).filter(row=>{
    const search=[row.label,row.question,...row.classification.programmes.map(group=>group.label)].join(' ').toLowerCase();
    const outcome=disposition(row,state);
    return search.includes(state.query.toLowerCase()) && (state.programme==='all'||row.classification.programmes.some(group=>group.id===state.programme)) &&
      (state.filter==='all'||state.filter==='unread'&&outcome==='NOT_READ'||state.filter==='unavailable'&&outcome==='UNAVAILABLE'||
        state.filter==='adverse'&&/FALSIF|REFUT|CONTRADICT|ADVERSE|MIXED/.test(outcome)||state.filter==='unresolved'&&/UNRESOLVED|UNEVALUABLE|OPEN/.test(outcome));
  });
}
export function results(state) {
  const collection=state.collection;
  if(!collection)return `<div class="empty-state"><h1>Open your selected investigations</h1><p>The collection contains registered original locators. Each investigation is read through its own engine.</p>${action('collection','','Read selected collection','primary-action')}<p><a href="/tools.html">Open an original path or an older engine in Tools ↗</a></p></div>`;
  const rows=selectedRows(state),programmes=new Map();
  for(const row of collection.page.rows)for(const group of row.classification.programmes)programmes.set(group.id,group.label);
  return `<div class="page-intro"><div class="intro-text"><p class="eyebrow">RETAINED INVESTIGATIONS</p><h1>Questions, findings and the work behind them.</h1><p class="intro-summary">Open an original result to inspect its current evidence. Unread entries retain their operator labels.</p></div></div><div class="results-tools"><label class="search-box"><span class="sr-only">Search investigations</span><input id="search" type="search" placeholder="Search a question or programme" value="${esc(state.query)}"></label><label class="filter-field"><span class="sr-only">Programme filter</span><select id="programme-filter"><option value="all">All programmes</option>${[...programmes].map(([id,label])=>`<option value="${esc(id)}"${state.programme===id?' selected':''}>${esc(label)}</option>`).join('')}</select></label><label class="filter-field"><span class="sr-only">Disposition filter</span><select id="disposition-filter">${[['all','All dispositions'],['unread','Not read'],['unresolved','Unresolved'],['adverse','Adverse / mixed'],['unavailable','Unavailable']].map(([id,label])=>`<option value="${id}"${state.filter===id?' selected':''}>${label}</option>`).join('')}</select></label>${action('collection','','Refresh collection','quiet-button')}</div><p class="collection-coverage">${rows.length} visible / ${collection.page.returned_count} in this page / ${collection.page.total} known entries. Filters do not change the original denominator.</p><div class="result-list">${rows.map(row=>{
    const read=observed(row,state),status=disposition(row,state);
    return `<article class="result-row" data-selection="${esc(row.selection_id)}"><div class="result-mark" aria-hidden="true"><img src="/el-equal-circles.svg" alt="" width="60" height="47"></div><div class="result-main"><p class="result-programme">${esc(row.classification.programmes.map(group=>group.label).join(' · ')||'Unclassified')}</p>${action('open',row.selection_id,`<h2>${esc(row.question)}</h2>`,'result-question')}<p>${esc(read?.text || row.label)}</p><small>${read?`Original read ${esc(read.observed_at)}`:'Operator selection · original finding not read in this view'}</small>${row.deployment?action('open-activity',row.selection_id,'Observe registered work ↗','brief-link'):''}${state.unavailable.has(row.selection_id)?`<p class="row-error">${esc(state.unavailable.get(row.selection_id))}</p>`:''}</div><div class="result-state">${pill(status)}<small>${row.identity?'Original identity selected':'Authored / pending result'}</small></div>${action('open',row.selection_id,'<span aria-hidden="true">↗</span><span class="sr-only">Open investigation</span>','result-open')}</article>`;
  }).join('')||'<div class="empty-state"><h2>No entries in this filter.</h2><p>The original collection and its complete count remain unchanged.</p></div>'}</div>${collection.page.next_cursor?action('collection-next',collection.page.next_cursor,'Next collection page →','primary-action'):''}`;
}
function groups(state) {
  const axis=state.lens==='programme'?'programmes':'disciplines',groups=new Map();
  for(const row of state.neighbourhood?.page.rows||[]) {
    let memberships=row.classification[axis];
    if(row.classification_status!=='PIN_VERIFIED')memberships=[{id:'source-unavailable',label:'Classification unavailable'}];
    else if(!memberships.length)memberships=[{id:'unclassified',label:'Unclassified'}];
    for(const group of memberships) {
      if(!groups.has(group.id))groups.set(group.id,{...group,rows:[]});
      groups.get(group.id).rows.push(row);
    }
  }
  return [...groups.values()];
}
function knowledgeNode(row,x,y,r,state) {
  const selected=state.selectionId===row.selection_id,mark=disposition(row,state);
  return `<g class="graph-node knowledge-object${selected?' selected':''}" role="button" tabindex="0" data-knowledge="${esc(row.selection_id)}" aria-label="${esc(row.label+'. '+mark)}"><circle class="node-hit" cx="${x}" cy="${y}" r="${r+5}"/><circle class="ring open" cx="${x}" cy="${y}" r="${r}"/>${recursiveMark(x,y-29,60)}${lines(row.label,16,2).map((line,i)=>`<text class="node-label" x="${x}" y="${y+6+i*17}" text-anchor="middle">${esc(line)}</text>`).join('')}<text class="node-caption" x="${x}" y="${y+44}" text-anchor="middle">${esc(mark==='NOT_READ'?'Open original':mark.length>17?'Inspect disposition':mark.toLowerCase())}</text></g>`;
}
function graph(state,all) {
  const selected=all.slice((state.groupPage||0)*4,(state.groupPage||0)*4+4),height=selected.length>2?850:430;
  let svg=svgStart(`Knowledge by ${state.lens}; source-backed editorial groups`,height,950);
  const membership=new Map();
  selected.forEach((group,i)=>group.rows.forEach(row=>{if(!membership.has(row.selection_id))membership.set(row.selection_id,i);}));
  // One visual link per group pair. Its complete original relationship records
  // remain below the map, including links outside this finite window.
  const connected=new Set();
  for(const edge of state.neighbourhood.relationships) {
    const a=membership.get(edge.from),b=membership.get(edge.to),pair=`${a}:${b}`;
    if(a===undefined||b===undefined||a===b||connected.has(pair)||edge.source_status!=='PIN_VERIFIED')continue;
    connected.add(pair);
    svg+=connection('knowledge-'+a,'knowledge-'+b,{fromSide:a<2&&b>=2?'S':'E',toSide:a<2&&b>=2?'N':'W',kind:'edge optional'});
  }
  selected.forEach((group,i)=>{
    const x=235+(i%2)*480,y=210+Math.floor(i/2)*420,r=185;
    svg+=`<g class="knowledge-cluster" data-group="${esc(group.label)}" ${routeShape('knowledge-'+i,x,y,r)}><circle class="knowledge-group" cx="${x}" cy="${y}" r="${r}"/>${lines(group.label,25,2).map((line,n)=>`<text class="knowledge-title" x="${x}" y="${y-122+n*24}" text-anchor="middle">${esc(line)}</text>`).join('')}<text class="knowledge-subtitle" x="${x}" y="${y-67}" text-anchor="middle">${group.rows.length} membership${group.rows.length===1?'':'s'} · editorial classification</text>`;
    const children=group.rows.slice(0,2);
    children.forEach((row,j)=>{svg+=knowledgeNode(row,x+(children.length===1?0:j?76:-76),y+42,children.length===1?78:70,state);});
    if(group.rows.length>2)svg+=`<text class="knowledge-subtitle" x="${x}" y="${y+149}" text-anchor="middle">${group.rows.length-2} more in the complete outline</text>`;
    svg+='</g>';
  });
  return svg+'</svg>';
}
function scientificNeighbourhood(state) {
  const body=state.body,view=body?.exploration;
  if(!view||body.selection?.selection_id!==state.selectionId)return '';
  const start=(state.relationPage||0)*32,edges=view.edges.slice(start,start+32),nodes=new Map(view.nodes.map(row=>[row.id,row.label]));
  return `<section class="scientific-neighbourhood"><h2>Relationships in the opened original</h2><p>${edges.length} / ${view.edges.length} source-backed relationships · original read ${esc(body.current_reader.observed_at_utc)}. Their scope is this investigation.</p><div class="relationship-list">${edges.map((edge,i)=>action('scientific-relationship',start+i,`<strong>${esc(edge.kind.replaceAll('_',' '))}</strong><span>${esc(nodes.get(edge.from))} → ${esc(nodes.get(edge.to))}</span><small>${esc(edge.scope)}</small>`,'relationship-row')).join('')}</div>${view.edges.length>32?`<div class="graph-continuation">${action('scientific-page',Math.max(0,(state.relationPage||0)-1),'← Previous relationships')}${action('scientific-page',Math.min(Math.ceil(view.edges.length/32)-1,(state.relationPage||0)+1),'Next relationships →')}</div>`:''}${recordDetails('Original operation connections',body.provenance?.scientific_connections||[])}${recordDetails('Unselected supplier proposals and their own prerequisites',view.layout.suppliers||[])}${body.selection.companion_roles.includes('contribution')?action('companion','contribution','Inspect the original contribution and product limits ↗','inspector-button'):''}${note('An unselected proposal is not assessed supply. Consumer admission and later updates require their actual owning reads.')}</section>`;
}
export function knowledge(state,inspector) {
  if(!state.neighbourhood)return `<div class="empty-state"><h1>Knowledge across investigations</h1><p>Read a bounded window of selected original identities and their source-backed editorial relationships.</p>${action('neighbourhood','','Read Knowledge neighbourhood','primary-action')}</div>`;
  const all=groups(state),count=state.neighbourhood.page.total;
  const outline=`<div class="knowledge-outline">${all.map(group=>`<section><h2>${esc(group.label)}</h2><ul class="outline-list">${group.rows.map(row=>`<li>${action('knowledge',row.selection_id,`<span class="outline-mark">·</span><span><strong>${esc(row.label)}</strong><small>${esc(row.question)}</small></span><span class="row-status">Select ↗</span>`,'outline-row')}</li>`).join('')}</ul></section>`).join('')}</div>`;
  return `<div class="page-intro"><div class="intro-text"><p class="eyebrow">KNOWLEDGE ACROSS INVESTIGATIONS</p><h1>What can one finding make possible?</h1><p class="intro-summary">Locate the same original identities through programmes or disciplines. Each relationship retains its stated meaning.</p></div></div><div class="knowledge-tools"><div class="lens-switch" role="group" aria-label="Knowledge organisation">${['programme','discipline'].map(lens=>`<button data-action="lens" data-value="${lens}" aria-pressed="${state.lens===lens}">By ${lens}</button>`).join('')}</div><span class="knowledge-note">${state.neighbourhood.page.returned_count} / ${count} selected objects · ${all.length} groups</span><div class="view-switch">${action('outline','false','Map')}${action('outline','true','Outline')}</div></div><div class="workspace"><section class="canvas-column" aria-label="Knowledge relationships"><div class="canvas knowledge-canvas">${state.outline?outline:graph(state,all)}</div>${all.length>4?`<div class="graph-continuation">${action('group-page',Math.max(0,(state.groupPage||0)-1),'← Previous groups')}${action('group-page',Math.min(Math.ceil(all.length/4)-1,(state.groupPage||0)+1),'Next groups →')}</div>`:''}<div class="canvas-legend"><span class="legend-item"><i class="legend-line informs"></i>Informing reference / editorial classification</span><span class="legend-context">No scientific supply inferred</span></div><div class="relationship-list">${state.neighbourhood.relationships.map((edge,i)=>action('relationship',i,`<strong>${esc(edge.kind.replaceAll('_',' '))}</strong><span>${esc(edge.label)}</span><small>${esc(edge.source_status)} · ${esc(edge.target_coverage)}</small>`,'relationship-row')).join('')||'<p class="relation-note">No relationship is selected in this window.</p>'}</div>${scientificNeighbourhood(state)}${note('This bounded collection does not enumerate unseen imports or corrections. Use Tools → Knowledge & exchange for explicit certificate verification, selected imports and destination admission.')}<a class="tool-link" href="/tools.html">Inspect certificates and selected imports ↗</a>${state.neighbourhood.page.next_cursor?action('neighbourhood-next',state.neighbourhood.page.next_cursor,'Next object window →','primary-action'):''}</section>${inspector}</div>`;
}
export function selectedKnowledgeDetail(row,state) {
  if(!row)return '<p>Select one original investigation in the map or outline.</p>';
  return `<p>${esc(row.question)}</p>${pill(disposition(row,state))}${inspect(row,state)}${recordDetails('Original selected identity',row.identity)}${note('Classification is editorial navigation. Open the original result for a current scientific read.')}`;
}
function inspect(row,state) {
  const original=fingerprint(row.identity);
  return `<p class="identity-short">${esc(original||'Result identity not yet selected')}</p>${action('open',row.selection_id,'Open original investigation ↗','inspector-button primary')}${state.body && fingerprint(state.body.identity)===original?action('view','current','Return to current result','inspector-button'):''}`;
}
