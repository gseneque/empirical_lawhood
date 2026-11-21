/* SPDX-License-Identifier: MPL-2.0 */
/* Real older engine negotiation through the current broker and retained tools. */
import {parseArgs} from 'node:util';
import {pathToFileURL} from 'node:url';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const {values}=parseArgs({options:{'output-dir':{type:'string'},playwright:{type:'string'},'expected-file':{type:'string'}}});
const expected=JSON.parse(await readFile(values['expected-file'],'utf8'));
const output=resolve(values['output-dir']);await mkdir(output,{recursive:false});
const {chromium}=await import(pathToFileURL(resolve(values.playwright)).href);
const browser=await chromium.launch({channel:'chrome',headless:true,chromiumSandbox:true});
const page=await browser.newPage({viewport:{width:1366,height:768}});page.setDefaultTimeout(60000);
const requests=[],checks=[],errors=[];let failure=null;
page.on('pageerror',error=>errors.push(error.message));
page.on('request',request=>{if(request.method()==='POST')requests.push(request.postDataJSON().operation);});
try {
  await page.goto(process.env.EL_WORKBENCH_CHECK_URL);await page.locator('#error').waitFor();
  assert((await page.locator('#error').textContent()).includes('does not support collection.list'));
  assert.equal(requests.length,0);
  await page.screenshot({path:resolve(output,'01-capability-fallback.png'),fullPage:true});
  checks.push({name:'actual older engine refuses new collection capability before dispatch',status:'PASS'});
  await page.locator('a[href="/tools.html"]').first().evaluate(link=>link.removeAttribute('target'));
  await page.locator('a[href="/tools.html"]').first().click();
  await page.locator('#context:not([disabled])').waitFor();
  await page.locator('#kind').selectOption('execution');await page.locator('#directory').fill(expected.directory);
  await page.locator('#open').click();await page.locator('#result tbody tr').first().waitFor();
  assert.equal(await page.locator('#error').isVisible(),false);
  assert.equal(requests.filter(name=>name==='recursive.execution').length,1);
  await page.screenshot({path:resolve(output,'02-original-execution.png'),fullPage:true});
  checks.push({name:'unchanged older context and original metadata reader remain available in Tools',status:'PASS'});
  await page.locator('#nav-workflows').click();await page.locator('.workflow-card').first().waitFor();
  assert(requests.every(name=>['recursive.execution','workflow.list'].includes(name)));
  assert.deepEqual(errors,[]);
  checks.push({name:'retained workflow navigation performs no effects or new UI calls',status:'PASS'});
} catch(error){failure=error.stack||String(error);await page.screenshot({path:resolve(output,'failure.png'),fullPage:true}).catch(()=>{});}
finally {
  await writeFile(resolve(output,'browser-acceptance.json'),JSON.stringify({status:failure?'FAIL':'PASS',browser:browser.version(),
    scope:'ACTUAL_OLDER_ENGINE_COMPATIBILITY',checks,requests,errors,failure},null,2)+'\n');await browser.close();
}
if(failure)throw new Error(failure);
console.log(JSON.stringify({status:'PASS',checks:checks.length,output}));
