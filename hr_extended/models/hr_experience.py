# -*- coding:utf-8 -*-
#
#
#    Copyright (C) 2011,2013 Michael Telahun Makonnen <mmakonnen@gmail.com>.
#    All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

from odoo import models, fields


class HrExperience(models.Model):
    _name = 'hr.employee.experience'
    _description = 'HR Employee Experience'

    name = fields.Char("Name of Company", required=True)
    type = fields.Char("Tyoe of Business")
    date_start = fields.Date("Date Start")
    position = fields.Char("Last Position")
    salary = fields.Integer("Last Salary")
    employee_id = fields.Many2one('hr.employee', "Employee")
