// ═══ DATA ═══════════════════════════════════════════════

const REGIONS = [
  {
    name: "Middle East",
    score: 88,
    cls: "risk-critical",
    x: "46%",
    y: "38%",
    w: "16%",
    h: "28%",
  },
  {
    name: "East Asia",
    score: 82,
    cls: "risk-critical",
    x: "72%",
    y: "28%",
    w: "20%",
    h: "35%",
  },
  {
    name: "Latin America",
    score: 63,
    cls: "risk-medium",
    x: "22%",
    y: "53%",
    w: "16%",
    h: "30%",
  },
  {
    name: "Africa",
    score: 69,
    cls: "risk-high",
    x: "46%",
    y: "55%",
    w: "16%",
    h: "28%",
  },
  {
    name: "South Asia",
    score: 76,
    cls: "risk-high",
    x: "63%",
    y: "40%",
    w: "14%",
    h: "24%",
  },
  {
    name: "SE Asia",
    score: 71,
    cls: "risk-high",
    x: "72%",
    y: "56%",
    w: "12%",
    h: "22%",
  },
  {
    name: "North America",
    score: 38,
    cls: "risk-low",
    x: "6%",
    y: "28%",
    w: "22%",
    h: "26%",
  },
  {
    name: "Europe",
    score: 45,
    cls: "risk-low",
    x: "38%",
    y: "20%",
    w: "18%",
    h: "22%",
  },
];

const SUPPLIERS = [
  {
    name: "Norilsk Nickel",
    id: "S008",
    country: "Russia",
    cat: "Mining",
    risk: 96,
    esg: 22,
    co2: 587.9,
    disrupt: 6,
    audit: "2023-11-14",
    status: "critical",
  },
  {
    name: "Zhongshan Electronics Co.",
    id: "S001",
    country: "China",
    cat: "Electronics",
    risk: 87,
    esg: 42,
    co2: 124.3,
    disrupt: 3,
    audit: "2024-04-12",
    status: "critical",
  },
  {
    name: "Aramco Trading",
    id: "S005",
    country: "Saudi Arabia",
    cat: "Energy",
    risk: 82,
    esg: 38,
    co2: 445.2,
    disrupt: 4,
    audit: "2024-02-28",
    status: "critical",
  },
  {
    name: "Vale S.A.",
    id: "S010",
    country: "Brazil",
    cat: "Mining",
    risk: 73,
    esg: 48,
    co2: 312.1,
    disrupt: 2,
    audit: "2024-03-05",
    status: "review",
  },
  {
    name: "Foxconn Technology",
    id: "S003",
    country: "Taiwan",
    cat: "Manufacturing",
    risk: 71,
    esg: 55,
    co2: 210.7,
    disrupt: 2,
    audit: "2024-03-18",
    status: "review",
  },
  {
    name: "Reliance Industries",
    id: "S006",
    country: "India",
    cat: "Textiles",
    risk: 65,
    esg: 61,
    co2: 93.8,
    disrupt: 1,
    audit: "2024-04-22",
    status: "review",
  },
  {
    name: "Covestro AG",
    id: "S009",
    country: "Germany",
    cat: "Polymers",
    risk: 41,
    esg: 76,
    co2: 78.3,
    disrupt: 0,
    audit: "2024-05-20",
    status: "active",
  },
  {
    name: "Samsung SDI",
    id: "S002",
    country: "South Korea",
    cat: "Batteries",
    risk: 38,
    esg: 71,
    co2: 64.2,
    disrupt: 0,
    audit: "2024-05-14",
    status: "active",
  },
  {
    name: "BASF SE",
    id: "S007",
    country: "Germany",
    cat: "Chemicals",
    risk: 33,
    esg: 82,
    co2: 89.4,
    disrupt: 0,
    audit: "2024-05-30",
    status: "active",
  },
  {
    name: "Ørsted",
    id: "S004",
    country: "Denmark",
    cat: "Energy",
    risk: 21,
    esg: 91,
    co2: 28.1,
    disrupt: 0,
    audit: "2024-06-01",
    status: "active",
  },
];

