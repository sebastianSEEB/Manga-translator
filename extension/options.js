const $=s=>document.querySelector(s);
function status(text,error=false){$("#status").textContent=text;$("#status").className=error?"error":"";}
async function send(message){const r=await chrome.runtime.sendMessage(message);if(!r.ok)throw new Error(r.error);return r.data;}
async function save(){
 const token=$("#token").value.trim(),series=$("#series").value.trim();
 if(token.length<32)throw new Error("Copy the full BACKEND_TOKEN from cloud variables or .env.");
 if(!/^[a-z0-9][a-z0-9_-]{0,63}$/.test(series))throw new Error("Use a lowercase series ID with letters, digits, hyphens or underscores.");
 const backendUrl=normalizeBackendUrl($("#backendUrl").value);
 if(backendUrl.startsWith("https://")){
   // Requested only for the chosen origin, directly from the button gesture.
   const granted=await chrome.permissions.request({origins:[backendUrl+"/*"]});
   if(!granted)throw new Error("Allow access to your selected backend to connect.");
 }
 await chrome.storage.local.set({backendUrl,token,series,learning:$("#learning").checked});
}
function action(id,fn){$(id).onclick=async()=>{try{await fn();}catch(e){status(e.message,true);}};}
chrome.storage.local.get(["backendUrl","token","series","learning"]).then(s=>{
 $("#backendUrl").value=s.backendUrl||"http://127.0.0.1:8000";$("#token").value=s.token||"";$("#series").value=s.series||"wangan-midnight";$("#learning").checked=s.learning!==false;
});
action("#save",async()=>{await save();status("Settings saved.");});
action("#connect",async()=>{await save();const list=await send({type:"health"});status("Connected. Series: "+list.map(x=>x.id).join(", "));});
action("#clear",async()=>{await send({type:"clearCache"});status("Backend cache cleared. Use Clear on the page to remove its overlay and learning queue.");});
action("#loadGlossary",async()=>{await save();const value=await send({type:"getGlossary",series:$("#series").value.trim()});$("#glossary").value=JSON.stringify(value,null,2);status("Glossary loaded.");});
action("#saveGlossary",async()=>{await save();await send({type:"putGlossary",series:$("#series").value.trim(),value:JSON.parse($("#glossary").value)});status("Glossary saved; translation cache invalidated.");});
