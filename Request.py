from time import time, sleep
import datetime
import re
import httplib, urllib
import threading
import redis
from hashlib import md5
from scipy.special import erf
from scipy.stats import norm
from scipy.misc import derivative
import random
from jsonDecode import decode

class WebRequest:
    """ I want one object controlling all web requests so we can monitor
        the amount of stuff that we do. This should be treated as a 
        singleton. Some services limit requests per second, so we need to
        control that. Also we are dealing with live stock information, so
        we want to be as up to date as possible. """
    def __init__(self):
        self.rlock = threading.RLock()
        self.redisConn = redis.Redis(host='localhost', port=6379, db=1)

    def request(self, server, url, useCache=True):
        """ Search for the requested data in local cache, and only
            make a web request if we have to.
            XXX: There is some stupid bug in Ubuntu's python-redis
            package where I couldn' set keys, make sure to manually
            install python-redis """
        responseData = None
        if useCache:
            responseData = self.redisConn.get(md5(url).hexdigest())
        if responseData is None:
            with self.rlock:
                try:
                    self.conn = httplib.HTTPConnection(server)
                    self.conn.request('GET', url)
                    response = self.conn.getresponse()
                    responseData = response.read()
                    """ XXX: Yahoo fucks us if we make requests too fast and we end
                        up caching wrong data. Maybe implement a throttle in this method
                        since we should get most of the tickers stored early """
                    if useCache:
                        self.redisConn.set(md5(url).hexdigest(), responseData)
                except Exception, e:
                    print e

        return responseData

class StockRequest:
    def __init__(self, webreq):
        self.webreq = webreq
        self.pattern = re.compile('\((.*?)\)')
        self.priceUrl = '/finance/getprices?q=%s&i=120&p=1d&f=d,c,v,o,h,l&df=cpct&auto=1'
        self.searchUrl = '/autoc.finance.yahoo.com/autoc?query=%s&callback=YAHOO.Finance.SymbolSuggest.ssCallback'

    def getTicker(self, ticker):
        """ Get a list of possible ticker matches from yahoo.
            Returns the JSON from the yahoo callback(no need to encode) """
        data = self.webreq.request('d.yimg.com', self.searchUrl % ticker.upper())
        print data
        match = re.findall('\(.*?\)', data)
        match = match[0][1:len(match)-2]
        return match

    def getPrice(self, ticker):
        """ Grab today's price information for the requested ticker
            Returns a dictionary """
        data = self.webreq.request('www.google.com', self.priceUrl % ticker.upper())
        volume = low = high = 0
        lastPrice = 0.0

        """ Parse our lists into useable values. Length checks help remove
            any badly formed rows """
        priceList = [x.split(',') for x in data.split('\n')[7:] if len(x) > 1]
        if len(priceList) > 0:
            volume = sum([float(x[5]) for x in priceList if len(x) >= 5])
            low = min([float(x[3]) for x in priceList if len(x) >= 3])
            high = max([float(x[2]) for x in priceList if len(x) >= 2])

            """ The most recent price will be in the last row """
            lastRow = priceList[-1]
            lastPrice = float(lastRow[1])
        return {'volume':volume,'low':low,'high':high,'last':lastPrice}


class OptionsRequest:
    """ For all methods
                S Stock price
                X Strike price
                R Rate of interest free return
                v Volatility
                t Time till expiration
    """
    def __init__(self, webreq):
        self.webreq = webreq
        self.cidUrl = '/finance?q=%s&output=json'
        self.optionUrl = '/finance/option_chain?cid=%s&output=json'

    def getCid(self, ticker):
        data = self.webreq.request('www.google.com', self.cidUrl % ticker.upper())
        match = re.findall('\"id\": \"(.*?)\"', data)
        if len(match) == 1: return match[0]

    def getChain(self, cid):
        data = self.webreq.request('www.google.com', self.optionUrl % cid, False)
        return decode(data)

    def IV(self, S, X, R, t, opt_price):
        delta1 = lambda B, R, y: (-math.log(B)+R+0.5*y)/y
        delta2 = lambda d, y: d - y

        err = 1.0
        while err - .001 > 0 and t < 2:
            try:
                d1 = delta1(X/S, R, math.sqrt(t))
                d2 = delta2(d1, math.sqrt(t))
                err = norm.cdf(d1) - (X/S)*math.exp(-R) * norm.cdf(d2) - (opt_price/S)
                t = t + .0001
            except:
                print "Died %f %f" % (t, err)
                return

        print err
        print opt_price

    def BS_call_price(self, S, X, R, v, t):
        d1 = (math.log(S/X) + R * t) / (v*(math.sqrt(t))) + 0.5*v*math.sqrt(t)
        d2 = d1 - (v * math.sqrt(t))
        c = S * norm.cdf(d1) - X * math.exp(-R*t) * norm.cdf(d2)
        return c

    def greeks(self, S, X, R, v, t):
        d1 = (math.log(S/X)+R*t) / (v*math.sqrt(t)) + 0.5*v*math.sqrt(t)
        d2 = d1 - (v*math.sqrt(t))

        delta = norm.cdf(d1)
        gamma = delta / (S * v * math.sqrt(t))
        theta = -(S*v*delta) / (2.0*math.sqrt(t)) - R*X*math.exp(-R*t)*norm.cdf(d2)

        return (delta, gamma, theta)
