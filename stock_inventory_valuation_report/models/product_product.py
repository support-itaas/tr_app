# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import pycompat
from odoo.tools.float_utils import float_round
from datetime import datetime
import operator as py_operator

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}

def strToDate(dt):
    return date(int(dt[0:4]), int(dt[5:7]), int(dt[8:10]))

class product_product(models.Model):
    _inherit = 'product.product'

    def _get_domain_locations(self):
        print ('-----NEW ---_get_domain_locations-------')
        if self.env.context.get('location', False):
            if isinstance(self.env.context['location'], pycompat.integer_types):
                location_ids = [self.env.context['location']]
            elif isinstance(self.env.context['location'], pycompat.string_types):
                domain = [('complete_name', 'ilike', self.env.context['location'])]
                if self.env.context.get('force_company', False):
                    domain += [('company_id', '=', self.env.context['force_company'])]
                location_ids = self.env['stock.location'].search(domain).ids
            else:
                location_ids = self.env.context['location']
            return self._get_domain_locations_new(location_ids, company_id=self.env.context.get('force_company', False),
                                                  compute_child=self.env.context.get('compute_child', True))

        else:
            return super(product_product,self)._get_domain_locations()
