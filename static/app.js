let activeId = null;
let pollHandle = null;

const $ = (id) => document.getElementById(id);
function fmtTime(ts){try{return new Date(ts).toLocaleTimeString([], {hour12:false,hour:'2-digit',minute:'2-digit',second:'2-digit'})}catch{return ts}}
function esc(s){return String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
async function api(path, options={}){const res=await fetch(path,{headers:{'Content-Type':'application/json',...(options.headers||{})},...options});if(!res.ok)throw new Error(await res.text());return res.json();}

function render(i){
  activeId=i.id;
  $('incidentTitle').textContent=i.title;
  $('pipeline').textContent=i.pipeline;
  $('risk').textContent=(i.risk?.level||'—').toUpperCase();
  $('assets').textContent=(i.blast_radius||[]).length;
  const selected=i.selected_fix;
  $('validation').textContent=selected?`${selected.checks_passed}/${selected.checks_total} pass`:'—';
  $('agentMode').textContent=i.agent_mode;
  $('rootCause').textContent=i.diagnosis?.root_cause||'Investigating…';
  $('evidence').textContent=(i.diagnosis?.evidence||[]).join(' • ')||'Collecting incident evidence.';
  $('repair').textContent=selected?.summary||'Waiting for candidate evaluation';
  $('patch').textContent=selected?.patch||'—';
  $('verification').textContent=i.verification?.pipeline_run==='success'?'Pipeline healthy':'Not complete';
  $('verificationDetail').textContent=i.verification?.checks?Object.entries(i.verification.checks).map(([k,v])=>`${k}: ${v}`).join(' • '):'No change has been verified yet.';
  $('report').textContent=i.incident_report||'After verification, the agent writes a concise report from the recorded evidence.';
  const st=$('statusPill');st.textContent=i.status.replaceAll('_',' ').toUpperCase();st.className='status '+(i.status==='resolved'?'ok':i.status==='failed'?'error':'active');
  $('approvalBox').classList.toggle('hidden',i.status!=='awaiting_approval');
  $('timeline').innerHTML=(i.timeline||[]).map(e=>`<div class="event ${esc(e.severity)}"><time>${esc(fmtTime(e.timestamp))}</time><span class="agent">${esc(e.agent)}</span><div class="msg">${esc(e.message)}</div></div>`).join('')||'<div class="empty">No events yet.</div>';
  if(['resolved','failed'].includes(i.status)&&pollHandle){clearInterval(pollHandle);pollHandle=null;}
}
async function poll(){if(!activeId)return;try{render(await api(`/api/incidents/${activeId}`));}catch(e){console.error(e)}}
$('injectBtn').onclick=async()=>{$('injectBtn').disabled=true;try{const out=await api('/api/demo/inject',{method:'POST',body:JSON.stringify({scenario:'schema_drift'})});activeId=out.incident_id;await poll();if(pollHandle)clearInterval(pollHandle);pollHandle=setInterval(poll,650);}finally{$('injectBtn').disabled=false;}};
$('approveBtn').onclick=async()=>{if(activeId){await api(`/api/incidents/${activeId}/approval`,{method:'POST',body:JSON.stringify({approved:true,actor:'hackathon-demo'})});await poll();}};
$('rejectBtn').onclick=async()=>{if(activeId){await api(`/api/incidents/${activeId}/approval`,{method:'POST',body:JSON.stringify({approved:false,actor:'hackathon-demo'})});await poll();}};
$('resetBtn').onclick=async()=>{await api('/api/demo/reset',{method:'POST'});activeId=null;if(pollHandle)clearInterval(pollHandle);location.reload();};
(async()=>{try{const incidents=await api('/api/incidents');if(incidents.length){render(incidents[0]);if(!['resolved','failed'].includes(incidents[0].status))pollHandle=setInterval(poll,650);}}catch(e){console.error(e)}})();
