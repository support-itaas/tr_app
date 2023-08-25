# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
import time
from odoo.exceptions import UserError

class res_partner_inherit(models.Model):
    _inherit = "res.partner"

    fax = fields.Char(string="Fax")
