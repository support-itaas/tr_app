import time

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class GenPickingCoupon(models.TransientModel):
    _name = "project.task.gen.coupon"


    def gen_picking_coupon(self):
        print('contect',self._context)
        coupon_task = self.env['project.task'].browse(self._context.get('active_ids', []))
        if coupon_task:
            for obj_coupon_task in coupon_task:
                obj_coupon_task.coupon_id.create_picking()

        return {'type': 'ir.actions.act_window_close'}
