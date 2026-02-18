#!/usr/bin/env node
/**
 * AI Harness - CLI Entry Point
 * 
 * Usage:
 *   ai-harness              # Interactive mode
 *   ai-harness scan         # Scan projects
 *   ai-harness status       # Show project status
 *   ai-harness run          # Run single task
 *   ai-harness continuous   # Run continuously
 */

const { spawn } = require('child_process');
const path = require('path');

const scriptPath = path.join(__dirname, '..', 'iflow_runner.py');
const args = process.argv.slice(2);

// Default to interactive mode if no args
if (args.length === 0) {
  args.push('--interactive');
}

// Spawn Python process
const child = spawn('python', [scriptPath, ...args], {
  stdio: 'inherit',
  env: { 
    ...process.env, 
    PYTHONIOENCODING: 'utf-8',
    PYTHONUTF8: '1'
  },
  shell: process.platform === 'win32'
});

child.on('error', (err) => {
  if (err.code === 'ENOENT') {
    console.error('[ERROR] Python not found. Please install Python 3.8+');
  } else {
    console.error('[ERROR]', err.message);
  }
  process.exit(1);
});

child.on('exit', (code) => {
  process.exit(code || 0);
});
