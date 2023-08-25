# -*- coding: utf-8 -*-

from openerp import fields, models, api, _
from datetime import datetime
from openerp.exceptions import UserError

class AccountReportGeneralLedger(models.TransientModel):
    _inherit = "account.report.general.ledger"

    department_id = fields.Many2one('hr.department', string="Department")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    operating_unit_id = fields.Many2one('operating.unit', string="Operating Unit")

    show_department = fields.Boolean(string='Show Department',defult=False)
    show_analytic_account = fields.Boolean(string='Show Analytic account',defult=False)
    show_operating_unit = fields.Boolean(string='Show Operating Unit',defult=False)

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        data['form'].update(self.read(['show_operating_unit'])[0])
        data['form'].update(self.read(['show_analytic_account'])[0])
        data['form'].update(self.read(['show_department'])[0])
        data['form'].update(self.read(['operating_unit_id'])[0])
        data['form'].update(self.read(['department_id'])[0])
        data['form'].update(self.read(['analytic_account_id'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date"))
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env.ref('account.action_report_general_ledger').with_context(landscape=True).report_action(records, data=data)
