document.querySelector("#settings").onclick=()=>chrome.runtime.openOptionsPage();
document.querySelector("#translate").onclick=()=>{
  chrome.runtime.sendMessage({type:"translate"});
  window.close();
};
