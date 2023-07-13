# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

{
    'name': 'Wizard Payment Integrations',
    'version': '11.0.4.0',
    'category': 'Wizard Payment Integrations',
    'sequence': 1,
    'author': 'Technaureus Info Solutions Pvt. Ltd',
    'summary': 'Wizard Payment Integrations',
    'description': 'Wizard Payment Integrations',
    'website': 'https://www.technaureus.com/',
    'depends': ['website', 'account', 'wizard_project'],
    'demo': [
        'security/ir.model.access.csv',
        'data/payment_method.xml'

    ],
    'data': [
        'security/ir.model.access.csv',
        # 'data/payment_method.xml',
        'views/views.xml',
        'views/payment_method.xml',
        'views/wizard_payment_form.xml',
        'views/wizard_payment_installment_form.xml',
        'views/res_config_settings_view.xml',
        'views/payment_details.xml',
        'views/verification.xml',
        'views/success.xml',
        'views/failed.xml',
        'views/cancel.xml',
        'views/qr_code.xml',
        'views/scb_log.xml',
        'wizard/slip_wizard_view.xml',
        'wizard/inquiry_wizard_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