const ALERTS = [
  {
    id: "A001",
    severity: "critical",
    type: "Geopolitical",
    region: "Middle East",
    title: "Geopolitical Escalation — Strait of Hormuz",
    desc: "Shipping lane disruption probability at 94%. 15 active vessels rerouting. Expected delay: 8–14 days.",
    suppliers: 8,
    time: "97h 14m ago",
    acked: false,
  },
  {
    id: "A002",
    severity: "critical",
    type: "Regulatory",
    region: "Russia",
    title: "Norilsk Nickel — Sanctions Escalation",
    desc: "New EU sanctions effective June 10. Immediate suspension required. Alternative sourcing needed for Q3.",
    suppliers: 1,
    time: "98h 58m ago",
    acked: false,
  },
  {
    id: "A003",
    severity: "critical",
    type: "Geopolitical",
    region: "East Asia",
    title: "Taiwan Strait — Elevated Military Activity",
    desc: "AI model detects 87% probability of shipping disruption in next 30 days. Foxconn Taiwan operations at risk.",
    suppliers: 5,
    time: "107h 28m ago",
    acked: false,
  },
  {
    id: "A004",
    severity: "high",
    type: "Labor",
    region: "China",
    title: "Zhongshan Electronics — Labor Strike",
    desc: "Plant workers have issued 72-hour notice for strike action. Production at 40% capacity.",
    suppliers: 1,
    time: "101h 13m ago",
    acked: false,
  },
  {
    id: "A005",
    severity: "high",
    type: "Logistics",
    region: "Europe",
    title: "Port of Rotterdam — Congestion",
    desc: "Berth wait times at 6.2 days (up from 1.8 days). 23 vessels queued. BASF SE shipments delayed.",
    suppliers: 4,
    time: "103h 43m ago",
    acked: true,
  },
  {
    id: "A006",
    severity: "high",
    type: "Environmental",
    region: "Brazil",
    title: "Vale S.A. — Tailings Pond Alert",
    desc: "Sensor anomaly detected at Brumadinho facility. Environmental inspection mandated within 48 hours.",
    suppliers: 1,
    time: "114h 02m ago",
    acked: false,
  },
  {
    id: "A007",
    severity: "medium",
    type: "Financial",
    region: "South Korea",
    title: "Samsung SDI — Credit Rating Watch",
    desc: "Fitch placed Samsung SDI on negative watch following battery recall affecting 3.2M units.",
    suppliers: 1,
    time: "122h 31m ago",
    acked: true,
  },
];

const PREDICTIONS = [
  {
    conf: 87,
    severity: "critical",
    type: "Geopolitical",
    period: "Jun 15 – Jul 15",
    title: "Taiwan Semiconductor Supply Disruption",
    drivers: [
      "PLA military exercise frequency +340%",
      "Cross-strait political tension index at 10-year high",
      "Key TSMC fab located within potential interdiction zone",
    ],
    rec: "Diversify to Samsung Foundry and Intel Foundry. Increase safety stock by 8 weeks.",
    open: true,
  },
  {
    conf: 79,
    severity: "critical",
    type: "Regulatory",
    period: "Jun 20 – Aug 01",
    title: "EU CBAM Compliance — Metals Tier",
    desc: "Carbon Border Adjustment Mechanism expands to steel & aluminum.",
    drivers: [
      "Norilsk Nickel non-compliant at current trajectory",
      "Vale S.A. compliance at 62% of threshold",
      "CBAM certificate costs estimated €14.2M/yr",
    ],
    rec: "Initiate carbon disclosure audit. Accelerate supplier code compliance roadmap.",
  },
  {
    conf: 74,
    severity: "high",
    type: "Climate",
    period: "Jul – Sep 2026",
    title: "Monsoon Disruption — South Asia Logistics",
    drivers: [
      "La Niña pattern strengthening in Indian Ocean",
      "Reliance Industries Chennai facility at flood risk",
      "Port of Chennai historical closure: 18 days in 2024",
    ],
    rec: "Pre-position 6 weeks of textile inventory. Activate secondary logistics partner.",
  },
  {
    conf: 71,
    severity: "high",
    type: "Labor",
    period: "Jun 25 – Jul 10",
    title: "Zhongshan — Extended Strike Action",
    drivers: [
      "Union ratified industrial action ballot (86% yes)",
      "Management-union gap: 23% wage increase demand vs 8% offer",
      "Third-party mediator declined engagement",
    ],
    rec: "Activate contingency suppliers in Vietnam and Malaysia for electronics sub-components.",
  },
  {
    conf: 68,
    severity: "medium",
    type: "Logistics",
    period: "Jul 5 – Aug 15",
    title: "Rotterdam Port Capacity Constraint",
    drivers: [
      "APM Terminals expansion stalled (permit dispute)",
      "Vessel traffic +31% vs 2025 baseline",
      "BASF and Covestro combined shipments: 1,240 TEU/month",
    ],
    rec: "Reroute 40% of European chemical shipments via Antwerp or Hamburg.",
  },
];

