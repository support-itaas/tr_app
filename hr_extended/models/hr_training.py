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


class HrTraining(models.Model):
    _name = 'hr.employee.training'
    _description = 'HR Employee Training'

    name = fields.Many2one('course.training', string='Course', required=True)
    location = fields.Char("Institution")
    date = fields.Date("Date")    
    note = fields.Char("Course Description")
    type = fields.Selection(
        [('planned', 'Planned Training'),('new', 'New Request'),('others', 'Others')])
    employee_id = fields.Many2one('hr.employee', "Employee")
    cost = fields.Float(string='Cost')


class Course_Training(models.Model):
    _name = 'course.training'

    name = fields.Char("Course", required=True)
    description = fields.Text(string='Description')