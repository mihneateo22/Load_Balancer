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

// ---------- test temporar (il stergem la Faza 3) ----------

getStats().then(data => buildCards(data.servers));