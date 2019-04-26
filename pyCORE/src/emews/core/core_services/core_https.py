"""
HTTPS Utility CoreService.

Adapted from the CORE HTTP Utility service.

Created on Apr 24, 2019
@author: Brian Ricks
"""
from core import CoreCommandError
from core.service import CoreService
from core.misc import utils


class HttpsService(CoreService):
    """Start an apache server (HTTPS support)."""

    name = "Serv_HTTPS"
    group = "eMews"
    configs = ("/etc/apache2/apache2.conf", "/etc/apache2/envvars", "httpd_start.sh",)
    dirs = ("/etc/apache2", "/var/run/apache2", "/var/log/apache2",
            "/run/lock", "/var/lock/apache2", "/var/run/apache2/ssl",
            "/var/run/apache2/ssl/cert", "/var/run/apache2/ssl/key",)
    startup = ("chown www-data /var/lock/apache2", "sh httpd_start.sh",)
    startindex = 50
    shutdown = ("apache2ctl stop",)
    validate = ("pidof apache2",)

    APACHEVER22, APACHEVER24 = (22, 24)

    @classmethod
    def generate_config(cls, node, filename):
        """Generate an apache2.conf configuration file."""
        if filename == cls.configs[0]:
            return cls.generateapache2conf(node, filename)
        elif filename == cls.configs[1]:
            return cls.generateenvvars(node, filename)
        elif filename == cls.configs[2]:
            return cls.generatekeygen(node, filename)
        else:
            return ""

    @classmethod
    def detectversionfromcmd(cls):
        """Detect the apache2 version using the 'a2query' command."""
        try:
            status, result = utils.cmd_output(['a2query', '-v'])
        except CoreCommandError:
            status = -1

        if status == 0 and result[:3] == '2.4':
            return cls.APACHEVER24

        return cls.APACHEVER22

    @classmethod
    def generateapache2conf(cls, node, filename):
        lockstr = {cls.APACHEVER22:
                       'LockFile ${APACHE_LOCK_DIR}/accept.lock\n',
                   cls.APACHEVER24:
                       'Mutex file:${APACHE_LOCK_DIR} default\n', }
        mpmstr = {cls.APACHEVER22: '', cls.APACHEVER24:
            'LoadModule mpm_worker_module /usr/lib/apache2/modules/mod_mpm_worker.so\n', }

        permstr = {cls.APACHEVER22:
                       '    Order allow,deny\n    Deny from all\n    Satisfy all\n',
                   cls.APACHEVER24:
                       '    Require all denied\n', }

        authstr = {cls.APACHEVER22:
                       'LoadModule authz_default_module /usr/lib/apache2/modules/mod_authz_default.so\n',
                   cls.APACHEVER24:
                       'LoadModule authz_core_module /usr/lib/apache2/modules/mod_authz_core.so\n', }

        permstr2 = {cls.APACHEVER22:
                        '\t\tOrder allow,deny\n\t\tallow from all\n',
                    cls.APACHEVER24:
                        '\t\tRequire all granted\n', }

        version = cls.detectversionfromcmd()
        cfg = "# apache2.conf generated by utility.py:HttpService\n"
        cfg += lockstr[version]
        cfg += """\
PidFile ${APACHE_PID_FILE}
Timeout 300
KeepAlive On
MaxKeepAliveRequests 100
KeepAliveTimeout 5
"""
        cfg += mpmstr[version]
        cfg += """\

<IfModule mpm_prefork_module>
    StartServers          5
    MinSpareServers       5
    MaxSpareServers      10
    MaxClients          150
    MaxRequestsPerChild   0
</IfModule>

<IfModule mpm_worker_module>
    StartServers          2
    MinSpareThreads      25
    MaxSpareThreads      75
    ThreadLimit          64
    ThreadsPerChild      25
    MaxClients          150
    MaxRequestsPerChild   0
</IfModule>

<IfModule mpm_event_module>
    StartServers          2
    MinSpareThreads      25
    MaxSpareThreads      75
    ThreadLimit          64
    ThreadsPerChild      25
    MaxClients          150
    MaxRequestsPerChild   0
</IfModule>

User ${APACHE_RUN_USER}
Group ${APACHE_RUN_GROUP}

AccessFileName .htaccess

<Files ~ "^\.ht">
"""
        cfg += permstr[version]
        cfg += """\
</Files>

DefaultType None

HostnameLookups Off

ErrorLog ${APACHE_LOG_DIR}/error.log
LogLevel warn

#Include mods-enabled/*.load
#Include mods-enabled/*.conf
LoadModule alias_module /usr/lib/apache2/modules/mod_alias.so
LoadModule auth_basic_module /usr/lib/apache2/modules/mod_auth_basic.so
"""
        cfg += authstr[version]
        cfg += """\
LoadModule authz_host_module /usr/lib/apache2/modules/mod_authz_host.so
LoadModule authz_user_module /usr/lib/apache2/modules/mod_authz_user.so
LoadModule autoindex_module /usr/lib/apache2/modules/mod_autoindex.so
LoadModule dir_module /usr/lib/apache2/modules/mod_dir.so
LoadModule env_module /usr/lib/apache2/modules/mod_env.so
LoadModule ssl_module /usr/lib/apache2/modules/mod_ssl.so

NameVirtualHost *:80
Listen 80
Listen 443

LogFormat "%v:%p %h %l %u %t \\"%r\\" %>s %O \\"%{Referer}i\\" \\"%{User-Agent}i\\"" vhost_combined
LogFormat "%h %l %u %t \\"%r\\" %>s %O \\"%{Referer}i\\" \\"%{User-Agent}i\\"" combined
LogFormat "%h %l %u %t \\"%r\\" %>s %O" common
LogFormat "%{Referer}i -> %U" referer
LogFormat "%{User-agent}i" agent

ServerTokens OS
ServerSignature On
TraceEnable Off

<VirtualHost *:80>
    ServerAdmin webmaster@cmu.sv.mews
    DocumentRoot /var/www/html
    <Directory />
        Options FollowSymLinks
        AllowOverride None
    </Directory>
    <Directory /var/www/html/>
        Options Indexes FollowSymLinks MultiViews
        AllowOverride None
"""
        cfg += permstr2[version]
        cfg += """\
    </Directory>
    ErrorLog ${APACHE_LOG_DIR}/error.log
    LogLevel warn
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
<VirtualHost *:443>
    SSLEngine on
    SSLVerifyClient none
    SSLCertificateFile "/var/run/apache2/ssl/cert/httpd.crt"
    SSLCertificateKeyFile "/var/run/apache2/ssl/key/httpd.key"
    ServerAdmin webmaster@cmu.sv.mews
    DocumentRoot /var/www/html
    <Directory />
        Options FollowSymLinks
        AllowOverride None
    </Directory>
    <Directory /var/www/html/>
        Options Indexes FollowSymLinks MultiViews
        AllowOverride None
"""
        cfg += permstr2[version]
        cfg += """\
        </Directory>
        ErrorLog ${APACHE_LOG_DIR}/error.log
        LogLevel warn
        CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
"""


        return cfg

    @classmethod
    def generateenvvars(cls, node, filename):
        return """\
# this file is used by apache2ctl - generated by utility.py:HttpService
# these settings come from a default Ubuntu apache2 installation
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
export APACHE_PID_FILE=/var/run/apache2.pid
export APACHE_RUN_DIR=/var/run/apache2
export APACHE_LOCK_DIR=/var/lock/apache2
export APACHE_LOG_DIR=/var/log/apache2
export LANG=C
export LANG
"""

    @classmethod
    def generatekeygen(cls, node, filename):
        """Generate a cert for Apache to use."""
        cert_cn = node.name
        for iface in node.netifs():
            if iface.name == "eth0":
                cert_cn = iface.addrlist[0].split("/")[0]  # m4d h4x
                break
        cfg = """\
#!/bin/sh
# We assume that the node only has one interface, so we assign to the cert the IP of this interface.
openssl req -new -x509 -days 365 -sha1 -newkey rsa:1024 -nodes -keyout /var/run/apache2/ssl/key/httpd.key -out /var/run/apache2/ssl/cert/httpd.crt -subj '/O=CORE/OU=CORE-emu/CN="""
        cfg += cert_cn
        cfg += """'
# Launch Apache here so we know that cert/key was generated first.
apache2ctl start
"""
        return cfg