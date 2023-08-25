# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Report HR',
    'version': '11.0.1.1',
    'price': 'Free',
    'currency': 'THB',
    'category': 'MISC',
    'summary': 'Report HR',
    'description': """
                Report:
                    - Creating Report
Tags:
Report
            """,
    'website': 'http://www.itaas.co.th/',
    'author': 'IT as a Service Co., Ltd.',
    'depends': ['hr','hr_payroll','hr_extended','hr_contract'],
    'data': [
        'views/hr_report_view.xml',
        'report/report_reg.xml',
        'report/sps1-10-1_report_period.xml',
        'report/sps1-10-2_report_period.xml',
        'report/pd1-1_report_period.xml',
        'report/pd1-2_report_period.xml',
        'report/pngd_1kor_report.xml',
        'report/pngd_1kor_nap_report.xml',
        'report/kortor20kor_report.xml',
        'report/sps1-02_report.xml',
        'report/sps1-03-2_report.xml',
        'report/sps6-09_report.xml',
        'report/pvd_report.xml',
        'report/sps1-03-1_report.xml',
        'report/teejai_50_report.xml',
        'report/teejai_50_all_report.xml',
        'wizard/attendance_report_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
