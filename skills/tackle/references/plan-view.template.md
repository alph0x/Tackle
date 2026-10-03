# Plan view template

```html
<!DOCTYPE html>
<html lang="{{lang}}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{title}}</title>
<style>
:root{color-scheme:light dark;--bg:#fafaf7;--fg:#1d1f23;--muted:#5d636e;--card:#ffffff;--line:#d9dbe0;--accent:#2457d6;--live:#0b7d4b;--warn:#a3530a;--mark:#e8eefc}
@media (prefers-color-scheme: dark){:root{--bg:#14161a;--fg:#e8eaed;--muted:#a1a7b3;--card:#1e2127;--line:#363b45;--accent:#7ea3ff;--live:#4fd08f;--warn:#f0a35a;--mark:#222b45}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
header,main,footer{max-width:1100px;margin:0 auto;padding:1.25rem 16px}
h1{font-size:1.9rem;line-height:1.2;margin:.2rem 0 .6rem}
h2{font-size:1.2rem;margin:2rem 0 .5rem}
p,li{max-width:70ch}
.muted{color:var(--muted)}
code,pre,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.85em}
pre{white-space:pre-wrap;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.8rem}
section{margin-bottom:1.5rem}
.stats{display:flex;flex-wrap:wrap;gap:.6rem;margin:.6rem 0}
.stats span{background:var(--card);border:1px solid var(--line);border-radius:999px;padding:.15rem .8rem}
#working-now{border:1px solid var(--line);border-left:4px solid var(--live);background:var(--card);border-radius:8px;padding:.6rem 1rem}
#working-now h2{margin-top:0}
.graph{overflow:auto;border:1px solid var(--line);border-radius:8px;background:var(--card);padding:.5rem}
.graph svg{display:block}
.node rect{fill:var(--card);stroke:var(--line);stroke-width:1.5}
.node text{fill:var(--fg);font-size:12px}
.node .id{fill:var(--muted);font-size:11px}
.node[data-live="true"] rect{stroke:var(--live);stroke-width:3}
.node{cursor:pointer}
.edge{fill:none;stroke:var(--line);stroke-width:1.5}
.sel rect{stroke:var(--accent);stroke-width:3}
.up rect,.down rect{stroke:var(--accent)}
.edge.on{stroke:var(--accent);stroke-width:2.5}
.dim{opacity:.3}
.bar{display:flex;flex-wrap:wrap;gap:.4rem;margin:.5rem 0}
button{font:inherit;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:.25rem .7rem;cursor:pointer}
button[aria-pressed="true"]{background:var(--mark);border-color:var(--accent)}
.tasks{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:.8rem}
.task{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.7rem .9rem}
.task h3{font-size:1rem;margin:0 0 .3rem}
.task[data-live="true"]{border-color:var(--live);box-shadow:0 0 0 2px var(--live)}
.task.sel{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent)}
.task.up,.task.down{background:var(--mark)}
.task[data-hidden="true"]{display:none}
.badge{display:inline-block;font-size:.8rem;border:1px solid var(--line);border-radius:999px;padding:0 .6rem}
.live{color:var(--live);font-weight:600}
.js .task .detail{display:none}
.js .task.sel .detail{display:block}
table{border-collapse:collapse;width:100%}
th,td{border-bottom:1px solid var(--line);padding:.35rem .5rem;text-align:left;vertical-align:top}
details{border:1px solid var(--line);border-radius:8px;padding:.5rem 1rem;background:var(--card)}
summary{cursor:pointer;font-weight:600}
a{color:var(--accent)}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:.9rem}
@media (max-width:600px){h1{font-size:1.5rem}}
</style>
</head>
<body>
<header>
<h1>{{title}}</h1>
<p>{{summary}}</p>
<div class="stats">{{stats}}</div>
</header>
<main>
{{working}}
{{graph}}
{{tasks}}
{{coverage}}
{{snapshot}}
<section id="technical">
<details>
<summary>{{ui_technical}}</summary>
<p class="muted">{{ui_technical_note}}</p>
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
  document.documentElement.classList.add('js');
  var cards = {}, nodes = {}, edges = [];
  Array.prototype.forEach.call(document.querySelectorAll('.task'), function (c) { cards[c.id.slice(5)] = c; });
  Array.prototype.forEach.call(document.querySelectorAll('.node'), function (n) { nodes[n.getAttribute('data-task')] = n; });
  edges = Array.prototype.slice.call(document.querySelectorAll('.edge'));
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
    function pick() { select(id, 'both'); if (cards[id]) { cards[id].scrollIntoView({block: 'nearest'}); } }
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
      Object.keys(cards).forEach(function (id) {
        var show = want === 'all' || cards[id].getAttribute('data-status') === want;
        if (show) { cards[id].removeAttribute('data-hidden'); } else { cards[id].setAttribute('data-hidden', 'true'); }
      });
    });
  });
})();
</script>
</body>
</html>
```
