# -*- coding: utf-8 -*-
from openerp import fields, api, models, _
from bahttext import bahttext
from openerp.exceptions import UserError
from datetime import datetime, date

class Mrp_production_inherit(models.Model):
    _inherit ="mrp.production"
    # x.reserved_availability and
    def _get_move_raw_ids(self):
        move_raw_ids = self.move_raw_ids.filtered(lambda x: not x.is_done and x.product_id.categ_id.name == 'เคมี')
        val = {}
        item = []

        for move in move_raw_ids:
            print(move.product_id.name)
            for lot in move.active_move_line_ids:
                val = {
                        'product_name':move.product_id.name,
                        'product_uom_qty': move.product_uom_qty,
                        'product_uom': move.product_uom.name,
                        'product_qty': lot.qty_done,
                        'lot': lot.lot_id.name,
                       }
                item.append(val)

        return item