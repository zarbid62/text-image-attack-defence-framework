const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const inputPath = path.join(root, "results", "model_comparison.json");
const outputPath = path.join(root, "results", "model_comparison_dashboard.html");

if (!fs.existsSync(inputPath)) {
  console.error("Missing results/model_comparison.json. Run src\\run_tests.py first.");
  process.exit(1);
}

const comparison = JSON.parse(fs.readFileSync(inputPath, "utf8"));
const data = JSON.stringify(comparison).replace(/</g, "\\u003c");

const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AegisAI Model Comparison Dashboard</title>
  <style>
    :root { --ink:#17212b; --muted:#64717d; --paper:#f5f7f8; --panel:#fff; --line:#dce3e7; --teal:#087f8c; --blue:#3b67c4; --amber:#d58b18; --coral:#d85d50; --green:#2f9560; }
    * { box-sizing:border-box; }
    body { margin:0; color:var(--ink); background:linear-gradient(135deg,#edf5f4 0%,#f8f5ef 55%,#eef1f8 100%); font:16px/1.5 "Segoe UI", sans-serif; }
    main { max-width:1400px; margin:0 auto; padding:42px 28px 60px; }
    header { display:flex; justify-content:space-between; gap:24px; align-items:end; margin-bottom:30px; }
    h1 { margin:0 0 8px; font:700 clamp(28px,4vw,52px)/1.02 Georgia,serif; letter-spacing:0; }
    h2 { margin:0 0 18px; font:700 23px/1.1 Georgia,serif; }
    .subtitle,.note { color:var(--muted); }
    .stamp { text-align:right; color:var(--muted); font-size:15px; }
    .cards { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:24px; }
    .card,.panel { background:rgba(255,255,255,.88); border:1px solid var(--line); box-shadow:0 10px 28px rgba(30,55,65,.07); }
    .card { padding:18px; border-radius:8px; }
    .card strong { display:block; font-size:30px; line-height:1; margin:8px 0 5px; }
    .card span { color:var(--muted); font-size:15px; }
    .panel { border-radius:8px; padding:24px; margin-bottom:20px; }
    .grid { display:grid; grid-template-columns:1.25fr .75fr; gap:20px; }
    .chart { min-height:320px; }
    svg { width:100%; height:auto; display:block; overflow:visible; }
    .legend { display:flex; flex-wrap:wrap; gap:12px 18px; margin-top:10px; color:var(--muted); font-size:15px; }
    .legend i { display:inline-block; width:11px; height:11px; margin-right:6px; border-radius:2px; }
    table { width:100%; border-collapse:collapse; font-size:15px; }
    th,td { text-align:left; padding:10px 8px; border-bottom:1px solid var(--line); }
    th { color:var(--muted); font-weight:600; }
    .heatmap { overflow-x:auto; }
    .heatmap td,.heatmap th { min-width:90px; text-align:center; }
    .heatmap th:first-child,.heatmap td:first-child { min-width:220px; text-align:left; }
    .heat { color:#fff; font-weight:700; border-radius:4px; }
    .model-gap td { height:18px; padding:0; border-bottom:0; background:transparent; }
    .model-group td { border-bottom-color:rgba(255,255,255,.8); }
    .model-group-start td { border-top:4px solid rgba(23,33,43,.18); }
    .error { color:var(--coral); font-weight:700; }
    .actions { display:flex; flex-wrap:wrap; gap:10px; margin-top:20px; }
    button { border:0; border-radius:6px; padding:11px 16px; color:#fff; background:var(--teal); cursor:pointer; font:600 15px "Segoe UI", sans-serif; }
    .actions a { display:inline-block; border-radius:6px; padding:11px 16px; color:#fff; background:var(--teal); text-decoration:none; font:600 15px "Segoe UI", sans-serif; }
    .actions a:hover { filter:brightness(.92); }
    button.secondary { background:var(--blue); }
    button:hover { filter:brightness(.92); }
    footer { color:var(--muted); font-size:14px; margin-top:10px; }
    @media print { body { background:#fff; } main { max-width:none; padding:0; } .actions, footer { display:none; } .panel,.card { box-shadow:none; break-inside:avoid; } .grid { gap:10px; } h1 { font-size:34px; } }
    @media (max-width:800px) { main { padding:25px 14px 40px; } header { display:block; } .stamp { text-align:left; margin-top:12px; } .cards { grid-template-columns:repeat(2,1fr); } .grid { grid-template-columns:1fr; } .panel { padding:16px; } }
    @media (max-width:430px) { .cards { grid-template-columns:1fr; } }
  </style>
</head>
<body>
<main>
  <header><div><h1>Model performance, at a glance</h1><div class="subtitle">AegisAI text-injection classification comparison</div><div class="actions"><a href="AegisAI_Model_Comparison_Report.pptx" download>Download PowerPoint</a><button type="button" class="secondary" onclick="generatePdf()">Generate PDF</button></div></div><div class="stamp" id="stamp"></div></header>
  <section class="cards" id="cards"></section>
  <div class="grid">
    <section class="panel"><h2>Classification quality</h2><div class="chart" id="quality"></div><div class="legend"><span><i style="background:#087f8c"></i>Accuracy</span><span><i style="background:#3b67c4"></i>Attack detection</span><span><i style="background:#2f9560"></i>Benign correctly rejected</span><span><i style="background:#d85d50"></i>False positives</span></div></section>
    <section class="panel"><h2>Successful calls vs errors</h2><div class="chart" id="reliability"></div><div class="legend"><span><i style="background:#2f9560"></i>Successful</span><span><i style="background:#d85d50"></i>Errors</span></div></section>
  </div>
  <div class="grid">
    <section class="panel"><h2>Speed comparison</h2><div class="chart" id="latency"></div><div class="note">Lower latency is faster. Values are average milliseconds per sample.</div></section>
    <section class="panel"><h2>Overall prediction mix</h2><div class="chart" id="mix"></div><div class="legend"><span><i style="background:#d85d50"></i>Attack predicted</span><span><i style="background:#3b67c4"></i>Benign predicted</span><span><i style="background:#d58b18"></i>Errors</span></div></section>
  </div>
  <div class="grid">
    <section class="panel"><h2>Correct vs incorrect decisions</h2><div class="chart" id="outcomes"></div><div class="legend"><span><i style="background:#2f9560"></i>Correct</span><span><i style="background:#d85d50"></i>Incorrect</span></div></section>
    <section class="panel"><h2>Average model confidence</h2><div class="chart" id="confidence"></div><div class="note">Confidence is the model's self-reported certainty, not proof that the decision is correct.</div></section>
  </div>
  <section class="panel"><h2>Attack detection by technique</h2><div class="heatmap" id="heatmap"></div><div class="note">Each cell shows the percentage of attack samples in that technique classified as attacks. Darker teal means stronger detection.</div></section>
  <section class="panel"><h2>Detailed model comparison</h2><div id="table"></div></section>
  <footer>Generated from <strong>results/model_comparison.json</strong>. Re-run <strong>node src/generate_model_dashboard.js</strong> after a new evaluation.</footer>
</main>
<script>
const comparison = ${data};
const models = comparison.models;
const rows = comparison.rows;
const colors = { teal:"#087f8c", blue:"#3b67c4", green:"#2f9560", amber:"#d58b18", coral:"#d85d50", grid:"#dce3e7", text:"#17212b", muted:"#64717d" };
const pct = value => value == null ? null : Number(value);
const fmt = value => value == null ? "N/A" : value + "%";
const esc = value => String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
document.getElementById("stamp").textContent = models.length + " models • " + rows.length + " scored samples";

function generatePdf() {
  window.print();
}

const best = key => models.filter(m => m[key] != null).sort((a,b) => b[key] - a[key])[0];
document.getElementById("cards").innerHTML = [
  ["Best accuracy", best("accuracy_pct"), "accuracy_pct"],
  ["Best attack detection", best("attack_detection_rate_pct"), "attack_detection_rate_pct"],
  ["Lowest false positives", models.filter(m => m.false_positive_rate_pct != null).sort((a,b) => a.false_positive_rate_pct-b.false_positive_rate_pct)[0], "false_positive_rate_pct"],
  ["Fastest average", models.filter(m => m.avg_latency_ms != null).sort((a,b) => a.avg_latency_ms-b.avg_latency_ms)[0], "avg_latency_ms"]
].map(([label, model, key]) => '<div class="card"><span>'+label+'</span><strong>'+(model ? (key === "avg_latency_ms" ? Math.round(model[key])+" ms" : fmt(model[key])) : "N/A")+'</strong><span>'+(model ? esc(model.model) : "No successful result")+'</span></div>').join("");

function shortName(name) { return name.replace(/^ollama:/,""); }
function barChart(target, series, max, suffix) {
  const width=760, height=300, left=48, bottom=62, top=18, plotH=height-top-bottom, groupW=(width-left-12)/models.length;
  let svg='<svg viewBox="0 0 '+width+' '+height+'" role="img">';
  for(let step=0;step<=4;step++){const y=top+plotH-(plotH*step/4); const value=Math.round(max*step/4); svg+='<line x1="'+left+'" y1="'+y+'" x2="'+width+'" y2="'+y+'" stroke="'+colors.grid+'"/><text x="4" y="'+(y+4)+'" fill="'+colors.muted+'" font-size="16">'+value+suffix+'</text>';}
  models.forEach((model,index)=>{ const x=left+index*groupW+8; const barW=Math.min(32,(groupW-18)/series.length); series.forEach((item,j)=>{const value=pct(model[item.key])||0; const h=plotH*value/max; const bx=x+j*(barW+4); const by=top+plotH-h; svg+='<rect x="'+bx+'" y="'+by+'" width="'+barW+'" height="'+h+'" rx="2" fill="'+item.color+'"><title>'+esc(shortName(model.model))+': '+item.label+' '+value+suffix+'</title></rect>';}); svg+='<text x="'+(x+groupW/2-8)+'" y="'+(height-32)+'" text-anchor="middle" fill="'+colors.text+'" font-size="16">'+esc(shortName(model.model))+'</text>'; });
  return svg+'</svg>';
}
document.getElementById("quality").innerHTML=barChart("quality",[{key:"accuracy_pct",label:"Accuracy",color:colors.teal},{key:"attack_detection_rate_pct",label:"Attack detection",color:colors.blue},{key:"benign_correctly_rejected_as_not_attack_pct",label:"Benign correct",color:colors.green},{key:"false_positive_rate_pct",label:"False positives",color:colors.coral}],100,"%");
function latencyChart() {
  const width=760,height=Math.max(300,models.length*72+70),left=190,right=30,top=20,barHeight=34,plotWidth=width-left-right,max=Math.max(...models.map(m=>m.avg_latency_ms||0),1);
  let svg='<svg viewBox="0 0 '+width+' '+height+'" role="img">';
  models.forEach((model,index)=>{const value=model.avg_latency_ms||0,y=top+index*72,h=Math.max(1,plotWidth*value/max);svg+='<text x="'+(left-12)+'" y="'+(y+23)+'" text-anchor="end" fill="'+colors.text+'" font-size="16">'+esc(shortName(model.model))+'</text><rect x="'+left+'" y="'+y+'" width="'+h+'" height="'+barHeight+'" rx="4" fill="'+colors.amber+'"><title>'+esc(model.model)+': '+Math.round(value)+' ms average latency</title></rect><text x="'+(left+h+8)+'" y="'+(y+23)+'" fill="'+colors.text+'" font-size="16">'+Math.round(value)+' ms</text>';});
  svg+='<text x="'+left+'" y="'+(height-8)+'" fill="'+colors.muted+'" font-size="16">Average latency (milliseconds)</text></svg>';return svg;
}
document.getElementById("latency").innerHTML=latencyChart();

function stacked(target) { const width=700,height=300,left=48,top=20,plotH=210,barW=42,max=18; let svg='<svg viewBox="0 0 '+width+' '+height+'">'; for(let step=0;step<=3;step++){const y=top+plotH-step*plotH/3;svg+='<line x1="'+left+'" y1="'+y+'" x2="'+width+'" y2="'+y+'" stroke="'+colors.grid+'"/><text x="5" y="'+(y+4)+'" fill="'+colors.muted+'" font-size="16">'+Math.round(max*step/3)+'</text>';} models.forEach((m,i)=>{const valid=m.successful_calls||0, errors=m.errors||0, x=left+55+i*190, validH=plotH*valid/max, errorH=plotH*errors/max;svg+='<rect x="'+x+'" y="'+(top+plotH-validH)+'" width="'+barW+'" height="'+validH+'" fill="'+colors.green+'" rx="2"><title>Successful calls: '+valid+'</title></rect><rect x="'+x+'" y="'+(top+plotH-validH-errorH)+'" width="'+barW+'" height="'+errorH+'" fill="'+colors.coral+'" rx="2"><title>Errors: '+errors+'</title></rect><text x="'+(x+barW/2)+'" y="'+(height-35)+'" text-anchor="middle" fill="'+colors.text+'" font-size="16">'+esc(shortName(m.model))+'</text>';});return svg+'</svg>'; }
document.getElementById("reliability").innerHTML=stacked();

function outcomeChart() {
  const width=700,height=300,left=48,top=20,plotH=210,barW=42,max=18;
  let svg='<svg viewBox="0 0 '+width+' '+height+'">';
  for(let step=0;step<=3;step++){const y=top+plotH-step*plotH/3;svg+='<line x1="'+left+'" y1="'+y+'" x2="'+width+'" y2="'+y+'" stroke="'+colors.grid+'"/><text x="5" y="'+(y+4)+'" fill="'+colors.muted+'" font-size="16">'+Math.round(max*step/3)+'</text>';}
  models.forEach((model,index)=>{const modelRows=rows.filter(r=>r.model===model.model),correct=modelRows.filter(r=>r.correct===true).length,incorrect=modelRows.filter(r=>r.correct===false).length,x=left+55+index*190,correctH=plotH*correct/max,incorrectH=plotH*incorrect/max;svg+='<rect x="'+x+'" y="'+(top+plotH-correctH)+'" width="'+barW+'" height="'+correctH+'" fill="'+colors.green+'" rx="2"><title>Correct: '+correct+'</title></rect><rect x="'+x+'" y="'+(top+plotH-correctH-incorrectH)+'" width="'+barW+'" height="'+incorrectH+'" fill="'+colors.coral+'" rx="2"><title>Incorrect: '+incorrect+'</title></rect><text x="'+(x+barW/2)+'" y="'+(height-35)+'" text-anchor="middle" fill="'+colors.text+'" font-size="16">'+esc(shortName(model.model))+'</text>';});
  return svg+'</svg>';
}
document.getElementById("outcomes").innerHTML=outcomeChart();

function confidenceChart() {
  const width=760,height=300,left=48,bottom=62,top=18,plotH=height-top-bottom,groupW=(width-left-12)/models.length;
  let svg='<svg viewBox="0 0 '+width+' '+height+'">';
  for(let step=0;step<=4;step++){const y=top+plotH-(plotH*step/4),value=Math.round(step*25);svg+='<line x1="'+left+'" y1="'+y+'" x2="'+width+'" y2="'+y+'" stroke="'+colors.grid+'"/><text x="4" y="'+(y+4)+'" fill="'+colors.muted+'" font-size="16">'+value+'%</text>';}
  models.forEach((model,index)=>{const modelRows=rows.filter(r=>r.model===model.model&&typeof r.confidence==="number"),average=modelRows.length?modelRows.reduce((sum,r)=>sum+r.confidence,0)/modelRows.length*100:0,h=plotH*average/100,x=left+index*groupW+groupW/2-18,y=top+plotH-h;svg+='<rect x="'+x+'" y="'+y+'" width="36" height="'+h+'" rx="3" fill="'+colors.blue+'"><title>'+esc(shortName(model.model))+': '+average.toFixed(1)+'% average confidence</title></rect><text x="'+(x+18)+'" y="'+(height-32)+'" text-anchor="middle" fill="'+colors.text+'" font-size="16">'+esc(shortName(model.model))+'</text>';});
  return svg+'</svg>';
}
document.getElementById("confidence").innerHTML=confidenceChart();

function donut() { const totals={attack:0,benign:0,error:0}; rows.forEach(r=>{if(r.error) totals.error++; else if(r.predicted_attack) totals.attack++; else totals.benign++;}); const total=Object.values(totals).reduce((a,b)=>a+b,0)||1; let angle=-Math.PI/2; const slices=[['attack',colors.coral],['benign',colors.blue],['error',colors.amber]]; let svg='<svg viewBox="0 0 360 300">'; slices.forEach(([key,color])=>{const next=angle+totals[key]/total*Math.PI*2;const large=next-angle>Math.PI?1:0;const x1=180+90*Math.cos(angle),y1=140+90*Math.sin(angle),x2=180+90*Math.cos(next),y2=140+90*Math.sin(next);svg+='<path d="M 180 140 L '+x1+' '+y1+' A 90 90 0 '+large+' 1 '+x2+' '+y2+' Z" fill="'+color+'"><title>'+key+': '+totals[key]+'</title></path>';angle=next;});svg+='<circle cx="180" cy="140" r="48" fill="#fff"/><text x="180" y="137" text-anchor="middle" font-size="22" font-weight="700">'+rows.length+'</text><text x="180" y="160" text-anchor="middle" font-size="16" fill="'+colors.muted+'">samples</text></svg>';return svg; }
document.getElementById("mix").innerHTML=donut();

const attacks=rows.filter(r=>r.label==="attack"); const categories=[...new Set(attacks.map(r=>r.category))];
document.getElementById("heatmap").innerHTML='<table><thead><tr><th>Attack technique</th>'+models.map(m=>'<th>'+esc(shortName(m.model))+'</th>').join('')+'</tr></thead><tbody>'+categories.map(category=>{const samples=attacks.filter(r=>r.category===category);return '<tr><td>'+esc(category)+'</td>'+models.map(m=>{const relevant=samples.filter(r=>r.model===m.model),detected=relevant.filter(r=>r.predicted_attack===true).length,value=relevant.length?Math.round(detected/relevant.length*100):null,shade=value==null?"#dce3e7":"rgb("+(8-Math.round(value/20))*8+","+(92+Math.round(value/3))%255+","+(100+Math.round(value/2))%255+")";return '<td class="heat" style="background:'+shade+'">'+(value==null?"N/A":value+"%")+'</td>';}).join('')+'</tr>';}).join('')+'</tbody></table>';

const modelNames=[...new Set(rows.map(r=>r.model))];
const modelColors=['#e6f4f1','#e8eefb','#fff1d9','#f5e8f2','#e9f1df','#fbe6e2','#e7edf0'];
const tableRows=[]; let previousModel=null; rows.forEach(r=>{const modelIndex=modelNames.indexOf(r.model),groupClass=previousModel!==r.model?' model-group-start':'';if(previousModel!==null&&r.model!==previousModel)tableRows.push('<tr class="model-gap"><td colspan="7"></td></tr>');tableRows.push('<tr class="model-group'+groupClass+'" style="background:'+modelColors[modelIndex%modelColors.length]+'"><td><strong>'+esc(r.model)+'</strong></td><td>'+esc(r.id)+'</td><td>'+esc(r.label)+'</td><td>'+ (r.predicted_attack===null?'N/A':(r.predicted_attack?'attack':'benign'))+'</td><td>'+ (r.correct===null?'N/A':(r.correct?'yes':'no'))+'</td><td>'+ (r.confidence===null?'N/A':r.confidence)+'</td><td class="'+(r.error?'error':'')+'">'+esc(r.error||'none')+'</td></tr>');previousModel=r.model;});
document.getElementById("table").innerHTML='<table><thead><tr><th>Model</th><th>ID</th><th>Label</th><th>Predicted</th><th>Correct</th><th>Confidence</th><th>Error</th></tr></thead><tbody>'+tableRows.join('')+'</tbody></table>';
</script>
</body>
</html>`;

fs.writeFileSync(outputPath, html);
console.log(`written ${outputPath}`);