# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class OrderLimitSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    so_credit_limit = fields.Monetary(
        related='company_id.so_credit_limit',
        string="Default Credit Limit *", currency_field='currency_id')
    # currency_id = fields.Many2one(
    #    'res.currency',
    #    related='company_id.currency_id')


class Company(models.Model):
    _inherit = 'res.company'

    so_credit_limit = fields.Monetary(
        string='Default Credit Limit',
        default=1000,
        currency_field='currency_id',
        help="The default credit limit to applied to new customers created in the system. Zero value means 'No limit'")
