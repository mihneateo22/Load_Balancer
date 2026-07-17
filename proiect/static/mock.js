// mock.js — simulator de backend
// Generează date în formatul din contract.md, fără să existe Scapy/Flask.
// Se folosește când MOCK = true în app.js.

const MockLB = (() => {

  const servers = [
    { id: 1, ip: "10.0.0.2", packets: 0, connections: 0, active_flows: 0, alive: true, last_seen_ms: 100 },
    { id: 2, ip: "10.0.0.3", packets: 0, connections: 0, active_flows: 0, alive: true, last_seen_ms: 100 },
    { id: 3, ip: "10.0.0.4", packets: 0, connections: 0, active_flows: 0, alive: true, last_seen_ms: 100 },
  ];

  let rr = 0;
  let uptime = 0;

  function tick() {
    uptime++;

    const alive = servers.filter(s => s.alive);

    if (alive.length > 0) {
      const newConns = 3 + Math.floor(Math.random() * 4);   // 3-6 conexiuni noi/sec
      for (let i = 0; i < newConns; i++) {
        const s = alive[rr % alive.length];
        rr++;
        s.connections += 1;
        s.packets += 8 + Math.floor(Math.random() * 3);     // 8-10 pachete/conexiune
      }
    }

    servers.forEach(s => {
      if (s.alive) {
        s.last_seen_ms = 80 + Math.floor(Math.random() * 60);
        s.active_flows = 2 + Math.floor(Math.random() * 4);
      } else {
        s.last_seen_ms = null;
        s.active_flows = 0;
      }
    });

    return {
      vip: "10.0.0.100",
      algorithm: "round-robin + flow persistence",
      uptime_seconds: uptime,
      servers: structuredClone(servers),
      totals: {
        packets:      servers.reduce((sum, s) => sum + s.packets, 0),
        connections:  servers.reduce((sum, s) => sum + s.connections, 0),
        flows_tracked: servers.reduce((sum, s) => sum + s.active_flows, 0),
      }
    };
  }

  function toggle(id) {
    const s = servers.find(x => x.id === id);
    if (s) s.alive = !s.alive;
  }

  return { tick, toggle };

})();