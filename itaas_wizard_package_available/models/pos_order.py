# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
import datetime
from datetime import date, timedelta

from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def create(self, values):
        lines = values.get('lines')
        branch_id = values.get('branch_id')
        for line in lines:
            pdt = self.env['product.product'].search([('id', '=', line[2]['product_id'])])
            if pdt.is_limit_branch and pdt.available_branch and branch_id not in pdt.available_branch.ids:
                raise UserError(_('This package has limited order for specific branch '))
            elif pdt.is_limit_branch and pdt.maximum_order_branch:
                self.env.cr.execute(
                    'SELECT sum(pol.qty) FROM pos_order_line pol '
                    'join pos_order pos on (pol.order_id=pos.id) WHERE pol.product_id = %s and pos.branch_id = %s',
                    (line[2]['product_id'],)+(branch_id,))
                res_new = self.env.cr.dictfetchall()
                if res_new[0]['sum'] + line[2]['qty'] > pdt.maximum_order_branch:
                    raise UserError(_('This package has limited order maximum per branch '))

        res = super(PosOrder, self).create(values)
        return res

    @api.multi
    def place_order(self, partner_id=None, branch_id=None, use_wallet=False, order_line_data=[],order=None):
        print ('PLACE ORDER--')
        if order_line_data:
            # is_limit = False
            for line in order_line_data:
                pdt = self.env['product.product'].search([('id', '=', line['product_id'])])
                if pdt.is_limit_branch and pdt.available_branch and branch_id not in pdt.available_branch.ids:
                    raise UserError(_('This package has limited order for specific branch '))
                elif pdt.is_limit_branch and pdt.maximum_order_branch:
                    self.env.cr.execute(
                        'SELECT sum(pol.qty) FROM pos_order_line pol '
                        'join pos_order pos on (pol.order_id=pos.id) WHERE pol.product_id = %s and pos.branch_id = %s',
                        (line['product_id'],)+(branch_id,))
                    res_new = self.env.cr.dictfetchall()
                    if res_new[0]['sum'] + line['qty'] > pdt.maximum_order_branch:
                        raise UserError(_('This package has limited order maximum per branch '))

            result = super(PosOrder, self).place_order(partner_id, branch_id, use_wallet, order_line_data, order)
            return result
        else:
            super(PosOrder, self).place_order(partner_id,branch_id,use_wallet,order_line_data,order)


