from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Protocol

from dsp_tools.error.xmllib_errors import XmllibInputError
from dsp_tools.error.xmllib_warnings import MessageInfo
from dsp_tools.error.xmllib_warnings_util import emit_xmllib_input_type_mismatch_warning
from dsp_tools.error.xmllib_warnings_util import raise_xmllib_input_error
from dsp_tools.utils.data_formats.uri_util import is_uri
from dsp_tools.xmllib.internal.checkers import check_and_inform_about_angular_brackets
from dsp_tools.xmllib.internal.circumvent_circular_imports import parse_richtext_as_xml
from dsp_tools.xmllib.internal.input_converters import check_and_fix_is_non_empty_string
from dsp_tools.xmllib.internal.input_converters import check_and_get_corrected_comment
from dsp_tools.xmllib.models.config_options import NewlineReplacement
from dsp_tools.xmllib.models.config_options import Permissions
from dsp_tools.xmllib.value_checkers import is_color
from dsp_tools.xmllib.value_checkers import is_date
from dsp_tools.xmllib.value_checkers import is_decimal
from dsp_tools.xmllib.value_checkers import is_geoname
from dsp_tools.xmllib.value_checkers import is_integer
from dsp_tools.xmllib.value_checkers import is_link_value
from dsp_tools.xmllib.value_checkers import is_nonempty_value
from dsp_tools.xmllib.value_checkers import is_timestamp
from dsp_tools.xmllib.value_converters import convert_to_bool_string
from dsp_tools.xmllib.value_converters import replace_newlines_with_tags


class Value(Protocol):
    value: str
    prop_name: str
    permissions: Permissions
    comment: str | None


@dataclass
class BooleanValue(Value):
    value: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
    ) -> BooleanValue:
        try:
            val = str(convert_to_bool_string(value)).lower()
        except XmllibInputError:
            emit_xmllib_input_type_mismatch_warning(
                expected_type="bool", value=value, res_id=resource_id, prop_name=prop_name
            )
            val = str(value)
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(value=val, prop_name=prop_name, permissions=permissions, comment=fixed_comment)


@dataclass
class ColorValue(Value):
    value: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
    ) -> ColorValue:
        if not is_color(value):
            emit_xmllib_input_type_mismatch_warning(
                expected_type="color", value=value, res_id=resource_id, prop_name=prop_name
            )
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(value=str(value), prop_name=prop_name, permissions=permissions, comment=fixed_comment)


@dataclass
class DateValue(Value):
    value: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
    ) -> DateValue:
        if not is_date(value):
            emit_xmllib_input_type_mismatch_warning(
                expected_type="date", value=value, res_id=resource_id, prop_name=prop_name
            )
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(value=str(value), prop_name=prop_name, permissions=permissions, comment=fixed_comment)


@dataclass
class DecimalValue(Value):
    value: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
    ) -> DecimalValue:
        if not is_decimal(value):
            emit_xmllib_input_type_mismatch_warning(
                expected_type="decimal", value=value, res_id=resource_id, prop_name=prop_name
            )
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(value=str(value), prop_name=prop_name, permissions=permissions, comment=fixed_comment)


@dataclass
class GeonameValue(Value):
    value: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
    ) -> GeonameValue:
        if not is_geoname(value):
            emit_xmllib_input_type_mismatch_warning(
                expected_type="geoname", value=value, res_id=resource_id, prop_name=prop_name
            )
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(value=str(value), prop_name=prop_name, permissions=permissions, comment=fixed_comment)


@dataclass
class IntValue(Value):
    value: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
    ) -> IntValue:
        if not is_integer(value):
            emit_xmllib_input_type_mismatch_warning(
                expected_type="integer", value=value, res_id=resource_id, prop_name=prop_name
            )
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(value=str(value), prop_name=prop_name, permissions=permissions, comment=fixed_comment)


@dataclass
class LinkValue(Value):
    value: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
    ) -> LinkValue:
        if not is_link_value(value):
            emit_xmllib_input_type_mismatch_warning(
                expected_type="xsd:ID or DSP resource IRI", value=value, res_id=resource_id, prop_name=prop_name
            )
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(value=str(value), prop_name=prop_name, permissions=permissions, comment=fixed_comment)


@dataclass
class ListValue(Value):
    value: str
    list_name: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        list_name: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
    ) -> ListValue:
        if str(value).startswith("http://rdfh.ch/lists/"):
            list_str = ""
        else:
            list_str = str(list_name)
            if not is_nonempty_value(list_name):
                emit_xmllib_input_type_mismatch_warning(
                    expected_type="list name", value=list_name, res_id=resource_id, prop_name=prop_name
                )
            if not is_nonempty_value(value):
                emit_xmllib_input_type_mismatch_warning(
                    expected_type="list node", value=value, res_id=resource_id, prop_name=prop_name
                )
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(
            value=str(value),
            list_name=list_str,
            prop_name=prop_name,
            permissions=permissions,
            comment=fixed_comment,
        )


@dataclass
class SimpleText(Value):
    value: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
    ) -> SimpleText:
        converted_val = check_and_fix_is_non_empty_string(value=value, res_id=resource_id, prop_name=prop_name)
        check_and_inform_about_angular_brackets(value=value, res_id=resource_id, prop_name=prop_name)
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(value=converted_val, prop_name=prop_name, permissions=permissions, comment=fixed_comment)


@dataclass
class Richtext(Value):
    value: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
        newline_replacement: NewlineReplacement = NewlineReplacement.NONE,
    ) -> Richtext:
        converted_val = check_and_fix_is_non_empty_string(value=value, res_id=resource_id, prop_name=prop_name)
        converted_val = replace_newlines_with_tags(converted_val, newline_replacement)
        result = parse_richtext_as_xml(converted_val)
        if isinstance(result, MessageInfo):
            raise_xmllib_input_error(result)
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(value=converted_val, prop_name=prop_name, permissions=permissions, comment=fixed_comment)


@dataclass
class TimeValue(Value):
    value: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
    ) -> TimeValue:
        if not is_timestamp(value):
            emit_xmllib_input_type_mismatch_warning(
                expected_type="timestamp", value=value, res_id=resource_id, prop_name=prop_name
            )
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(value=str(value), prop_name=prop_name, permissions=permissions, comment=fixed_comment)


@dataclass
class UriValue(Value):
    value: str
    prop_name: str
    permissions: Permissions = Permissions.PROJECT_SPECIFIC_PERMISSIONS
    comment: str | None = None

    @classmethod
    def new(
        cls,
        value: Any,
        prop_name: str,
        permissions: Permissions,
        comment: str | None,
        resource_id: str | None,
    ) -> UriValue:
        if not is_uri(value):
            emit_xmllib_input_type_mismatch_warning(
                expected_type="uri", value=value, res_id=resource_id, prop_name=prop_name
            )
        fixed_comment = check_and_get_corrected_comment(comment, resource_id, prop_name)
        return cls(value=str(value), prop_name=prop_name, permissions=permissions, comment=fixed_comment)
