const express = require('express');
const fs = require('fs');
const path = require('path');
const { analyzeSecurityData } = require('../services/securityAnalyzer');

const router = express.Router();

function loadCloudData() {
  const filePath = path.join(__dirname, '../data/hilti-cloud-data.json');
  const rawData = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(rawData);
}

function getAnalysis() {
  const cloudData = loadCloudData();
  return analyzeSecurityData(cloudData);
}

function matchesFilter(value, filter) {
  if (!filter) return true;

  const normalizedValue = String(value || '').toLowerCase();
  const normalizedFilter = String(filter).toLowerCase();

  return normalizedValue === normalizedFilter || normalizedValue.includes(normalizedFilter);
}

function handleSecurityDataError(res, error) {
  res.status(500).json({
    error: 'Failed to load security data',
    details: error.message
  });
}

router.get('/', (req, res) => {
  res.json({
    message: 'Cloud Security API is running',
    endpoints: ['/summary', '/findings', '/dashboard', '/graph', '/resources/:id']
  });
});

router.get('/summary', (req, res) => {
  try {
    const analysis = getAnalysis();
    res.json(analysis.securitySummary);
  } catch (error) {
    handleSecurityDataError(res, error);
  }
});

router.get('/findings', (req, res) => {
  try {
    const { category, severity, status, owner, resourceType } = req.query;
    const analysis = getAnalysis();

    const findings = analysis.findings.filter(finding => (
      matchesFilter(finding.category, category) &&
      matchesFilter(finding.severity, severity) &&
      matchesFilter(finding.status, status) &&
      matchesFilter(finding.owner, owner) &&
      matchesFilter(finding.resourceType, resourceType)
    ));

    res.json(findings);
  } catch (error) {
    handleSecurityDataError(res, error);
  }
});

router.get('/dashboard', (req, res) => {
  try {
    const analysis = getAnalysis();
    res.json(analysis.dashboardData);
  } catch (error) {
    handleSecurityDataError(res, error);
  }
});

router.get('/graph', (req, res) => {
  try {
    const analysis = getAnalysis();
    res.json(analysis.graphData);
  } catch (error) {
    handleSecurityDataError(res, error);
  }
});

router.get('/resources/:id', (req, res) => {
  try {
    const cloudData = loadCloudData();
    const analysis = analyzeSecurityData(cloudData);
    const resources = Array.isArray(cloudData.resources) ? cloudData.resources : [];
    const graphNodes = Array.isArray(analysis.graphData.nodes) ? analysis.graphData.nodes : [];
    const relationships = Array.isArray(analysis.graphData.edges)
      ? analysis.graphData.edges.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        type: edge.type,
        label: edge.label
      }))
      : [];
    const resource = resources.find(item => item.id === req.params.id) ||
      graphNodes.find(item => item.id === req.params.id);

    if (!resource) {
      res.status(404).json({
        error: 'Resource not found'
      });
      return;
    }

    const relatedFindings = analysis.findings.filter(finding => finding.resourceId === resource.id);
    const resourceRelationships = relationships.filter(relationship => (
      relationship.source === resource.id || relationship.target === resource.id
    ));
    const connectedResourceIds = new Set();

    resourceRelationships.forEach(relationship => {
      const connectedId = relationship.source === resource.id
        ? relationship.target
        : relationship.source;

      if (connectedId && connectedId !== resource.id) {
        connectedResourceIds.add(connectedId);
      }
    });

    const connectedResources = Array.from(connectedResourceIds)
      .map(resourceId => resources.find(item => item.id === resourceId) ||
        graphNodes.find(item => item.id === resourceId))
      .filter(Boolean);

    res.json({
      resource,
      relatedFindings,
      connectedResources,
      relationships: resourceRelationships
    });
  } catch (error) {
    handleSecurityDataError(res, error);
  }
});

module.exports = router;
