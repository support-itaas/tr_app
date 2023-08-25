from odoo import models, fields, api, _
from odoo.tools import float_is_zero
import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class PosSessionBom(models.Model):
    _name = 'pos.session.bom'

    session_id = fields.Many2one('pos.session',string='Session', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product')
    product_qty = fields.Float(string='Product Quantity')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure')

