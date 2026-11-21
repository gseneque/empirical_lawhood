/* SPDX-License-Identifier: MPL-2.0 */
/* The same fixed broker endpoints and durable lifetimes as the secondary tools. */
export class StaleView extends Error {}
export class ApplicationTransport {
  constructor(onStatus) {
    this.onStatus=onStatus; this.contexts=[]; this.context=null; this.generation=0; this.pending=false;
    this.token=new URLSearchParams(location.hash.slice(1)).get('session') || sessionStorage.getItem('el-session');
    if(this.token)sessionStorage.setItem('el-session',this.token);
    if(location.hash.includes('session='))history.replaceState(null,'',location.pathname);
  }
  clear() {this.generation++;}
  select(id) {this.clear();this.context=this.contexts.find(row=>row.selection.value.context_id===id)||null;}
  supports(operation) {return this.context?.engine?.operations?.find(row=>row.operation_id===operation);}
  async fetchJSON(path,body) {
    const response=await fetch(path,{method:body===undefined?'GET':'POST',headers:{'X-EL-Session':this.token||'',...(body===undefined?{}:{'Content-Type':'application/json'})},
      body:body===undefined?undefined:JSON.stringify(body),cache:'no-store',credentials:'omit',redirect:'error'});
    const raw=await response.text();
    if(raw.length>5*1024*1024)throw new Error('The local response exceeds its display limit.');
    const value=JSON.parse(raw);
    if(!response.ok)throw new Error(value.errors?.map(row=>`${row.reason_code}: ${row.message}`).join(' · ')||`Local request refused (${response.status}).`);
    return value;
  }
  async connect() {
    if(!this.token)throw new Error('Open the session URL printed by the local workbench launcher.');
    const configuration=await this.fetchJSON('/api/context');
    this.contexts=configuration.contexts;this.applicationVersion=configuration.application_version;
    this.context=this.contexts[0]||null;
    return configuration;
  }
  remember(row) {
    let rows=[];
    try {rows=JSON.parse(localStorage.getItem('el-workbench-invocations')||'[]');} catch {}
    if(!Array.isArray(rows))rows=[];
    // Original handles are recovery locators. Scientific bodies and paths are never stored here.
    localStorage.setItem('el-workbench-invocations',JSON.stringify([...rows.filter(old=>old.handle!==row.handle),row].slice(-32)));
  }
  async durable(document, generation) {
    const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(document.context_id+':'+document.request_id));
    const handle=[...new Uint8Array(digest)].map(value=>value.toString(16).padStart(2,'0')).join('');
    this.remember({handle,context_id:document.context_id,operation:document.operation,request_id:document.request_id});
    const response=await fetch('/api/invoke',{method:'POST',headers:{'X-EL-Session':this.token||'','Content-Type':'application/json'},
      body:JSON.stringify(document),cache:'no-store',credentials:'omit',redirect:'error'});
    if(!response.ok)throw new Error(`Original read refused (${response.status}). Open Tools → Invocations for its retained handle.`);
    const reader=response.body.getReader(), decoder=new TextDecoder();let buffer='', received=0, result=null;
    try {
      while(true) {
        const chunk=await reader.read();if(chunk.done)break;
        received+=chunk.value.byteLength;
        if(received>5*1024*1024)throw new Error('The original response exceeds its display limit.');
        buffer+=decoder.decode(chunk.value,{stream:true});let end;
        while((end=buffer.indexOf('\n'))>=0) {
          const event=JSON.parse(buffer.slice(0,end));buffer=buffer.slice(end+1);
          if(event.event==='result')result=event.payload;
          if(event.event==='invocation' && generation===this.generation)this.onStatus(`Reading original · ${event.payload.state}. Handle retained in Tools → Invocations.`);
          if(event.event==='existing' && generation===this.generation)this.onStatus('An original invocation already exists. Inspect its handle in Tools → Invocations.');
        }
      }
      if(buffer.trim())throw new Error('The original response ended before its complete record. Inspect the retained invocation; no retry was made.');
      if(!result)throw new Error('No original response was delivered. Inspect Tools → Invocations before selecting a fresh read.');
      return result;
    } finally {reader.releaseLock();}
  }
  async request(operation,parameters={}) {
    if(this.pending)throw new Error('A read is still in flight. Its original handle remains available in Tools → Invocations.');
    const declared=this.supports(operation);
    if(!declared?.browser_available)throw new Error(declared?.unavailable_reason||`The selected engine does not support ${operation}. Its original tools remain available.`);
    const generation=this.generation;
    this.pending=true;
    try {
      const document={schema:'empirical-lawhood/application/request',version:'1.0.0',request_id:crypto.randomUUID(),
        context_id:this.context.selection.value.context_id,operation,parameters};
      const result=['DURABLE_READ','EFFECT'].includes(declared.lifecycle)?await this.durable(document,generation):await this.fetchJSON('/api/execute',document);
      if(generation!==this.generation || window.document.hidden)throw new StaleView('The context or visibility changed during this read.');
      if(result.status!=='SUCCEEDED')throw new Error(result.errors?.map(row=>`${row.reason_code}: ${row.message}`).join(' · ')||result.status);
      return result.payload;
    } finally {this.pending=false;}
  }
}
