# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt.Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2019. All rights reserved.
from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_available_in_pos = fields.Boolean(string="Is Available In POS", default=False)

    @api.model
    def create_from_ui(self, partner):
        partner_id = super(ResPartner, self).create_from_ui(partner)
        self.browse(partner_id).write({'is_available_in_pos': True})
        return partner_id

