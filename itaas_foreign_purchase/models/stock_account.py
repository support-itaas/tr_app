# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def _get_price_unit(self):
        if self.picking_id:
            if self.picking_id.currency_id != self.company_id.currency_id and self.picking_id.exchange_rate:
                context = self._context.copy()
                context['exchange_params'] = {'it_currency_rate': self.picking_id.exchange_rate}
                self.env.context = context
        return super(StockMove, self)._get_price_unit()
