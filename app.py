from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import asyncio
import edge_tts
import re

async def generate_voice(text):
    # মাইক্রোসফটের আসল মিষ্টি আবেগভরা বাঙালি নারীকণ্ঠ
    voice = "bn-BD-NabanitaNeural"
    # পিচ এবং স্পিড সামান্য বাড়িয়ে আরও কিউট ও ন্যাচারাল করা হয়েছে
    communicate = edge_tts.Communicate(text, voice, pitch="+12Hz", rate="+5%")
    audio_data = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
    return bytes(audio_data)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        raw_text = query.get('text', [''])[0].strip()

        if not raw_text:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("Text missing!".encode('utf-8'))
            return

        clean_text = re.sub(r'[\U00010000-\U0010ffff]', '', raw_text)
        clean_text = re.sub(r'[()\[\]*#_~]', '', clean_text).strip()[:200]

        try:
            audio_bytes = asyncio.run(generate_voice(clean_text))
            self.send_response(200)
            self.send_header('Content-type', 'audio/mpeg')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'public, max-age=86400')
            self.end_headers()
            self.wfile.write(audio_bytes)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"TTS Error: {str(e)}".encode('utf-8'))

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=10000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Server running on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
