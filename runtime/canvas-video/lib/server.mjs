import http from 'node:http';
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { extname, normalize, resolve, sep } from 'node:path';

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.css': 'text/css; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2', '.ttf': 'font/ttf',
  '.otf': 'font/otf', '.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.mp4': 'video/mp4', '.mov': 'video/quicktime',
};

function contained(root, file) {
  return file === root || file.startsWith(`${root}${sep}`);
}

function resolveRequest(projectRoot, runtimeRoot, requestPath) {
  if (requestPath.startsWith('/@canvas-video/vendor/three/')) {
    const relative = requestPath.slice('/@canvas-video/vendor/three/'.length);
    const vendorRoot = resolve(runtimeRoot, 'node_modules', 'three');
    const file = resolve(vendorRoot, relative);
    return contained(vendorRoot, file) ? file : null;
  }
  const relative = normalize(requestPath).replace(/^[/\\]+/, '');
  const file = resolve(projectRoot, relative || 'scene.html');
  return contained(projectRoot, file) ? file : null;
}

export function startServer(projectRoot, runtimeRoot, port = 0) {
  const server = http.createServer(async (request, response) => {
    const requestPath = decodeURIComponent(new URL(request.url, 'http://canvas-video.local').pathname);
    const file = resolveRequest(projectRoot, runtimeRoot, requestPath);
    if (!file) {
      response.writeHead(403);
      response.end('forbidden');
      return;
    }
    try {
      const info = await stat(file);
      if (!info.isFile()) throw new Error('not a file');
      const type = TYPES[extname(file).toLowerCase()] ?? 'application/octet-stream';
      const match = request.headers.range?.match(/^bytes=(\d*)-(\d*)$/);
      if (match) {
        const start = match[1] ? Number(match[1]) : 0;
        const end = match[2] ? Math.min(Number(match[2]), info.size - 1) : info.size - 1;
        if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start > end || start >= info.size) {
          response.writeHead(416, { 'Content-Range': `bytes */${info.size}` });
          response.end();
          return;
        }
        response.writeHead(206, {
          'Accept-Ranges': 'bytes', 'Content-Type': type, 'Content-Length': end - start + 1,
          'Content-Range': `bytes ${start}-${end}/${info.size}`,
        });
        createReadStream(file, { start, end }).pipe(response);
        return;
      }
      response.writeHead(200, { 'Accept-Ranges': 'bytes', 'Content-Type': type, 'Content-Length': info.size });
      createReadStream(file).pipe(response);
    } catch {
      response.writeHead(404);
      response.end('not found');
    }
  });
  return new Promise(resolveStarted => {
    server.listen(port, '127.0.0.1', () => resolveStarted({ server, port: server.address().port }));
  });
}
