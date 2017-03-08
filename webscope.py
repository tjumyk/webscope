#!/usr/bin/env python2
import json
import logging
import multiprocessing
import os
import socket
from datetime import datetime
from Queue import Queue
from functools import wraps

import requests
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, Response, request, jsonify
from selenium import webdriver

app = Flask(__name__)

f_cfg = open('config.json')
config = json.load(f_cfg)
f_cfg.close()

sites = []
last_scan_time = None
screenshot_folder = 'static/screenshot'


def check_auth(username, password):
    for user in config['users']:
        if username == user['id'] and password == user['password']:
            return True
    return False


def authenticate():
    return Response(
        'You have no permission to access this URL', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def open_driver():
    driver = webdriver.PhantomJS(executable_path=config['phantomjs']['path'], service_args=[
        '--load-images=true',
        '--ignore-ssl-errors=true',
        '--web-security=false'])
    driver.set_page_load_timeout(config['timeout']['phantomjs_load'])
    return driver


def check_screenshot_folder():
    if not os.path.isdir(screenshot_folder):
        os.mkdir(screenshot_folder)
    for old_file in os.listdir(screenshot_folder):
        file_path = os.path.join(screenshot_folder, old_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)


def take_screenshot(url, file_path):
    driver = None
    try:
        driver = open_driver()
        screen_size = config['phantomjs']['screen']
        driver.set_window_size(int(screen_size['width']), int(screen_size['height']))
        driver.get(url)
        driver.get_screenshot_as_file(file_path)
        title = driver.execute_script('return document.title;')
        icon = driver.execute_script(
            "var l = document.querySelector('link[rel=\"shortcut icon\"]');if(!l){return null;}else{return l.href;}")
        return {
            "title": title,
            "icon": icon
        }
    except Exception as e:
        raise e
    finally:
        if driver is not None:
            driver.close()


def scan(host, port):
    s = socket.socket()
    s.settimeout(config['timeout']['socket_check'])
    success = False
    if s.connect_ex((host, port)) == 0:
        success = True
    s.close()
    return success


def worker(targets):
    while not targets.empty():
        protocol, host, port = targets.get()
        try:
            if scan(host, port):
                logging.info("[Scan] %s:%d" % (host, port))
                url = "%s://%s:%s" % (protocol, host, str(port))
                screenshot = "%s/%s-%s.png" % (screenshot_folder, host, str(port))
                data = take_screenshot(url, screenshot)
                # since webdriver does not provide status code, we have to make another request manually
                status_code = requests.head(url, timeout=config['timeout']['request_head'],
                                            allow_redirects=True).status_code
                sites.append({
                    "host": host,
                    "port": port,
                    "url": url,
                    "screenshot": "/" + screenshot,
                    "title": data['title'],
                    "icon": data['icon'],
                    "status_code": status_code
                })
        except Exception as e:
            print e
        finally:
            targets.task_done()


@app.route('/')
@requires_auth
def index():
    return app.send_static_file('index.html')


@app.route('/api/scan')
@requires_auth
def scan_all():
    global sites, last_scan_time
    check_screenshot_folder()
    targets = Queue()
    sites = []
    for server in config['scan']['servers']:
        host = server['host']
        for port_range in server['port_ranges']:
            protocol = 'http'
            if 'https' in port_range and port_range['https'] is True:
                protocol = 'https'
            port = port_range['low']
            stop = port_range['high']
            while port <= stop:
                targets.put((protocol, host, port))
                port += 1
    workers = multiprocessing.cpu_count()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for i in range(workers):
            executor.submit(worker, targets)
    last_scan_time = datetime.utcnow().isoformat()
    return "OK", 200


@app.route('/api/servers')
@requires_auth
def get_servers():
    server_dict = {}
    for site in list(sites):
        host_name = site['host']
        server_sites = server_dict.get(host_name)
        if server_sites is None:
            server_sites = []
            server_dict[host_name] = server_sites
        server_sites.append(site)
    servers = []
    for host_name in server_dict:
        server_sites = server_dict[host_name]
        server_sites = sorted(server_sites, key=lambda x: x['port'])
        servers.append({
            'host': host_name,
            'sites': server_sites
        })
    servers = sorted(servers, key=lambda x: x['host'])
    return jsonify(servers=servers, last_scan=last_scan_time)


if __name__ == '__main__':
    app.run(**config['app'])
