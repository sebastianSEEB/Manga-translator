(()=>{
 if(globalThis.__mangaTranslatorLoaded) return;
 globalThis.__mangaTranslatorLoaded=true;
 const host=document.createElement("div");
 host.style.cssText="all:initial;position:fixed;inset:0;z-index:2147483647;pointer-events:none;";
 document.documentElement.append(host);
 const root=host.attachShadow({mode:"closed"});
 const style=document.createElement("style");style.textContent=`
 *{box-sizing:border-box}button,select{font:13px system-ui;padding:6px 9px;border:1px solid #72918d;border-radius:3px;cursor:pointer;background:#fff;color:#17352f}
 button:hover{background:#e0ece8}button:disabled{opacity:.5} .toolbar{pointer-events:auto;position:fixed;left:12px;bottom:12px;max-width:calc(100vw - 24px);display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:10px;background:#183b37;color:white;border:1px solid #608780;border-radius:4px;font:13px system-ui;box-shadow:0 3px 16px #0004}
 .box{pointer-events:auto;position:absolute;margin:0;padding:2px;border:0;border-radius:2px;background:white;color:#111;display:flex;flex-direction:column;align-items:center;justify-content:center;line-height:1.13;font-family:Arial,sans-serif;text-align:center;overflow:hidden;overflow-wrap:anywhere;cursor:pointer}
 .box:hover{outline:2px solid #158b7e}.box .jp{font-size:10px;color:#555;margin-top:3px}.box.overflow{justify-content:flex-start;overflow:auto;outline:1px dashed #c57814}.box.sfx{font-style:italic;background:#fffE}
 .panel{pointer-events:auto;position:fixed;right:12px;top:12px;width:380px;max-width:calc(100vw - 24px);max-height:calc(100vh - 100px);overflow:auto;background:#fff;color:#18312b;padding:18px;border:1px solid #698a80;border-radius:4px;font:14px/1.5 system-ui;box-shadow:0 4px 25px #0004}
 .panel h2{font-size:17px;margin:0 0 10px}.panel p{white-space:pre-wrap}.panel small{display:block;color:#536760}.word{display:flex;align-items:center;justify-content:space-between;border-top:1px solid #dce5e1;padding:8px 0;gap:8px}ruby{font-size:18px;line-height:2.4}rt{font-size:11px}.reading{font-size:20px}.status{max-width:380px} .hidden{display:none!important}
 `;root.append(style);
 const boxes=document.createElement("div"),toolbar=document.createElement("div"),panel=document.createElement("section");
 toolbar.className="toolbar";panel.className="panel hidden";root.append(boxes,toolbar,panel);
 const state={ticket:0,result:null,metrics:null,mode:"english",learning:true,selected:[],active:false,lessonTicket:0};
 const el=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
 const button=(label,fn)=>{const b=el("button",label);b.onclick=fn;return b;};
 const status=el("span","Ready");status.className="status";
 const mode=el("select");for(const [value,label] of [["english","English"],["original","Original"],["both","Both"]]){const o=el("option",label);o.value=value;mode.append(o);}
 mode.onchange=()=>{state.mode=mode.value;draw();};
 const count=el("span","0 saved");
 toolbar.append(button("Translate",()=>send({type:"translate"}).catch(showError)),mode,status,count,
   button("CSV",()=>exportWords("csv")),button("Anki",()=>exportWords("anki")),
   button("Clear",()=>{invalidate("Cleared");state.selected=[];count.textContent="0 saved";toolbar.classList.add("hidden");}));
 async function send(message){const response=await chrome.runtime.sendMessage(message);if(!response?.ok)throw new Error(response?.error||"Extension disconnected; reload the page.");return response.data;}
 function showError(error){host.style.visibility="visible";toolbar.classList.remove("hidden");status.textContent=error.message||String(error);}
 function metrics(){return {width:innerWidth,height:innerHeight,x:scrollX,y:scrollY,url:location.href,dpr:devicePixelRatio,scale:visualViewport?.scale||1};}
 function same(a,b){return ["width","height","x","y","url","dpr","scale"].every(k=>a[k]===b[k]);}
 function invalidate(message){state.ticket++;state.lessonTicket++;state.active=false;state.result=null;boxes.replaceChildren();panel.replaceChildren();panel.classList.add("hidden");host.style.visibility="visible";status.textContent=message;}
 function pageChanged(){if(state.active||state.result)invalidate("Page changed. Translate again.");}
 addEventListener("scroll",e=>{if(!e.composedPath().includes(host))pageChanged();},true);
 addEventListener("resize",pageChanged);visualViewport?.addEventListener("resize",pageChanged);
 addEventListener("popstate",pageChanged);addEventListener("hashchange",pageChanged);
 addEventListener("pagehide",()=>{invalidate("Page closed");state.selected=[];});
 addEventListener("visibilitychange",()=>{if(document.hidden)pageChanged();});
 addEventListener("pointerdown",e=>{if(!e.composedPath().includes(host))pageChanged();},true);
 addEventListener("keydown",e=>{if(e.key==="Escape"){state.mode="original";mode.value="original";draw();panel.classList.add("hidden");}
   else if(!e.composedPath().includes(host)&&["ArrowLeft","ArrowRight","PageDown","PageUp"," "].includes(e.key))pageChanged();},true);
 const observer=new MutationObserver(changes=>{
   if(changes.some(c=>c.target!==host&&!host.contains(c.target)&&
      !(c.type==="childList"&&[...c.addedNodes,...c.removedNodes].every(n=>n===host)))) pageChanged();
 });
 observer.observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:["src","srcset"]});
 function draw(){
   boxes.replaceChildren();if(!state.result||state.mode==="original")return;
   const sx=state.metrics.width/state.result.width,sy=state.metrics.height/state.result.height;
   for(const region of state.result.regions){
     const [x,y,w,h]=region.bbox;const b=el("button");b.className="box"+(region.kind==="sfx"?" sfx":"");
     b.style.left=x*sx+"px";b.style.top=y*sy+"px";b.style.width=w*sx+"px";b.style.height=h*sy+"px";
     b.setAttribute("aria-label",region.en);b.title="Click for full text";
     b.append(el("span",region.en));if(state.mode==="both"){const jp=el("span",region.jp);jp.className="jp";b.append(jp);}
     boxes.append(b);
     let size=Math.min(region.kind==="sfx"?14:22,Math.max(8,h*sy/3));b.style.fontSize=size+"px";
     while(size>8&&(b.scrollHeight>b.clientHeight||b.scrollWidth>b.clientWidth)){size--;b.style.fontSize=size+"px";}
     if(b.scrollHeight>b.clientHeight||b.scrollWidth>b.clientWidth)b.classList.add("overflow");
     b.onclick=()=>openBubble(region);
   }
 }
 function save(row){if(state.selected.length>=500){showError("Export or clear the 500 saved items first.");return;}
   const existing=state.selected.findIndex(x=>x.jp===row.jp&&x.en===row.en);
   if(existing<0)state.selected.push(row);else if(row.reading)state.selected[existing]=row;
   count.textContent=state.selected.length+" saved";}
 async function exportWords(format){
   if(!state.selected.length){showError("Tap a bubble and save a sentence or word first.");return;}
   try{const {text}=await send({type:"export",rows:state.selected,format});
     const url=URL.createObjectURL(new Blob([format==="csv"?"\ufeff"+text:text],{type:format==="csv"?"text/csv;charset=utf-8":"text/tab-separated-values;charset=utf-8"}));
     const a=el("a");a.href=url;a.download="manga-learning."+(format==="csv"?"csv":"tsv");root.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
   }catch(e){showError(e);}
 }
 async function openBubble(region){
   const ticket=++state.lessonTicket;
   panel.replaceChildren();panel.classList.remove("hidden");
   panel.append(button("Close",()=>panel.classList.add("hidden")),el("h2","Bubble"),el("p",region.jp),el("p",region.en));
   panel.append(button("Save sentence",()=>save({jp:region.jp,en:region.en,reading:"",notes:""})));
   if(!state.learning)return;
   const loading=el("p","Loading reading and word breakdown…");panel.append(loading);
   try{const started=await send({type:"learn",jp:region.jp,en:region.en});
     let lesson;
     const end=Date.now()+240000;
     while(Date.now()<end){
       if(ticket!==state.lessonTicket)return;
       const job=await send({type:"poll",id:started.job_id});
       if(job.status==="error")throw new Error(job.detail);
       if(job.status==="done"){lesson=job.result;break;}
       await new Promise(resolve=>setTimeout(resolve,900));
     }
     if(!lesson)throw new Error("Learning request timed out.");
     if(ticket!==state.lessonTicket)return;loading.remove();
     const reading=el("div");reading.className="reading";
     if(lesson.aligned){for(const word of lesson.words){const ruby=el("ruby",word.surface);if(word.reading&&word.reading!==word.surface)ruby.append(el("rt",word.reading));reading.append(ruby,document.createTextNode(" "));}}
     else reading.textContent=lesson.reading;
     panel.append(reading,button("Save with reading",()=>save({jp:region.jp,en:region.en,reading:lesson.reading,notes:lesson.grammar})));
     for(const word of lesson.words){const row=el("div");row.className="word";const text=el("div",word.surface+" ("+word.reading+") — "+word.meaning);text.append(el("small",word.part_of_speech));row.append(text,button("Save word",()=>save({jp:word.surface,reading:word.reading,en:word.meaning,notes:region.jp})));panel.append(row);}
     panel.append(el("p",lesson.grammar),el("small",lesson.warning));
   }catch(e){if(ticket===state.lessonTicket)loading.textContent=e.message;}
 }
 async function poll(id,ticket,captured){
   const end=Date.now()+240000;
   while(Date.now()<end){
     if(ticket!==state.ticket)return;
     try{const job=await send({type:"poll",id});
       if(ticket!==state.ticket)return;
       if(!same(captured,metrics())){pageChanged();return;}
       if(job.status==="error")throw new Error(job.detail);
       if(job.status==="done"){
         state.active=false;state.result=job.result;state.metrics=captured;
         status.textContent=`${job.result.regions.length} regions · ${(job.result.timing_ms.total/1000).toFixed(1)}s${job.result.cache_hit?" · cached":""}`;
         draw();return;
       }
     }catch(e){state.active=false;showError(e);return;}
     await new Promise(resolve=>setTimeout(resolve,900));
   }
   state.active=false;showError("Timed out waiting for the page. Backend may still be working.");
 }
 chrome.runtime.onMessage.addListener((message,sender,reply)=>{
   if(message.type==="prepare"){
     if(state.active){reply({error:"Already translating this page."});return;}
     if((visualViewport?.scale||1)!==1){reply({error:"Reset pinch zoom before capture. Normal browser zoom is supported."});return;}
     invalidate("Capturing…");state.active=true;state.learning=message.learning;state.mode="english";mode.value="english";
     toolbar.classList.remove("hidden");host.style.visibility="hidden";const ticket=state.ticket,captured=metrics();
     requestAnimationFrame(()=>requestAnimationFrame(()=>reply({ticket,metrics:captured})));return true;
   }
   if(message.type==="captured"){
     host.style.visibility="visible";status.textContent="Translating…";reply({valid:message.ticket===state.ticket});return;
   }
   if(message.type==="job"){
     reply({ok:true});if(message.ticket===state.ticket)poll(message.id,message.ticket,message.metrics);return;
   }
   if(message.type==="error"){
     if(message.ticket===undefined||message.ticket===state.ticket){if(!message.statusOnly)state.active=false;showError(message.message);}reply({ok:true});return;
   }
   if(message.type==="toggle"){state.mode=state.mode==="original"?"english":"original";mode.value=state.mode;draw();reply({ok:true});}
 });
})();
