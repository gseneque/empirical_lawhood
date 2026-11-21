# SPDX-License-Identifier: MPL-2.0
"""Typed terminal client for the same selected application operations as the UI."""

import argparse
from pathlib import Path
import sys

from empirical_lawhood.api.application_contracts import MAX_REQUEST_BYTES, ApplicationContext, ApplicationRequest, absolute_path, application_result, error_result, load_application_json, response_bytes
from empirical_lawhood.workbench.launcher import invoke_engine, negotiate_engine


def _document(path):
    with path.open("rb") as source:
        return load_application_json(source.read(MAX_REQUEST_BYTES+1))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run one typed application request in its selected engine.")
    parser.add_argument("--context", type=Path, required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--request", type=Path)
    selection.add_argument("--handle", help="Inspect an original durable invocation without repeating dispatch.")
    parser.add_argument("--required-mount", type=Path)
    args = parser.parse_args(argv)
    try:
        context = ApplicationContext.from_document(_document(absolute_path(args.context, "context")))
        if args.handle is not None:
            from empirical_lawhood.workbench.invocations import inspect_invocation
            body = response_bytes(application_result("application.invocation-state",
                inspect_invocation(context, args.handle, required_mount=args.required_mount)))
            sys.stdout.buffer.write(body)
            return 0
        request = ApplicationRequest.from_document(_document(absolute_path(args.request, "request")))
        selected = negotiate_engine(context)
        descriptor = next((row for row in selected.description["operations"] if row["operation_id"] == request.operation), {})
        if descriptor.get("lifecycle") in ("DURABLE_READ", "EFFECT"):
            from empirical_lawhood.workbench.invocations import dispatch
            snapshot, delivery = dispatch(selected, request, required_mount=args.required_mount, client="cli")
            sys.stderr.buffer.write(response_bytes(application_result("application.invocation-state", snapshot)))
            sys.stderr.buffer.flush()
            body = (response_bytes(application_result("application.invocation-state", snapshot))
                    if delivery is None else delivery.result())
            result = load_application_json(body, maximum_bytes=4*1024**2)
        else:
            result, body = invoke_engine(selected, request, client="cli")
        sys.stdout.buffer.write(body)
        return {"SUCCEEDED": 0, "INVALID": 2, "NOT_FOUND": 7, "CONFLICT": 8, "BLOCKED": 3, "FAILED": 6}[result["status"]]
    except Exception as error:
        sys.stderr.buffer.write(response_bytes(error_result("application.command", error)))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
