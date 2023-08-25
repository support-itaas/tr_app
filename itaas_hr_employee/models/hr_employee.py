# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

GENDER_SELECTION = [('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other')]

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    requisition_month = fields.Integer(string="Month")


class material_purchase_requisition(models.Model):
    _inherit = "material.purchase.requisition"

    @api.multi
    def confirm_requisition(self):
        print('confirm_requisition')
        res = super(material_purchase_requisition, self).confirm_requisition()
        requisition_month = self.employee_id.requisition_month
        if requisition_month != 0 :
            date_to = datetime.today()
            date_form = date_to - relativedelta(months=requisition_month)
            print('date_to:',date_to)
            print('date_form:',date_form)
            print('res:',res)
            requisition_id = self.env['material.purchase.requisition'].search([('create_date','>=', str(date_form)),
                                                                           ('create_date','<=', str(date_to)),
                                                                           ('employee_id','=',self.employee_id.id)])
            if requisition_id:
                raise UserError('เดือนนี้คุณได้ทำการเบิกไปแล้ว')

            print('requisition_id:',requisition_id)
        return res