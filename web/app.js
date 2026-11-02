const D=JSON.parse(document.getElementById('atlas-data').textContent);
function relationLabel(o){return /topic|concept|depth_observations/.test(o.relation)?'限于该主题已核深度，不外推整概念覆盖':o.relation}
// No analytics, account, upload, local teaching records or third-party runtime.
function resources(c){
  const cards=D.cards.filter(r=>r.concept_ids.includes(c.id));
  return '<div class="callout">原创诊断与补桥教学卡，含教师参考答案。任务表现只支持相应知识点的判断；不是官方试题或整科掌握证明。</div>'+(cards.length?cards.map(r=>{
    const m=r.data;
    let body='<article class="card"><div class="chips"><span class="chip">'+E(r.subject)+'</span><span class="chip">原创教学资源</span></div><h3>'+E(r.card_id)+' '+E(r.title)+'</h3><p class="muted">'+E(m.target_course)+'</p><h4>教学要点</h4>'+B(m.teaching_focus)+'<h4>先修要求（教研建议）</h4>'+B(m.prerequisites);
    body+='<details><summary>展开诊断、活动和参考答案</summary>';
    for(const [key,label] of [['diagnostic_task','诊断任务'],['diagnostic_solution','诊断参考答案'],['common_misconception','常见误区'],['teaching_activity','教学活动'],['practice_task','迁移练习'],['practice_solution','练习参考答案'],['exit_evidence','退出证据']])if(m[key])body+='<h4>'+label+'</h4>'+B(m[key]);
    body+='</details>';
    if(m.as_a2_extension||m.board_bridges||m.ncuk_bridge||m.ncuk_links){
      body+='<details class="trace"><summary>查看 AS / A-Level、考试局与 NCUK 接续建议</summary>';
      for(const [key,label] of [['as_a2_extension','AS / A-Level 升级'],['board_bridges','考试局接续'],['ncuk_bridge','NCUK 接续'],['ncuk_links','NCUK 对应线索'],['transfer_rules','转入判断']])if(m[key])body+='<h4>'+label+'</h4>'+B(m[key]);
      body+='</details>';
    }
    if(m.data_notice)body+='<p class="muted">'+E(m.data_notice)+'</p>';
    return body+'<p><a href="'+E(noteLink(r.note))+'" target="_blank" rel="noopener noreferrer">查看完整教学卡 Markdown ↗</a></p></article>';
  }).join(''):'<div class="empty">暂未挂接教学卡；请查分阶段课程位置。</div>');
}

function evidence(c,os){
  const sources=[...new Set(os.map(o=>o.source_id))].map(id=>sm.get(id)).filter(Boolean);
  return '<div class="callout">资料快照为 '+E(D.created)+'；本次公开发布未重新核验全部教材和大纲。下列“已核”状态指原快照中的核对记录。</div>'+
    sources.map(s=>'<article class="card"><span class="chip">'+E(s.kind)+'</span><h3>'+E(s.title)+'</h3>'+B(s.version_note||'以书名及所查原件为准；未补充认定具体印次。')+'<p>'+E(s.access_note)+'</p><p class="muted hash">SHA-256：'+E(s.sha256)+'</p><div class="row-actions"><a class="btn" href="'+E(noteLink(s.note))+'" target="_blank" rel="noopener noreferrer">书目与定位记录 ↗</a><a class="btn" href="'+E(s.official_entry)+'" target="_blank" rel="noopener noreferrer">机构 / 平台入口 ↗</a></div><p class="muted">入口不等于该哈希原件的下载地址；请核对课程代码、版次与适用年份。</p></article>').join('')+
    '<h3>如何理解这些关系</h3>'+Object.values(D.evidence_rules).map(t=>'<p>'+E(t)+'</p>').join('');
}

