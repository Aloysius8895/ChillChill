const express = require('express');
const { runOpsAnalyzer } = require('../services/opsAnalyzerRunner');
const { addAiRecommendations } = require('../services/opsAiRecommendations');

const router = express.Router();

router.get('/analyze', async (req, res) => {
  try {
    const analyzedData = await runOpsAnalyzer();
    const data = await addAiRecommendations(analyzedData);
    res.json(data);
  } catch (error) {
    res.status(500).json({
      error: 'Failed to analyze construction-ready operations data',
      details: error.message
    });
  }
});

module.exports = router;
