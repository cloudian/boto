import threading

class GMTUsage:
    """Collective usage for all requests since last get()"""

    # use GMTUsage.get() to get the values
    _SB = 0  # 1V
    _RC = 0  # 2v 
    _BS = 0  # 3V
    _BR = 0  # 4V
    _SO = 0  # 5V
    mutex = threading.Lock()

    @staticmethod
    def get():
        with GMTUsage.mutex:
            b = GMTUsage._SB
            c = GMTUsage._RC
            s = GMTUsage._BS
            r = GMTUsage._BR
            o = GMTUsage._SO
            GMTUsage._SB = GMTUsage._RC = GMTUsage._BS = GMTUsage._BR = GMTUsage._SO = 0
            return (b,c,s,r,o)

    @staticmethod
    def update(resp):
        usage = resp.getheader("x-gmt-usage", None)
        if not usage:
            return
        b,c,s,r,o = GMTUsage.parse_usage(usage)
        with GMTUsage.mutex:
            GMTUsage._SB += b
            GMTUsage._RC += c
            GMTUsage._BS += s
            GMTUsage._BR += r
            GMTUsage._SO += o
            # Add what we get from usage-2 if it exists
            usage2 = resp.getheader("x-gmt-usage-2", None)
            if not usage2:
                return
            b,c,s,r,o = GMTUsage.parse_usage(usage2)
            GMTUsage._SB += b
            GMTUsage._RC += c
            GMTUsage._BS += s
            GMTUsage._BR += r
            GMTUsage._SO += o

    @staticmethod
    def parse_usage(usage):
        ul = usage.split(',')
        if len(ul) != 5:
            return (0,0,0,0,0)  # best not to disturb stuff
        il = [int(num) for num in ul]
        return (il[0], il[1], il[2], il[3], il[4])
