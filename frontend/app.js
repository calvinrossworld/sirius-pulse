/* Sirius Pulse — Frontend App */
const API_BASE = '';

let currentPlanId = null;

const formSection = document.getElementById('form-section');
const loadingSection = document.getElementById('loading-section');
const planSection = document.getElementById('plan-section');
const form = document.getElementById('strategy-form');
const submitBtn = document.getElementById('submit-btn');
const btnText = submitBtn.querySelector('.btn-text');
const btnLoader = submitBtn.querySelector('.btn-loader');
const planContent = document.getElementById('plan-content');
const planArtistName = document.getElementById('plan-artist-name');
const downloadBtn = document.getElementById('download-btn');

form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const formData = new FormData(form);
  const data = {
    stage_name: formData.get('stage_name'),
    genre: formData.get('genre'),
    subgenre: formData.get('subgenre') || '',
    career_stage: formData.get('career_stage'),
    platforms: formData.getAll('platforms'),
    promoting: formData.get('promoting'),
    model_artists: formData.get('model_artists') || '',
    challenge: formData.get('challenge') || '',
  };

  if (data.platforms.length === 0) {
    alert('Please select at least one platform.');
    return;
  }

  // Show loading
  formSection.hidden = true;
  loadingSection.hidden = false;
  submitBtn.disabled = true;
  btnText.hidden = false;
  btnLoader.hidden = true;

  try {
    const res = await fetch(`${API_BASE}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const json = await res.json();
    currentPlanId = json.plan_id;
    await displayPlan(json.plan_id, data.stage_name);
  } catch (err) {
    alert(`Something went wrong: ${err.message}`);
    formSection.hidden = false;
    loadingSection.hidden = true;
    submitBtn.disabled = false;
  }
});

async function displayPlan(planId, artistName) {
  const res = await fetch(`${API_BASE}/plan/${planId}`);
  if (!res.ok) throw new Error('Failed to load plan');
  const { plan, artist } = await res.json();

  planArtistName.textContent = artist.stage_name;
  planContent.innerHTML = '';

  // Profile Audit
  if (plan.profile_audit) {
    planContent.appendChild(makeCard('Profile Audit', plan.profile_audit));
  }

  // Platforms
  const platforms = plan.platforms || {};
  for (const [platform, data] of Object.entries(platforms)) {
    if (!data) continue;
    const block = document.createElement('div');
    block.className = 'platform-block';

    const icons = { instagram: '📸', tiktok: '🎵', youtube: '▶️', twitter: '🐦' };
    block.innerHTML = `
      <div class="platform-title">
        <span class="platform-icon">${icons[platform] || '◎'}</span>
        ${platform.charAt(0).toUpperCase() + platform.slice(1)}
      </div>
      <div class="platform-meta">
        <div class="platform-meta-item">
          <span class="meta-label">Frequency</span>
          <span class="meta-value">${data.posting_frequency || '—'}</span>
        </div>
        <div class="platform-meta-item">
          <span class="meta-label">Best Times</span>
          <span class="meta-value">${data.best_times || '—'}</span>
        </div>
      </div>
      ${data.content_types?.length ? `<p style="font-size:13px; color:#9CA3AF; margin-bottom:12px"><strong style="color:#fff">Types:</strong> ${data.content_types.join(', ')}</p>` : ''}
      ${(data.example_posts || []).map((p, i) => `
        <div class="example-post">
          <div class="example-post-label">Example Post ${i + 1}</div>
          <p><strong>Hook:</strong> ${p.hook}</p>
          <p><strong>Format:</strong> ${p.format}</p>
          <p><strong>Caption:</strong> ${p.caption_hint}</p>
        </div>
      `).join('')}
    `;
    planContent.appendChild(block);
  }

  // Caption Framework
  if (plan.caption_framework) {
    planContent.appendChild(makeCard('Caption Framework', plan.caption_framework));
  }

  // Calendar
  if (plan.calendar_30day) {
    planContent.appendChild(makeCard('30-Day Content Calendar', plan.calendar_30day));
  }

  // Growth Tactics
  if (plan.growth_tactics) {
    const gt = plan.growth_tactics;
    if (typeof gt === 'object') {
      const card = document.createElement('div');
      card.className = 'plan-card';
      let html = '<div class="plan-section-title">Growth Tactics</div><div class="plan-body">';
      if (gt.next_7_days_actions?.length) {
        html += '<strong>Next 7 Days:</strong><ul>';
        gt.next_7_days_actions.forEach(a => { html += `<li>${a}</li>`; });
        html += '</ul>';
      }
      if (gt.things_to_avoid?.length) {
        html += '<strong>Avoid:</strong><ul>';
        gt.things_to_avoid.forEach(a => { html += `<li>${a}</li>`; });
        html += '</ul>';
      }
      html += '</div>';
      card.innerHTML = html;
      planContent.appendChild(card);
    } else {
      planContent.appendChild(makeCard('Growth Tactics', gt));
    }
  }

  loadingSection.hidden = true;
  planSection.hidden = false;
}

function makeCard(title, body) {
  const card = document.createElement('div');
  card.className = 'plan-card';
  card.innerHTML = `
    <div class="plan-section-title">${title}</div>
    <div class="plan-body">${body}</div>
  `;
  return card;
}

downloadBtn.addEventListener('click', () => {
  if (!currentPlanId) return;
  window.open(`${API_BASE}/download/${currentPlanId}`, '_blank');
});

// Platform "all" toggle logic
const platformCheckboxes = document.querySelectorAll('input[name="platforms"]');
platformCheckboxes.forEach(cb => {
  cb.addEventListener('change', () => {
    // Optional: could add "select all" logic here
  });
});