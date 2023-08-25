from odoo import fields, models, api, tools, _


class stock_location_route(models.Model):
    _inherit = 'stock.location.route'
    send_demo_route = fields.Boolean(string='Send Demo Route')
