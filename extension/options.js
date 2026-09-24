const $=s=>document.querySelector(s);
function status(text,error=false){$("#status").textContent=text;$("#status").className=error?"error":"";}
async function send(message){const r=await chrome.runtime.sendMessage(message);if(!r.ok)throw new Error(r.error);return r.data;}
async function save(){
 const token=$("#token").value.trim(),series=$("#series").value.trim();
 if(token.length<32)throw new Error("Copy the full BACKEND_TOKEN from .env.");
 if(!/^[a-z0-9][a-z0-9_-]{0,63}$/.test(series))throw new Error("Use a lowercase series ID with letters, digits, hyphens or underscores.");
 await chrome.storage.local.set({token,series,learning:$("#learning").checked});
}
function action(id,fn){$(id).onclick=async()=>{try{await fn();}catch(e){status(e.message,true);}};}
chrome.storage.local.get(["token","series","learning"]).then(s=>{
 $("#token").value=s.token||"";$("#series").value=s.series||"wangan-midnight";$("#learning").checked=s.learning!==false;
});
action("#save",async()=>{await save();status("Settings saved.");});
action("#connect",async()=>{await save();const list=await send({type:"health"});status("Connected. Series: "+list.map(x=>x.id).join(", "));});
action("#clear",async()=>{await send({type:"clearCache"});status("Backend cache cleared. Use Clear on the page to remove its overlay and learning queue.");});
action("#loadGlossary",async()=>{await save();const value=await send({type:"getGlossary",series:$("#series").value.trim()});$("#glossary").value=JSON.stringify(value,null,2);status("Glossary loaded.");});
action("#saveGlossary",async()=>{await save();await send({type:"putGlossary",series:$("#series").value.trim(),value:JSON.parse($("#glossary").value)});status("Glossary saved; translation cache invalidated.");});