const ESG_TARGETS = [
  {
    name: "Net Zero Target",
    current: 2045,
    target: 2040,
    status: "behind",
  },
  {
    name: "Renewable Energy Mix",
    current: "38%",
    target: "60%",
    status: "behind",
    pct: 63,
  },
  {
    name: "Waste Reduction",
    current: "27%",
    target: "25%",
    status: "on-track",
    pct: 108,
  },
  {
    name: "Supplier Code Compliance",
    current: "81%",
    target: "100%",
    status: "behind",
    pct: 81,
  },
  {
    name: "Carbon Offset (ktCO₂e)",
    current: 142,
    target: 200,
    status: "behind",
    pct: 71,
  },
  {
    name: "Water Efficiency Index",
    current: 72,
    target: 70,
    status: "on-track",
    pct: 103,
  },
];

// ═══ NAV ═════════════════════════════════════════════════
const navItems = document.querySelectorAll(".nav-item");
const pages = document.querySelectorAll(".page-section");
const breadcrumbEl = document.getElementById("topbar-breadcrumb");
const titleEl = document.getElementById("topbar-title");

const pageMeta = {
  overview: {
    bc: "CHAINGUARD / SUPPLY CHAIN OVERVIEW",
    title: "Real-time global risk & sustainability dashboard",
  },
  riskmap: {
    bc: "CHAINGUARD / RISK MAP",
    title: "Regional supplier risk visualization",
  },
  aipred: {
    bc: "CHAINGUARD / AI PREDICTIONS",
    title: "ML-powered disruption forecasting",
  },
  suppliers: {
    bc: "CHAINGUARD / SUPPLIER NETWORK",
    title: "Full supplier risk & sustainability registry",
  },
  sustainability: {
    bc: "CHAINGUARD / SUSTAINABILITY AUDIT",
    title: "ESG scoring, emissions tracking, and target compliance",
  },
  alerts: {
    bc: "CHAINGUARD / ACTIVE ALERTS",
    title: "Unresolved incidents requiring attention",
  },
  trends: {
    bc: "CHAINGUARD / TREND ANALYSIS",
    title: "Historical risk and sustainability trajectories",
  },
};

let chartsInit = {};

navItems.forEach((item) => {
  item.addEventListener("click", () => {
    const page = item.dataset.page;
    navItems.forEach((n) => n.classList.remove("active"));
    item.classList.add("active");
    pages.forEach((p) => p.classList.remove("active"));
    document.getElementById("page-" + page)?.classList.add("active");
    const meta = pageMeta[page];
    if (meta) {
      breadcrumbEl.textContent = meta.bc;
      titleEl.textContent = meta.title;
    }
    // Init charts lazily
    setTimeout(() => initChartsForPage(page), 50);
  });
});

// ═══ TREEMAP RENDERER ════════════════════════════════════
function buildTreemap(containerId) {
  const el = document.getElementById(containerId);
  if (!el || el.dataset.built) return;
  el.dataset.built = "1";
  REGIONS.forEach((r) => {
    const cell = document.createElement("div");
    cell.className = `treemap-cell ${r.cls}`;
    cell.style.cssText = `left:${r.x};top:${r.y};width:${r.w};height:${r.h};`;
    cell.innerHTML = `<span class="treemap-score">${r.score}</span><span class="treemap-label">${r.name}</span>`;
    el.appendChild(cell);
  });
}

// ═══ SUPPLIER TABLE ═══════════════════════════════════════
function getRiskColor(score) {
  if (score >= 80) return "var(--crimson)";
  if (score >= 65) return "var(--amber)";
  if (score >= 50) return "var(--blue)";
  return "var(--green)";
}

