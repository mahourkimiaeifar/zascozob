# -*- coding: utf-8 -*-
import jdatetime
from django import template
from django.utils import timezone

register = template.Library()
FA = str.maketrans('0123456789', '\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9')


@register.filter(name='jdate')
def jdate(value, arg='%Y/%m/%d'):
    if not value:
        return ''
    try:
        value = timezone.localtime(value)
    except Exception:
        pass
    try:
        jd = jdatetime.datetime.fromgregorian(datetime=value)
        return jd.strftime(arg).translate(FA)
    except Exception:
        return value.strftime(arg).translate(FA)


@register.filter(name='jdatetime_full')
def jdatetime_full(value):
    """تاریخ و ساعت کامل جلالی"""
    if not value:
        return ''
    try:
        value = timezone.localtime(value)
    except Exception:
        pass
    try:
        jd = jdatetime.datetime.fromgregorian(datetime=value)
        return jd.strftime('%A %d %B %Y - %H:%M').translate(FA)
    except Exception:
        return value.strftime('%Y/%m/%d %H:%M').translate(FA)