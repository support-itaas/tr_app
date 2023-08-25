
from odoo import api, fields, models, _


class account_asset_asset11(models.Model):
    _inherit = "account.asset.asset"

    location_asset = fields.Many2one('assets.location', string='Location asset', track_visibility='onchange')