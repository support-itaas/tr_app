# -*- coding: utf-8 -*-
"""
# License LGPL-3.0 or later (https://opensource.org/licenses/LGPL-3.0).
#
# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT section below).
#
# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
#########COPYRIGHT#####
# © 2016 Bernard K Too<bernard.too@optima.co.ke>
"""

from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_is_zero


class customers_credit_limit(models.Model):
    _inherit = ['res.partner']

    commercial_credit = fields.Monetary(related='commercial_partner_id.credit')
    credit_limit = fields.Monetary(
        'Credit Limit',
        default=lambda self: self.env.user.company_id.so_credit_limit,
        help="Maximum amount to offer as credit to this customer")
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Currency")
    confirmed_orders_count = fields.Integer(
        compute='_count_confirmed_orders',
        string="Total Confirmed Orders:")
    confirmed_orders_total = fields.Monetary(
        compute='_count_confirmed_orders',
        default=0.00,
        string="Confirmed Orders Worth:")
    so_draft_invoices_count = fields.Integer(
        compute='_count_draft_invoices',
        string="Total Draft Invoices:")
    so_draft_invoices_total = fields.Float(
        compute='_count_draft_invoices',
        string="Draft Invoices Worth:")
    receivable_tax = fields.Monetary(
        compute='_get_receivable_tax',
        string="Receivable Tax")
    credit_limit_without_tax = fields.Boolean(
        'Exclude Taxes in Credit Limit?', default=False,)
    so_overdue_invoices_count = fields.Integer(
        compute='_count_overdue_invoices',
        string="Overdue Invoices:")
    so_overdue_invoices_total = fields.Float(
        compute='_count_overdue_invoices',
        string="Overdue Invoices Worth:")
    overdue_invoice_ids = fields.Many2many(
        'account.invoice',
        compute="_count_overdue_invoices",
        string='Overdue Invoices',
        copy=False)

    def _commercial_fields(self):
        """first we declare commercial fields for delegation purpose."""
        return super(customers_credit_limit,
                     self)._commercial_fields() + ['overdue_invoice_ids',
                                                   'so_overdue_invoices_total',
                                                   'so_overdue_invoices_count',
                                                   'credit_limit_without_tax',
                                                   'receivable_tax',
                                                   'so_draft_invoices_total',
                                                   'so_draft_invoices_count',
                                                   'confirmed_orders_total',
                                                   'confirmed_orders_count']

    @api.one
    def _get_receivable_tax(self):
        tax = 0.0
        tables, where_clause, where_params = self.env['account.move.line']._query_get(
        )
        where_params = [tuple(self.ids)] + where_params
        self.env.cr.execute("""SELECT l.move_id
                      FROM account_move_line l
                      LEFT JOIN account_account a ON (l.account_id=a.id)
		      LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                      WHERE act.type IN ('receivable')
                      AND l.partner_id IN %s
                      AND l.reconciled IS FALSE """ + where_clause + """""", where_params)
        move_ids = self._cr.fetchall()
        if move_ids:
            self.env.cr.execute("""SELECT SUM(l.credit-l.debit)
                      FROM account_move_line l
                      LEFT JOIN account_account a ON (l.account_id=a.id)
		      LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                      WHERE act.type IN ('other')
                      AND l.partner_id IN %s
                      AND l.reconciled IS FALSE
                      AND l.product_id IS NULL
                      AND l.tax_line_id IS NOT NULL
                      AND l.move_id IN  %s
                      """ + where_clause + """
                      """,
                                (tuple(self.ids), tuple(move_ids),))
            tax = self._cr.fetchall()[0][0] if not None else 0
        self.receivable_tax = tax

    @api.multi
    def action_notify_manager(self):
        """This function opens a window to compose an email, with the notify-
        sales manger template message loaded by default."""
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                'customers_credit_limit', 'email_template_sales_manager')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'sale.order',
            'default_res_id': self.env.context.get('order_id'),
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.one
    def _count_confirmed_orders(self):
        ptnr = self.commercial_partner_id  # work with commercial partner
        cpy_currency_id = self.env.user.company_id.currency_id
        confirmed_orders = self.env['sale.order'].search(
            [('partner_id.commercial_partner_id', '=', ptnr.id), ('state', 'in', ['sale', 'done']),
             ('invoice_status', '=', 'to invoice')])
        self.confirmed_orders_count = len(confirmed_orders)
        self.confirmed_orders_total = sum(
            [(x.currency_id.compute(x.amount_untaxed, cpy_currency_id)
              if ptnr.credit_limit_without_tax
              else x.currency_id.compute(x.amount_total, cpy_currency_id))
             for x in confirmed_orders])

    @api.one
    def _count_draft_invoices(self):
        ptnr = self.commercial_partner_id  # work with commercial partner
        cpy_currency_id = self.env.user.company_id.currency_id
        draft_invoices = self.env['account.invoice'].search(
            [('partner_id.commercial_partner_id', '=', ptnr.id),
             ('state', '=', 'draft'), ('type', '=', 'out_invoice')])
        self.so_draft_invoices_count = len(draft_invoices)
        self.so_draft_invoices_total = sum(
            [(x.currency_id.compute(x.amount_untaxed, cpy_currency_id)
              if ptnr.credit_limit_without_tax
              else x.currency_id.compute(x.amount_total, cpy_currency_id))
             for x in draft_invoices])

    @api.one
    def _count_overdue_invoices(self):
        ptnr = self.commercial_partner_id  # work with commercial partner
        cpy_currency_id = self.env.user.company_id.currency_id
        overdue_invoices = self.env['account.invoice'].search(
            [
                ('partner_id.commercial_partner_id',
                 '=',
                 ptnr.id),
                ('state',
                 '=',
                 'open'),
                ('type',
                 '=',
                 'out_invoice'),
                ('date_due',
                 '<=',
                 fields.Date.to_string(
                     datetime.now() -
                     timedelta(
                         days=1)))])
        self.overdue_invoice_ids = overdue_invoices
        self.so_overdue_invoices_count = len(overdue_invoices)
        self.so_overdue_invoices_total = sum(
            [(x.currency_id.compute(x.amount_untaxed, cpy_currency_id)
              if ptnr.credit_limit_without_tax
              else x.currency_id.compute(x.amount_total, cpy_currency_id))
             for x in overdue_invoices])

    @api.multi
    def so_confirm_override(self):
        order_id = self.env.context.get('order_id')
        if order_id:
            sale_order = self.env['sale.order'].browse([order_id])
            if sale_order:
                super(sale_credit_limit, sale_order).action_confirm()


