/* SPDX-License-Identifier: MPL-2.0 */
import {esc,action,lines,stateText,stateCode,statusKind,note} from './explorer-core.js';
import {motif,svgStart,routeShape,connection} from './explorer-geometry.js';

export const bounds={nodes:16,edges:32,depth:8};
const key=(view,id)=>String(view.nodes.findIndex(row=>row.id===id));
const node=(view,id)=>view.nodes.find(row=>row.id===id);
const mark=(view,id,x,y,r,state,options={})=>{
  const item=node(view,id);if(!item)return '';
  return motif(x,y,r,key(view,id),options.lines||lines(item.label),options.caption||stateText(item),
    statusKind(stateCode(item))||'open',options.symbol||'motif',state.selected===key(view,id));
};
const branchLabel={overview:'Question',physical:'Physical applicability',contrasts:'Paired contrasts',suppliers:'Possible suppliers',all:'All requirements',node:'Further requirements',stages:'Investigation stages'};
export function visibleRequirements(view,state) {
  const root=node(view,view.root_id);
  if(state.branch==='physical')return view.nodes.filter(row=>row.group==='shared' && root.children.includes(row.id));
  if(state.branch==='contrasts') {
    const selected=view.layout.cases?.[state.caseIndex||0];
    return selected?view.nodes.filter(row=>row.group===selected.id):[];
  }
  if(state.branch==='suppliers')return view.nodes.filter(row=>row.role==='supplier');
  if(state.branch==='node')return (view.nodes[Number(state.expanded)]?.children||[]).map(id=>node(view,id)).filter(Boolean);
  if(state.branch==='all')return view.nodes;
  return root.children.map(id=>node(view,id)).filter(Boolean);
}
export function outline(view,state,rows=(state.branch==='overview' && view.layout.kind!=='rubisco-joint-root'
  ? [node(view,view.root_id),...visibleRequirements(view,state)] : visibleRequirements(view,state))) {
  return `<div class="outline"><div class="outline-heading"><span>${esc(branchLabel[state.branch])}</span><span>${rows.length} selected / ${view.coverage.total_nodes} original records</span></div><ul class="outline-list">${rows.map(row=>`<li>${action('node',key(view,row.id),`<span class="outline-mark">${row.children.length||'·'}</span><span><strong>${esc(row.label)}</strong><small>${esc(row.role)} · ${row.children.length} further requirements</small></span><span class="row-status">${esc(stateText(row))}</span>`,`outline-row${state.selected===key(view,row.id)?' selected':''}`)}</li>`).join('')}</ul></div>`;
}
function overview(view,state) {
  const root=node(view,view.root_id),numerical=node(view,view.layout.numerical),retained=node(view,view.layout.retained);
  if(!numerical || !retained)return generic(view,state,[root,...root.children.map(id=>node(view,id)).filter(Boolean)]);
  const shared=view.nodes.filter(row=>row.group==='shared' && root.children.includes(row.id));
  const contrasts=view.nodes.filter(row=>view.layout.cases.some(item=>item.id===row.group));
  return svgStart('Follow the question back to the named conditions and potential inputs',510,980)+
    connection(key(view,root.id),'@physical',{fromSide:'N',toSide:'N',kind:'requirement-loop',label:['WHAT MUST THE RECEIVER KNOW?','Trace a missing condition back to its source'],x:490,y:34})+
    [[key(view,retained.id),'@physical'],['@physical','@contrasts'],['@contrasts',key(view,root.id)]].map(([from,to])=>connection(from,to,{kind:'chain-link',direct:true})).join('')+
    connection(key(view,numerical.id),key(view,root.id),{fromSide:'E',toSide:'E',kind:'numerical-link',label:['NUMERICAL ASSESSMENT','a separate required condition'],x:855,y:324})+
    mark(view,retained.id,105,365,40,state,{lines:['Retained inputs'],caption:stateText(retained)})+
    motif(310,285,55,'@physical',['Physical applicability'],`${shared.length} shared conditions`,'open','motif',state.branch==='physical')+
    motif(515,205,65,'@contrasts',['Paired contrasts'],`${view.layout.cases.map(row=>row.label.toUpperCase()).join(' / ')} · ${contrasts.length} conditions`,'open','motif',false)+
    mark(view,root.id,750,125,78,state,{lines:lines(root.label,28,2)})+
    mark(view,numerical.id,710,410,32,state,{lines:['Numerical assessment'],symbol:stateCode(numerical)==='SATISFIED'?'✓':'?'})+
    '<text class="chain-caption" x="330" y="488" text-anchor="middle">Requirement journey · positions do not imply execution order or supply</text></svg>';
}
function physical(view,state) {
  const rows=visibleRequirements(view,state);
  if(rows.length!==2)return generic(view,state,rows);
  return svgStart('Shared physical conditions required by the same receiver',430)+
    connection(key(view,rows[0].id),key(view,rows[1].id),{fromSide:'N',toSide:'N',kind:'requirement-bracket',label:['BOTH REQUIRED BY THE JOINT RECEIVER','Shared conditions remain counted once'],x:380,y:46})+
    rows.map((row,i)=>mark(view,row.id,205+i*350,220,72,state,{lines:lines(row.label,21,2)})).join('')+
    '<text class="chain-caption" x="380" y="406" text-anchor="middle">The receiver determines which preparation is sufficient</text></svg>';
}
function contrasts(view,state) {
  const selected=view.layout.cases?.[state.caseIndex||0];
  if(!selected?.groups || selected.groups.length!==2 || selected.groups.some(row=>row.requirement_ids.length!==2) || selected.joint_support_ids.length!==1)
    return generic(view,state,visibleRequirements(view,state));
  const support=selected.joint_support_ids[0];
  const group=(row,i)=>{
    const cx=215+430*i;
    return `<g class="contrast-cluster" data-group="${esc(row.label)}" ${routeShape('group'+i,cx,195,170)}><circle class="endpoint-group" cx="${cx}" cy="195" r="170"/><text class="endpoint-title" x="${cx}" y="68" text-anchor="middle">${esc(row.label)}</text><text class="endpoint-formula" x="${cx}" y="93" text-anchor="middle">${esc(row.formula)}</text>${row.requirement_ids.map((id,j)=>{
      const item=node(view,id),x=cx+(j?75:-75),y=222;
      return `<g class="graph-node contrast-object${state.selected===key(view,id)?' selected':''}" role="button" tabindex="0" data-node="${key(view,id)}" aria-label="${esc(item.label+'. '+stateText(item))}"><circle class="node-hit" cx="${x}" cy="${y}" r="73"/><circle class="ring ${statusKind(stateCode(item))||'open'}" cx="${x}" cy="${y}" r="68"/>${lines(item.label,15,3).map((line,index)=>`<text class="node-label" x="${x}" y="${y-15+index*18}" text-anchor="middle">${esc(line)}</text>`).join('')}<text class="node-caption" x="${x}" y="${y+48}" text-anchor="middle">${esc(stateText(item))}</text></g>`;
    }).join('')}</g>`;
  };
  return svgStart(`${selected.label.toUpperCase()} nested endpoint requirements`,555,860)+
    selected.groups.map((_,i)=>connection('group'+i,key(view,support),{fromSide:'S',toSide:i?'E':'W',kind:'chain-link'})).join('')+
    selected.groups.map(group).join('')+mark(view,support,430,440,34,state,{lines:['Joint support'],symbol:'↔'})+'</svg>';
}
function generic(view,state,all) {
  const offset=(state.graphPage||0)*bounds.nodes,rows=all.slice(offset,offset+bounds.nodes),columns=4;
  const rowCount=Math.ceil(rows.length/columns),height=Math.max(330,rowCount*210+60),positions=new Map();
  const content=rows.map((row,i)=>{
    const x=120+(i%columns)*235,y=100+Math.floor(i/columns)*210;positions.set(row.id,[x,y]);
    return mark(view,row.id,x,y,42,state,{lines:lines(row.label,23,2)});
  }).join('');
  const selectedEdges=view.edges.filter(edge=>positions.has(edge.from)&&positions.has(edge.to));
  const edges=selectedEdges.slice(0,bounds.edges).map(edge=>{
    const a=positions.get(edge.from),b=positions.get(edge.to);
    return connection(key(view,edge.from),key(view,edge.to),{fromSide:b[1]>a[1]?'S':'E',toSide:b[1]>a[1]?'N':'W',kind:'edge'});
  }).join('');
  return svgStart(`Original requirement window ${offset+1} to ${offset+rows.length} of ${all.length}`,height,950)+edges+content+'</svg>'+
    (all.length>bounds.nodes?`<div class="graph-continuation">${action('graph-page',Math.max(0,(state.graphPage||0)-1),'← Previous window')}<span>${offset+1}–${offset+rows.length} / ${all.length} · ${Math.min(selectedEdges.length,bounds.edges)} / ${selectedEdges.length} visible links</span>${action('graph-page',Math.min(Math.ceil(all.length/bounds.nodes)-1,(state.graphPage||0)+1),'Next window →')}</div>`:'');
}
export function investigationCanvas(view,state) {
  const showingOutline=state.outline;
  const branch=state.branch||'overview';
  const toolbar=`<div class="canvas-toolbar"><div class="breadcrumbs">${action('branch','overview','Question')}<span>/</span>${esc(branchLabel[branch])}</div><div class="view-switch" role="group" aria-label="Investigation display">${action('outline','false','Map')}${action('outline','true','Outline')}</div></div>`;
  const branches=`<div class="branch-tabs" role="group" aria-label="Question branches">${['overview',...(view.layout.kind==='rubisco-joint-root'?['physical','contrasts','suppliers']:[]),'all'].map(name=>action('branch',name,esc(branchLabel[name]),branch===name?'selected':'')).join('')}</div>`;
  const cases=branch==='contrasts'?`<div class="case-switch" role="group" aria-label="Processing view">${(view.layout.cases||[]).map((row,i)=>`<button data-action="case" data-value="${i}" aria-pressed="${i===(state.caseIndex||0)}">${esc(row.label.toUpperCase())}</button>`).join('')}</div>`:'';
  let content;
  if(showingOutline)content=outline(view,state);
  else if(view.layout.kind==='rubisco-joint-root' && branch==='overview')content=overview(view,state);
  else if(view.layout.kind==='rubisco-joint-root' && branch==='physical')content=physical(view,state);
  else if(view.layout.kind==='rubisco-joint-root' && branch==='contrasts')content=contrasts(view,state);
  else if(branch==='suppliers')content=outline(view,state);
  else content=generic(view,state,branch==='overview'?[node(view,view.root_id),...visibleRequirements(view,state)]:visibleRequirements(view,state));
  return toolbar+branches+cases+`<div class="canvas ${branch==='contrasts'?'contrast-canvas':''}">${content}</div><div class="canvas-legend"><span class="legend-item"><i class="legend-line"></i>Assessed at the named scope</span><span class="legend-item"><i class="legend-line open"></i>Still to establish / unselected</span><span class="legend-context">${view.coverage.total_nodes} original records · ${view.coverage.total_edges} requirement links</span></div>`+
    note(view.layout.overview_scope||'Original relationship kinds and scopes remain available in the outline and evidence inspector.');
}
