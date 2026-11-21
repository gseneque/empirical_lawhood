/* SPDX-License-Identifier: MPL-2.0 */
/* Run against an actual selected broker; see docs/development/testing.md. */
import {parseArgs} from 'node:util';
import {pathToFileURL} from 'node:url';
import {mkdir, writeFile, readFile, mkdtemp, rm} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {geometry,settled} from './workbench-geometry-check.mjs';

const {values}=parseArgs({options:{url:{type:'string'},'output-dir':{type:'string'},playwright:{type:'string'},'expected-file':{type:'string'},'fixture-mode':{type:'boolean',default:false}}});
values.url ||= process.env.EL_WORKBENCH_CHECK_URL;
for(const field of ['url','output-dir','playwright'])if(!values[field])throw new Error(`Select --${field}.`);
const output=resolve(values['output-dir']);await mkdir(output,{recursive:false});
const expected=values['expected-file']?JSON.parse(await readFile(values['expected-file'],'utf8')):{};
const {chromium}=await import(pathToFileURL(resolve(values.playwright)).href);
if(!process.env.TMPDIR)throw new Error('Select the external browser scratch directory through TMPDIR.');
const profile=await mkdtemp(resolve(process.env.TMPDIR,'el-workbench-browser-'));
const browserContext=await chromium.launchPersistentContext(profile,{channel:'chrome',headless:true,chromiumSandbox:true,
  viewport:{width:1366,height:768},reducedMotion:'reduce',acceptDownloads:true});
