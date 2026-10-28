// Synthetic worker for one disposable, credential-free Hyper-V service test.
// Uses the retained authenticated per-VM bridge; never dials the physical GPU.
import fs from 'node:fs';
import net from 'node:net';
import {startDesktopWorkerTransport} from './desktop-worker-transport.mjs';
const cfg = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (cfg.disposableFixtureOnly !== true || cfg.timeoutSeconds !== 240) throw Error('explicit bounded fixture required');
const sockets = new Set();
let connections = 0, receivedBytes = 0;
const worker = net.createServer(socket => {
  if (sockets.size >= 8) { socket.destroy(); return; }
  connections++; sockets.add(socket);
  socket.on('error', () => {});
  socket.on('close', () => sockets.delete(socket));
  socket.on('data', data => { receivedBytes += data.length; socket.destroy(); });
});
await new Promise(resolve => worker.listen(0, '127.0.0.1', resolve));
let transport;
try {
  transport = await startDesktopWorkerTransport({bridge: cfg.bridge, vmId: cfg.vmId,
    mapping: {appId: cfg.expect.appID, record: {runtimeId: cfg.runtimeId,
      desktop: {profile: 'kvm-box-masked-v1', profileSha256: cfg.expect.profileSHA, gpuMilli: cfg.expect.gpuMilli}}},
    runtimeId: cfg.runtimeId, workerPort: worker.address().port});
  fs.writeFileSync(cfg.readyFile, JSON.stringify({ready: true, vmId: cfg.vmId, pid: process.pid}));
  await Promise.race([transport.exited, new Promise(resolve => {
    const deadline = Date.now() + cfg.timeoutSeconds * 1000;
    const interval = setInterval(() => {
      if (Date.now() >= deadline || fs.existsSync(cfg.stopFile)) { clearInterval(interval); resolve(); }
    }, 250);
    transport.exited.then(() => { clearInterval(interval); resolve(); });
  })]);
} finally {
  await transport?.stop();
  await new Promise(resolve => { worker.close(resolve); for (const socket of sockets) socket.destroy(); });
  fs.writeFileSync(cfg.resultFile, JSON.stringify({vmId: cfg.vmId, connections, receivedBytes,
    stats: transport?.stats(), syntheticWorker: true, physicalGpuAccess: false}));
}
