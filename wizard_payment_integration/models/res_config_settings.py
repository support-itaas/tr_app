# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    gbp_public_key = fields.Char(string='Public Key')
    gbp_secret_key = fields.Char(string='Secret Key')
    gbp_token = fields.Char(string='Token')

    scb_api_key = fields.Char(string='Api Key')
    scb_api_secret = fields.Char(string='Api Secret')
    biller_id = fields.Char(string='Biller ID')

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        IrDefault = self.env['ir.default'].sudo()
        IrDefault.set(
            'res.config.settings', "gbp_public_key", self.gbp_public_key)
        IrDefault.set(
            'res.config.settings', "gbp_secret_key", self.gbp_secret_key)
        IrDefault.set(
            'res.config.settings', "gbp_token", self.gbp_token)
        IrDefault.set(
            'res.config.settings', "scb_api_key", self.scb_api_key)
        IrDefault.set(
            'res.config.settings', "scb_api_secret", self.scb_api_secret)
        IrDefault.set(
            'res.config.settings', "biller_id", self.biller_id)

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        IrDefault = self.env['ir.default'].sudo()
        gbp_public_key = IrDefault.get(
            'res.config.settings', "gbp_public_key")
        gbp_secret_key = IrDefault.get(
            'res.config.settings', "gbp_secret_key")
        gbp_token = IrDefault.get(
            'res.config.settings', "gbp_token")
        scb_api_key = IrDefault.get(
            'res.config.settings', "scb_api_key")
        scb_api_secret = IrDefault.get(
            'res.config.settings', "scb_api_secret")
        biller_id = IrDefault.get(
            'res.config.settings', "biller_id")
        res.update(
            gbp_public_key=gbp_public_key,
            gbp_secret_key=gbp_secret_key,
            gbp_token=gbp_token,
            scb_api_key=scb_api_key,
            scb_api_secret=scb_api_secret,
            biller_id=biller_id,
        )
        return res
