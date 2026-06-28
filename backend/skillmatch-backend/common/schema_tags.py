"""drf-spectacular postprocessing hook: group endpoints into categories.

By default drf-spectacular tags each operation by the first path segment, which
splits related endpoints apart in Swagger. This hook assigns a single, friendly
category tag per endpoint so the Swagger UI mirrors the API reference docs.
"""

# Order matters: the first prefix that matches a path wins. More specific
# prefixes (e.g. "/api/matching/") are listed before broader ones so that
# "/api/matching/jobs/{id}/candidates/" is categorised as Matching, not Jobs.
CATEGORY_RULES = [
    ("/api/health", "System & Operational"),
    ("/api/schema", "System & Operational"),
    ("/api/docs", "System & Operational"),
    ("/api/auth/", "Authentication & Account"),
    ("/api/matching/", "Matching & AI"),
    ("/api/notifications/", "Notifications"),
    ("/api/skills", "Skills"),
    ("/api/resumes", "Resumes"),
    ("/api/jobs", "Jobs"),
    ("/api/applications", "Applications"),
]

_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}


def categorize_operations(result, generator, request, public):
    """Rewrite each operation's ``tags`` based on its URL path."""
    for path, path_item in result.get("paths", {}).items():
        category = next(
            (name for prefix, name in CATEGORY_RULES if path.startswith(prefix)),
            None,
        )
        if category is None:
            continue
        for method, operation in path_item.items():
            if method.lower() in _HTTP_METHODS and isinstance(operation, dict):
                operation["tags"] = [category]
    return result
