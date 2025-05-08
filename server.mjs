import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readFileSync } from 'node:fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// MIME 타입 매핑
const MIME_TYPES = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

const server = createServer((req, res) => {
  // 기본 경로 설정
  let filePath = req.url === '/' 
    ? join(__dirname, 'public', 'index.html')
    : join(__dirname, 'public', req.url);

  // 파일 확장자 가져오기
  const extname = String(filePath).split('.').pop();
  const contentType = MIME_TYPES[`.${extname}`] || 'application/octet-stream';

  try {
    // 파일 읽기
    const content = readFileSync(filePath);
    
    // 응답 헤더 설정
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content, 'utf-8');
  } catch (error) {
    if (error.code === 'ENOENT') {
      // 파일을 찾을 수 없는 경우
      res.writeHead(404);
      res.end('404 Not Found');
    } else {
      // 서버 오류
      res.writeHead(500);
      res.end(`Server Error: ${error.code}`);
    }
  }
});

// 서버 시작
const PORT = process.env.PORT || 3000;
server.listen(PORT, '127.0.0.1', () => {
  console.log(`서버가 http://127.0.0.1:${PORT} 에서 실행 중입니다.`);
}); 