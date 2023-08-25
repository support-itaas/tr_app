# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class hr_department (models.Model):
    _inherit = 'hr.department'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')


    # def update_analytic_account_all(self):
    #     session_ids = self.env['pos.session'].search([('start_at','>=','2021-01-01')],limit=10)
    #     for session in session_ids:
    #         # print (session.name)
    #         session.update_analytic_account()
    #
    # def update_analytic_account(self):
    #     for session in self:
    #         if session.config_id and session.config_id.branch_id and session.config_id.branch_id.analytic_account_id:
    #             analytic_account_id = session.config_id.branch_id.analytic_account_id
    #             order_ids = session.order_ids.filtered(lambda o: o.account_move)
    #             if order_ids and analytic_account_id:
    #                 account_move_id = order_ids[0].account_move
    #                 account_move_id.line_ids.update({'analytic_account_id': analytic_account_id.id})