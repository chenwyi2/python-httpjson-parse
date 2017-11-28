import urllib2
import json
import time
import influxdb
import threading
import base64


def read_config_file(config_file_path):
    try:
        f = open(config_file_path)
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
        print 'read_config_file' + str(e)
        return []


def get_json(stats_url, user, passwd):
    """
    GET JSON from HTTP using urllib2
    Using Add base64 header to handle Basic Auth or secret key provided by cloud
    If url is available return the dict transform from json
    else return False
    :param passwd:      http auth user
    :param user:        http auth passwd
    :param stats_url:   http url
    """
    try:
        # replace '$(date +%Y%m%d)' in url with today's date formatted 'YYYYmmdd'
        stats_url = stats_url.replace(r'$(date+%Y%m%d)', str(time.strftime("%Y%m%d", time.localtime())))
        # get json
        request = urllib2.Request(stats_url)
        if user != '':

            if user == 'key':
                request.add_header("Authorization", "key=%s" % passwd)
                # if user == key, use auth secret key provided by cloud
            else:
                base64string = base64.b64encode('%s:%s' % (user, passwd))
                request.add_header("Authorization", "Basic %s" % base64string)
                # else use BASIC AUTH (username and Base64 password)

        r = urllib2.urlopen(request).read()
        return_json = json.loads(r)
        return return_json
    except Exception as e:
        print 'get json' + str(e)
        return None


"""
GET value functions
GET value from dict
args: dict r_j, list request_json_path
If value is available return value
else return error_code
"""


def get_json_value(origin_json, request_json_path):
    try:
        json_parse_result = 0
        for request_path in request_json_path:
            tmp_json = origin_json
            path = request_path.split('.')
            # compatible with lists in json like {"a":[{"b":2},{"c":3}]}
            # config file json_path should be like a.0.b
            for j in path:
                j = int(j) if j.isdigit() and type(tmp_json) == list else j
                tmp_json = tmp_json[j]
            json_parse_result += tmp_json
        return float(json_parse_result)
    except Exception as e:
        print 'get_json_value' + str(e)
        return error_code

"""
END GET value functions
"""


def ini_influxdb(host, database):
    """
    Initial influxdb client
    """
    try:
        client = influxdb.InfluxDBClient(host, '8086', '', '', database)
        return client
    except Exception as e:
        print 'ini_influxdb' + str(e)
        return False


def write_point(client, result, monitor_point):
    """
    Write Point to influxdb
    Build the json_body and write the point to influxdb
    time is generated by influxdb
    :param client:                  influxdb client
    :param result:                  value get from json
    :param monitor_point:           monitor_point dict
    :return:                        client
    """
    try:
        json_body = [
            {
                "measurement": monitor_point['measurement'],
                "tags": {
                    "type": monitor_point['type'],
                    "host": monitor_point['host'],
                    "type_instance": monitor_point['instance']
                },
                # "time": c_time,
                "fields": {
                    "value": result
                }
            }
        ]
        # print json_body  # DEBUG
        client.write_points(json_body)
        return client
    except Exception as e:
        print 'write_point' + str(e)
        return client


def run(client, get_func, monitor_point):
    """
    :param client:          influxdb client
    :param get_func:        get value function
    :param monitor_point:   monitor_point dict
                            {'measurement': line[0],
                            'type': line[1],
                            'instance': line[2],
                            'host': line[3],
                            'url': line[4],
                            'username': line[5].split(':')[0],
                            'passwd': line[5].split(':')[1],
                            'json_path': eval(line[6]) if line[6][0] == '[' else [line[6]],
                            'interval': int(line[7])}
    """
    while True:
        r_json = get_json(monitor_point['url'],
                          monitor_point['username'],
                          monitor_point['passwd'])
        if r_json:
            result = get_func(r_json, monitor_point['json_path'])
        else:
            print r_json
            result = error_code
        # DEBUG
        # print str(time.time()) + ' ' + monitor_point['type'] + ' ' + str(monitor_point['interval']) + ' ' + str(result)
        write_point(client,
                    result,
                    monitor_point)
        time.sleep(monitor_point['interval'])


def parser_start(file_path, influxdb_host, influxdb_database):
    global error_code
    error_code = float(-1)
    c = ini_influxdb(influxdb_host, influxdb_database)
    t = []
    monitor_points = read_config_file(file_path)
    for i in monitor_points:
        thread = threading.Thread(target=run,
                                  args=(c,
                                        get_json_value,
                                        i))
        t.append(thread)

    for i in t:
        i.setDaemon(True)
        i.start()

    for i in t:
        i.join()

if __name__ == '__main__':
    parser_start('http_json.conf', '10.91.250.20', 'test')
