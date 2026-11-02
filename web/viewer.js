'use strict';

const D=JSON.parse(document.getElementById('atlas-data').textContent);
const $=id=>document.getElementById(id);
const E=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const N=value=>String(value??'').normalize('NFKC').toLowerCase().replace(/[^a-z0-9\u3400-\u9fff]/g,'');
const fieldLabels={stage:'阶段',course:'课程',topics:'主题',title:'主题',pdf_pages:'PDF 页码',pdf_page:'PDF 页码',teaching_upgrade:'升级教学',course_boundary:'课程边界',upgrade_teaching:'升级教学',component:'组件',scope:'范围',code:'代码',id:'编号',evidence_sufficient:'证据足够',concept_gap:'概念缺口',language_only_gap:'语言支持'};
const T=value=>value==null?'':Array.isArray(value)?value.map(T).join('\n'):typeof value==='object'?Object.entries(value).map(([k,v])=>(fieldLabels[k]||k)+'：'+T(v)).join('\n'):String(value);
const B=value=>'<div class="prose">'+E(T(value))+'</div>';
const cm=new Map(D.concepts.map(c=>[c.id,c]));
const om=new Map(D.occurrences.map(o=>[o.id,o]));
const sm=new Map(D.sources.map(s=>[s.id,s]));
const rm=new Map(D.cards.map(r=>[r.id,r]));
let selected=cm.has('BIO12')?'BIO12':D.concepts[0].id;
let tab='timeline',filtered=[];

function openPreview(title,body){
  $('evidenceTitle').textContent=title;
  $('evidenceBody').innerHTML=body;
  if(!$('evidenceDialog').open)$('evidenceDialog').showModal();
  $('evidenceDialog').scrollTop=0;
}

function relationLabel(o){
  return /topic|concept|depth_observations/.test(o.relation)?'限于该主题已核深度，不外推整概念覆盖':o.relation;
}

function stageData(c){
  return c.occurrence_ids.map(id=>om.get(id)).filter(Boolean).sort((a,b)=>(a.sequence_rank??99999)-(b.sequence_rank??99999)||a.position_label.localeCompare(b.position_label,'zh'));
}

function sourceLine(o){
  const s=sm.get(o.source_id);
  if(!s)return '<span class="muted">来源定位待补</span>';
  return '<button class="inline-link" data-source="'+E(s.id)+'">'+E(s.title)+'</button> · PDF '+E(T(o.pdf_pages));
}

function occurrence(o){
  return '<article class="card occ '+(o.first_seen_eligible?'verified':'')+'" id="'+E(o.id)+'"><div class="chips"><span class="chip '+(o.first_seen_eligible?'verified':'')+'">'+(o.first_seen_eligible?'已核正文':'课程证据')+'</span><span class="chip">'+E(relationLabel(o))+'</span></div><h4>'+E(o.position_label)+'</h4>'+B(o.depth_summary)+'<details><summary>查看要求、深度边界与来源</summary><div class="detail-grid"><div><h4>可观察要求 / 产出</h4>'+B(o.expected_outputs)+'<h4>补桥建议与边界</h4>'+B(o.gap)+'</div><div><h4>证据状态</h4>'+B(o.evidence_status)+'<h4>版本与时间口径</h4>'+B(o.version_note||'以所查原件为准')+B(o.teaching_position_status)+'</div></div></details><div class="source-line">'+sourceLine(o)+'</div></article>';
}

function scored(c,q){
  if(!q)return c.canonical_status==='待归并目标'?1:5;
  const terms=[c.id,c.title_zh,c.title_en,...c.aliases].map(N).filter(Boolean);
  if(terms.includes(q))return 100;
  if(terms.some(t=>t.includes(q)))return 80;
  if(terms.some(t=>t.length>=3&&q.includes(t)))return 65;
  const parts=String($('search').value).toLowerCase().match(/[a-z0-9]+|[\u3400-\u9fff]+/g)||[];
  if(parts.length>1&&parts.every(p=>terms.join(' ').includes(N(p))))return 60;
  return c.occurrence_ids.some(id=>{const o=om.get(id);return o&&N(o.title+' '+o.code+' '+o.depth_summary).includes(q)})?30:0;
}

