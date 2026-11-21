/* SPDX-License-Identifier: MPL-2.0 */
/* Geometry carried from the accepted prototype; no scientific state lives here. */
import {esc} from "./explorer-core.js";
  function recursiveMark(cx,cy,width=90) {
    return `<image class="recursive-mark" href="/el-equal-circles.svg" x="${cx-width/2}" y="${cy-width*250/640}" width="${width}" height="${width*250/320}" aria-hidden="true"/>`;
  }
  function motif(cx,cy,r,id,lines,caption,kind='open',inside='', isSelected=false) {
    const selected=isSelected?' selected':'';
    const label=[...lines,caption].filter(Boolean).join('. ');
    const core=inside&&inside!=='motif'&&inside!=='pair'
      ? `<text class="node-count" text-anchor="middle" x="${cx}" y="${cy+7}">${esc(inside)}</text>`
      : recursiveMark(cx,cy,r*1.8);
    const ring=kind==='complete'
      ? `<path class="ring complete" d="M${cx+r*.91},${cy+r*.41} A${r},${r} 0 1 1 ${cx+r*.91},${cy-r*.41}"/>`
      : `<circle class="ring ${kind}" cx="${cx}" cy="${cy}" r="${r}"/>`;
    return `<g class="graph-node${selected}" role="button" tabindex="0" data-node="${esc(id)}" ${routeShape(id,cx,cy,r)} aria-label="${esc(label)}"><circle class="node-hit" cx="${cx}" cy="${cy}" r="${r+7}"/>${ring}${core}${lines.map((line,i)=>`<text class="node-label" text-anchor="middle" x="${cx}" y="${cy+r+25+i*19}">${esc(line)}</text>`).join('')}<text class="node-caption" text-anchor="middle" x="${cx}" y="${cy+r+29+lines.length*19}">${esc(caption)}</text></g>`;
  }
  const svgStart=(label,height=440,width=760)=>`<svg viewBox="0 0 ${width} ${height}" role="group" aria-label="${esc(label)}"><defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M1 1 L8 5 L1 9" fill="none" stroke="context-stroke" stroke-width="1.4"/></marker></defs>`;
  const routeShape=(id,x,y,r)=>`data-route-id="${esc(id)}" data-cx="${x}" data-cy="${y}" data-radius="${r}"`;
  // Positions express the selected editorial composition. Connections are derived
  // from circle ports and actual font metrics, never independent Bezier handles.
  function connection(from,to,{fromSide='E',toSide='W',kind='edge',label=[],x=0,y=0,direct=false}={}) {
    return `<g class="connection" data-from="${esc(from)}" data-to="${esc(to)}" data-from-side="${fromSide}" data-to-side="${toSide}" data-direct="${direct}"><path class="routed-edge ${kind}"/>${label.length?`<g class="connection-label">${label.map((line,i)=>`<text class="${i?'loop-caption':'edge-label'}" x="${x}" y="${y+i*18}" text-anchor="middle">${esc(line)}</text>`).join('')}</g>`:''}</g>`;
  }
  const inBox=(p,b)=>p.x>b.x&&p.x<b.right&&p.y>b.y&&p.y<b.bottom;
  function clearSegment(a,b,boxes) {
    // Liang–Barsky segment/rectangle clipping also covers diagonal chain links.
    return boxes.every(box=>{
      let low=0,high=1;
      const dx=b.x-a.x,dy=b.y-a.y;
      for(const [p,q] of [[-dx,a.x-box.x],[dx,box.right-a.x],[-dy,a.y-box.y],[dy,box.bottom-a.y]]) {
        if(p===0) {if(q<=0)return true;continue;}
        const t=q/p;
        if(p<0)low=Math.max(low,t);else high=Math.min(high,t);
        if(low>=high)return true;
      }
      return low>=high;
    });
  }
  function orthogonalRoute(start,end,boxes,width,height,deadline) {
    // Visibility grid + shortest path, with a bend penalty. Each coordinate is
    // a port or a padded obstacle boundary; ordinary updates preserve node order.
    const axis=(key,limit)=>[...new Set([16,limit-16,start[key],end[key],...boxes.flatMap(b=>key==='x'?[b.x-4,b.right+4]:[b.y-4,b.bottom+4])])].filter(v=>v>=8&&v<=limit-8).sort((a,b)=>a-b);
    const xs=axis('x',width),ys=axis('y',height),cols=xs.length,count=cols*ys.length;
    const point=i=>({x:xs[i%cols],y:ys[Math.floor(i/cols)]});
    const startIndex=ys.indexOf(start.y)*cols+xs.indexOf(start.x),endIndex=ys.indexOf(end.y)*cols+xs.indexOf(end.x);
    const valid=Array.from({length:count},(_,i)=>!boxes.some(b=>inBox(point(i),b)));
    const distance=new Float64Array(count*3).fill(Infinity),previous=new Int32Array(count*3).fill(-1);
    const queue=[{state:startIndex*3,cost:0}],startState=startIndex*3;
    distance[startState]=0;
    let finish=-1;
    while(queue.length) {
      if(performance.now()>deadline)throw new Error('Diagram routing exceeded its one-second budget. Use the complete outline.');
      queue.sort((a,b)=>b.cost-a.cost);
      const {state:current,cost}=queue.pop();
      if(cost!==distance[current])continue;
      const index=Math.floor(current/3),direction=current%3,a=point(index);
      if(index===endIndex){finish=current;break;}
      const col=index%cols,row=Math.floor(index/cols);
      for(const [next,dir] of [[col>0?index-1:-1,1],[col<cols-1?index+1:-1,1],[row>0?index-cols:-1,2],[row<ys.length-1?index+cols:-1,2]]) {
        if(next<0||!valid[next])continue;
        const b=point(next);
        if(!clearSegment(a,b,boxes))continue;
        const candidate=cost+Math.abs(b.x-a.x)+Math.abs(b.y-a.y)+(direction&&direction!==dir?24:0),nextState=next*3+dir;
        if(candidate>=distance[nextState])continue;
        distance[nextState]=candidate;previous[nextState]=current;queue.push({state:nextState,cost:candidate});
      }
    }
    if(finish<0)throw new Error('No clear connection route in selected diagram');
    const points=[];
    for(let i=finish;i!==-1;i=previous[i])points.push(point(Math.floor(i/3)));
    return points.reverse();
  }
  function roundedPath(points) {
    const clean=[];
    for(const p of points) {
      const b=clean.at(-1),a=clean.at(-2);
      if(b&&p.x===b.x&&p.y===b.y)continue;
      if(a&&((a.x===b.x&&b.x===p.x)||(a.y===b.y&&b.y===p.y)))clean.pop();
      clean.push(p);
    }
    let d=`M${clean[0].x} ${clean[0].y}`;
    for(let i=1;i<clean.length-1;i++) {
      const a=clean[i-1],b=clean[i],c=clean[i+1];
      const ab=Math.hypot(b.x-a.x,b.y-a.y),bc=Math.hypot(c.x-b.x,c.y-b.y),r=Math.min(9,ab/2,bc/2);
      d+=` L${b.x+(a.x-b.x)*r/ab} ${b.y+(a.y-b.y)*r/ab} Q${b.x} ${b.y} ${b.x+(c.x-b.x)*r/bc} ${b.y+(c.y-b.y)*r/bc}`;
    }
    return d+` L${clean.at(-1).x} ${clean.at(-1).y}`;
  }
  function layoutConnections(root=document) {
    const deadline=performance.now()+1000;
    root.querySelectorAll('.canvas>svg').forEach(svg=>{
      const shapes=[...svg.querySelectorAll('[data-route-id]')].map(el=>({id:el.dataset.routeId,x:+el.dataset.cx,y:+el.dataset.cy,r:+el.dataset.radius}));
      const shapeBoxes=shapes.map(s=>({id:s.id,x:s.x-s.r-9,y:s.y-s.r-9,right:s.x+s.r+9,bottom:s.y+s.r+9}));
      const textBoxes=[...svg.querySelectorAll('text')].map(el=>{
        const b=el.getBBox();return {x:b.x-8,y:b.y-8,right:b.x+b.width+8,bottom:b.y+b.height+8};
      }).filter(b=>!shapeBoxes.some(s=>b.x>=s.x&&b.right<=s.right&&b.y>=s.y&&b.bottom<=s.bottom));
      const obstacles=[...shapeBoxes,...textBoxes];
      const port=(s,side,offset)=>{const [dx,dy]={N:[0,-1],E:[1,0],S:[0,1],W:[-1,0]}[side];return {x:s.x+dx*(s.r+offset),y:s.y+dy*(s.r+offset)};};
      svg.querySelectorAll('.connection').forEach(el=>{
        const a=shapes.find(s=>s.id===el.dataset.from),b=shapes.find(s=>s.id===el.dataset.to);
        if(!a||!b)throw new Error('Connection has no declared circle port');
        let points;
        if(el.dataset.direct==='true') {
          const length=Math.hypot(b.x-a.x,b.y-a.y),dx=(b.x-a.x)/length,dy=(b.y-a.y)/length;
          points=[{x:a.x+dx*(a.r+10),y:a.y+dy*(a.r+10)},{x:b.x-dx*(b.r+10),y:b.y-dy*(b.r+10)}];
          if(!clearSegment(...points,[...shapeBoxes.filter(s=>s.id!==a.id&&s.id!==b.id),...textBoxes]))points=null;
        }
        if(!points) {
          const start=port(a,el.dataset.fromSide,23),end=port(b,el.dataset.toSide,23);
          points=[port(a,el.dataset.fromSide,10),...orthogonalRoute(start,end,obstacles,svg.viewBox.baseVal.width,svg.viewBox.baseVal.height,deadline),port(b,el.dataset.toSide,10)];
        }
        el.querySelector('path').setAttribute('d',roundedPath(points));
      });
      svg.dataset.layoutStatus='ready';
    });
  }


export {recursiveMark, motif, svgStart, routeShape, connection, layoutConnections};
