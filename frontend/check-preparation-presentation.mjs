/* SPDX-License-Identifier: MPL-2.0 */
/* Actual retained-prefix read plus separately disclosed typed renderer controls. */
import {parseArgs} from 'node:util';
import {pathToFileURL} from 'node:url';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {geometry,settled} from './workbench-geometry-check.mjs';

const {values}=parseArgs({options:{url:{type:'string'},'output-dir':{type:'string'},playwright:{type:'string'},'expected-file':{type:'string'},'fixture-mode':{type:'boolean',default:false},phase:{type:'string',default:'all'}}});
values.url ||= process.env.EL_WORKBENCH_CHECK_URL;
for(const key of ['url','output-dir','playwright','expected-file'])if(!values[key])throw new Error(`Select --${key}.`);
if(!values['fixture-mode'])throw new Error('The assessed display operands require --fixture-mode.');
if(!['all','original','renderer'].includes(values.phase))throw new Error('Select all, original or renderer checks.');
const expected=JSON.parse(await readFile(values['expected-file'],'utf8'));
const controlBytes=await readFile(expected.renderer_controls);
assert.equal(createHash('sha256').update(controlBytes).digest('hex'),expected.renderer_controls_sha256);
const controls=JSON.parse(controlBytes);
assert.equal(controls.scope,'EXPOSED_PRESENTATION_CONTROLS_ONLY');
assert.equal(controls.new_native_calls,0);
const output=resolve(values['output-dir']);await mkdir(output,{recursive:false});
const {chromium}=await import(pathToFileURL(resolve(values.playwright)).href);
const browser=await chromium.launch({channel:'chrome',headless:true,chromiumSandbox:true});
let page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});
page.setDefaultTimeout(180000);
const checks=[],requests=[],errors=[],measurements=[];let failure=null,rendererLayout=null;
page.on('pageerror',error=>errors.push(error.message));
page.on('request',request=>{if(request.method()==='POST')requests.push(request.postDataJSON().operation);});
async function check(name,run){await run();checks.push({name,status:'PASS'});}
async function action(name,value){await page.locator(`[data-action="${name}"]${value===undefined?'':`[data-value="${value}"]`}`).first().click();}
async function screenshot(name){await settled(page);await page.screenshot({path:resolve(output,name+'.png'),fullPage:true});}
async function cleanText(selector){const text=await page.locator(selector).textContent();assert(!text.includes('undefined'));assert(!text.includes('NaN'));return text;}
async function close(){await page.keyboard.press('Escape');await page.locator('#modal').waitFor({state:'hidden'});}
try {
  await page.goto(values.url,{waitUntil:'domcontentloaded'});
  await page.locator('.result-row').first().waitFor();
  if(values.phase!=='renderer') {
  await check('registered original prefix opens through the current production reader',async()=>{
    assert(!requests.some(row=>row.startsWith('exploration.')));
    await action('open',expected.selection_id);await page.locator('.investigation-brief').waitFor();
    assert.equal(await page.locator('#error').isVisible(),false);
    assert.equal(await page.locator('.question-readouts>details').count(),6);
    const text=await cleanText('.investigation-brief');
    assert(text.includes('Original Publication Incomplete'));assert(!text.includes('physical conditions unresolved'));
    assert(!text.includes('numerical assessment'));
    measurements.push(await geometry(page,'actual unentered prefix'));await screenshot('actual-unentered-prefix');
  });
  await check('generic finding and evidence use only supplied M50 records',async()=>{
    const before=requests.length;
    await page.getByRole('tab',{name:'Finding',exact:true}).click();
    const text=await cleanText('.inspector');
    assert(text.includes('Original scoped findings'));assert(!text.includes('Cases → alternatives'));
    assert(text.includes('384'));
    await page.getByRole('tab',{name:'Evidence',exact:true}).click();
    assert.equal(await page.locator('.inspector [data-action="record"][data-value="assessment"]').count(),0);
    assert.equal(await page.locator('.inspector [data-action="record"][data-value="requirement_graph"]').count(),0);
    assert.equal(requests.length,before);
  });
  await check('exact original design opens and exports unchanged bytes',async()=>{
    await page.getByRole('button',{name:'Read exact original record',exact:true}).click();
    await page.locator('#modal-body>pre').waitFor();
    const raw=await page.locator('#modal-body>pre').textContent();
    assert.equal(createHash('sha256').update(raw).digest('hex'),expected.design_sha256);
    const event=page.waitForEvent('download');await action('download');
    const download=await event;const path=resolve(output,'exact-original-design.json');await download.saveAs(path);
    assert.equal(await readFile(path,'utf8'),raw);await close();
  });
  await check('M50 Method inspection reads declared current source',async()=>{
    await page.getByRole('tab',{name:'Method',exact:true}).click();
    const text=await cleanText('.inspector');assert(text.includes('Retain all six questions'));
    await action('method-source');await page.locator('#modal-body>pre').waitFor();
    assert((await page.locator('#modal-body').textContent()).includes('CURRENT_SELECTED_READER_IMPLEMENTATION'));
    assert((await page.locator('#modal-body>pre').textContent()).includes('def prepare_prefix_continuation'));
    assert.equal(await page.locator('#notice').isVisible(),false);
    await close();
  });
  await check('actual pending readouts remain complete on a narrow screen',async()=>{
    await page.setViewportSize({width:390,height:844});
    await action('outline','true');
    assert.equal(await page.locator('.outline-row').count(),1);
    for(const detail of await page.locator('.question-readouts>details').all())await detail.locator(':scope > summary').click();
    const text=await cleanText('.question-readouts');assert(text.includes('384'));assert(text.includes('independent_biological_replicates'));
    assert(text.includes('NOT_YET_ASSESSED'));
    measurements.push(await geometry(page,'actual narrow prefix'));await screenshot('actual-narrow-prefix');
  });
  }
  // The following operands are a typed, disclosed display fixture. They are
  // deliberately outside the live application state and confer no scientific read.
  if(values.phase!=='original') {
  // A separate same-origin page has no live shell or observation callbacks.
  // It loads the production stylesheet and pure rendering modules only.
  const origin=new URL(values.url).origin;
  page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'});
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(request.method()==='POST')requests.push(request.postDataJSON().operation);});
  const rendererUrl=origin+'/__m50-renderer-control';
  await page.route(rendererUrl,route=>route.fulfill({contentType:'text/html',
    body:'<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">'+
      '<link rel="stylesheet" href="/explorer.css"></head><body><main id="main"></main></body></html>'}));
  await page.goto(rendererUrl,{waitUntil:'load'});
  await check('assessed renderer preserves six questions, signed error and unavailable outcomes',async()=>{
    rendererLayout=await page.evaluate(async view=>{
      const {investigationBrief,inspector,questionReadouts}=await import('/explorer-details.js');
      const {investigationCanvas}=await import('/explorer-diagrams.js');
      const {layoutConnections}=await import('/explorer-geometry.js');
      const body={scope:'EXPOSED_PRESENTATION_CONTROLS_ONLY',summary:view.summary,exploration:view,
        value_semantics:'Exposed renderer control. No acquired molecular finding.',page:{rows:view.question_readouts,total:6,returned_count:6},
        selection:{companion_roles:[]}};
      const state={body,selected:'5',tab:'finding',branch:'overview',outline:false};
      const node=document.createElement('section');node.id='exposed-m50-renderer';
      node.innerHTML='<h1>Exposed M50 renderer control</h1>'+investigationBrief(body,null)+
        '<div class="workspace"><section class="canvas-column">'+investigationCanvas(view,state)+questionReadouts(view)+'</section>'+inspector(state)+'</div>';
      document.querySelector('#main').replaceChildren(node);
      await document.fonts.ready;
      let fallback=null;
      try {layoutConnections();}
      catch(error) {
        // Use the shell's documented complete-outline fallback, retaining why
        // this diagram was unavailable rather than accepting partial edges.
        fallback=error.message;state.outline=true;
        node.querySelector('.canvas-column').innerHTML=investigationCanvas(view,state)+questionReadouts(view);
      }
      for(const detail of node.querySelectorAll('.question-readouts>details,.inspector .record-details'))detail.open=true;
      return {outline:state.outline,fallback};
    },controls.assessed);
    assert.equal(await page.locator('#exposed-m50-renderer .question-readouts>details').count(),6);
    const text=await cleanText('#exposed-m50-renderer');
    for(const word of ['-0.10000000000000000001','Exposed Adverse','Unavailable','384','empirical discrepancy'])assert(text.includes(word),'Missing '+word);
    assert(!text.includes('Cases → alternatives'));
    if(rendererLayout.outline)assert.equal(await page.locator('#exposed-m50-renderer .outline-row').count(),7);
    measurements.push(await geometry(page,'assessed renderer control'));await screenshot('exposed-assessed-questions');
  });
  await check('signed and unavailable assessed operands fit a narrow screen',async()=>{
    await page.setViewportSize({width:390,height:844});
    measurements.push(await geometry(page,'narrow assessed renderer control'));
    assert((await cleanText('#exposed-m50-renderer')).includes('-0.10000000000000000001'));
    await screenshot('exposed-narrow-assessed-questions');
  });
  await check('generic exact-record controls retain only the selected question locator',async()=>{
    await page.evaluate(async view=>{
      const {inspector}=await import('/explorer-details.js');
      document.querySelector('#exposed-m50-renderer .inspector').outerHTML=inspector({body:{exploration:view,selection:{companion_roles:[]}},selected:'5',tab:'evidence'});
    },controls.assessed);
    assert.deepEqual(await page.locator('#exposed-m50-renderer .inspector [data-action="record"]').evaluateAll(nodes=>nodes.map(node=>node.dataset.value)),['5']);
  });
  await check('conditional-root summaries and absent-original bindings retain their separate meaning',async()=>{
    const html=await page.evaluate(async()=>{
      const {investigationBrief,questionReadouts}=await import('/explorer-details.js');
      return investigationBrief({exploration:{layout:{kind:'rubisco-joint-root'},summary:{numerical_disposition:'SATISFIED',
        unresolved_physical_requirements:12,root_prerequisites:13,biological_predictive_validity:'UNEVALUABLE'},coverage:{total_nodes:27}}},null)+
        questionReadouts({pending_bindings:[{owner:'original record',reader:'implemented reader',status:'NOT_SUPPLIED_BY_THIS_ORIGINAL'}]});
    });
    assert(html.includes('12 physical conditions unresolved'));assert(html.includes('13 root prerequisites'));
    assert(!html.includes('readers remain unavailable'));assert(html.includes('does not supply'));
  });
  }
  await check('browser reads perform no execution and report no script errors',async()=>{
    assert(requests.every(row=>['collection.list','collection.entry','exploration.read','exploration.record','exploration.method'].includes(row)));
    assert.deepEqual(errors,[]);
  });
} catch(error){failure=error.stack||String(error);await screenshot('failure').catch(()=>{});}
finally {
  await writeFile(resolve(output,'browser-acceptance.json'),JSON.stringify({status:failure?'FAIL':'PASS',
    scope:values.phase==='renderer'?'DISCLOSED_RENDERER_CONTROLS_ONLY':values.phase==='original'?
      'CURRENT_PRODUCTION_READER_OF_UNENTERED_ORIGINAL':'CURRENT_PRODUCTION_READER_OF_UNENTERED_ORIGINAL_PLUS_DISCLOSED_ASSESSED_RENDERER_CONTROL',
    phase:values.phase,
    browser:browser.version(),checks,requests,measurements,rendererLayout,errors,failure,new_native_calls:0,provider_calls:0},null,2)+'\n');
  await browser.close();
}
if(failure)throw new Error(failure);
console.log(JSON.stringify({status:'PASS',checks:checks.length,output}));
