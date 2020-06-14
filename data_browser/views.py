import csv
import io
import itertools
import json
import sys

import django.contrib.admin.views.decorators as admin_decorators
from django import http
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template import engines, loader
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from . import version
from .models import View
from .orm import _OPEN_IN_ADMIN, get_models, get_results
from .query import TYPES, BoundQuery, Query


def _get_query_data(bound_query):
    return {
        "filters": [
            {
                "path": filter_.path,
                "pathStr": filter_.path_str,
                "prettyPath": filter_.pretty_path,
                "lookup": filter_.lookup,
                "value": filter_.value,
            }
            for filter_ in bound_query.filters
        ],
        "filterErrors": [filter_.err_message for filter_ in bound_query.filters],
        "fields": [
            {
                "path": field.path,
                "pathStr": field.path_str,
                "prettyPath": field.pretty_path,
                "sort": field.direction,
                "priority": field.priority,
                "pivoted": field.pivoted,
            }
            for field in bound_query.fields
        ],
        "model": bound_query.model_name,
        "version": version,
    }


def _get_model_fields(orm_model):
    def sort_model_fields(fields):
        fields = sorted(fields)
        front = {"id": 1, _OPEN_IN_ADMIN: 2}
        return sorted(fields, key=lambda x: front.get(x, sys.maxsize))

    all_fields = {
        name: {
            "model": orm_field.rel_name,
            "type": orm_field.type_.name if orm_field.type_ else None,
            "concrete": orm_field.concrete,
            "canPivot": orm_field.can_pivot,
            "prettyName": orm_field.pretty_name,
        }
        for name, orm_field in orm_model.fields.items()
    }

    return {"fields": all_fields, "sortedFields": sort_model_fields(all_fields)}


def _get_config(user, orm_models):
    types = {
        name: {
            "lookups": {n: {"type": t} for n, t in type_.lookups.items()},
            "sortedLookups": list(type_.lookups),
            "defaultLookup": type_.default_lookup,
            "defaultValue": type_.default_value,
        }
        for name, type_ in TYPES.items()
    }

    all_model_fields = {
        model_name: _get_model_fields(orm_model)
        for model_name, orm_model in orm_models.items()
    }

    saved_views = [
        {
            "name": view.name,
            "public": view.public,
            "model": view.model_name,
            "description": view.description,
            "query": _get_query_data(BoundQuery.bind(view.get_query(), orm_models)),
        }
        for view in View.objects.filter(owner=user).order_by("name")
    ]

    admin_url = None
    if "data_browser.View" in orm_models:
        admin_url = reverse(f"admin:{View._meta.db_table}_add")

    return {
        "baseUrl": reverse("data_browser:home"),
        "adminUrl": admin_url,
        "types": types,
        "allModelFields": all_model_fields,
        "sortedModels": sorted(
            name for name, model in orm_models.items() if model.root
        ),
        "version": version,
        "savedViews": saved_views,
    }


def _get_context(request, model_name, fields):
    query = Query.from_request(model_name, fields, request.GET)
    orm_models = get_models(request)
    if query.model_name and query.model_name not in orm_models:
        raise http.Http404(f"{query.model_name} does not exist")
    bound_query = BoundQuery.bind(query, orm_models)
    return {
        "config": _get_config(request.user, orm_models),
        "initialState": {
            "results": [],
            "cols": [],
            "rows": [],
            **_get_query_data(bound_query),
        },
        "sentryDsn": getattr(settings, "DATA_BROWSER_FE_DSN", None),
    }


@admin_decorators.staff_member_required
def query_ctx(request, *, model_name, fields=""):
    ctx = _get_context(request, model_name, fields)
    return http.JsonResponse(ctx)


