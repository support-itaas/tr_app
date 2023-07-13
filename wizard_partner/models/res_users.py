# -*- coding: utf-8 -*-
# Copyright (C) 2020-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).

from odoo import fields, models, api, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    smsmkt_username = fields.Char(string='SMSMKT Registered Username')
    smsmkt_password = fields.Char(string='SMSMKT Password')
    smsmkt_sender = fields.Char(string='SMSMKT Sender Name')
