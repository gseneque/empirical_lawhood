/* SPDX-License-Identifier: MPL-2.0 */
/* Actual original readers after a disclosed local transfer/allocation control. */
import {parseArgs} from 'node:util';
import {pathToFileURL} from 'node:url';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
import {geometry,settled} from './workbench-geometry-check.mjs';

const {values}=parseArgs({options:{'output-dir':{type:'string'},playwright:{type:'string'},'expected-file':{type:'string'},'fixture-mode':{type:'boolean',default:false}}});
if(!values['fixture-mode'])throw new Error('Disclose the operational allocation control with --fixture-mode.');
const expected=JSON.parse(await readFile(values['expected-file'],'utf8'));
assert.equal(expected.scope,'REAL_ORIGINAL_COPY_AND_READ_WITH_DISCLOSED_ALLOCATION');
assert.equal(expected.original_files_unchanged,true);
const output=resolve(values['output-dir']);await mkdir(output,{recursive:false});
const {chromium}=await import(pathToFileURL(resolve(values.playwright)).href);
const browser=await chromium.launch({channel:'chrome',headless:true,chromiumSandbox:true});
const page=await browser.newPage({viewport:{width:1366,height:768},reducedMotion:'reduce'});
page.setDefaultTimeout(60000);
const checks=[],requests=[],errors=[],measurements=[];let failure=null;
page.on('pageerror',error=>errors.push(error.message));
page.on('request',request=>{if(request.method()==='POST')requests.push(request.postDataJSON().operation);});
async function check(name,run){await run();checks.push({name,status:'PASS'});}
async function action(name,value){await page.locator(`[data-action="${name}"]${value===undefined?'':`[data-value="${value}"]`}`).first().click();}
async function screenshot(name){await settled(page);await page.screenshot({path:resolve(output,name+'.png'),fullPage:true});}
try {
  await page.goto(process.env.EL_WORKBENCH_CHECK_URL);await page.locator('.result-row').waitFor();
  await check('independent reading and contribution return stages survive session restart',async()=>{
    await action('open-activity','returned.original');await page.locator('.return-panel').waitFor();
    assert.equal(await page.locator('.return-stages>li').count(),6);
    const text=await page.locator('.return-panel').textContent();
    assert(text.includes('Original Read Completed'));assert(text.includes('Byte Verified'));
    assert.equal(await page.locator('#error').isVisible(),false);
    await screenshot('01-return-stages');
    if(await page.locator('[data-action="pause-observation"]').count())await action('pause-observation');
  });
  await check('returned-local reader opens the same original in its selected custody context',async()=>{
    await action('open-return');assert.equal(await page.locator('[data-action="return-reader"]').count(),2);
    await action('return-reader','1');await page.locator('.investigation-brief').waitFor({timeout:180000});
    assert.equal(await page.locator('#context').inputValue(),'exposed.original.return');
    assert((await page.locator('.investigation-brief').textContent()).includes('Unresolved'));
    measurements.push(await geometry(page,'returned original'));await screenshot('02-returned-original');
    await page.getByRole('tab',{name:'Evidence',exact:true}).click();await action('companion','contribution');
    await page.locator('#modal-body>pre').waitFor({timeout:180000});
    const contribution=JSON.parse(await page.locator('#modal-body>pre').textContent());
    assert.equal(contribution.contribution.value.products.length,2);
    assert(contribution.contribution.value.products.every(row=>row.value.evidence_ceiling==='NON_PROMOTABLE'));
    await screenshot('03-original-contribution');await page.keyboard.press('Escape');
  });
  await check('observation returns to its registered context after an alternate original read',async()=>{
    await action('observe');await page.locator('.return-panel').waitFor();
    if(await page.locator('[data-action="pause-observation"]').count())await action('pause-observation');
    await action('open-return');await action('return-reader','0');
    await page.locator('.investigation-brief').waitFor({timeout:180000});
    assert.notEqual(await page.locator('#context').inputValue(),'exposed.original.return');
    await action('observe');await page.locator('.return-panel').waitFor();
    assert.equal(await page.locator('#context').inputValue(),'exposed.original.return');
    assert.equal(await page.locator('#error').isVisible(),false);
    if(await page.locator('[data-action="pause-observation"]').count())await action('pause-observation');
  });
  await check('return navigation performs reads only',async()=>{
    assert(requests.every(operation=>['collection.list','collection.entry','observation.read','exploration.read','exploration.companion'].includes(operation)));
    assert.deepEqual(errors,[]);
  });
} catch(error){failure=error.stack||String(error);await screenshot('failure').catch(()=>{});}
finally {
  await writeFile(resolve(output,'browser-acceptance.json'),JSON.stringify({status:failure?'FAIL':'PASS',scope:expected.scope,
    browser:browser.version(),checks,requests,measurements,errors,failure},null,2)+'\n');
  await browser.close();
}
if(failure)throw new Error(failure);
console.log(JSON.stringify({status:'PASS',checks:checks.length,output}));
