from datetime import datetime
from django import template
from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
import http.client
from django.contrib.staticfiles.templatetags.staticfiles import static
from web.models import ArticleImage, Allergen


register = template.Library()


@register.filter()
def verbose_name(value, arg):
    return value._meta.get_field(arg).verbose_name.title()


@register.filter()
def as_table(value, arg=""):
    return_value = ""
    value_dict = value.__dict__
    exclude_keys = ["_state", "id"] + arg.split(",")
    for col_key, col_value in value_dict.items():
        if col_key not in exclude_keys:

            return_value += "<tr class=\"table-row\">"
            return_value += "<td class=\"table-item-key\">" + \
                value._meta.get_field(col_key).verbose_name + "</td>"
            return_value += "<td class=\"table-item-value\">"
            if (type(col_value) is datetime):
                if col_value.year < 1970:
                    return_value += "-"
                else:
                    return_value += col_value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                return_value += str(col_value)
            return_value += "</td>"
            return_value += "</tr>"
    return mark_safe(return_value)


@register.filter()
def image_or_default(value, arg="large"):
    if value is None:
        return mark_safe("<img class=\"static-image-size-" + arg +
                         "\" src=\"" +
                         static("images/no-image-available.jpg") +
                         "\" alt=\"No image available\">")

    if value == "PALLET":
        return mark_safe("<img class=\"static-image-size-" + arg +
                         "\" src=\"" +
                         static("images/pallet.svg") +
                         "\" alt=\"Pallet\">")

    if value == "CASE":
        return mark_safe("<img class=\"static-image-size-" + arg +
                         "\" src=\"" +
                         static("images/case.svg") +
                         "\" alt=\"Case\">")

    static_domain = settings.STATIC_BUCKET_URL
    static_folder = "/pim/product-image/"

    if isinstance(value, ArticleImage) or value.source == 'validoo':
        static_folder = "/pim/article-image/"

    if settings.DEBUG and value.source != "mathem":
        static_domain = "static.mathem.se"

    conn = http.client.HTTPSConnection(static_domain)
    conn.request("HEAD", static_folder + arg + "/" + value.filename)
    res = conn.getresponse()
    print("IMAGE", static_domain + static_folder + arg + "/" + value.filename)
    content_type = res.getheader("Content-Type", "default")

    if "image" not in content_type:
        return mark_safe("<img class=\"static-image-size-" + arg +
                         "\" src=\"" +
                         static("images/image-not-found.jpg") +
                         "\" alt=\"Image not found\">")

    zoom_attr = ("https://" + static_domain +
                 static_folder + "large/" + value.filename)

    content = ("<img class=\"img-fluid\" zoom=\"" + zoom_attr +
               "\" src=\"https://" + static_domain +
               static_folder + arg + "/" + value.filename + "\">")

    return mark_safe(content)


@register.filter()
def pop_encode(value, arg=""):
    v_copy = value.copy()
    new_v = v_copy.pop(arg, True) and v_copy.urlencode()
    return new_v


@register.filter()
def is_text_field(value):
    return (isinstance(value.field.widget, forms.Textarea) or
            isinstance(value.field.widget, forms.TextInput))


@register.filter()
def get_attribute(value, arg=""):
    return getattr(value, arg)


@register.filter()
def allergen_text(value):
    return Allergen.get_text(value)