@admin_decorators.staff_member_required
def query_html(request, *, model_name="", fields=""):
    ctx = _get_context(request, model_name, fields)
    ctx = json.dumps(ctx)
    ctx = ctx.replace("<", "\\u003C").replace(">", "\\u003E").replace("&", "\\u0026")

    if getattr(settings, "DATA_BROWSER_DEV", False):  # pragma: no cover
        try:
            response = _get_from_js_dev_server(request)
        except Exception as e:
            return http.HttpResponse(f"Error loading from JS dev server.<br><br>{e}")

        template = engines["django"].from_string(response.text)
    else:
        template = loader.get_template("data_browser/index.html")

    return TemplateResponse(request, template, {"ctx": ctx})


@admin_decorators.staff_member_required
def query(request, *, model_name, fields="", media):
    query = Query.from_request(model_name, fields, request.GET)
    return _data_response(request, query, media, meta=True)


def view(request, pk, media):
    view = get_object_or_404(View.objects.filter(public=True), public_slug=pk)
    if (
        # some of these are checked by the admin but this is a good time to be paranoid
        view.owner.is_active
        and view.owner.is_staff
        and view.owner.has_perm("data_browser.make_view_public")
        and getattr(settings, "DATA_BROWSER_ALLOW_PUBLIC", False)
    ):
        request.user = view.owner  # public views are run as the person who owns them
        query = view.get_query()
        return _data_response(request, query, media, meta=False)
    else:
        raise http.Http404("No View matches the given query.")


def pad(x):
    return [None] * max(0, x)


def concat(*lists):
    return list(itertools.chain.from_iterable(lists))


def flip_table(table):
    return [list(x) for x in zip(*table)]


def join_tables(*tables):
    return [concat(*ts) for ts in zip(*tables)]


def format_table(fields, table, spacing=0):
    return concat(
        [[" ".join(f.pretty_path) for f in fields]],
        *[
            [[row[f.path_str] for f in fields]] + [pad(len(fields))] * spacing
            for row in table
        ],
    )


def pad_table(x, table):
    return [pad(x) + row for row in table]


def _data_response(request, query, media, meta):
    orm_models = get_models(request)
    if query.model_name not in orm_models:
        raise http.Http404(f"{query.model_name} does not exist")
    bound_query = BoundQuery.bind(query, orm_models)
    results = get_results(request, bound_query, orm_models)

    if media == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        # the pivoted column headers
        writer.writerows(
            pad_table(
                len(bound_query.row_fields) - 1,
                flip_table(
                    format_table(
                        bound_query.col_fields,
                        results["cols"],
                        spacing=len(bound_query.data_fields) - 1,
                    )
                ),
            )
        )

        # the row headers and data area
        writer.writerows(
            pad_table(
                1 - len(bound_query.row_fields),
                join_tables(
                    format_table(bound_query.row_fields, results["rows"]),
                    *(
                        format_table(bound_query.data_fields, sub_table)
                        for sub_table in results["body"]
                    ),
                ),
            )
        )

        buffer.seek(0)
        response = http.HttpResponse(buffer, content_type="text")
        response[
            "Content-Disposition"
        ] = f"attachment; filename={query.model_name}-{timezone.now().isoformat()}.csv"
        return response
    elif media == "json":
        resp = _get_query_data(bound_query) if meta else {}
        resp.update(results)
        return http.JsonResponse(resp)
    else:
        assert False


def _get_from_js_dev_server(request):  # pragma: no cover
    import requests

    upstream_url = f"http://127.0.0.1:3000{request.path}"
    method = request.META["REQUEST_METHOD"].lower()
    return getattr(requests, method)(upstream_url, stream=True)


@csrf_exempt
def proxy_js_dev_server(request, path):  # pragma: no cover
    """
    Proxy HTTP requests to the frontend dev server in development.

    The implementation is very basic e.g. it doesn't handle HTTP headers.

    """
    response = _get_from_js_dev_server(request)
    return http.StreamingHttpResponse(
        streaming_content=response.iter_content(2 ** 12),
        content_type=response.headers.get("Content-Type"),
        status=response.status_code,
        reason=response.reason,
    )
