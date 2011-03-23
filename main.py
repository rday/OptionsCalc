import web
from mimerender import mimerender
import json
from Request import WebRequest
from Request import StockRequest
from Request import OptionsRequest

render_json = lambda **args: json.JSONEncoder().encode(args)

urls = (
    '/stock/(.*)', 'Stock',
    '/search/(.*)', 'Search',
    '/optionchain/(.*)', 'Options',
    '/(.*)', 'WebPage',
    )


app = web.application(urls, globals())
render = web.template.render('templates/')
webRequest = WebRequest()
stockRequest = StockRequest(webRequest)
optionsRequest = OptionsRequest(webRequest)

if __name__ == "__main__":
    app.run()

class WebPage:
    def GET(self, page):
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
