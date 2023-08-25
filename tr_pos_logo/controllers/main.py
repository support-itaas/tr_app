# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).


from odoo import http
import babel.messages.pofile
import base64
import datetime
import functools
import glob
import hashlib
import imghdr
import io
import itertools
import jinja2
import json
import logging
import operator
import os
import re
import sys
import tempfile
import time
import zlib

import werkzeug
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from collections import OrderedDict
from werkzeug.urls import url_decode, iri_to_uri
from xml.etree import ElementTree
import unicodedata


import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo.modules import get_resource_path
from odoo.tools import crop_image, topological_sort, html_escape, pycompat
from odoo.tools.translate import _
from odoo.tools.misc import str2bool, xlwt, file_open
from odoo.tools.safe_eval import safe_eval
from odoo import http
from odoo.http import content_disposition, dispatch_rpc, request, \
    serialize_exception as _serialize_exception, Response
from odoo.exceptions import AccessError, UserError
from odoo.models import check_method_name
from odoo.service import db
db_list = http.db_list
db_monodb = http.db_monodb


class Binary(http.Controller):

    @http.route([
        '/web/binary/pos_company_logo',
    ], type='http', auth="none", cors="*")
    def pos_company_logo(self, dbname=None, **kw):
        imgname = 'logo'
        imgext = '.png'
        placeholder = functools.partial(get_resource_path, 'web', 'static', 'src', 'img')
        uid = None
        if request.session.db:
            dbname = request.session.db
            uid = request.session.uid
        elif dbname is None:
            dbname = db_monodb()

        if not uid:
            uid = odoo.SUPERUSER_ID

        if not dbname:
            response = http.send_file(placeholder(imgname + imgext))
        else:
            try:
                # create an empty registry
                registry = odoo.modules.registry.Registry(dbname)
                with registry.cursor() as cr:
                    company = int(kw['company']) if kw and kw.get('company') else False
                    if company:
                        cr.execute("""SELECT pos_logo, write_date
                                            FROM res_company
                                           WHERE id = %s
                                       """, (company,))
                    else:
                        cr.execute("""SELECT c.pos_logo, c.write_date
                                            FROM res_users u
                                       LEFT JOIN res_company c
                                              ON c.id = u.company_id
                                           WHERE u.id = %s
                                       """, (uid,))
                    row = cr.fetchone()
                    if row and row[0]:
                        image_base64 = base64.b64decode(row[0])
                        image_data = io.BytesIO(image_base64)
                        imgext = '.' + (imghdr.what(None, h=image_base64) or 'png')
                        response = http.send_file(image_data, filename=imgname + imgext, mtime=row[1])
                    else:
                        response = http.send_file(placeholder('nologo.png'))
            except Exception:
                response = http.send_file(placeholder(imgname + imgext))

        return response
