/* SPDX-License-Identifier: MPL-2.0 */
/* Real broker and live telemetry process; disclosed response/lifecycle faults. */
import {parseArgs} from 'node:util';
import {spawn} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const {values}=parseArgs({options:{'output-dir':{type:'string'},playwright:{type:'string'},'expected-file':{type:'string'},'fixture-mode':{type:'boolean'}}});
if(!values['fixture-mode'])throw new Error('Select --fixture-mode for exposed progress controls.');
const expected=JSON.parse(await readFile(values['expected-file'],'utf8'));
const output=resolve(values['output-dir']);await mkdir(output,{recursive:false});
const {chromium}=await import(pathToFileURL(resolve(values.playwright)).href);
const worker=spawn(expected.python,['-B',fileURLToPath(new URL('./prepare-progress-controls.py',import.meta.url)),
  '--worker','--contexts',expected.contexts,'--required-mount',expected.required_mount],{stdio:['pipe','pipe','pipe']});
let workerError='',buffer='',commandId=0,readyResolve,readyReject;
const ready=new Promise((resolve,reject)=>{readyResolve=resolve;readyReject=reject;});
const acknowledgements=new Map();
worker.stdout.on('data',chunk=>{buffer+=chunk;let end;while((end=buffer.indexOf('\n'))>=0){
  const value=JSON.parse(buffer.slice(0,end));buffer=buffer.slice(end+1);
  if(value.event==='ready')readyResolve(value.rows);
  if(value.event==='ack'){acknowledgements.get(value.id)?.();acknowledgements.delete(value.id);}
}});
worker.stderr.on('data',chunk=>{if(workerError.length<16000)workerError+=chunk;});
worker.once('error',readyReject);worker.once('exit',code=>readyReject(new Error(`Control process exited ${code}: ${workerError}`)));
const command=action=>new Promise((resolve,reject)=>{
  const id=++commandId,timeout=setTimeout(()=>reject(new Error(`Control command timed out: ${action}`)),10000);
  acknowledgements.set(id,()=>{clearTimeout(timeout);resolve();});worker.stdin.write(JSON.stringify({action,id})+'\n');
});
let browser,page,failure=null,mode='real',frozen=null,held=[],realResponse=null;
const checks=[],errors=[],requests=[];
const pass=name=>checks.push({name,status:'PASS'});
try {
  const timer=setTimeout(()=>readyReject(new Error('Control readiness timed out. '+workerError)),60000);
  const rows=await ready.finally(()=>clearTimeout(timer));
  browser=await chromium.launch({channel:'chrome',headless:true,chromiumSandbox:true});
  page=await browser.newPage({viewport:{width:1366,height:900}});page.setDefaultTimeout(20000);
  await page.addInitScript(rows=>{
    localStorage.setItem('el-workbench-invocations',JSON.stringify(rows));
    window.progressReads={active:0,maximum:0,total:0};
    const original=window.fetch;
    window.fetch=async(...args)=>{
      if(args[0]!=='/api/invocation-state')return original(...args);
      const counts=window.progressReads;counts.active++;counts.total++;counts.maximum=Math.max(counts.maximum,counts.active);
      try{return await original(...args);}finally{counts.active--;}
    };
  },rows);
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(request.method()==='POST')requests.push(new URL(request.url()).pathname);});
  await page.route('**/api/invocation-state',async route=>{
    if(mode==='hang'){held.push(route);return;}
    if(mode==='error'){await route.abort('failed');return;}
    if(mode==='frozen'){await route.fulfill({json:frozen});return;}
    const response=await route.fetch();
    realResponse=await response.json();await route.fulfill({response});
  });
  const session=new URL(process.env.EL_WORKBENCH_CHECK_URL);session.pathname='/tools.html';
  await page.goto(session.href);await page.locator('#context:not([disabled])').waitFor();
  await page.locator('#nav-invocations').click();
  const card=()=>page.locator('.invocation-card');
  await page.getByRole('heading',{name:'control.file-publication',exact:true}).waitFor();
  assert((await card().textContent()).includes('9007199254740993 / 9007199254740999 bytes'));
  assert((await card().textContent()).includes('5 / 12 tasks'));
  assert((await card().textContent()).includes('2 failed'));
  assert.equal(await card().locator('progress').count(),2);
  assert.equal(await card().locator('.progress-freshness').getAttribute('aria-live'),'off');
  assert.equal(await card().locator('.progress-live-status').getAttribute('role'),'status');
  assert((await card().locator('.progress-steps summary').textContent()).includes('64 shown · 6 omitted from 70 total'));
  await card().locator('.progress-steps summary').click();
  assert.equal(await card().locator('.progress-steps li').count(),64);
  assert.equal(await card().locator('.progress-steps .adverse').count(),2);
  await card().locator('.progress-steps summary').focus();
  await command('heartbeat');await card().getByRole('button',{name:'Refresh invocation'}).click();
  await page.waitForFunction(()=>!document.querySelector('.invocation-card button').disabled);
  assert.equal(await card().locator('.progress-steps').getAttribute('open'),'');
  assert((await card().locator('.progress-heartbeat').textContent()).includes('advancement remains unknown'));
  await page.screenshot({path:resolve(output,'01-known-census-wide.png'),fullPage:true});
  await card().locator('.progress-steps summary').click();
  const older=structuredClone(realResponse);
  pass('Live process, production progress binding, exact large counters, separate denominators and bounded adverse history');

  await command('unknown');
  await page.getByRole('heading',{name:'control.native-iterations',exact:true}).waitFor();
  assert.equal(await card().locator('progress').count(),1);
  assert((await card().textContent()).includes('7 / Unknown iterations'));
  pass('Unknown convergence total has no phase percentage; whole-workflow census remains separate');

  frozen=older;mode='frozen';await card().getByRole('button',{name:'Refresh invocation'}).click();
  await page.getByText('An older progress report was ignored.',{exact:false}).waitFor();
  assert.equal(await page.getByRole('heading',{name:'control.native-iterations',exact:true}).count(),1);
  pass('Older sequence cannot overwrite the last bound progress');

  mode='real';await card().getByRole('button',{name:'Refresh invocation'}).click();
  await page.waitForFunction(()=>document.querySelector('.progress-notice').hidden);
  frozen=structuredClone(realResponse);frozen.payload.progress.age_seconds={decimal:'0'};mode='frozen';
  await page.waitForFunction(()=>document.querySelector('.invocation-card').dataset.stale==='true',{},{timeout:16000});
  pass('Repeated same-sequence replies with zero reported age cannot keep old work fresh');

  mode='real';await command('heartbeat');await card().getByRole('button',{name:'Refresh invocation'}).click();
  await page.waitForFunction(()=>document.querySelector('.invocation-card').dataset.stale==='false');
  pass('A new bound sequence clears staleness');

  mode='hang';await card().getByRole('button',{name:'Refresh invocation'}).click();
  await page.waitForFunction(()=>document.querySelector('.invocation-card button').disabled);
  await card().getByRole('button',{name:'Refresh invocation'}).evaluate(button=>{for(let i=0;i<10;i++)button.click();});
  await page.getByText('State request timed out.',{exact:false}).waitFor();
  await page.waitForFunction(()=>document.querySelector('.invocation-card').dataset.stale==='true');
  assert.equal((await page.evaluate(()=>window.progressReads)).maximum,1);
  await page.screenshot({path:resolve(output,'02-stalled-read-stale.png'),fullPage:true});
  pass('Hung read times out, stale age advances without a response, and repeated refresh cannot overlap a read');
  mode='real';for(const route of held.splice(0))await route.abort().catch(()=>{});
  await page.waitForFunction(()=>document.querySelector('.invocation-card').dataset.stale==='false');
  pass('Polling recovers automatically after a stalled read without redispatch');

  mode='error';await card().getByRole('button',{name:'Refresh invocation'}).click();
  await page.getByText('Retrying; the last report continues to age.',{exact:false}).waitFor();
  mode='real';await page.waitForFunction(()=>document.querySelector('.progress-notice').hidden);
  pass('Transient transport failure retains the report and retries');

  frozen=structuredClone(realResponse);frozen.payload.progress={availability:'UPDATING_OR_UNBOUND',scientific_authority:'NONE'};mode='frozen';
  await card().getByRole('button',{name:'Refresh invocation'}).click();
  await page.getByText('Showing last bound report',{exact:false}).waitFor();
  assert.equal(await page.getByRole('heading',{name:'control.native-iterations',exact:true}).count(),1);
  frozen=structuredClone(realResponse);frozen.payload.context_id=rows[1].context_id;
  await card().getByRole('button',{name:'Refresh invocation'}).click();
  await page.getByText('Invocation identity changed.',{exact:false}).waitFor();
  assert.equal(await card().getAttribute('data-handle'),rows[0].handle);
  pass('Unbound publication retains the last report; cross-context response is refused');

  mode='hang';await card().getByRole('button',{name:'Refresh invocation'}).click();
  await page.waitForFunction(()=>document.querySelector('.invocation-card button').disabled);
  mode='real';await page.locator('#context').selectOption(rows[1].context_id);
  for(const route of held.splice(0))await route.fulfill({json:frozen}).catch(()=>{});
  await page.getByRole('heading',{name:'control.native-iterations',exact:true}).waitFor();
  assert.equal(await card().getAttribute('data-handle'),rows[1].handle);
  pass('Context change disposes the old read; late response cannot mutate the new card');

  await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});
  assert.equal(await card().count(),0);
  const pausedReads=await page.evaluate(()=>window.progressReads.total);
  await page.waitForTimeout(2300);assert.equal(await page.evaluate(()=>window.progressReads.total),pausedReads);
  await page.evaluate(()=>{delete document.hidden;document.dispatchEvent(new Event('visibilitychange'));});
  await page.getByRole('heading',{name:'control.native-iterations',exact:true}).waitFor();
  pass('Controlled hidden-tab event disposes reads and timers; visible-tab event obtains current state');

  worker.kill('SIGSTOP');
  await page.waitForFunction(()=>document.querySelector('.invocation-card').dataset.stale==='true',{},{timeout:16000});
  assert((await card().textContent()).includes('Stale report'));
  worker.kill('SIGCONT');await command('heartbeat');
  await page.waitForFunction(()=>document.querySelector('.invocation-card').dataset.stale==='false');
  pass('Actual stopped telemetry process becomes stale; resumed process publishes a fresh bound report');

  for(const [width,height,name] of [[390,844,'03-narrow'],[1100,800,'04-compact'],[1920,1080,'05-wide']]){
    await page.setViewportSize({width,height});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await page.screenshot({path:resolve(output,`${name}.png`),fullPage:true});
  }
  await page.setViewportSize({width:1366,height:900});await page.evaluate(()=>{document.documentElement.style.zoom='2';});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await page.screenshot({path:resolve(output,'06-two-hundred-percent.png'),fullPage:true});
  await page.evaluate(()=>{document.documentElement.style.zoom='';});
  await page.emulateMedia({reducedMotion:'reduce'});
  const disclosure=card().locator('.details summary');await disclosure.focus();await page.keyboard.press('Enter');
  assert.equal(await card().locator('.details').getAttribute('open'),'');
  await page.keyboard.press('Enter');
  pass('390/1100/1920 pixel layouts, 200 percent zoom, keyboard disclosure and reduced-motion setting');

  await command('return');await card().getByRole('button',{name:'Refresh invocation'}).click();
  await page.getByText('Invocation returned · SUCCEEDED.',{exact:false}).waitFor();
  assert((await card().textContent()).includes('Reopen the original result for scientific findings.'));
  const terminalReads=await page.evaluate(()=>window.progressReads.total);
  await page.waitForTimeout(2300);assert.equal(await page.evaluate(()=>window.progressReads.total),terminalReads);
  await page.screenshot({path:resolve(output,'07-returned.png'),fullPage:true});
  pass('Real retained control return stops polling and supplies no scientific success claim');
  assert(requests.every(path=>path==='/api/invocation-state'));
  assert.deepEqual(errors,[]);
  pass('No application dispatch, replay, scientific read or browser exception');
}catch(error){failure=error.stack||String(error);await page?.screenshot({path:resolve(output,'failure.png'),fullPage:true}).catch(()=>{});}
finally{
  mode='error';for(const route of held.splice(0))await route.abort().catch(()=>{});
  worker.kill('SIGCONT');worker.stdin.end();
  const exited=new Promise(resolve=>worker.once('exit',resolve));
  if(worker.exitCode===null)await Promise.race([exited,new Promise(resolve=>setTimeout(()=>{worker.kill('SIGTERM');resolve();},3000))]);
  await writeFile(resolve(output,'browser-acceptance.json'),JSON.stringify({status:failure?'FAIL':'PASS',
    scope:'EXPOSED_PROCESS_AND_TELEMETRY_CONFORMANCE; REAL_BROKER; CONTROLLED_TRANSPORT_AND_VISIBILITY_FAULTS',
    browser:browser?.version(),checks,requests,errors,workerError,failure},null,2)+'\n');
  await browser?.close();
}
if(failure)throw new Error(failure);
console.log(JSON.stringify({status:'PASS',checks:checks.length,output}));