function render(){
  const c=cm.get(selected);
  if(!c||!filtered.length){$('main').innerHTML='<div class="empty">请用中文、英文、别名或课程编号检索。未命中不代表课程没有该内容。</div>';return}
  const os=stageData(c),verified=specificVerified(os);
  const systematic=verified.find(o=>/系统|正式定义|运算方法|机制与|定量|方法选择|数系|技能/.test(o.depth_band));
  $('main').innerHTML='<div class="toolbar-line"><div><div class="chips"><span class="chip">'+E(c.id)+'</span><span class="chip">'+E(c.subjects.join(' / '))+'</span><span class="chip">'+E(c.canonical_status)+'</span></div><h2>'+E(c.title_zh)+'</h2><div class="en">'+E(c.title_en)+'</div></div><div class="row-actions"><a class="btn" href="'+E(noteLink(c.note))+'" target="_blank" rel="noopener noreferrer">Markdown 笔记 ↗</a><button class="btn" id="exportConcept">导出此知识点</button></div></div><div class="definition">'+E(c.definition)+'</div><p class="muted">别名：'+E(c.aliases.join(' · '))+'</p>'+
    (/速度/.test($('search').value)?'<div class="disambiguation">请区分速率 speed（路程 / 时间）与矢量速度 velocity（位移变化率）；以具体原文定义为准。</div>':'')+
    '<div class="summary-grid"><div class="summary-box"><div class="label">所查版本中较早的正文线索</div>'+smallSummary(verified[0],'尚未核到可确定的早期正文')+'</div><div class="summary-box"><div class="label">系统讲解 / 方法入口线索</div>'+smallSummary(systematic,'尚未核到系统讲解的窄主题证据')+'</div><div class="summary-box"><div class="label">当前可查范围</div><strong>'+os.length+' 条课程位置 / 线索</strong><small>资料快照 '+E(D.created)+'。课程要求与示例周次不代表实际授课或学生掌握。</small></div></div>'+
    '<div class="callout">'+E(D.evidence_rules.first_seen)+' 深度请看每条具体要求、仍需补足什么及证据状态。</div><nav class="tabs" aria-label="知识点视图">'+[['timeline','分阶段查看'],['graph','知识点关系图'],['resources','教学卡与接续'],['evidence','来源与证据口径']].map(([id,t])=>'<button data-tab="'+id+'" class="'+(tab===id?'active':'')+'" aria-pressed="'+(tab===id)+'">'+t+'</button>').join('')+'</nav><div id="tabbody">'+(tab==='timeline'?timeline(c,os):tab==='graph'?graph(c,os):tab==='resources'?resources(c):evidence(c,os))+'</div><div class="site-footer">公开版 '+E(D.release)+' · 发布于 '+E(D.published)+' · 原创注释与练习：CC BY 4.0；软件：MIT。<br>本项目独立整理，非课程机构官方对照或教学效果认证。</div>';
  for(const b of document.querySelectorAll('[data-tab]'))b.onclick=()=>{tab=b.dataset.tab;render()};
  for(const b of document.querySelectorAll('[data-prior]'))b.onclick=()=>{selected=b.dataset.prior;$('search').value='';$('subject').value='';search()};
  for(const b of document.querySelectorAll('[data-occ]'))b.onclick=()=>{const o=om.get(b.dataset.occ);$('evidenceTitle').textContent=o.title;$('evidenceBody').innerHTML=occ(o);$('evidenceDialog').showModal()};
  $('exportConcept').onclick=()=>download(c.id+'_'+c.title_zh+'.json',{schema_version:D.schema_version,concept:c,occurrences:os,sources:[...new Set(os.map(o=>o.source_id))].map(id=>sm.get(id)).filter(Boolean),evidence_rules:D.evidence_rules});
  try{history.replaceState(null,'','#'+encodeURIComponent(c.id))}catch{}
}

