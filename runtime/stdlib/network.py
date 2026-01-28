import requests

class NetWrapper:
    def post(self, url, data):
        try:
            res = requests.post(url, json=data)
            return res.status_code
        except:
            return -1
            
    def get(self, url):
        try:
            res = requests.get(url)
            return res.text
        except:
            return ""

    def discord_webhook(self, url, message):
        return self.post(url, {"content": str(message)})