const browser=browserContext.browser(),page=await browserContext.newPage();
page.setDefaultTimeout(20000);
const errors=[], requests=[], checks=[], measurements=[];
page.on('pageerror',error=>errors.push(error.message));
page.on('request',request=>{if(request.method()==='POST'){try{const body=request.postDataJSON();requests.push({path:new URL(request.url()).pathname,operation:body.operation,context_id:body.context_id,selection_id:body.parameters?.selection_id});}catch{}}});
async function check(name,run){const start=performance.now();await run();checks.push({name,status:'PASS',elapsed_ms:performance.now()-start});}
async function screenshot(name){await settled(page);await page.screenshot({path:resolve(output,`${name}.png`),fullPage:true});}
async function measure(name){measurements.push(await geometry(page,name));}
async function tab(name){await page.getByRole('tab',{name,exact:true}).click();}
async function action(name,value){await page.locator(`[data-action="${name}"]${value===undefined?'':`[data-value="${value}"]`}`).first().click();}
async function view(name){await page.locator(`[data-view="${name}"]`).click();}
async function close(){await page.keyboard.press('Escape');await page.locator('#modal').waitFor({state:'hidden'});}
async function open(id){await action('open',id);await page.locator('.investigation-brief').waitFor({timeout:180000});assert.equal(await page.locator('#error').isVisible(),false);}
async function contains(locator,texts){const text=await locator.textContent();for(const value of texts)assert(text.includes(value),`Missing displayed text: ${value}`);}
let failure=null;
try {
  await page.goto(values.url,{waitUntil:'domcontentloaded'});
  await check('negotiated collection and three primary destinations',async()=>{
    await page.locator('.result-row').first().waitFor({timeout:60000});
    await page.locator('[data-view="results"]').click();
    assert.equal(await page.locator('.primary-nav button').count(),3);
    if(expected.selection_ids)assert.deepEqual(await page.locator('.result-row').evaluateAll(rows=>rows.map(row=>row.dataset.selection).sort()),[...expected.selection_ids].sort());
    assert.equal(requests.some(row=>row.operation?.startsWith('exploration.')),false,'Listing has no eager scientific read');
  });
  await screenshot('01-results');
  const primary=expected.primary_id||await page.locator('.result-row').first().getAttribute('data-selection');
  await check('original result through the production reader',async()=>{
    await open(primary);
    assert(requests.some(row=>row.operation==='exploration.read'));
    await contains(page.locator('.investigation-brief'),expected.brief_text||[]);
    await measure('original overview');
  });
  await screenshot('02-current');
  await check('local branches and inspection depths do not reread science',async()=>{
    const before=requests.length;
    for(const name of ['Finding','Evidence','Method','Question'])await tab(name);
    if(expected.root_nodes){
      for(const branch of ['physical','contrasts','suppliers','all']){
        await action('branch',branch);await measure(branch);
        if(branch==='contrasts'){
          await screenshot('03-contrasts-m1');
          if(await page.locator('[data-action="case"][data-value="1"]').count()){await action('case','1');await measure('second complete case');}
        }
      }
      assert.equal(await page.locator('.canvas .graph-node').count(),Math.min(16,expected.root_nodes));
      await action('outline','true');
      assert.equal(await page.locator('.outline-row').count(),expected.root_nodes);
      await action('branch','overview');await action('outline','false');
    }
    assert.equal(requests.length,before);
  });
  if(expected.root_nodes){
    await check('persistent cost summary and complete non-additive scenarios',async()=>{
      await action('costs');await contains(page.locator('#modal-body'),['Net saving unavailable','Total unknown','not additive','full delivery cost unknown']);
      assert.equal(await page.locator('.scenario-item').count(),expected.scenario_count);
      if(expected.exact_cost_subtotal)await contains(page.locator('#modal-body'),[expected.exact_cost_subtotal]);
      await screenshot('04-costs');await close();
    });
    await check('fresh exact record and byte-identical explicit download',async()=>{
      await tab('Evidence');await page.getByRole('button',{name:'Read exact original requirement',exact:true}).click();
      await page.locator('#modal-body > pre').waitFor({timeout:180000});
      const raw=await page.locator('#modal-body > pre').textContent();
      const digest=createHash('sha256').update(raw).digest('hex');
      if(expected.exact_record_sha256)assert.equal(digest,expected.exact_record_sha256);
      const event=page.waitForEvent('download');await action('download');const download=await event;
      const path=resolve(output,'exact-original-record.json');await download.saveAs(path);
      assert.equal(await readFile(path,'utf8'),raw);
      await screenshot('05-exact-record');await close();
      await page.waitForFunction(()=>document.activeElement.textContent.includes('Read exact original requirement'));
    });
    await check('declared method source from the selected engine',async()=>{
      await tab('Method');await action('method-source');
      await page.locator('#modal-body > pre').waitFor({timeout:180000});
      await contains(page.locator('#modal-body'),['CURRENT_SELECTED_READER_IMPLEMENTATION','def ']);
      await screenshot('06-method-source');await close();
    });
    await check('local metadata observation does not repeat scientific reconstruction',async()=>{
      const before=requests.length;await action('observe');await page.locator('.observation-status').waitFor({timeout:60000});
      assert.deepEqual(requests.slice(before).map(row=>row.operation),['exploration.execution']);
      await contains(page.locator('.activity-panel'),['Succeeded','No scientific reconstruction']);
      assert.equal(await page.locator('[data-action="pause-observation"]').count(),0);
    });
    await check('separate original assessment, runtime evidence and contribution preserve their scopes',async()=>{
      await tab('Evidence');
      for(const [role,phrases] of [['assessment',['SEPARATE_CLOSED_STANDALONE_ASSESSMENT','ORIGINAL_SOURCE_PUBLICATIONS_AND_INDEPENDENT_JOINT_RECONSTRUCTION']],
        ['methods',['RETAINED_AUDIT_METHOD_OBSERVATION','8.3.1','1.8.1','UNAVAILABLE_IN_THIS_EVENT']],
        ['contribution',['NON_PROMOTABLE','NOT_ESTABLISHED','AUTHENTICATED']]]){
        await action('companion',role);await page.locator('#modal-body > pre').waitFor({timeout:180000});
        await contains(page.locator('#modal-body'),phrases);
        if(role==='contribution'){
          const report=JSON.parse(await page.locator('#modal-body > pre').textContent());
          assert.equal(report.contribution.value.products.length,2);
          assert(report.contribution.value.products.every(row=>row.value.evidence_ceiling==='NON_PROMOTABLE'));
        }
        await screenshot('06-companion-'+role);await close();
      }
    });
  }
  await check('knowledge lenses preserve the selected investigation',async()=>{
    await view('knowledge');
    await page.locator('[data-action="lens"]').first().waitFor();
    const title=await page.locator('.inspector h2').textContent();
    for(const lens of ['programme','discipline']){
      await action('lens',lens);assert.equal(await page.locator('.inspector h2').textContent(),title);
      await measure('Knowledge '+lens);await screenshot('07-knowledge-'+lens);
    }
    if(expected.root_nodes){
      await contains(page.locator('.scientific-neighbourhood'),['Relationships in the opened original','Unselected supplier proposals']);
      await action('scientific-relationship');await contains(page.locator('#modal-body'),['REQUIRES','source','scope']);await close();
    }
    if(await page.locator('.relationship-row').count()){
      await action('relationship');await contains(page.locator('#modal-body'),['INFORMING_REFERENCE','NO_ASSESSED_SCIENTIFIC_SUPPLY']);await close();
    }
    await view('current');
  });
  await check('responsive geometry, compact inspector and reduced motion',async()=>{
    for(const [width,height] of [[1366,768],[1920,1080],[2734,1500],[1100,900],[390,844],[960,540]]){
      await page.setViewportSize({width,height});await measure('current '+width);await screenshot('08-current-'+width);
      if(width===1100)assert.equal(await page.locator('.workspace').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length),1);
      if(width===390)assert.equal(await page.locator('[data-action="outline"][data-value="true"]').getAttribute('aria-pressed'),'true');
    }
    assert(await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches));
    await page.setViewportSize({width:1366,height:768});
    await action('outline','false');
  });
  await check('actual 200 percent Chrome zoom retains geometry and accessible text contrast',async()=>{
    const settings=await browserContext.newPage();
    await settings.goto('chrome://settings/appearance');
    await settings.evaluate(()=>new Promise(resolve=>chrome.settingsPrivate.setDefaultZoom(2,resolve)));
    await page.setViewportSize({width:1920,height:1080});await page.bringToFront();
    await page.waitForFunction(()=>devicePixelRatio===2&&innerWidth===960);
    assert.equal(await page.locator('.investigation-brief').isVisible(),true);
    await measure('Chrome 200% zoom');await screenshot('09-actual-200-percent-zoom');
    const ratios=await page.evaluate(()=>{
      const css=getComputedStyle(document.documentElement);
      const luminance=hex=>{const rgb=hex.trim().replace('#','').match(/../g).map(v=>parseInt(v,16)/255)
        .map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];};
      const background=luminance('#28363d');
      return Object.fromEntries(['--white','--muted','--gold','--gold-soft','--green','--red','--paper-muted']
        .map(name=>[name,(luminance(css.getPropertyValue(name))+.05)/(background+.05)]));
    });
    for(const [name,ratio] of Object.entries(ratios))assert(ratio>=4.5,`${name} text contrast ${ratio}`);
    measurements.push({name:'primary text palette against lightest ordinary dark surface',ratios,minimum:4.5});
    await settings.evaluate(()=>new Promise(resolve=>chrome.settingsPrivate.setDefaultZoom(1,resolve)));
    await settings.close();await page.setViewportSize({width:1366,height:768});await page.bringToFront();
    await page.waitForFunction(()=>devicePixelRatio===1);await action('outline','false');
  });
  await check('keyboard inspector and equivalent complete outline',async()=>{
    await tab('Question');await page.keyboard.press('ArrowRight');
    assert.equal(await page.getByRole('tab',{name:'Finding',exact:true}).getAttribute('aria-selected'),'true');
    if(expected.root_nodes){
      await action('branch','physical');await action('outline','true');await page.locator('.outline-row').first().focus();await page.keyboard.press('Enter');
      assert(await page.locator('.outline-row').first().evaluate(el=>el===document.activeElement));
      await action('branch','overview');await action('outline','false');
    }
  });
  await check('selected collection search and programme filters have no scientific side effects',async()=>{
    await view('results');const before=requests.length;
    const title=await page.locator('.result-row').first().getAttribute('data-selection');
    const label=await page.locator('.result-row').first().locator('h2').textContent();
    await page.locator('#search').fill(label);assert.equal(await page.locator('.result-row').count(),1);
    assert.equal(await page.locator('.result-row').first().getAttribute('data-selection'),title);
    await page.locator('#search').fill('no such investigation in this selected collection');assert.equal(await page.locator('.result-row').count(),0);
    await page.locator('#search').fill('');
    const programmes=await page.locator('#programme-filter option').evaluateAll(rows=>rows.slice(1).map(row=>row.value));
    for(const programme of programmes){await page.locator('#programme-filter').selectOption(programme);assert(await page.locator('.result-row').count()>0);}
    await page.locator('#programme-filter').selectOption('all');assert.equal(requests.length,before);
  });
  for(const id of expected.selection_ids||[]){
    if(id===primary)continue;
    await check('original selected reader: '+id,async()=>{
      await open(id);await tab('Finding');
      await contains(page.locator('#inspector-content'),expected.finding_text?.[id]||[]);
      await screenshot('09-original-'+id);await view('results');
    });
  }
  await check('late original responses cannot repopulate a changed context',async()=>{
    const alternate=await page.locator('#context option').evaluateAll(rows=>rows.map(row=>row.value).find(id=>id!=='rubisco.original'));
    if(!alternate||!expected.root_nodes)return;
    let release,arrived;
    const gate=new Promise(resolve=>release=resolve),ready=new Promise(resolve=>arrived=resolve);
    let captured=false;
    const delayed=async route=>{
      const request=route.request().postDataJSON();
      if(request.operation!=='exploration.read'||captured){await route.continue();return;}
      captured=true;const response=await route.fetch({timeout:180000});arrived();await gate;await route.fulfill({response});
    };
    await page.route('**/api/invoke',delayed);
    try {
      await action('open',primary);await ready;
      await page.locator('#context').selectOption(alternate);
      assert.equal(await page.locator('.investigation-brief').count(),0);
      const delivered=page.waitForResponse(response=>response.url().endsWith('/api/invoke'));
      release();await delivered;await page.waitForTimeout(200);
      assert.equal(await page.locator('.investigation-brief').count(),0);
      assert.equal(await page.locator('#modal').isVisible(),false);
    } finally {release();await page.unroute('**/api/invoke',delayed);}
    await page.locator('#context').selectOption('rubisco.original');
    await page.locator('.result-row').first().waitFor({timeout:60000});
  });
  await check('a disclosed current-access refusal clears previously displayed science',async()=>{
    if(!expected.root_nodes)return;
    await open(primary);await tab('Evidence');
    const refuse=async route=>{
      if(route.request().postDataJSON().operation!=='exploration.record'){await route.continue();return;}
      await route.fulfill({status:200,contentType:'application/x-ndjson',body:JSON.stringify({event:'result',payload:{status:'REFUSED',
        errors:[{reason_code:'CURRENT_CUSTODY_REFUSED',message:'Disclosed transport refusal control.'}]}})+'\n'});
    };
    await page.route('**/api/invoke',refuse);
    try {
      await action('record','result');await page.locator('#error').waitFor();
      await contains(page.locator('#error'),['CURRENT_CUSTODY_REFUSED']);
      assert.equal(await page.locator('.investigation-brief').count(),0);
      assert.equal(await page.locator('#modal').isVisible(),false);
    } finally {await page.unroute('**/api/invoke',refuse);}
  });
  await check('navigation preferences survive reload without retaining scientific bodies',async()=>{
    await view('knowledge');await page.locator('.lens-switch').waitFor();await action('lens','discipline');
    const before=requests.length;await page.reload();await page.locator('.lens-switch').waitFor({timeout:60000});
    assert.equal(await page.locator('[data-action="lens"][data-value="discipline"]').getAttribute('aria-pressed'),'true');
    assert.equal(requests.slice(before).some(row=>row.operation?.startsWith('exploration.')),false);
    const saved=await page.evaluate(()=>JSON.parse(localStorage.getItem('el-explorer-navigation')));
    assert.deepEqual(Object.keys(saved).sort(),['contextId','nav','version']);
    assert(!JSON.stringify(saved).includes('/media/'));assert(!JSON.stringify(saved).includes('canonical_text'));
  });
  await check('secondary tools remain available and navigation dispatches no effects',async()=>{
    const response=await page.request.get(new URL('/tools.html',values.url).href);assert.equal(response.status(),200);
    await page.goto(new URL('/tools.html',values.url).href);await page.locator('#context:not([disabled])').waitFor({timeout:60000});
    assert.equal(await page.title(),'Empirical Lawhood · Research workbench');
    for(const name of ['design','programme','inquiry','knowledge','workflows','invocations','context']){
      await page.locator('#nav-'+name).click();await page.locator('#page-title').waitFor();
      assert.equal(await page.locator('#error').isVisible(),false);
    }
    assert.equal(requests.some(row=>/register|\.run$|\.apply$|\.prepare$|\.import$|record-return|\.export$/.test(row.operation||'')),false);
    assert.equal((await page.request.get(new URL('/not-a-fixed-asset',values.url).href)).status(),404);
  });
  assert.deepEqual(errors,[]);
} catch(error) {failure=error.stack||String(error);await screenshot('failure').catch(()=>{});}
finally {
  await writeFile(resolve(output,'browser-acceptance.json'),JSON.stringify({status:failure?'FAIL':'PASS',browser:browser.version(),fixture_mode:values['fixture-mode'],expected_source:values['expected-file']||null,
    zoom_scope:'Chrome default zoom set to 200%; verified devicePixelRatio 2 and 960 CSS pixels in a 1920-pixel viewport',checks,measurements,errors,requests,failure},null,2)+'\n');
  await browserContext.close();await rm(profile,{recursive:true});
}
if(failure)throw new Error(failure);
console.log(JSON.stringify({status:'PASS',checks:checks.length,output}));
