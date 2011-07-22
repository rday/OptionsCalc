import os
import sys
import site 

cwd = os.path.abspath(os.path.dirname(__file__))
sys.path.append(cwd)
sys.stdout = sys.stderr

import web
from mimerender import mimerender
import json

from Request import WebRequest
from Request import StockRequest
from Request import OptionsRequest

render_json = lambda **args: json.JSONEncoder().encode(args)

urls = (
    '/stocks/(.*)', 'Stock',
    '/search/(.*)', 'Search',
    '/optionchain/(.*)', 'Options',
    '/(.*)', 'WebPage'
    )


webRequest = WebRequest()
stockRequest = StockRequest(webRequest)
optionsRequest = OptionsRequest(webRequest)

app = web.application(urls, globals(), autoreload=False)
render = web.template.render(cwd + '/templates/')

class WebPage:
    def GET(self, page):
        if page == 'robots.txt':
            return render.robots()
        return render.index(page)

class Stock:
    @mimerender(
            default = 'json',
            json = render_json,
            )
    def GET(self, ticker):
        return stockRequest.getPrice(ticker)

class Search:
    def GET(self, ticker):
        return stockRequest.getTicker(ticker)

class Options:
    @mimerender(
            default = 'json',
            json = render_json,
            )
    def GET(self, ticker):
        cid = optionsRequest.getCid(ticker)
        (len, data) = optionsRequest.getChain(cid)
        return data

if __name__ == "__main__":
    app.run()
else:
    application = app.wsgifunc()
