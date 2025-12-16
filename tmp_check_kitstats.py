import urllib.request, re
html = urllib.request.urlopen('http://127.0.0.1:8000/').read().decode('utf-8')
m = re.search(r'<div id="kitStatsData".*?>([\s\S]*?)<\/div>', html)
if m:
    content = m.group(1).strip()
    print('---kitStatsData---')
    print(content)
    print('---end---')
else:
    print('kitStatsData not found')
