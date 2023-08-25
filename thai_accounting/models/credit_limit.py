# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://opensource.org/licenses/LGPL-3.0).
#
#This software and associated files (the "Software") may only be used (executed,
#modified, executed after modifications) if you have purchased a valid license
#from the authors, typically via Odoo Apps, or if you have received a written
#agreement from the authors of the Software (see the COPYRIGHT section below).
#
#You may develop Odoo modules that use the Software as a library (typically
#by depending on it, importing it and using its resources), but without copying
#any source code or material from the Software. You may distribute those
#modules under the license of your choice, provided that this license is
#compatible with the terms of the Odoo Proprietary License (For example:
#LGPL, MIT, or proprietary licenses similar to this one).
#
#It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#or modified copies of the Software.
#
#The above copyright notice and this permission notice must be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#DEALINGS IN THE SOFTWARE.
#
#########COPYRIGHT#####
# © 2017 Bernard K Too<bernard.too@optima.co.ke>

from openerp import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class customers_credit_limit(models.Model):
	_inherit=['res.partner']
	credit_limit = fields.Monetary('Credit Limit', default=0.0, help="Maximum amount to offer as credit to this customer")
        currency_id = fields.Many2one(related="company_id.currency_id", string="Currency")
        confirmed_orders_count = fields.Integer(compute='_count_confirmed_orders', string="Total Confirmed Orders:")
        confirmed_orders_total = fields.Monetary(compute='_count_confirmed_orders',default=0.00, string="Confirmed Orders Worth:")
        draft_invoices_count = fields.Integer(compute='_count_draft_invoices', string="Total Draft Invoices:")
        draft_invoices_total = fields.Float(compute='_count_draft_invoices', string="Draft Invoices Worth:")
        receivable_tax = fields.Monetary(compute='_get_receivable_tax', string="Receivable Tax")
        credit_limit_without_tax = fields.Boolean('Exclude Taxes in Credit Limit?', default=False,)

        @api.one
        def _get_receivable_tax(self):
           tax =0.0
	   tables, where_clause, where_params = self.env['account.move.line']._query_get()
	   where_params = [tuple(self.ids)] + where_params
           self.env.cr.execute("""SELECT l.move_id
                      FROM account_move_line l
                      LEFT JOIN account_account a ON (l.account_id=a.id)
		      LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                      WHERE act.type IN ('receivable')
                      AND l.partner_id IN %s
                      AND l.reconciled IS FALSE
                      """ + where_clause + """
                      """,
  	 	      where_params)
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

        @api.one
        def _count_confirmed_orders(self):
            confirmed_orders = self.env['sale.order'].search([('partner_id','=',self.id), ('state','in',['sale','done']),('invoice_status','=','to invoice')])
            self.confirmed_orders_count = len(confirmed_orders)
            self.confirmed_orders_total = sum(map(lambda x: x.amount_untaxed / x.pricelist_id.currency_id.rate if self.credit_limit_without_tax else x.amount_total / x.pricelist_id.currency_id.rate, confirmed_orders))

        @api.one
        def _count_draft_invoices(self):
            draft_invoices = self.env['account.invoice'].search([('partner_id','=',self.id), ('state','=','draft')])
            self.draft_invoices_count = len(draft_invoices)
            self.draft_invoices_total = sum(map(lambda x: x.amount_untaxed / x.currency_id.rate if self.credit_limit_without_tax else x.amount_total / x.currency_id.rate, draft_invoices))



	@api.multi
	def confirm_override(self):
	    order_id = self.env.context.get('order_id')
	    if order_id:
	       sale_order = self.env['sale.order'].browse([order_id])
	       if sale_order:
		  super(sale_credit_limit, sale_order).action_confirm()

class sale_credit_limit(models.Model):
	_inherit = ['sale.order']

	@api.multi
    	def action_confirm(self):
            without_tax = self.partner_id.credit_limit_without_tax
            net_receivable = ((self.partner_id.credit - self.partner_id.receivable_tax)
                             if (self.partner_id.receivable_tax < self.partner_id.credit) else self.partner_id.credit)
            confirmed_orders_total = 0.00
            draft_invoices_total = 0.00
            confirmed_orders = self.search([('partner_id','=',self.partner_id.id), ('state','in',['sale','done']),('invoice_status','=','to invoice')])
            draft_invoices = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id), ('state','=','draft')])
            if draft_invoices:
               draft_invoices_total = sum(map(lambda x: x.amount_untaxed / x.currency_id.rate if without_tax else x.amount_total / x.currency_id.rate, draft_invoices))
            if confirmed_orders:
               confirmed_orders_total = sum(map(lambda x: x.amount_untaxed / x.pricelist_id.currency_id.rate if without_tax else x.amount_total / x.pricelist_id.currency_id.rate, confirmed_orders))
            total_credit = ((self.amount_untaxed / self.pricelist_id.currency_id.rate if without_tax else self.amount_total / self.pricelist_id.currency_id.rate) +
                          (net_receivable if without_tax else self.partner_id.credit) + confirmed_orders_total + draft_invoices_total)

	    if self.partner_id.credit_limit < total_credit:
		extra = total_credit - self.partner_id.credit_limit
		view = self.env['ir.model.data'].xmlid_to_res_id('customers_credit_limit.climit_override_credit_form')
		ctx = self.env.context.copy()
		ctx.update({'order_id': self.id})
		return {
             		'name': _(u'Warning: Credit limit will be exceeded by {}{:,.2f}'.format(self.company_id.currency_id.symbol, extra)),
             		'type': 'ir.actions.act_window',
             		'view_type': 'form',
             		'view_mode': 'form',
             		'res_model': 'res.partner',
             		'views': [(view, 'form')],
             		'view_id': view,
             		'target': 'new',
             		'res_id': self.partner_id.id,
             		'context': ctx,
            	 }
	    super(sale_credit_limit, self).action_confirm()


