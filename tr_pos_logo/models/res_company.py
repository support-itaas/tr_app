# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning

class ResCompany(models.Model):
    _inherit = 'res.company'

    pos_logo = fields.Binary('POS Logo')
