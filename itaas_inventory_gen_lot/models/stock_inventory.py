# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions(<http://www.technaureus.com/>).

from odoo import models, fields, api ,_
from odoo.exceptions import UserError


class stock_inventory_line(models.Model):
    _inherit = "stock.inventory"

    def gen_lot_from_stock(self):
        for line in self.line_ids:
            if not line.prod_lot_id and line.theoretical_qty > 0:
                qty_temp = line.theoretical_qty
                val = {
                    'name':'07/07/2021@TR',
                    'product_id':line.product_id.id,
                }
                existing_lot_id = self.env['stock.production.lot'].search([('name','=','07/07/2021@TR'),('product_id','=',line.product_id.id)],limit=1)
                if existing_lot_id:
                    lot_id = existing_lot_id
                else:
                    lot_id = self.env['stock.production.lot'].create(val)

                line.prod_lot_id = lot_id
                line.product_qty = qty_temp

    def _get_inventory_lines_values(self):
        res = super(stock_inventory_line,self)._get_inventory_lines_values()
        count = 0
        actual_value = []
        for line in res:
            if self.env['product.product'].browse(line['product_id']).type != 'product':
                count+=1
                continue
            elif line['product_qty'] < 0:
                count += 1
                continue
            else:
                actual_value.append(line)
        print ('RETRUN VALUE')
        print (res)
        print (len(res))
        print (actual_value)
        print (len(actual_value))
        print ('COUNT',count)
        return actual_value