class sale_credit_limit(models.Model):
    _inherit = ['sale.order']

    so_overdue_invoices_count = fields.Integer(
        related='partner_id.so_overdue_invoices_count',
        help="The supplier has overdue bills",
        string="Overdue Invoices")
    overdue_invoice_ids = fields.Many2many(
        'account.invoice',
        related="partner_id.overdue_invoice_ids",
        string='Overdue Invoices',
        copy=False)
    credit_status = fields.Selection(
        [('within', 'Order Within Credit Limit'),
         ('out', 'Order Exceeds Credit Limit!'),
         ('none', 'Credit Limit Not Set'),
         ('na', 'Credit Limit Not Applicable')],
        string='Credit Limit Status',
        compute='_compute_credit_limit',
        store=True)

    @api.multi
    @api.depends('state', 'amount_untaxed', 'amount_tax',
                 'partner_id.credit_limit')
    def _compute_credit_limit(self):
        """This function will compute and populate the credit_status selection
        field based on the order amount, with or without tax."""
        precision = self.env['decimal.precision'].precision_get('Account')
        cpy = self.env.user.company_id
        for order in self:
            # work with commercial partner
            ptnr = order.partner_id.commercial_partner_id
            if order.state in ('sale', 'done', 'cancel'):
                order.credit_status = 'na'
                continue
            if float_is_zero(
                    ptnr.credit_limit,
                    precision_digits=precision):
                order.credit_status = 'none'
                continue
            without_tax = ptnr.credit_limit_without_tax
            net_receivable = (ptnr.credit) \
                - (ptnr.receivable_tax) if ptnr.receivable_tax \
                < ptnr.credit \
                else ptnr.credit
            confirmed_so_total = ptnr.confirmed_orders_total
            draft_invoices_total = ptnr.so_draft_invoices_total
            total_credit = (
                order.currency_id.compute(
                    order.amount_untaxed,
                    cpy.currency_id) if without_tax else order.currency_id.compute(
                        order.amount_total,
                        cpy.currency_id)) + (
                            net_receivable if without_tax else ptnr.credit) \
                + confirmed_so_total + draft_invoices_total
            if ptnr.credit_limit < total_credit:  # Limit exceeded
                order.credit_status = 'out'
            else:
                order.credit_status = 'within'

    @api.multi
    def action_view_overdue(self):
        """This function returns an action that display existing overdue
        customer invoices.

        When only one found, show the invoice immediately in form
        format.

        """
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]

        # override the context to get rid of the default filtering
        result['context'] = {
            'type': 'out_invoice',
            'default_order_id': self.id}

        if not self.overdue_invoice_ids:
            # Choose a default account journal in the same currency in case a
            # new invoice is created
            journal_domain = [
                ('type', '=', 'sale'),
                ('company_id', '=', self.company_id.id),
                ('currency_id', '=', self.currency_id.id),
            ]
            default_journal_id = self.env['account.journal'].search(
                journal_domain, limit=1)
            if default_journal_id:
                result['context']['default_journal_id'] = default_journal_id.id
        else:
            # Use the same account journal than a previous invoice
            result['context']['default_journal_id'] = self.overdue_invoice_ids[0].journal_id.id

        # choose the view_mode accordingly
        if len(self.overdue_invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + \
                str(self.overdue_invoice_ids.ids) + ")]"
        elif len(self.overdue_invoice_ids) == 1:
            res = self.env.ref('account.invoice_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.overdue_invoice_ids.id
        return result

    @api.multi
    def action_confirm(self):
        ptnr = self.partner_id.commercial_partner_id  # work with commercial partner
        without_tax = ptnr.credit_limit_without_tax
        cpy = self.env.user.company_id
        precision = self.env['decimal.precision'].precision_get('Account')
        net_receivable = (
            (ptnr.credit -
             ptnr.receivable_tax) if (
                ptnr.receivable_tax < ptnr.credit) else ptnr.credit)
        confirmed_orders_total = ptnr.confirmed_orders_total
        so_draft_invoices_total = ptnr.so_draft_invoices_total
        total_credit = (
            self.currency_id.compute(
                self.amount_untaxed,
                cpy.currency_id) if without_tax else self.currency_id.compute(
                    self.amount_total,
                    cpy.currency_id)) + (
                        net_receivable if without_tax else ptnr.credit) \
            + confirmed_orders_total + so_draft_invoices_total

        if not float_is_zero(
                ptnr.credit_limit,
                precision_digits=precision) and ptnr.credit_limit < total_credit:
            extra = total_credit - ptnr.credit_limit
            view = self.env['ir.model.data'].xmlid_to_res_id(
                'customers_credit_limit.climit_override_credit_form')
            ctx = self.env.context.copy()
            ctx.update({'order_id': self.id})
            return {
                'name': _(
                    u'Warning: Credit limit will be exceeded by {}{:,.2f}'.format(
                        self.company_id.currency_id.symbol,
                        extra)),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'res.partner',
                'views': [
                    (view,
                     'form')],
                'view_id': view,
                'target': 'new',
                'res_id': self.partner_id.id,
                'context': ctx,
            }
        super(sale_credit_limit, self).action_confirm()
