# -*- coding: utf-8 -*-
import werkzeug
import json
import base64
from random import randint
import os
import datetime
import requests
import logging
_logger = logging.getLogger(__name__)

import odoo.http as http
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.http_routing.models.ir_http import slug

class SupportTicketController(http.controller):

    @http.route('/sav/acc/create', type="http", auth="public", website=True)
    def support_account_create(self, **kw):
        return http.request.render('ticket-module.account_create_page', {})

    @http.route('/sav/acc/create/process', type="http", auth="public", website=True)
    def support_account_create_process(self, **kw):
        """  Create no permission account"""

        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value

            # Create the new user
        new_user = request.env['res.users'].sudo().create(
            {'name': values['name'], 'login': values['login'], 'email': values['login'],
             'password': values['password']})

            # Remove all permissions
        new_user.groups_id = False

            # Add the user to the support group
        support_group = request.env['ir.model.data'].sudo().get_object('website_support', 'support_group')
        support_group.users = [(4, new_user.id)]

            # Also add them to the portal group so they can access the website
        #group_portal = request.env['ir.model.data'].sudo().get_object('base', 'group_portal')
        #group_portal.users = [(4, new_user.id)]

            # Automatically sign the new user in
        request.cr.commit()  # as authenticate will use its own cursor we need to commit the current transaction
        request.session.authenticate(request.env.cr.dbname, values['login'], values['password'])

            # Redirect them to the support page
        return werkzeug.utils.redirect("/home")

    @http.route('/support/ticket/submit', type="http", auth="public", website=True)
    def support_submit_ticket(self, **kw):
        """Let's public and registered user submit a support ticket"""
        person_name = ""
        if http.request.env.user.name != "Public user":
            person_name = http.request.env.user.name

        category_access = []
        for category_permission in http.request.env.user.groups_id:
            category_access.append(category_permission.id)

        ticket_categories = http.request.env['ticket.category'].sudo().search(
            ['|', ('access_group_ids', 'in', category_access), ('access_group_ids', '=', False)])

        setting_google_recaptcha_active = request.env['ir.default'].get('support.settings',
                                                                        'google_recaptcha_active')
        setting_google_captcha_client_key = request.env['ir.default'].get('support.settings',
                                                                          'google_captcha_client_key')
        setting_max_ticket_attachments = request.env['ir.default'].get('support.settings',
                                                                       'max_ticket_attachments')
        setting_max_ticket_attachment_filesize = request.env['ir.default'].get('support.settings',
                                                                               'max_ticket_attachment_filesize')
        setting_allow_website_priority_set = request.env['ir.default'].get('support.settings',
                                                                           'allow_website_priority_set')

        return http.request.render('ticket-module.support_submit_ticket', {'categories': ticket_categories,
                                                                             'priorities': http.request.env['ticket.priority'].sudo().search(
                                                                                 []), 'person_name': person_name,
                                                                             'email': http.request.env.user.email,
                                                                             'setting_max_ticket_attachments': setting_max_ticket_attachments,
                                                                             'setting_max_ticket_attachment_filesize': setting_max_ticket_attachment_filesize,
                                                                             'setting_google_recaptcha_active': setting_google_recaptcha_active,
                                                                             'setting_google_captcha_client_key': setting_google_captcha_client_key,
                                                                             #'setting_allow_website_priority_set': setting_allow_website_priority_set
                                                                        })
