import { spawn } from 'node:child_process';

const processes = [];

function start(command, args) {
  const child = spawn(command, args, { stdio: 'inherit', shell: false });
  processes.push(child);
  return child;
}

const api = start(process.execPath, ['mock-server/server.js']);
const vite = start(process.execPath, ['node_modules/vite/bin/vite.js']);

function stop(exitCode = 0) {
  processes.forEach((child) => child.exitCode === null && child.kill());
  process.exit(exitCode);
}

process.on('SIGINT', () => stop());
process.on('SIGTERM', () => stop());

vite.on('exit', (code) => stop(code ?? 0));
api.on('exit', (code) => {
  if (code && vite.exitCode === null) {
    console.error('The roadmap API stopped. Check whether port 4000 is already in use.');
  }
});
