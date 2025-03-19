import json
from flask import render_template

from app.web import web
from helper.auth import check_login
from helper.endpoint import check_page_permission

@web.route('/admin/announcement')
@check_login
@check_page_permission('announcement/create')
def page_admin_announcement():
    with open('announcement.json') as f:
        announcement = json.load(f)
    return render_template('admin/announcement.html', title = "Announcement Settings", announcement = announcement, hide_announcement = True)