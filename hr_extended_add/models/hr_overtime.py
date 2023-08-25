#-*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HrOvertime(models.Model):
    _inherit = 'hr.overtime'

    @api.multi
    def _track_subtype(self, init_values):
        print('init_values : ',init_values)
        print('elf.state : ',self.state)
        self.ensure_one()
        if 'state' in init_values and self.state == 'submit':
            return 'hr_extended_add.mt_overtime_submit'
        elif 'state' in init_values and self.state == 'approve':
            return 'hr_extended_add.mt_overtime_approve'

        return super(HrOvertime, self)._track_subtype(init_values)