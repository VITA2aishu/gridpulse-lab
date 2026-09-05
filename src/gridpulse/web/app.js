const assetGrid = document.querySelector('#asset-grid');
const assetSelect = document.querySelector('#incident-asset');
let knownAssets = [];

const point = (asset, name) => asset.points[name];
const value = (asset, name, digits = 1) => {
  const item = point(asset, name);
  if (item.value === null) return '—';
  return typeof item.value === 'number' ? item.value.toFixed(digits) : String(item.value);
};
const qualityClass = item => `quality-${item.quality}`;

function renderAsset(asset) {
  const soc = point(asset, 'soc');
  const health = asset.health || {status: 'unknown', score: 0};
  return `<article class="asset">
    <div class="asset-header"><div><h3>${asset.name}</h3><p>${asset.region} · ${asset.capacity_mw} MW / ${asset.energy_mwh} MWh</p></div>
      <span class="badge health-${health.status}">${health.status} · ${health.score}</span></div>
    <div class="soc-line"><div><span>STATE OF CHARGE</span><br><strong class="${qualityClass(soc)}">${value(asset, 'soc')}%</strong></div><span>${asset.asset_id}</span></div>
    <div class="soc-track"><div class="soc-fill" style="width:${soc.value || 0}%"></div></div>
    <div class="metrics">
      ${metric(asset, 'active_power', 'Active power', 2)}
      ${metric(asset, 'reactive_power', 'Reactive power', 2)}
      ${metric(asset, 'frequency', 'Frequency', 3)}
      ${metric(asset, 'temperature', 'Temperature', 1)}
    </div>
  </article>`;
}

function metric(asset, name, label, digits) {
  const item = point(asset, name);
  return `<div class="metric"><span>${label}</span><strong class="${qualityClass(item)}">${value(asset, name, digits)} ${item.unit}</strong></div>`;
}

async function refresh() {
  try {
    const response = await fetch('/api/v1/telemetry');
    const data = await response.json();
    assetGrid.innerHTML = data.assets.map(renderAsset).join('');
    const output = data.assets.reduce((sum, asset) => sum + point(asset, 'active_power').value, 0);
    const soc = data.assets.reduce((sum, asset) => sum + (point(asset, 'soc').value || 0), 0) / data.assets.length;
    const attention = data.quality_summary.bad + data.quality_summary.stale + data.quality_summary.missing;
    document.querySelector('#fleet-output').textContent = output.toFixed(1);
    document.querySelector('#average-soc').textContent = soc.toFixed(1);
    document.querySelector('#healthy-points').textContent = data.quality_summary.good;
    document.querySelector('#attention-points').textContent = attention;
    document.querySelector('#last-updated').textContent = `Updated ${new Date(data.generated_at).toLocaleTimeString()}`;
    document.querySelector('#alarm-list').innerHTML = data.alarms.length
      ? data.alarms.map(alarm => `<div class="alarm-row"><strong>${alarm.severity}</strong><span>${alarm.asset_id}</span><p>${alarm.message}</p></div>`).join('')
      : '<p class="empty-state">No active alarms</p>';
    if (knownAssets.length === 0) {
      knownAssets = data.assets;
      assetSelect.innerHTML = data.assets.map(a => `<option value="${a.asset_id}">${a.name}</option>`).join('');
    }
  } catch (error) {
    document.querySelector('#last-updated').textContent = 'Telemetry unavailable';
  }
}

document.querySelector('#incident-form').addEventListener('submit', async event => {
  event.preventDefault();
  await fetch('/api/v1/incidents', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ asset_id: assetSelect.value, kind: document.querySelector('#incident-kind').value }) });
  refresh();
});

document.querySelector('#clear-incidents').addEventListener('click', async () => {
  await Promise.all(knownAssets.map(asset => fetch(`/api/v1/incidents/${asset.asset_id}`, {method: 'DELETE'})));
  refresh();
});

refresh();
setInterval(refresh, 2000);
