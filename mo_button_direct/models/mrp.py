# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.osv import expression
from openerp.tools import float_is_zero
from openerp.tools import float_compare, float_round
from openerp.tools.misc import formatLang
from openerp.exceptions import UserError, ValidationError
from datetime import datetime, date


import time
import math



class Mrp_Production(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def button_gen_line(self):
        print('button_gen_line')
        minute_qty = 0
        check_product = []
        check_product_all = []
        for line in self.labour_cost_ids:
            print('==============')
            if line.product_id.id   not in check_product:
                check_product.append(line.product_id.id)
                value = {'product_id': line.product_id.id,
                         'minute': line.minute_qty * line.product_qty,
                         'qty': line.product_qty,
                         }
                check_product_all.append(value)
            else:
                for i in check_product_all:
                    if i['product_id'] == line.product_id.id:
                        i['minute'] = i['minute'] + (line.minute_qty * line.product_qty)

            for check_product_one in check_product_all:
                print('check_product_one:',check_product_one)
                print('xxxxx:',check_product_one['minute'])
                move_raw_ids = self.move_raw_ids.filtered(lambda x: x.product_id.id == check_product_one['product_id'])
                print('move_raw_ids:',move_raw_ids)
                if move_raw_ids:
                    move_raw_ids.quantity_done = check_product_one['minute']

                elif not move_raw_ids:
                    values = {
                        'raw_material_production_id': line.mrp_id.id,
                        'product_id': line.product_id.id,
                        'name':line.product_id.name,
                        'product_uom' : line.product_id.uom_id.id,
                        'location_id': self.location_src_id.id,
                        'location_dest_id' :self.location_dest_id.id,
                        'product_uom_qty': 1,
                        'quantity_done': line.minute_qty,
                    }
                    self.move_raw_ids.create(values)

