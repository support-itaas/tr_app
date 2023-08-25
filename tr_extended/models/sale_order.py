# -*- coding: utf-8 -*-
from openerp import fields, api, models, _
from bahttext import bahttext
from openerp.exceptions import UserError
from datetime import datetime, date

class SaleOrderLine_inherit(models.Model):
    _inherit ="sale.order.line"

    @api.onchange('product_id')
    def product_id_change_name(self):
        print("onchange_product_id_name")
        for line in self:
            print(self.product_id.name)
            line.update({'name':self.product_id.name,})


