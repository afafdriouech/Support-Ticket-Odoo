# -*- coding: utf-8 -*-
{
    'name': "ticket-module",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Afaf",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','resource','web','website'],

    # always loaded
    'data': [
        'views/views.xml',
        'views/templates.xml',
        'views/customer_reply_template.xml',
        'views/ticket_category_view.xml',
        'views/ticket_priority_view.xml',
        'views/ticket_state_view.xml',
        'views/users_view.xml',
        'views/support_ticket_view.xml',
        'views/website_templates.xml',
        'views/settings_view.xml',
        'views/menus.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/ir.module.category.csv',
        'demo/demo.xml',
        'demo/ticket.category.xml',
        'demo/ticket.priority.xml',
        'demo/ticket.state.xml',
        'demo/ticket_seq.xml',
    ],
    'installable': True,
    'application': True,
}