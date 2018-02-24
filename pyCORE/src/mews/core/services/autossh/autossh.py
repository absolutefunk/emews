'''
Created on Feb 23, 2018

@author: Brian Ricks
'''

from pexpect import pxssh

class AutoSSH(object):
    '''
    classdocs
    '''

    def __init__(self, host, port):
        '''
        Constructor
        '''

        # class attributes
        self._s = pxssh.pxssh()

        self._host = host  # hostname of ssh server
        self._port = port  # port of ssh server

        self._username = None  # username for ssh login
        self._password = None  # password for ssh login

    def setusername(self, username):
        '''
        sets the username to use for ssh login
        '''
        self._username = username

    def setpassword(self, password):
        '''
        sets the password to use for ssh login
        '''
        self._password = password

    def connect(self):
        '''
        attempts to connect and login to the ssh server given with the
        credentials given
        '''
        try:
            self._s.login(self._host, self._username, port=self._port)
        except pxssh.ExceptionPxssh, e:
            print "[AutoSSH]: pxssh failed on login."
            print str(e)
            return False

        return True
