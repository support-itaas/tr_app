# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _


class res_users(models.Model):
    _inherit = 'res.users'

    default_sale_journal_id = fields.Many2one('account.journal',string="Default Sales Journal")
    default_purchase_journal_id = fields.Many2one('account.journal', string="Default Purchase Journal")

    image_signature = fields.Binary('Image')