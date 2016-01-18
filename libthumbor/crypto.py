#!/usr/bin/python
# -*- coding: utf-8 -*-

# libthumbor - python extension to thumbor
# http://github.com/heynemann/libthumbor

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 Bernardo Heynemann heynemann@gmail.com

'''Encrypted URLs for thumbor encryption.'''

from __future__ import absolute_import

import base64
import hmac
import hashlib

from six import text_type, b, PY3

try:
    from Crypto.Cipher import AES
    PYCRYPTOFOUND = True
except ImportError:
    PYCRYPTOFOUND = False

from libthumbor.url import url_for, unsafe_url, plain_image_url


class CryptoURL(object):
    '''Class responsible for generating encrypted URLs for thumbor'''

    def __init__(self, key):
        '''
        Initializes the encryptor with the proper key
        :param key: secret key to use for hashing.
        :param thread_safe: if True (default) CryptoURL will not reuse the hmac instance on every generate call,
         instead a copy of the hmac object will be created. Consider setting this parameter to False when only one
         thread has access to the CryptoURL object at a time.
        '''
        if not PYCRYPTOFOUND:
            raise RuntimeError('pyCrypto could not be found,' +
                               ' please install it before using libthumbor')
        if isinstance(key, text_type):
            key = str(key)
        self.key = key
        self.computed_key = (key * 16)[:16]
        self.hmac = hmac.new(b(key), digestmod=hashlib.sha1)

    def generate_old(self, options):
        url = url_for(**options)

        pad = lambda s: s + (16 - len(s) % 16) * "{"
        cypher = AES.new(self.computed_key)
        encrypted = base64.urlsafe_b64encode(cypher.encrypt(pad(url)))

        if PY3:
            encrypted = encrypted.decode('ascii')
        return "/%s/%s" % (encrypted, options['image_url'])

    def generate_new(self, options):
        url = plain_image_url(**options)
        _hmac = self.hmac.copy()
        _hmac.update(text_type(url).encode('utf-8'))
        signature = base64.urlsafe_b64encode(_hmac.digest())

        if PY3:
            signature = signature.decode('ascii')
        return '/%s/%s' % (signature, url)

    def generate(self, **options):
        '''Generates an encrypted URL with the specified options'''

        if options.get('unsafe', False):
            return unsafe_url(**options)
        else:
            is_old = options.get('old', False)
            if is_old:
                return self.generate_old(options)
            return self.generate_new(options)