function noteLink(note){return 'https://github.com/MaxLiu1979/Curriculum-Bridge-Atlas/blob/main/'+note.split('/').map(encodeURIComponent).join('/')}
function source(o){
  const s=sm.get(o.source_id);
  if(!s)return '<span class="muted">原件定位待补；仅作为教研线索</span>';
  return '<a href="'+E(noteLink(s.note))+'" target="_blank" rel="noopener noreferrer">'+E(s.title)+'</a> · PDF '+E(T(o.pdf_pages))+' <span class="muted">'+E(s.id)+' · 原件未随库分发</span>';
}
const $=id=>document.getElementById(id),E=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const N=x=>String(x??'').toLowerCase().replace(/[^a-z0-9\u3400-\u9fff]/g,''),T=x=>x==null?'':Array.isArray(x)?x.map(T).join('、'):typeof x==='object'?Object.entries(x).map(([k,v])=>k+'：'+T(v)).join('\n'):String(x),B=x=>'<div class="prose">'+E(T(x))+'</div>';
const cm=new Map(D.concepts.map(c=>[c.id,c])),om=new Map(D.occurrences.map(o=>[o.id,o])),sm=new Map(D.sources.map(s=>[s.id,s]));
let selected=D.concepts.find(c=>c.id==='BIO12')?.id||D.concepts[0].id,tab='timeline',filtered=[];
function scored(c,q){if(!q)return c.canonical_status==='待归并目标'?1:5;let terms=[c.id,c.title_zh,c.title_en,...(c.aliases||[])].map(N).filter(Boolean);if(terms.includes(q))return 100;if(terms.some(t=>t.includes(q)))return 80;if(terms.some(t=>t.length>=3&&q.includes(t)))return 65;let qs=String($('search').value).toLowerCase().match(/[a-z0-9]+|[\u3400-\u9fff]+/g)||[];let hay=terms.join(' ');if(qs.length>1&&qs.every(t=>hay.includes(N(t))))return 60;let score=0;for(const id of c.occurrence_ids){let o=om.get(id);if(o&&N(o.title+' '+o.code+' '+o.depth_summary).includes(q))score=Math.max(score,30)}return score}
function search(){let q=N($('search').value),sub=$('subject').value;filtered=D.concepts.filter(c=>!sub||(c.subjects||[c.subject]).includes(sub)).map(c=>({c,score:scored(c,q)})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score||a.c.title_zh.localeCompare(b.c.title_zh,'zh')).map(x=>x.c);if(!filtered.some(c=>c.id===selected)&&filtered.length)selected=filtered[0].id;$('matchCount').textContent=filtered.length+' 个知识点 / 主题组';$('results').innerHTML=filtered.length?filtered.map(c=>'<button class="result '+(c.id===selected?'active':'')+'" data-concept="'+E(c.id)+'"><b>'+E(c.title_zh)+'</b><span>'+E(c.title_en)+'</span><span>'+E((c.subjects||[c.subject]).join(' · '))+' · '+E(c.id)+(c.canonical_status==='待归并目标'?' · 待归并目标':'')+'</span></button>').join(''):'<div class="no-results">没有找到直接条目。可换中文、英文、课程代码或近义词；未命中不代表课程没有该内容。</div>';for(const b of document.querySelectorAll('[data-concept]'))b.onclick=()=>{selected=b.dataset.concept;search()};render()}
function specificVerified(os){let ls=os.filter(o=>o.first_seen_eligible&&o.stage.startsWith('国内')),q=N($('search').value);if(q){let narrow=ls.filter(o=>[o.title,...(o.search_terms||[])].some(s=>{let n=N(s);return n&&(n.includes(q)||q.includes(n))}));if(narrow.length)ls=narrow;}return ls.sort((a,b)=>(a.sequence_rank??99999)-(b.sequence_rank??99999))}
function smallSummary(o,empty){return o?'<strong>'+E(o.title)+'</strong><div>'+E(o.position_label)+'</div><small>'+E(o.depth_band)+'；'+E(o.version_note||'以所查原件为准')+'</small>':'<strong>'+E(empty)+'</strong>'}
function occ(o){let verified=o.first_seen_eligible,week=!!o.week_in_plan;return '<article class="card occ '+(verified?'verified':'')+'" id="'+E(o.id)+'"><div class="chips"><span class="chip '+(verified?'verified':week?'pending':'')+'">'+E(verified?'已核正文':week?'示例计划，非实授':'课程证据')+'</span><span class="chip">'+E(relationLabel(o))+'</span></div><h4>'+E(o.position_label)+'</h4>'+B(o.depth_summary)+'<details><summary>查看要求、深度边界与原件证据</summary><div class="detail-grid"><div><h4>可观察要求 / 产出</h4>'+B(o.expected_outputs)+'<h4>尚需补足或不能推出什么</h4>'+B(o.gap)+'</div><div><h4>证据状态</h4>'+B(o.evidence_status)+'<h4>时间与版次口径</h4>'+B(o.teaching_position_status)+B(o.version_note)+(week?B(o.timing_status):'')+'<p class="muted">实际授课：本条是课程证据，未填真实授课日期。</p></div></div></details><div class="source-line">'+source(o)+' · <a href="'+E(noteLink(o.note))+'">查看此条 Markdown</a></div></article>'}
function stageData(c){return c.occurrence_ids.map(id=>om.get(id)).filter(Boolean).sort((a,b)=>(a.sequence_rank??99999)-(b.sequence_rank??99999)||a.position_label.localeCompare(b.position_label,'zh'))}
function timeline(c,os){return D.stages.map(stage=>{let ls=os.filter(o=>o.stage===stage),primary=ls.filter(o=>!o.week_in_plan||o.timing_precision==='exact_topic_row'),blocks=ls.filter(o=>o.week_in_plan&&o.timing_precision!=='exact_topic_row');return '<section class="stage-section"><div class="stage-head"><h3>'+E(stage)+'</h3><span class="count">'+ls.length+' 条位置 / 线索</span></div>'+(primary.length?primary.map(occ).join(''):'<div class="empty">'+(stage.startsWith('国内')?'本库未核到该阶段的直接正文定位；请区分下方可能的先修或组合来源。':'尚未建立该阶段的直接目标条目。不能据此认定课程一定没有。')+'</div>')+(blocks.length?'<details class="trace"><summary>'+blocks.length+' 条示例教学周块线索（不是单个概念的精确授课周）</summary><p class="muted">同一周块可跨主题；请打开原计划核具体行。只有标为“精确主题行”的记录才可据此引用该主题的示例周次。</p>'+blocks.map(occ).join('')+'</details>':'')+'</section>'}).join('')}
function graph(c,os){let cols=6,w=1450,stageNodes=[],paths='',nodes='';D.stages.forEach((s,i)=>{let ls=os.filter(o=>o.stage===s).sort((a,b)=>Number(b.first_seen_eligible)-Number(a.first_seen_eligible));let shown=ls.slice(0,4);nodes+='<text x="'+(i*240+12)+'" y="130" font-size="15" fill="#214e65">'+E(s)+'</text>';shown.forEach((o,j)=>stageNodes.push({o,x:i*240+8,y:155+j*125}));if(ls.length>4)nodes+='<text x="'+(i*240+12)+'" y="665" font-size="12" fill="#637686">另有 '+(ls.length-4)+' 条，见分阶段列表</text>'});for(const {o,x,y} of stageNodes){paths+='<path class="edge" marker-end="url(#arr)" d="M725,78 C725,110 '+(x+106)+',110 '+(x+106)+','+y+'"/>';let lines=[o.position_label.slice(0,20),o.position_label.slice(20,40),o.depth_band||o.relation];nodes+='<g class="node" data-occ="'+E(o.id)+'"><rect x="'+x+'" y="'+y+'" width="220" height="100" rx="8" fill="'+(o.first_seen_eligible?'#e1f2ec':'#fff')+'" stroke="#b1cbd1"/>'+lines.map((t,k)=>'<text x="'+(x+12)+'" y="'+(y+23+k*22)+'" font-size="12" fill="#2b475c">'+E(t.slice(0,24))+'</text>').join('')+'</g>'}let prereq=(c.prerequisite_ids||[]).filter(id=>cm.has(id));return '<div class="callout">连线表示“该知识点关联此课程位置”，包含部分交集和先修线索，不能读成完全等价或实际已教。图上每阶段最多画4条，完整证据见分阶段列表。</div><div class="graph-wrap"><svg width="'+w+'" height="710" viewBox="0 0 1450 710"><defs><marker id="arr" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#b3c9d1"/></marker></defs>'+paths+'<rect x="535" y="12" width="380" height="66" rx="10" fill="#153a54"/><text x="725" y="40" fill="white" text-anchor="middle" font-size="18">'+E(c.title_zh.slice(0,23))+'</text><text x="725" y="62" fill="#c7e2eb" text-anchor="middle" font-size="12">'+E(c.title_en.slice(0,47))+'</text>'+nodes+'</svg></div><h3>先修关系（教研建议）</h3>'+(prereq.length?'<div class="hint">'+prereq.map(id=>'<button data-prior="'+E(id)+'">'+E(cm.get(id).title_zh)+'</button>').join('')+'</div>':'<div class="empty">本概念尚未列明确先修边。</div>')+'<p><a href="'+E(noteLink('vault/'+c.subject+'知识网络.canvas'))+'">下载本学科 Obsidian Canvas</a></p>'}
function download(name,obj){let u=URL.createObjectURL(new Blob([JSON.stringify(obj,null,2)],{type:'application/json;charset=utf-8'})),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}

const initial=decodeURIComponent(location.hash.slice(1));if(cm.has(initial))selected=initial;
$('subject').innerHTML='<option value="">全部科目</option>'+D.subjects.map(s=>'<option>'+E(s)+'</option>').join('');
$('search').oninput=search;$('subject').onchange=search;
$('clear').onclick=()=>{$('search').value='';$('subject').value='';search()};
for(const b of document.querySelectorAll('[data-example]'))b.onclick=()=>{$('search').value=b.dataset.example;$('subject').value='';search()};
$('closeEvidence').onclick=()=>$('evidenceDialog').close();
search();
