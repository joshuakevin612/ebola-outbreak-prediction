import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { spawn } from 'node:child_process'
import { createInterface } from 'node:readline'
import { fileURLToPath } from 'node:url'
import { resolve } from 'node:path'

function pythonApiBridge() {
  let worker
  const pending = []
  return {
    name: 'python-model-api',
    configureServer(server) {
      const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
      worker = spawn('python', [resolve(root, 'api.py'), '--stdio'], { cwd: root, stdio: ['pipe', 'pipe', 'pipe'] })
      const lines = createInterface({ input: worker.stdout })
      lines.on('line', (line) => {
        const response = pending.shift()
        if (!response) return
        try {
          const payload = JSON.parse(line)
          response.writeHead(payload.status, { 'Content-Type': 'application/json; charset=utf-8' })
          response.end(JSON.stringify(payload.payload))
        } catch {
          response.writeHead(502, { 'Content-Type': 'application/json' })
          response.end(JSON.stringify({ error: 'The model API returned an unreadable response.' }))
        }
      })
      worker.stderr.on('data', (data) => process.stderr.write(data))
      worker.on('error', (error) => process.stderr.write(`Python model API could not start: ${error.message}\n`))
      worker.on('exit', (code) => {
        if (code === 0) return
        for (const response of pending.splice(0)) {
          response.writeHead(503, { 'Content-Type': 'application/json' })
          response.end(JSON.stringify({ error: 'The Python model process stopped. Restart the frontend dev server and try again.' }))
        }
      })
      server.middlewares.use((request, response, next) => {
        if (!request.url?.startsWith('/api/')) return next()
        if (!worker || worker.killed || !worker.stdin.writable) {
          response.writeHead(503, { 'Content-Type': 'application/json' })
          return response.end(JSON.stringify({ error: 'Restart the frontend dev server to start the Python model API.' }))
        }
        const chunks = []
        request.on('data', (chunk) => chunks.push(chunk))
        request.on('end', () => {
          let body = {}
          try { if (chunks.length) body = JSON.parse(Buffer.concat(chunks).toString('utf8')) } catch {
            response.writeHead(400, { 'Content-Type': 'application/json' })
            return response.end(JSON.stringify({ error: 'The request body must be valid JSON.' }))
          }
          pending.push(response)
          worker.stdin.write(`${JSON.stringify({ method: request.method, url: request.url, body })}\n`)
        })
      })
      server.httpServer?.once('close', () => worker?.kill())
    },
  }
}

export default defineConfig({
  plugins: [react(), pythonApiBridge()],
})
