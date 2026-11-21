/* SPDX-License-Identifier: MPL-2.0 */
/* Own a local broker for one bounded browser acceptance, without saving its key. */
import {parseArgs} from 'node:util';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
const {values}=parseArgs({options:{'broker-python':{type:'string'},contexts:{type:'string'},'required-mount':{type:'string'},'session-dir':{type:'string'},
  'output-dir':{type:'string'},playwright:{type:'string'},'expected-file':{type:'string'},suite:{type:'string',default:'originals'},'fixture-mode':{type:'boolean',default:false},phase:{type:'string'}}});
for(const name of ['broker-python','contexts','required-mount','session-dir','output-dir','playwright'])if(!values[name])throw new Error(`Select --${name}.`);
if(!['originals','observations','preparation','return','legacy','progress'].includes(values.suite))throw new Error('Select the originals, observations, preparation, return, legacy or progress suite.');
if(values.phase && (values.suite!=='preparation'||!['all','original','renderer'].includes(values.phase)))throw new Error('A preparation phase selects all, original or renderer checks.');
const broker=spawn(values['broker-python'],['-u','-m','empirical_lawhood.workbench.broker','--contexts',values.contexts,'--required-mount',values['required-mount'],'--output-dir',values['session-dir']],{stdio:['ignore','pipe','pipe']});
let output='',errors='',code=1;
const exited=new Promise(resolve=>broker.once('exit',resolve));
try {
  const url=await new Promise((resolve,reject)=>{
    const timeout=setTimeout(()=>reject(new Error('The selected local broker did not start within 60 seconds.')),60000);
    broker.stdout.on('data',chunk=>{output+=chunk.toString();if(output.length>8192){clearTimeout(timeout);reject(new Error('Broker startup output exceeded its bound.'));return;}
      const match=output.match(/http:\/\/127\.0\.0\.1:\d+\/#session=[A-Za-z0-9_-]+/);if(match){clearTimeout(timeout);resolve(match[0]);}});
    broker.stderr.on('data',chunk=>{if(errors.length<8192)errors+=chunk.toString();});
    broker.once('error',error=>{clearTimeout(timeout);reject(error);});
    broker.once('exit',()=>{clearTimeout(timeout);reject(new Error('The selected broker exited before it supplied its local session. '+errors));});
  });
  const scripts={originals:'./check-workbench.mjs',observations:'./check-observations.mjs',preparation:'./check-preparation-presentation.mjs',return:'./check-return.mjs',legacy:'./check-legacy.mjs',progress:'./check-progress.mjs'};
  const args=[fileURLToPath(new URL(scripts[values.suite],import.meta.url)),'--output-dir',values['output-dir'],'--playwright',values.playwright];
  if(values['expected-file'])args.push('--expected-file',values['expected-file']);
  if(values['fixture-mode'])args.push('--fixture-mode');
  if(values.phase)args.push('--phase',values.phase);
  const child=spawn(process.execPath,args,{stdio:'inherit',env:{...process.env,EL_WORKBENCH_CHECK_URL:url}});
  code=await new Promise((resolve,reject)=>{child.once('exit',resolve);child.once('error',reject);});
} finally {
  broker.kill('SIGINT');
  await Promise.race([exited,new Promise(resolve=>setTimeout(()=>{broker.kill('SIGTERM');resolve();},3000))]);
}
process.exitCode=code||0;
