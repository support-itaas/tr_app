# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import uuid

from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools.misc import formatLang

from odoo.addons import decimal_precision as dp


class respartner_inherit(models.Model):
    _inherit = "res.partner"

    bigc_code = fields.Char(string='BigC Code')


##################### ค้นหาฟิวในช่อง Many2one // Form sale order partner_shipping_id #####################################
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        # print (len('ส้ม'))
        # print(operator)
        if operator not in ('ilike', 'like', '=', '=like', '=ilike'):
            return super(respartner_inherit, self).name_search(name, args, operator, limit)
        args = args or []
        # print(operator)
        domain = ['|', ('ref', operator, name), ('name', operator, name)]
        partners = self.env['res.partner'].search(['|',
                                                   ('name', operator, name),
                                                   ('bigc_code', operator, name)], limit=limit)
        print(partners.ids)
        if partners:
            domain = ['|'] + domain + [('id', 'in', partners.ids)]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()
#########################################################################################################
    # @api.multi
    # def name_get(self):
    #     res = []
    #     for analytic in self:
    #         name = analytic.name
    #         if analytic.code:
    #             name = '[' + analytic.code + '] ' + name
    #         if analytic.partner_id:
    #             name = name + ' - ' + analytic.partner_id.commercial_partner_id.name
    #         res.append((analytic.id, name))
    #     return res

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
    #     if operator not in ('ilike', 'like', '=', '=like', '=ilike'):
    #         return super(AccountAnalyticAccount, self).name_search(name, args, operator, limit)
    #     args = args or []
    #     domain = ['|', ('code', operator, name), ('name', operator, name)]
    #     partners = self.env['res.partner'].search([('name', operator, name)], limit=limit)
    #     if partners:
    #         domain = ['|'] + domain + [('partner_id', 'in', partners.ids)]
    #     recs = self.search(domain + args, limit=limit)
    #     return recs.name_get()
#########################################################################################################