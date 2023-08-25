# -*- coding: utf-8 -*-
# Copyright (C) 2019-Today  Technaureus Info Solutions Pvt Ltd.(<http://technaureus.com/>).
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_branch = fields.Boolean(string="Is a Branch", default=False)
