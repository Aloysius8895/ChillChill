const express = require('express');
const cors = require('cors');
const path = require('path');
const opsRoutes = require('./routes/opsRoutes');
const securityRoutes = require('./routes/securityRoutes');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());
app.use('/frontend', express.static(path.join(__dirname, '../frontend')));
app.use('/pic', express.static(path.join(__dirname, '../pic')));

app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    message: 'Cloud Security backend is running'
  });
});

app.use('/api/security', securityRoutes);
app.use('/api', opsRoutes);

app.get('/', (req, res) => {
  res.redirect('/frontend/index.html');
});

app.listen(PORT, () => {
  console.log(`Cloud Security backend running on http://localhost:${PORT}`);
});
