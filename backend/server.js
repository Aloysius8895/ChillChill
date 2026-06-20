const express = require('express');
const cors = require('cors');
const securityRoutes = require('./routes/securityRoutes');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    message: 'Cloud Security backend is running'
  });
});

app.use('/api/security', securityRoutes);

app.listen(PORT, () => {
  console.log(`Cloud Security backend running on http://localhost:${PORT}`);
});
