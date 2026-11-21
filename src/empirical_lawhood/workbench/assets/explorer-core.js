/* SPDX-License-Identifier: MPL-2.0 */
export const $ = selector => document.querySelector(selector);
export const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const exact = value => value === null || value === undefined ? 'Unavailable' : typeof value === 'object'
  ? (Object.keys(value).length === 1 && 'decimal' in value ? value.decimal
    : Object.keys(value).length === 1 && 'integer' in value ? value.integer : JSON.stringify(value)) : String(value);
export const human = value => exact(value).replaceAll('_',' ').replace(/\b[A-Z]{3,}\b/g, word => word[0]+word.slice(1).toLowerCase());
export const unpack = value => value?.schema && value?.value ? value.value : value;
export const action = (name, value, label, className='') => `<button class="${esc(className)}" data-action="${esc(name)}" data-value="${esc(value)}">${label}</button>`;
export const statusKind = value => /CONTRADICT|FALSIF|REFUT|FAIL|REJECT/.test(exact(value)) ? 'adverse'
  : /^(SATISFIED|SUPPORTED|PASS|SUCCEEDED|COMPLETED)$/.test(exact(value)) ? 'complete' : '';
export const pill = (label, kind=statusKind(label)) => `<span class="status-pill ${esc(kind)}">${esc(human(label))}</span>`;
export const detail = (name, value) => `<div class="detail-row"><span>${esc(name)}</span><strong>${esc(exact(value))}</strong></div>`;
export const note = text => `<div class="evidence-scope">${esc(text)}</div>`;
export const inspectButton = (name, value, label, primary=false) => action(name,value,`<span>${esc(label)}</span><span aria-hidden="true">↗</span>`,`inspector-button${primary?' primary':''}`);
export const fields = value => Object.entries(value || {}).map(([key,item]) => detail(human(key),item)).join('');
export const recordDetails = (label, value) => `<details class="record-details"><summary>${esc(label)}</summary><pre>${esc(JSON.stringify(value,null,2))}</pre></details>`;
export const stateText = node => Object.values(node?.state || {}).map(human).join(' · ') || 'Not read';
export const stateCode = node => Object.values(node?.state || {})[0] || 'UNAVAILABLE';
export const fingerprint = identity => identity?.value?.object_fingerprint || identity?.packet_sha256 || null;
export const narrow = () => matchMedia('(max-width:760px)').matches;
export function lines(text, width=22, maximum=3) {
  const output=[];
  const words=String(text).split(/\s+/).flatMap(word=>{
    const chunks=[];
    for(let i=0;i<word.length;i+=width)chunks.push(word.slice(i,i+width));
    return chunks;
  });
  for(const word of words) {
    if(output.length && (output.at(-1)+' '+word).length <= width) output[output.length-1]+=' '+word;
    else output.push(word);
  }
  if(output.length>maximum) return [...output.slice(0,maximum-1),output.slice(maximum-1).join(' ').slice(0,width-1)+'…'];
  return output;
}
export function scalarSummary(summary) {
  return Object.fromEntries(Object.entries(summary || {}).filter(([,v])=>v === null || typeof v !== 'object' || Object.keys(v).length===1 && ('decimal' in v || 'integer' in v)));
}
// Only an explicitly requested display approximation uses numeric conversion.
// Original strings are always retained beside it and in exact exports.
export function hours(seconds) {
  const value=exact(seconds);
  const approximation=Number(value);
  return /^\d+(\.\d+)?$/.test(value) && Number.isFinite(approximation) && approximation<=Number.MAX_SAFE_INTEGER
    ? (approximation/3600).toFixed(2) : 'Unavailable';
}