function buildSupplierTable() {
  const tbody = document.getElementById("supplier-tbody");
  if (!tbody || tbody.dataset.built) return;
  tbody.dataset.built = "1";
  SUPPLIERS.forEach((s) => {
    const rColor = getRiskColor(s.risk);
    const eColor = getRiskColor(100 - s.esg);
    const warnIcon =
      s.risk >= 80
        ? '<span class="warn-icon critical">▲</span>'
        : s.risk >= 65
          ? '<span class="warn-icon high">▲</span>'
          : "";
    tbody.innerHTML += `<tr>
      <td>
        <div class="supplier-name">${warnIcon} ${s.name}</div>
        <span class="supplier-id">${s.id}</span>
      </td>
      <td style="font-size:12px;color:var(--text-secondary)">${s.country}</td>
      <td><span class="category-tag">${s.cat}</span></td>
      <td>
        <div class="risk-bar-wrap">
          <div class="risk-bar-bg"><div class="risk-bar-fill" style="width:${s.risk}%;background:${rColor}"></div></div>
          <span class="risk-score" style="color:${rColor}">${s.risk}</span>
        </div>
      </td>
      <td>
        <div class="risk-bar-wrap">
          <div class="risk-bar-bg"><div class="risk-bar-fill" style="width:${s.esg}%;background:${eColor}"></div></div>
          <span class="risk-score" style="color:var(--text-secondary)">${s.esg}</span>
        </div>
      </td>
      <td style="font-family:var(--font-mono);font-size:11px;">${s.co2}</td>
      <td><span class="disrupt-val ${s.disrupt > 2 ? "up" : "low"}">${s.disrupt > 0 ? "+" + s.disrupt : "—"}</span></td>
      <td style="font-family:var(--font-mono);font-size:10px;color:var(--text-muted)">${s.audit}</td>
      <td><span class="ext-link">↗</span></td>
    </tr>`;
  });
}

// ═══ ALERTS ═══════════════════════════════════════════════
function buildAlerts(containerId, maxItems) {
  const el = document.getElementById(containerId);
  if (!el || el.dataset.built) return;
  el.dataset.built = "1";
  const items = maxItems ? ALERTS.slice(0, maxItems) : ALERTS;
  items.forEach((a, i) => {
    el.innerHTML += `<div class="alert-item ${a.severity}" id="alert-${containerId}-${i}">
      <div class="alert-header">
        <div class="alert-tags">
          <span class="severity-tag ${a.severity}">${a.severity}</span>
          <span class="type-tag">${a.type}</span>
          <span class="region-tag">${a.region}</span>
        </div>
        <div style="display:flex;align-items:center;gap:10px;">
          <span class="alert-time">${a.time}</span>
          <button class="ack-btn ${a.acked ? "done" : ""}" onclick="ackAlert(this)">${a.acked ? "✓ ACK" : "ACK"}</button>
        </div>
      </div>
      <div class="alert-title">${a.title}</div>
      <div class="alert-desc">${a.desc}</div>
      <div class="alert-footer">
        <span class="alert-meta">${a.suppliers} supplier${a.suppliers !== 1 ? "s" : ""} affected · ${a.id}</span>
      </div>
    </div>`;
  });
}

function ackAlert(btn) {
  btn.textContent = "✓ ACK";
  btn.classList.add("done");
}

// ═══ PREDICTIONS ══════════════════════════════════════════
function buildPredictions() {
  const el = document.getElementById("predictions-list");
  if (!el || el.dataset.built) return;
  el.dataset.built = "1";
  PREDICTIONS.forEach((p, i) => {
    const bodyId = `pred-body-${i}`;
    el.innerHTML += `<div class="prediction-card ${p.severity}">
      <div class="prediction-header" onclick="togglePred('${bodyId}')">
        <div class="confidence-circle">${p.conf}%</div>
        <div class="prediction-info">
          <div class="prediction-title">${p.title}</div>
          <div class="prediction-meta">
            <span class="severity-tag ${p.severity}" style="margin-right:6px;">${p.severity}</span>
            ${p.type} · ${p.period}
          </div>
        </div>
        <span style="font-family:var(--font-mono);font-size:12px;color:var(--text-muted)">▾</span>
      </div>
      <div class="prediction-body ${p.open ? "open" : ""}" id="${bodyId}">
        <div>
          <div class="pred-section-label">Key Risk Drivers</div>
          ${p.drivers.map((d) => `<div class="pred-driver">${d}</div>`).join("")}
        </div>
        <div>
          <div class="pred-section-label">AI Recommendation</div>
          <div class="pred-rec">${p.rec}</div>
        </div>
      </div>
    </div>`;
  });
}

