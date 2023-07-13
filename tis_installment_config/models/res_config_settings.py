# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    min_amount_install = fields.Float(string='Minimum Amount')

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set(
            'res.config.settings', "min_amount_install", self.min_amount_install)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        min_amount_install = IrDefault.get(
            'res.config.settings', "min_amount_install")
        res.update(

            min_amount_install=min_amount_install,
        )
        return res
