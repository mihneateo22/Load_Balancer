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

// ---------- randare ----------

function render(data) {
  const dt = prev ? (data.uptime_seconds - prev.uptime_seconds) || 1 : 1;

  data.servers.forEach(s => {
    const ref = cardRefs.get(s.id);
    if (!ref) return;

    const before = prev ? prev.servers.find(x => x.id === s.id) : null;
    const rate = before ? Math.round((s.packets - before.packets) / dt) : 0;

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
    if (cardRefs.size === 0) buildCards(data.servers);
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

setInterval(tick, 1000);
tick();