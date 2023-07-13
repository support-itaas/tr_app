# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import fields, models, _, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    smsmkt_username = fields.Char(string='SMSMKT Registered Username')
    smsmkt_password = fields.Char(string='SMSMKT Password')
    smsmkt_sender = fields.Char(string='SMSMKT Sender Name')
    otp_expiry = fields.Float(string='OTP Expiry Time', default=2)

    android = fields.Char(string='ANDROID VERSION')
    ios = fields.Char(string='IOS VERSION')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            smsmkt_username=self.env['ir.config_parameter'].sudo().get_param('wizard_partner.smsmkt_username'),
            smsmkt_password=self.env['ir.config_parameter'].sudo().get_param('wizard_partner.smsmkt_password'),
            smsmkt_sender=self.env['ir.config_parameter'].sudo().get_param('wizard_partner.smsmkt_sender'),
            otp_expiry=self.env['ir.config_parameter'].sudo().get_param('wizard_partner.otp_expiry'),
            android=self.env['ir.config_parameter'].sudo().get_param('wizard_partner.android'),
            ios=self.env['ir.config_parameter'].sudo().get_param('wizard_partner.ios'),

        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('wizard_partner.smsmkt_username', self.smsmkt_username)
        self.env['ir.config_parameter'].sudo().set_param('wizard_partner.smsmkt_password', self.smsmkt_password)
        self.env['ir.config_parameter'].sudo().set_param('wizard_partner.smsmkt_sender', self.smsmkt_sender)
        self.env['ir.config_parameter'].sudo().set_param('wizard_partner.otp_expiry', self.otp_expiry)
        self.env['ir.config_parameter'].sudo().set_param('wizard_partner.android', self.android)
        self.env['ir.config_parameter'].sudo().set_param('wizard_partner.ios', self.ios)





