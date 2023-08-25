# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


# ========================== this is for mixer schedule report =======================================

class vat_report(models.AbstractModel):
    _name = 'report.print_report_account.account_vat_report_id'

    @api.multi
    def render_html(self, data):
        self.model = self.env.context.get('active_model')
        company_id = self.env.user.company_id

        domain = []
        if data['form']['date_from'] and data['form']['date_to']:
            domain.append(('date_maturity', '>=', data['form']['date_from']))
            domain.append(('date_maturity', '<=', data['form']['date_to']))
        if data['form']['type']:
            domain.append(('wht_personal_company', '=', data['form']['type']))
            domain.append(('wht_type', '!=', False))
        elif not data['form']['type']:
            domain.append(('wht_type', '!=', False))
            domain.append(('wht_personal_company', '!=', False))

        docs = self.env['account.move.line'].search(domain)
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'date_from': data['form']['date_from'],
            'date_to': data['form']['date_to'],
            'docs': docs,
            'company_id': company_id,
        }

        return self.env['report'].render('print_report_account.account_vat_report_id', docargs)
# ============================================ End  =================================================