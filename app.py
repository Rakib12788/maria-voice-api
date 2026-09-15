from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import asyncio
import edge_tts
import os
import re

# মাইক্রোসফটের ন্যাচারাল ও মিষ্টি বাংলা ফিমেল ভয়েস
VOICE = "bn-BD-NabanitaNeural"

async def generate_emotional_audio(text):
    # কোনো SSML ট্যাগ ছাড়া সরাসরি টেক্সট পাস করা হলো যাতে কণ্ঠ পরিষ্কার ও স্বাভাবিক থাকে
    communicate = edge_tts.Communicate(text, VOICE)
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

        # ইমোজি বা অপ্রয়োজনীয় ক্যারেক্টার ক্লিন করা
        clean_text = re.sub(r'[()\[\]*#_~]', '', raw_text).strip()[:300]

        try:
            # অ্যাসিনক্রোনাস ভয়েস জেনারেট করা
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_bytes = loop.run_until_complete(generate_emotional_audio(clean_text))
            loop.close()

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

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler):
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Server running on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
