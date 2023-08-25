# -*- coding: utf-8 -*-
# Copyright (C) 2016-2017  ITtaas.
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from dateutil.rrule import (YEARLY,MONTHLY,WEEKLY,DAILY)
from datetime import datetime, timedelta, date
from pytz import timezone
import pytz
import calendar

import uuid

from datetime import datetime, timedelta


class pos_session_advance(models.TransientModel):
    _name = 'pos.session.advance'


    def session_no_post_by_account(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['pos.session'].browse(active_ids):
            if record.is_ignore_account:
                record.is_ignore_account = False
        return {'type': 'ir.actions.act_window_close'}

    def session_cancel_by_account(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['pos.session'].browse(active_ids):
            # if record.is_ignore_account:
            #     record.is_ignore_account = False
            # record.update_opening_date()
            record.cancel_post_entry()
            # record.action_pos_session_validate_new()
        return {'type': 'ir.actions.act_window_close'}

    def session_validate_by_account(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []

        for record in self.env['pos.session'].browse(active_ids):
            if record.is_ignore_account:
                record.is_ignore_account = False
            record.update_opening_date()
            record.cancel_post_entry()
            record.action_pos_session_validate_new()
        return {'type': 'ir.actions.act_window_close'}

class pos_session(models.Model):
    _inherit = "pos.session"

    is_ignore_account = fields.Boolean(string='No Post to Account',default=True)

    def update_opening_date(self):
        for session_id in self:
            if session_id.order_ids:
                session_id.update({'start_at': session_id.order_ids[0].date_order})



    @api.multi
    def action_pos_session_validate_new(self):
        if not self.is_ignore_account:
            print ('8------')
            self._check_pos_session_balance()
            print ('9------')
            self.action_pos_session_close()
            print ('10------')

    def action_pos_session_close(self):
        if self.is_ignore_account:
            self.write({'state': 'closed'})
            return {
                'type': 'ir.actions.client',
                'name': 'Point of Sale Menu',
                'tag': 'reload',
                'params': {'menu_id': self.env.ref('point_of_sale.menu_point_root').id},
            }

        else:

            res = super(pos_session, self).action_pos_session_close()
            move_line_ids = self.mapped('statement_ids').mapped('move_line_ids')
            move_line_ids.update({'operating_unit_id': self.config_id.operating_branch_id.id})
            return res


    def cancel_post_entry(self):
        for session in self:
            order_ids = session.order_ids.filtered(lambda o: o.state not in ['invoiced'] and o.account_move)
            if order_ids:
                move_id = order_ids[0].account_move
                move_id.line_ids.remove_move_reconcile()
                move_id.button_cancel()
                move_id.unlink()

            order_ids.write({
                'state': 'paid',
            })

            for st in session.statement_ids:
                st.button_draft()
                st.line_ids.button_cancel_reconciliation()



















