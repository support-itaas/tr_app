# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError




class account_asset_asset_advance(models.TransientModel):
    _name = "account.asset.asset.advance"
    _description = "Asset Advance Confirm Order"

    @api.multi
    def confirm_order(self):
        asset_ids = self.env['account.asset.asset'].browse(self._context.get('active_ids', []))

        for asset in asset_ids.filtered(lambda x: x.state == 'draft'):
            asset.validate()
        return {'type': 'ir.actions.act_window_close'}
