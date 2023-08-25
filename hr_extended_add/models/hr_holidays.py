#-*-coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class hr_holidays(models.Model):
    _inherit = "hr.holidays"

    number_of_days_temp = fields.Float(
        'Allocation', copy=False, readonly=True, digits=(16,3),
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help='Number of days of the leave request according to your working schedule.')

    @api.multi
    def action_approve(self):

        if not self.env.user.has_group('hr_extended_add.group_hr_leave_allocation'):
            if not (self.employee_id.parent_id.user_id.id == self.env.uid or self.employee_id.department_id.manager_id.user_id.id == self.env.uid):
                raise UserError(_("Only HR holidays can approve and manager or department manager"))

        return super(hr_holidays, self).action_approve()