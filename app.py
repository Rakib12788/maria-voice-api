from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import json
import re

# তোমার দেওয়া দুটি ElevenLabs API Key
API_KEYS = [
    "sk_78f12d0fd5f2d4c8067045d24e86c35a89e79211451bb3ec",
    "sk_76c7f6d8eb286bcce3419c017b88ece946b402d11b02af1e"
]

current_key_index = 0

def get_next_api_key():
    global current_key_index
    if not API_KEYS:
        return None
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    return key

def generate_elevenlabs_voice(text):
    # মারিয়ার জন্য কিউট ও মিষ্টি কণ্ঠের ভয়েস আইডি (Rachel)
    voice_id = "21m00Tcm4TlvDq8ikWAM" 
    
    for _ in range(len(API_KEYS)):
        api_key = get_next_api_key()
        if not api_key:
            raise Exception("API Key পাওয়া যায়নি!")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.35,      # ইমোশন ও এক্সপ্রেশন বাড়ানোর জন্য
                "similarity_boost": 0.8
            }
        }

        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            # কোটা শেষ হলে পরের কি-তে সুইচ করবে
            if e.code == 401 or e.code == 429:
                continue
            else:
                raise Exception(f"ElevenLabs Error: {e.reason}")
        except Exception as e:
            raise e

    raise Exception("সবগুলো API Key এর কোটা শেষ হয়ে গেছে!")

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
            audio_bytes = generate_elevenlabs_voice(clean_text)
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
