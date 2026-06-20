const { spawn } = require('child_process');
const path = require('path');

const PYTHON_BIN = process.env.PYTHON_BIN || 'python';
const SCRIPT_PATH = path.join(__dirname, '..', 'python', 'analyze_feature4.py');
const ANALYZER_TIMEOUT_MS = Number(process.env.OPS_ANALYZER_TIMEOUT_MS || 15000);

function runOpsAnalyzer() {
  return new Promise((resolve, reject) => {
    const child = spawn(PYTHON_BIN, [SCRIPT_PATH], {
      cwd: path.join(__dirname, '..'),
      windowsHide: true
    });

    let stdout = '';
    let stderr = '';
    let settled = false;

    const timeout = setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill();
      reject(new Error(`Feature 4 analyzer timed out after ${ANALYZER_TIMEOUT_MS}ms`));
    }, ANALYZER_TIMEOUT_MS);

    child.stdout.on('data', chunk => {
      stdout += chunk.toString('utf8');
    });

    child.stderr.on('data', chunk => {
      stderr += chunk.toString('utf8');
    });

    child.on('error', error => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      reject(error);
    });

    child.on('close', code => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);

      if (code !== 0) {
        reject(new Error(stderr.trim() || `Feature 4 analyzer exited with code ${code}`));
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`Feature 4 analyzer returned invalid JSON: ${error.message}`));
      }
    });
  });
}

module.exports = {
  runOpsAnalyzer
};
