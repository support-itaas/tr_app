# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from operator import itemgetter
from io import BytesIO
from odoo import models, fields, api, _
from datetime import datetime,date
import xlwt
import base64
from odoo.exceptions import UserError
from odoo.tools import misc
from decimal import *
from dateutil.relativedelta import relativedelta
import calendar
import requests
import json
from datetime import date, timedelta

import math
import re


class ProductProduct(models.Model):
    _inherit = 'product.product'

    gift_voucher_amount = fields.Float(string='Gift Voucher Amount')