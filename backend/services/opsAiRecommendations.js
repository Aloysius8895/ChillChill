const fs = require('fs');
const path = require('path');

const ANTHROPIC_URL = 'https://api.anthropic.com/v1/messages';
const DEFAULT_MODEL = process.env.ANTHROPIC_MODEL || 'claude-3-5-haiku-20241022';
const REQUEST_TIMEOUT_MS = Number(process.env.AI_RECOMMENDATION_TIMEOUT_MS || 10000);

function parseEnvFile(filePath) {
  if (!fs.existsSync(filePath)) return {};

  return fs.readFileSync(filePath, 'utf-8')
    .split(/\r?\n/)
    .reduce((values, line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) return values;

      const separatorIndex = trimmed.indexOf('=');
      if (separatorIndex === -1) return values;

      const key = trimmed.slice(0, separatorIndex).trim();
      const value = trimmed.slice(separatorIndex + 1).trim().replace(/^["']|["']$/g, '');
      values[key] = value;
      return values;
    }, {});
}

function getApiKey() {
  const backendEnv = parseEnvFile(path.join(__dirname, '..', '.env'));
  const rootEnv = parseEnvFile(path.join(__dirname, '..', '..', '.env'));
  const key = process.env.ANTHROPIC_API_KEY ||
    process.env.API_KEY ||
    backendEnv.ANTHROPIC_API_KEY ||
    backendEnv.API_KEY ||
    rootEnv.ANTHROPIC_API_KEY ||
    rootEnv.API_KEY ||
    '';

  if (!key || key.includes('paste-your-key-here')) return '';
  return key;
}

function localModel(data) {
  return {
    ...data,
    ai: false,
    ai_label: 'Local Model'
  };
}

function buildPrompt(data) {
  const current = data.current || {};
  const resources = Array.isArray(current.resources) ? current.resources : [];
  const candidates = Array.isArray(data.recommendations) ? data.recommendations : [];

  const resourceLines = resources
    .filter(resource => resource.cost_saved_usd > 0 || resource.reduced_carbon_kg > 0 || resource.issues.length || resource.waste.length)
    .map(resource => {
      const featureOutputs = resource.feature_outputs || {};
      const security = featureOutputs.feature1_security || {};
      const efficiency = featureOutputs.feature2_efficiency || {};
      const carbon = featureOutputs.feature3_carbon || {};
      const issues = resource.issues.map(issue => `${issue[0]}:${issue[1]}`).join('; ') || 'none';
      const waste = resource.waste.join('; ') || 'none';
      return [
        resource.id,
        resource.name,
        resource.service,
        `F1 security score ${security.score ?? resource.security_score}`,
        `F2 efficiency ${efficiency.classification || 'unknown'} score ${efficiency.score ?? resource.efficiency_score}`,
        `F3 carbon ${carbon.carbon_kg_month ?? resource.carbon}kgCO2 @ ${carbon.region_carbon_intensity ?? 'unknown'}g/kWh`,
        `$${resource.monthly_cost_usd}/mo`,
        `${resource.utilization_pct}% util`,
        `${resource.carbon}kgCO2/mo`,
        `$${resource.cost_saved_usd}/mo saved`,
        `${resource.reduced_carbon_kg}kgCO2 saved`,
        `SEC[${issues}]`,
        `WASTE[${waste}]`
      ].join(' | ');
    })
    .join('\n');

  const candidateIds = candidates.map(item => item.resource_id).filter(Boolean).join(', ');

  return `You are the AI Recommendation Engine for Feature 4 of a construction cloud governance dashboard.
Rewrite and rank recommendations using the outputs from Feature 1 security, Feature 2 resource efficiency, and Feature 3 carbon footprint.
Use only these resource_id values: ${candidateIds}.
Do not invent resources. Do not calculate or change money, carbon, security point, or score values.

Current scores:
CHS ${current.scores?.chs}, Security ${current.scores?.security}, Efficiency ${current.scores?.efficiency}, Sustainability ${current.scores?.sustainability}

Dataset-derived Feature 1/2/3 outputs per resource:
${resourceLines}

Return ONLY valid JSON with this exact shape:
{"recommendations":[{"resource_id":"...","action":"short imperative action","category":"security|cost|carbon","rationale":"one sentence, construction context"}]}
Give up to 6 highest-impact recommendations.`;
}

function extractJsonObject(text) {
  const cleaned = String(text || '').replace(/```json|```/g, '').trim();
  const first = cleaned.indexOf('{');
  const last = cleaned.lastIndexOf('}');
  if (first === -1 || last === -1 || last <= first) {
    throw new Error('Model response did not contain JSON');
  }
  return JSON.parse(cleaned.slice(first, last + 1));
}

function normalizeModelRecommendations(modelRecommendations, fallbackRecommendations) {
  const fallbackById = new Map(
    fallbackRecommendations
      .filter(item => item.resource_id)
      .map(item => [item.resource_id, item])
  );

  const normalized = [];

  for (const item of modelRecommendations || []) {
    const base = fallbackById.get(item.resource_id);
    if (!base) continue;

    normalized.push({
      ...base,
      rank: normalized.length + 1,
      action: String(item.action || base.action).slice(0, 90),
      category: String(item.category || base.category),
      rationale: String(item.rationale || base.rationale).slice(0, 240)
    });
  }

  if (!normalized.length) {
    return fallbackRecommendations;
  }

  const usedIds = new Set(normalized.map(item => item.resource_id));
  for (const fallback of fallbackRecommendations) {
    if (normalized.length >= 6) break;
    if (usedIds.has(fallback.resource_id)) continue;

    normalized.push({
      ...fallback,
      rank: normalized.length + 1
    });
  }

  return normalized;
}

async function callAnthropic(data, apiKey) {
  if (typeof fetch !== 'function') {
    throw new Error('Node fetch API is unavailable');
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(ANTHROPIC_URL, {
      method: 'POST',
      signal: controller.signal,
      headers: {
        'content-type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: DEFAULT_MODEL,
        max_tokens: 900,
        messages: [
          {
            role: 'user',
            content: buildPrompt(data)
          }
        ]
      })
    });

    if (!response.ok) {
      throw new Error(`Anthropic request failed: ${response.status} ${response.statusText}`);
    }

    const payload = await response.json();
    const text = Array.isArray(payload.content)
      ? payload.content.map(item => item.type === 'text' ? item.text : '').join('')
      : '';

    return extractJsonObject(text);
  } finally {
    clearTimeout(timeout);
  }
}

async function addAiRecommendations(data) {
  const fallbackData = localModel(data);
  const apiKey = getApiKey();

  if (!apiKey) {
    return fallbackData;
  }

  try {
    const modelData = await callAnthropic(data, apiKey);
    const fallbackRecommendations = Array.isArray(data.recommendations) ? data.recommendations : [];

    return {
      ...data,
      ai: true,
      ai_label: 'Claude AI',
      recommendations: normalizeModelRecommendations(
        modelData.recommendations,
        fallbackRecommendations
      )
    };
  } catch (error) {
    return {
      ...fallbackData,
      ai_error: error.message
    };
  }
}

module.exports = {
  addAiRecommendations
};
