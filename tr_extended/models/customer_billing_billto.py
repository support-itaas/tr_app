# -*- coding: utf-8 -*-

import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

from odoo.exceptions import UserError, RedirectWarning, ValidationError

# class CustomerBilling(models.Model):
#     _inherit = "customer.billing"
#
#     @api.onchange('partner_id')
#     @api.depends('partner_id')
#     def onchange_partner_id(self):
#         super(CustomerBilling,self).onchange_partner_id()
#         print ('-BILL')
#         print (self.partner_id)
#
#         invoice_bill_to_ids = self.env['account.invoice'].search([('bill_to_id','=',self.partner_id.id)])
#         print(invoice_bill_to_ids)
