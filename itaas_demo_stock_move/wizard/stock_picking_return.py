# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt Ltd(<http://www.technaureus.com/>).

from odoo import models, fields, api


class ReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    def _create_returns(self):
        res = super(ReturnPicking, self)._create_returns()

        new_picking_id = self.env['stock.return.picking'].browse(res[0])
        if new_picking_id:
            new_picking_id.write({'demo_picking_id': self.picking_id.demo_sale_id.id})
        return res
