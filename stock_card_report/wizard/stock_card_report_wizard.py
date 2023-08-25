# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat
from odoo import models, fields, api, _
from datetime import datetime


class StockCardReportWizard(models.TransientModel):
    _name = 'stock.card.report.wizard'
    _description = 'Stock Card Report Wizard'

    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Period',
    )
    date_from = fields.Date(
        string='Start Date',
    )
    date_to = fields.Date(
        string='End Date',
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True,
    )
    product_ids = fields.Many2many(
        comodel_name='product.product',
        string='Products',
        required=False,
    )

    category_id = fields.Many2one('product.category',string='Category')

    company_id = fields.Many2one('res.company', string='Company')

    @api.model
    def default_get(self, fields):
        res = super(StockCardReportWizard, self).default_get(fields)
        curr_date = datetime.now()
        from_date = datetime(curr_date.year, 1, 1).date() or False
        to_date = datetime(curr_date.year, curr_date.month, curr_date.day).date() or False
        company_id = self.env.user.company_id.id
        # print (company_id)
        res.update({'date_from': str(from_date), 'date_to': str(to_date), 'company_id': company_id})
        return res

    @api.onchange('date_range_id')
    def _onchange_date_range_id(self):
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.multi
    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref(
            'stock_card_report.action_report_stock_card_report_html')
        vals = action.read()[0]
        context = vals.get('context', {})
        if isinstance(context, pycompat.string_types):
            context = safe_eval(context)
        model = self.env['report.stock.card.report']
        report = model.create(self._prepare_stock_card_report())
        context['active_id'] = report.id
        context['active_ids'] = report.ids
        vals['context'] = context
        return vals

    @api.multi
    def button_export_pdf(self):
        self.ensure_one()
        report_type = 'qweb-pdf'
        return self._export(report_type)

    @api.multi
    def button_export_xlsx(self):
        self.ensure_one()
        report_type = 'xlsx'
        return self._export(report_type)

    def _prepare_stock_card_report(self):
        self.ensure_one()
        # print ('---COMPANY--')
        # print (self.company_id)
        if self.product_ids:
            product_ids = self.product_ids
        elif self.category_id:
            product_ids = self.env['product.product'].search([('categ_id','=',self.category_id.id),('type','=','product')])
        else:
            product_ids = self.env['product.product'].search([('type','=','product')],limit=10)

        # print ('PRODUCT IDS')
        # print (product_ids)
        # print (len(product_ids))
        # print (xx)
        return {
            'date_from': self.date_from,
            'date_to': self.date_to or fields.Date.context_today(self),
            'product_ids': [(6, 0, product_ids.ids)],
            'location_id': self.location_id.id,
            'company_id': self.company_id.id,
        }

    def _export(self, report_type):
        model = self.env['report.stock.card.report']
        report = model.create(self._prepare_stock_card_report())
        return report.print_report(report_type)
