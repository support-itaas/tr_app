# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class account_move_line (models.Model):
    _inherit = 'account.move.line'

    def write(self, vals):
        res = super(account_move_line, self).write(vals)
        for aml in self:
            department_id = vals.get('department_id') or (aml.department_id and aml.department_id.id)
            analytic_account_id = vals.get('analytic_account_id') or (aml.analytic_account_id and aml.analytic_account_id.id)
            if department_id and not analytic_account_id:
                department_id = self.env['hr.department'].browse(department_id)
                if department_id and department_id.analytic_account_id:
                    aml.analytic_account_id = department_id.analytic_account_id

        return res