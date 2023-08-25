# -*- coding: utf-8 -*-

import time
import math

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class Stock_Move(models.Model):
    _inherit = 'stock.move'

    partner_id_sm = fields.Many2one('res.partner', string='Vender')
    compute_sm = fields.Boolean( string='compute sm',compute='_compute_vender', copy=True,defult=False)
    check_satus = fields.Boolean(string='check satus',defult=False)

    @api.multi
    def _compute_vender(self):
        # print ("------------------")
        objs = False
        objp = False
        value = {}
        for line in self.filtered(lambda r: r.check_satus == False):
            # print("------------------")
            source_document = line.origin
            print(source_document)

            if (source_document):
                objs = self.env['sale.order'].sudo().search(
                    [('name', '=', source_document)], limit=1)

                objp = self.env['purchase.order'].sudo().search(
                    [('name', '=', source_document)], limit=1)

                if objs:
                    value = {'check_satus': True,
                             'partner_id_sm': objs.partner_id.id,
                             }
                if objp:
                    value = {'check_satus': True,
                             'partner_id_sm': objp.partner_id.id,
                             }

                line.sudo().write(value)