# WebScope 

![logo](static/image/logo-128.png)

This is a tiny web server that has the following capabilities:
  
1. Scan given port ranges on given host addresses to detect all the web servers 
2. Take a screenshot of the homepage of each website
3. Show the list of all these servers along with their screenshots
4. Provide a basic HTTP authentication to secure itself

This is useful especially in an internal network where many small websites are deployed at different ports under a single host address and you do not want to remember all these ports (and addresses).   

## Installation

1. Python packages

    ```bash
    (setup virtualenv if you want)
    pip install -r requirements.txt
    ```

2. PhantomJS

   Download/Install a suitable executable of [PhantomJS](http://phantomjs.org/) for your platform

## Configurations
  
  Edit `config.json` to set 
  - server settings of itself
  - phantomJS path and settings
  - scan timeout
  - hostnames and port ranges to scan
  - server authentication


