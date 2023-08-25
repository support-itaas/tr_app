# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt.Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2019. All rights reserved.
from odoo import fields, models, api


class Hr_salary_rule_inherit(models.Model):
    _inherit = 'hr.salary.rule'

    check_active = fields.Boolean('Check Active')


class hr_department_inherit(models.Model):
    _inherit = 'hr.department'

    code = fields.Char('รหัสแผนก')


class hr_department_inherit(models.Model):
    _inherit = 'hr.job'


    code = fields.Char('รหัสแผนก')

