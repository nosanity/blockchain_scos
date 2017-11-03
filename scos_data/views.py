# coding: utf-8

from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from scos_data.utils import InfluxQueryHandler


class Frontage(TemplateView):
    template_name = 'frontpage.html'


class NodeStatusView(TemplateView):
    template_name = 'node_status.html'

    def get_context_data(self, **kwargs):
        cd = super(NodeStatusView, self).get_context_data(**kwargs)
        data = InfluxQueryHandler().get_info()
        if not data:
            cd['error'] = _(u'Ошибка при получении данных')
        else:
            cd.update(data)
        return cd
