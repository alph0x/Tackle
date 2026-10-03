# Plan view template

```html
<!DOCTYPE html>
<html lang="{{lang}}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{title}}</title>
<style>
:root{--bg:#f5f3ee;--bg2:#efece5;--surface:#ffffff;--raise:#f7f5f0;--ink:#121418;--ink2:#383d45;--mut:#5f656f;--line:#e3dfd5;--line2:#d3cec2;--accent:#0d6a53;--accent-ink:#0a5442;--accent-soft:#e2efe9;--on-accent:#ffffff;--done:#0d6a53;--prog:#ad5f0a;--ready:#2b5d93;--draft:#8b9099;--block:#b5373a;--wait:#6a4fb0;--edge:#a9a496;--glow:rgba(13,106,83,.16);--dotgrid:rgba(18,20,24,.07);--shadow:0 1px 1px rgba(18,20,24,.03),0 2px 6px rgba(18,20,24,.04),0 14px 32px -12px rgba(18,20,24,.10);color-scheme:light;--r:16px;--ease:cubic-bezier(.22,1,.36,1);--serif:ui-serif,Georgia,"Times New Roman",serif;--sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}
:root[data-theme="dark"]{--bg:#0b0c0e;--bg2:#101215;--surface:#14161a;--raise:#191c21;--ink:#eeece7;--ink2:#c6c3bc;--mut:#959aa3;--line:#24272d;--line2:#30343b;--accent:#5fd1ad;--accent-ink:#7fdcbf;--accent-soft:#132a23;--on-accent:#06261d;--done:#5fd1ad;--prog:#eaa64e;--ready:#7fb0e8;--draft:#6f757e;--block:#ef7d7d;--wait:#b3a2f2;--edge:#4a4f57;--glow:rgba(95,209,173,.14);--dotgrid:rgba(238,236,231,.06);--shadow:0 1px 1px rgba(0,0,0,.4),0 10px 30px -10px rgba(0,0,0,.6);color-scheme:dark}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0b0c0e;--bg2:#101215;--surface:#14161a;--raise:#191c21;--ink:#eeece7;--ink2:#c6c3bc;--mut:#959aa3;--line:#24272d;--line2:#30343b;--accent:#5fd1ad;--accent-ink:#7fdcbf;--accent-soft:#132a23;--on-accent:#06261d;--done:#5fd1ad;--prog:#eaa64e;--ready:#7fb0e8;--draft:#6f757e;--block:#ef7d7d;--wait:#b3a2f2;--edge:#4a4f57;--glow:rgba(95,209,173,.14);--dotgrid:rgba(238,236,231,.06);--shadow:0 1px 1px rgba(0,0,0,.4),0 10px 30px -10px rgba(0,0,0,.6);color-scheme:dark}}
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth;scroll-padding-top:84px;-webkit-text-size-adjust:100%}
html,body{overflow-x:clip}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
::selection{background:var(--accent);color:var(--on-accent)}
code,pre,.mono{font-family:var(--mono);font-size:.86em}
a{color:var(--accent-ink)}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px;border-radius:6px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:fixed;left:16px;top:-60px;z-index:100;background:var(--ink);color:var(--bg);padding:10px 14px;border-radius:10px;text-decoration:none}
.skip:focus{top:12px}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
@media (max-width:640px){.wrap{padding:0 16px}}
.progress{position:fixed;inset:0 0 auto 0;height:2px;z-index:60;background:var(--accent);transform-origin:0 50%;transform:scaleX(0)}
nav.top{position:sticky;top:0;z-index:50;background:color-mix(in srgb,var(--bg) 78%,transparent);backdrop-filter:saturate(1.5) blur(14px);-webkit-backdrop-filter:saturate(1.5) blur(14px);border-bottom:1px solid var(--line)}
nav.top .wrap{display:flex;align-items:center;gap:20px;height:60px}
.brand{font-weight:600;text-decoration:none;color:var(--ink);display:flex;align-items:center;gap:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:38vw}
.brand i{flex:none;width:9px;height:9px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px var(--accent-soft)}
.links{display:flex;gap:2px;margin-left:auto}
.links a{color:var(--mut);text-decoration:none;font-size:14px;padding:7px 12px;border-radius:999px}
.links a:hover{color:var(--ink);background:var(--surface)}
.toggle{flex:none;width:40px;height:40px;border-radius:12px;border:1px solid var(--line);background:var(--surface);color:var(--ink);display:grid;place-items:center;cursor:pointer;padding:0}
.toggle svg{width:18px;height:18px;grid-area:1/1;transition:transform .5s var(--ease),opacity .3s}
.toggle .sun{opacity:0;transform:rotate(-90deg) scale(.5)}
:root[data-theme="dark"] .toggle .sun{opacity:1;transform:none}
:root[data-theme="dark"] .toggle .moon{opacity:0;transform:rotate(90deg) scale(.5)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .toggle .sun{opacity:1;transform:none}:root:not([data-theme="light"]) .toggle .moon{opacity:0;transform:rotate(90deg) scale(.5)}}
@media (max-width:760px){.links{display:none}nav.top .toggle{margin-left:auto}}
.hero{position:relative;padding:56px 0 40px;isolation:isolate;overflow:clip}
.hero::before{content:"";position:absolute;inset:-60px 0 0;z-index:-2;background-image:radial-gradient(var(--dotgrid) 1px,transparent 1.4px);background-size:22px 22px;-webkit-mask-image:radial-gradient(ellipse 70% 70% at 70% 30%,#000 20%,transparent 75%);mask-image:radial-gradient(ellipse 70% 70% at 70% 30%,#000 20%,transparent 75%)}
.orb{position:absolute;z-index:-1;width:520px;height:520px;right:-120px;top:-180px;border-radius:50%;background:radial-gradient(circle at 40% 40%,var(--glow),transparent 62%);animation:drift 22s ease-in-out infinite alternate;pointer-events:none}
@keyframes drift{to{transform:translate3d(-120px,80px,0) scale(1.12)}}
.hero-grid{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:56px;align-items:end}
@media (max-width:980px){.hero-grid{grid-template-columns:1fr;gap:28px}}
.kicker{display:inline-flex;align-items:center;gap:10px;font:500 13px/1 var(--sans);color:var(--accent-ink);background:var(--accent-soft);padding:7px 13px 7px 11px;border-radius:999px;max-width:100%}
.kicker i{position:relative;flex:none;width:7px;height:7px;border-radius:50%;background:var(--accent)}
.kicker i::after{content:"";position:absolute;inset:-4px;border-radius:50%;border:1.5px solid var(--accent);animation:ping 2.4s var(--ease) infinite}
@keyframes ping{0%{transform:scale(.5);opacity:.9}80%,100%{transform:scale(1.9);opacity:0}}
h1{font-family:var(--serif);font-weight:400;font-size:clamp(40px,8vw,104px);line-height:.98;letter-spacing:-.03em;margin:22px 0 20px;overflow-wrap:anywhere;text-wrap:balance}
.objective{font-size:clamp(17px,1.5vw,20px);line-height:1.58;color:var(--ink2);max-width:62ch;margin:0;text-wrap:pretty}
.prog-card{background:var(--surface);border:1px solid var(--line);border-radius:24px;padding:24px;box-shadow:var(--shadow)}
.ring{position:relative;width:148px;height:148px;margin:0 auto}
.ring svg{display:block;transform:rotate(-90deg)}
.ring circle{fill:none;stroke-width:9;stroke-linecap:round}
.ring .track{stroke:var(--line)}
.ring .val{stroke:var(--accent);stroke-dasharray:390;stroke-dashoffset:var(--off);animation:ringin 1.4s var(--ease) both}
@keyframes ringin{from{stroke-dashoffset:390}}
.ring .num{position:absolute;inset:0;display:grid;place-content:center;text-align:center}
.ring .num b{font:600 36px/1 var(--sans);letter-spacing:-.03em;font-variant-numeric:tabular-nums}
.ring .num small{display:block;margin-top:4px;color:var(--mut);font-size:12px}
.prog-card .cap{text-align:center;margin:12px 0 14px;color:var(--ink2);font-size:14px}
.segbar{display:flex;gap:3px;height:8px;border-radius:8px;overflow:hidden}
.segbar i{display:block;background:var(--draft);border-radius:3px}
.segbar i.done{background:var(--done)}.segbar i.prog{background:var(--prog)}.segbar i.ready{background:var(--ready)}.segbar i.block{background:var(--block)}.segbar i.wait{background:var(--wait)}
.seglegend{list-style:none;margin:12px 0 0;padding:0;display:grid;gap:6px;font-size:13.5px;color:var(--ink2)}
.seglegend li{display:flex;align-items:center;gap:8px}.seglegend b{margin-left:auto;font-variant-numeric:tabular-nums;color:var(--ink)}
.dot{flex:none;width:8px;height:8px;border-radius:50%;display:inline-block;background:var(--draft)}
.dot.done{background:var(--done)}.dot.prog{background:var(--prog)}.dot.ready{background:var(--ready)}.dot.block{background:var(--block)}.dot.wait{background:var(--wait)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.stat{padding:22px 22px 22px 0}
.stat+.stat{padding-left:22px;border-left:1px solid var(--line)}
.stat .k{display:block;font-size:13px;color:var(--mut);margin-bottom:8px}
.stat b{display:block;font:600 clamp(28px,3vw,38px)/1 var(--sans);letter-spacing:-.03em;font-variant-numeric:tabular-nums}
@media (max-width:760px){.stats{grid-template-columns:1fr 1fr}.stat{padding:16px 16px 16px 0}.stat+.stat{padding-left:16px}.stat:nth-child(3){border-left:0;padding-left:0}.stat:nth-child(-n+2){border-bottom:1px solid var(--line)}}
.sec{padding:64px 0 0}
.sh{margin-bottom:22px;max-width:760px}
.sh h2{font-family:var(--serif);font-weight:400;font-size:clamp(32px,4.4vw,52px);line-height:1.02;letter-spacing:-.022em;margin:0}
.sh p{margin:10px 0 0;color:var(--mut);font-size:16.5px;max-width:62ch;text-wrap:pretty}
.eyebrow{margin:0 0 10px;font:500 12px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--mut)}
#working-now{margin-top:32px;padding:16px 20px;background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--done);border-radius:var(--r);box-shadow:var(--shadow)}
#working-now ul{list-style:none;margin:0;padding:0;display:grid;gap:6px}
#working-now li{display:flex;align-items:center;gap:10px}
#working-now li::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--done);animation:beat 1.8s ease-in-out infinite}
#working-now p{margin:0;color:var(--ink2)}
@keyframes beat{50%{transform:scale(1.5);opacity:.6}}
.map{background:var(--surface);border:1px solid var(--line);border-radius:24px;box-shadow:var(--shadow);overflow:hidden}
.map-bar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:12px 20px;border-bottom:1px solid var(--line);color:var(--ink2);font-size:13px}
.gscroll{overflow:auto;padding:12px}
.gscroll svg{display:block;margin:0 auto}
.band{fill:var(--bg2);stroke:var(--line)}
.band-h{fill:var(--accent-ink);font:600 12px var(--mono);letter-spacing:.05em}
.band-c{fill:var(--mut);font:12px var(--sans)}
.edge{fill:none;stroke:var(--edge);stroke-width:1.6;transition:opacity .3s,stroke .2s}
.arrowhead{fill:var(--edge)}
.node{cursor:pointer;transition:opacity .3s}
.node rect{fill:var(--surface);stroke:var(--line2);stroke-width:1.4;transition:stroke .2s}
.node:hover rect,.node:focus-visible rect{stroke:var(--accent);stroke-width:2.4}
.node:focus-visible{outline:none}
.node.s-done rect{stroke:var(--done)}.node.s-prog rect{stroke:var(--prog)}.node.s-ready rect{stroke:var(--ready)}.node.s-block rect{stroke:var(--block)}.node.s-wait rect{stroke:var(--wait)}
.node.s-draft rect{stroke-dasharray:5 4}
.node[data-live="true"] rect{stroke:var(--done);stroke-width:3}
.dot-done{fill:var(--done)}.dot-prog{fill:var(--prog)}.dot-ready{fill:var(--ready)}.dot-block{fill:var(--block)}.dot-wait{fill:var(--wait)}.dot-draft{fill:var(--draft)}
.node .nid{fill:var(--mut);font:500 11px var(--mono)}
.node .nt{fill:var(--ink);font:550 12.5px var(--sans)}
.sel rect{stroke:var(--accent);stroke-width:3}
.up rect,.down rect{stroke:var(--accent);stroke-width:2.4}
.edge.on{stroke:var(--accent);stroke-width:2.6}
.dim{opacity:.28}
.node[data-hidden="true"]{opacity:.14}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px}
button{font:inherit;color:var(--ink);cursor:pointer}
.chip{display:inline-flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:6px 14px;font-size:14px}
.chip:hover{border-color:var(--accent)}
.chip[aria-pressed="true"]{background:var(--accent-soft);border-color:var(--accent);color:var(--accent-ink)}
.chip b{font-variant-numeric:tabular-nums}
.tasks{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}
.task{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:14px 16px;box-shadow:var(--shadow);transition:transform .35s var(--ease),border-color .2s}
.task:hover{transform:translateY(-2px);border-color:var(--line2)}
.task h3{font-size:15.5px;line-height:1.35;margin:10px 0 4px;font-weight:600;overflow-wrap:anywhere}
.tc-top{display:flex;align-items:center;gap:8px;font-size:12.5px;color:var(--mut)}
.pill{margin-left:auto;display:inline-flex;align-items:center;gap:6px;border:1px solid var(--line);border-radius:999px;padding:1px 10px;font-size:12px;color:var(--ink2)}
.task[data-live="true"]{border-color:var(--done);box-shadow:0 0 0 2px var(--done)}
.live{color:var(--done);font-weight:600;font-size:12px}
.task.sel{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent)}
.task.up,.task.down{background:var(--accent-soft)}
.task[data-hidden="true"]{display:none}
.detail p{margin:6px 0;font-size:14px;color:var(--ink2);overflow-wrap:anywhere}
.detail button{background:var(--raise);border:1px solid var(--line);border-radius:8px;padding:4px 10px;font-size:13px}
.js .task .detail{display:none}
.js .task.sel .detail{display:block}
.snap{background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:16px 20px;white-space:pre-wrap;overflow-wrap:anywhere;margin:0;font-family:var(--sans);font-size:15px;color:var(--ink2)}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border-bottom:1px solid var(--line);padding:7px 10px;text-align:left;vertical-align:top;overflow-wrap:anywhere}
th{color:var(--mut);font-weight:500}
details{border:1px solid var(--line);border-radius:var(--r);padding:12px 20px;background:var(--surface)}
summary{cursor:pointer;font-weight:600;font-size:17px}
details h3{margin:24px 0 8px;font-size:16px}
.tw{overflow-x:auto}
footer{max-width:1180px;margin:72px auto 0;padding:24px;border-top:1px solid var(--line);color:var(--mut);font-size:14px}
footer p{margin:2px 0}
.motion [data-reveal]{opacity:0;transform:translateY(14px);transition:opacity .7s var(--ease),transform .7s var(--ease)}
.motion [data-reveal].in{opacity:1;transform:none}
@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}.motion [data-reveal]{opacity:1;transform:none}}
</style>
</head>
<body>
<a class="skip" href="#main">{{ui_skip}}</a>
<div class="progress" aria-hidden="true"></div>
<nav class="top"><div class="wrap">
<a class="brand" href="#top"><i aria-hidden="true"></i>{{brand}}</a>
<div class="links">{{nav}}</div>
<button type="button" class="toggle" id="theme" aria-label="{{ui_theme}}" title="{{ui_theme}}"><svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg><svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg></button>
</div></nav>
<header class="hero" id="top"><div class="orb" aria-hidden="true"></div><div class="wrap hero-grid">
<div>
<span class="kicker"><i aria-hidden="true"></i>{{kicker}}</span>
<h1>{{title}}</h1>
{{objective}}
</div>
<aside class="prog-card" aria-label="{{ui_progress}}">{{progress}}</aside>
</div></header>
<main id="main" class="wrap">
<div class="stats">{{stats}}</div>
{{working}}
{{graph}}
{{tasks}}
{{snapshot}}
<section class="sec" id="technical" data-reveal>
<details>
<summary>{{ui_technical}}</summary>
<p>{{ui_technical_note}}</p>
{{technical}}
</details>
</section>
</main>
<footer>
{{footer}}
</footer>
<script type="application/json" id="plan-view-data">{{island}}</script>
<script>
(function () {
  var root = document.documentElement;
  root.classList.add('js');
  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var theme = document.getElementById('theme');
  function isDark() {
    var set = root.getAttribute('data-theme');
    return set ? set === 'dark' : !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  }
  try {
    var saved = localStorage.getItem('plan-view-theme');
    if (saved === 'light' || saved === 'dark') { root.setAttribute('data-theme', saved); }
  } catch (e) {}
  theme.addEventListener('click', function () {
    var next = isDark() ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('plan-view-theme', next); } catch (e) {}
  });
  var bar = document.querySelector('.progress');
  function onScroll() {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.transform = 'scaleX(' + (h > 0 ? window.scrollY / h : 0) + ')';
  }
  if (!reduced) { window.addEventListener('scroll', onScroll, { passive: true }); onScroll(); }
  var reveals = Array.prototype.slice.call(document.querySelectorAll('[data-reveal]'));
  if (!reduced && 'IntersectionObserver' in window) {
    root.classList.add('motion');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0.05 });
    reveals.forEach(function (el) { io.observe(el); });
  }
  var cards = {}, nodes = {};
  var edges = Array.prototype.slice.call(document.querySelectorAll('.edge'));
  Array.prototype.forEach.call(document.querySelectorAll('.task'), function (c) { cards[c.id.slice(5)] = c; });
  Array.prototype.forEach.call(document.querySelectorAll('.node'), function (n) { nodes[n.getAttribute('data-task')] = n; });
  function walk(id, attr, seen) {
    var card = cards[id];
    if (!card) { return seen; }
    (card.getAttribute(attr) || '').split(' ').forEach(function (next) {
      if (next && !seen[next]) { seen[next] = true; walk(next, attr, seen); }
    });
    return seen;
  }
  function mark(el, cls, on) { if (el) { el.classList.toggle(cls, on); } }
  function clear() {
    Object.keys(cards).forEach(function (id) {
      ['sel', 'up', 'down', 'dim'].forEach(function (c) { mark(cards[id], c, false); mark(nodes[id], c, false); });
    });
    edges.forEach(function (e) { mark(e, 'on', false); mark(e, 'dim', false); });
  }
  function select(id, mode) {
    clear();
    if (!cards[id]) { return; }
    var up = mode === 'down' ? {} : walk(id, 'data-upstream', {});
    var down = mode === 'up' ? {} : walk(id, 'data-downstream', {});
    Object.keys(cards).forEach(function (other) {
      var role = other === id ? 'sel' : up[other] ? 'up' : down[other] ? 'down' : 'dim';
      mark(cards[other], role, true);
      mark(nodes[other], role, true);
    });
    edges.forEach(function (e) {
      var from = e.getAttribute('data-from'), to = e.getAttribute('data-to');
      var inPath = (from === id || up[from] || down[from]) && (to === id || up[to] || down[to]);
      var side = (mode !== 'down' && (to === id || up[to])) || (mode !== 'up' && (from === id || down[from]));
      mark(e, 'on', !!(inPath && side));
      mark(e, 'dim', !(inPath && side));
    });
  }
  Object.keys(cards).forEach(function (id) {
    cards[id].addEventListener('click', function (ev) {
      var trace = ev.target.getAttribute && ev.target.getAttribute('data-trace');
      select(id, trace || 'both');
    });
  });
  Object.keys(nodes).forEach(function (id) {
    function pick() { select(id, 'both'); if (cards[id]) { cards[id].scrollIntoView({ block: 'nearest' }); } }
    nodes[id].addEventListener('click', pick);
    nodes[id].addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); pick(); } });
  });
  var clearButton = document.getElementById('clear-trace');
  if (clearButton) { clearButton.addEventListener('click', clear); }
  var filters = Array.prototype.slice.call(document.querySelectorAll('[data-filter]'));
  filters.forEach(function (button) {
    button.addEventListener('click', function () {
      var want = button.getAttribute('data-filter');
      filters.forEach(function (other) { other.setAttribute('aria-pressed', other === button ? 'true' : 'false'); });
      var hidden = {};
      Object.keys(cards).forEach(function (id) {
        var off = want !== 'all' && cards[id].getAttribute('data-status') !== want;
        hidden[id] = off;
        [cards[id], nodes[id]].forEach(function (el) {
          if (!el) { return; }
          if (off) { el.setAttribute('data-hidden', 'true'); } else { el.removeAttribute('data-hidden'); }
        });
      });
      edges.forEach(function (e) {
        mark(e, 'dim', !!(hidden[e.getAttribute('data-from')] || hidden[e.getAttribute('data-to')]));
      });
    });
  });
})();
</script>
</body>
</html>
```
