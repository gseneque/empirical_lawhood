/* SPDX-License-Identifier: MPL-2.0 */
/* Production broker/engine reads of disclosed, sealed, imported controls. */
import {parseArgs} from 'node:util';
import {pathToFileURL} from 'node:url';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
import {geometry,settled} from './workbench-geometry-check.mjs';

const {values}=parseArgs({options:{url:{type:'string'},'output-dir':{type:'string'},playwright:{type:'string'},'expected-file':{type:'string'},'fixture-mode':{type:'boolean',default:false}}});
values.url ||= process.env.EL_WORKBENCH_CHECK_URL;
for(const key of ['url','output-dir','playwright','expected-file'])if(!values[key])throw new Error(`Select --${key}.`);
if(!values['fixture-mode'])throw new Error('These observations require the explicit --fixture-mode disclosure.');
const expected=JSON.parse(await readFile(values['expected-file'],'utf8'));
assert.equal(expected.scope,'EXPOSED_SOFTWARE_CONTROLS_ONLY');
assert.equal(expected.real_provider_calls,0);assert.equal(expected.new_native_calls,0);
const output=resolve(values['output-dir']);await mkdir(output,{recursive:false});
const {chromium}=await import(pathToFileURL(resolve(values.playwright)).href);
const browser=await chromium.launch({channel:'chrome',headless:true,chromiumSandbox:true});
const page=await browser.newPage({viewport:{width:1366,height:768},reducedMotion:'reduce'});
page.setDefaultTimeout(60000);
const requests=[],checks=[],errors=[],measurements=[],inflight=new Set();let maximumInFlight=0,failure=null;
page.on('pageerror',error=>errors.push(error.message));
page.on('request',request=>{
  if(request.method()!=='POST')return;
  const body=request.postDataJSON();
  requests.push({operation:body.operation,selection_id:body.parameters?.selection_id,at_ms:performance.now()});
  inflight.add(request);maximumInFlight=Math.max(maximumInFlight,inflight.size);
});
page.on('requestfinished',request=>inflight.delete(request));page.on('requestfailed',request=>inflight.delete(request));
async function check(name,run){await run();checks.push({name,status:'PASS'});}
async function action(name,value){await page.locator(`[data-action="${name}"]${value===undefined?'':`[data-value="${value}"]`}`).first().click();}
async function contains(selector,texts){const text=await page.locator(selector).textContent();for(const item of texts)assert(text.includes(item),'Missing '+item);}
async function screenshot(name){await settled(page);await page.screenshot({path:resolve(output,name+'.png'),fullPage:true});}
async function open(row){
  await page.locator('[data-view="results"]').click();await page.locator('.result-row').first().waitFor();
  await action('open-activity',row.id);await page.locator('.finance-panel').waitFor();
  assert.equal(await page.locator('#error').isVisible(),false);
}
try {
  await page.goto(values.url,{waitUntil:'domcontentloaded'});await page.locator('.result-row').first().waitFor();
  await check('registered external work is discoverable before any scientific result exists',async()=>{
    assert.equal(await page.locator('.result-row').count(),expected.rows.length);
    assert.equal(requests.some(row=>row.operation?.startsWith('exploration.')),false);
  });
  for(const row of expected.rows){
    await check('production observation: '+row.kind,async()=>{
      const before=requests.length;await open(row);
      assert.deepEqual(requests.slice(before).map(item=>item.operation),['collection.entry','observation.read']);
      await contains('.finance-panel',['USD 50',row.accounting,row.remaining,'not invoices','Last monetary observation']);
      assert.equal(await page.locator('.stage-list>.stage').count(),4);
      assert.deepEqual(await page.locator('.stage-list>.stage summary strong').evaluateAll(nodes=>nodes.map(node=>node.textContent.split(' · ')[0])),['m50.06','m50.07','m50.09','m50.08']);
      await contains('.stage-list',['Declined','Adaptive refinement before challenge']);
      if(row.kind==='unavailable-reader'){
        await contains('.activity-panel',['scientific observation binding is unavailable','No scientific observation callback is selected for this original wave.']);
        assert.equal(await page.locator('.domain-observation').count(),0);
      } else {
        assert.equal(await page.locator('.position-grid>.position').count(),4);
        assert.deepEqual(await page.locator('.allowances>details summary>span:not(.status-pill)').evaluateAll(nodes=>nodes.map(node=>node.textContent)),
          ['0 / 10 complete returns','0 / 20 complete returns','0 / 4 complete returns','0 / 4 complete returns']);
        await action('pause-observation');
        await page.locator('.effect-coverage>summary').click();
        await contains('.effect-coverage',['0.01','0.02','primary','additional','NOT_ESTABLISHED']);
        await page.locator('.position-grid>.position').first().locator('summary').first().click();
        await contains('.position-grid',['COORDINATE_RESTART_ONLY','ADVISORY_TRIAL_OBSERVED']);
      }
      if(row.kind==='unknown-contact')await contains('.activity-panel',['UNKNOWN_CONTACT','Interrupted']);
      if(row.kind==='stale-transfer')await contains('.observation-status',['Stale']);
      if(row.kind==='collector-restart')await contains('.activity-panel',['.restarted','sequence 1']);
      if(row.kind==='financial-stop')await contains('.finance-panel',['Financial Cancellation Returned','STOP_SCIENCE_RETURN_ONLY']);
      if(row.kind==='retirement-unresolved')await contains('.finance-panel',['Retirement Unresolved','USD -']);
      if(row.kind==='retired-volume')await contains('.finance-panel',['Compute Absent Volume Retained','Continuing Until Separate Volume Retirement','USD -']);
      if(row.kind==='return-failed')await contains('.return-panel',['Failed','Return observation remains open']);
      assert.equal(await page.locator('.return-stages>li').count(),6);
      measurements.push(await geometry(page,row.kind));await screenshot(row.kind);
    });
  }
  await check('terminal science retains independent finance and evidence-return observation',async()=>{
    await open(expected.rows.find(row=>row.kind==='retired-volume'));
    assert.equal(await page.locator('[data-action="pause-observation"]').count(),1);
    await contains('.observation-status',['Succeeded']);
    const before=requests.filter(row=>row.operation==='observation.read').length;
    await page.waitForTimeout(31000);
    await page.waitForFunction(()=>document.querySelector('.finance-panel'));
    assert.equal(requests.filter(row=>row.operation==='observation.read').length,before+1);
    const times=requests.filter(row=>row.operation==='observation.read').slice(-2).map(row=>row.at_ms);
    assert(times[1]-times[0]>=29000,'Refresh respects the declared 30 second cadence');
    await action('pause-observation');
    const deadline=performance.now()+60000;
    while(inflight.size&&performance.now()<deadline)await page.waitForTimeout(100);
    assert.equal(inflight.size,0);
    assert.equal(await page.locator('[data-action="pause-observation"]').count(),0,'A late response cannot restart paused observation');
  });
  await check('four positions, stage coverage and money remain readable on narrow screens',async()=>{
    await page.setViewportSize({width:390,height:844});measurements.push(await geometry(page,'narrow observation'));
    await screenshot('narrow-observation');await page.setViewportSize({width:1366,height:768});
  });
  await check('declared six-question renderer preserves exact values and complete denominators',async()=>{
    const fixture=await page.evaluate(async()=>{
      const {questionReadouts}=await import('/explorer-details.js');
      const rows=Array.from({length:6},(_,index)=>({question_id:'Q'+(index+1),label:'EXPOSED SOFTWARE CONTROL',
        acquisition_state:index%2?'UNENTERED':'RETURNED_CONTROL',authentication_state:index%2?'UNAVAILABLE':'CONTROL_ONLY',
        assessment_state:index%2?'READER_UNAVAILABLE':'CONTROL_ASSESSMENT',disposition:index%2?'UNANSWERED':'EXPOSED_ADVERSE',
        quantity:index%2?null:{decimal:'-0.10000000000000000001'},uncertainty:null,
        denominator:{matched_constructions:1,nested_positions:4,independent_biological_units:0,
          unavailable_alternative:'V1',cutoff:{integer:'9007199254740993'},design:'EXPOSED_CONTROL_ONLY'},
        evidence:[],consequence:'No real M50 finding is supplied by this renderer control.'}));
      const node=document.createElement('section');node.id='disclosed-question-control';node.innerHTML=questionReadouts({question_readouts:rows});
      // Keep this explicitly disclosed renderer control outside the live view:
      // viewport/visibility changes legitimately replace the production main.
      document.body.append(node);
      for(const detail of node.querySelectorAll('details'))detail.open=true;
      return rows;
    });
    assert.equal(await page.locator('#disclosed-question-control .question-readouts>details').count(),6);
    await contains('#disclosed-question-control',['-0.10000000000000000001','9007199254740993','V1','Unanswered','Unavailable']);
    await writeFile(resolve(output,'six-question-render-control.json'),JSON.stringify({scope:'DISCLOSED_RENDERER_CONTROL; NO ORIGINAL SCIENTIFIC READOUT SELECTED',rows:fixture},null,2)+'\n');
    await screenshot('six-question-renderer-control');await page.locator('#disclosed-question-control').evaluate(node=>node.remove());
  });
  await check('browser visibility clears observations and reconnect requires a fresh permitted read',async()=>{
    await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});
    assert.equal(await page.locator('.finance-panel').count(),0);
    assert.equal(await page.locator('.position-grid').count(),0);
    await page.evaluate(()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'));});
    await page.locator('[data-view="results"]').click();await page.locator('.result-row').first().waitFor();
    await open(expected.rows[0]);await contains('.finance-panel',['USD 50']);await action('pause-observation');
  });
  await check('read-only refresh neither dispatches effects nor opens scientific readers',async()=>{
    assert(requests.every(row=>['collection.list','collection.entry','observation.read'].includes(row.operation)));
    assert.equal(maximumInFlight,1);assert.deepEqual(errors,[]);
  });
} catch(error){failure=error.stack||String(error);await screenshot('failure').catch(()=>{});}
finally {
  await writeFile(resolve(output,'browser-acceptance.json'),JSON.stringify({status:failure?'FAIL':'PASS',scope:expected.scope,
    browser:browser.version(),checks,measurements,requests,maximumInFlight,errors,failure},null,2)+'\n');
  await browser.close();
}
if(failure)throw new Error(failure);
console.log(JSON.stringify({status:'PASS',checks:checks.length,output}));
