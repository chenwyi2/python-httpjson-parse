import http_json_parse
import multiprocessing
import os


class Parser(multiprocessing.Process):
    def __init__(self, proxy, config):
        multiprocessing.Process.__init__(self)
        self.proxy = proxy
        self.file = config

    def run(self):
        # os.environ['http_proxy'] = self.proxy
        # write influxdb using http protocal
        # http_proxy may cause some problems
        os.environ['https_proxy'] = self.proxy
        http_json_parse.parser_start(self.file, '10.91.250.20', 'test')

if __name__ == '__main__':
    multiprocessing.freeze_support()

    internal_p = Parser('', 'http_json.conf')
    external_p = Parser('http://10.94.4.6:22222',
                        'public_json.conf')

    internal_p.start()
    external_p.start()