# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import pytz

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        # print ('--ON CHANGE')
        res = super(purchase_order_line, self).onchange_product_id()
        fpos = self.order_id.fiscal_position_id
        for line in self:
            # print ('--CHECK PARTNER')
            # case1-not enable then do nothing (OK)
            # case2-enable and don't set on partner then get false (OK)
            # case3-enable and set partner tax and create directly on purchase
            # case4-enable and set partner tax and create from purchase request
            if self.env.user.company_id.is_vat_by_partner and line.order_id.partner_id:
                # print('---UPDAT TAX')
                if line.order_id.partner_id.supplier_taxes_id:
                    line.taxes_id = fpos.map_tax(line.order_id.partner_id.supplier_taxes_id)
                else:
                    line.taxes_id = False
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    # inter company rules
    @api.model
    def _prepare_sale_order_line_data(self, line, company, sale_id):
        # print('_prepare_sale_order_line_data res :', line, company, sale_id)
        res = super(PurchaseOrder, self)._prepare_sale_order_line_data(line, company, sale_id)
        # print('_prepare_sale_order_line_data res :', res)
        if sale_id:
            so = self.env["sale.order"].sudo(company.intercompany_user_id).browse(sale_id)
            fpos = so.fiscal_position_id or so.partner_id.property_account_position_id
            if so.company_id.is_vat_by_partner and so.partner_id and so.partner_id.taxes_id:
                taxes = fpos.map_tax(so.partner_id.taxes_id)
                res['tax_id'] = [(6, 0, taxes.ids)]

        return res