function togglePred(id) {
  const el = document.getElementById(id);
  el.classList.toggle("open");
}

// ═══ SUSTAINABILITY ════════════════════════════════════════
function buildTargets() {
  const el = document.getElementById("targets-list");
  if (!el || el.dataset.built) return;
  el.dataset.built = "1";
  ESG_TARGETS.forEach((t) => {
    const color = t.status === "on-track" ? "var(--green)" : "var(--amber)";
    const pct = t.pct || 70;
    el.innerHTML += `<div class="target-row">
      <div class="target-bar-container">
        <div class="target-bar-fill" style="height:${Math.min(100, pct)}%;background:${color}"></div>
      </div>
      <div class="target-name">${t.name}</div>
      <div class="target-progress" style="font-family:var(--font-mono);font-size:11px;color:var(--text-muted)">${t.current} / ${t.target}</div>
      <div class="target-status ${t.status}">${t.status === "on-track" ? "ON TRACK" : "BEHIND"}</div>
    </div>`;
  });
}

// ═══ CHARTS ═══════════════════════════════════════════════
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.color = "#9CA3AF";

function makeForecastChart(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || chartsInit[canvasId]) return;
  chartsInit[canvasId] = true;
  const labels = [
    "May 1",
    "May 8",
    "May 15",
    "May 22",
    "May 29",
    "Jun 7",
    "Jun 14",
    "Jun 21",
    "Jun 28",
    "Jul 5",
    "Jul 12",
    "Jul 19",
  ];
  const actual = [
    null,
    null,
    null,
    null,
    null,
    74,
    76,
    null,
    null,
    null,
    null,
    null,
  ];
  const predicted = [62, 64, 65, 68, 72, 74, 76, 78, 76, 73, 70, 68];
  const upper = [null, null, null, null, null, null, null, 82, 80, 77, 74, 72];
  const lower = [null, null, null, null, null, null, null, 74, 72, 69, 66, 64];

  new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Upper",
          data: upper,
          borderColor: "transparent",
          backgroundColor: "rgba(232,0,61,0.08)",
          fill: "+1",
          pointRadius: 0,
          tension: 0.4,
        },
        {
          label: "Lower",
          data: lower,
          borderColor: "transparent",
          backgroundColor: "rgba(232,0,61,0.08)",
          fill: false,
          pointRadius: 0,
          tension: 0.4,
        },
        {
          label: "Predicted",
          data: predicted,
          borderColor: "#9CA3AF",
          borderDash: [5, 3],
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.4,
          fill: false,
        },
        {
          label: "Actual",
          data: actual,
          borderColor: "var(--crimson)",
          borderWidth: 2,
          pointRadius: 3,
          tension: 0.4,
          fill: false,
          pointBackgroundColor: "var(--crimson)",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { mode: "index" } },
      scales: {
        x: { grid: { color: "#F0F0F0" }, ticks: { font: { size: 10 } } },
        y: {
          min: 40,
          max: 100,
          grid: { color: "#F0F0F0" },
          ticks: { font: { size: 10 }, stepSize: 15 },
        },
      },
    },
  });
}

function makeTrendChart() {
  const canvas = document.getElementById("trendChart");
  if (!canvas || chartsInit["trendChart"]) return;
  chartsInit["trendChart"] = true;
  const labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"];
  new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "ESG Score",
          data: [56, 58, 60, 62, 68, 73],
          borderColor: "#16A34A",
          backgroundColor: "rgba(22,163,74,0.07)",
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointBackgroundColor: "#16A34A",
        },
        {
          label: "Risk Index",
          data: [null, null, null, null, null, null],
          borderColor: "var(--crimson)",
          tension: 0.4,
          pointRadius: 4,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { font: { size: 11 }, usePointStyle: true },
        },
      },
      scales: {
        x: { grid: { color: "#F5F5F5" } },
        y: { min: 30, max: 90, grid: { color: "#F5F5F5" } },
      },
    },
  });
}

