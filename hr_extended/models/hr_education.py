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


class HrEducation(models.Model):
    _name = 'hr.employee.education'
    _description = 'HR Employee Education'

    name = fields.Char("Name of Institution", required=True)
    type = fields.Selection(
        [('university', 'University'), ('college', 'College'), ('school', 'School')])
    employee_id = fields.Many2one('hr.employee', "Employee")
    year = fields.Date("Year")
    grade = fields.Float("Grade")
    deegree = fields.Selection(
        [('none', 'No Education'), ('primary', 'Primary School'), ('secondary', 'Secondary School'),
         ('diploma', 'Diploma'), ('bachelor', 'Bachelor Degree'), ('masters', 'Masters Degree'), ('phd', 'PhD')])
    employee_id = fields.Many2one('hr.employee', "Employee")
