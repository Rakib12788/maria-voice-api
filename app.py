from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import asyncio
import edge_tts
import os
import re

# মাইক্রোসফটের আসল এবং ডিফল্ট ন্যাচারাল বাংলা ভয়েস (নবনিতা)
VOICE = "bn-BD-NabanitaNeural"

async def generate_natural_audio(text):
    # মাইক্রোসফটের ডিফল্ট ন্যাচারাল ভয়েস পেতে কোনো কাস্টম পিচ বা রেট দেওয়া হলো না 
    # যাতে কণ্ঠ একদম নিখুঁত, পরিষ্কার এবং আসল মাইক্রোসফট স্টাইলের হয়।
    communicate = edge_tts.Communicate(text, VOICE)
    
    audio_data = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data.extend(chunk["data"])
    return bytes(audio_data)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query_string = parsed_path.query
        raw_text = ""
        
        for param in query_string.split('&'):
            if param.startswith('text='):
                raw_text = unquote(param[5:], encoding='utf-8')
                break

        raw_text = raw_text.strip()

        if not raw_text:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("Text missing!".encode('utf-8'))
            return

        # টেক্সট একদম পরিষ্কার করা যাতে কোনো অদ্ভুত সিম্বল বা মার্কডাউন ভয়েস ইঞ্জিনকে confuse না করে
        clean_text = re.sub(r'[()\[\]*#_~`!@$%^&+=|\:;""\'<>,.?/]', ' ', raw_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()[:300]

        if not clean_text:
            clean_text = "বলো সোনা"

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_bytes = loop.run_until_complete(generate_natural_audio(clean_text))
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
            self.wfile.write(f"TTS Error: {str(e)}".encode('utf-8'))

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler):
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Server running on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
            
