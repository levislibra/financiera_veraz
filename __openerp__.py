# -*- coding: utf-8 -*-
{
    'name': "Veraz Informes comerciales",

    'summary': """
        Integracion con informes comerciales Veraz""",

    'description': """
        Integracion con informes comerciales Veraz
    """,

    'author': "Librasoft",
    'website': "http://www.libra-soft.com.ar",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'finance',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'financiera_prestamos'],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/extends_res_company.xml',
        'views/veraz_configuracion.xml',
        'views/veraz_informe.xml',
        'views/veraz_cda.xml',
        'views/extends_res_partner.xml',
        'views/veraz_cuestionario.xml',
        # 'wizards/veraz_pregunta_wizard.xml',
        # 'reports/veraz_reports.xml',
        # 'data/ir_cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}