function makeMomChart() {
  const canvas = document.getElementById("momChart");
  if (!canvas || chartsInit["momChart"]) return;
  chartsInit["momChart"] = true;
  const cats = [
    "Electronics",
    "Energy",
    "Mining",
    "Textiles",
    "Chemicals",
    "Manufactur.",
    "Batteries",
  ];
  const curr = [68, 65, 78, 60, 35, 63, 27];
  new Chart(canvas, {
    type: "bar",
    data: {
      labels: cats,
      datasets: [
        {
          label: "Prior Month",
          data: [58, 55, 68, 54, 30, 55, 22],
          backgroundColor: "rgba(59,130,246,0.3)",
          borderRadius: 0,
        },
        {
          label: "Current",
          data: curr,
          backgroundColor: "rgba(232,0,61,0.7)",
          borderRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { font: { size: 11 }, usePointStyle: true },
        },
      },
      scales: {
        x: { grid: { display: false } },
        y: { min: 0, max: 100, grid: { color: "#F5F5F5" } },
      },
    },
  });
}

function makeRadarChart() {
  const canvas = document.getElementById("radarChart");
  if (!canvas || chartsInit["radarChart"]) return;
  chartsInit["radarChart"] = true;
  new Chart(canvas, {
    type: "radar",
    data: {
      labels: ["Carbon", "Water", "Waste", "Labor", "Governance", "Diversity"],
      datasets: [
        {
          data: [52, 68, 74, 61, 70, 58],
          borderColor: "#16A34A",
          backgroundColor: "rgba(22,163,74,0.12)",
          pointBackgroundColor: "#16A34A",
          borderWidth: 2,
          pointRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: { stepSize: 25, font: { size: 9 } },
          grid: { color: "#E5E7EB" },
          pointLabels: { font: { size: 11, family: "'Space Grotesk'" } },
        },
      },
    },
  });
}

function makeCo2Chart() {
  const canvas = document.getElementById("co2Chart");
  if (!canvas || chartsInit["co2Chart"]) return;
  chartsInit["co2Chart"] = true;
  const sorted = [...SUPPLIERS].sort((a, b) => a.co2 - b.co2);
  const getColor = (co2) =>
    co2 > 400
      ? "rgba(232,0,61,0.7)"
      : co2 > 200
        ? "rgba(217,119,6,0.7)"
        : "rgba(22,163,74,0.7)";
  new Chart(canvas, {
    type: "bar",
    data: {
      labels: sorted.map((s) => s.name.split(" ")[0]),
      datasets: [
        {
          data: sorted.map((s) => s.co2),
          backgroundColor: sorted.map((s) => getColor(s.co2)),
          borderRadius: 0,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: "#F5F5F5" }, ticks: { font: { size: 10 } } },
        y: { grid: { display: false }, ticks: { font: { size: 11 } } },
      },
    },
  });
}

// ═══ INIT PER PAGE ════════════════════════════════════════
function initChartsForPage(page) {
  if (page === "overview" || page === "riskmap") {
    buildTreemap("treemap-overview");
    buildTreemap("treemap-full");
  }
  if (page === "overview") {
    makeForecastChart("forecastChart");
    buildAlerts("alerts-preview", 3);
  }
  if (page === "aipred") {
    makeForecastChart("forecastChartFull");
    buildPredictions();
  }
  if (page === "suppliers") {
    buildSupplierTable();
    // Filter tabs
    const tabs = document.querySelectorAll("#page-suppliers .filter-tab");
    tabs.forEach((t) =>
      t.addEventListener("click", () => {
        tabs.forEach((x) => x.classList.remove("active"));
        t.classList.add("active");
      }),
    );
  }
  if (page === "sustainability") {
    makeRadarChart();
    buildTargets();
    makeCo2Chart();
  }
  if (page === "alerts") {
    buildAlerts("alerts-list");
    const tabs = document.querySelectorAll("#page-alerts .filter-tab");
    tabs.forEach((t) =>
      t.addEventListener("click", () => {
        tabs.forEach((x) => x.classList.remove("active"));
        t.classList.add("active");
      }),
    );
  }
  if (page === "trends") {
    makeTrendChart();
    makeMomChart();
  }
}

// Init overview on load
setTimeout(() => initChartsForPage("overview"), 100);
