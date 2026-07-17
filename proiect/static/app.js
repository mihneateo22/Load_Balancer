// app.js — logica dashboard-ului

const MOCK = true;   // Faza 7: schimbi in false

// ---------- acces la date ----------

async function getStats() {
  if (MOCK) return MockLB.tick();
  const r = await fetch('/api/traffic');
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

// ---------- construirea cardurilor ----------

const cardRefs = new Map();

function buildCards(servers) {
  const container = document.getElementById('cards');

  servers.forEach(s => {
    const el = document.createElement('div');
    el.className = 'card';
    el.innerHTML = `
      <div class="card-head">
        <span class="dot"></span>
        <strong>Server ${s.id}</strong>
        <code>${s.ip}</code>
        <button class="kill" data-id="${s.id}">kill</button>
      </div>
      <div class="metric-big"><span class="rate">0</span> <small>pkt/s</small></div>
      <div class="metrics">
        <div>packets <b class="packets">0</b></div>
        <div>conns <b class="conns">0</b></div>
        <div>flows <b class="flows">0</b></div>
        <div>latency <b class="lat">—</b></div>
      </div>
    `;
    container.appendChild(el);

    cardRefs.set(s.id, {
      root:    el,
      dot:     el.querySelector('.dot'),
      rate:    el.querySelector('.rate'),
      packets: el.querySelector('.packets'),
      conns:   el.querySelector('.conns'),
      flows:   el.querySelector('.flows'),
      lat:     el.querySelector('.lat'),
    });
  });
}

// ---------- starea buclei ----------

let prev = null;
let failures = 0;

// ---------- bara de distributie ----------

function renderDistribution(data) {
  const bar = document.getElementById('distribution');
  const total = data.totals.packets || 1;

  if (bar.children.length === 0) {
    data.servers.forEach(s => {
      const seg = document.createElement('div');
      seg.className = `seg seg-${s.id}`;
      bar.appendChild(seg);
    });
  }

  data.servers.forEach(s => {
    const seg = bar.querySelector(`.seg-${s.id}`);
    if (!seg) return;

    const pct = (s.packets / total) * 100;
    seg.style.flexGrow = pct;
    seg.textContent = pct > 8 ? `${pct.toFixed(1)}%` : '';
    seg.classList.toggle('dead', !s.alive);
  });
}

// ---------- topologia ----------

const TOPO_W = 900;
const TOPO_H = 150;

function buildTopology(servers) {
  const el = document.getElementById('topology');

  const lbX = 300, lbY = TOPO_H / 2;
  const srvX = 700;
  const step = TOPO_H / (servers.length + 1);

  const lines = servers.map((s, i) => {
    const y = step * (i + 1);
    return `<path id="link-${s.id}" class="link"
                  d="M ${lbX + 55} ${lbY} C ${lbX + 160} ${lbY}, ${srvX - 160} ${y}, ${srvX - 8} ${y}" />`;
  }).join('');

  const nodes = servers.map((s, i) => {
    const y = step * (i + 1);
    return `
      <circle id="node-${s.id}" class="node" cx="${srvX}" cy="${y}" r="7" />
      <text class="node-label" x="${srvX + 16}" y="${y + 4}">srv${s.id}</text>
      <text class="node-ip" x="${srvX + 62}" y="${y + 4}">${s.ip}</text>
    `;
  }).join('');

  el.innerHTML = `
    <svg viewBox="0 0 ${TOPO_W} ${TOPO_H}" preserveAspectRatio="xMidYMid meet">
      ${lines}

      <path class="link link-client" d="M 108 ${lbY} L ${lbX - 55} ${lbY}" />

      <rect class="box" x="40" y="${lbY - 24}" width="68" height="48" rx="8" />
      <text class="box-label" x="74" y="${lbY - 2}">client</text>
      <text class="box-ip" x="74" y="${lbY + 14}">10.0.0.1</text>

      <rect class="box box-lb" x="${lbX - 55}" y="${lbY - 26}" width="110" height="52" rx="8" />
      <text class="box-label" x="${lbX}" y="${lbY - 3}">LB</text>
      <text class="box-ip" x="${lbX}" y="${lbY + 14}">10.0.0.100</text>

      ${nodes}
    </svg>
  `;
}

const RATE_CEILING = 60;   // pkt/s la care linia atinge grosimea maxima

function renderTopology(data, rates) {
  data.servers.forEach(s => {
    const link = document.getElementById(`link-${s.id}`);
    const node = document.getElementById(`node-${s.id}`);
    if (!link || !node) return;

    const rate = rates[s.id] || 0;
    const t = Math.min(rate / RATE_CEILING, 1);
    const w = s.alive ? 2 + t * 12 : 2;

    link.style.strokeWidth = w;
    link.classList.toggle('dead', !s.alive);
    node.classList.toggle('dead', !s.alive);
  });
}

// ---------- randare ----------

function render(data) {
  const dt = prev ? (data.uptime_seconds - prev.uptime_seconds) || 1 : 1;
  const rates = {};

  data.servers.forEach(s => {
    const before = prev ? prev.servers.find(x => x.id === s.id) : null;
    rates[s.id] = before ? Math.round((s.packets - before.packets) / dt) : 0;
  });

  renderTopology(data, rates);
  renderDistribution(data);

  data.servers.forEach(s => {
    const ref = cardRefs.get(s.id);
    if (!ref) return;

    const rate = rates[s.id];

    ref.rate.textContent    = rate;
    ref.packets.textContent = s.packets.toLocaleString();
    ref.conns.textContent   = s.connections;
    ref.flows.textContent   = s.active_flows;
    ref.lat.textContent     = s.last_seen_ms !== null ? `${s.last_seen_ms}ms` : '—';

    ref.root.classList.toggle('dead', !s.alive);

    if (rate > 0) pulse(ref.root);
  });

  document.getElementById('subtitle').textContent =
    `${data.vip} · ${data.algorithm}`;

  document.getElementById('totals').textContent =
    `${data.totals.packets.toLocaleString()} packets · ` +
    `${data.totals.connections} connections · ` +
    `${data.totals.flows_tracked} active flows · ` +
    `up ${data.uptime_seconds}s`;
}

// ---------- animatie ----------

function pulse(el) {
  el.classList.remove('pulse');
  void el.offsetWidth;
  el.classList.add('pulse');
}

// ---------- status ----------

function setStatus(state) {
  const el = document.getElementById('status');
  el.textContent = state;
  el.className = state;
}

// ---------- bucla ----------

async function tick() {
  try {
    const data = await getStats();
    if (cardRefs.size === 0) {
      buildCards(data.servers);
      buildTopology(data.servers);      // ← adaugi linia asta
    }
    render(data);
    prev = data;
    failures = 0;
    setStatus('connected');
  } catch (e) {
    failures++;
    setStatus(failures > 3 ? 'disconnected' : 'reconnecting');
    console.error('tick failed:', e);
  }
}

// ---------- kill button ----------

document.getElementById('cards').addEventListener('click', async (e) => {
  const btn = e.target.closest('.kill');
  if (!btn) return;

  const id = Number(btn.dataset.id);

  if (MOCK) {
    MockLB.toggle(id);
    tick();
    return;
  }

  btn.disabled = true;
  try {
    const r = await fetch(`/api/servers/${id}/toggle`, { method: 'POST' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    await tick();
  } catch (err) {
    console.error('toggle failed:', err);
    setStatus('error');
  } finally {
    btn.disabled = false;
  }
});

setInterval(tick, 1000);
tick();