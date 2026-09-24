const BASE = "http://127.0.0.1:8000";
chrome.storage.local.setAccessLevel({accessLevel:"TRUSTED_CONTEXTS"});
const defaultSettings = {token:"", series:"wangan-midnight", learning:true};
async function settings() { return {...defaultSettings, ...await chrome.storage.local.get(Object.keys(defaultSettings))}; }
async function api(path, method="GET", body) {
  const s=await settings();
  if(!s.token) throw new Error("Open Settings and enter your backend token first.");
  const response=await fetch(BASE+path,{method,headers:{"Authorization":"Bearer "+s.token,
    ...(body===undefined?{}:{"Content-Type":"application/json"})},
    body:body===undefined?undefined:JSON.stringify(body), cache:"no-store",signal:AbortSignal.timeout(25000)});
  if(!response.ok){
    const value=await response.json().catch(()=>({}));
    throw new Error(typeof value.detail==="string"?value.detail:`Backend HTTP ${response.status}`);
  }
  if(path==="/export") return {text:await response.text()};
  return response.json();
}
async function activeTab(){const [tab]=await chrome.tabs.query({active:true,currentWindow:true});return tab;}
async function inject(tab){
  if(!tab?.id || !/^https?:/.test(tab.url||"")) throw new Error("Open an ordinary website tab first.");
  await chrome.scripting.executeScript({target:{tabId:tab.id},files:["content.js"]});
}
async function translate(){
  const tab=await activeTab(); await inject(tab);
  let prepared;
  try{
    const s=await settings();
    if(!s.token) throw new Error("Open Settings and enter your backend token first.");
    prepared=await chrome.tabs.sendMessage(tab.id,{type:"prepare",learning:s.learning});
    if(prepared.error) throw new Error(prepared.error);
    // captureVisibleTab captures the currently active tab: verify it before AND after capture.
    let [current]=await chrome.tabs.query({active:true,windowId:tab.windowId});
    if(current?.id!==tab.id) throw new Error("Tab changed; translate again.");
    const screenshot=await chrome.tabs.captureVisibleTab(tab.windowId,{format:"png"});
    [current]=await chrome.tabs.query({active:true,windowId:tab.windowId});
    if(current?.id!==tab.id) throw new Error("Tab changed during capture; translate again.");
    const confirmed=await chrome.tabs.sendMessage(tab.id,{type:"captured",ticket:prepared.ticket});
    if(!confirmed.valid) throw new Error("Page moved during capture; translate again.");
    const job=await api("/jobs","POST",{image:screenshot,series:s.series});
    await chrome.tabs.sendMessage(tab.id,{type:"job",id:job.job_id,ticket:prepared.ticket,metrics:prepared.metrics});
  }catch(error){
    await chrome.tabs.sendMessage(tab.id,{type:"error",message:error.message,ticket:prepared?.ticket,statusOnly:!!prepared?.error}).catch(()=>{});
    throw error;
  }
}
chrome.commands.onCommand.addListener(async name=>{
  try{if(name==="translate-page") await translate();
    else{const tab=await activeTab();await inject(tab);await chrome.tabs.sendMessage(tab.id,{type:"toggle"});}}
  catch(error){console.warn("Manga Translator:",error.message);}
});
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
  (async()=>{
    if(sender.id!==chrome.runtime.id) throw new Error("Invalid sender.");
    if(message.type==="translate") {await translate(); return {ok:true};}
    if(message.type==="poll" && /^[A-Za-z0-9_-]{20,64}$/.test(message.id)) return api("/jobs/"+message.id);
    if(message.type==="learn") return api("/learn/jobs","POST",{jp:message.jp,en:message.en});
    if(message.type==="export") return api("/export","POST",{rows:message.rows,format:message.format});
    if(message.type==="clearCache") return api("/cache","DELETE");
    // Settings actions are only available to extension pages, never content scripts.
    if(!sender.tab){
      if(message.type==="health") return api("/glossaries");
      if(message.type==="getGlossary") return api("/glossaries/"+encodeURIComponent(message.series));
      if(message.type==="putGlossary") return api("/glossaries/"+encodeURIComponent(message.series),"PUT",message.value);
    }
    throw new Error("Unknown operation.");
  })().then(data=>reply({ok:true,data})).catch(error=>reply({ok:false,error:error.message}));
  return true;
});
