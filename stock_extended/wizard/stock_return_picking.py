# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def _create_returns(self):
        new_picking, pick_type_id = super(StockReturnPicking, self)._create_returns()
        picking = self.env['stock.picking'].browse(new_picking)
        if picking.state == 'waiting':
            raise UserError(_('รายการสินค้าได้ถูกโอนย้ายแล้ว กรุณาตรวจสอบ'))
        return new_picking, pick_type_id