function search(){
  const q=N($('search').value),subject=$('subject').value;
  filtered=D.concepts.filter(c=>!subject||c.subjects.includes(subject)).map(c=>({c,score:scored(c,q)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score||a.c.title_zh.localeCompare(b.c.title_zh,'zh')).map(x=>x.c);
  if(!filtered.some(c=>c.id===selected)&&filtered.length)selected=filtered[0].id;
  $('matchCount').textContent=filtered.length+' 个 CIE 知识点 / 主题组';
  $('results').innerHTML=filtered.length?filtered.map(c=>'<button class="result '+(c.id===selected?'active':'')+'" data-concept="'+E(c.id)+'"><b>'+E(c.title_zh)+'</b><span>'+E(c.title_en)+'</span><span>'+E(c.subjects.join(' · '))+' · '+E(c.id)+'</span></button>').join(''):'<div class="no-results">没有找到直接条目。可换中文、英文、别名或 CIE 课程代码；未命中不代表课程没有该内容。</div>';
  render();
}

function verifiedEvidence(os){
  let rows=os.filter(o=>o.first_seen_eligible&&o.stage.startsWith('国内'));
  const q=N($('search').value);
  if(q){const narrow=rows.filter(o=>[o.title,...(o.search_terms||[])].some(value=>{const n=N(value);return n&&(n.includes(q)||q.includes(n))}));if(narrow.length)rows=narrow;}
  return rows.sort((a,b)=>(a.sequence_rank??99999)-(b.sequence_rank??99999));
}

function summaryEvidence(o,label,kind){
  if(!o)return '';
  return '<div class="summary-box" data-summary="'+kind+'"><div class="label">'+label+'</div><strong>'+E(o.title)+'</strong><div>'+E(o.position_label)+'</div><small>'+E(o.depth_band)+'；'+E(o.version_note||'以所查原件为准')+'</small></div>';
}

function timeline(os){
  return D.stages.map(stage=>{
    const rows=os.filter(o=>o.stage===stage);
    return rows.length?'<section class="stage-section"><div class="stage-head"><h3>'+E(stage)+'</h3><span class="count">'+rows.length+' 条位置 / 线索</span></div>'+rows.map(occurrence).join('')+'</section>':'';
  }).join('');
}

function graph(c,os){
  const stages=D.stages.filter(s=>os.some(o=>o.stage===s));
  const width=Math.max(800,stages.length*260),mid=width/2;
  let paths='',nodes='';
  stages.forEach((stage,i)=>{
    const rows=os.filter(o=>o.stage===stage).sort((a,b)=>Number(b.first_seen_eligible)-Number(a.first_seen_eligible));
    const x=i*260+12;
    nodes+='<text x="'+x+'" y="130" font-size="15" fill="#214e65">'+E(stage)+'</text>';
    rows.slice(0,4).forEach((o,j)=>{
      const y=155+j*125;
      paths+='<path class="edge" marker-end="url(#arr)" d="M'+mid+',78 C'+mid+',110 '+(x+110)+',110 '+(x+110)+','+y+'"/>';
      const lines=[o.position_label.slice(0,20),o.position_label.slice(20,40),o.depth_band||relationLabel(o)];
      nodes+='<g class="node" role="button" tabindex="0" aria-label="'+E(o.title)+'" data-occ="'+E(o.id)+'"><rect x="'+x+'" y="'+y+'" width="232" height="100" rx="8" fill="'+(o.first_seen_eligible?'#e1f2ec':'#fff')+'" stroke="#b1cbd1"/>'+lines.map((line,k)=>'<text x="'+(x+12)+'" y="'+(y+23+k*22)+'" font-size="12" fill="#2b475c">'+E(line.slice(0,25))+'</text>').join('')+'</g>';
    });
    if(rows.length>4)nodes+='<text x="'+x+'" y="675" font-size="12" fill="#637686">另有 '+(rows.length-4)+' 条，见分阶段列表</text>';
  });
  const prior=c.prerequisite_ids.filter(id=>cm.has(id));
  return '<div class="callout">连线表示知识点与课程位置的关联，包含部分交集和先修线索。每阶段最多展示四条，点选节点可在网页中预览完整说明。</div><div class="graph-wrap"><svg width="'+width+'" height="710" viewBox="0 0 '+width+' 710"><defs><marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#b3c9d1"/></marker></defs>'+paths+'<rect x="'+(mid-190)+'" y="12" width="380" height="66" rx="10" fill="#153a54"/><text x="'+mid+'" y="40" fill="white" text-anchor="middle" font-size="18">'+E(c.title_zh.slice(0,23))+'</text><text x="'+mid+'" y="62" fill="#c7e2eb" text-anchor="middle" font-size="12">'+E(c.title_en.slice(0,47))+'</text>'+nodes+'</svg></div>'+(prior.length?'<h3>先修关系（教研建议）</h3><div class="hint">'+prior.map(id=>'<button data-prior="'+E(id)+'">'+E(cm.get(id).title_zh)+'</button>').join('')+'</div>':'');
}

function fullResource(r){
  const m=r.data;
  let body='<div class="chips"><span class="chip">'+E(r.subject)+'</span><span class="chip">原创教学资源 · 网页预览</span></div><p>'+E(m.target_course)+'</p><div class="callout">含教师参考答案；任务表现只支持相应知识点的判断，不能替代整科评估。</div>';
  for(const [key,label] of [['teaching_focus','教学要点'],['prerequisites','先修要求'],['target_topics','CIE 主题定位'],['diagnostic_task','诊断任务'],['diagnostic_solution','诊断参考答案'],['common_misconception','常见误区'],['teaching_activity','教学活动'],['practice_task','迁移练习'],['practice_solution','练习参考答案'],['exit_evidence','退出证据'],['as_a2_extension','CIE AS / A-Level 升级建议'],['transfer_rules','转入判断建议'],['data_notice','示例数据说明'],['teaching_boundary','教学边界']]){
    if(m[key])body+='<h3>'+label+'</h3>'+B(m[key]);
  }
  return body;
}

function resources(c){
  const cards=D.cards.filter(r=>r.concept_ids.includes(c.id));
  if(!cards.length)return '<p class="muted">可先查阅分阶段课程位置。</p>';
  return '<div class="callout">原创诊断、补桥活动与迁移练习均可在网页内展开查看，含教师参考答案。</div>'+cards.map(r=>'<article class="card"><div class="chips"><span class="chip">'+E(r.subject)+'</span><span class="chip">原创教学资源</span></div><h3>'+E(r.card_id)+' '+E(r.title)+'</h3><p class="muted">'+E(r.data.target_course)+'</p>'+B(r.data.teaching_focus)+'<div class="row-actions"><button class="btn primary" data-resource="'+E(r.id)+'">网页预览完整教学卡</button></div></article>').join('');
}

function sourcePreview(s){
  const rows=stageData(cm.get(selected)).filter(o=>o.source_id===s.id);
  return '<span class="chip">'+E(s.kind)+'</span><p>'+E(s.access_note)+'</p><h3>版本说明</h3>'+B(s.version_note||'以所查原件书名、版本及适用年份为准。')+(rows.length?'<h3>当前知识点的定位</h3>'+rows.map(o=>'<div class="trace"><strong>'+E(o.position_label)+'</strong><p>PDF 物理页：'+E(T(o.pdf_pages))+'</p>'+B(o.evidence_status)+'</div>').join(''):'')+'<details class="trace"><summary>查看版本识别信息</summary><p class="muted hash">来源编号：'+E(s.id)+'<br>SHA-256：'+E(s.sha256)+'</p></details>';
}

function evidence(os){
  const sources=[...new Set(os.map(o=>o.source_id))].map(id=>sm.get(id)).filter(Boolean);
  return '<div class="callout">资料快照为 '+E(D.created)+'。“已核”沿用当时的核对记录；本次页面调整没有重新逐页复核全部原件。</div>'+sources.map(s=>'<article class="card"><span class="chip">'+E(s.kind)+'</span><h3>'+E(s.title)+'</h3>'+B(s.version_note||'以所查原件及适用年份为准')+'<p>'+E(s.access_note)+'</p><button class="btn" data-source="'+E(s.id)+'">网页预览来源说明与页码</button></article>').join('')+'<h3>如何理解这些关系</h3>'+Object.values(D.evidence_rules).map(t=>'<p>'+E(t)+'</p>').join('');
}

function conceptPreview(c){
  const os=stageData(c);
  return '<p class="en">'+E(c.title_en)+'</p>'+B(c.definition)+'<p class="muted">别名：'+E(c.aliases.join(' · '))+'</p><div class="callout">'+E(c.relation_warning)+'</div>'+timeline(os);
}

function render(){
  const c=cm.get(selected);
  if(!c||!filtered.length){$('main').innerHTML='<div class="empty">请用中文、英文、别名或 CIE 课程编号检索。</div>';return}
  const hasResources=D.cards.some(r=>r.concept_ids.includes(c.id));
  if(tab==='resources'&&!hasResources)tab='timeline';
  const os=stageData(c),verified=verifiedEvidence(os);
  const systematic=verified.find(o=>/系统|正式定义|运算方法|机制与|定量|方法选择|数系|技能/.test(o.depth_band));
  const summaries=summaryEvidence(verified[0],'所查版本中较早的正文线索','early')+summaryEvidence(systematic,'系统讲解 / 方法入口线索','systematic');
  $('main').innerHTML='<div class="toolbar-line"><div><div class="chips"><span class="chip">'+E(c.id)+'</span><span class="chip">'+E(c.subjects.join(' / '))+'</span></div><h2>'+E(c.title_zh)+'</h2><div class="en">'+E(c.title_en)+'</div></div><button class="btn" data-preview-concept="'+E(c.id)+'">概念卡片预览</button></div><div class="definition">'+E(c.definition)+'</div><p class="muted">别名：'+E(c.aliases.join(' · '))+'</p>'+(/速度/.test($('search').value)?'<div class="disambiguation">请区分速率 speed（路程 / 时间）与矢量速度 velocity（位移变化率），以具体原文定义为准。</div>':'')+'<div class="summary-grid">'+summaries+'<div class="summary-box" data-summary="coverage"><div class="label">当前可查范围</div><strong>'+os.length+' 条课程位置 / 线索</strong><small>CIE 要求与国内先修位置分别查看；课程位置不代表实际授课或学生掌握。</small></div></div>'+(verified[0]?'<div class="callout">'+E(D.evidence_rules.first_seen)+'</div>':'')+'<nav class="tabs" aria-label="知识点视图">'+[['timeline','分阶段查看'],['graph','知识点关系图'],['resources','教学卡预览'],['evidence','来源与证据口径']].filter(([id])=>id!=='resources'||hasResources).map(([id,label])=>'<button data-tab="'+id+'" class="'+(tab===id?'active':'')+'" aria-pressed="'+(tab===id)+'">'+label+'</button>').join('')+'</nav><div id="tabbody">'+(tab==='timeline'?timeline(os):tab==='graph'?graph(c,os):tab==='resources'?resources(c):evidence(os))+'</div><div class="site-footer">'+E(D.release)+' · 资料快照 '+E(D.created)+' · Max Liu<br>原创注释与练习：CC BY 4.0；软件：MIT。独立教研整理，非 CIE 官方对照。</div>';
  try{history.replaceState(null,'','#'+encodeURIComponent(c.id))}catch{}
}

document.addEventListener('click',event=>{
  const button=event.target.closest('[data-concept],[data-prior],[data-tab],[data-occ],[data-resource],[data-source],[data-preview-concept]');
  if(!button)return;
  if(button.dataset.concept||button.dataset.prior){selected=button.dataset.concept||button.dataset.prior;if(button.dataset.prior){$('search').value='';$('subject').value=''}search();}
  else if(button.dataset.tab){tab=button.dataset.tab;render();}
  else if(button.dataset.occ){const o=om.get(button.dataset.occ);if(o)openPreview(o.title,occurrence(o));}
  else if(button.dataset.resource){const r=rm.get(button.dataset.resource);if(r)openPreview(r.card_id+' · '+r.title,fullResource(r));}
  else if(button.dataset.source){const s=sm.get(button.dataset.source);if(s)openPreview(s.title,sourcePreview(s));}
  else if(button.dataset.previewConcept){const c=cm.get(button.dataset.previewConcept);if(c)openPreview(c.title_zh,conceptPreview(c));}
});
document.addEventListener('keydown',event=>{if((event.key==='Enter'||event.key===' ')&&event.target.matches('svg [data-occ]')){event.preventDefault();event.target.dispatchEvent(new MouseEvent('click',{bubbles:true}));}});
$('subject').innerHTML='<option value="">全部科目</option>'+D.subjects.map(s=>'<option>'+E(s)+'</option>').join('');
$('search').oninput=search;$('subject').onchange=search;
$('clear').onclick=()=>{$('search').value='';$('subject').value='';search()};
for(const b of document.querySelectorAll('[data-example]'))b.onclick=()=>{$('search').value=b.dataset.example;$('subject').value='';search()};
$('closeEvidence').onclick=()=>$('evidenceDialog').close();
$('aboutEvidence').onclick=()=>openPreview('证据口径',Object.values(D.evidence_rules).map(t=>'<p>'+E(t)+'</p>').join(''));
try{const initial=decodeURIComponent(location.hash.slice(1));if(cm.has(initial))selected=initial}catch{}
search();
