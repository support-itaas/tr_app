# -*- coding: utf-8 -*-
# Copyright (C) 2019-present Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models, _


class Inventory(models.Model):
    _inherit = "stock.inventory"

    force_date = fields.Datetime(string='Force Date',
                                 states={'done': [('readonly', True)], 'cancel': [('readonly', True)], 'confirm': [('readonly', True)]}, )

    def post_inventory(self):
        # Here we are updating params for fetching the values from the function "update_available_quantity"
        params = self._context.get('params')
        if self.force_date:
            params.update({'force_date': self.force_date})

        print ('PARMA')
        print (params)
        return super(Inventory, self).post_inventory()


class InventoryLine(models.Model):
    _inherit = "stock.inventory.line"

    def _get_move_values(self, qty, location_id, location_dest_id, out):
        # Writing the values to the stock move
        res = super(InventoryLine, self)._get_move_values(qty, location_id, location_dest_id, out)

        res.update({
            'date': self.inventory_id.force_date or fields.datetime.today(),
        })
        # print ('InventoryLine')
        # print (res)
        return res
