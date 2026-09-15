import asyncio
import os
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import edge_tts

# মাইক্রোসফটের ন্যাচারাল বাংলা ফিমেল ভয়েস
VOICE = "bn-BD-NabanitaNeural"

async def generate_audio(text):
    communicate = edge_tts.Communicate(text, VOICE)
    audio_data = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
    return bytes(audio_data)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            query_string = parsed_path.query
            raw_text = ""
            
            for param in query_string.split('&'):
                if param.startswith('text='):
                    raw_text = unquote(param[5:], encoding='utf-8')
                    break

            raw_text = raw_text.strip()
            if not raw_text:
                raw_text = "বলো সোনা"

            # যেকোনো জটিল ক্যারেক্টার বা মার্কডাউন ক্লিন করা
            clean_text = re.sub(r'[()\[\]*#_~`!@$%^&+=|\:;""\'<>,.?/]', ' ', raw_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()[:300]

            if not clean_text:
                clean_text = "শুনছি"

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_bytes = loop.run_until_complete(generate_audio(clean_text))
            loop.close()

            self.send_response(200)
            self.send_header('Content-type', 'audio/mpeg')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            self.wfile.write(audio_bytes)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode('utf-8'))

def run():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Server running on port {port}")
    server.serve_forever()

if __name__ == '__main__':
    run()
