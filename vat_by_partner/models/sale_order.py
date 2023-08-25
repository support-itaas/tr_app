# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _compute_tax_id(self):
        # print('_compute_tax_id ')
        super(sale_order_line, self)._compute_tax_id()
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            if self.env.user.company_id.is_vat_by_partner and line.order_id.partner_id:
                tax_id = fpos.map_tax(line.order_id.partner_id.taxes_id)
            else:
                # If company_id is set, always filter taxes by the company
                taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
                tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id) if fpos else taxes

            line.tax_id = tax_id