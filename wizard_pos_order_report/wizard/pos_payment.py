# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def _default_note(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            order = self.env['pos.order'].browse(active_id)
            return order.note
        return False

    note = fields.Char(string='Note', default=_default_note)

