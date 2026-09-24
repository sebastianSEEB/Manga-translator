// Run with Playwright installed: node tests/browser_smoke.cjs
// This is a simulated page test, not an installed-extension/live YanMaga test.
const {chromium}=require('playwright');
const path=require('path');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
 const page=await browser.newPage({viewport:{width:1000,height:800}});
 await page.setContent('<html><body style="height:2000px"><main>Simulated manga viewer</main></body></html>');
 await page.evaluate(()=>{
   // Open shadow only in the harness so rendered controls can be asserted.
   const attach=Element.prototype.attachShadow;
   Element.prototype.attachShadow=function(options){return attach.call(this,{...options,mode:'open'})};
   window.listener=null;window.messages=[];
   window.chrome={runtime:{onMessage:{addListener:fn=>window.listener=fn},sendMessage:async m=>{
     window.messages.push(m);
     if(m.type==='poll')return {ok:true,data:{status:'done',result:{width:2000,height:1600,
       regions:[{id:'b000',bbox:[200,100,220,160],jp:'行くぞ',en:"Let's go!",kind:'dialogue',vertical:true}],
       timing_ms:{total:1200},cache_hit:false}}};
     return {ok:true,data:{}};
   }}};
   window.dispatch=(m)=>new Promise(resolve=>window.listener(m,{},resolve));
 });
 await page.addScriptTag({path:path.join(__dirname,'../extension/content.js')});
 const prepared=await page.evaluate(()=>window.dispatch({type:'prepare',learning:false}));
 assert.equal(prepared.metrics.width,1000);
 assert.equal((await page.evaluate(t=>window.dispatch({type:'captured',ticket:t}),prepared.ticket)).valid,true);
 await page.evaluate(p=>window.dispatch({type:'job',id:'test',ticket:p.ticket,metrics:p.metrics}),prepared);
 await page.waitForSelector('.box');
 const bounds=await page.locator('.box').boundingBox();assert.equal(bounds.x,100);assert.equal(bounds.y,50);assert.equal(bounds.width,110);
 await page.locator('select').selectOption('both');assert.equal(await page.locator('.box .jp').textContent(),'行くぞ');
 await page.locator('.box').click();await page.getByRole('button',{name:'Save sentence',exact:true}).click();
 assert.equal(await page.getByText('1 saved',{exact:true}).count(),1);
 await page.locator('select').selectOption('original');assert.equal(await page.locator('.box').count(),0);
 await page.evaluate(()=>window.dispatch({type:'toggle'}));assert.equal(await page.locator('.box').count(),1);
 await page.evaluate(()=>window.scrollTo(0,100));await page.waitForFunction(()=>!document.querySelector('div').shadowRoot.querySelector('.box'));
 const stale=await page.evaluate(()=>window.dispatch({type:'prepare',learning:false}));
 await page.evaluate(()=>window.dispatchEvent(new Event('resize')));
 assert.equal((await page.evaluate(t=>window.dispatch({type:'captured',ticket:t}),stale.ticket)).valid,false);
 console.log('PASS: capture handshake, Retina scaling, bilingual/original toggle, learning queue, scroll invalidation, stale capture rejection.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
