# -*- coding: utf-8 -*-
# Copyright (C) 2019-present  Technaureus Info Solutions Pvt. Ltd.(<http://www.technaureus.com/>).
# 17/10/2020 - 11.0.3.9
# fix - def create_actual_revenue(self), due to system does not work on coupon order from difference company between tr and dealer
# 04/11/2020 - 11.0.4.0
# add is_create_task for each coupon (product) and manage to create task or not from this flag
#08/02/2021 - 11.0.5.0 by Jeng
# if product_id in not is_create_task will create deadline = redeem
# create button deadline for deadline != redeem
#11.0.6.4 - 18/07/2021 - update back from TIS
#11.0.6.5 - 18/07/2021 - update ITAAS Function (expire schedule, notification, claim coupon)
#11.0.6.6 - 10/08/2021 - add account payable to claim coupon
{
    'name': 'Wizard Coupon',
    'version': '11.0.6.7',
    'summary': 'Wizard Coupon',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'description': "Wizard Coupon",
    'category': 'Coupons',
    'website': 'http://www.technaureus.com',
    'depends': ['sale', 'pos_combo_product', 'portal', 'wizard_partner', 'wizard_project', 'account_cancel','base'],
    'data': [
        'security/ir.model.access.csv',
        'data/wizard_coupon.xml',
        'data/expire_coupon_scheduler.xml',
        'data/redeem_coupon_scheduler.xml',
        'data/coupon_data.xml',
        'data/coupon_journal_data.xml',
        'data/car_settings_data.xml',
        'views/wizard_coupon_view.xml',
        'views/product_view.xml',
        'views/res_partner_views.xml',
        'views/car_settings_views.xml',
        'views/project_views.xml',
        'views/response_template.xml',
        'views/account_journal_view.xml',
        'wizard/wizard_customer_transfer_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
