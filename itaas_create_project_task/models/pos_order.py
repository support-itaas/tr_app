
from odoo import models, fields, api
from datetime import datetime, date

class PosOrder(models.Model):
    _inherit = "pos.order"

    is_create_project_task = fields.Boolean(string='Create Project Task', default=False)

    def create_project_task(self, value):
        print("create_project_task")
        print("value :",value)
        qty_all = self.lines.mapped('qty')
        print('qty_all:',qty_all)
        for qty in qty_all:
            for qty_task in range(0,int(qty)):
                date_deadline = date.today()
                date_assign = datetime.today()
                value = ({
                    'project_id': self.branch_id.id,
                    'name': self.lines.product_id.name,
                    'order_id': self.id,
                    'company_id': self.company_id.id,
                    'partner_id': self.partner_id.id,
                    'plate_number_id': self.car_id.id,
                    'date_deadline': date_deadline,
                    'date_assign': date_assign,
                })

                task_id = self.env['project.task'].create(value)
                task_id.write({'state': 'done'})
                self.is_create_project_task = True
                print('create_project_task_id: ', task_id)

