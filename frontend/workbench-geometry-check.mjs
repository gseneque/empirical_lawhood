/* SPDX-License-Identifier: MPL-2.0 */
/* Inspect rendered SVG geometry independently of the production router. */
import assert from 'node:assert/strict';

export async function settled(page) {
  await page.evaluate(async()=>{
    await document.fonts.ready;
    await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  });
}

export async function geometry(page, name) {
  await settled(page);
  const result=await page.evaluate(()=>{
    const problems=[];
    if(document.documentElement.scrollWidth>innerWidth+1)problems.push('Horizontal document overflow');
    for(const svg of document.querySelectorAll('.canvas>svg')) {
      if(svg.querySelector('.routed-edge')&&svg.dataset.layoutStatus!=='ready')problems.push('Routing did not finish');
      const labels=[...svg.querySelectorAll('text')].map(el=>({text:el.textContent,box:el.getBBox()}));
      for(const [i,a] of labels.entries()) {
        const b=a.box,v=svg.viewBox.baseVal;
        if(b.x<0||b.y<0||b.x+b.width>v.width||b.y+b.height>v.height)problems.push('Clipped text: '+a.text);
        for(const other of labels.slice(i+1)) {
          const c=other.box;
          if(b.x<c.x+c.width&&b.x+b.width>c.x&&b.y<c.y+c.height&&b.y+b.height>c.y)problems.push('Overlapping text: '+a.text+' / '+other.text);
        }
      }
      const circles=[...svg.querySelectorAll('[data-route-id]')].map(el=>({id:el.dataset.routeId,x:+el.dataset.cx,y:+el.dataset.cy,r:+el.dataset.radius}));
      for(const line of svg.querySelectorAll('.routed-edge')) {
        if(!line.getAttribute('d')){problems.push('Empty connection');continue;}
        for(let i=0,length=line.getTotalLength();i<=length;i+=2) {
          const p=line.getPointAtLength(i);
          const text=labels.find(({box:b})=>p.x>b.x-4&&p.x<b.x+b.width+4&&p.y>b.y-4&&p.y<b.y+b.height+4);
          const node=circles.find(c=>Math.hypot(p.x-c.x,p.y-c.y)<c.r+3);
          if(text||node){problems.push('Connection crosses '+(text?'text: '+text.text:'circle: '+node.id));break;}
        }
      }
      for(const group of svg.querySelectorAll('.knowledge-cluster,.contrast-cluster,.knowledge-object,.contrast-object')) {
        const circle=group.querySelector(':scope>.knowledge-group,:scope>.endpoint-group,:scope>.ring');
        if(!circle)continue;
        const cx=circle.cx.baseVal.value,cy=circle.cy.baseVal.value,r=circle.r.baseVal.value;
        for(const text of group.querySelectorAll('text')) {
          const b=text.getBBox();
          if([[b.x,b.y],[b.x+b.width,b.y],[b.x,b.y+b.height],[b.x+b.width,b.y+b.height]].some(([x,y])=>Math.hypot(x-cx,y-cy)>r-5))problems.push('Text outside circle margin: '+text.textContent);
        }
      }
    }
    return {problems,width:innerWidth,height:innerHeight,nodes:document.querySelectorAll('.canvas .graph-node').length,
      edges:document.querySelectorAll('.canvas .routed-edge').length,routingMilliseconds:Number(document.querySelector('#main').dataset.routingMilliseconds||0)};
  });
  assert.deepEqual(result.problems,[],name+' preserves label, circle and connection clearance');
  assert(result.nodes<=16,name+' visible node bound');assert(result.edges<=32,name+' visible edge bound');
  return {name,...result};
}
