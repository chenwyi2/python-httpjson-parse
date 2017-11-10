import json
'''
config file template:
measurement type instance host http_url user:password json_path interval
redis qps - 10.91.207.11 http://10.91.207.11:18080/topom/stats : proxy.stats.a708d3474813e994fbbb95f66fcee41b.stats.ops.qps 1
redis qps - 10.91.207.11 http://10.91.207.11:18080/topom/stats : ['proxy.stats.a708d3474813e994fbbb95f66fcee41b.stats.ops.qps','proxy.stats.cb2ad81497864016d25bb5e3babceac4.stats.ops.qps'] 1
'''


def read_config_file(file_path):
    try:
        f = open(file_path)
        monitor_point = []
        for line in f:
            if line[0] == '#':
                continue
            line = line.split(' ')
            conf = {'measurement': line[0],
                    'type': line[1],
                    'instance': line[2],
                    'host': line[3],
                    'url': line[4],
                    'username': line[5].split(':')[0],
                    'passwd': line[5].split(':')[1],
                    'json_path': eval(line[6]) if line[6][0] == '[' else [line[6]],
                    'interval': int(line[7])}

            monitor_point.append(conf)
        return monitor_point
    except Exception as e:
        print e
        return 0


f_p = 'http_json.conf'
print read_config_file(f_p)