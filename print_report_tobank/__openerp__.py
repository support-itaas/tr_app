# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name' : 'Report to Bank',
    'version' : '1.0',
    'price' : 'Free',
    'currency': 'THB',
    'category': 'Quotations',
    'summary' : 'Print Report to Bank',
    'description': """
                Print Report to Bank
Tags: 
Stock report
            """,
    'author' : 'ITAAS',
    'website' : 'www.itaas.co.th',
    'depends' : ['sale','base','account','purchase','hr_extended','hr_payroll','hr','report_xlsx'],
    'data' : [
        'report/report_reg.xml',
        'wizard/bank_hr_report_view.xml',
        'views/view_company_form.xml',
        'views/view_hr_employee_form.xml',
        'security/ir.model.access.csv',
    ],


    #'report/productvariant_report.xml'],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
